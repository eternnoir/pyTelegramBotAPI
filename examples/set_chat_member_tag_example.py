#!/usr/bin/python

# This example shows how to assign a tag to a regular supergroup member.
# The bot must be an administrator with permission to manage tags.

import telebot


API_TOKEN = '<api_token>'
CHAT_ID = -1001234567890
USER_ID = 123456789
TAG = 'support'

bot = telebot.TeleBot(API_TOKEN)

bot.set_chat_member_tag(CHAT_ID, USER_ID, TAG)

member = bot.get_chat_member(CHAT_ID, USER_ID)
print(member.tag)
