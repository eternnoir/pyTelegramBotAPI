from telebot import types, TeleBot


def hello_handler(message: types.Message, bot: TeleBot):
    bot.send_message(message.chat.id, "Hi :)")


def echo_handler(message: types.Message, bot: TeleBot):
    bot.send_message(message.chat.id, message.text)


def register_handlers(bot: TeleBot):
    bot.register_message_handler(hello_handler, func=lambda message: message.text == 'Hello', pass_bot=True)
    bot.register_message_handler(echo_handler, pass_bot=True)
