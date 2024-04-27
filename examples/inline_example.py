# This example show how to write an inline mode telegram bot use pyTelegramBotAPI.
import logging
import sys
import time

import telebot
from telebot.types import (
    InlineQueryResultArticle,
    InputTextMessageContent,
    InlineQueryResultPhoto,
    InlineQueryResultVideo,
)

bot = telebot.TeleBot("TOKEN")
telebot.logger.setLevel(logging.DEBUG)


@bot.inline_handler(lambda query: query.query == "text")
def query_text(inline_query):
    try:
        r = InlineQueryResultArticle(
            "1", "Result1", InputTextMessageContent("hi")
        )
        r2 = InlineQueryResultArticle(
            "2", "Result2", InputTextMessageContent("hi")
        )
        bot.answer_inline_query(inline_query.id, [r, r2])
    except Exception as e:
        print(e)


@bot.inline_handler(lambda query: query.query == "photo1")
def query_photo(inline_query):
    try:
        r = InlineQueryResultPhoto(
            "1",
            "https://raw.githubusercontent.com/eternnoir/pyTelegramBotAPI/master/examples/detailed_example/kitten.jpg",
            "https://raw.githubusercontent.com/eternnoir/pyTelegramBotAPI/master/examples/detailed_example/kitten.jpg",
            input_message_content=InputTextMessageContent("hi"),
        )
        r2 = InlineQueryResultPhoto(
            "2",
            "https://raw.githubusercontent.com/eternnoir/pyTelegramBotAPI/master/examples/detailed_example/rooster.jpg",
            "https://raw.githubusercontent.com/eternnoir/pyTelegramBotAPI/master/examples/detailed_example/rooster.jpg",
        )
        bot.answer_inline_query(inline_query.id, [r, r2], cache_time=1)
    except Exception as e:
        print(e)


@bot.inline_handler(lambda query: query.query == "video")
def query_video(inline_query):
    try:
        r = InlineQueryResultVideo(
            "1",
            "https://github.com/eternnoir/pyTelegramBotAPI/blob/master/tests/test_data/test_video.mp4?raw=true",
            "video/mp4",
            "https://raw.githubusercontent.com/eternnoir/pyTelegramBotAPI/master/examples/detailed_example/rooster.jpg",
            "Title",
        )
        bot.answer_inline_query(inline_query.id, [r])
    except Exception as e:
        print(e)


@bot.inline_handler(lambda query: len(query.query) == 0)
def default_query(inline_query):
    try:
        r = InlineQueryResultArticle(
            "1", "default", InputTextMessageContent("default")
        )
        bot.answer_inline_query(inline_query.id, [r])
    except Exception as e:
        print(e)


def main_loop():
    bot.infinity_polling()
    while 1:
        time.sleep(3)


if __name__ == "__main__":
    try:
        main_loop()
    except KeyboardInterrupt:
        print("\nExiting by user request.\n")
        sys.exit(0)
