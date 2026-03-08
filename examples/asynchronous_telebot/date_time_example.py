#!/usr/bin/python

# This example shows how to send a message with the Bot API 9.5 'date_time' entity.
# Telegram clients will render the selected text range as a localized date and time.

import asyncio
import time

from telebot import types
from telebot.async_telebot import AsyncTeleBot


API_TOKEN = '<api_token>'
bot = AsyncTeleBot(API_TOKEN)


@bot.message_handler(commands=['date_time'])
async def send_date_time(message):
    unix_time = int(time.time()) + 3600
    text = 'Reminder'
    entity = types.MessageEntity(
        type='date_time',
        offset=0,
        length=len(text),
        unix_time=unix_time,
        date_time_format='Dt'
    )

    await bot.send_message(message.chat.id, text, entities=[entity])


asyncio.run(bot.polling())
