#!/usr/bin/python

# This is an example file to create polls and handle poll answers
import telebot

API_TOKEN = "<api_token>"

bot = telebot.TeleBot(API_TOKEN)


DATA = {}


@bot.message_handler(commands=["poll"])
def create_poll(message):
    bot.send_message(message.chat.id, "English Article Test")
    answer_options = ["a", "an", "the", "-"]

    # is_anonymous = False -- if you want to check the user answer like here
    poll = bot.send_poll(
        chat_id=message.chat.id,
        question="We are going to '' park.",
        options=answer_options,
        is_anonymous=False,
    )

    # store the poll_id against user_id in the database
    poll_id = poll.poll.id
    DATA[message.chat.id] = poll_id


@bot.poll_answer_handler()
def handle_poll_answers(poll):

    if DATA.get(poll.user.id) == poll.poll_id:
        # to check the correct answer
        user_answer = poll.option_ids[0]
        correct_answer = 2  # "the" is the correct answer
        if user_answer == correct_answer:
            bot.send_message(poll.user.id, "Good! You're right.")
        else:
            bot.send_message(poll.user.id, 'The correct answer is "the" .')


bot.infinity_polling()
