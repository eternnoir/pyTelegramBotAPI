# -*- coding: utf-8 -*-
from __future__ import print_function

import threading
import time
import re
import sys
import six

import logging

logger = logging.getLogger('TeleBot')
formatter = logging.Formatter('%(asctime)s (%(filename)s:%(lineno)d) %(levelname)s - %(name)s: "%(message)s"')

console_output_handler = logging.StreamHandler(sys.stderr)
console_output_handler.setFormatter(formatter)
logger.addHandler(console_output_handler)

logger.setLevel(logging.ERROR)

from telebot import apihelper, types, util

"""
Module : telebot
"""


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
    """

    def __init__(self, token, create_threads=True, num_threads=4):
        """
        :param token: bot API token
        :param create_threads: Create thread for message handler
        :param num_threads: Number of worker in thread pool.
        :return: Telebot object.
        """
        self.token = token
        self.update_listener = []
        self.polling_thread = None
        self.__stop_polling = threading.Event()
        self.last_update_id = 0
        self.num_threads = num_threads
        self.__create_threads = create_threads

        self.message_subscribers_messages = []
        self.message_subscribers_callbacks = []
        self.message_subscribers_lock = threading.Lock()

        # key: chat_id, value: handler list
        self.message_subscribers_next_step = {}

        self.message_handlers = []
        if self.__create_threads:
            self.worker_pool = util.ThreadPool(num_threads)

    def get_updates(self, offset=None, limit=None, timeout=20):
        """
        Use this method to receive incoming updates using long polling (wiki). An Array of Update objects is returned.
        :param offset: Integer. Identifier of the first update to be returned.
        :param limit: Integer. Limits the number of updates to be retrieved.
        :param timeout: Integer. Timeout in seconds for long polling.
        :return: array of Updates
        """
        json_updates = apihelper.get_updates(self.token, offset, limit, timeout)
        ret = []
        for ju in json_updates:
            ret.append(types.Update.de_json(ju))
        return ret

    def get_update(self, timeout=20):
        """
        Retrieves any updates from the Telegram API.
        Registered listeners and applicable message handlers will be notified when a new message arrives.
        :raises ApiException when a call has failed.
        """
        updates = self.get_updates(offset=(self.last_update_id + 1), timeout=timeout)
        new_messages = []
        for update in updates:
            if update.update_id > self.last_update_id:
                self.last_update_id = update.update_id
            new_messages.append(update.message)
        logger.debug('Received {0} new messages'.format(len(new_messages)))
        if len(new_messages) > 0:
            self.process_new_messages(new_messages)

    def process_new_messages(self, new_messages):
        self.__notify_update(new_messages)
        self._notify_command_handlers(new_messages)
        self._notify_message_subscribers(new_messages)
        self._notify_message_next_handler(new_messages)

    def __notify_update(self, new_messages):
        for listener in self.update_listener:
            if self.__create_threads:
                self.worker_pool.put(listener, new_messages)
            else:
                listener(new_messages)

    def polling(self, none_stop=False, interval=0, block=True, timeout=20):
        """
        This function creates a new Thread that calls an internal __polling function.
        This allows the bot to retrieve Updates automagically and notify listeners and message handlers accordingly.

        Do not call this function more than once!

        Always get updates.
        :param none_stop: Do not stop polling when Exception occur.
        :param timeout: Timeout in seconds for long polling.
        :return:
        """
        self.__stop_polling.set()
        if self.polling_thread:
            self.polling_thread.join()  # wait thread stop.
        self.__stop_polling.clear()
        self.polling_thread = threading.Thread(target=self.__polling, args=([none_stop, interval, timeout]))
        self.polling_thread.daemon = True
        self.polling_thread.start()

        if block:
            while self.polling_thread.is_alive:
                try:
                    time.sleep(.1)
                except KeyboardInterrupt:
                    logger.info("Received KeyboardInterrupt. Stopping.")
                    self.stop_polling()
                    self.polling_thread.join()
                    break

    def __polling(self, none_stop, interval, timeout):
        logger.info('Started polling.')

        error_interval = .25
        while not self.__stop_polling.wait(interval):
            try:
                self.get_update(timeout)
                error_interval = .25
            except apihelper.ApiException as e:
                if not none_stop:
                    self.__stop_polling.set()
                    logger.info("Exception occurred. Stopping.")
                else:
                    time.sleep(error_interval)
                    error_interval *= 2
                logger.error(e)

        logger.info('Stopped polling.')

    def stop_polling(self):
        self.__stop_polling.set()

    def set_update_listener(self, listener):
        self.update_listener.append(listener)

    def get_me(self):
        result = apihelper.get_me(self.token)
        return types.User.de_json(result)

    def get_file(self, file_id):
        return types.File.de_json(apihelper.get_file(self.token, file_id))

    def download_file(self, file_path):
        return apihelper.download_file(self.token, file_path)

    def get_user_profile_photos(self, user_id, offset=None, limit=None):
        """
        Retrieves the user profile photos of the person with 'user_id'
        See https://core.telegram.org/bots/api#getuserprofilephotos
        :param user_id:
        :param offset:
        :param limit:
        :return: API reply.
        """
        result = apihelper.get_user_profile_photos(self.token, user_id, offset, limit)
        return types.UserProfilePhotos.de_json(result)

    def send_message(self, chat_id, text, disable_web_page_preview=None, reply_to_message_id=None, reply_markup=None,
                     parse_mode=None):
        """
        Use this method to send text messages.

        Warning: Do not send more than about 5000 characters each message, otherwise you'll risk an HTTP 414 error.
        If you must send more than 5000 characters, use the split_string function in apihelper.py.

        :param chat_id:
        :param text:
        :param disable_web_page_preview:
        :param reply_to_message_id:
        :param reply_markup:
        :param parse_mode:
        :return: API reply.
        """
        return types.Message.de_json(
            apihelper.send_message(self.token, chat_id, text, disable_web_page_preview, reply_to_message_id,
                                   reply_markup, parse_mode))

    def forward_message(self, chat_id, from_chat_id, message_id):
        """
        Use this method to forward messages of any kind.
        :param chat_id: which chat to forward
        :param from_chat_id: which chat message from
        :param message_id: message id
        :return: API reply.
        """
        return types.Message.de_json(apihelper.forward_message(self.token, chat_id, from_chat_id, message_id))

    def send_photo(self, chat_id, photo, caption=None, reply_to_message_id=None, reply_markup=None):
        """
        Use this method to send photos.
        :param chat_id:
        :param photo:
        :param caption:
        :param reply_to_message_id:
        :param reply_markup:
        :return: API reply.
        """
        return types.Message.de_json(
            apihelper.send_photo(self.token, chat_id, photo, caption, reply_to_message_id, reply_markup))

    def send_audio(self, chat_id, audio, duration=None, performer=None, title=None, reply_to_message_id=None,
                   reply_markup=None):
        """
        Use this method to send audio files, if you want Telegram clients to display them in the music player. Your audio must be in the .mp3 format.
        :param chat_id:Unique identifier for the message recipient
        :param audio:Audio file to send.
        :param duration:Duration of the audio in seconds
        :param performer:Performer
        :param title:Track name
        :param reply_to_message_id:If the message is a reply, ID of the original message
        :param reply_markup:
        :return: Message
        """
        return types.Message.de_json(
            apihelper.send_audio(self.token, chat_id, audio, duration, performer, title, reply_to_message_id,
                                 reply_markup))

    def send_voice(self, chat_id, voice, duration=None, reply_to_message_id=None, reply_markup=None):
        """
        Use this method to send audio files, if you want Telegram clients to display the file as a playable voice message.
        :param chat_id:Unique identifier for the message recipient.
        :param voice:
        :param duration:Duration of sent audio in seconds
        :param reply_to_message_id:
        :param reply_markup:
        :return: Message
        """
        return types.Message.de_json(
            apihelper.send_voice(self.token, chat_id, voice, duration, reply_to_message_id, reply_markup))

    def send_document(self, chat_id, data, reply_to_message_id=None, reply_markup=None):
        """
        Use this method to send general files.
        :param chat_id:
        :param data:
        :param reply_to_message_id:
        :param reply_markup:
        :return: API reply.
        """
        return types.Message.de_json(
            apihelper.send_data(self.token, chat_id, data, 'document', reply_to_message_id, reply_markup))

    def send_sticker(self, chat_id, data, reply_to_message_id=None, reply_markup=None):
        """
        Use this method to send .webp stickers.
        :param chat_id:
        :param data:
        :param reply_to_message_id:
        :param reply_markup:
        :return: API reply.
        """
        return types.Message.de_json(
            apihelper.send_data(self.token, chat_id, data, 'sticker', reply_to_message_id, reply_markup))

    def send_video(self, chat_id, data, duration=None, caption=None, reply_to_message_id=None, reply_markup=None):
        """
        Use this method to send video files, Telegram clients support mp4 videos.
        :param chat_id: Integer : Unique identifier for the message recipient — User or GroupChat id
        :param data: InputFile or String : Video to send. You can either pass a file_id as String to resend a video that is already on the Telegram server
        :param duration: Integer : Duration of sent video in seconds
        :param caption: String : Video caption (may also be used when resending videos by file_id).
        :param reply_to_message_id:
        :param reply_markup:
        :return:
        """
        return types.Message.de_json(
            apihelper.send_video(self.token, chat_id, data, duration, caption, reply_to_message_id, reply_markup))

    def send_location(self, chat_id, latitude, longitude, reply_to_message_id=None, reply_markup=None):
        """
        Use this method to send point on the map.
        :param chat_id:
        :param latitude:
        :param longitude:
        :param reply_to_message_id:
        :param reply_markup:
        :return: API reply.
        """
        return types.Message.de_json(
            apihelper.send_location(self.token, chat_id, latitude, longitude, reply_to_message_id, reply_markup))

    def send_chat_action(self, chat_id, action):
        """
        Use this method when you need to tell the user that something is happening on the bot's side.
        The status is set for 5 seconds or less (when a message arrives from your bot, Telegram clients clear
        its typing status).
        :param chat_id:
        :param action:  One of the following strings: 'typing', 'upload_photo', 'record_video', 'upload_video',
                        'record_audio', 'upload_audio', 'upload_document', 'find_location'.
        :return: API reply. :type: boolean
        """
        return apihelper.send_chat_action(self.token, chat_id, action)

    def reply_to(self, message, text, **kwargs):
        """
        Convenience function for `send_message(message.chat.id, text, reply_to_message_id=message.message_id, **kwargs)`
        """
        return self.send_message(message.chat.id, text, reply_to_message_id=message.message_id, **kwargs)

    def register_for_reply(self, message, callback):
        """
        Registers a callback function to be notified when a reply to `message` arrives.

        Warning: `message` must be sent with reply_markup=types.ForceReply(), otherwise TeleBot will not be able to see
        the difference between a reply to `message` and an ordinary message.

        :param message:     The message for which we are awaiting a reply.
        :param callback:    The callback function to be called when a reply arrives. Must accept one `message`
                            parameter, which will contain the replied message.
        """
        with self.message_subscribers_lock:
            self.message_subscribers_messages.insert(0, message.message_id)
            self.message_subscribers_callbacks.insert(0, callback)
            if len(self.message_subscribers_messages) > 10000:
                self.message_subscribers_messages.pop()
                self.message_subscribers_callbacks.pop()

    def _notify_message_subscribers(self, new_messages):
        for message in new_messages:
            if not hasattr(message, 'reply_to_message'):
                continue

            reply_msg_id = message.reply_to_message.message_id
            if reply_msg_id in self.message_subscribers_messages:
                index = self.message_subscribers_messages.index(reply_msg_id)
                self.message_subscribers_callbacks[index](message)

                with self.message_subscribers_lock:
                    index = self.message_subscribers_messages.index(reply_msg_id)
                    del self.message_subscribers_messages[index]
                    del self.message_subscribers_callbacks[index]

    def register_next_step_handler(self, message, callback):
        """
        Registers a callback function to be notified when new message arrives after `message`.

        :param message:     The message for which we want to handle new message after that in same chat.
        :param callback:    The callback function which next new message arrives.
        """
        chat_id = message.chat.id
        if chat_id in self.message_subscribers_next_step:
            self.message_subscribers_next_step[chat_id].append(callback)
        else:
            self.message_subscribers_next_step[chat_id] = [callback]

    def _notify_message_next_handler(self, new_messages):
        for message in new_messages:
            chat_id = message.chat.id
            if chat_id in self.message_subscribers_next_step:
                handlers = self.message_subscribers_next_step[chat_id]
                for handler in handlers:
                    self.worker_pool.put(handler, message)
                self.message_subscribers_next_step.pop(chat_id, None)

    def message_handler(self, commands=None, regexp=None, func=None, content_types=['text']):
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
        """

        def decorator(fn):
            handler_dict = {'function': fn}
            filters = {'content_types': content_types}
            if regexp:
                filters['regexp'] = regexp
            if func:
                filters['lambda'] = func
            if commands:
                filters['commands'] = commands
            handler_dict['filters'] = filters
            self.message_handlers.append(handler_dict)
            return fn

        return decorator

    @staticmethod
    def _test_message_handler(message_handler, message):
        for filter, filter_value in six.iteritems(message_handler['filters']):
            if not TeleBot._test_filter(filter, filter_value, message):
                return False
        return True

    @staticmethod
    def _test_filter(filter, filter_value, message):
        if filter == 'content_types':
            return message.content_type in filter_value
        if filter == 'regexp':
            return message.content_type == 'text' and re.search(filter_value, message.text)
        if filter == 'commands':
            return message.content_type == 'text' and util.extract_command(message.text) in filter_value
        if filter == 'lambda':
            return filter_value(message)
        return False

    def _notify_command_handlers(self, new_messages):
        for message in new_messages:
            for message_handler in self.message_handlers:
                if self._test_message_handler(message_handler, message):
                    if self.__create_threads:
                        self.worker_pool.put(message_handler['function'], message)
                    else:
                        message_handler['function'](message)
                    break


