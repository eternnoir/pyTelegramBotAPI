#!/usr/bin/python3

# This is a simple bot with schedule timer 
# https://github.com/ibrb/python-aioschedule
# https://schedule.readthedocs.io

import asyncio
import aioschedule
from telebot.async_telebot import AsyncTeleBot

API_TOKEN = '<api_token>'
bot = AsyncTeleBot(API_TOKEN)


async def beep(chat_id) -> None:
    """Send the beep message."""
    await bot.send_message(chat_id, text='Beep!')
    aioschedule.clear(chat_id)  # return schedule.CancelJob not working in aioschedule use tag for delete


@bot.message_handler(commands=['help', 'start'])
async def send_welcome(message):
    await bot.reply_to(message, "Hi! Use /set <seconds> to set a timer")


@bot.message_handler(commands=['set'])
async def set_timer(message):
    args = message.text.split()
    if len(args) > 1 and args[1].isdigit():
        sec = int(args[1])
        aioschedule.every(sec).seconds.do(beep, message.chat.id).tag(message.chat.id)
    else:
        await bot.reply_to(message, 'Usage: /set <seconds>')


@bot.message_handler(commands=['unset'])
def unset_timer(message):
    aioschedule.clean(message.chat.id)


async def scheduler():
    while True:
        await aioschedule.run_pending()
        await asyncio.sleep(1)


async def main():
    await asyncio.gather(bot.infinity_polling(), scheduler())


if __name__ == '__main__':
    asyncio.run(main())
