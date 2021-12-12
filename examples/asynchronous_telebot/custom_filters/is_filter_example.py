from telebot.async_telebot import AsyncTeleBot
import telebot

bot = AsyncTeleBot('TOKEN')



# Check if message is a reply
@bot.message_handler(is_reply=True)
async def start_filter(message):
    await bot.send_message(message.chat.id, "Looks like you replied to my message.")

# Check if message was forwarded
@bot.message_handler(is_forwarded=True)
async def text_filter(message):
    await bot.send_message(message.chat.id, "I do not accept forwarded messages!")

# Do not forget to register filters
bot.add_custom_filter(telebot.asyncio_filters.IsReplyFilter())
bot.add_custom_filter(telebot.asyncio_filters.ForwardFilter())

import asyncio
asyncio.run(bot.polling())
