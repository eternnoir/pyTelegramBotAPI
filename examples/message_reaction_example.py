#!/usr/bin/python3

# This is a simple bot using message reactions (emoji)
# https://core.telegram.org/bots/api#reactiontype

import random
import telebot
from telebot.types import ReactionTypeEmoji

API_TOKEN = '<api_token>'
bot = telebot.TeleBot(API_TOKEN)


# Send a reactions to all messages with content_type 'text' (content_types defaults to ['text'])
@bot.message_handler(func=lambda message: True)
def send_reaction(message):
    emo = ["\U0001F525", "\U0001F917", "\U0001F60E"]  # or use ["🔥", "🤗", "😎"]
    bot.set_message_reaction(message.chat.id, message.id, [ReactionTypeEmoji(random.choice(emo))], is_big=False)
    

@bot.message_reaction_handler(func=lambda message: True)
def get_reactions(message):
    bot.reply_to(message, f"You change reaction from {[r.emoji for r in message.old_reaction]} to {[r.emoji for r in message.new_reaction]}")

# https://core.telegram.org/bots/api#update
# allowed_updates: Specify an empty list to receive all update types except, chat_member, message_reaction, and message_reaction_count. 
# If you want to receive message_reaction events, you can't just leave allowed_updates=None at its default setting. You must explicitly list all the events you want to receive and include message_reaction.
bot.infinity_polling(allowed_updates=['message', 'message_reaction'])
