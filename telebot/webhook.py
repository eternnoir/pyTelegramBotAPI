import asyncio
import logging
from typing import Any, Callable, Coroutine, Optional

from aiohttp import web

from telebot import api, types
from telebot.runner import BotRunner

logger = logging.getLogger(__name__)


WEBHOOK_ROUTE = "/webhook/{subroute}/"


class WebhookApp:
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.bot_runner_by_subroute: dict[str, BotRunner] = dict()
        self.background_tasks: set[asyncio.Task] = set()
        self.aiohttp_app = web.Application()
        self.aiohttp_app.router.add_post(WEBHOOK_ROUTE, self.bot_webhook_handler)

    async def bot_webhook_handler(self, request: web.Request):
        subroute = request.match_info.get("subroute")
        if subroute is None:
            return web.Response(status=404)
        bot_runner = self.bot_runner_by_subroute.get(subroute)
        if bot_runner is None:
            return web.Response(status=404)
        try:
            update = types.Update.de_json(await request.json())
            if update is not None:
                await bot_runner.bot.process_new_updates([update])
        except Exception:
            update_id = update.update_id if update is not None else "<not defined>"
            logger.exception(f"Unexpected error processing update #{update_id}:\n{update}")
        finally:
            return web.Response()

    async def add_bot_runner(self, runner: BotRunner) -> bool:
        subroute = runner.webhook_subroute()
        try:
            await runner.bot.delete_webhook()
            await runner.bot.set_webhook(url=self.base_url + WEBHOOK_ROUTE.format(subroute=subroute))
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

        loop = asyncio.get_running_loop()
        for idx, coro in enumerate(runner.background_jobs):
            idx += 1  # 1-based numbering
            task = loop.create_task(coro, name=f"{runner.bot_prefix}-{idx}")
            self.background_tasks.add(task)

            def background_job_done(task: asyncio.Task):
                self.background_tasks.discard(task)
                logger.info(f"Backgound job completed: {task}")

            task.add_done_callback(background_job_done)
            logger.info(f"Background task created for {runner.bot_prefix} ({idx}/{len(runner.background_jobs)})")

        self.bot_runner_by_subroute[subroute] = runner
        return True

    async def remove_bot_runner(self, runner: BotRunner) -> bool:
        """Warning: background jobs and aux endpoints added with the runner are not removed/cancelled"""
        subroute = runner.webhook_subroute()
        if subroute not in self.bot_runner_by_subroute:
            return False
        try:
            await runner.bot.delete_webhook()
            logger.info(f"Webhook removed for {runner.bot_prefix}; was /webhook/{subroute}")
        except Exception as e:
            logger.exception(f"Error deleting webhook for the bot {runner.bot_prefix}, keeping it")
            return False

        self.bot_runner_by_subroute.pop(subroute)
        return True

    async def run(self, port: int, on_server_listening: Optional[Callable[[], Coroutine[None, None, Any]]] = None):
        aiohttp_runner = web.AppRunner(self.aiohttp_app, access_log=None)
        await aiohttp_runner.setup()
        site = web.TCPSite(aiohttp_runner, "0.0.0.0", port)
        try:
            await site.start()
            if on_server_listening is not None:
                await on_server_listening()
            while True:
                await asyncio.sleep(3600)
        finally:
            logger.debug("Cleanup started")
            await api.session_manager.close_session()
            for t in self.background_tasks:
                logger.debug(f"Cancelling background task {t}")
                t.cancel()
            logger.debug("Cleanup completed")
            await aiohttp_runner.cleanup()
