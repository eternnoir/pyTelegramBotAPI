# -*- coding: utf-8 -*-
from __future__ import print_function

import threading
# Python3 queue support.
try:
    import Queue
except ImportError:
    import queue as Queue
import time

import re
from telebot import apihelper, types

"""
Module : telebot
"""

API_URL = r"https://api.telegram.org/"


class ThreadPool:
    class WorkerThread(threading.Thread):
        count = 0

        def __init__(self, queue):
            threading.Thread.__init__(self, name="WorkerThread{0}".format(self.__class__.count + 1))
            self.__class__.count += 1
            self.queue = queue
            self.daemon = True

            self._running = True
            self.start()

        def run(self):
            while self._running:
                try:
                    task, args, kwargs = self.queue.get()
                    task(*args, **kwargs)
                except Queue.Empty:
                    time.sleep(0)
                    pass

        def stop(self):
            self._running = False

    def __init__(self, num_threads=4):
        self.tasks = Queue.Queue()
        self.workers = [self.WorkerThread(self.tasks) for _ in range(num_threads)]

        self.num_threads = num_threads

    def put(self, func, *args, **kwargs):
        self.tasks.put((func, args, kwargs))

    def close(self):
        for worker in self.workers:
            worker.stop()
        for worker in self.workers:
            worker.join()


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
        :return:
        """
        self.token = token
        self.update_listener = []
        self.polling_thread = None
        self.__stop_polling = False
        self.last_update_id = 0
        self.num_threads = num_threads
        self.__create_threads = create_threads

        self.message_handlers = []
        if self.__create_threads:
            self.worker_pool = ThreadPool(num_threads)

    def get_update(self):
        """
        Retrieves any updates from the Telegram API.
        Registered listeners and applicable message handlers will be notified when a new message arrives.
        :raises ApiException when a call has failed.
        """
        updates = apihelper.get_updates(self.token, offset=(self.last_update_id + 1), timeout=20)
        new_messages = []
        for update in updates:
            if update['update_id'] > self.last_update_id:
                self.last_update_id = update['update_id']
            msg = types.Message.de_json(update['message'])
            new_messages.append(msg)

        if len(new_messages) > 0:
            self.process_new_messages(new_messages)

    def process_new_messages(self, new_messages):
        self.__notify_update(new_messages)
        self._notify_command_handlers(new_messages)

    def __notify_update(self, new_messages):
        for listener in self.update_listener:
            if self.__create_threads:
                self.worker_pool.put(listener, new_messages)
            else:
                listener(new_messages)

    def polling(self, none_stop=False):
        """
        This function creates a new Thread that calls an internal __polling function.
        This allows the bot to retrieve Updates automagically and notify listeners and message handlers accordingly.

        Do not call this function more than once!

        Always get updates.
        :param none_stop: Do not stop polling when Exception occur.
        :return:
        """
        self.__stop_polling = False
        self.polling_thread = threading.Thread(target=self.__polling, args=([none_stop]))
        self.polling_thread.daemon = True
        self.polling_thread.start()

    def __polling(self, none_stop):
        print('TeleBot: Started polling.')
        while not self.__stop_polling:
            try:
                self.get_update()
            except Exception as e:
                if not none_stop:
                    self.__stop_polling = True
                    print("TeleBot: Exception occurred. Stopping.")
                print(e)

        print('TeleBot: Stopped polling.')

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
        :return: API reply.
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
        :return: API reply.
        """
        return types.Message.de_json(
            apihelper.send_message(self.token, chat_id, text, disable_web_page_preview, reply_to_message_id,
                                   reply_markup))

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

    def send_audio(self, chat_id, data, reply_to_message_id=None, reply_markup=None):
        """
        Use this method to send audio files, if you want Telegram clients to display the file as a playable
        voice message. For this to work, your audio must be in an .ogg file encoded with OPUS
        :param chat_id:
        :param data:
        :param reply_to_message_id:
        :param reply_markup:
        :return: API reply.
        """
        return types.Message.de_json(
            apihelper.send_data(self.token, chat_id, data, 'audio', reply_to_message_id, reply_markup))

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

    def send_video(self, chat_id, data, reply_to_message_id=None, reply_markup=None):
        """
        Use this method to send video files, Telegram clients support mp4 videos.
        :param chat_id:
        :param data:
        :param reply_to_message_id:
        :param reply_markup:
        :return: API reply.
        """
        return types.Message.de_json(
            apihelper.send_data(self.token, chat_id, data, 'video', reply_to_message_id, reply_markup))

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
        return self.send_message(message.chat.id, text, reply_to_message_id=message.message_id, **kwargs)

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
            func_dict = {'function': fn, 'content_types': content_types}
            if regexp:
                func_dict['regexp'] = regexp if 'text' in content_types else None
            if func:
                func_dict['lambda'] = func
            if commands:
                func_dict['commands'] = commands if 'text' in content_types else None
            self.message_handlers.append(func_dict)
            return fn

        return decorator

    @staticmethod
    def is_command(text):
        """
        Checks if `text` is a command. Telegram chat commands start with the '/' character.
        :param text: Text to check.
        :return: True if `text` is a command, else False.
        """
        return text.startswith('/')

    @staticmethod
    def extract_command(text):
        """
        Extracts the command from `text` (minus the '/') if `text` is a command (see is_command).
        If `text` is not a command, this function returns None.

        Examples:
        extract_command('/help'): 'help'
        extract_command('/help@BotName'): 'help'
        extract_command('/search black eyed peas'): 'search'
        extract_command('Good day to you'): None

        :param text: String to extract the command from
        :return: the command if `text` is a command, else None.
        """
        return text.split()[0].split('@')[0][1:] if TeleBot.is_command(text) else None

    @staticmethod
    def _test_message_handler(message_handler, message):
        if message.content_type not in message_handler['content_types']:
            return False
        if 'commands' in message_handler and message.content_type == 'text':
            return TeleBot.extract_command(message.text) in message_handler['commands']
        if 'regexp' in message_handler and message.content_type == 'text' and re.search(message_handler['regexp'],
                                                                                        message.text):
            return False
        if 'lambda' in message_handler:
            return message_handler['lambda'](message)
        return False

    def _notify_command_handlers(self, new_messages):
        for message in new_messages:
            for message_handler in self.message_handlers:
                if self._test_message_handler(message_handler, message):
                    if self.__create_threads:
                        self.worker_pool.put(message_handler['function'], message)
                        # t = threading.Thread(target=message_handler['function'], args=(message,))
                        # t.start()
                    else:
                        message_handler['function'](message)
                    break