class AsyncTeleBot(TeleBot):
    def __init__(self, *args, **kwargs):
        TeleBot.__init__(self, *args, **kwargs)

    @util.async()
    def get_me(self):
        return TeleBot.get_me(self)

    @util.async()
    def get_user_profile_photos(self, *args, **kwargs):
        return TeleBot.get_user_profile_photos(self, *args, **kwargs)

    @util.async()
    def send_message(self, *args, **kwargs):
        return TeleBot.send_message(self, *args, **kwargs)

    @util.async()
    def forward_message(self, *args, **kwargs):
        return TeleBot.forward_message(self, *args, **kwargs)

    @util.async()
    def send_photo(self, *args, **kwargs):
        return TeleBot.send_photo(self, *args, **kwargs)

    @util.async()
    def send_audio(self, *args, **kwargs):
        return TeleBot.send_audio(self, *args, **kwargs)

    @util.async()
    def send_document(self, *args, **kwargs):
        return TeleBot.send_document(self, *args, **kwargs)

    @util.async()
    def send_sticker(self, *args, **kwargs):
        return TeleBot.send_sticker(self, *args, **kwargs)

    @util.async()
    def send_video(self, *args, **kwargs):
        return TeleBot.send_video(self, *args, **kwargs)

    @util.async()
    def send_location(self, *args, **kwargs):
        return TeleBot.send_location(self, *args, **kwargs)

    @util.async()
    def send_chat_action(self, *args, **kwargs):
        return TeleBot.send_chat_action(self, *args, **kwargs)
