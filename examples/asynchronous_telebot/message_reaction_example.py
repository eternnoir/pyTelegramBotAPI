#!/usr/bin/python3

# This is a simple bot using message reactions (emoji)
# https://core.telegram.org/bots/api#reactiontype
# https://core.telegram.org/bots/api#update
# allowed_updates: Specify an empty list to receive all update types except, chat_member, message_reaction, and message_reaction_count. 
# If you want to receive message_reaction events, you cannot simply leave the allowed_updates=None default value. 
# The default list of events does not include chat_member, message_reaction, and message_reaction_count events. 
# You must explicitly specify all the events you wish to receive and add message_reaction to this list. 
# It’s also important to note that after using allowed_updates=[...], in the future, using allowed_updates=None will mean 
# that the list of events you will receive will consist of the events you last explicitly specified.

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
    await bot.reply_to(message, f"You changed the reaction from {[r.emoji for r in message.old_reaction]} to {[r.emoji for r in message.new_reaction]}")


import asyncio
asyncio.run(bot.infinity_polling(allowed_updates=['message', 'message_reaction']))