class AsyncTask:
    def __init__(self, target, *args, **kwargs):
        self.target = target
        self.args = args
        self.kwargs = kwargs

        self.done = False
        self.thread = threading.Thread(target=self._run)
        self.thread.start()

    def _run(self):
        try:
            self.result = self.target(*self.args, **self.kwargs)
        except Exception as e:
            self.result = e
        self.done = True

    def wait(self):
        if not self.done:
            self.thread.join()
        if isinstance(self.result, Exception):
            raise self.result
        else:
            return self.result


def async():
    def decorator(fn):
        def wrapper(*args, **kwargs):
            return AsyncTask(fn, *args, **kwargs)

        return wrapper

    return decorator


class AsyncTeleBot(TeleBot):
    def __init__(self, *args, **kwargs):
        TeleBot.__init__(self, *args, **kwargs)

    @async()
    def get_me(self):
        return TeleBot.get_me(self)

    @async()
    def get_user_profile_photos(self, *args, **kwargs):
        return TeleBot.get_user_profile_photos(self, *args, **kwargs)

    @async()
    def send_message(self, *args, **kwargs):
        return TeleBot.send_message(self, *args, **kwargs)

    @async()
    def forward_message(self, *args, **kwargs):
        return TeleBot.forward_message(self, *args, **kwargs)

    @async()
    def send_photo(self, *args, **kwargs):
        return TeleBot.send_photo(self, *args, **kwargs)

    @async()
    def send_audio(self, *args, **kwargs):
        return TeleBot.send_audio(self, *args, **kwargs)

    @async()
    def send_document(self, *args, **kwargs):
        return TeleBot.send_document(self, *args, **kwargs)

    @async()
    def send_sticker(self, *args, **kwargs):
        return TeleBot.send_sticker(self, *args, **kwargs)

    @async()
    def send_video(self, *args, **kwargs):
        return TeleBot.send_video(self, *args, **kwargs)

    @async()
    def send_location(self, *args, **kwargs):
        return TeleBot.send_location(self, *args, **kwargs)

    @async()
    def send_chat_action(self, *args, **kwargs):
        return TeleBot.send_chat_action(self, *args, **kwargs)
