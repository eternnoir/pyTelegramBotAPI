#!/usr/bin/python

# This example shows how to implement i18n (internationalization) l10n (localization) to create
# multi-language bots with middleware handler.
#
# Also, you could check language code in handler itself too.
# But this example just to show the work of middlewares.

import telebot
from telebot.async_telebot import AsyncTeleBot
from telebot import asyncio_handler_backends
import logging

logger = telebot.logger
telebot.logger.setLevel(logging.DEBUG) # Outputs debug messages to console.

TRANSLATIONS = {
    'hello': {
        'en': 'hello',
        'ru': 'привет',
        'uz': 'salom'
    }
}



bot = AsyncTeleBot('TOKEN')


class LanguageMiddleware(asyncio_handler_backends.BaseMiddleware):
    def __init__(self):
        self.update_types = ['message'] # Update types that will be handled by this middleware.
    async def pre_process(self, message, data):
        data['response'] = TRANSLATIONS['hello'][message.from_user.language_code]
    async def post_process(self, message, data, exception):
        if exception: # You can get exception occured in handler.
            logger.exception(str(exception))

bot.setup_middleware(LanguageMiddleware()) # do not forget to setup

@bot.message_handler(commands=['start'])
async def start(message, data: dict):
    # you can get the data in handler too.
    # Not necessary to create data parameter in handler function.
    await bot.send_message(message.chat.id, data['response'])


import asyncio
asyncio.run(bot.polling())
