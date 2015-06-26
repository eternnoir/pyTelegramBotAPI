# -*- coding: utf-8 -*-

import apihelper
import json
import types

"""
Module : telebot
"""

API_URL = r"https://api.telegram.org/"


class TeleBot:
    """ This is TeleBot Class
    Methods:
        getMe
        sendMessage
        forwardMessage
        sendPhoto
        sendAudio
        sendDocument
        sendSticker
        sendVideo
        sendLocation
        sendChatAction
        getUserProfilePhotos
        getUpdates
        setWebhook
    """

    def __init__(self, token):
        self.token = token

    def get_me(self):
        result = apihelper.get_me(self.token)
        if result['ok'] is not True:
            raise Exception('getMe Error.'+json.dumps(result))
        u = types.User.de_json(json.dumps(result['result']))
        return u

    def send_message(self, chat_id, text, disable_web_page_preview=None, reply_to_message_id=None, reply_markup=None):
        return apihelper.send_message(self.token, chat_id, text, disable_web_page_preview, reply_to_message_id,
                                      reply_markup)
