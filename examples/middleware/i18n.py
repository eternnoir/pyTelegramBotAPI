#!/usr/bin/python

# This example shows how to implement i18n (internationalization) l10n (localization) to create
# multi-language bots with middleware handler.
#
# Note: For the sake of simplicity of this example no extra library is used. However, it is recommended to use
# better i18n systems (gettext and etc) for handling multilingual translations.
# This is not a working, production-ready sample and it is highly recommended not to use it in production.
#
# In this example let's imagine we want to introduce localization or internationalization into our project and
# we need some global function to activate the language once and to use that language in all other message
# handler functions for not repeatedly activating it.
# The middleware (i18n and l10n) is explained:

import telebot
from telebot import apihelper

apihelper.ENABLE_MIDDLEWARE = True

TRANSLATIONS = {
    'hello': {
        'en': 'hello',
        'ru': 'привет',
        'uz': 'salom'
    }
}

_lang = 'en'


def activate(lang):
    global _lang
    _lang = lang


def _(string):
    return TRANSLATIONS[string][_lang]


bot = telebot.TeleBot('TOKEN')


@bot.middleware_handler(update_types=['message'])
def activate_language(bot_instance, message):
    activate(message.from_user.language_code)


@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id, _('hello'))


bot.polling()
