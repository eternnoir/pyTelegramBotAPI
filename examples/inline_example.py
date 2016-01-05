# This example show how to write an inline mode telegramt bot use pyTelegramBotAPI.
import telebot
import time
import sys
import logging
from telebot import types

API_TOKEN = '<api_token>'

bot = telebot.TeleBot(API_TOKEN)
telebot.logger.setLevel(logging.DEBUG)


@bot.inline_handler(lambda query: query.query == 'text')
def query_text(inline_query):
    try:
        r = types.InlineQueryResultArticle('1', 'Result', inline_query.query)
        r2 = types.InlineQueryResultArticle('2', 'Result2', inline_query.query)
        bot.answer_inline_query(inline_query.id, [r, r2])
    except Exception as e:
        print(e)


@bot.inline_handler(lambda query: query.query == 'photo')
def query_photo(inline_query):
    try:
        r = types.InlineQueryResultPhoto('1',
                                         'https://raw.githubusercontent.com/eternnoir/pyTelegramBotAPI/master/examples/detailed_example/kitten.jpg',
                                         thumb_url='https://raw.githubusercontent.com/eternnoir/pyTelegramBotAPI/master/examples/detailed_example/kitten.jpg')
        r2 = types.InlineQueryResultPhoto('2',
                                          'https://raw.githubusercontent.com/eternnoir/pyTelegramBotAPI/master/examples/detailed_example/rooster.jpg',
                                          thumb_url='https://raw.githubusercontent.com/eternnoir/pyTelegramBotAPI/master/examples/detailed_example/rooster.jpg')
        bot.answer_inline_query(inline_query.id, [r, r2])
    except Exception as e:
        print(e)


@bot.inline_handler(lambda query: len(query.query) is 0)
def default_query(inline_query):
    try:
        r = types.InlineQueryResultArticle('1', 'default', 'default')
        bot.answer_inline_query(inline_query.id, [r])
    except Exception as e:
        print(e)


def main_loop():
    bot.polling(True)
    while 1:
        time.sleep(3)


if __name__ == '__main__':
    try:
        main_loop()
    except KeyboardInterrupt:
        print >> sys.stderr, '\nExiting by user request.\n'
        sys.exit(0)
