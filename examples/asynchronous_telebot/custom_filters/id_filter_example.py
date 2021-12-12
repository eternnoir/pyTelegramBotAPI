from telebot.async_telebot import AsyncTeleBot
import telebot
bot = AsyncTeleBot('TOKEN')


# Chat id can be private or supergroups.
@bot.message_handler(chat_id=[12345678], commands=['admin']) # chat_id checks id corresponds to your list or not.
async def admin_rep(message):
    await bot.send_message(message.chat.id, "You are allowed to use this command.")

@bot.message_handler(commands=['admin'])
async def not_admin(message):
    await bot.send_message(message.chat.id, "You are not allowed to use this command")

# Do not forget to register
bot.add_custom_filter(telebot.asyncio_filters.ChatFilter())
import asyncio
asyncio.run(bot.polling())
