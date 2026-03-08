#!/usr/bin/python

# This example shows how to send a message with the Bot API 9.5 'date_time' entity.
# Telegram clients will render the selected text range as a localized date and time.

import time

import telebot
from telebot import types


API_TOKEN = '<api_token>'
bot = telebot.TeleBot(API_TOKEN)


@bot.message_handler(commands=['date_time'])
def send_date_time(message):
    unix_time = int(time.time()) + 3600
    text = 'Reminder'
    entity = types.MessageEntity(
        type='date_time',
        offset=0,
        length=len(text),
        unix_time=unix_time,
        date_time_format='Dt'
    )

    bot.send_message(message.chat.id, text, entities=[entity])


bot.infinity_polling()
