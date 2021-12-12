from telebot.async_telebot import AsyncTeleBot
from telebot import asyncio_filters
bot = AsyncTeleBot('1297441208:AAGiez5xhzai5russPtPKmZjbdjybW4T0U8')

# Handler
@bot.message_handler(chat_types=['supergroup'], is_chat_admin=True)
async def answer_for_admin(message):
    await bot.send_message(message.chat.id,"hello my admin")

# Register filter
bot.add_custom_filter(asyncio_filters.IsAdminFilter(bot))

import asyncio
asyncio.run(bot.polling())
