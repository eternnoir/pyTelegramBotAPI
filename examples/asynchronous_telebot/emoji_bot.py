#!/usr/bin/python

# This is a simple echo bot using message reactions (emoji)
# https://core.telegram.org/bots/api#reactiontype

import random
from telebot.async_telebot import AsyncTeleBot
from telebot.types import ReactionTypeEmoji

API_TOKEN = '<api_token>'
bot = AsyncTeleBot(API_TOKEN)


# Handle '/start' and '/help'
@bot.message_handler(commands=['help', 'start'])
async def send_welcome(message):
    await bot.reply_to(message, """\
Hi there, I am EchoBot.
I am here to echo your kind words back to you. Just say anything nice and I'll say the exact same thing to you!\
""")


# Handle all other messages with content_type 'text' (content_types defaults to ['text'])
@bot.message_handler(func=lambda message: True)
async def message_reaction(message):
    emo = ["\U0001F525", "\U0001F917", "\U0001F60E"]  # or use ["🔥", "🤗", "😎"]
    await bot.set_message_reaction(message.chat.id, message.id, [ReactionTypeEmoji(random.choice(emo))], is_big=False)


import asyncio
asyncio.run(bot.polling())
