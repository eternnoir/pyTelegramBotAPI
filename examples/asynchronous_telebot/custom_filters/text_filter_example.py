from telebot.async_telebot import AsyncTeleBot
import telebot
bot = AsyncTeleBot('TOKEN')


# Check if message starts with @admin tag
@bot.message_handler(text_startswith="@admin")
async def start_filter(message):
    await bot.send_message(message.chat.id, "Looks like you are calling admin, wait...")

# Check if text is hi or hello
@bot.message_handler(text=['hi','hello'])
async def text_filter(message):
    await bot.send_message(message.chat.id, "Hi, {name}!".format(name=message.from_user.first_name))

# Do not forget to register filters
bot.add_custom_filter(telebot.asyncio_filters.TextMatchFilter())
bot.add_custom_filter(telebot.asyncio_filters.TextStartsFilter())

import asyncio
asyncio.run(bot.polling())
