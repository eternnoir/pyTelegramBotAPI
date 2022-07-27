import asyncio
import logging
import os

from telebot import AsyncTeleBot
from telebot import types as tg
from telebot.runner import BotRunner
from telebot.types import constants as tg_const

bot = AsyncTeleBot(os.environ["TOKEN"])

logging.basicConfig(level=logging.DEBUG)


@bot.message_handler(chat_types=[tg_const.ChatType.private])
async def echo(message: tg.Message):
    await bot.reply_to(message, message.text_content)


asyncio.run(BotRunner(bot_prefix="echo-bot", bot=bot).run_polling())
