from telebot.async_telebot import AsyncTeleBot
from telebot.types import Message


async def hello_handler(message: Message, bot: AsyncTeleBot):
    await bot.send_message(message.chat.id, "Hi :)")


async def echo_handler(message: Message, bot: AsyncTeleBot):
    await bot.send_message(message.chat.id, message.text)


def register_handlers(bot: AsyncTeleBot):
    bot.register_message_handler(
        hello_handler, func=lambda message: message.text == "Hello", pass_bot=True
    )
    bot.register_message_handler(echo_handler, pass_bot=True)
