from telebot.async_telebot import AsyncTeleBot
from telebot.asyncio_handler_backends import ContinueHandling


bot = AsyncTeleBot('TOKEN')

@bot.message_handler(commands=['start'])
async def start(message):
    await bot.send_message(message.chat.id, 'Hello World!')
    return ContinueHandling()

@bot.message_handler(commands=['start'])
async def start2(message):
    """
    This handler comes after the first one, but it will never be called.
    But you can call it by returning ContinueHandling() in the first handler.

    If you return ContinueHandling() in the first handler, the next 
    registered handler with appropriate filters will be called.
    """
    await bot.send_message(message.chat.id, 'Hello World2!')

import asyncio 
asyncio.run(bot.polling()) # just a reminder that infinity polling
# wraps polling into try/except block just as sync version,
# but you can use any of them because neither of them stops if you
# pass non_stop=True
