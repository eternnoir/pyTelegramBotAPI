# -*- coding: utf-8 -*-
"""
This Example will show you usage of TextFilter
In this example you will see how to use TextFilter
with (message_handler, callback_query_handler, poll_handler)
"""
import asyncio

from telebot import types
from telebot.async_telebot import AsyncTeleBot
from telebot.asyncio_filters import TextMatchFilter, TextFilter

bot = AsyncTeleBot("")


@bot.message_handler(text=TextFilter(equals='hello'))
async def hello_handler(message: types.Message):
    await bot.send_message(message.chat.id, message.text)


@bot.message_handler(text=TextFilter(equals='hello', ignore_case=True))
async def hello_handler_ignore_case(message: types.Message):
    await bot.send_message(message.chat.id, message.text + ' ignore case')


@bot.message_handler(text=TextFilter(contains=['good', 'bad']))
async def contains_handler(message: types.Message):
    await bot.send_message(message.chat.id, message.text)


@bot.message_handler(text=TextFilter(contains=['good', 'bad'], ignore_case=True))
async def contains_handler_ignore_case(message: types.Message):
    await bot.send_message(message.chat.id, message.text + ' ignore case')


@bot.message_handler(text=TextFilter(starts_with='st'))  # stArk, steve, stONE
async def starts_with_handler(message: types.Message):
    await bot.send_message(message.chat.id, message.text)


@bot.message_handler(text=TextFilter(starts_with='st', ignore_case=True))  # STark, sTeve, stONE
async def starts_with_handler_ignore_case(message: types.Message):
    await bot.send_message(message.chat.id, message.text + ' ignore case')


@bot.message_handler(text=TextFilter(ends_with='ay'))  # wednesday, SUNday, WeekDay
async def ends_with_handler(message: types.Message):
    await bot.send_message(message.chat.id, message.text)


@bot.message_handler(text=TextFilter(ends_with='ay', ignore_case=True))  # wednesdAY, sundAy, WeekdaY
async def ends_with_handler_ignore_case(message: types.Message):
    await bot.send_message(message.chat.id, message.text + ' ignore case')


@bot.message_handler(text=TextFilter(equals='/callback'))
async def send_callback(message: types.Message):
    keyboard = types.InlineKeyboardMarkup(
        keyboard=[
            [types.InlineKeyboardButton(text='callback data', callback_data='example')],
            [types.InlineKeyboardButton(text='ignore case callback data', callback_data='ExAmPLe')]
        ]
    )
    await bot.send_message(message.chat.id, message.text, reply_markup=keyboard)


@bot.callback_query_handler(func=None, text=TextFilter(equals='example'))
async def callback_query_handler(call: types.CallbackQuery):
    await bot.answer_callback_query(call.id, call.data, show_alert=True)


@bot.callback_query_handler(func=None, text=TextFilter(equals='example', ignore_case=True))
async def callback_query_handler_ignore_case(call: types.CallbackQuery):
    await bot.answer_callback_query(call.id, call.data + " ignore case", show_alert=True)


@bot.message_handler(text=TextFilter(equals='/poll'))
async def send_poll(message: types.Message):
    await bot.send_poll(message.chat.id, question='When do you prefer to work?', options=['Morning', 'Night'])
    await bot.send_poll(message.chat.id, question='WHEN DO you pRefeR to worK?', options=['Morning', 'Night'])


@bot.poll_handler(func=None, text=TextFilter(equals='When do you prefer to work?'))
async def poll_question_handler(poll: types.Poll):
    print(poll.question)


@bot.poll_handler(func=None, text=TextFilter(equals='When do you prefer to work?', ignore_case=True))
async def poll_question_handler_ignore_case(poll: types.Poll):
    print(poll.question + ' ignore case')


if __name__ == '__main__':
    bot.add_custom_filter(TextMatchFilter())
    asyncio.run(bot.polling())
