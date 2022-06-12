import asyncio
import logging

from aiohttp import web

from telebot import api, types
from telebot.runner import BotRunner

logger = logging.getLogger(__name__)


def create_webhook_app(bot_runners: list[BotRunner], base_url: str) -> web.Application:
    ROUTE_TEMPLATE = "/webhook/{subroute}/"
    bot_runner_by_subroute = {bw.webhook_subroute(): bw for bw in bot_runners}

    async def webhook_handler(request: web.Request):
        subroute = request.match_info.get("subroute")
        if subroute is None:
            return web.Response(status=404)
        bot_runner = bot_runner_by_subroute.get(subroute)
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

    background_tasks: set[asyncio.Task] = set()

    async def setup(_):
        broken_subroutes = []
        for subroute, br in bot_runner_by_subroute.items():
            try:
                await br.bot.delete_webhook()
                await br.bot.set_webhook(url=base_url + ROUTE_TEMPLATE.format(subroute=subroute))
                logger.info(f"Webhook set for {br.name:>30}: /{subroute}")
            except Exception as e:
                logger.error(f"Error setting up webhook for the bot {br.name}, dropping it: {e}")
                broken_subroutes.append(subroute)

        for subroute in broken_subroutes:
            bot_runner_by_subroute.pop(subroute)

        loop = asyncio.get_running_loop()
        for br in bot_runner_by_subroute.values():
            for idx, coro in enumerate(br.background_jobs):
                idx += 1  # 1-based numbering
                task = loop.create_task(coro, name=f"{br.name}-{idx}")
                background_tasks.add(task)

                def background_job_done(task: asyncio.Task):
                    background_tasks.discard(task)
                    logger.info(f"Backgound job completed: {task}")

                task.add_done_callback(background_job_done)
                logger.info(f"Background task created for {br.name} ({idx}/{len(br.background_jobs)})")

    async def cleanup(_):
        logger.debug("Cleanup started")
        await api.session_manager.close_session()
        for t in background_tasks:
            logger.debug(f"Cancelling background task {t}")
            t.cancel()
        logger.debug("Cleanup completed")

    app = web.Application()
    app.on_startup.append(setup)
    app.on_cleanup.append(cleanup)
    app.router.add_post(ROUTE_TEMPLATE, webhook_handler)
    return app


def run_webhook_server(bot_runners: list[BotRunner], base_url: str, port: int):
    app = create_webhook_app(bot_runners, base_url)
    web.run_app(app, host="0.0.0.0", port=port, access_log=None)
