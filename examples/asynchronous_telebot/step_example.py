# -*- coding: utf-8 -*-
"""
This Example will show you how to use register_next_step handler.
"""

import asyncio

from telebot import asyncio_filters, types
from telebot.async_telebot import AsyncTeleBot
from telebot.asyncio_storage.memory_storage import StateMemoryStorage

API_TOKEN = '<api_token>'
bot = AsyncTeleBot(API_TOKEN, state_storage=StateMemoryStorage())




# Handle '/start' and '/help'
@bot.message_handler(commands=['help', 'start'])
async def send_welcome(message):
    msg = await bot.reply_to(message, """\
Hi there, I am Example bot.
What's your name?
""")
    await bot.register_next_step_handler(message.from_user.id, message.chat.id, process_name_step)


@bot.step_handler()
async def process_name_step(message):
    try:
        chat_id = message.chat.id
        name = message.text
        msg = await bot.reply_to(message, 'How old are you?')
        await bot.register_next_step_handler(message.from_user.id, message.chat.id, process_age_step,name=name)
    except Exception as e:
        await bot.reply_to(message, 'oooops')

@bot.step_handler()
async def process_age_step(message, name):
    try:
        chat_id = message.chat.id
        age = message.text
        if not age.isdigit():
            msg = await bot.reply_to(message, 'Age should be a number. How old are you?')
            await bot.register_next_step_handler(message.from_user.id, message.chat.id, process_age_step, name=name)
            return
        markup = types.ReplyKeyboardMarkup(one_time_keyboard=True)
        markup.add('Male', 'Female')
        msg = await bot.reply_to(message,f'Name: {name}\nWhat is your gender', reply_markup=markup)
        await bot.register_next_step_handler(message.from_user.id, message.chat.id, process_sex_step, name=name, age=age)
    except Exception as e:
        await bot.reply_to(message, 'oooops')

@bot.step_handler()
async def process_sex_step(message, name, age):
    try:
        chat_id = message.chat.id
        sex = message.text
        if sex not in [u'Male', u'Female']:
            raise Exception("Unknown sex")
        await bot.send_message(chat_id, 'Nice to meet you ' + name + '\nAge:' + str(age) + '\nSex:' + sex)
    except Exception as e:
        await bot.reply_to(message, 'oooops')


# Enable saving next step handlers to file "./.handlers-saves/step.save".
# Delay=2 means that after any change in next step handlers (e.g. calling register_next_step_handler())
# saving will hapen after delay 2 seconds.
bot.add_custom_filter(asyncio_filters.StateFilter(bot))


import asyncio
asyncio.run(bot.polling())