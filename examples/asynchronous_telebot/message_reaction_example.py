#!/usr/bin/python3

# This is a simple bot using message reactions (emoji)
# https://core.telegram.org/bots/api#reactiontype

import random
from telebot.async_telebot import AsyncTeleBot
from telebot.types import ReactionTypeEmoji

API_TOKEN = '<api_token>'
bot = AsyncTeleBot(API_TOKEN)



# Send a reactions to all messages with content_type 'text' (content_types defaults to ['text'])
@bot.message_handler(func=lambda message: True)
async def send_reaction(message):
    emo = ["\U0001F525", "\U0001F917", "\U0001F60E"]  # or use ["🔥", "🤗", "😎"]
    await bot.set_message_reaction(message.chat.id, message.id, [ReactionTypeEmoji(random.choice(emo))], is_big=False)


@bot.message_reaction_handler(func=lambda message: True)
async def get_reactions(message):
    await bot.reply_to(message, f"You change reaction from {[r.emoji for r in message.old_reaction]} to {[r.emoji for r in message.new_reaction]}")


import asyncio
asyncio.run(bot.polling())
