import logging

import telebot
from telebot.async_telebot import AsyncTeleBot, ExceptionHandler

logger = telebot.logger
telebot.logger.setLevel(logging.DEBUG)  # Outputs debug messages to console.


class MyExceptionHandler(ExceptionHandler):
    async def handle(self, exception):
        logger.error(exception)


bot = AsyncTeleBot('TOKEN', exception_handler=MyExceptionHandler())


@bot.message_handler(commands=['photo'])
async def photo_send(message: telebot.types.Message):
    await bot.send_message(message.chat.id, 'Hi, this is an example of exception handlers.')
    raise Exception('test')  # Exception goes to ExceptionHandler if it is set
    

import asyncio
asyncio.run(bot.polling())
