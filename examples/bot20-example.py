# -*- coding: utf-8 -*-
import telebot
from telebot import types
bot = telebot.TeleBot('your bot token')
        
@bot.callback_query_handler(func=lambda call: True)
def callback(call):
    if call.data == "{usd}":
        answer = 'Success USD'
        kb = types.InlineKeyboardMarkup()
        kb.add(types.InlineKeyboardButton("Success USD", callback_data='{usd}'))
        bot.edit_message_text(text=answer, message_id=call.message.message_id, chat_id=call.message.chat.id, parse_mode="HTML", reply_markup=kb)
    if call.data == "{eur}":
        answer = "Success EUR"
        kb = types.InlineKeyboardMarkup()
        kb.add(types.InlineKeyboardButton("Success EUR", callback_data='{eur}'))
        bot.edit_message_text(text=answer, message_id=call.message.message_id, chat_id=call.message.chat.id, parse_mode="HTML", reply_markup=kb)
@bot.message_handler(content_types=['text'])
def main(message):
    if message.text == "/test":
        cid = message.chat.id
        markup = types.InlineKeyboardMarkup()
        usd = types.InlineKeyboardButton(text="USD", callback_data="{usd}")
        eur = types.InlineKeyboardButton(text="EUR", callback_data="{eur}")
        markup.row(usd, eur)
        bot.send_message(cid, "Choose one currency:", reply_markup=markup)
    else:
        cid = message.chat.id
        bot.send_message(cid, "That command doesnt exist")
bot.polling(none_stop=True, interval=0)
