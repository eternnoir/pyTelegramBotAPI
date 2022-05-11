import asyncio

from aiohttp import web
from telebot import types, util
from telebot.async_telebot import AsyncTeleBot
from handlers import register_handlers

import config

main_bot = AsyncTeleBot(config.MAIN_BOT_TOKEN)
app = web.Application()
tokens = {config.MAIN_BOT_TOKEN: True}


async def webhook(request):
    token = request.match_info.get('token')
    if not tokens.get(token):
        return web.Response(status=404)

    if request.headers.get('content-type') != 'application/json':
        return web.Response(status=403)

    json_string = await request.json()
    update = types.Update.de_json(json_string)
    if token == main_bot.token:
        await main_bot.process_new_updates([update])
        return web.Response()

    from_update_bot = AsyncTeleBot(token)
    register_handlers(from_update_bot)
    await from_update_bot.process_new_updates([update])
    return web.Response()


app.router.add_post("/" + config.WEBHOOK_PATH + "/{token}", webhook)


@main_bot.message_handler(commands=['add_bot'])
async def add_bot(message: types.Message):
    token = util.extract_arguments(message.text)
    tokens[token] = True

    new_bot = AsyncTeleBot(token)
    await new_bot.delete_webhook()
    await new_bot.set_webhook(f"{config.WEBHOOK_HOST}/{config.WEBHOOK_PATH}/{token}")

    await new_bot.send_message(message.chat.id, "Webhook was set.")


async def main():
    await main_bot.delete_webhook()
    await main_bot.set_webhook(f"{config.WEBHOOK_HOST}/{config.WEBHOOK_PATH}/{config.MAIN_BOT_TOKEN}")
    web.run_app(app, host=config.WEBAPP_HOST, port=config.WEBAPP_PORT)

if __name__ == '__main__':
    asyncio.run(main())
