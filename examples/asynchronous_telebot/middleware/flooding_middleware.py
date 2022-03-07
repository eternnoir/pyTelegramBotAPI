# Just a little example of middleware handlers

from telebot.asyncio_handler_backends import BaseMiddleware, CancelUpdate
from telebot.async_telebot import AsyncTeleBot
bot = AsyncTeleBot('TOKEN')


class SimpleMiddleware(BaseMiddleware):
    def __init__(self, limit) -> None:
        self.last_time = {}
        self.limit = limit
        self.update_types = ['message']
        # Always specify update types, otherwise middlewares won't work


    async def pre_process(self, message, data):
        if not message.from_user.id in self.last_time:
            # User is not in a dict, so lets add and cancel this function
            self.last_time[message.from_user.id] = message.date
            return
        if message.date - self.last_time[message.from_user.id] < self.limit:
            # User is flooding
            await bot.send_message(message.chat.id, 'You are making request too often')
            return CancelUpdate()
        self.last_time[message.from_user.id] = message.date

        
    async def post_process(self, message, data, exception):
        pass

bot.setup_middleware(SimpleMiddleware(2))

@bot.message_handler(commands=['start'])
async def start(message):
    await bot.send_message(message.chat.id, 'Hello!')

import asyncio
asyncio.run(bot.polling())
