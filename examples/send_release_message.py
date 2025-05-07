#!/usr/bin/python

# This is a simple script that sends a message to a defined chat_id using GitHub Actions.
# It was created alongside action_release_message.yml

import telebot
import os

bot = telebot.TeleBot(os.environ.get('TOKEN'))
chat_id = os.environ.get('CHAT_ID')
release_tag = os.environ.get('RELEASE_TAG')
release_title = os.environ.get('RELEASE_TITLE')
release_body = os.environ.get('RELEASE_BODY')

message = (
    f'🎉 <b>{release_tag} - {release_title}</b>\n\n'
    f'🛠 Changes:\n'
    f'<b>{release_body}</b>\n\n'
    f'<a href="https://github.com/eternnoir/pyTelegramBotAPI/releases/tag/{release_tag}">Release</a>'
)

bot.send_message(
    chat_id,
    message,
    parse_mode='HTML',
    link_preview_options=telebot.types.LinkPreviewOptions(is_disabled=True)
)
