# -*- coding: utf-8 -*-
from __future__ import print_function

import time
import threading
import re

from telebot import apihelper, types

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
        self.update_listener = []
        self.polling_thread = None
        self.__stop_polling = False
        self.interval = 3

        self.last_update_id = 0

        self.commands = []

    def get_update(self):
        """
        Retrieves any updates from the Telegram API.
        Registered listeners and applicable message handlers will be notified when a new message arrives.
        :raises ApiException when a call has failed.
        """
        updates = apihelper.get_updates(self.token, offset=(self.last_update_id + 1))
        new_messages = []
        for update in updates:
            if update['update_id'] > self.last_update_id:
                self.last_update_id = update['update_id']
            msg = types.Message.de_json(update['message'])
            new_messages.append(msg)

        if len(new_messages) > 0:
            self.__notify_update(new_messages)
            self._notify_command_handlers(new_messages)

    def __notify_update(self, new_messages):
        for listener in self.update_listener:
            t = threading.Thread(target=listener, args=new_messages)
            t.start()

    def polling(self, interval=3):
        """
        Always get updates.
        :param interval: interval secs.
        :return:
        """
        self.interval = interval
        # clear thread.
        self.__stop_polling = True
        time.sleep(interval + 1)
        self.__stop_polling = False
        self.polling_thread = threading.Thread(target=self.__polling, args=())
        self.polling_thread.daemon = True
        self.polling_thread.start()

    def __polling(self):
        print('telegram bot start polling')
        while not self.__stop_polling:
            try:
                self.get_update()
            except Exception as e:
                print(e)
            time.sleep(self.interval)

        print('telegram bot stop polling')

    def stop_polling(self):
        self.__stop_polling = True

    def set_update_listener(self, listener):
        self.update_listener.append(listener)

    def get_me(self):
        result = apihelper.get_me(self.token)
        return types.User.de_json(result)

    def get_user_profile_photos(self, user_id, offset=None, limit=None):
        """
        Retrieves the user profile photos of the person with 'user_id'
        See https://core.telegram.org/bots/api#getuserprofilephotos
        :param user_id:
        :param offset:
        :param limit:
        :return:
        """
        result = apihelper.get_user_profile_photos(self.token, user_id, offset, limit)
        return types.UserProfilePhotos.de_json(result)

    def send_message(self, chat_id, text, disable_web_page_preview=None, reply_to_message_id=None, reply_markup=None):
        """
        Use this method to send text messages.
        :param chat_id:
        :param text:
        :param disable_web_page_preview:
        :param reply_to_message_id:
        :param reply_markup:
        :return:
        """
        return apihelper.send_message(self.token, chat_id, text, disable_web_page_preview, reply_to_message_id,
                                      reply_markup)

    def forward_message(self, chat_id, from_chat_id, message_id):
        """
        Use this method to forward messages of any kind.
        :param chat_id: which chat to forward
        :param from_chat_id: which chat message from
        :param message_id: message id
        :return:
        """
        return apihelper.forward_message(self.token, chat_id, from_chat_id, message_id)

    def send_photo(self, chat_id, photo, caption=None, reply_to_message_id=None, reply_markup=None):
        """
        Use this method to send photos.
        :param chat_id:
        :param photo:
        :param caption:
        :param reply_to_message_id:
        :param reply_markup:
        :return:
        """
        return apihelper.send_photo(self.token, chat_id, photo, caption, reply_to_message_id, reply_markup)

    def send_audio(self, chat_id, data, reply_to_message_id=None, reply_markup=None):
        """
        Use this method to send audio files, if you want Telegram clients to display the file as a playable
        voice message. For this to work, your audio must be in an .ogg file encoded with OPUS
        :param chat_id:
        :param data:
        :param reply_to_message_id:
        :param reply_markup:
        :return:
        """
        return apihelper.send_data(self.token, chat_id, data, 'audio', reply_to_message_id, reply_markup)

    def send_document(self, chat_id, data, reply_to_message_id=None, reply_markup=None):
        """
        Use this method to send general files.
        :param chat_id:
        :param data:
        :param reply_to_message_id:
        :param reply_markup:
        :return:
        """
        return apihelper.send_data(self.token, chat_id, data, 'document', reply_to_message_id, reply_markup)

    def send_sticker(self, chat_id, data, reply_to_message_id=None, reply_markup=None):
        """
        Use this method to send .webp stickers.
        :param chat_id:
        :param data:
        :param reply_to_message_id:
        :param reply_markup:
        :return:
        """
        return apihelper.send_data(self.token, chat_id, data, 'sticker', reply_to_message_id, reply_markup)

    def send_video(self, chat_id, data, reply_to_message_id=None, reply_markup=None):
        """
        Use this method to send video files, Telegram clients support mp4 videos.
        :param chat_id:
        :param data:
        :param reply_to_message_id:
        :param reply_markup:
        :return:
        """
        return apihelper.send_data(self.token, chat_id, data, 'video', reply_to_message_id, reply_markup)

    def send_location(self, chat_id, latitude, longitude, reply_to_message_id=None, reply_markup=None):
        """
        Use this method to send point on the map.
        :param chat_id:
        :param latitude:
        :param longitude:
        :param reply_to_message_id:
        :param reply_markup:
        :return:
        """
        return apihelper.send_location(self.token, chat_id, latitude, longitude, reply_to_message_id, reply_markup)

    def send_chat_action(self, chat_id, action):
        """
        Use this method when you need to tell the user that something is happening on the bot's side.
        The status is set for 5 seconds or less (when a message arrives from your bot, Telegram clients clear
        its typing status).
        :param chat_id:
        :param action: string . typing,upload_photo,record_video,upload_video,record_audio,upload_audio,upload_document,
                                find_location.
        :return:
        """
        return apihelper.send_chat_action(self.token, chat_id, action)

    def message_handler(self, regexp=None, func=None, content_types=['text']):
        """
        Message handler decorator.
        This decorator can be used to decorate functions that must handle certain types of messages.
        All message handlers are tested in the order they were added.

        Example:

        bot = TeleBot('TOKEN')

        # Handles all messages which text matches regexp.
        @bot.message_handler(regexp='someregexp')
        def command_help(message):
            bot.send_message(message.chat.id, 'Did someone call for help?')

        # Handle all sent documents of type 'text/plain'.
        @bot.message_handler(func=lambda message: message.document.mime_type == 'text/plain', content_types=['document'])
        def command_handle_document(message):
            bot.send_message(message.chat.id, 'Document received, sir!')

        # Handle all other commands.
        @bot.message_handler(func=lambda message: True, content_types=['audio', 'video', 'document', 'text', 'location', 'contact', 'sticker'])
        def default_command(message):
            bot.send_message(message.chat.id, "This is the default command handler.")

        :param regexp: Optional regular expression.
        :param func: Optional lambda function. The lambda receives the message to test as the first parameter. It must return True if the command should handle the message.
        :param content_types: This commands' supported content types. Must be a list. Defaults to ['text'].
        :return:
        """
        def decorator(fn):
            self.commands.append([fn, regexp, func, content_types])
            return fn
        return decorator

    @staticmethod
    def _test_command(command, message):
        if message.content_type not in command[3]:
            return False
        if command[1] is not None and message.content_type == 'text' and re.search(command[1], message.text):
            return True
        if command[2] is not None:
            return command[2](message)
        return False

    def _notify_command_handlers(self, new_messages):
        for message in new_messages:
            for command in self.commands:
                if self._test_command(command, message):
                    t = threading.Thread(target=command[0], args=(message,))
                    t.start()
                    break
