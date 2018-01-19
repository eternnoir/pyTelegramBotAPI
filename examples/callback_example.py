import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

bot = telebot.TeleBot('Api Token')


@bot.message_handler(commands=['start'])
def handler(message):
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton('First Button', callback_data='first'))
    markup.add(InlineKeyboardButton('Second Button', callback_data='second'))

    bot.send_message(message.chat.id, 'Menu', reply_markup=markup)


@bot.callback_query_handler(lambda update: update.data == 'first')
def first_handler(update):
    bot.send_message(update.message.chat.id, 'First')
    bot.answer_callback_query(update.id)


@bot.callback_query_handler(lambda update: update.data == 'second')
def second_handler(update):
    bot.send_message(update.message.chat.id, 'Second')
    bot.answer_callback_query(update.id)


bot.polling()
