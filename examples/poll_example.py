#!/usr/bin/python

# This is an example file to create quiz polls
import telebot

API_TOKEN = "<api_token>"

bot = telebot.TeleBot(API_TOKEN)


@bot.message_handler(commands=["poll"])
def create_poll(message):
    bot.send_message(message.chat.id, "English Article Test")
    answer_options = ["a", "an", "the", "-"]

    bot.send_poll(
        chat_id=message.chat.id,
        question="We are going to '' park.",
        options=answer_options,
        type='quiz',
        correct_option_id=2,
        is_anonymous=False,
    )



bot.infinity_polling()
