#!/usr/bin/python

# This example shows how to assign a tag to a regular supergroup member.
# The bot must be an administrator with permission to manage tags.

import asyncio

from telebot.async_telebot import AsyncTeleBot


API_TOKEN = '<api_token>'
CHAT_ID = -1001234567890
USER_ID = 123456789
TAG = 'support'

bot = AsyncTeleBot(API_TOKEN)


async def main():
    await bot.set_chat_member_tag(CHAT_ID, USER_ID, TAG)

    member = await bot.get_chat_member(CHAT_ID, USER_ID)
    print(member.tag)

    await bot.close_session()


asyncio.run(main())
