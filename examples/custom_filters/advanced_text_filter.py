# -*- coding: utf-8 -*-
"""
This Example will show you usage of TextFilter
In this example you will see how to use TextFilter
with (message_handler, callback_query_handler, poll_handler)
"""

from telebot import TeleBot, types
from telebot.custom_filters import TextFilter, TextMatchFilter, IsReplyFilter

bot = TeleBot("")


@bot.message_handler(text=TextFilter(equals='hello'))
def hello_handler(message: types.Message):
    bot.send_message(message.chat.id, message.text)


@bot.message_handler(text=TextFilter(equals='hello', ignore_case=True))
def hello_handler_ignore_case(message: types.Message):
    bot.send_message(message.chat.id, message.text + ' ignore case')


@bot.message_handler(text=TextFilter(contains=['good', 'bad']))
def contains_handler(message: types.Message):
    bot.send_message(message.chat.id, message.text)


@bot.message_handler(text=TextFilter(contains=['good', 'bad'], ignore_case=True))
def contains_handler_ignore_case(message: types.Message):
    bot.send_message(message.chat.id, message.text + ' ignore case')


@bot.message_handler(text=TextFilter(starts_with='st'))  # stArk, steve, stONE
def starts_with_handler(message: types.Message):
    bot.send_message(message.chat.id, message.text)


@bot.message_handler(text=TextFilter(starts_with='st', ignore_case=True))  # STark, sTeve, stONE
def starts_with_handler_ignore_case(message: types.Message):
    bot.send_message(message.chat.id, message.text + ' ignore case')


@bot.message_handler(text=TextFilter(ends_with='ay'))  # wednesday, SUNday, WeekDay
def ends_with_handler(message: types.Message):
    bot.send_message(message.chat.id, message.text)


@bot.message_handler(text=TextFilter(ends_with='ay', ignore_case=True))  # wednesdAY, sundAy, WeekdaY
def ends_with_handler_ignore_case(message: types.Message):
    bot.send_message(message.chat.id, message.text + ' ignore case')


@bot.message_handler(text=TextFilter(equals='/callback'))
def send_callback(message: types.Message):
    keyboard = types.InlineKeyboardMarkup(
        keyboard=[
            [types.InlineKeyboardButton(text='callback data', callback_data='example')],
            [types.InlineKeyboardButton(text='ignore case callback data', callback_data='ExAmPLe')]
        ]
    )
    bot.send_message(message.chat.id, message.text, reply_markup=keyboard)


@bot.callback_query_handler(func=None, text=TextFilter(equals='example'))
def callback_query_handler(call: types.CallbackQuery):
    bot.answer_callback_query(call.id, call.data, show_alert=True)


@bot.callback_query_handler(func=None, text=TextFilter(equals='example', ignore_case=True))
def callback_query_handler_ignore_case(call: types.CallbackQuery):
    bot.answer_callback_query(call.id, call.data + " ignore case", show_alert=True)


@bot.message_handler(text=TextFilter(equals='/poll'))
def send_poll(message: types.Message):
    bot.send_poll(message.chat.id, question='When do you prefer to work?', options=['Morning', 'Night'])
    bot.send_poll(message.chat.id, question='WHEN DO you pRefeR to worK?', options=['Morning', 'Night'])


@bot.poll_handler(func=None, text=TextFilter(equals='When do you prefer to work?'))
def poll_question_handler(poll: types.Poll):
    print(poll.question)


@bot.poll_handler(func=None, text=TextFilter(equals='When do you prefer to work?', ignore_case=True))
def poll_question_handler_ignore_case(poll: types.Poll):
    print(poll.question + ' ignore case')


# either hi or contains one of (привет, salom)
@bot.message_handler(text=TextFilter(equals="hi", contains=('привет', 'salom'), ignore_case=True))
def multiple_patterns_handler(message: types.Message):
    bot.send_message(message.chat.id, message.text)


# starts with one of (mi, mea) for ex. minor, milk, meal, meat
@bot.message_handler(text=TextFilter(starts_with=['mi', 'mea'], ignore_case=True))
def multiple_starts_with_handler(message: types.Message):
    bot.send_message(message.chat.id, message.text)


# ends with one of (es, on) for ex. Jones, Davies, Johnson, Wilson
@bot.message_handler(text=TextFilter(ends_with=['es', 'on'], ignore_case=True))
def multiple_ends_with_handler(message: types.Message):
    bot.send_message(message.chat.id, message.text)


# !ban /ban .ban !бан /бан .бан
@bot.message_handler(is_reply=True,
                     text=TextFilter(starts_with=('!', '/', '.'), ends_with=['ban', 'бан'], ignore_case=True))
def ban_command_handler(message: types.Message):
    if len(message.text) == 4 and message.chat.type != 'private':
        try:
            bot.ban_chat_member(message.chat.id, message.reply_to_message.from_user.id)
            bot.reply_to(message.reply_to_message, 'Banned.')
        except Exception as err:
            print(err.args)
            return


if __name__ == '__main__':
    bot.add_custom_filter(TextMatchFilter())
    bot.add_custom_filter(IsReplyFilter())
    bot.infinity_polling()
