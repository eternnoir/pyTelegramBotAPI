from flask import Flask
from flask import request, abort
from telebot import TeleBot, types, util
from handlers import register_handlers

import config

main_bot = TeleBot(config.MAIN_BOT_TOKEN)
app = Flask(__name__)
tokens = {config.MAIN_BOT_TOKEN: True}


@app.route(f"/{config.WEBHOOK_PATH}/<token>", methods=['POST'])
def webhook(token: str):
    if not tokens.get(token):
        return abort(404)

    if request.headers.get('content-type') != 'application/json':
        return abort(403)

    json_string = request.get_data().decode('utf-8')
    update = types.Update.de_json(json_string)
    if token == main_bot.token:
        main_bot.process_new_updates([update])
        return ''

    from_update_bot = TeleBot(token)
    register_handlers(from_update_bot)
    from_update_bot.process_new_updates([update])
    return ''


@main_bot.message_handler(commands=['add_bot'])
def add_bot(message: types.Message):
    token = util.extract_arguments(message.text)
    tokens[token] = True

    new_bot = TeleBot(token)
    new_bot.delete_webhook()
    new_bot.set_webhook(f"{config.WEBHOOK_HOST}/{config.WEBHOOK_PATH}/{token}")

    new_bot.send_message(message.chat.id, "Webhook was set.")


if __name__ == '__main__':
    main_bot.delete_webhook()
    main_bot.set_webhook(f"{config.WEBHOOK_HOST}/{config.WEBHOOK_PATH}/{config.MAIN_BOT_TOKEN}")
    app.run(host=config.WEBAPP_HOST, port=config.WEBAPP_PORT)
