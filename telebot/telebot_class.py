
import threading
import six
import sys

import telebot.apihelper as apihelper
import telebot.listeners as listeners
from telebot.util import logger


class TeleBot(object, apihelper.TelegramApiInterface):

    def __init__(self, token, request_executor=None):
        """
        :param token: bot API token
        :return: Telebot object.
        """
        request_executor = request_executor if request_executor is not None else apihelper.RequestExecutorImpl()
        super(TeleBot, self).__init__(token, request_executor)

        self.token = token
        self.update_listeners = []

        self.__stop_polling = threading.Event()
        self.last_update_id = 0

    def __yield_updates(self, timeout=20):
        updates = self.get_updates(offset=self.last_update_id, timeout=timeout)
        while updates:
            self.last_update_id = max(updates, key=lambda u: u.update_id)
            updates = self.get_updates(offset=(self.last_update_id + 1), timeout=timeout)
            yield (x for x in updates)

    def skip_updates(self, timeout=1):
        """
        Get and discard all pending updates before first poll of the bot
        This method may take up to `timeout` seconds to execute.
        :return: A list of all skipped updates
        :rtype list[types.Update]
        """
        return list(self.__yield_updates(timeout=timeout))

    def retrieve_updates(self, timeout=20):
        """
        Retrieves updates from Telegram and notifies listeners.
        Does not catch any exceptions raised by listeners.
        """
        self.process_new_updates(self.__yield_updates(timeout=timeout))

    @staticmethod
    def __call_listener(listener, update):
        r = listener(update)
        # Assume the listener wants to stay in the list if it does not return anything
        return r if r is not None else True

    def process_new_updates(self, updates):
        logger.debug('Received {0} new updates'.format(len(updates)))
        for update in updates:
            self.update_listeners = filter(lambda l: self.__call_listener(l, update), self.update_listeners)

    @staticmethod
    def __default_exception_handler(bot, exception):
        logger.error(exception)
        logger.info("Exception occurred. Stopping.")
        bot.stop_polling()

    def polling(self, skip_pending=False, timeout=20, exception_handler=lambda e: True):
        """
        This function creates a new Thread that calls an internal __retrieve_updates function.
        This allows the bot to retrieve Updates automagically and notify listeners and message handlers accordingly.

        Warning: Do not call this function more than once!

        Always get updates.
        :param exception_handler:
        :param skip_pending: Retrieve and discard pending updates
        :param timeout: Timeout in seconds for long polling.
        :return:
        """
        logger.info('Started polling.')
        self.__stop_polling.clear()

        if skip_pending:
            logger.info('Skipped {0} pending messages'.format(self.skip_updates()))

        while not self.__stop_polling.wait(0):
            try:
                self.retrieve_updates(timeout)
            except apihelper.ApiException as e:
                exception_handler(self, e)
            except KeyboardInterrupt:
                logger.info("KeyboardInterrupt")
                self.__stop_polling.set()
                six.reraise(*sys.exc_info())

        logger.info('Stopped polling.')

    def stop_polling(self):
        self.__stop_polling.set()

    def add_update_listener(self, listener):
        self.update_listeners.append(listener)

    def remove_webhook(self):
        return self.set_webhook()  # No params resets webhook

    def reply_to(self, message, text, **kwargs):
        """
        Convenience function for `send_message(message.chat.id, text, reply_to_message_id=message.message_id, **kwargs)`
        """
        return self.send_message(message.chat.id, text, reply_to_message_id=message.message_id, **kwargs)

    def register_next_step_handler(self, message, handler):
        self.add_update_listener(listeners.NextStepHandler(handler, message))

    def message_handler(self, **kwargs):
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
            self.add_message_handler(handler, **kwargs)
            return handler
        return decorator

    def add_message_handler(self, handler, **kwargs):
        self.add_update_listener(listeners.MessageHandler(handler, **kwargs))

    def inline_handler(self, func):
        def decorator(handler):
            self.add_inline_handler(handler, func)
            return handler
        return decorator

    def add_inline_handler(self, handler, func):
        self.add_update_listener(listeners.InlineHandler(handler, func))

    def chosen_inline_handler(self, func):
        def decorator(handler):
            self.add_chosen_inline_handler(handler, func)
            return handler
        return decorator

    def add_chosen_inline_handler(self, handler, func):
        self.add_update_listener(listeners.ChosenInlineResultHandler(handler, func))

    def callback_query_handler(self, func):
        def decorator(handler):
            self.add_callback_query_handler(handler, func)
            return handler
        return decorator

    def add_callback_query_handler(self, handler, func):
        self.add_update_listener(listeners.CallbackQueryHandler(handler, func))
