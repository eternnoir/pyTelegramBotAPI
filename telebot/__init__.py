# -*- coding: utf-8 -*-

import apihelper
import json
import types
import time
import threading

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
        self.update_entries = {}
        self.update_listener = []
        self.chat_list = {}
        self.update_id_list = []
        self.max_message_size = 100000
        self.polling_thread = None
        self.__stop_polling = False
        self.interval = 3

    def get_update(self):
        result = apihelper.get_updates(self.token)
        if result['ok'] is not True:
            raise Exception('getMe Error.' + json.dumps(result))
        updates = result['result']
        notify_updates = []
        for update in updates:
            if update['update_id'] in self.update_entries:
                continue
            msg = types.Message.de_json(json.dumps(update['message']))
            self.__append_message_to_cache(update['update_id'], msg)
            notify_updates.append(msg)
        self.__notify_update(notify_updates)

    def __append_message_to_cache(self, update_id, message):
        # over buffer size
        if len(self.update_id_list) > self.max_message_size:
            # remove oldest element.
            upid = self.update_id_list[0]
            if upid in self.update_entries:
                del self.update_entries[upid]
        self.update_entries[update_id] = message
        self.update_id_list.append(update_id)

    def __notify_update(self, new_messages):
        for listener in self.update_listener:
            t = threading.Thread(target=listener, args=(new_messages))
            t.start()

    def polling(self, interval=3):
        """
        Always get updates.
        :param interval: iterval secs.
        :return:
        """
        self.interval = interval
        # clear thread.
        self.__stop_polling = True
        time.sleep(interval + 1)
        self.__stop_polling = False
        self.polling_thread = threading.Thread(target=self.__polling, args=())
        self.polling_thread.start()

    def __polling(self):
        print 'telegram bot start polling'
        while not self.__stop_polling:
            self.get_update()
            time.sleep(self.interval)

        print 'telegram bot stop polling'

    def stop_polling(self):
        self.__stop_polling = True

    def set_update_listener(self, listener):
        self.update_listener.append(listener)

    def get_me(self):
        result = apihelper.get_me(self.token)
        if result['ok'] is not True:
            raise Exception('getMe Error.' + json.dumps(result))
        u = types.User.de_json(json.dumps(result['result']))
        return u

    def send_message(self, chat_id, text, disable_web_page_preview=None, reply_to_message_id=None, reply_markup=None):
        return apihelper.send_message(self.token, chat_id, text, disable_web_page_preview, reply_to_message_id,
                                      reply_markup)

    def forward_message(self, chat_id, from_chat_id, message_id):
        """

        :param chat_id: which chat to forward
        :param from_chat_id: which chat message from
        :param message_id: message id
        :return:
        """
        return apihelper.forward_message(self.token, chat_id, from_chat_id, message_id)
