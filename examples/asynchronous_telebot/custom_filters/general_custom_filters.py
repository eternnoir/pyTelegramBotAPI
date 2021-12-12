from telebot.async_telebot import AsyncTeleBot
import telebot
bot = AsyncTeleBot('TOKEN')


# AdvancedCustomFilter is for list, string filter values
class MainFilter(telebot.asyncio_filters.AdvancedCustomFilter):
    key='text'
    @staticmethod
    async def check(message, text):
        return message.text in text

# SimpleCustomFilter is for boolean values, such as is_admin=True
class IsAdmin(telebot.asyncio_filters.SimpleCustomFilter):
    key='is_admin'
    @staticmethod
    async def check(message: telebot.types.Message):
        result = await bot.get_chat_member(message.chat.id,message.from_user.id)
        return result.status in ['administrator','creator']


@bot.message_handler(is_admin=True, commands=['admin']) # Check if user is admin
async def admin_rep(message):
    await bot.send_message(message.chat.id, "Hi admin")

@bot.message_handler(is_admin=False, commands=['admin']) # If user is not admin
async def not_admin(message):
    await bot.send_message(message.chat.id, "You are not admin")

@bot.message_handler(text=['hi']) # Response to hi message
async def welcome_hi(message):
    await bot.send_message(message.chat.id, 'You said hi')

@bot.message_handler(text=['bye']) # Response to bye message
async def bye_user(message):
    await bot.send_message(message.chat.id, 'You said bye')


# Do not forget to register filters
bot.add_custom_filter(MainFilter())
bot.add_custom_filter(IsAdmin())

import asyncio
asyncio.run(bot.polling())
