# -*- coding: utf-8 -*-

import telebot # https://github.com/eternnoir/pyTelegramBotAPI
from telebot import types
import random
import string

bot = telebot.TeleBot('your_token')

markup = types.InlineKeyboardMarkup()
item_text = types.InlineKeyboardButton('Generate password', callback_data="password")
item_num = types.InlineKeyboardButton('Generate PIN', callback_data="pin")
markup.row(item_text, item_num)


@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id, "*Hi there!*\nPress one of the buttons to generate a *password* or a *PIN*.",
                     reply_markup=markup, parse_mode='Markdown')


@bot.callback_query_handler(func=lambda call: call.data == 'password')
def btn_pass(call):
    symbols = string.ascii_letters + string.digits
    text = ''.join(random.choice(symbols) for _ in range(8))
    bot.edit_message_text(text, call.from_user.id, call.message.message_id, reply_markup=markup)
    bot.answer_callback_query(call.id, text="Password is generated")


@bot.callback_query_handler(func=lambda call: call.data == 'pin')
def btn_pin(call):
    symbols = string.digits
    text = ''.join(random.choice(symbols) for _ in range(4))
    bot.edit_message_text(text, call.from_user.id, call.message.message_id, reply_markup=markup)
    bot.answer_callback_query(call.id, text="PIN is generated")


if __name__ == "__main__":
    bot.polling(True)
