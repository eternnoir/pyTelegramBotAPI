
import threading
import time
import re
import six

import apihelper
import util
from util import logger


class TeleBot(apihelper.TelegramApiInterface):
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

    def __init__(self, token, skip_pending=False, request_executor=None):
        """
        :param token: bot API token
        :return: Telebot object.
        """
        self.token = token
        self.update_listener = []
        self.skip_pending = skip_pending

        self.__stop_polling = threading.Event()
        self.last_update_id = 0

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

        if request_executor is None:
            apihelper.TelegramApiInterface.__init__(self, token, apihelper.RequestExecutorImpl())
        else:
            apihelper.TelegramApiInterface.__init__(self, token, request_executor)

    def __skip_updates(self):
        """
        Get and discard all pending updates before first poll of the bot
        :return: total updates skipped
        """
        total = 0
        updates = self.get_updates(offset=self.last_update_id)
        while updates:
            total += len(updates)
            for update in updates:
                if update.update_id > self.last_update_id:
                    self.last_update_id = update.update_id
            updates = self.get_updates(offset=self.last_update_id + 1)
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
            listener(new_messages)

    def polling(self, continue_on_exception=False, interval=0, timeout=20):
        """
        This function creates a new Thread that calls an internal __retrieve_updates function.
        This allows the bot to retrieve Updates automagically and notify listeners and message handlers accordingly.

        Warning: Do not call this function more than once!

        Always get updates.
        :param interval:
        :param continue_on_exception: Do not stop polling when an ApiException occurs.
        :param timeout: Timeout in seconds for long polling.
        :return:
        """
        logger.info('Started polling.')
        self.__stop_polling.clear()
        error_interval = .25

        while not self.__stop_polling.wait(interval):
            try:
                self.__retrieve_updates(timeout)
                error_interval = .25
            except apihelper.ApiException as e:
                logger.error(e)
                if not continue_on_exception:
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

    def stop_polling(self):
        self.__stop_polling.set()

    def add_update_listener(self, listener):
        self.update_listener.append(listener)

    def remove_webhook(self):
        return self.set_webhook()  # No params resets webhook

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
                    handler(message)
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

        :param commands:
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
                    message_handler['function'](message)
                    break

