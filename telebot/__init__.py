# -*- coding: utf-8 -*-
from __future__ import print_function

import threading
import time
import re
import sys
import six

import logging

logger = logging.getLogger('TeleBot')
formatter = logging.Formatter(
    '%(asctime)s (%(filename)s:%(lineno)d %(threadName)s) %(levelname)s - %(name)s: "%(message)s"'
)

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

    def __init__(self, token, threaded=True, skip_pending=False):
        """
        :param token: bot API token
        :return: Telebot object.
        """
        self.token = token
        self.update_listener = []
        self.skip_pending = skip_pending

        self.__stop_polling = threading.Event()
        self.last_update_id = 0
        self.exc_info = None

        self.message_subscribers_messages = []
        self.message_subscribers_callbacks = []
        self.message_subscribers_lock = threading.Lock()

        # key: chat_id, value: handler list
        self.message_subscribers_next_step = {}
        self.pre_message_subscribers_next_step = {}

        self.message_handlers = []
        self.inline_handlers = []
        self.chosen_inline_handlers = []
        self.callback_query_handlers = []

        self.threaded = threaded
        if self.threaded:
            self.worker_pool = util.ThreadPool()

    def set_webhook(self, url=None, certificate=None):
        return apihelper.set_webhook(self.token, url, certificate)

    def remove_webhook(self):
        return self.set_webhook()  # No params resets webhook

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

    def __skip_updates(self):
        """
        Get and discard all pending updates before first poll of the bot
        :return: total updates skipped
        """
        total = 0
        updates = self.get_updates(offset=self.last_update_id, timeout=1)
        while updates:
            total += len(updates)
            for update in updates:
                if update.update_id > self.last_update_id:
                    self.last_update_id = update.update_id
            updates = self.get_updates(offset=self.last_update_id + 1, timeout=1)
        return total

    def __retrieve_updates(self, timeout=20):
        """
        Retrieves any updates from the Telegram API.
        Registered listeners and applicable message handlers will be notified when a new message arrives.
        :raises ApiException when a call has failed.
        """
        if self.skip_pending:
            logger.debug('Skipped {0} pending messages'.format(self.__skip_updates()))
            self.skip_pending = False
        updates = self.get_updates(offset=(self.last_update_id + 1), timeout=timeout)
        self.process_new_updates(updates)

    def process_new_updates(self, updates):
        new_messages = []
        new_inline_querys = []
        new_chosen_inline_results = []
        new_callback_querys = []
        for update in updates:
            if update.update_id > self.last_update_id:
                self.last_update_id = update.update_id
            if update.message:
                new_messages.append(update.message)
            if update.inline_query:
                new_inline_querys.append(update.inline_query)
            if update.chosen_inline_result:
                new_chosen_inline_results.append(update.chosen_inline_result)
            if update.callback_query:
                new_callback_querys.append(update.callback_query)
        logger.debug('Received {0} new updates'.format(len(updates)))
        if len(new_messages) > 0:
            self.process_new_messages(new_messages)
        if len(new_inline_querys) > 0:
            self.process_new_inline_query(new_inline_querys)
        if len(new_chosen_inline_results) > 0:
            self.process_new_chosen_inline_query(new_chosen_inline_results)
        if len(new_callback_querys) > 0:
            self.process_new_callback_query(new_callback_querys)

    def process_new_messages(self, new_messages):
        self._append_pre_next_step_handler()
        self.__notify_update(new_messages)
        self._notify_command_handlers(self.message_handlers, new_messages)
        self._notify_message_subscribers(new_messages)
        self._notify_message_next_handler(new_messages)

    def process_new_inline_query(self, new_inline_querys):
        self._notify_command_handlers(self.inline_handlers, new_inline_querys)

    def process_new_chosen_inline_query(self, new_chosen_inline_querys):
        self._notify_command_handlers(self.chosen_inline_handlers, new_chosen_inline_querys)

    def process_new_callback_query(self, new_callback_querys):
        self._notify_command_handlers(self.callback_query_handlers, new_callback_querys)

    def __notify_update(self, new_messages):
        for listener in self.update_listener:
            self.__exec_task(listener, new_messages)

    def polling(self, none_stop=False, interval=0, timeout=20):
        """
        This function creates a new Thread that calls an internal __retrieve_updates function.
        This allows the bot to retrieve Updates automagically and notify listeners and message handlers accordingly.

        Warning: Do not call this function more than once!

        Always get updates.
        :param none_stop: Do not stop polling when an ApiException occurs.
        :param timeout: Timeout in seconds for long polling.
        :return:
        """
        if self.threaded:
            self.__threaded_polling(none_stop, interval, timeout)
        else:
            self.__non_threaded_polling(none_stop, interval, timeout)

    def __threaded_polling(self, none_stop=False, interval=0, timeout=3):
        logger.info('Started polling.')
        self.__stop_polling.clear()
        error_interval = .25

        polling_thread = util.WorkerThread(name="PollingThread")
        or_event = util.OrEvent(
            polling_thread.done_event,
            polling_thread.exception_event,
            self.worker_pool.exception_event
        )

        while not self.__stop_polling.wait(interval):
            or_event.clear()
            try:
                polling_thread.put(self.__retrieve_updates, timeout)

                or_event.wait()  # wait for polling thread finish, polling thread error or thread pool error

                polling_thread.raise_exceptions()
                self.worker_pool.raise_exceptions()

                error_interval = .25
            except apihelper.ApiException as e:
                logger.error(e)
                if not none_stop:
                    self.__stop_polling.set()
                    logger.info("Exception occurred. Stopping.")
                else:
                    polling_thread.clear_exceptions()
                    self.worker_pool.clear_exceptions()
                    logger.info("Waiting for {0} seconds until retry".format(error_interval))
                    time.sleep(error_interval)
                    error_interval *= 2
            except KeyboardInterrupt:
                logger.info("KeyboardInterrupt received.")
                self.__stop_polling.set()
                polling_thread.stop()
                break

        logger.info('Stopped polling.')

    def __non_threaded_polling(self, none_stop=False, interval=0, timeout=3):
        logger.info('Started polling.')
        self.__stop_polling.clear()
        error_interval = .25

        while not self.__stop_polling.wait(interval):
            try:
                self.__retrieve_updates(timeout)
                error_interval = .25
            except apihelper.ApiException as e:
                logger.error(e)
                if not none_stop:
                    self.__stop_polling.set()
                    logger.info("Exception occurred. Stopping.")
                else:
                    logger.info("Waiting for {0} seconds until retry".format(error_interval))
                    time.sleep(error_interval)
                    error_interval *= 2
            except KeyboardInterrupt:
                logger.info("KeyboardInterrupt received.")
                self.__stop_polling.set()
                break

        logger.info('Stopped polling.')

    def __exec_task(self, task, *args, **kwargs):
        if self.threaded:
            self.worker_pool.put(task, *args, **kwargs)
        else:
            task(*args, **kwargs)

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
                     parse_mode=None, disable_notification=None):
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
        :param disable_notification: Boolean, Optional. Sends the message silently.
        :return: API reply.
        """
        return types.Message.de_json(
            apihelper.send_message(self.token, chat_id, text, disable_web_page_preview, reply_to_message_id,
                                   reply_markup, parse_mode, disable_notification))

    def forward_message(self, chat_id, from_chat_id, message_id, disable_notification=None):
        """
        Use this method to forward messages of any kind.
        :param disable_notification:
        :param chat_id: which chat to forward
        :param from_chat_id: which chat message from
        :param message_id: message id
        :return: API reply.
        """
        return types.Message.de_json(
            apihelper.forward_message(self.token, chat_id, from_chat_id, message_id, disable_notification))

    def send_photo(self, chat_id, photo, caption=None, reply_to_message_id=None, reply_markup=None,
                   disable_notification=None):
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
            apihelper.send_photo(self.token, chat_id, photo, caption, reply_to_message_id, reply_markup,
                                 disable_notification))

    def send_audio(self, chat_id, audio, duration=None, performer=None, title=None, reply_to_message_id=None,
                   reply_markup=None, disable_notification=None):
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
                                 reply_markup, disable_notification))

    def send_voice(self, chat_id, voice, duration=None, reply_to_message_id=None, reply_markup=None,
                   disable_notification=None):
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
            apihelper.send_voice(self.token, chat_id, voice, duration, reply_to_message_id, reply_markup,
                                 disable_notification))

    def send_document(self, chat_id, data, reply_to_message_id=None, reply_markup=None, disable_notification=None):
        """
        Use this method to send general files.
        :param chat_id:
        :param data:
        :param reply_to_message_id:
        :param reply_markup:
        :return: API reply.
        """
        return types.Message.de_json(
            apihelper.send_data(self.token, chat_id, data, 'document', reply_to_message_id, reply_markup,
                                disable_notification))

    def send_sticker(self, chat_id, data, reply_to_message_id=None, reply_markup=None, disable_notification=None):
        """
        Use this method to send .webp stickers.
        :param chat_id:
        :param data:
        :param reply_to_message_id:
        :param reply_markup:
        :return: API reply.
        """
        return types.Message.de_json(
            apihelper.send_data(self.token, chat_id, data, 'sticker', reply_to_message_id, reply_markup,
                                disable_notification))

    def send_video(self, chat_id, data, duration=None, caption=None, reply_to_message_id=None, reply_markup=None,
                   disable_notification=None):
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
            apihelper.send_video(self.token, chat_id, data, duration, caption, reply_to_message_id, reply_markup,
                                 disable_notification))

    def send_location(self, chat_id, latitude, longitude, reply_to_message_id=None, reply_markup=None,
                      disable_notification=None):
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
            apihelper.send_location(self.token, chat_id, latitude, longitude, reply_to_message_id, reply_markup,
                                    disable_notification))

    def send_venue(self, chat_id, latitude, longitude, title, address, foursquare_id=None, disable_notification=None,
                   reply_to_message_id=None, reply_markup=None):
        """
        Use this method to send information about a venue.
        :param chat_id: Integer or String : Unique identifier for the target chat or username of the target channel
        :param latitude: Float : Latitude of the venue
        :param longitude: Float : Longitude of the venue
        :param title: String : Name of the venue
        :param address: String : Address of the venue
        :param foursquare_id: String : Foursquare identifier of the venue
        :param disable_notification:
        :param reply_to_message_id:
        :param reply_markup:
        :return:
        """
        return types.Message.de_json(
            apihelper.send_venue(self.token, chat_id, latitude, longitude, title, address, foursquare_id,
                                 disable_notification, reply_to_message_id, reply_markup)
        )

    def send_contact(self, chat_id, phone_number, first_name, last_name=None, disable_notification=None,
                     reply_to_message_id=None, reply_markup=None):
        return types.Message.de_json(
            apihelper.send_contact(self.token, chat_id, phone_number, first_name, last_name, disable_notification,
                                   reply_to_message_id, reply_markup)
        )

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

    def kick_chat_member(self, chat_id, user_id):
        """
        Use this method to kick a user from a group or a supergroup.
        :param chat_id: Int or string : Unique identifier for the target group or username of the target supergroup
        :param user_id: Int : Unique identifier of the target user
        :return: types.Message
        """
        return apihelper.kick_chat_member(self.token, chat_id, user_id)

    def unban_chat_member(self, chat_id, user_id):
        return apihelper.unban_chat_member(self.token, chat_id, user_id)

    def answer_callback_query(self, callback_query_id, text=None, show_alert=None):
        return apihelper.answer_callback_query(self.token, callback_query_id, text, show_alert)

    def edit_message_text(self, text, chat_id=None, message_id=None, inline_message_id=None, parse_mode=None,
                          disable_web_page_preview=None, reply_markup=None):
        result = apihelper.edit_message_text(self.token, text, chat_id, message_id, inline_message_id, parse_mode,
                                        disable_web_page_preview, reply_markup)
        if type(result) == bool:    # if edit inline message return is bool not Message.
            return result
        return types.Message.de_json(result)

    def edit_message_reply_markup(self, chat_id=None, message_id=None, inline_message_id=None, reply_markup=None):
        return types.Message.de_json(
            apihelper.edit_message_reply_markup(self.token, chat_id, message_id, inline_message_id, reply_markup)
        )

    def edit_message_caption(self, caption, chat_id=None, message_id=None, inline_message_id=None, reply_markup=None):
        return types.Message.de_json(
            apihelper.edit_message_caption(self.token, caption, chat_id, message_id, inline_message_id, reply_markup)
        )

    def reply_to(self, message, text, **kwargs):
        """
        Convenience function for `send_message(message.chat.id, text, reply_to_message_id=message.message_id, **kwargs)`
        """
        return self.send_message(message.chat.id, text, reply_to_message_id=message.message_id, **kwargs)

    def answer_inline_query(self, inline_query_id, results, cache_time=None, is_personal=None, next_offset=None,
                            switch_pm_text=None, switch_pm_parameter=None):
        """
        Use this method to send answers to an inline query. On success, True is returned.
        No more than 50 results per query are allowed.
        :param inline_query_id: Unique identifier for the answered query
        :param results: Array of results for the inline query
        :param cache_time: The maximum amount of time in seconds that the result of the inline query may be cached on the server.
        :param is_personal: Pass True, if results may be cached on the server side only for the user that sent the query.
        :param next_offset: Pass the offset that a client should send in the next query with the same text to receive more results.
        :param switch_pm_parameter: If passed, clients will display a button with specified text that switches the user
         to a private chat with the bot and sends the bot a start message with the parameter switch_pm_parameter
        :param switch_pm_text: 	Parameter for the start message sent to the bot when user presses the switch button
        :return: True means success.
        """
        return apihelper.answer_inline_query(self.token, inline_query_id, results, cache_time, is_personal, next_offset,
                                             switch_pm_text, switch_pm_parameter)

    def answer_callback_query(self, callback_query_id, text=None, show_alert=None):
        """
        Use this method to send answers to callback queries sent from inline keyboards. The answer will be displayed to
        the user as a notification at the top of the chat screen or as an alert.
        :param callback_query_id:
        :param text:
        :param show_alert:
        :return:
        """
        return apihelper.answer_callback_query(self.token, callback_query_id, text, show_alert)

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
            if not message.reply_to_message:
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
        if chat_id in self.pre_message_subscribers_next_step:
            self.pre_message_subscribers_next_step[chat_id].append(callback)
        else:
            self.pre_message_subscribers_next_step[chat_id] = [callback]

    def _notify_message_next_handler(self, new_messages):
        for message in new_messages:
            chat_id = message.chat.id
            if chat_id in self.message_subscribers_next_step:
                handlers = self.message_subscribers_next_step[chat_id]
                for handler in handlers:
                    self.__exec_task(handler, message)
                self.message_subscribers_next_step.pop(chat_id, None)

    def _append_pre_next_step_handler(self):
        for k in self.pre_message_subscribers_next_step.keys():
            if k in self.message_subscribers_next_step:
                self.message_subscribers_next_step[k].extend(self.pre_message_subscribers_next_step[k])
            else:
                self.message_subscribers_next_step[k] = self.pre_message_subscribers_next_step[k]
        self.pre_message_subscribers_next_step = {}

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

        def decorator(handler):
            self.add_message_handler(handler, commands, regexp, func, content_types)
            return handler

        return decorator

    def add_message_handler(self, handler, commands=None, regexp=None, func=None, content_types=None):
        if content_types is None:
            content_types = ['text']

        filters = {'content_types': content_types}
        if regexp:
            filters['regexp'] = regexp
        if func:
            filters['lambda'] = func
        if commands:
            filters['commands'] = commands

        handler_dict = {
            'function': handler,
            'filters': filters
        }

        self.message_handlers.append(handler_dict)

    def inline_handler(self, func):
        def decorator(handler):
            self.add_inline_handler(handler, func)
            return handler

        return decorator

    def add_inline_handler(self, handler, func):
        filters = {'lambda': func}

        handler_dict = {
            'function': handler,
            'filters': filters
        }

        self.inline_handlers.append(handler_dict)

    def chosen_inline_handler(self, func):
        def decorator(handler):
            self.add_chosen_inline_handler(handler, func)
            return handler

        return decorator

    def add_chosen_inline_handler(self, handler, func):
        filters = {'lambda': func}

        handler_dict = {
            'function': handler,
            'filters': filters
        }

        self.chosen_inline_handlers.append(handler_dict)

    def callback_query_handler(self, func):
        def decorator(handler):
            self.add_callback_query_handler(handler, func)

        return decorator

    def add_callback_query_handler(self, handler, func):
        filters = {'lambda': func}

        handler_dict = {
            'function': handler,
            'filters': filters
        }

        self.callback_query_handlers.append(handler_dict)

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

    def _notify_command_handlers(self, handlers, new_messages):
        for message in new_messages:
            for message_handler in handlers:
                if self._test_message_handler(message_handler, message):
                    self.__exec_task(message_handler['function'], message)
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
