# -*- coding: utf-8 -*-
"""
This Example will show you an advanced usage of CallbackData.
In this example calendar was implemented
"""
import asyncio
from datetime import date

from filters import calendar_factory, calendar_zoom, bind_filters
from keyboards import generate_calendar_days, generate_calendar_months, EMTPY_FIELD
from telebot import types
from telebot.async_telebot import AsyncTeleBot

API_TOKEN = ''
bot = AsyncTeleBot(API_TOKEN)


@bot.message_handler(commands='start')
async def start_command_handler(message: types.Message):
    await bot.send_message(message.chat.id,
                           f"Hello {message.from_user.first_name}. This bot is an example of calendar keyboard."
                           "\nPress /calendar to see it.")


@bot.message_handler(commands='calendar')
async def calendar_command_handler(message: types.Message):
    now = date.today()
    await bot.send_message(message.chat.id, 'Calendar',
                           reply_markup=generate_calendar_days(year=now.year, month=now.month))


@bot.callback_query_handler(func=None, calendar_config=calendar_factory.filter())
async def calendar_action_handler(call: types.CallbackQuery):
    callback_data: dict = calendar_factory.parse(callback_data=call.data)
    year, month = int(callback_data['year']), int(callback_data['month'])

    await bot.edit_message_reply_markup(call.message.chat.id, call.message.id,
                                        reply_markup=generate_calendar_days(year=year, month=month))


@bot.callback_query_handler(func=None, calendar_zoom_config=calendar_zoom.filter())
async def calendar_zoom_out_handler(call: types.CallbackQuery):
    callback_data: dict = calendar_zoom.parse(callback_data=call.data)
    year = int(callback_data.get('year'))

    await bot.edit_message_reply_markup(call.message.chat.id, call.message.id,
                                        reply_markup=generate_calendar_months(year=year))


@bot.callback_query_handler(func=lambda call: call.data == EMTPY_FIELD)
async def callback_empty_field_handler(call: types.CallbackQuery):
    await bot.answer_callback_query(call.id)


if __name__ == '__main__':
    bind_filters(bot)
    asyncio.run(bot.infinity_polling())
