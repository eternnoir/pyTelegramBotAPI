# -*- coding: utf-8 -*-
"""
This Example will show you an advanced usage of CallbackData.
In this example calendar was implemented
"""

from datetime import date

from examples.callback_data_examples.advanced_calendar_example.keyboards import generate_calendar_days, \
    generate_calendar_months, EMTPY_FIELD
from filters import calendar_factory, calendar_zoom, bind_filters
from telebot import types, TeleBot

API_TOKEN = ''
bot = TeleBot(API_TOKEN)


@bot.message_handler(commands='start')
def start_command_handler(message: types.Message):
    bot.send_message(message.chat.id,
                     f"Hello {message.from_user.first_name}. This bot is an example of calendar keyboard."
                     "\nPress /calendar to see it.")


@bot.message_handler(commands='calendar')
def calendar_command_handler(message: types.Message):
    now = date.today()
    bot.send_message(message.chat.id, 'Calendar', reply_markup=generate_calendar_days(year=now.year, month=now.month))


@bot.callback_query_handler(func=None, calendar_config=calendar_factory.filter())
def calendar_action_handler(call: types.CallbackQuery):
    callback_data: dict = calendar_factory.parse(callback_data=call.data)
    year, month = int(callback_data['year']), int(callback_data['month'])

    bot.edit_message_reply_markup(call.message.chat.id, call.message.id,
                                  reply_markup=generate_calendar_days(year=year, month=month))


@bot.callback_query_handler(func=None, calendar_zoom_config=calendar_zoom.filter())
def calendar_zoom_out_handler(call: types.CallbackQuery):
    callback_data: dict = calendar_zoom.parse(callback_data=call.data)
    year = int(callback_data.get('year'))

    bot.edit_message_reply_markup(call.message.chat.id, call.message.id,
                                  reply_markup=generate_calendar_months(year=year))


@bot.callback_query_handler(func=lambda call: call.data == EMTPY_FIELD)
def callback_empty_field_handler(call: types.CallbackQuery):
    bot.answer_callback_query(call.id)


if __name__ == '__main__':
    bind_filters(bot)
    bot.infinity_polling()
