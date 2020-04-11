#!/usr/bin/python

# This example shows how to implement session creation and retrieval based on user id with middleware handler.
#
# Note: For the sake of simplicity of this example no extra library is used. However, it is recommended to use
# in-memory or on-disk storage implementations (redis, mysql, postgres and etc) for storing and retrieving structures.
# This is not a working, production-ready sample and it is highly recommended not to use it in production.
#
# In this example let's imagine we want to create a session for each user who communicates with the bot to store
# different kind of temporary data while session is active. As an example we want to track the state of the user
# with the help of this session. So, we need a way to store this session data somewhere globally to enable other
# message handler functions to be able to use it.
# The middleware session is explained:

import telebot
from telebot import apihelper

apihelper.ENABLE_MIDDLEWARE = True

INFO_STATE = 'ON_INFO_MENU'
MAIN_STATE = 'ON_MAIN_MENU'

SESSIONS = {
    -10000: {
        'state': INFO_STATE
    },
    -11111: {
        'state': MAIN_STATE
    }
}


def get_or_create_session(user_id):
    try:
        return SESSIONS[user_id]
    except KeyError:
        SESSIONS[user_id] = {'state': MAIN_STATE}
        return SESSIONS[user_id]


bot = telebot.TeleBot('TOKEN')


@bot.middleware_handler(update_types=['message'])
def set_session(bot_instance, message):
    bot_instance.session = get_or_create_session(message.from_user.id)


@bot.message_handler(commands=['start'])
def start(message):
    bot.session['state'] = MAIN_STATE
    bot.send_message(message.chat.id, bot.session['state'])


@bot.message_handler(commands=['info'])
def start(message):
    bot.session['state'] = INFO_STATE
    bot.send_message(message.chat.id, bot.session['state'])


bot.polling()
