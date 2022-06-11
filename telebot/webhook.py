import asyncio
import logging

from aiohttp import web

from telebot import api, types
from telebot.runner import BotRunner

logger = logging.getLogger(__name__)


def create_webhook_app(bot_runners: list[BotRunner], base_url: str) -> web.Application:
    ROUTE_TEMPLATE = "/webhook/{subroute}/"
    bot_runner_by_subroute = {bw.webhook_subroute(): bw for bw in bot_runners}
    logger.info("Running bots:\n" + "\n".join(f"/{path}: {bw.name}" for path, bw in bot_runner_by_subroute.items()))

    async def webhook_handler(request: web.Request):
        subroute = request.match_info.get("subroute")
        if subroute is None:
            return web.Response(status=404)
        bot_runner = bot_runner_by_subroute.get(subroute)
        if bot_runner is None:
            return web.Response(status=403)
        try:
            update = types.Update.de_json(await request.json())
            if update is not None:
                await bot_runner.bot.process_new_updates([update])
        except Exception as e:
            update_id = update.update_id if update is not None else "<not defined>"
            logger.exception(f"Unexpected error processing update #{update_id}:\n{update}")
        finally:
            return web.Response()

    background_tasks: set[asyncio.Task] = set()

    async def setup(_):
        loop = asyncio.get_running_loop()
        for subroute, br in bot_runner_by_subroute.items():
            await br.bot.delete_webhook()
            await br.bot.set_webhook(url=base_url + ROUTE_TEMPLATE.format(subroute=subroute))
            logger.info(f"Webhook set for {br.name}")
        for br in bot_runners:
            for idx, coro in enumerate(br.background_jobs):
                task = loop.create_task(coro, name=f"{br.name}-{idx}")
                background_tasks.add(task)

                def background_job_done(task: asyncio.Task):
                    background_tasks.discard(task)
                    logger.info(f"Backgound job is completed: {task}")

                task.add_done_callback(background_job_done)
                logger.info(f"Background task created for {br.name} (#{idx})")

    async def cleanup(_):
        logger.debug("Cleanup started")
        await api.session_manager.close_session()
        for t in background_tasks:
            logger.debug(f"Cancelling background task {t}")
            t.cancel()
        await asyncio.gather(*background_tasks)
        logger.debug("Cleanup completed")

    app = web.Application()
    app.on_startup.append(setup)
    app.on_cleanup.append(cleanup)
    app.router.add_post(ROUTE_TEMPLATE, webhook_handler)
    return app


def run_webhook_server(bot_runners: list[BotRunner], base_url: str, port: int):
    app = create_webhook_app(bot_runners, base_url)
    web.run_app(app, host="0.0.0.0", port=port, access_log=None)
