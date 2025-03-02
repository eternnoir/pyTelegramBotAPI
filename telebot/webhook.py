import asyncio
import collections
import logging
import time
from typing import Any, Callable, Coroutine, Optional

from aiohttp import web
from aiohttp.typedefs import Handler as AiohttpHandler

from telebot import api, types
from telebot.graceful_shutdown import (
    GracefulShutdownCondition,
    GracefulShutdownHandler,
    is_shutting_down,
)
from telebot.metrics import (
    TelegramUpdateMetrics,
    TelegramUpdateMetricsHandler,
    noop_metrics_handler,
)
from telebot.runner import BotRunner
from telebot.util import create_error_logging_task

logger = logging.getLogger(__name__)


WEBHOOK_ROUTE = "/webhook/{subroute}/"


class WebhookApp:
    def __init__(
        self,
        base_url: str,
        metrics_handler: TelegramUpdateMetricsHandler = noop_metrics_handler,
    ):
        self.base_url = base_url
        self.bot_runner_by_subroute: dict[str, BotRunner] = dict()
        self.background_task_by_bot_subroute: dict[str, set[asyncio.Task]] = collections.defaultdict(set)
        self.aiohttp_app = web.Application()
        self.aiohttp_app.router.add_post(WEBHOOK_ROUTE, self._bot_webhook_handler)
        self.aiohttp_app.middlewares.append(self._graceful_shutdown_middleware)
        self._current_request_count = 0
        self._metrics_handler = metrics_handler

        self._shutdown_condition = GracefulShutdownCondition(
            predicate=self.is_ready_to_shutdown,
            description="still processing requests in webhook app",
        )

    async def is_ready_to_shutdown(self) -> bool:
        return self._current_request_count == 0

    async def _bot_webhook_handler(self, request: web.Request):
        subroute = request.match_info.get("subroute")
        if subroute is None:
            return web.Response(status=404)
        bot_runner = self.bot_runner_by_subroute.get(subroute)
        if bot_runner is None:
            return web.Response(status=404)
        update = None
        try:
            update = types.Update.de_json(
                await request.json(),
                metrics=TelegramUpdateMetrics(
                    bot_prefix=bot_runner.bot_prefix,
                    received_at=time.time(),
                ),
            )
            if update is not None:
                await bot_runner.bot.process_new_updates(
                    [update],
                    global_update_metrics_handler=self._metrics_handler,
                )
        except Exception:
            update_id = update.update_id if update is not None else "<not defined>"
            logger.exception(f"Unexpected error processing update #{update_id}:\n{update}")
        finally:
            return web.Response()

    @web.middleware
    async def _graceful_shutdown_middleware(self, request: web.Request, handler: AiohttpHandler) -> web.StreamResponse:
        if is_shutting_down():
            raise web.HTTPInternalServerError(reason="Server is going offline, try again later")
        self._current_request_count += 1
        try:
            return await handler(request)
        finally:
            self._current_request_count -= 1

    async def add_bot_runner(self, runner: BotRunner) -> bool:
        subroute = runner.webhook_subroute()
        if subroute in self.bot_runner_by_subroute:
            logger.info("Attempt to set bot runner for already existing subroute")
            return False
        webhook_url = self.base_url + WEBHOOK_ROUTE.format(subroute=subroute)
        try:
            existing_webhook_info = await runner.bot.get_webhook_info()
            if existing_webhook_info.url == webhook_url:
                logger.info(f"Existing webhook found for {runner.bot_prefix}")
            else:
                await runner.bot.set_webhook(url=webhook_url)
                logger.info(f"Webhook set for {runner.bot_prefix}: /webhook/{subroute}")
        except Exception as e:
            logger.exception(f"Error setting up webhook for the bot {runner.bot_prefix}, dropping it: {e}")
            return False

        for endpoint in runner.aux_endpoints:
            self.aiohttp_app.router.add_route(
                endpoint.method,
                endpoint.route,
                endpoint.handler,
            )
            logger.info(f"Aux endpoint created for {runner.bot_prefix}: {endpoint.route}")

        for idx, coro in enumerate(runner.background_jobs):
            idx += 1  # 1-based numbering
            task = create_error_logging_task(coro, name=f"{runner.bot_prefix}-{idx}")
            self.background_task_by_bot_subroute[subroute].add(task)

            def background_job_done(task: asyncio.Task):
                if task.cancelled():
                    logger.info(f"Backgound job cancelled: {task}")
                else:
                    logger.info(f"Backgound job completed: {task}")

            task.add_done_callback(background_job_done)
            logger.info(f"Background task created for {runner.bot_prefix} ({idx}/{len(runner.background_jobs)})")

        self.bot_runner_by_subroute[subroute] = runner
        return True

    async def remove_bot_runner(self, runner: BotRunner) -> bool:
        subroute = runner.webhook_subroute()
        if subroute not in self.bot_runner_by_subroute:
            return False
        try:
            await runner.bot.delete_webhook()
            logger.info(f"Webhook removed for {runner.bot_prefix}; was /webhook/{subroute}")
        except Exception:
            logger.exception(f"Error deleting webhook for the bot {runner.bot_prefix}")
            return False
        await self._cancel_background_tasks(subroute)
        self.background_task_by_bot_subroute.pop(subroute, None)
        self.bot_runner_by_subroute.pop(subroute)
        return True

    async def _cancel_background_tasks(self, subroute: str) -> None:
        tasks = self.background_task_by_bot_subroute.get(subroute)
        if tasks is None:
            return
        for task in tasks:
            logger.debug(f"Cancelling background task {task} for {subroute}")
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass

    async def run(
        self,
        port: int,
        graceful_shutdown: bool = True,
        on_server_listening: Optional[Callable[[], Coroutine[None, None, Any]]] = None,
    ):
        aiohttp_runner = web.AppRunner(self.aiohttp_app, access_log=None)
        await aiohttp_runner.setup()
        site = web.TCPSite(aiohttp_runner, "0.0.0.0", port)
        try:
            await site.start()
            if on_server_listening is not None:
                await on_server_listening()
            if graceful_shutdown:
                await GracefulShutdownHandler().run()
            else:
                while True:
                    await asyncio.sleep(3600)
        finally:
            logger.debug("Cleanup started")
            for subroute in self.background_task_by_bot_subroute:
                await self._cancel_background_tasks(subroute)

            await api.session_manager.close_session()
            await aiohttp_runner.cleanup()
            logger.debug("Cleanup completed")
