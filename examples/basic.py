import asyncio
import logging
import os

from dotenv import load_dotenv

from telebot import AsyncTeleBot
from telebot import types as tg
from telebot.runner import BotRunner
from telebot.types import constants as tg_const

load_dotenv()

bot = AsyncTeleBot(os.environ["TOKEN"])

logging.basicConfig(level=logging.DEBUG)


@bot.message_handler(chat_types=[tg_const.ChatType.private])
async def echo(message: tg.Message):
    await bot.reply_to(message, "you said:\n\n" + message.html_text, parse_mode="HTML")


asyncio.run(BotRunner(bot_prefix="echo-bot", bot=bot).run_polling())
