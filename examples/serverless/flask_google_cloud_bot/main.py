'''
Simple bot for Google cloud deployment.

Docs:
https://cloud.google.com/run/docs/quickstarts/build-and-deploy/deploy-python-service

1. Receive your bot's token from https://t.me/BotFather

2. Create a Google Cloud project. https://cloud.google.com/resource-manager/docs/creating-managing-projects

3. Install the Google Cloud CLI. https://cloud.google.com/sdk/docs/install

4. Move to telegram_google_cloud_bot folder

cd telegram_google_cloud_bot/

5. Initialize the gcloud CLI:

gcloud init

6. To set the default project for your Cloud Run service:

gcloud config set project PROJECT_ID

7. Deploy:

gcloud run deploy
'''

import os

from flask import Flask, request

import telebot

TOKEN = 'token_from_botfather'

bot = telebot.TeleBot(TOKEN)

app = Flask(__name__)


@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, 'Hello, ' + message.from_user.first_name)


@bot.message_handler(func=lambda message: True, content_types=['text'])
def echo_message(message):
    bot.reply_to(message, message.text)


@app.route('/' + TOKEN, methods=['POST'])
def getMessage():
    json_string = request.get_data().decode('utf-8')
    update = telebot.types.Update.de_json(json_string)
    bot.process_new_updates([update])
    return '!', 200


@app.route('/')
def webhook():
    bot.remove_webhook()
    bot.set_webhook(url='https://mydomain.com/' + TOKEN)
    return '!', 200