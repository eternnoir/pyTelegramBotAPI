#!/usr/bin/python

# This example shows how to implement deep linking (https://core.telegram.org/bots#deep-linking)
# with the pyTelegramBotAPI.
# Note: This is not a working, production-ready sample.
#
# In this example we are connecting a user account on a website with a Telegram bot.
# Implementing this will enable you to push notifications (and other content) to your users' Telegram account.
# In this explanation the word 'database' can refer to any form of key-value storage.
# The deep linking explained:
#
# 1.	Let the user log in on an actual website with actual username-password authentication.
#
# 2. 	Generate a unique hashcode (we will call it unique_code)
#
# 3. 	Save unique_code->username to the database.
#
# 4. 	Show the user the URL https://telegram.me/YOURBOTNAME?start=unique_code
#
# 5. 	Now as soon as the user opens this URL in Telegram and presses 'Start',
#       your bot will receive a text message containing '/start unique_code',
#       where unique_code is of course replaced by the actual hashcode.
#
# 6. 	Let the bot retrieve the username by querying the database for unique_code.
#
# 7. 	Save chat_id->username to the database.
#
# 8. 	Now when your bot receives another message, it can query message.chat.id in the database
#       to check if the message is from this specific user. (And handle accordingly) or
#       you can push messages to the user using his chat id.
#
# Steps 1 to 4 will have to be implemented in a web server, using a language such as PHP, Python, C# or Java. These
# steps are not shown here. Only steps 5 to 7 are illustrated, some in pseudo-code, with this example.

import telebot

bot = telebot.TeleBot('TOKEN')


def extract_unique_code(text):
    # Extracts the unique_code from the sent /start command.
    return text.split()[1] if len(text.split()) > 1 else None


def in_storage(unique_code):
    # (pseudo-code) Should check if a unique code exists in storage
    return True


def get_username_from_storage(unique_code):
    # (pseudo-code) Does a query to the storage, retrieving the associated username
    # Should be replaced by a real database-lookup.
    return "ABC" if in_storage(unique_code) else None


def save_chat_id(chat_id, username):
    # (pseudo-code) Save the chat_id->username to storage
    # Should be replaced by a real database query.
    pass


@bot.message_handler(commands=['start'])
def send_welcome(message):
    unique_code = extract_unique_code(message.text)
    if unique_code:  # if the '/start' command contains a unique_code
        username = get_username_from_storage(unique_code)
        if username:  # if the username exists in our database
            save_chat_id(message.chat.id, username)
            reply = "Hello {0}, how are you?".format(username)
        else:
            reply = "I have no clue who you are..."
    else:
        reply = "Please visit me via a provided URL from the website."
    bot.reply_to(message, reply)


bot.polling()
