import asyncio
import json
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

    background_tasks: list[asyncio.Task] = []

    async def setup(_):
        loop = asyncio.get_event_loop()
        for subroute, br in bot_runner_by_subroute.items():
            await br.bot.delete_webhook()
            await br.bot.set_webhook(url=base_url + ROUTE_TEMPLATE.format(subroute=subroute))
            logger.info(f"Webhook set for {br.name}")
        for bw in bot_runners:
            for idx, coro in enumerate(bw.background_jobs):
                background_tasks.append(loop.create_task(coro))
                logger.info(f"Background task #{idx} created for {bw.name}")

    async def cleanup(_):
        await api.session_manager.close_session()
        for t in background_tasks:
            t.cancel()

    app = web.Application()
    app.on_startup.append(setup)
    app.on_cleanup.append(cleanup)
    app.router.add_post(ROUTE_TEMPLATE, webhook_handler)

    return app


def run_webhook_server(bot_runners: list[BotRunner], base_url: str, port: int):
    app = create_webhook_app(bot_runners, base_url)
    web.run_app(app, host="0.0.0.0", port=port, access_log=None)
