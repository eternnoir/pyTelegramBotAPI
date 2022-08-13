# -*- coding: utf-8 -*-
from datetime import datetime

import logging
import re
import sys
import threading
import time
import traceback
from typing import Any, Callable, List, Optional, Union

# these imports are used to avoid circular import error
import telebot.util
import telebot.types

# storage
from telebot.storage import StatePickleStorage, StateMemoryStorage, StateStorageBase

# random module to generate random string
import random
import string

import ssl

logger = logging.getLogger('TeleBot')

formatter = logging.Formatter(
    '%(asctime)s (%(filename)s:%(lineno)d %(threadName)s) %(levelname)s - %(name)s: "%(message)s"'
)

import inspect

console_output_handler = logging.StreamHandler(sys.stderr)
console_output_handler.setFormatter(formatter)
logger.addHandler(console_output_handler)

logger.setLevel(logging.ERROR)

from telebot import apihelper, util, types
from telebot.handler_backends import HandlerBackend, MemoryHandlerBackend, FileHandlerBackend, BaseMiddleware, CancelUpdate, SkipHandler, State
from telebot.custom_filters import SimpleCustomFilter, AdvancedCustomFilter


REPLY_MARKUP_TYPES = Union[
    types.InlineKeyboardMarkup, types.ReplyKeyboardMarkup, 
    types.ReplyKeyboardRemove, types.ForceReply]



"""
Module : telebot
"""


class Handler:
    """
    Class for (next step|reply) handlers.
    """

    def __init__(self, callback, *args, **kwargs):
        self.callback = callback
        self.args = args
        self.kwargs = kwargs

    def __getitem__(self, item):
        return getattr(self, item)


class ExceptionHandler:
    """
    Class for handling exceptions while Polling
    """

    # noinspection PyMethodMayBeStatic,PyUnusedLocal
    def handle(self, exception):
        return False


class TeleBot:
    """
    This is the main synchronous class for Bot.

    It allows you to add handlers for different kind of updates.

    Usage:

    .. code-block:: python3
        :caption: Creating instance of TeleBot

        from telebot import TeleBot
        bot = TeleBot('token') # get token from @BotFather
        # now you can register other handlers/update listeners, 
        # and use bot methods.

    See more examples in examples/ directory:
    https://github.com/eternnoir/pyTelegramBotAPI/tree/master/examples


    :param token: Token of a bot, should be obtained from @BotFather
    :type token: :obj:`str`

    :param parse_mode: Default parse mode, defaults to None
    :type parse_mode: :obj:`str`, optional

    :param threaded: Threaded or not, defaults to True
    :type threaded: :obj:`bool`, optional

    :param skip_pending: Skips pending updates, defaults to False
    :type skip_pending: :obj:`bool`, optional

    :param num_threads: Number of maximum parallel threads, defaults to 2
    :type num_threads: :obj:`int`, optional

    :param next_step_backend: Next step backend class, defaults to None
    :type next_step_backend: :class:`telebot.handler_backends.HandlerBackend`, optional

    :param reply_backend: Reply step handler class, defaults to None
    :type reply_backend: :class:`telebot.handler_backends.HandlerBackend`, optional

    :param exception_handler: Exception handler to handle errors, defaults to None
    :type exception_handler: :class:`telebot.ExceptionHandler`, optional

    :param last_update_id: Last update's id, defaults to 0
    :type last_update_id: :obj:`int`, optional

    :param suppress_middleware_excepions: Supress middleware exceptions, defaults to False
    :type suppress_middleware_excepions: :obj:`bool`, optional

    :param state_storage: Storage for states, defaults to StateMemoryStorage()
    :type state_storage: :class:`telebot.storage.StateStorageBase`, optional

    :param use_class_middlewares: Use class middlewares, defaults to False
    :type use_class_middlewares: :obj:`bool`, optional
    """

    def __init__(
            self, token: str, parse_mode: Optional[str]=None, threaded: Optional[bool]=True,
            skip_pending: Optional[bool]=False, num_threads: Optional[int]=2,
            next_step_backend: Optional[HandlerBackend]=None, reply_backend: Optional[HandlerBackend]=None,
            exception_handler: Optional[ExceptionHandler]=None, last_update_id: Optional[int]=0,
            suppress_middleware_excepions: Optional[bool]=False, state_storage: Optional[StateStorageBase]=StateMemoryStorage(),
            use_class_middlewares: Optional[bool]=False
    ):
        self.token = token
        self.parse_mode = parse_mode
        self.update_listener = []
        self.skip_pending = skip_pending
        self.suppress_middleware_excepions = suppress_middleware_excepions

        self.__stop_polling = threading.Event()
        self.last_update_id = last_update_id
        self.exc_info = None

        self.next_step_backend = next_step_backend
        if not self.next_step_backend:
            self.next_step_backend = MemoryHandlerBackend()

        self.reply_backend = reply_backend
        if not self.reply_backend:
            self.reply_backend = MemoryHandlerBackend()

        self.exception_handler = exception_handler

        self.message_handlers = []
        self.edited_message_handlers = []
        self.channel_post_handlers = []
        self.edited_channel_post_handlers = []
        self.inline_handlers = []
        self.chosen_inline_handlers = []
        self.callback_query_handlers = []
        self.shipping_query_handlers = []
        self.pre_checkout_query_handlers = []
        self.poll_handlers = []
        self.poll_answer_handlers = []
        self.my_chat_member_handlers = []
        self.chat_member_handlers = []
        self.chat_join_request_handlers = []
        self.custom_filters = {}
        self.state_handlers = []

        self.current_states = state_storage

        self.use_class_middlewares = use_class_middlewares
        if apihelper.ENABLE_MIDDLEWARE and not use_class_middlewares:
            self.typed_middleware_handlers = {
                'message': [],
                'edited_message': [],
                'channel_post': [],
                'edited_channel_post': [],
                'inline_query': [],
                'chosen_inline_result': [],
                'callback_query': [],
                'shipping_query': [],
                'pre_checkout_query': [],
                'poll': [],
                'poll_answer': [],
                'my_chat_member': [],
                'chat_member': [],
                'chat_join_request': []
            }
            self.default_middleware_handlers = []
        if apihelper.ENABLE_MIDDLEWARE and use_class_middlewares:
            self.typed_middleware_handlers = None
            logger.error(
                'You are using class based middlewares while having ENABLE_MIDDLEWARE set to True. This is not recommended.'
            )
        self.middlewares = [] if use_class_middlewares else None
        self.threaded = threaded
        if self.threaded:
            self.worker_pool = util.ThreadPool(self, num_threads=num_threads)
    
    @property
    def user(self) -> types.User:
        """
        The User object representing this bot.
        Equivalent to bot.get_me() but the result is cached so only one API call is needed.

        :return: Bot's info.
        :rtype: :class:`telebot.types.User`
        """
        if not hasattr(self, "_user"):
            self._user = self.get_me()
        return self._user

    def enable_save_next_step_handlers(self, delay: Optional[int]=120, filename: Optional[str]="./.handler-saves/step.save"):
        """
        Enable saving next step handlers (by default saving disabled)

        This function explicitly assigns FileHandlerBackend (instead of Saver) just to keep backward
        compatibility whose purpose was to enable file saving capability for handlers. And the same
        implementation is now available with FileHandlerBackend

        :param delay: Delay between changes in handlers and saving, defaults to 120
        :type delay: :obj:`int`, optional

        :param filename: Filename of save file, defaults to "./.handler-saves/step.save"
        :type filename: :obj:`str`, optional

        :return: None
        """
        self.next_step_backend = FileHandlerBackend(self.next_step_backend.handlers, filename, delay)


    def enable_saving_states(self, filename: Optional[str]="./.state-save/states.pkl"):
        """
        Enable saving states (by default saving disabled)

        .. note::
            It is recommended to pass a :class:`~telebot.storage.StatePickleStorage` instance as state_storage
            to TeleBot class.

        :param filename: Filename of saving file, defaults to "./.state-save/states.pkl"
        :type filename: :obj:`str`, optional
        """
        self.current_states = StatePickleStorage(file_path=filename)
        self.current_states.create_dir()


    def enable_save_reply_handlers(self, delay=120, filename="./.handler-saves/reply.save"):
        """
        Enable saving reply handlers (by default saving disable)

        This function explicitly assigns FileHandlerBackend (instead of Saver) just to keep backward
        compatibility whose purpose was to enable file saving capability for handlers. And the same
        implementation is now available with FileHandlerBackend

        :param delay: Delay between changes in handlers and saving, defaults to 120
        :type delay: :obj:`int`, optional

        :param filename: Filename of save file, defaults to "./.handler-saves/reply.save"
        :type filename: :obj:`str`, optional
        """
        self.reply_backend = FileHandlerBackend(self.reply_backend.handlers, filename, delay)


    def disable_save_next_step_handlers(self):
        """
        Disable saving next step handlers (by default saving disable)

        This function is left to keep backward compatibility whose purpose was to disable file saving capability
        for handlers. For the same purpose, MemoryHandlerBackend is reassigned as a new next_step_backend backend
        instead of FileHandlerBackend.
        """
        self.next_step_backend = MemoryHandlerBackend(self.next_step_backend.handlers)


    def disable_save_reply_handlers(self):
        """
        Disable saving next step handlers (by default saving disable)

        This function is left to keep backward compatibility whose purpose was to disable file saving capability
        for handlers. For the same purpose, MemoryHandlerBackend is reassigned as a new reply_backend backend
        instead of FileHandlerBackend.
        """
        self.reply_backend = MemoryHandlerBackend(self.reply_backend.handlers)


    def load_next_step_handlers(self, filename="./.handler-saves/step.save", del_file_after_loading=True):
        """
        Load next step handlers from save file

        This function is left to keep backward compatibility whose purpose was to load handlers from file with the
        help of FileHandlerBackend and is only recommended to use if next_step_backend was assigned as
        FileHandlerBackend before entering this function


        :param filename: Filename of the file where handlers was saved, defaults to "./.handler-saves/step.save"
        :type filename: :obj:`str`, optional

        :param del_file_after_loading: If True is passed, after the loading file will be deleted, defaults to True
        :type del_file_after_loading: :obj:`bool`, optional
        """
        self.next_step_backend.load_handlers(filename, del_file_after_loading)


    def load_reply_handlers(self, filename="./.handler-saves/reply.save", del_file_after_loading=True):
        """
        Load reply handlers from save file

        This function is left to keep backward compatibility whose purpose was to load handlers from file with the
        help of FileHandlerBackend and is only recommended to use if reply_backend was assigned as
        FileHandlerBackend before entering this function

        :param filename: Filename of the file where handlers was saved, defaults to "./.handler-saves/reply.save"
        :type filename: :obj:`str`, optional

        :param del_file_after_loading: If True is passed, after the loading file will be deleted, defaults to True, defaults to True
        :type del_file_after_loading: :obj:`bool`, optional
        """
        self.reply_backend.load_handlers(filename, del_file_after_loading)


    def set_webhook(self, url: Optional[str]=None, certificate: Optional[Union[str, Any]]=None, max_connections: Optional[int]=None,
                    allowed_updates: Optional[List[str]]=None, ip_address: Optional[str]=None,
                    drop_pending_updates: Optional[bool] = None, timeout: Optional[int]=None, secret_token: Optional[str]=None) -> bool:
        """
        Use this method to specify a URL and receive incoming updates via an outgoing webhook.
        Whenever there is an update for the bot, we will send an HTTPS POST request to the specified URL,
        containing a JSON-serialized Update. In case of an unsuccessful request, we will give up after
        a reasonable amount of attempts. Returns True on success.

        If you'd like to make sure that the webhook was set by you, you can specify secret data in the parameter secret_token.
        If specified, the request will contain a header “X-Telegram-Bot-Api-Secret-Token” with the secret token as content.

        Telegram Documentation: https://core.telegram.org/bots/api#setwebhook

        :param url: HTTPS URL to send updates to. Use an empty string to remove webhook integration, defaults to None
        :type url: :obj:`str`, optional

        :param certificate: Upload your public key certificate so that the root certificate in use can be checked, defaults to None
        :type certificate: :class:`str`, optional

        :param max_connections: The maximum allowed number of simultaneous HTTPS connections to the webhook for update delivery, 1-100.
            Defaults to 40. Use lower values to limit the load on your bot's server, and higher values to increase your bot's throughput,
            defaults to None
        :type max_connections: :obj:`int`, optional
        
        :param allowed_updates: A JSON-serialized list of the update types you want your bot to receive. For example,
            specify [“message”, “edited_channel_post”, “callback_query”] to only receive updates of these types. See Update
            for a complete list of available update types. Specify an empty list to receive all update types except chat_member (default).
            If not specified, the previous setting will be used.
            
            Please note that this parameter doesn't affect updates created before the call to the setWebhook, so unwanted updates may be received
            for a short period of time. Defaults to None
        
        :type allowed_updates: :obj:`list`, optional

        :param ip_address: The fixed IP address which will be used to send webhook requests instead of the IP address
            resolved through DNS, defaults to None
        :type ip_address: :obj:`str`, optional

        :param drop_pending_updates: Pass True to drop all pending updates, defaults to None
        :type drop_pending_updates: :obj:`bool`, optional

        :param timeout: Timeout of a request, defaults to None
        :type timeout: :obj:`int`, optional

        :param secret_token: A secret token to be sent in a header “X-Telegram-Bot-Api-Secret-Token” in every webhook request, 1-256 characters.
            Only characters A-Z, a-z, 0-9, _ and - are allowed. The header is useful to ensure that the request comes from a webhook set by you. Defaults to None
        :type secret_token: :obj:`str`, optional

        :return: True on success.
        :rtype: :obj:`bool` if the request was successful.
        """

        return apihelper.set_webhook(self.token, url, certificate, max_connections, allowed_updates, ip_address,
                                     drop_pending_updates, timeout, secret_token)


    def run_webhooks(self,
                    listen: Optional[str]="127.0.0.1",
                    port: Optional[int]=443,
                    url_path: Optional[str]=None,
                    certificate: Optional[str]=None,
                    certificate_key: Optional[str]=None,
                    webhook_url: Optional[str]=None,
                    max_connections: Optional[int]=None,
                    allowed_updates: Optional[List]=None,
                    ip_address: Optional[str]=None,
                    drop_pending_updates: Optional[bool] = None,
                    timeout: Optional[int]=None,
                    secret_token: Optional[str]=None,
                    secret_token_length: Optional[int]=20,
                    debug: Optional[bool]=False):
        """
        This class sets webhooks and listens to a given url and port.

        Requires fastapi, uvicorn, and latest version of starlette.

        :param listen: IP address to listen to, defaults to "127.0.0.1"
        :type listen: :obj:`str`, optional

        :param port: A port which will be used to listen to webhooks., defaults to 443
        :type port: :obj:`int`, optional

        :param url_path: Path to the webhook. Defaults to /token, defaults to None
        :type url_path: :obj:`str`, optional

        :param certificate: Path to the certificate file, defaults to None
        :type certificate: :obj:`str`, optional

        :param certificate_key: Path to the certificate key file, defaults to None
        :type certificate_key: :obj:`str`, optional

        :param webhook_url: Webhook URL to be set, defaults to None
        :type webhook_url: :obj:`str`, optional

        :param max_connections: Maximum allowed number of simultaneous HTTPS connections
                to the webhook for update delivery, 1-100. Defaults to 40. Use lower values to limit the load on your bot's server,
                and higher values to increase your bot's throughput., defaults to None
        :type max_connections: :obj:`int`, optional

        :param allowed_updates: A JSON-serialized list of the update types you want your bot to receive. For example, specify [“message”, “edited_channel_post”, “callback_query”]
            to only receive updates of these types. See Update for a complete list of available update types. Specify an empty list to receive all updates regardless of type (default). 
            If not specified, the previous setting will be used. defaults to None
        :type allowed_updates: :obj:`list`, optional

        :param ip_address: The fixed IP address which will be used to send webhook requests instead of the IP address resolved through DNS, defaults to None
        :type ip_address: :obj:`str`, optional

        :param drop_pending_updates: Pass True to drop all pending updates, defaults to None
        :type drop_pending_updates: :obj:`bool`, optional

        :param timeout: Request connection timeout, defaults to None
        :type timeout: :obj:`int`, optional

        :param secret_token: Secret token to be used to verify the webhook request, defaults to None
        :type secret_token: :obj:`str`, optional

        :param secret_token_length: Length of a secret token, defaults to 20
        :type secret_token_length: :obj:`int`, optional

        :param debug: set True if you want to set debugging on for webserver, defaults to False
        :type debug: :obj:`bool`, optional

        :raises ImportError: If necessary libraries were not installed.
        """

        # generate secret token if not set
        if not secret_token:
            secret_token = ''.join(random.choices(string.ascii_uppercase + string.digits, k=secret_token_length))

        if not url_path:
            url_path = self.token + '/'
        if url_path[-1] != '/': url_path += '/'
        
        protocol = "https" if certificate else "http"
        if not webhook_url:
            webhook_url = "{}://{}:{}/{}".format(protocol, listen, port, url_path)

        if certificate and certificate_key:
            ssl_ctx = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
            ssl_ctx.load_cert_chain(certificate, certificate_key)

        # open certificate if it exists
        cert_file = open(certificate, 'rb') if certificate else None
        self.set_webhook(
            url=webhook_url,
            certificate=cert_file,
            max_connections=max_connections,
            allowed_updates=allowed_updates,
            ip_address=ip_address,
            drop_pending_updates=drop_pending_updates,
            timeout=timeout,
            secret_token=secret_token
        )
        if cert_file: cert_file.close()

        ssl_context = (certificate, certificate_key) if certificate else (None, None)
        # webhooks module
        try:
            from telebot.ext.sync import SyncWebhookListener
        except (NameError, ImportError):
            raise ImportError("Please install uvicorn and fastapi in order to use `run_webhooks` method.")
        self.webhook_listener = SyncWebhookListener(self, secret_token, listen, port, ssl_context, '/'+url_path, debug)
        self.webhook_listener.run_app()


    def delete_webhook(self, drop_pending_updates: Optional[bool]=None, timeout: Optional[int]=None) -> bool:
        """
        Use this method to remove webhook integration if you decide to switch back to getUpdates.
        Returns True on success.

        Telegram documentation: https://core.telegram.org/bots/api#deletewebhook

        :param drop_pending_updates: Pass True to drop all pending updates, defaults to None
        :type drop_pending_updates: :obj: `bool`, optional

        :param timeout: Request connection timeout, defaults to None
        :type timeout: :obj:`int`, optional

        :return: Returns True on success.
        :rtype: :obj:`bool`
        """
        return apihelper.delete_webhook(self.token, drop_pending_updates, timeout)


    def get_webhook_info(self, timeout: Optional[int]=None) -> types.WebhookInfo:
        """
        Use this method to get current webhook status. Requires no parameters.
        On success, returns a WebhookInfo object. If the bot is using getUpdates, will return an object with the url field empty.

        Telegram documentation: https://core.telegram.org/bots/api#getwebhookinfo

        :param timeout: Request connection timeout
        :type timeout: :obj:`int`, optional

        :return: On success, returns a WebhookInfo object.
        :rtype: :class:`telebot.types.WebhookInfo`
        """
        result = apihelper.get_webhook_info(self.token, timeout)
        return types.WebhookInfo.de_json(result)


    def remove_webhook(self) -> bool:
        """
        Deletes webhooks using set_webhook() function.

        :return: True on success.
        :rtype: :obj:`bool`
        """
        return self.set_webhook()  # No params resets webhook


    def get_updates(self, offset: Optional[int]=None, limit: Optional[int]=None, 
            timeout: Optional[int]=20, allowed_updates: Optional[List[str]]=None, 
            long_polling_timeout: int=20) -> List[types.Update]:
        """
        Use this method to receive incoming updates using long polling (wiki). An Array of Update objects is returned.

        Telegram documentation: https://core.telegram.org/bots/api#getupdates


        :param offset: Identifier of the first update to be returned. Must be greater by one than the highest among the identifiers of previously received updates.
            By default, updates starting with the earliest unconfirmed update are returned. An update is considered confirmed as soon as getUpdates is called with an offset
            higher than its update_id. The negative offset can be specified to retrieve updates starting from -offset update from the end of the updates queue.
            All previous updates will forgotten.
        :type offset: :obj:`int`, optional

        :param limit: Limits the number of updates to be retrieved. Values between 1-100 are accepted. Defaults to 100.
        :type limit: :obj:`int`, optional

        :param timeout: Request connection timeout
        :type timeout: :obj:`int`, optional

        :param allowed_updates: Array of string. List the types of updates you want your bot to receive.
        :type allowed_updates: :obj:`list`, optional

        :param long_polling_timeout: Timeout in seconds for long polling.
        :type long_polling_timeout: :obj:`int`, optional

        :return: An Array of Update objects is returned.
        :rtype: :obj:`list` of :class:`telebot.types.Update`
        """
        json_updates = apihelper.get_updates(self.token, offset, limit, timeout, allowed_updates, long_polling_timeout)
        return [types.Update.de_json(ju) for ju in json_updates]

    def __skip_updates(self):
        """
        Get and discard all pending updates before first poll of the bot.

        :meta private:

        :return:
        """
        self.get_updates(offset=-1)

    def __retrieve_updates(self, timeout=20, long_polling_timeout=20, allowed_updates=None):
        """
        Retrieves any updates from the Telegram API.
        Registered listeners and applicable message handlers will be notified when a new message arrives.

        :meta private:
        
        :raises ApiException when a call has failed.
        """
        if self.skip_pending:
            self.__skip_updates()
            logger.debug('Skipped all pending messages')
            self.skip_pending = False
        updates = self.get_updates(offset=(self.last_update_id + 1), 
                                   allowed_updates=allowed_updates,
                                   timeout=timeout, long_polling_timeout=long_polling_timeout)
        self.process_new_updates(updates)

    def process_new_updates(self, updates: List[types.Update]):
        """
        Processes new updates. Just pass list of subclasses of Update to this method.

        :param updates: List of :class:`telebot.types.Update` objects.
        :type updates: :obj:`list` of :class:`telebot.types.Update`

        :return None:
        """
        upd_count = len(updates)
        logger.debug('Received {0} new updates'.format(upd_count))
        if upd_count == 0: return

        new_messages = None
        new_edited_messages = None
        new_channel_posts = None
        new_edited_channel_posts = None
        new_inline_queries = None
        new_chosen_inline_results = None
        new_callback_queries = None
        new_shipping_queries = None
        new_pre_checkout_queries = None
        new_polls = None
        new_poll_answers = None
        new_my_chat_members = None
        new_chat_members = None
        new_chat_join_request = None
        
        for update in updates:
            if apihelper.ENABLE_MIDDLEWARE and not self.use_class_middlewares:
                try:
                    self.process_middlewares(update)
                except Exception as e:
                    logger.error(str(e))
                    if not self.suppress_middleware_excepions:
                        raise
                    else:
                        if update.update_id > self.last_update_id: self.last_update_id = update.update_id
                        continue

            if update.update_id > self.last_update_id:
                self.last_update_id = update.update_id
            if update.message:
                if new_messages is None: new_messages = []
                new_messages.append(update.message)
            if update.edited_message:
                if new_edited_messages is None: new_edited_messages = []
                new_edited_messages.append(update.edited_message)
            if update.channel_post:
                if new_channel_posts is None: new_channel_posts = []
                new_channel_posts.append(update.channel_post)
            if update.edited_channel_post:
                if new_edited_channel_posts is None: new_edited_channel_posts = []
                new_edited_channel_posts.append(update.edited_channel_post)
            if update.inline_query:
                if new_inline_queries is None: new_inline_queries = []
                new_inline_queries.append(update.inline_query)
            if update.chosen_inline_result:
                if new_chosen_inline_results is None: new_chosen_inline_results = []
                new_chosen_inline_results.append(update.chosen_inline_result)
            if update.callback_query:
                if new_callback_queries is None: new_callback_queries = []
                new_callback_queries.append(update.callback_query)
            if update.shipping_query:
                if new_shipping_queries is None: new_shipping_queries = []
                new_shipping_queries.append(update.shipping_query)
            if update.pre_checkout_query:
                if new_pre_checkout_queries is None: new_pre_checkout_queries = []
                new_pre_checkout_queries.append(update.pre_checkout_query)
            if update.poll:
                if new_polls is None: new_polls = []
                new_polls.append(update.poll)
            if update.poll_answer:
                if new_poll_answers is None: new_poll_answers = []
                new_poll_answers.append(update.poll_answer)
            if update.my_chat_member:
                if new_my_chat_members is None: new_my_chat_members = []
                new_my_chat_members.append(update.my_chat_member)
            if update.chat_member:
                if new_chat_members is None: new_chat_members = []
                new_chat_members.append(update.chat_member)
            if update.chat_join_request:
                if new_chat_join_request is None: new_chat_join_request = []
                new_chat_join_request.append(update.chat_join_request)

        if new_messages:
            self.process_new_messages(new_messages)
        if new_edited_messages:
            self.process_new_edited_messages(new_edited_messages)
        if new_channel_posts:
            self.process_new_channel_posts(new_channel_posts)
        if new_edited_channel_posts:
            self.process_new_edited_channel_posts(new_edited_channel_posts)
        if new_inline_queries:
            self.process_new_inline_query(new_inline_queries)
        if new_chosen_inline_results:
            self.process_new_chosen_inline_query(new_chosen_inline_results)
        if new_callback_queries:
            self.process_new_callback_query(new_callback_queries)
        if new_shipping_queries:
            self.process_new_shipping_query(new_shipping_queries)
        if new_pre_checkout_queries:
            self.process_new_pre_checkout_query(new_pre_checkout_queries)
        if new_polls:
            self.process_new_poll(new_polls)
        if new_poll_answers:
            self.process_new_poll_answer(new_poll_answers)
        if new_my_chat_members:
            self.process_new_my_chat_member(new_my_chat_members)
        if new_chat_members:
            self.process_new_chat_member(new_chat_members)
        if new_chat_join_request:
            self.process_new_chat_join_request(new_chat_join_request)

    def process_new_messages(self, new_messages):
        """
        :meta private:
        """
        self._notify_next_handlers(new_messages)
        self._notify_reply_handlers(new_messages)
        self.__notify_update(new_messages)
        self._notify_command_handlers(self.message_handlers, new_messages, 'message')

    def process_new_edited_messages(self, edited_message):
        """
        :meta private:
        """
        self._notify_command_handlers(self.edited_message_handlers, edited_message, 'edited_message')

    def process_new_channel_posts(self, channel_post):
        """
        :meta private:
        """
        self._notify_command_handlers(self.channel_post_handlers, channel_post, 'channel_post')

    def process_new_edited_channel_posts(self, edited_channel_post):
        """
        :meta private:
        """
        self._notify_command_handlers(self.edited_channel_post_handlers, edited_channel_post, 'edited_channel_post')

    def process_new_inline_query(self, new_inline_querys):
        """
        :meta private:
        """
        self._notify_command_handlers(self.inline_handlers, new_inline_querys, 'inline_query')

    def process_new_chosen_inline_query(self, new_chosen_inline_querys):
        """
        :meta private:
        """
        self._notify_command_handlers(self.chosen_inline_handlers, new_chosen_inline_querys, 'chosen_inline_query')

    def process_new_callback_query(self, new_callback_querys):
        """
        :meta private:
        """
        self._notify_command_handlers(self.callback_query_handlers, new_callback_querys, 'callback_query')

    def process_new_shipping_query(self, new_shipping_querys):
        """
        :meta private:
        """
        self._notify_command_handlers(self.shipping_query_handlers, new_shipping_querys, 'shipping_query')

    def process_new_pre_checkout_query(self, pre_checkout_querys):
        """
        :meta private:
        """
        self._notify_command_handlers(self.pre_checkout_query_handlers, pre_checkout_querys, 'pre_checkout_query')

    def process_new_poll(self, polls):
        """
        :meta private:
        """
        self._notify_command_handlers(self.poll_handlers, polls, 'poll')

    def process_new_poll_answer(self, poll_answers):
        """
        :meta private:
        """
        self._notify_command_handlers(self.poll_answer_handlers, poll_answers, 'poll_answer')
    
    def process_new_my_chat_member(self, my_chat_members):
        """
        :meta private:
        """
        self._notify_command_handlers(self.my_chat_member_handlers, my_chat_members, 'my_chat_member')

    def process_new_chat_member(self, chat_members):
        """
        :meta private:
        """
        self._notify_command_handlers(self.chat_member_handlers, chat_members, 'chat_member')

    def process_new_chat_join_request(self, chat_join_request):
        """
        :meta private:
        """
        self._notify_command_handlers(self.chat_join_request_handlers, chat_join_request, 'chat_join_request')

    def process_middlewares(self, update):
        """
        :meta private:
        """
        if self.typed_middleware_handlers:
            for update_type, middlewares in self.typed_middleware_handlers.items():
                if getattr(update, update_type) is not None:
                    for typed_middleware_handler in middlewares:
                        try:
                            typed_middleware_handler(self, getattr(update, update_type))
                        except Exception as e:
                            e.args = e.args + (f'Typed middleware handler "{typed_middleware_handler.__qualname__}"',)
                            raise

        if self.default_middleware_handlers:
            for default_middleware_handler in self.default_middleware_handlers:
                try:
                    default_middleware_handler(self, update)
                except Exception as e:
                    e.args = e.args + (f'Default middleware handler "{default_middleware_handler.__qualname__}"',)
                    raise


    def __notify_update(self, new_messages):
        """
        :meta private:
        """
        if len(self.update_listener) == 0:
            return
        for listener in self.update_listener:
            self._exec_task(listener, new_messages)


    def infinity_polling(self, timeout: Optional[int]=20, skip_pending: Optional[bool]=False, long_polling_timeout: Optional[int]=20,
                         logger_level: Optional[int]=logging.ERROR, allowed_updates: Optional[List[str]]=None, *args, **kwargs):
        """
        Wrap polling with infinite loop and exception handling to avoid bot stops polling.

        :param timeout: Request connection timeout.
        :type timeout: :obj:`int`

        :param long_polling_timeout: Timeout in seconds for long polling (see API docs)
        :type long_polling_timeout: :obj:`int`

        :param skip_pending: skip old updates
        :type skip_pending: :obj:`bool`

        :param logger_level: Custom (different from logger itself) logging level for infinity_polling logging.
            Use logger levels from logging as a value. None/NOTSET = no error logging
        :type logger_level: :obj:`int`.

        :param allowed_updates: A list of the update types you want your bot to receive.
            For example, specify [“message”, “edited_channel_post”, “callback_query”] to only receive updates of these types. 
            See util.update_types for a complete list of available update types. 
            Specify an empty list to receive all update types except chat_member (default). 
            If not specified, the previous setting will be used.
            Please note that this parameter doesn't affect updates created before the call to the get_updates, 
            so unwanted updates may be received for a short period of time.
        :type allowed_updates: :obj:`list` of :obj:`str`

        :return:
        """
        if skip_pending:
            self.__skip_updates()

        while not self.__stop_polling.is_set():
            try:
                self.polling(non_stop=True, timeout=timeout, long_polling_timeout=long_polling_timeout,
                             logger_level=logger_level, allowed_updates=allowed_updates, *args, **kwargs)
            except Exception as e:
                if logger_level and logger_level >= logging.ERROR:
                    logger.error("Infinity polling exception: %s", str(e))
                if logger_level and logger_level >= logging.DEBUG:
                    logger.error("Exception traceback:\n%s", traceback.format_exc())
                time.sleep(3)
                continue
            if logger_level and logger_level >= logging.INFO:
                logger.error("Infinity polling: polling exited")
        if logger_level and logger_level >= logging.INFO:
            logger.error("Break infinity polling")


    def polling(self, non_stop: Optional[bool]=False, skip_pending: Optional[bool]=False, interval: Optional[int]=0,
                timeout: Optional[int]=20, long_polling_timeout: Optional[int]=20,
                logger_level: Optional[int]=logging.ERROR, allowed_updates: Optional[List[str]]=None,
                none_stop: Optional[bool]=None):
        """
        This function creates a new Thread that calls an internal __retrieve_updates function.
        This allows the bot to retrieve Updates automatically and notify listeners and message handlers accordingly.

        Warning: Do not call this function more than once!
        
        Always gets updates.

        .. deprecated:: 4.1.1
            Use :meth:`infinity_polling` instead.

        :param interval: Delay between two update retrivals
        :type interval: :obj:`int`

        :param non_stop: Do not stop polling when an ApiException occurs.
        :type non_stop: :obj:`bool`

        :param timeout: Request connection timeout
        :type timeout: :obj:`int`

        :param skip_pending: skip old updates
        :type skip_pending: :obj:`bool`
        
        :param long_polling_timeout: Timeout in seconds for long polling (see API docs)
        :type long_polling_timeout: :obj:`int`

        :param logger_level: Custom (different from logger itself) logging level for infinity_polling logging.
            Use logger levels from logging as a value. None/NOTSET = no error logging
        :type logger_level: :obj:`int`

        :param allowed_updates: A list of the update types you want your bot to receive.
            For example, specify [“message”, “edited_channel_post”, “callback_query”] to only receive updates of these types. 
            See util.update_types for a complete list of available update types. 
            Specify an empty list to receive all update types except chat_member (default). 
            If not specified, the previous setting will be used.
            
            Please note that this parameter doesn't affect updates created before the call to the get_updates, 
            so unwanted updates may be received for a short period of time.
        :type allowed_updates: :obj:`list` of :obj:`str`

        :param none_stop: Deprecated, use non_stop. Old typo, kept for backward compatibility.
        :type none_stop: :obj:`bool`
        
        :return:
        """
        if none_stop is not None:
            logger.warning("polling: none_stop parameter is deprecated. Use non_stop instead.")
            non_stop = none_stop

        if skip_pending:
            self.__skip_updates()
            
        if self.threaded:
            self.__threaded_polling(non_stop=non_stop, interval=interval, timeout=timeout, long_polling_timeout=long_polling_timeout,
                                    logger_level=logger_level, allowed_updates=allowed_updates)
        else:
            self.__non_threaded_polling(non_stop=non_stop, interval=interval, timeout=timeout, long_polling_timeout=long_polling_timeout,
                                        logger_level=logger_level, allowed_updates=allowed_updates)


    def __threaded_polling(self, non_stop = False, interval = 0, timeout = None, long_polling_timeout = None,
                           logger_level=logging.ERROR, allowed_updates=None):
        if not(logger_level) or (logger_level < logging.INFO):
            warning = "\n  Warning: this message appearance will be changed. Set logger_level=logging.INFO to continue seeing it."
        else:
            warning = ""
        #if logger_level and logger_level >= logging.INFO:   # enable in future releases. Change output to logger.error
        logger.info('Started polling.' + warning)
        self.__stop_polling.clear()
        error_interval = 0.25

        polling_thread = util.WorkerThread(name="PollingThread")
        or_event = util.OrEvent(
            polling_thread.done_event,
            polling_thread.exception_event,
            self.worker_pool.exception_event
        )

        while not self.__stop_polling.wait(interval):
            or_event.clear()
            try:
                polling_thread.put(self.__retrieve_updates, timeout, long_polling_timeout, allowed_updates=allowed_updates)
                or_event.wait()  # wait for polling thread finish, polling thread error or thread pool error
                polling_thread.raise_exceptions()
                self.worker_pool.raise_exceptions()
                error_interval = 0.25
            except apihelper.ApiException as e:
                if self.exception_handler is not None:
                    handled = self.exception_handler.handle(e)
                else:
                    handled = False
                if not handled:
                    if logger_level and logger_level >= logging.ERROR:
                        logger.error("Threaded polling exception: %s", str(e))
                    if logger_level and logger_level >= logging.DEBUG:
                        logger.error("Exception traceback:\n%s", traceback.format_exc())
                    if not non_stop:
                        self.__stop_polling.set()
                        # if logger_level and logger_level >= logging.INFO:   # enable in future releases. Change output to logger.error
                        logger.info("Exception occurred. Stopping." + warning)
                    else:
                        # if logger_level and logger_level >= logging.INFO:   # enable in future releases. Change output to logger.error
                        logger.info("Waiting for {0} seconds until retry".format(error_interval) + warning)
                        time.sleep(error_interval)
                        if error_interval * 2 < 60:
                            error_interval *= 2
                        else:
                            error_interval = 60
                else:
                    # polling_thread.clear_exceptions()
                    # self.worker_pool.clear_exceptions()
                    time.sleep(error_interval)
                polling_thread.clear_exceptions()   #*
                self.worker_pool.clear_exceptions() #*
            except KeyboardInterrupt:
                # if logger_level and logger_level >= logging.INFO:   # enable in future releases. Change output to logger.error
                logger.info("KeyboardInterrupt received." + warning)
                self.__stop_polling.set()
                break
            except Exception as e:
                if self.exception_handler is not None:
                    handled = self.exception_handler.handle(e)
                else:
                    handled = False
                if not handled:
                    polling_thread.stop()
                    polling_thread.clear_exceptions()   #*
                    self.worker_pool.clear_exceptions() #*
                    raise e
                else:
                    polling_thread.clear_exceptions()
                    self.worker_pool.clear_exceptions()
                    time.sleep(error_interval)

        polling_thread.stop()
        polling_thread.clear_exceptions()
        self.worker_pool.clear_exceptions()
        #if logger_level and logger_level >= logging.INFO:   # enable in future releases. Change output to logger.error
        logger.info('Stopped polling.' + warning)


    def __non_threaded_polling(self, non_stop=False, interval=0, timeout=None, long_polling_timeout=None,
                               logger_level=logging.ERROR, allowed_updates=None):
        if not(logger_level) or (logger_level < logging.INFO):
            warning = "\n  Warning: this message appearance will be changed. Set logger_level=logging.INFO to continue seeing it."
        else:
            warning = ""
        #if logger_level and logger_level >= logging.INFO:   # enable in future releases. Change output to logger.error
        logger.info('Started polling.' + warning)
        self.__stop_polling.clear()
        error_interval = 0.25

        while not self.__stop_polling.wait(interval):
            try:
                self.__retrieve_updates(timeout, long_polling_timeout, allowed_updates=allowed_updates)
                error_interval = 0.25
            except apihelper.ApiException as e:
                if self.exception_handler is not None:
                    handled = self.exception_handler.handle(e)
                else:
                    handled = False

                if not handled:
                    if logger_level and logger_level >= logging.ERROR:
                        logger.error("Polling exception: %s", str(e))
                    if logger_level and logger_level >= logging.DEBUG:
                        logger.error("Exception traceback:\n%s", traceback.format_exc())
                    if not non_stop:
                        self.__stop_polling.set()
                        # if logger_level and logger_level >= logging.INFO:   # enable in future releases. Change output to logger.error
                        logger.info("Exception occurred. Stopping." + warning)
                    else:
                        # if logger_level and logger_level >= logging.INFO:   # enable in future releases. Change output to logger.error
                        logger.info("Waiting for {0} seconds until retry".format(error_interval) + warning)
                        time.sleep(error_interval)
                        error_interval *= 2
                else:
                    time.sleep(error_interval)
            except KeyboardInterrupt:
                # if logger_level and logger_level >= logging.INFO:   # enable in future releases. Change output to logger.error
                logger.info("KeyboardInterrupt received." + warning)
                self.__stop_polling.set()
                break
            except Exception as e:
                if self.exception_handler is not None:
                    handled = self.exception_handler.handle(e)
                else:
                    handled = False
                if not handled:
                    raise e
                else:
                    time.sleep(error_interval)
        #if logger_level and logger_level >= logging.INFO:   # enable in future releases. Change output to logger.error
        logger.info('Stopped polling.' + warning)


    def _exec_task(self, task, *args, **kwargs):
        if kwargs and kwargs.get('task_type') == 'handler':
            pass_bot = kwargs.get('pass_bot')
            kwargs.pop('pass_bot')
            kwargs.pop('task_type')
            if pass_bot:
                kwargs['bot'] = self
        
        if self.threaded:
            self.worker_pool.put(task, *args, **kwargs)
        else:
            try:
                task(*args, **kwargs)
            except Exception as e:
                if self.exception_handler is not None:
                    handled = self.exception_handler.handle(e)
                else:
                    handled = False
                if not handled:
                    raise e


    def stop_polling(self):
        """
        Stops polling.

        Does not accept any arguments.
        """
        self.__stop_polling.set()


    def stop_bot(self):
        """
        Stops bot by stopping polling and closing the worker pool.
        """
        self.stop_polling()
        if self.threaded and self.worker_pool:
            self.worker_pool.close()


    def set_update_listener(self, listener: Callable):
        """
        Sets a listener function to be called when a new update is received.

        :param listener: Listener function.
        :type listener: Callable
        """
        self.update_listener.append(listener)


    def get_me(self) -> types.User:
        """
        A simple method for testing your bot's authentication token. Requires no parameters.
        Returns basic information about the bot in form of a User object.

        Telegram documentation: https://core.telegram.org/bots/api#getme
        """
        result = apihelper.get_me(self.token)
        return types.User.de_json(result)


    def get_file(self, file_id: Optional[str]) -> types.File:
        """
        Use this method to get basic info about a file and prepare it for downloading.
        For the moment, bots can download files of up to 20MB in size. 
        On success, a File object is returned. 
        It is guaranteed that the link will be valid for at least 1 hour. 
        When the link expires, a new one can be requested by calling get_file again.

        Telegram documentation: https://core.telegram.org/bots/api#getfile

        :param file_id: File identifier
        :type file_id: :obj:`str`

        :return: :class:`telebot.types.File`
        """
        return types.File.de_json(apihelper.get_file(self.token, file_id))


    def get_file_url(self, file_id: Optional[str]) -> str:
        """
        Get a valid URL for downloading a file.

        :param file_id: File identifier to get download URL for.
        :type file_id: :obj:`str`

        :return: URL for downloading the file.
        :rtype: :obj:`str`
        """
        return apihelper.get_file_url(self.token, file_id)


    def download_file(self, file_path: str) -> bytes:
        """
        Downloads file.

        :param file_path: Path where the file should be downloaded.
        :type file_path: str

        :return: bytes
        :rtype: :obj:`bytes`
        """
        return apihelper.download_file(self.token, file_path)


    def log_out(self) -> bool:
        """
        Use this method to log out from the cloud Bot API server before launching the bot locally. 
        You MUST log out the bot before running it locally, otherwise there is no guarantee
        that the bot will receive updates.
        After a successful call, you can immediately log in on a local server, 
        but will not be able to log in back to the cloud Bot API server for 10 minutes. 
        Returns True on success.

        Telegram documentation: https://core.telegram.org/bots/api#logout

        :return: True on success.
        :rtype: :obj:`bool`
        """
        return apihelper.log_out(self.token)
    
    
    def close(self) -> bool:
        """
        Use this method to close the bot instance before moving it from one local server to another. 
        You need to delete the webhook before calling this method to ensure that the bot isn't launched again
        after server restart.
        The method will return error 429 in the first 10 minutes after the bot is launched. 
        Returns True on success.

        Telegram documentation: https://core.telegram.org/bots/api#close

        :return: :obj:`bool`
        """
        return apihelper.close(self.token)


    def get_user_profile_photos(self, user_id: int, offset: Optional[int]=None, 
            limit: Optional[int]=None) -> types.UserProfilePhotos:
        """
        Use this method to get a list of profile pictures for a user.
        Returns a :class:`telebot.types.UserProfilePhotos` object.

        Telegram documentation: https://core.telegram.org/bots/api#getuserprofilephotos

        :param user_id: Unique identifier of the target user
        :type user_id: :obj:`int`

        :param offset: Sequential number of the first photo to be returned. By default, all photos are returned.
        :type offset: :obj:`int`

        :param limit: Limits the number of photos to be retrieved. Values between 1-100 are accepted. Defaults to 100.
        :type limit: :obj:`int`

        :return: `UserProfilePhotos <https://core.telegram.org/bots/api#userprofilephotos>`_
        :rtype: :class:`telebot.types.UserProfilePhotos`

        """
        result = apihelper.get_user_profile_photos(self.token, user_id, offset, limit)
        return types.UserProfilePhotos.de_json(result)


    def get_chat(self, chat_id: Union[int, str]) -> types.Chat:
        """
        Use this method to get up to date information about the chat (current name of the user for one-on-one
        conversations, current username of a user, group or channel, etc.). Returns a Chat object on success.

        Telegram documentation: https://core.telegram.org/bots/api#getchat

        :param chat_id: Unique identifier for the target chat or username of the target supergroup or channel (in the format @channelusername)
        :type chat_id: :obj:`int` or :obj:`str`

        :return: Chat information
        :rtype: :class:`telebot.types.Chat`
        """
        result = apihelper.get_chat(self.token, chat_id)
        return types.Chat.de_json(result)


    def leave_chat(self, chat_id: Union[int, str]) -> bool:
        """
        Use this method for your bot to leave a group, supergroup or channel. Returns True on success.

        Telegram documentation: https://core.telegram.org/bots/api#leavechat

        :param chat_id: Unique identifier for the target chat or username of the target supergroup or channel (in the format @channelusername)
        :type chat_id: :obj:`int` or :obj:`str`

        :return: :obj:`bool`
        """
        result = apihelper.leave_chat(self.token, chat_id)
        return result


    def get_chat_administrators(self, chat_id: Union[int, str]) -> List[types.ChatMember]:
        """
        Use this method to get a list of administrators in a chat.
        On success, returns an Array of ChatMember objects that contains
        information about all chat administrators except other bots.

        Telegram documentation: https://core.telegram.org/bots/api#getchatadministrators    

        :param chat_id: Unique identifier for the target chat or username
            of the target supergroup or channel (in the format @channelusername)
        :return: List made of ChatMember objects.
        :rtype: :obj:`list` of :class:`telebot.types.ChatMember`
        """
        result = apihelper.get_chat_administrators(self.token, chat_id)
        return [types.ChatMember.de_json(r) for r in result]


    @util.deprecated(deprecation_text="Use get_chat_member_count instead")
    def get_chat_members_count(self, chat_id: Union[int, str]) -> int:
        """
        This function is deprecated. Use `get_chat_member_count` instead.

        .. deprecated:: 4.0.0
            This function is deprecated. Use `get_chat_member_count` instead.

        Use this method to get the number of members in a chat.

        Telegram documentation: https://core.telegram.org/bots/api#getchatmembercount

        :param chat_id: Unique identifier for the target chat or username of the target supergroup or channel (in the format @channelusername)
        :type chat_id: :obj:`int` or :obj:`str`

        :return: Number of members in the chat.
        :rtype: :obj:`int`
        """
        result = apihelper.get_chat_member_count(self.token, chat_id)
        return result
    
    def get_chat_member_count(self, chat_id: Union[int, str]) -> int:
        """
        Use this method to get the number of members in a chat.

        Telegram documentation: https://core.telegram.org/bots/api#getchatmembercount

        :param chat_id: Unique identifier for the target chat or username of the target supergroup or channel (in the format @channelusername)
        :type chat_id: :obj:`int` or :obj:`str`

        :return: Number of members in the chat.
        :rtype: :obj:`int`
        """
        result = apihelper.get_chat_member_count(self.token, chat_id)
        return result

    def set_chat_sticker_set(self, chat_id: Union[int, str], sticker_set_name: str) -> types.StickerSet:
        """
        Use this method to set a new group sticker set for a supergroup. The bot must be an administrator in the chat
        for this to work and must have the appropriate administrator rights. Use the field can_set_sticker_set optionally returned
        in getChat requests to check if the bot can use this method. Returns True on success.
        
        Telegram documentation: https://core.telegram.org/bots/api#setchatstickerset

        :param chat_id: Unique identifier for the target chat or username of the target supergroup (in the format @supergroupusername)
        :type chat_id: :obj:`int` or :obj:`str`

        :param sticker_set_name: Name of the sticker set to be set as the group sticker set
        :type sticker_set_name: :obj:`str`

        :return: StickerSet object
        :rtype: :class:`telebot.types.StickerSet`
        """
        result = apihelper.set_chat_sticker_set(self.token, chat_id, sticker_set_name)
        return result

    def delete_chat_sticker_set(self, chat_id: Union[int, str]) -> bool:
        """
        Use this method to delete a group sticker set from a supergroup. The bot must be an administrator in the chat
        for this to work and must have the appropriate admin rights. Use the field can_set_sticker_set
        optionally returned in getChat requests to check if the bot can use this method. Returns True on success.
        
        Telegram documentation: https://core.telegram.org/bots/api#deletechatstickerset

        :param chat_id:	Unique identifier for the target chat or username of the target supergroup (in the format @supergroupusername)
        :type chat_id: :obj:`int` or :obj:`str`

        :return: Returns True on success.
        :rtype: :obj:`bool`
        """
        result = apihelper.delete_chat_sticker_set(self.token, chat_id)
        return result

    def get_chat_member(self, chat_id: Union[int, str], user_id: int) -> types.ChatMember:
        """
        Use this method to get information about a member of a chat. Returns a ChatMember object on success.
        
        Telegram documentation: https://core.telegram.org/bots/api#getchatmember

        :param chat_id: Unique identifier for the target chat or username of the target supergroup (in the format @supergroupusername)
        :type chat_id: :obj:`int` or :obj:`str`

        :param user_id: Unique identifier of the target user
        :type user_id: :obj:`int`

        :return: Returns ChatMember object on success.
        :rtype: :class:`telebot.types.ChatMember`
        """
        result = apihelper.get_chat_member(self.token, chat_id, user_id)
        return types.ChatMember.de_json(result)

    def send_message(
            self, chat_id: Union[int, str], text: str, 
            parse_mode: Optional[str]=None, 
            entities: Optional[List[types.MessageEntity]]=None,
            disable_web_page_preview: Optional[bool]=None, 
            disable_notification: Optional[bool]=None, 
            protect_content: Optional[bool]=None,
            reply_to_message_id: Optional[int]=None, 
            allow_sending_without_reply: Optional[bool]=None,
            reply_markup: Optional[REPLY_MARKUP_TYPES]=None,
            timeout: Optional[int]=None) -> types.Message:
        """
        Use this method to send text messages.

        Warning: Do not send more than about 4096 characters each message, otherwise you'll risk an HTTP 414 error.
        If you must send more than 4096 characters, 
        use the `split_string` or `smart_split` function in util.py.

        Telegram documentation: https://core.telegram.org/bots/api#sendmessage

        :param chat_id: Unique identifier for the target chat or username of the target channel (in the format @channelusername)
        :type chat_id: :obj:`int` or :obj:`str`

        :param text: Text of the message to be sent
        :type text: :obj:`str`

        :param parse_mode: Mode for parsing entities in the message text.
        :type parse_mode: :obj:`str`

        :param entities: List of special entities that appear in message text, which can be specified instead of parse_mode
        :type entities: Array of :class:`telebot.types.MessageEntity`

        :param disable_web_page_preview: Disables link previews for links in this message
        :type disable_web_page_preview: :obj:`bool`

        :param disable_notification: Sends the message silently. Users will receive a notification with no sound.
        :type disable_notification: :obj:`bool`

        :param protect_content: If True, the message content will be hidden for all users except for the target user
        :type protect_content: :obj:`bool`

        :param reply_to_message_id: If the message is a reply, ID of the original message
        :type reply_to_message_id: :obj:`int`

        :param allow_sending_without_reply: Pass True, if the message should be sent even if the specified replied-to message is not found
        :type allow_sending_without_reply: :obj:`bool`

        :param reply_markup: Additional interface options. A JSON-serialized object for an inline keyboard, custom reply keyboard, instructions to remove reply keyboard or to force a reply from the user.
        :type reply_markup: :class:`telebot.types.InlineKeyboardMarkup` or :class:`telebot.types.ReplyKeyboardMarkup` or :class:`telebot.types.ReplyKeyboardRemove`
            or :class:`telebot.types.ForceReply`

        :param timeout: Timeout in seconds for the request.
        :type timeout: :obj:`int`

        :return: On success, the sent Message is returned.
        :rtype: :class:`telebot.types.Message`
        """
        parse_mode = self.parse_mode if (parse_mode is None) else parse_mode

        return types.Message.de_json(
            apihelper.send_message(
                self.token, chat_id, text, disable_web_page_preview, reply_to_message_id,
                reply_markup, parse_mode, disable_notification, timeout,
                entities, allow_sending_without_reply, protect_content=protect_content))

    def forward_message(
            self, chat_id: Union[int, str], from_chat_id: Union[int, str], 
            message_id: int, disable_notification: Optional[bool]=None,
            protect_content: Optional[bool]=None,
            timeout: Optional[int]=None) -> types.Message:
        """
        Use this method to forward messages of any kind.

        Telegram documentation: https://core.telegram.org/bots/api#forwardmessage

        :param disable_notification: Sends the message silently. Users will receive a notification with no sound
        :type disable_notification: :obj:`bool`

        :param chat_id: Unique identifier for the target chat or username of the target channel (in the format @channelusername)
        :type chat_id: :obj:`int` or :obj:`str`

        :param from_chat_id: Unique identifier for the chat where the original message was sent (or channel username in the format @channelusername)
        :type from_chat_id: :obj:`int` or :obj:`str`

        :param message_id: Message identifier in the chat specified in from_chat_id
        :type message_id: :obj:`int`

        :param protect_content: Protects the contents of the forwarded message from forwarding and saving
        :type protect_content: :obj:`bool`

        :param timeout: Timeout in seconds for the request.
        :type timeout: :obj:`int`

        :return: On success, the sent Message is returned.
        :rtype: :class:`telebot.types.Message`
        """
        return types.Message.de_json(
            apihelper.forward_message(self.token, chat_id, from_chat_id, message_id, disable_notification, timeout, protect_content))


    def copy_message(
            self, chat_id: Union[int, str], 
            from_chat_id: Union[int, str], 
            message_id: int, 
            caption: Optional[str]=None, 
            parse_mode: Optional[str]=None, 
            caption_entities: Optional[List[types.MessageEntity]]=None,
            disable_notification: Optional[bool]=None, 
            protect_content: Optional[bool]=None,
            reply_to_message_id: Optional[int]=None, 
            allow_sending_without_reply: Optional[bool]=None,
            reply_markup: Optional[REPLY_MARKUP_TYPES]=None, 
            timeout: Optional[int]=None) -> types.MessageID:
        """
        Use this method to copy messages of any kind.

        Telegram documentation: https://core.telegram.org/bots/api#copymessage

        :param chat_id: Unique identifier for the target chat or username of the target channel (in the format @channelusername)
        :type chat_id: :obj:`int` or :obj:`str`

        :param from_chat_id: Unique identifier for the chat where the original message was sent (or channel username in the format @channelusername)
        :type from_chat_id: :obj:`int` or :obj:`str`
        :param message_id: Message identifier in the chat specified in from_chat_id
        :type message_id: :obj:`int`

        :param caption: New caption for media, 0-1024 characters after entities parsing. If not specified, the original caption is kept
        :type caption: :obj:`str`

        :param parse_mode: Mode for parsing entities in the new caption.
        :type parse_mode: :obj:`str`

        :param caption_entities: A JSON-serialized list of special entities that appear in the new caption, which can be specified instead of parse_mode
        :type caption_entities: Array of :class:`telebot.types.MessageEntity`

        :param disable_notification: Sends the message silently. Users will receive a notification with no sound.
        :type disable_notification: :obj:`bool`

        :param protect_content: Protects the contents of the sent message from forwarding and saving
        :type protect_content: :obj:`bool`

        :param reply_to_message_id: If the message is a reply, ID of the original message
        :type reply_to_message_id: :obj:`int`

        :param allow_sending_without_reply: Pass True, if the message should be sent even if the specified replied-to message is not found
        :type allow_sending_without_reply: :obj:`bool`

        :param reply_markup: Additional interface options. A JSON-serialized object for an inline keyboard, custom reply keyboard, instructions to remove reply keyboard
            or to force a reply from the user.
        :type reply_markup: :class:`telebot.types.InlineKeyboardMarkup` or :class:`telebot.types.ReplyKeyboardMarkup` or :class:`telebot.types.ReplyKeyboardRemove`
            or :class:`telebot.types.ForceReply`

        :param timeout: Timeout in seconds for the request.
        :type timeout: :obj:`int`
        
        :return: On success, the sent Message is returned.
        :rtype: :class:`telebot.types.Message`
        """
        return types.MessageID.de_json(
            apihelper.copy_message(self.token, chat_id, from_chat_id, message_id, caption, parse_mode, caption_entities,
                                   disable_notification, reply_to_message_id, allow_sending_without_reply, reply_markup,
                                   timeout, protect_content))

    def delete_message(self, chat_id: Union[int, str], message_id: int, 
            timeout: Optional[int]=None) -> bool:
        """
        Use this method to delete a message, including service messages, with the following limitations:
        - A message can only be deleted if it was sent less than 48 hours ago.
        - A dice message in a private chat can only be deleted if it was sent more than 24 hours ago.
        - Bots can delete outgoing messages in private chats, groups, and supergroups.
        - Bots can delete incoming messages in private chats.
        - Bots granted can_post_messages permissions can delete outgoing messages in channels.
        - If the bot is an administrator of a group, it can delete any message there.
        - If the bot has can_delete_messages permission in a supergroup or a channel, it can delete any message there.
        Returns True on success.

        Telegram documentation: https://core.telegram.org/bots/api#deletemessage

        :param chat_id: Unique identifier for the target chat or username of the target channel (in the format @channelusername)
        :type chat_id: :obj:`int` or :obj:`str`

        :param message_id: Identifier of the message to delete
        :type message_id: :obj:`int`

        :param timeout: Timeout in seconds for the request.
        :type timeout: :obj:`int`

        :return: Returns True on success.
        :rtype: :obj:`bool`
        """
        return apihelper.delete_message(self.token, chat_id, message_id, timeout)

    def send_dice(
            self, chat_id: Union[int, str],
            emoji: Optional[str]=None, disable_notification: Optional[bool]=None, 
            reply_to_message_id: Optional[int]=None,
            reply_markup: Optional[REPLY_MARKUP_TYPES]=None, 
            timeout: Optional[int]=None,
            allow_sending_without_reply: Optional[bool]=None,
            protect_content: Optional[bool]=None) -> types.Message:
        """
        Use this method to send an animated emoji that will display a random value. On success, the sent Message is returned.

        Telegram documentation: https://core.telegram.org/bots/api#senddice

        :param chat_id: Unique identifier for the target chat or username of the target channel (in the format @channelusername)
        :type chat_id: :obj:`int` or :obj:`str`

        :param emoji: Emoji on which the dice throw animation is based. Currently, must be one of “🎲”, “🎯”, “🏀”, “⚽”, “🎳”, or “🎰”.
            Dice can have values 1-6 for “🎲”, “🎯” and “🎳”, values 1-5 for “🏀” and “⚽”, and values 1-64 for “🎰”. Defaults to “🎲”
        :type emoji: :obj:`str`

        :param disable_notification: Sends the message silently. Users will receive a notification with no sound.
        :type disable_notification: :obj:`bool`

        :param reply_to_message_id: If the message is a reply, ID of the original message
        :type reply_to_message_id: :obj:`int`

        :param reply_markup: Additional interface options. A JSON-serialized object for an inline keyboard, custom reply keyboard, instructions
            to remove reply keyboard or to force a reply from the user.
        :type reply_markup: :class:`telebot.types.InlineKeyboardMarkup` or :class:`telebot.types.ReplyKeyboardMarkup` or :class:`telebot.types.ReplyKeyboardRemove`
            or :class:`telebot.types.ForceReply`

        :param timeout: Timeout in seconds for the request.
        :type timeout: :obj:`int`

        :param allow_sending_without_reply: Pass True, if the message should be sent even if the specified replied-to message is not found
        :type allow_sending_without_reply: :obj:`bool`

        :param protect_content: Protects the contents of the sent message from forwarding
        :type protect_content: :obj:`bool`

        :return: On success, the sent Message is returned.
        :rtype: :class:`telebot.types.Message`
        """
        return types.Message.de_json(
            apihelper.send_dice(
                self.token, chat_id, emoji, disable_notification, reply_to_message_id,
                reply_markup, timeout, allow_sending_without_reply, protect_content)
        )


    def send_photo(
            self, chat_id: Union[int, str], photo: Union[Any, str], 
            caption: Optional[str]=None, parse_mode: Optional[str]=None,
            caption_entities: Optional[List[types.MessageEntity]]=None,
            disable_notification: Optional[bool]=None,
            protect_content: Optional[bool]=None,
            reply_to_message_id: Optional[int]=None, 
            allow_sending_without_reply: Optional[bool]=None,
            reply_markup: Optional[REPLY_MARKUP_TYPES]=None,
            timeout: Optional[int]=None,) -> types.Message:
        """
        Use this method to send photos. On success, the sent Message is returned.

        Telegram documentation: https://core.telegram.org/bots/api#sendphoto
        
        :param chat_id: Unique identifier for the target chat or username of the target channel (in the format @channelusername)
        :type chat_id: :obj:`int` or :obj:`str`

        :param photo: Photo to send. Pass a file_id as String to send a photo that exists on the Telegram servers (recommended),
            pass an HTTP URL as a String for Telegram to get a photo from the Internet, or upload a new photo using multipart/form-data.
            The photo must be at most 10 MB in size. The photo's width and height must not exceed 10000 in total. Width and height ratio must be at most 20.
        :type photo: :obj:`str` or :class:`telebot.types.InputFile`

        :param caption: Photo caption (may also be used when resending photos by file_id), 0-1024 characters after entities parsing
        :type caption: :obj:`str`

        :param parse_mode: Mode for parsing entities in the photo caption.
        :type parse_mode: :obj:`str`

        :param caption_entities: A JSON-serialized list of special entities that appear in the caption, which can be specified instead of parse_mode
        :type caption_entities: :obj:`list` of :class:`telebot.types.MessageEntity`

        :param disable_notification: Sends the message silently. Users will receive a notification with no sound.
        :type disable_notification: :obj:`bool`

        :param protect_content: Protects the contents of the sent message from forwarding and saving
        :type protect_content: :obj:`bool`

        :param reply_to_message_id: If the message is a reply, ID of the original message
        :type reply_to_message_id: :obj:`int`

        :param allow_sending_without_reply: Pass True, if the message should be sent even if the specified replied-to message is not found
        :type allow_sending_without_reply: :obj:`bool`

        :param reply_markup: Additional interface options. A JSON-serialized object for an inline keyboard, custom reply keyboard, instructions
            to remove reply keyboard or to force a reply from the user.
        :type reply_markup: :class:`telebot.types.InlineKeyboardMarkup` or :class:`telebot.types.ReplyKeyboardMarkup` or :class:`telebot.types.ReplyKeyboardRemove`
            or :class:`telebot.types.ForceReply`

        :param timeout: Timeout in seconds for the request.
        :type timeout: :obj:`int`
        
        :return: On success, the sent Message is returned.
        :rtype: :class:`telebot.types.Message`
        """
        parse_mode = self.parse_mode if (parse_mode is None) else parse_mode

        return types.Message.de_json(
            apihelper.send_photo(
                self.token, chat_id, photo, caption, reply_to_message_id, reply_markup,
                parse_mode, disable_notification, timeout, caption_entities,
                allow_sending_without_reply, protect_content))

    # TODO: Rewrite this method like in API.
    def send_audio(
            self, chat_id: Union[int, str], audio: Union[Any, str], 
            caption: Optional[str]=None, duration: Optional[int]=None, 
            performer: Optional[str]=None, title: Optional[str]=None,
            reply_to_message_id: Optional[int]=None, 
            reply_markup: Optional[REPLY_MARKUP_TYPES]=None, 
            parse_mode: Optional[str]=None, 
            disable_notification: Optional[bool]=None,
            timeout: Optional[int]=None, 
            thumb: Optional[Union[Any, str]]=None,
            caption_entities: Optional[List[types.MessageEntity]]=None,
            allow_sending_without_reply: Optional[bool]=None,
            protect_content: Optional[bool]=None) -> types.Message:
        """
        Use this method to send audio files, if you want Telegram clients to display them in the music player.
        Your audio must be in the .MP3 or .M4A format. On success, the sent Message is returned. Bots can currently send audio files of up to 50 MB in size,
        this limit may be changed in the future.

        For sending voice messages, use the send_voice method instead.

        Telegram documentation: https://core.telegram.org/bots/api#sendaudio
        
        :param chat_id: Unique identifier for the target chat or username of the target channel (in the format @channelusername)
        :type chat_id: :obj:`int` or :obj:`str`

        :param audio: Audio file to send. Pass a file_id as String to send an audio file that exists on the Telegram servers (recommended),
            pass an HTTP URL as a String for Telegram to get an audio file from the Internet, or upload a new one using multipart/form-data.
            Audio must be in the .MP3 or .M4A format.
        :type audio: :obj:`str` or :class:`telebot.types.InputFile`

        :param caption: Audio caption, 0-1024 characters after entities parsing
        :type caption: :obj:`str`

        :param duration: Duration of the audio in seconds
        :type duration: :obj:`int`

        :param performer: Performer
        :type performer: :obj:`str`

        :param title: Track name
        :type title: :obj:`str`

        :param reply_to_message_id: If the message is a reply, ID of the original message
        :type reply_to_message_id: :obj:`int`

        :param reply_markup:
        :type reply_markup: :class:`telebot.types.InlineKeyboardMarkup` or :class:`telebot.types.ReplyKeyboardMarkup` or :class:`telebot.types.ReplyKeyboardRemove`
            or :class:`telebot.types.ForceReply`

        :param parse_mode: Mode for parsing entities in the audio caption. See formatting options for more details.
        :type parse_mode: :obj:`str`

        :param disable_notification: Sends the message silently. Users will receive a notification with no sound.
        :type disable_notification: :obj:`bool`

        :param timeout: Timeout in seconds for the request.
        :type timeout: :obj:`int`

        :param thumb: Thumbnail of the file sent; can be ignored if thumbnail generation for the file is supported server-side.
            The thumbnail should be in JPEG format and less than 200 kB in size. A thumbnail's width and height should not exceed 320.
            Ignored if the file is not uploaded using multipart/form-data. Thumbnails can't be reused and can be only uploaded as a new file,
            so you can pass “attach://<file_attach_name>” if the thumbnail was uploaded using multipart/form-data under <file_attach_name>
        :type thumb: :obj:`str`

        :param caption_entities: A JSON-serialized list of special entities that appear in the caption, which can be specified instead of parse_mode
        :type caption_entities: :obj:`list` of :class:`telebot.types.MessageEntity`

        :param allow_sending_without_reply: Pass True, if the message should be sent even if the specified replied-to message is not found
        :type allow_sending_without_reply: :obj:`bool`

        :param protect_content: Protects the contents of the sent message from forwarding and saving
        :type protect_content: :obj:`bool`

        :return: On success, the sent Message is returned.
        :rtype: :class:`telebot.types.Message`
        """
        parse_mode = self.parse_mode if (parse_mode is None) else parse_mode

        return types.Message.de_json(
            apihelper.send_audio(
                self.token, chat_id, audio, caption, duration, performer, title, reply_to_message_id,
                reply_markup, parse_mode, disable_notification, timeout, thumb,
                caption_entities, allow_sending_without_reply, protect_content))

    # TODO: Rewrite this method like in API.
    def send_voice(
            self, chat_id: Union[int, str], voice: Union[Any, str], 
            caption: Optional[str]=None, duration: Optional[int]=None, 
            reply_to_message_id: Optional[int]=None, 
            reply_markup: Optional[REPLY_MARKUP_TYPES]=None,
            parse_mode: Optional[str]=None, 
            disable_notification: Optional[bool]=None, 
            timeout: Optional[int]=None,
            caption_entities: Optional[List[types.MessageEntity]]=None,
            allow_sending_without_reply: Optional[bool]=None,
            protect_content: Optional[bool]=None) -> types.Message:
        """
        Use this method to send audio files, if you want Telegram clients to display the file as a playable voice message.
        For this to work, your audio must be in an .OGG file encoded with OPUS (other formats may be sent as Audio or Document).
        On success, the sent Message is returned. Bots can currently send voice messages of up to 50 MB in size, this limit may be changed in the future.

        Telegram documentation: https://core.telegram.org/bots/api#sendvoice
        
        :param chat_id: Unique identifier for the target chat or username of the target channel (in the format @channelusername)
        :type chat_id: :obj:`int` or :obj:`str`

        :param voice: Audio file to send. Pass a file_id as String to send a file that exists on the Telegram servers (recommended),
            pass an HTTP URL as a String for Telegram to get a file from the Internet, or upload a new one using multipart/form-data.
        :type voice: :obj:`str` or :class:`telebot.types.InputFile`

        :param caption: Voice message caption, 0-1024 characters after entities parsing
        :type caption: :obj:`str`

        :param duration: Duration of the voice message in seconds
        :type duration: :obj:`int`

        :param reply_to_message_id: If the message is a reply, ID of the original message
        :type reply_to_message_id: :obj:`int`

        :param reply_markup: Additional interface options. A JSON-serialized object for an inline keyboard, custom reply keyboard, instructions
            to remove reply keyboard or to force a reply from the user.
        :type reply_markup: :class:`telebot.types.InlineKeyboardMarkup` or :class:`telebot.types.ReplyKeyboardMarkup` or :class:`telebot.types.ReplyKeyboardRemove`
            or :class:`telebot.types.ForceReply`

        :param parse_mode: Mode for parsing entities in the voice message caption. See formatting options for more details.
        :type parse_mode: :obj:`str`

        :param disable_notification: Sends the message silently. Users will receive a notification with no sound.
        :type disable_notification: :obj:`bool`

        :param timeout: Timeout in seconds for the request.
        :type timeout: :obj:`int`

        :param caption_entities: A JSON-serialized list of special entities that appear in the caption, which can be specified instead of parse_mode
        :type caption_entities: :obj:`list` of :class:`telebot.types.MessageEntity`

        :param allow_sending_without_reply: Pass True, if the message should be sent even if the specified replied-to message is not found
        :type allow_sending_without_reply: :obj:`bool`

        :param protect_content: Protects the contents of the sent message from forwarding and saving
        :type protect_content: :obj:`bool`

        :return: On success, the sent Message is returned.
        """
        parse_mode = self.parse_mode if (parse_mode is None) else parse_mode

        return types.Message.de_json(
            apihelper.send_voice(
                self.token, chat_id, voice, caption, duration, reply_to_message_id, reply_markup,
                parse_mode, disable_notification, timeout, caption_entities,
                allow_sending_without_reply, protect_content))

    # TODO: Rewrite this method like in API.
    def send_document(
            self, chat_id: Union[int, str], document: Union[Any, str],
            reply_to_message_id: Optional[int]=None, 
            caption: Optional[str]=None, 
            reply_markup: Optional[REPLY_MARKUP_TYPES]=None,
            parse_mode: Optional[str]=None, 
            disable_notification: Optional[bool]=None, 
            timeout: Optional[int]=None, 
            thumb: Optional[Union[Any, str]]=None,
            caption_entities: Optional[List[types.MessageEntity]]=None,
            allow_sending_without_reply: Optional[bool]=None,
            visible_file_name: Optional[str]=None,
            disable_content_type_detection: Optional[bool]=None,
            data: Optional[Union[Any, str]]=None,
            protect_content: Optional[bool]=None) -> types.Message:
        """
        Use this method to send general files.

        Telegram documentation: https://core.telegram.org/bots/api#senddocument
        
        :param chat_id: Unique identifier for the target chat or username of the target channel (in the format @channelusername)
        :type chat_id: :obj:`int` or :obj:`str`

        :param document: (document) File to send. Pass a file_id as String to send a file that exists on the Telegram servers (recommended), pass an HTTP URL as a
            String for Telegram to get a file from the Internet, or upload a new one using multipart/form-data
        :type document: :obj:`str` or :class:`telebot.types.InputFile`

        :param reply_to_message_id: If the message is a reply, ID of the original message
        :type reply_to_message_id: :obj:`int`

        :param caption: Document caption (may also be used when resending documents by file_id), 0-1024 characters after entities parsing
        :type caption: :obj:`str`

        :param reply_markup: Additional interface options. A JSON-serialized object for an inline keyboard, custom reply keyboard, instructions to remove reply keyboard
            or to force a reply from the user.
        :type reply_markup: :class:`telebot.types.InlineKeyboardMarkup` or :class:`telebot.types.ReplyKeyboardMarkup` or :class:`telebot.types.ReplyKeyboardRemove`
            or :class:`telebot.types.ForceReply`

        :param parse_mode: Mode for parsing entities in the document caption
        :type parse_mode: :obj:`str`

        :param disable_notification: Sends the message silently. Users will receive a notification with no sound.
        :type disable_notification: :obj:`bool`

        :param timeout: Timeout in seconds for the request.
        :type timeout: :obj:`int`

        :param thumb: InputFile or String : Thumbnail of the file sent; can be ignored if thumbnail generation for the file is supported server-side. The thumbnail should be in JPEG format and less than 200 kB in size. A thumbnail's width and height should not exceed 320. Ignored if the file is not uploaded using multipart/form-data. Thumbnails can't be reused and can be only uploaded as a new file, so you can pass “attach://<file_attach_name>” if the thumbnail was uploaded using multipart/form-data under <file_attach_name>
        :type thumb: :obj:`str` or :class:`telebot.types.InputFile`

        :param caption_entities: A JSON-serialized list of special entities that appear in the caption, which can be specified instead of parse_mode
        :type caption_entities: :obj:`list` of :class:`telebot.types.MessageEntity`

        :param allow_sending_without_reply: Pass True, if the message should be sent even if the specified replied-to message is not found
        :type allow_sending_without_reply: :obj:`bool`

        :param visible_file_name: allows to define file name that will be visible in the Telegram instead of original file name
        :type visible_file_name: :obj:`str`

        :param disable_content_type_detection: Disables automatic server-side content type detection for files uploaded using multipart/form-data
        :type disable_content_type_detection: :obj:`bool`

        :param data: function typo miss compatibility: do not use it
        :type data: :obj:`str`

        :param protect_content: Protects the contents of the sent message from forwarding and saving
        :type protect_content: :obj:`bool`

        :return: On success, the sent Message is returned.
        :rtype: :class:`telebot.types.Message`
        """
        parse_mode = self.parse_mode if (parse_mode is None) else parse_mode
        if data and not(document):
            # function typo miss compatibility
            document = data

        return types.Message.de_json(
            apihelper.send_data(
                self.token, chat_id, document, 'document',
                reply_to_message_id = reply_to_message_id, reply_markup = reply_markup, parse_mode = parse_mode,
                disable_notification = disable_notification, timeout = timeout, caption = caption, thumb = thumb,
                caption_entities = caption_entities, allow_sending_without_reply = allow_sending_without_reply,
                disable_content_type_detection = disable_content_type_detection, visible_file_name = visible_file_name,
                protect_content = protect_content))


    # TODO: Rewrite this method like in API.
    def send_sticker(
            self, chat_id: Union[int, str],
            sticker: Union[Any, str],
            reply_to_message_id: Optional[int]=None, 
            reply_markup: Optional[REPLY_MARKUP_TYPES]=None,
            disable_notification: Optional[bool]=None, 
            timeout: Optional[int]=None,
            allow_sending_without_reply: Optional[bool]=None,
            protect_content:Optional[bool]=None,
            data: Union[Any, str]=None) -> types.Message:
        """
        Use this method to send static .WEBP, animated .TGS, or video .WEBM stickers.
        On success, the sent Message is returned.

        Telegram documentation: https://core.telegram.org/bots/api#sendsticker

        :param chat_id: Unique identifier for the target chat or username of the target channel (in the format @channelusername)
        :type chat_id: :obj:`int` or :obj:`str`

        :param sticker: Sticker to send. Pass a file_id as String to send a file that exists on the Telegram servers (recommended), pass an HTTP URL
            as a String for Telegram to get a .webp file from the Internet, or upload a new one using multipart/form-data.
        :type sticker: :obj:`str` or :class:`telebot.types.InputFile`

        :param reply_to_message_id: If the message is a reply, ID of the original message
        :type reply_to_message_id: :obj:`int`

        :param reply_markup: Additional interface options. A JSON-serialized object for an inline keyboard, custom reply keyboard, instructions to remove reply keyboard
            or to force a reply from the user.
        :type reply_markup: :class:`telebot.types.InlineKeyboardMarkup` or :class:`telebot.types.ReplyKeyboardMarkup` or :class:`telebot.types.ReplyKeyboardRemove`
            or :class:`telebot.types.ForceReply`

        :param disable_notification: to disable the notification
        :type disable_notification: :obj:`bool`

        :param timeout: Timeout in seconds for the request.
        :type timeout: :obj:`int`

        :param allow_sending_without_reply: Pass True, if the message should be sent even if the specified replied-to message is not found
        :type allow_sending_without_reply: :obj:`bool`

        :param protect_content: Protects the contents of the sent message from forwarding and saving
        :type protect_content: :obj:`bool`

        :param data: function typo miss compatibility: do not use it
        :type data: :obj:`str`

        :return: On success, the sent Message is returned.
        :rtype: :class:`telebot.types.Message`
        """
        if data and not(sticker):
            # function typo miss compatibility
            sticker = data
        return types.Message.de_json(
            apihelper.send_data(
                self.token, chat_id, sticker, 'sticker',
                reply_to_message_id=reply_to_message_id, reply_markup=reply_markup,
                disable_notification=disable_notification, timeout=timeout, 
                allow_sending_without_reply=allow_sending_without_reply,
                protect_content=protect_content))

    def send_video(
            self, chat_id: Union[int, str], video: Union[Any, str], 
            duration: Optional[int]=None,
            width: Optional[int]=None,
            height: Optional[int]=None,
            thumb: Optional[Union[Any, str]]=None, 
            caption: Optional[str]=None, 
            parse_mode: Optional[str]=None, 
            caption_entities: Optional[List[types.MessageEntity]]=None,
            supports_streaming: Optional[bool]=None, 
            disable_notification: Optional[bool]=None,
            protect_content: Optional[bool]=None,
            reply_to_message_id: Optional[int]=None, 
            allow_sending_without_reply: Optional[bool]=None,
            reply_markup: Optional[REPLY_MARKUP_TYPES]=None,
            timeout: Optional[int]=None,
            data: Optional[Union[Any, str]]=None) -> types.Message:
        """
        Use this method to send video files, Telegram clients support mp4 videos (other formats may be sent as Document).
        
        Telegram documentation: https://core.telegram.org/bots/api#sendvideo

        :param chat_id: Unique identifier for the target chat or username of the target channel (in the format @channelusername)
        :type chat_id: :obj:`int` or :obj:`str`

        :param video: Video to send. You can either pass a file_id as String to resend a video that is already on the Telegram servers, or upload a new video file using multipart/form-data.
        :type video: :obj:`str` or :class:`telebot.types.InputFile`

        :param duration: Duration of sent video in seconds
        :type duration: :obj:`int`

        :param width: Video width
        :type width: :obj:`int`

        :param height: Video height
        :type height: :obj:`int`

        :param thumb: Thumbnail of the file sent; can be ignored if thumbnail generation for the file is supported server-side. The thumbnail should be in JPEG format and less than 200 kB in size. A thumbnail's width and height should not exceed 320. Ignored if the file is not uploaded using multipart/form-data. Thumbnails can't be reused and can be only uploaded as a new file, so you can pass “attach://<file_attach_name>” if the thumbnail was uploaded using multipart/form-data under <file_attach_name>.
        :type thumb: :obj:`str` or :class:`telebot.types.InputFile`
        
        :param caption: Video caption (may also be used when resending videos by file_id), 0-1024 characters after entities parsing
        :type caption: :obj:`str`

        :param parse_mode: Mode for parsing entities in the video caption
        :type parse_mode: :obj:`str`

        :param caption_entities: List of special entities that appear in the caption, which can be specified instead of parse_mode
        :type caption_entities: :obj:`list` of :class:`telebot.types.MessageEntity`

        :param supports_streaming: Pass True, if the uploaded video is suitable for streaming
        :type supports_streaming: :obj:`bool`

        :param disable_notification: Sends the message silently. Users will receive a notification with no sound.
        :type disable_notification: :obj:`bool`

        :param protect_content: Protects the contents of the sent message from forwarding and saving
        :type protect_content: :obj:`bool`

        :param reply_to_message_id: If the message is a reply, ID of the original message
        :type reply_to_message_id: :obj:`int`

        :param allow_sending_without_reply: Pass True, if the message should be sent even if the specified replied-to message is not found
        :type allow_sending_without_reply: :obj:`bool`

        :param reply_markup: Additional interface options. A JSON-serialized object for an inline keyboard, custom reply keyboard, instructions to remove reply keyboard
            or to force a reply from the user.
        :type reply_markup: :class:`telebot.types.InlineKeyboardMarkup` or :class:`telebot.types.ReplyKeyboardMarkup` or :class:`telebot.types.ReplyKeyboardRemove`
            or :class:`telebot.types.ForceReply`

        :param timeout: Timeout in seconds for the request.
        :type timeout: :obj:`int`

        :param data: function typo miss compatibility: do not use it
        :type data: :obj:`str`

        :return: On success, the sent Message is returned.
        :rtype: :class:`telebot.types.Message`
        """
        parse_mode = self.parse_mode if (parse_mode is None) else parse_mode
        if data and not(video):
            # function typo miss compatibility
            video = data

        return types.Message.de_json(
            apihelper.send_video(
                self.token, chat_id, video, duration, caption, reply_to_message_id, reply_markup,
                parse_mode, supports_streaming, disable_notification, timeout, thumb, width, height,
                caption_entities, allow_sending_without_reply, protect_content))

    def send_animation(
            self, chat_id: Union[int, str], animation: Union[Any, str], 
            duration: Optional[int]=None,
            width: Optional[int]=None,
            height: Optional[int]=None,
            thumb: Optional[Union[Any, str]]=None,
            caption: Optional[str]=None, 
            parse_mode: Optional[str]=None,
            caption_entities: Optional[List[types.MessageEntity]]=None,
            disable_notification: Optional[bool]=None,
            protect_content: Optional[bool]=None,
            reply_to_message_id: Optional[int]=None,
            allow_sending_without_reply: Optional[bool]=None,
            reply_markup: Optional[REPLY_MARKUP_TYPES]=None, 
            timeout: Optional[int]=None, ) -> types.Message:
        """
        Use this method to send animation files (GIF or H.264/MPEG-4 AVC video without sound).
        On success, the sent Message is returned. Bots can currently send animation files of up to 50 MB in size, this limit may be changed in the future.
        
        Telegram documentation: https://core.telegram.org/bots/api#sendanimation

        :param chat_id: Unique identifier for the target chat or username of the target channel (in the format @channelusername)
        :type chat_id: :obj:`int` or :obj:`str`

        :param animation: Animation to send. Pass a file_id as String to send an animation that exists on the Telegram servers (recommended),
            pass an HTTP URL as a String for Telegram to get an animation from the Internet, or upload a new animation using multipart/form-data.
        :type animation: :obj:`str` or :class:`telebot.types.InputFile`

        :param duration: Duration of sent animation in seconds
        :type duration: :obj:`int`

        :param width: Animation width
        :type width: :obj:`int`

        :param height: Animation height
        :type height: :obj:`int`
        
        :param thumb: Thumbnail of the file sent; can be ignored if thumbnail generation for the file is supported server-side.
            The thumbnail should be in JPEG format and less than 200 kB in size. A thumbnail's width and height should not exceed 320.
            Ignored if the file is not uploaded using multipart/form-data. Thumbnails can't be reused and can be only uploaded as a new file,
            so you can pass “attach://<file_attach_name>” if the thumbnail was uploaded using multipart/form-data under <file_attach_name>.
        :type thumb: :obj:`str` or :class:`telebot.types.InputFile`

        :param caption: Animation caption (may also be used when resending animation by file_id), 0-1024 characters after entities parsing
        :type caption: :obj:`str`

        :param parse_mode: Mode for parsing entities in the animation caption
        :type parse_mode: :obj:`str`

        :param protect_content: Protects the contents of the sent message from forwarding and saving
        :type protect_content: :obj:`bool`

        :param reply_to_message_id: If the message is a reply, ID of the original message
        :type reply_to_message_id: :obj:`int`

        :param reply_markup: Additional interface options. A JSON-serialized object for an inline keyboard, custom reply keyboard, instructions to remove reply keyboard
            or to force a reply from the user.
        :type reply_markup: :class:`telebot.types.InlineKeyboardMarkup` or :class:`telebot.types.ReplyKeyboardMarkup` or :class:`telebot.types.ReplyKeyboardRemove`
            or :class:`telebot.types.ForceReply`

        :param disable_notification: Sends the message silently. Users will receive a notification with no sound.
        :type disable_notification: :obj:`bool`

        :param timeout: Timeout in seconds for the request.
        :type timeout: :obj:`int`

        :param caption_entities: List of special entities that appear in the caption, which can be specified instead of parse_mode
        :type caption_entities: :obj:`list` of :class:`telebot.types.MessageEntity`

        :param allow_sending_without_reply: Pass True, if the message should be sent even if the specified replied-to message is not found
        :type allow_sending_without_reply: :obj:`bool`

        :return: On success, the sent Message is returned.
        :rtype: :class:`telebot.types.Message`
        """
        parse_mode = self.parse_mode if (parse_mode is None) else parse_mode

        return types.Message.de_json(
            apihelper.send_animation(
                self.token, chat_id, animation, duration, caption, reply_to_message_id,
                reply_markup, parse_mode, disable_notification, timeout, thumb,
                caption_entities, allow_sending_without_reply, protect_content, width, height))

    # TODO: Rewrite this method like in API.
    def send_video_note(
            self, chat_id: Union[int, str], data: Union[Any, str], 
            duration: Optional[int]=None, 
            length: Optional[int]=None,
            reply_to_message_id: Optional[int]=None, 
            reply_markup: Optional[REPLY_MARKUP_TYPES]=None,
            disable_notification: Optional[bool]=None, 
            timeout: Optional[int]=None, 
            thumb: Optional[Union[Any, str]]=None,
            allow_sending_without_reply: Optional[bool]=None,
            protect_content: Optional[bool]=None) -> types.Message:
        """
        As of v.4.0, Telegram clients support rounded square MPEG4 videos of up to 1 minute long.
        Use this method to send video messages. On success, the sent Message is returned.

        Telegram documentation: https://core.telegram.org/bots/api#sendvideonote
        
        :param chat_id: Unique identifier for the target chat or username of the target channel (in the format @channelusername)
        :type chat_id: :obj:`int` or :obj:`str`
        
        :param data: Video note to send. Pass a file_id as String to send a video note that exists on the Telegram servers (recommended)
            or upload a new video using multipart/form-data. Sending video notes by a URL is currently unsupported
        :type data: :obj:`str` or :class:`telebot.types.InputFile`

        :param duration: Duration of sent video in seconds
        :type duration: :obj:`int`

        :param length: Video width and height, i.e. diameter of the video message
        :type length: :obj:`int`

        :param reply_to_message_id: If the message is a reply, ID of the original message
        :type reply_to_message_id: :obj:`int`

        :param reply_markup: Additional interface options. A JSON-serialized object for an inline keyboard, custom reply keyboard, instructions to remove reply keyboard
            or to force a reply from the user.
        :type reply_markup: :class:`telebot.types.InlineKeyboardMarkup` or :class:`telebot.types.ReplyKeyboardMarkup` or :class:`telebot.types.ReplyKeyboardRemove`
            or :class:`telebot.types.ForceReply`

        :param disable_notification: Sends the message silently. Users will receive a notification with no sound.
        :type disable_notification: :obj:`bool`

        :param timeout: Timeout in seconds for the request.
        :type timeout: :obj:`int`

        :param thumb: Thumbnail of the file sent; can be ignored if thumbnail generation for the file is supported server-side.
            The thumbnail should be in JPEG format and less than 200 kB in size. A thumbnail's width and height should not exceed 320.
            Ignored if the file is not uploaded using multipart/form-data. Thumbnails can't be reused and can be only uploaded as a new file,
            so you can pass “attach://<file_attach_name>” if the thumbnail was uploaded using multipart/form-data under <file_attach_name>. 
        :type thumb: :obj:`str` or :class:`telebot.types.InputFile`

        :param allow_sending_without_reply: Pass True, if the message should be sent even if the specified replied-to message is not found
        :type allow_sending_without_reply: :obj:`bool`

        :param protect_content: Protects the contents of the sent message from forwarding and saving
        :type protect_content: :obj:`bool`

        :return: On success, the sent Message is returned.
        :rtype: :class:`telebot.types.Message`
        """
        return types.Message.de_json(
            apihelper.send_video_note(
                self.token, chat_id, data, duration, length, reply_to_message_id, reply_markup,
                disable_notification, timeout, thumb, allow_sending_without_reply, protect_content))


    def send_media_group(
            self, chat_id: Union[int, str], 
            media: List[Union[
                types.InputMediaAudio, types.InputMediaDocument, 
                types.InputMediaPhoto, types.InputMediaVideo]],
            disable_notification: Optional[bool]=None, 
            protect_content: Optional[bool]=None,
            reply_to_message_id: Optional[int]=None, 
            timeout: Optional[int]=None,
            allow_sending_without_reply: Optional[bool]=None) -> List[types.Message]:
        """
        Use this method to send a group of photos, videos, documents or audios as an album. Documents and audio files
        can be only grouped in an album with messages of the same type. On success, an array of Messages that were sent is returned.
        
        Telegram documentation: https://core.telegram.org/bots/api#sendmediagroup

        :param chat_id: Unique identifier for the target chat or username of the target channel (in the format @channelusername)
        :type chat_id: :obj:`int` or :obj:`str`

        :param media: A JSON-serialized array describing messages to be sent, must include 2-10 items
        :type media: :obj:`list` of :obj:`types.InputMedia`

        :param disable_notification: Sends the messages silently. Users will receive a notification with no sound.
        :type disable_notification: :obj:`bool`

        :param protect_content: Protects the contents of the sent message from forwarding and saving
        :type protect_content: :obj:`bool`

        :param reply_to_message_id: If the message is a reply, ID of the original message
        :type reply_to_message_id: :obj:`int`

        :param timeout: Timeout in seconds for the request.
        :type timeout: :obj:`int`

        :param allow_sending_without_reply: Pass True, if the message should be sent even if the specified replied-to message is not found
        :type allow_sending_without_reply: :obj:`bool`

        :return: On success, an array of Messages that were sent is returned.
        :rtype: List[types.Message]
        """
        result = apihelper.send_media_group(
            self.token, chat_id, media, disable_notification, reply_to_message_id, timeout, 
            allow_sending_without_reply, protect_content)
        return [types.Message.de_json(msg) for msg in result]

    # TODO: Rewrite this method like in API.
    def send_location(
            self, chat_id: Union[int, str], 
            latitude: float, longitude: float, 
            live_period: Optional[int]=None, 
            reply_to_message_id: Optional[int]=None, 
            reply_markup: Optional[REPLY_MARKUP_TYPES]=None, 
            disable_notification: Optional[bool]=None, 
            timeout: Optional[int]=None,
            horizontal_accuracy: Optional[float]=None, 
            heading: Optional[int]=None, 
            proximity_alert_radius: Optional[int]=None, 
            allow_sending_without_reply: Optional[bool]=None,
            protect_content: Optional[bool]=None) -> types.Message:
        """
        Use this method to send point on the map. On success, the sent Message is returned.

        Telegram documentation: https://core.telegram.org/bots/api#sendlocation

        :param chat_id: Unique identifier for the target chat or username of the target channel (in the format @channelusername)
        :type chat_id: :obj:`int` or :obj:`str`

        :param latitude: Latitude of the location
        :type latitude: :obj:`float`

        :param longitude: Longitude of the location
        :type longitude: :obj:`float`

        :param live_period: Period in seconds for which the location will be updated (see Live Locations, should be between 60 and 86400.
        :type live_period: :obj:`int`

        :param reply_to_message_id: If the message is a reply, ID of the original message
        :type reply_to_message_id: :obj:`int`

        :param reply_markup: Additional interface options. A JSON-serialized object for an inline keyboard, custom reply keyboard, instructions to remove reply keyboard
            or to force a reply from the user.
        :type reply_markup: :class:`telebot.types.InlineKeyboardMarkup` or :class:`telebot.types.ReplyKeyboardMarkup` or :class:`telebot.types.ReplyKeyboardRemove`
            or :class:`telebot.types.ForceReply`

        :param disable_notification: Sends the message silently. Users will receive a notification with no sound.
        :type disable_notification: :obj:`bool`

        :param timeout: Timeout in seconds for the request.
        :type timeout: :obj:`int`

        :param horizontal_accuracy: The radius of uncertainty for the location, measured in meters; 0-1500
        :type horizontal_accuracy: :obj:`float`

        :param heading: For live locations, a direction in which the user is moving, in degrees. Must be between 1 and 360 if specified.
        :type heading: :obj:`int`

        :param proximity_alert_radius: For live locations, a maximum distance for proximity alerts about approaching another chat member, in meters. Must be between 1 and 100000 if specified.
        :type proximity_alert_radius: :obj:`int`

        :param allow_sending_without_reply: Pass True, if the message should be sent even if the specified replied-to message is not found
        :type allow_sending_without_reply: :obj:`bool`
        
        :param protect_content: Protects the contents of the sent message from forwarding and saving
        :type protect_content: :obj:`bool`

        :return: On success, the sent Message is returned.
        :rtype: :class:`telebot.types.Message`
        """
        return types.Message.de_json(
            apihelper.send_location(
                self.token, chat_id, latitude, longitude, live_period, 
                reply_to_message_id, reply_markup, disable_notification, timeout, 
                horizontal_accuracy, heading, proximity_alert_radius, 
                allow_sending_without_reply, protect_content))

    def edit_message_live_location(
            self, latitude: float, longitude: float, 
            chat_id: Optional[Union[int, str]]=None, 
            message_id: Optional[int]=None,
            inline_message_id: Optional[str]=None, 
            reply_markup: Optional[REPLY_MARKUP_TYPES]=None, 
            timeout: Optional[int]=None,
            horizontal_accuracy: Optional[float]=None, 
            heading: Optional[int]=None, 
            proximity_alert_radius: Optional[int]=None) -> types.Message or bool:
        """
        Use this method to edit live location messages. A location can be edited until its live_period expires or editing is explicitly
            disabled by a call to stopMessageLiveLocation. On success, if the edited message is not an inline message, the edited Message
            is returned, otherwise True is returned.

        Telegram documentation: https://core.telegram.org/bots/api#editmessagelivelocation

        :param latitude: Latitude of new location
        :type latitude: :obj:`float`

        :param longitude: Longitude of new location
        :type longitude: :obj:`float`

        :param chat_id: Unique identifier for the target chat or username of the target channel (in the format @channelusername)
        :type chat_id: :obj:`int` or :obj:`str`

        :param message_id: Required if inline_message_id is not specified. Identifier of the message to edit
        :type message_id: :obj:`int`

        :param reply_markup: A JSON-serialized object for a new inline keyboard.
        :type reply_markup: :class:`telebot.types.InlineKeyboardMarkup` or :class:`telebot.types.ReplyKeyboardMarkup` or :class:`telebot.types.ReplyKeyboardRemove`
            or :class:`telebot.types.ForceReply`

        :param timeout: Timeout in seconds for the request.
        :type timeout: :obj:`int`

        :param inline_message_id: Required if chat_id and message_id are not specified. Identifier of the inline message
        :type inline_message_id: :obj:`str`

        :param horizontal_accuracy: The radius of uncertainty for the location, measured in meters; 0-1500
        :type horizontal_accuracy: :obj:`float`

        :param heading: Direction in which the user is moving, in degrees. Must be between 1 and 360 if specified.
        :type heading: :obj:`int`

        :param proximity_alert_radius: The maximum distance for proximity alerts about approaching another chat member, in meters. Must be between 1 and 100000 if specified.
        :type proximity_alert_radius: :obj:`int`

        :return: On success, if the edited message is not an inline message, the edited Message is returned, otherwise True is returned.
        :rtype: :class:`telebot.types.Message` or bool
        """
        return types.Message.de_json(
            apihelper.edit_message_live_location(
                self.token, latitude, longitude, chat_id, message_id,
                inline_message_id, reply_markup, timeout,
                horizontal_accuracy, heading, proximity_alert_radius))

    def stop_message_live_location(
            self, chat_id: Optional[Union[int, str]]=None, 
            message_id: Optional[int]=None,
            inline_message_id: Optional[str]=None, 
            reply_markup: Optional[REPLY_MARKUP_TYPES]=None, 
            timeout: Optional[int]=None) -> types.Message or bool:
        """
        Use this method to stop updating a live location message before live_period expires.
        On success, if the message is not an inline message, the edited Message is returned, otherwise True is returned.

        Telegram documentation: https://core.telegram.org/bots/api#stopmessagelivelocation
        
        :param chat_id: Unique identifier for the target chat or username of the target channel (in the format @channelusername)
        :type chat_id: :obj:`int` or :obj:`str`

        :param message_id: 	Required if inline_message_id is not specified. Identifier of the message with live location to stop
        :type message_id: :obj:`int`

        :param inline_message_id: Required if chat_id and message_id are not specified. Identifier of the inline message with live location to stop
        :type inline_message_id: :obj:`str`

        :param reply_markup: A JSON-serialized object for a new inline keyboard.
        :type reply_markup: :class:`telebot.types.InlineKeyboardMarkup` or :class:`telebot.types.ReplyKeyboardMarkup` or :class:`telebot.types.ReplyKeyboardRemove`
            or :class:`telebot.types.ForceReply`

        :param timeout: Timeout in seconds for the request.
        :type timeout: :obj:`int`

        :return: On success, if the message is not an inline message, the edited Message is returned, otherwise True is returned.
        :rtype: :class:`telebot.types.Message` or bool
        """
        return types.Message.de_json(
            apihelper.stop_message_live_location(
                self.token, chat_id, message_id, inline_message_id, reply_markup, timeout))

    # TODO: Rewrite this method like in API.
    def send_venue(
            self, chat_id: Union[int, str], 
            latitude: Optional[float], longitude: Optional[float], 
            title: str, address: str, 
            foursquare_id: Optional[str]=None, 
            foursquare_type: Optional[str]=None,
            disable_notification: Optional[bool]=None, 
            reply_to_message_id: Optional[int]=None, 
            reply_markup: Optional[REPLY_MARKUP_TYPES]=None, 
            timeout: Optional[int]=None,
            allow_sending_without_reply: Optional[bool]=None,
            google_place_id: Optional[str]=None,
            google_place_type: Optional[str]=None,
            protect_content: Optional[bool]=None) -> types.Message:
        """
        Use this method to send information about a venue. On success, the sent Message is returned.
        
        Telegram documentation: https://core.telegram.org/bots/api#sendvenue

        :param chat_id: Unique identifier for the target chat or username of the target channel
        :type chat_id: :obj:`int` or :obj:`str`
        
        :param latitude: Latitude of the venue
        :type latitude: :obj:`float`

        :param longitude: Longitude of the venue
        :type longitude: :obj:`float`

        :param title: Name of the venue
        :type title: :obj:`str`

        :param address: Address of the venue
        :type address: :obj:`str`

        :param foursquare_id: Foursquare identifier of the venue
        :type foursquare_id: :obj:`str`

        :param foursquare_type: Foursquare type of the venue, if known. (For example, “arts_entertainment/default”,
            “arts_entertainment/aquarium” or “food/icecream”.)
        :type foursquare_type: :obj:`str`

        :param disable_notification: Sends the message silently. Users will receive a notification with no sound.
        :type disable_notification: :obj:`bool`

        :param reply_to_message_id: If the message is a reply, ID of the original message
        :type reply_to_message_id: :obj:`int`

        :param reply_markup: Additional interface options. A JSON-serialized object for an inline keyboard,
            custom reply keyboard, instructions to remove reply keyboard or to force a reply from the user.
        :type reply_markup: :class:`telebot.types.InlineKeyboardMarkup` or :class:`telebot.types.ReplyKeyboardMarkup` or :class:`telebot.types.ReplyKeyboardRemove`
            or :class:`telebot.types.ForceReply`

        :param timeout: Timeout in seconds for the request.
        :type timeout: :obj:`int`

        :param allow_sending_without_reply: Pass True, if the message should be sent even if one of the specified
            replied-to messages is not found.
        :type allow_sending_without_reply: :obj:`bool`

        :param google_place_id: Google Places identifier of the venue
        :type google_place_id: :obj:`str`

        :param google_place_type: Google Places type of the venue.
        :type google_place_type: :obj:`str`

        :param protect_content: Protects the contents of the sent message from forwarding and saving
        :type protect_content: :obj:`bool`

        :return: On success, the sent Message is returned.
        :rtype: :class:`telebot.types.Message`
        """
        return types.Message.de_json(
            apihelper.send_venue(
                self.token, chat_id, latitude, longitude, title, address, foursquare_id, foursquare_type,
                disable_notification, reply_to_message_id, reply_markup, timeout,
                allow_sending_without_reply, google_place_id, google_place_type, protect_content))


    # TODO: Rewrite this method like in API.
    def send_contact(
            self, chat_id: Union[int, str], phone_number: str, 
            first_name: str, last_name: Optional[str]=None, 
            vcard: Optional[str]=None,
            disable_notification: Optional[bool]=None, 
            reply_to_message_id: Optional[int]=None, 
            reply_markup: Optional[REPLY_MARKUP_TYPES]=None, 
            timeout: Optional[int]=None,
            allow_sending_without_reply: Optional[bool]=None,
            protect_content: Optional[bool]=None) -> types.Message:
        """
        Use this method to send phone contacts. On success, the sent Message is returned.

        Telegram documentation: https://core.telegram.org/bots/api#sendcontact

        :param chat_id: Unique identifier for the target chat or username of the target channel
        :type chat_id: :obj:`int` or :obj:`str`

        :param phone_number: Contact's phone number
        :type phone_number: :obj:`str`

        :param first_name: Contact's first name
        :type first_name: :obj:`str`

        :param last_name: Contact's last name
        :type last_name: :obj:`str`

        :param vcard: Additional data about the contact in the form of a vCard, 0-2048 bytes
        :type vcard: :obj:`str`

        :param disable_notification: Sends the message silently. Users will receive a notification with no sound.
        :type disable_notification: :obj:`bool`

        :param reply_to_message_id: If the message is a reply, ID of the original message
        :type reply_to_message_id: :obj:`int`

        :param reply_markup: Additional interface options. A JSON-serialized object for an inline keyboard,
            custom reply keyboard, instructions to remove reply keyboard or to force a reply from the user.
        :type reply_markup: :class:`telebot.types.InlineKeyboardMarkup` or :class:`telebot.types.ReplyKeyboardMarkup` or :class:`telebot.types.ReplyKeyboardRemove`
            or :class:`telebot.types.ForceReply`

        :param timeout: Timeout in seconds for the request.
        :type timeout: :obj:`int`

        :param allow_sending_without_reply: Pass True, if the message should be sent even if one of the specified
            replied-to messages is not found.
        :type allow_sending_without_reply: :obj:`bool`

        :param protect_content: Protects the contents of the sent message from forwarding and saving
        :type protect_content: :obj:`bool`

        :return: On success, the sent Message is returned.
        :rtype: :class:`telebot.types.Message`
        """
        return types.Message.de_json(
            apihelper.send_contact(
                self.token, chat_id, phone_number, first_name, last_name, vcard,
                disable_notification, reply_to_message_id, reply_markup, timeout,
                allow_sending_without_reply, protect_content))

    def send_chat_action(
            self, chat_id: Union[int, str], action: str, timeout: Optional[int]=None) -> bool:
        """
        Use this method when you need to tell the user that something is happening on the bot's side.
        The status is set for 5 seconds or less (when a message arrives from your bot, Telegram clients clear its typing status).
        Returns True on success.

        Example: The ImageBot needs some time to process a request and upload the image. Instead of sending a text message along the lines of
        “Retrieving image, please wait…”, the bot may use sendChatAction with action = upload_photo. The user will see a “sending photo” status for the bot.

        Telegram documentation: https://core.telegram.org/bots/api#sendchataction

        :param chat_id: Unique identifier for the target chat or username of the target channel
        :type chat_id: :obj:`int` or :obj:`str`
        
        :param action: Type of action to broadcast. Choose one, depending on what the user is about
            to receive: typing for text messages, upload_photo for photos, record_video or upload_video
            for videos, record_voice or upload_voice for voice notes, upload_document for general files,
            choose_sticker for stickers, find_location for location data, record_video_note or upload_video_note for video notes.
        :type action: :obj:`str`

        :param timeout: Timeout in seconds for the request.
        :type timeout: :obj:`int`

        :return: Returns True on success.
        :rtype: :obj:`bool`
        """
        return apihelper.send_chat_action(self.token, chat_id, action, timeout)
    
    @util.deprecated(deprecation_text="Use ban_chat_member instead")
    def kick_chat_member(
            self, chat_id: Union[int, str], user_id: int, 
            until_date:Optional[Union[int, datetime]]=None, 
            revoke_messages: Optional[bool]=None) -> bool:
        """
        This function is deprecated. Use `ban_chat_member` instead.
        """
        return apihelper.ban_chat_member(self.token, chat_id, user_id, until_date, revoke_messages)

    def ban_chat_member(
            self, chat_id: Union[int, str], user_id: int, 
            until_date: Optional[Union[int, datetime]]=None, 
            revoke_messages: Optional[bool]=None) -> bool:
        """
        Use this method to ban a user in a group, a supergroup or a channel. 
        In the case of supergroups and channels, the user will not be able to return to the chat on their 
        own using invite links, etc., unless unbanned first. 
        Returns True on success.

        Telegram documentation: https://core.telegram.org/bots/api#banchatmember

        :param chat_id: Unique identifier for the target group or username of the target supergroup
            or channel (in the format @channelusername)
        :type chat_id: :obj:`int` or :obj:`str`

        :param user_id: Unique identifier of the target user
        :type user_id: :obj:`int`

        :param until_date: Date when the user will be unbanned, unix time. If user is banned for more than 366 days or
               less than 30 seconds from the current time they are considered to be banned forever
        :type until_date: :obj:`int` or :obj:`datetime`

        :param revoke_messages: Bool: Pass True to delete all messages from the chat for the user that is being removed.
            If False, the user will be able to see messages in the group that were sent before the user was removed. 
            Always True for supergroups and channels.
        :type revoke_messages: :obj:`bool`
        
        :return: Returns True on success.
        :rtype: :obj:`bool`
        """
        return apihelper.ban_chat_member(self.token, chat_id, user_id, until_date, revoke_messages)

    def unban_chat_member(
            self, chat_id: Union[int, str], user_id: int, 
            only_if_banned: Optional[bool]=False) -> bool:
        """
        Use this method to unban a previously kicked user in a supergroup or channel.
        The user will not return to the group or channel automatically, but will be able to join via link, etc.
        The bot must be an administrator for this to work. By default, this method guarantees that after the call
        the user is not a member of the chat, but will be able to join it. So if the user is a member of the chat
        they will also be removed from the chat. If you don't want this, use the parameter only_if_banned.

        Telegram documentation: https://core.telegram.org/bots/api#unbanchatmember

        :param chat_id: Unique identifier for the target group or username of the target supergroup or channel
            (in the format @username)
        :type chat_id: :obj:`int` or :obj:`str`

        :param user_id: Unique identifier of the target user
        :type user_id: :obj:`int`

        :param only_if_banned: Do nothing if the user is not banned
        :type only_if_banned: :obj:`bool`

        :return: True on success
        :rtype: :obj:`bool`
        """
        return apihelper.unban_chat_member(self.token, chat_id, user_id, only_if_banned)

    def restrict_chat_member(
            self, chat_id: Union[int, str], user_id: int, 
            until_date: Optional[Union[int, datetime]]=None,
            can_send_messages: Optional[bool]=None, 
            can_send_media_messages: Optional[bool]=None,
            can_send_polls: Optional[bool]=None, 
            can_send_other_messages: Optional[bool]=None,
            can_add_web_page_previews: Optional[bool]=None, 
            can_change_info: Optional[bool]=None,
            can_invite_users: Optional[bool]=None, 
            can_pin_messages: Optional[bool]=None) -> bool:
        """
        Use this method to restrict a user in a supergroup.
        The bot must be an administrator in the supergroup for this to work and must have
        the appropriate admin rights. Pass True for all boolean parameters to lift restrictions from a user.

        Telegram documentation: https://core.telegram.org/bots/api#restrictchatmember

        :param chat_id: Unique identifier for the target group or username of the target supergroup
            or channel (in the format @channelusername)
        :type chat_id: :obj:`int` or :obj:`str`

        :param user_id: Unique identifier of the target user
        :type user_id: :obj:`int`

        :param until_date: Date when restrictions will be lifted for the user, unix time.
            If user is restricted for more than 366 days or less than 30 seconds from the current time,
            they are considered to be restricted forever
        :type until_date: :obj:`int` or :obj:`datetime`

        :param can_send_messages: Pass True, if the user can send text messages, contacts, locations and venues
        :type can_send_messages: :obj:`bool`
        
        :param can_send_media_messages: Pass True, if the user can send audios, documents, photos, videos, video notes
            and voice notes, implies can_send_messages
        :type can_send_media_messages: :obj:`bool`
        
        :param can_send_polls: Pass True, if the user is allowed to send polls, implies can_send_messages
        :type can_send_polls: :obj:`bool`

        :param can_send_other_messages: Pass True, if the user can send animations, games, stickers and use inline bots, implies can_send_media_messages
        :type can_send_other_messages: :obj:`bool`

        :param can_add_web_page_previews: Pass True, if the user may add web page previews to their messages,
            implies can_send_media_messages
        :type can_add_web_page_previews: :obj:`bool`

        :param can_change_info: Pass True, if the user is allowed to change the chat title, photo and other settings.
            Ignored in public supergroups
        :type can_change_info: :obj:`bool`

        :param can_invite_users: Pass True, if the user is allowed to invite new users to the chat,
            implies can_invite_users
        :type can_invite_users: :obj:`bool`

        :param can_pin_messages: Pass True, if the user is allowed to pin messages. Ignored in public supergroups
        :type can_pin_messages: :obj:`bool`

        :return: True on success
        :rtype: :obj:`bool`
        """
        return apihelper.restrict_chat_member(
            self.token, chat_id, user_id, until_date,
            can_send_messages, can_send_media_messages,
            can_send_polls, can_send_other_messages,
            can_add_web_page_previews, can_change_info,
            can_invite_users, can_pin_messages)

    def promote_chat_member(
            self, chat_id: Union[int, str], user_id: int,
            can_change_info: Optional[bool]=None, 
            can_post_messages: Optional[bool]=None,
            can_edit_messages: Optional[bool]=None, 
            can_delete_messages: Optional[bool]=None, 
            can_invite_users: Optional[bool]=None,
            can_restrict_members: Optional[bool]=None, 
            can_pin_messages: Optional[bool]=None, 
            can_promote_members: Optional[bool]=None,
            is_anonymous: Optional[bool]=None, 
            can_manage_chat: Optional[bool]=None, 
            can_manage_video_chats: Optional[bool]=None,
            can_manage_voice_chats: Optional[bool]=None) -> bool:
        """
        Use this method to promote or demote a user in a supergroup or a channel. The bot must be an administrator
        in the chat for this to work and must have the appropriate admin rights.
        Pass False for all boolean parameters to demote a user.

        Telegram documentation: https://core.telegram.org/bots/api#promotechatmember

        :param chat_id: Unique identifier for the target chat or username of the target channel (
            in the format @channelusername)
        :type chat_id: :obj:`int` or :obj:`str`

        :param user_id: Unique identifier of the target user
        :type user_id: :obj:`int`

        :param can_change_info: Pass True, if the administrator can change chat title, photo and other settings
        :type can_change_info: :obj:`bool`

        :param can_post_messages: Pass True, if the administrator can create channel posts, channels only
        :type can_post_messages: :obj:`bool`

        :param can_edit_messages: Pass True, if the administrator can edit messages of other users, channels only
        :type can_edit_messages: :obj:`bool`

        :param can_delete_messages: Pass True, if the administrator can delete messages of other users
        :type can_delete_messages: :obj:`bool`

        :param can_invite_users: Pass True, if the administrator can invite new users to the chat
        :type can_invite_users: :obj:`bool`

        :param can_restrict_members: Pass True, if the administrator can restrict, ban or unban chat members
        :type can_restrict_members: :obj:`bool`

        :param can_pin_messages: Pass True, if the administrator can pin messages, supergroups only
        :type can_pin_messages: :obj:`bool`

        :param can_promote_members: Pass True, if the administrator can add new administrators with a subset
            of his own privileges or demote administrators that he has promoted, directly or indirectly
            (promoted by administrators that were appointed by him)
        :type can_promote_members: :obj:`bool`

        :param is_anonymous: Pass True, if the administrator's presence in the chat is hidden
        :type is_anonymous: :obj:`bool`

        :param can_manage_chat: Pass True, if the administrator can access the chat event log, chat statistics, 
            message statistics in channels, see channel members, 
            see anonymous administrators in supergroups and ignore slow mode. 
            Implied by any other administrator privilege
        :type can_manage_chat: :obj:`bool`

        :param can_manage_video_chats: Pass True, if the administrator can manage voice chats
            For now, bots can use this privilege only for passing to other administrators.
        :type can_manage_video_chats: :obj:`bool`

        :param can_manage_voice_chats: Deprecated, use can_manage_video_chats.
        :type can_manage_voice_chats: :obj:`bool`

        :return: True on success.
        :rtype: :obj:`bool`
        """
        if can_manage_voice_chats is not None:
            logger.warning("promote_chat_member: can_manage_voice_chats parameter is deprecated. Use can_manage_video_chats instead.")
            if can_manage_video_chats is None:
                can_manage_video_chats = can_manage_voice_chats

        return apihelper.promote_chat_member(
            self.token, chat_id, user_id, can_change_info, can_post_messages,
            can_edit_messages, can_delete_messages, can_invite_users,
            can_restrict_members, can_pin_messages, can_promote_members,
            is_anonymous, can_manage_chat, can_manage_video_chats)

    def set_chat_administrator_custom_title(
            self, chat_id: Union[int, str], user_id: int, custom_title: str) -> bool:
        """
        Use this method to set a custom title for an administrator in a supergroup promoted by the bot.
        Returns True on success.

        Telegram documentation: https://core.telegram.org/bots/api#setchatadministratorcustomtitle

        :param chat_id: Unique identifier for the target chat or username of the target supergroup
            (in the format @supergroupusername)
        :type chat_id: :obj:`int` or :obj:`str`

        :param user_id: Unique identifier of the target user
        :type user_id: :obj:`int`

        :param custom_title: New custom title for the administrator;
            0-16 characters, emoji are not allowed
        :type custom_title: :obj:`str`

        :return: True on success.
        :rtype: :obj:`bool`
        """
        return apihelper.set_chat_administrator_custom_title(self.token, chat_id, user_id, custom_title)
    
    def ban_chat_sender_chat(self, chat_id: Union[int, str], sender_chat_id: Union[int, str]) -> bool:
        """
        Use this method to ban a channel chat in a supergroup or a channel.
        The owner of the chat will not be able to send messages and join live 
        streams on behalf of the chat, unless it is unbanned first. 
        The bot must be an administrator in the supergroup or channel 
        for this to work and must have the appropriate administrator rights. 
        Returns True on success.

        Telegram documentation: https://core.telegram.org/bots/api#banchatsenderchat

        :param chat_id: Unique identifier for the target chat or username of the target channel (in the format @channelusername)
        :type chat_id: :obj:`int` or :obj:`str`

        :param sender_chat_id: Unique identifier of the target sender chat
        :type sender_chat_id: :obj:`int` or :obj:`str`

        :return: True on success.
        :rtype: :obj:`bool`
        """
        return apihelper.ban_chat_sender_chat(self.token, chat_id, sender_chat_id)

    def unban_chat_sender_chat(self, chat_id: Union[int, str], sender_chat_id: Union[int, str]) -> bool:
        """
        Use this method to unban a previously banned channel chat in a supergroup or channel. 
        The bot must be an administrator for this to work and must have the appropriate 
        administrator rights.
        Returns True on success.

        Telegram documentation: https://core.telegram.org/bots/api#unbanchatsenderchat

        :param chat_id: Unique identifier for the target chat or username of the target channel (in the format @channelusername)
        :type chat_id: :obj:`int` or :obj:`str`

        :param sender_chat_id: Unique identifier of the target sender chat.
        :type sender_chat_id: :obj:`int` or :obj:`str`

        :return: True on success.
        :rtype: :obj:`bool`
        """
        return apihelper.unban_chat_sender_chat(self.token, chat_id, sender_chat_id)

    def set_chat_permissions(
            self, chat_id: Union[int, str], permissions: types.ChatPermissions) -> bool:
        """
        Use this method to set default chat permissions for all members.
        The bot must be an administrator in the group or a supergroup for this to work
        and must have the can_restrict_members admin rights.

        Telegram documentation: https://core.telegram.org/bots/api#setchatpermissions

        :param chat_id: Unique identifier for the target chat or username of the target supergroup
            (in the format @supergroupusername)
        :type chat_id: :obj:`int` or :obj:`str`

        :param permissions: New default chat permissions
        :type permissions: :class:`telebot.types..ChatPermissions`

        :return: True on success
        :rtype: :obj:`bool`
        """
        return apihelper.set_chat_permissions(self.token, chat_id, permissions)

    def create_chat_invite_link(
            self, chat_id: Union[int, str],
            name: Optional[str]=None,
            expire_date: Optional[Union[int, datetime]]=None, 
            member_limit: Optional[int]=None,
            creates_join_request: Optional[bool]=None) -> types.ChatInviteLink:
        """
        Use this method to create an additional invite link for a chat. The bot must be an administrator in the chat for this to work and
        must have the appropriate administrator rights.
        The link can be revoked using the method revokeChatInviteLink.
        Returns the new invite link as ChatInviteLink object.

        Telegram documentation: https://core.telegram.org/bots/api#createchatinvitelink

        :param chat_id: Id: Unique identifier for the target chat or username of the target channel
            (in the format @channelusername)
        :type chat_id: :obj:`int` or :obj:`str`

        :param name: Invite link name; 0-32 characters
        :type name: :obj:`str`

        :param expire_date: Point in time (Unix timestamp) when the link will expire
        :type expire_date: :obj:`int` or :obj:`datetime`

        :param member_limit: Maximum number of users that can be members of the chat simultaneously
        :type member_limit: :obj:`int`

        :param creates_join_request: True, if users joining the chat via the link need to be approved by chat administrators. If True, member_limit can't be specified
        :type creates_join_request: :obj:`bool`

        :return: Returns the new invite link as ChatInviteLink object.
        :rtype: :class:`telebot.types.ChatInviteLink`
        """
        return types.ChatInviteLink.de_json(
            apihelper.create_chat_invite_link(self.token, chat_id, name, expire_date, member_limit, creates_join_request)
        )

    def edit_chat_invite_link(
            self, chat_id: Union[int, str],
            invite_link: Optional[str] = None,
            name: Optional[str]=None,
            expire_date: Optional[Union[int, datetime]]=None,
            member_limit: Optional[int]=None,
            creates_join_request: Optional[bool]=None) -> types.ChatInviteLink:
        """
        Use this method to edit a non-primary invite link created by the bot.
        The bot must be an administrator in the chat for this to work and must have the appropriate admin rights.

        Telegram documentation: https://core.telegram.org/bots/api#editchatinvitelink

        :param chat_id: Id: Unique identifier for the target chat or username of the target channel
            (in the format @channelusername)
        :type chat_id: :obj:`int` or :obj:`str`

        :param name: Invite link name; 0-32 characters
        :type name: :obj:`str`

        :param invite_link: The invite link to edit
        :type invite_link: :obj:`str`

        :param expire_date: Point in time (Unix timestamp) when the link will expire
        :type expire_date: :obj:`int` or :obj:`datetime`

        :param member_limit: Maximum number of users that can be members of the chat simultaneously
        :type member_limit: :obj:`int`

        :param creates_join_request: True, if users joining the chat via the link need to be approved by chat administrators. If True, member_limit can't be specified
        :type creates_join_request: :obj:`bool`

        :return: Returns the new invite link as ChatInviteLink object.
        :rtype: :class:`telebot.types.ChatInviteLink`
        """
        return types.ChatInviteLink.de_json(
            apihelper.edit_chat_invite_link(self.token, chat_id, name, invite_link, expire_date, member_limit, creates_join_request)
        )

    def revoke_chat_invite_link(
            self, chat_id: Union[int, str], invite_link: str) -> types.ChatInviteLink:
        """
        Use this method to revoke an invite link created by the bot.
        Note: If the primary link is revoked, a new link is automatically generated The bot must be an administrator 
        in the chat for this to work and must have the appropriate admin rights.

        Telegram documentation: https://core.telegram.org/bots/api#revokechatinvitelink

        :param chat_id: Id: Unique identifier for the target chat or username of the target channel
            (in the format @channelusername)
        :type chat_id: :obj:`int` or :obj:`str`

        :param invite_link: The invite link to revoke
        :type invite_link: :obj:`str`

        :return: Returns the new invite link as ChatInviteLink object.
        :rtype: :class:`telebot.types.ChatInviteLink`
        """
        return types.ChatInviteLink.de_json(
            apihelper.revoke_chat_invite_link(self.token, chat_id, invite_link)
        )

    def export_chat_invite_link(self, chat_id: Union[int, str]) -> str:
        """
        Use this method to export an invite link to a supergroup or a channel. The bot must be an administrator
        in the chat for this to work and must have the appropriate admin rights.

        Telegram documentation: https://core.telegram.org/bots/api#exportchatinvitelink

        :param chat_id: Id: Unique identifier for the target chat or username of the target channel
            (in the format @channelusername)
        :type chat_id: :obj:`int` or :obj:`str`

        :return: exported invite link as String on success.
        :rtype: :obj:`str`
        """
        return apihelper.export_chat_invite_link(self.token, chat_id)

    def approve_chat_join_request(self, chat_id: Union[str, int], user_id: Union[int, str]) -> bool:
        """
        Use this method to approve a chat join request. 
        The bot must be an administrator in the chat for this to work and must have
        the can_invite_users administrator right. Returns True on success.

        Telegram documentation: https://core.telegram.org/bots/api#approvechatjoinrequest

        :param chat_id: Unique identifier for the target chat or username of the target supergroup
            (in the format @supergroupusername)
        :type chat_id: :obj:`int` or :obj:`str`

        :param user_id: Unique identifier of the target user
        :type user_id: :obj:`int` or :obj:`str`

        :return: True on success.
        :rtype: :obj:`bool`
        """
        return apihelper.approve_chat_join_request(self.token, chat_id, user_id)

    def decline_chat_join_request(self, chat_id: Union[str, int], user_id: Union[int, str]) -> bool:
        """
        Use this method to decline a chat join request. 
        The bot must be an administrator in the chat for this to work and must have
        the can_invite_users administrator right. Returns True on success.

        Telegram documentation: https://core.telegram.org/bots/api#declinechatjoinrequest

        :param chat_id: Unique identifier for the target chat or username of the target supergroup
            (in the format @supergroupusername)
        :type chat_id: :obj:`int` or :obj:`str`

        :param user_id: Unique identifier of the target user
        :type user_id: :obj:`int` or :obj:`str`

        :return: True on success.
        :rtype: :obj:`bool`
        """
        return apihelper.decline_chat_join_request(self.token, chat_id, user_id)

    def set_chat_photo(self, chat_id: Union[int, str], photo: Any) -> bool:
        """
        Use this method to set a new profile photo for the chat. Photos can't be changed for private chats.
        The bot must be an administrator in the chat for this to work and must have the appropriate admin rights.
        Returns True on success.
        Note: In regular groups (non-supergroups), this method will only work if the ‘All Members Are Admins’
        setting is off in the target group.

        Telegram documentation: https://core.telegram.org/bots/api#setchatphoto

        :param chat_id: Int or Str: Unique identifier for the target chat or username of the target channel
            (in the format @channelusername)
        :type chat_id: :obj:`int` or :obj:`str`

        :param photo: InputFile: New chat photo, uploaded using multipart/form-data
        :type photo: :obj:`typing.Union[file_like, str]`
        :return: True on success.
        :rtype: :obj:`bool`
        """
        return apihelper.set_chat_photo(self.token, chat_id, photo)

    def delete_chat_photo(self, chat_id: Union[int, str]) -> bool:
        """
        Use this method to delete a chat photo. Photos can't be changed for private chats.
        The bot must be an administrator in the chat for this to work and must have the appropriate admin rights.
        Returns True on success.
        Note: In regular groups (non-supergroups), this method will only work if the ‘All Members Are Admins’ setting is off in the target group.

        Telegram documentation: https://core.telegram.org/bots/api#deletechatphoto

        :param chat_id: Int or Str: Unique identifier for the target chat or username of the target channel
            (in the format @channelusername)
        :type chat_id: :obj:`int` or :obj:`str`

        :return: True on success.
        :rtype: :obj:`bool`
        """
        return apihelper.delete_chat_photo(self.token, chat_id)
    
    def get_my_commands(self, scope: Optional[types.BotCommandScope]=None, 
            language_code: Optional[str]=None) -> List[types.BotCommand]:
        """
        Use this method to get the current list of the bot's commands. 
        Returns List of BotCommand on success.

        Telegram documentation: https://core.telegram.org/bots/api#getmycommands

        :param scope: The scope of users for which the commands are relevant. 
            Defaults to BotCommandScopeDefault.
        :type scope: :class:`telebot.types.BotCommandScope`

        :param language_code: A two-letter ISO 639-1 language code. If empty, 
            commands will be applied to all users from the given scope, 
            for whose language there are no dedicated commands
        :type language_code: :obj:`str`

        :return: List of BotCommand on success.
        :rtype: :obj:`list` of :class:`telebot.types.BotCommand`
        """
        result = apihelper.get_my_commands(self.token, scope, language_code)
        return [types.BotCommand.de_json(cmd) for cmd in result]

    def set_chat_menu_button(self, chat_id: Union[int, str]=None, 
                menu_button: types.MenuButton=None) -> bool:
        """
        Use this method to change the bot's menu button in a private chat, 
        or the default menu button. 
        Returns True on success.

        Telegram documentation: https://core.telegram.org/bots/api#setchatmenubutton

        :param chat_id: Unique identifier for the target private chat. 
            If not specified, default bot's menu button will be changed.
        :type chat_id: :obj:`int` or :obj:`str`

        :param menu_button: A JSON-serialized object for the new bot's menu button. Defaults to MenuButtonDefault
        :type menu_button: :class:`telebot.types.MenuButton`

        :return: True on success.
        :rtype: :obj:`bool`
        """
        return apihelper.set_chat_menu_button(self.token, chat_id, menu_button)

    def get_chat_menu_button(self, chat_id: Union[int, str]=None) -> types.MenuButton:
        """
        Use this method to get the current value of the bot's menu button
        in a private chat, or the default menu button.
        Returns MenuButton on success.

        Telegram Documentation: https://core.telegram.org/bots/api#getchatmenubutton

        :param chat_id: Unique identifier for the target private chat.
            If not specified, default bot's menu button will be returned.
        :type chat_id: :obj:`int` or :obj:`str`

        :return: types.MenuButton
        :rtype: :class:`telebot.types.MenuButton`
        """
        return types.MenuButton.de_json(apihelper.get_chat_menu_button(self.token, chat_id))

    def set_my_default_administrator_rights(self, rights: types.ChatAdministratorRights=None, 
                                    for_channels: Optional[bool]=None) -> bool:
        """
        Use this method to change the default administrator rights requested by the bot
        when it's added as an administrator to groups or channels.
        These rights will be suggested to users, but they are are free to modify
        the list before adding the bot. 
        Returns True on success.

        Telegram documentation: https://core.telegram.org/bots/api#setmydefaultadministratorrights

        :param rights: A JSON-serialized object describing new default administrator rights. If not specified,
            the default administrator rights will be cleared.
        :type rights: :class:`telebot.types.ChatAdministratorRights`

        :param for_channels: Pass True to change the default administrator rights of the bot in channels.
            Otherwise, the default administrator rights of the bot for groups and supergroups will be changed.
        :type for_channels: :obj:`bool`

        :return: True on success.
        :rtype: :obj:`bool`
        """
        return apihelper.set_my_default_administrator_rights(self.token, rights, for_channels)

    def get_my_default_administrator_rights(self, for_channels: Optional[bool]=None) -> types.ChatAdministratorRights:
        """
        Use this method to get the current default administrator rights of the bot.
        Returns ChatAdministratorRights on success.

        Telegram documentation: https://core.telegram.org/bots/api#getmydefaultadministratorrights

        :param for_channels: Pass True to get the default administrator rights of the bot in channels. Otherwise, the default administrator rights of the bot for groups and supergroups will be returned.
        :type for_channels: :obj:`bool`

        :return: Returns ChatAdministratorRights on success.
        :rtype: :class:`telebot.types.ChatAdministratorRights`
        """
        return types.ChatAdministratorRights.de_json(apihelper.get_my_default_administrator_rights(self.token, for_channels))
        
    def set_my_commands(self, commands: List[types.BotCommand],
            scope: Optional[types.BotCommandScope]=None,
            language_code: Optional[str]=None) -> bool:
        """
        Use this method to change the list of the bot's commands.

        Telegram documentation: https://core.telegram.org/bots/api#setmycommands

        :param commands: List of BotCommand. At most 100 commands can be specified.
        :type commands: :obj:`list` of :class:`telebot.types.BotCommand`

        :param scope: The scope of users for which the commands are relevant. 
            Defaults to BotCommandScopeDefault.
        :type scope: :class:`telebot.types.BotCommandScope`

        :param language_code: A two-letter ISO 639-1 language code. If empty, 
            commands will be applied to all users from the given scope, 
            for whose language there are no dedicated commands
        :type language_code: :obj:`str`

        :return: True on success.
        :rtype: :obj:`bool`
        """
        return apihelper.set_my_commands(self.token, commands, scope, language_code)
    
    def delete_my_commands(self, scope: Optional[types.BotCommandScope]=None, 
            language_code: Optional[str]=None) -> bool:
        """
        Use this method to delete the list of the bot's commands for the given scope and user language. 
        After deletion, higher level commands will be shown to affected users. 
        Returns True on success.

        Telegram documentation: https://core.telegram.org/bots/api#deletemycommands
        
        :param scope: The scope of users for which the commands are relevant. 
            Defaults to BotCommandScopeDefault.
        :type scope: :class:`telebot.types.BotCommandScope`

        :param language_code: A two-letter ISO 639-1 language code. If empty, 
            commands will be applied to all users from the given scope, 
            for whose language there are no dedicated commands
        :type language_code: :obj:`str`

        :return: True on success.
        :rtype: :obj:`bool`
        """
        return apihelper.delete_my_commands(self.token, scope, language_code)

    def set_chat_title(self, chat_id: Union[int, str], title: str) -> bool:
        """
        Use this method to change the title of a chat. Titles can't be changed for private chats.
        The bot must be an administrator in the chat for this to work and must have the appropriate admin rights.
        Returns True on success.
        Note: In regular groups (non-supergroups), this method will only work if the ‘All Members Are Admins’
        setting is off in the target group.

        Telegram documentation: https://core.telegram.org/bots/api#setchattitle

        :param chat_id: Unique identifier for the target chat or username of the target channel
            (in the format @channelusername)
        :type chat_id: :obj:`int` or :obj:`str`

        :param title: New chat title, 1-255 characters
        :type title: :obj:`str`

        :return: True on success.
        :rtype: :obj:`bool`
        """
        return apihelper.set_chat_title(self.token, chat_id, title)

    def set_chat_description(self, chat_id: Union[int, str], description: Optional[str]=None) -> bool:
        """
        Use this method to change the description of a supergroup or a channel.
        The bot must be an administrator in the chat for this to work and must have the appropriate admin rights.

        Telegram documentation: https://core.telegram.org/bots/api#setchatdescription

        :param chat_id: Unique identifier for the target chat or username of the target channel
            (in the format @channelusername)
        :type chat_id: :obj:`int` or :obj:`str`

        :param description: Str: New chat description, 0-255 characters
        :type description: :obj:`str`

        :return: True on success.
        :rtype: :obj:`bool`
        """
        return apihelper.set_chat_description(self.token, chat_id, description)

    def pin_chat_message(
            self, chat_id: Union[int, str], message_id: int, 
            disable_notification: Optional[bool]=False) -> bool:
        """
        Use this method to pin a message in a supergroup.
        The bot must be an administrator in the chat for this to work and must have the appropriate admin rights.
        Returns True on success.

        Telegram documentation: https://core.telegram.org/bots/api#pinchatmessage

        :param chat_id: Unique identifier for the target chat or username of the target channel
            (in the format @channelusername)
        :type chat_id: :obj:`int` or :obj:`str`

        :param message_id: Identifier of a message to pin
        :type message_id: :obj:`int`

        :param disable_notification: Pass True, if it is not necessary to send a notification
            to all group members about the new pinned message
        :type disable_notification: :obj:`bool`

        :return: True on success.
        :rtype: :obj:`bool`
        """
        return apihelper.pin_chat_message(self.token, chat_id, message_id, disable_notification)

    def unpin_chat_message(self, chat_id: Union[int, str], message_id: Optional[int]=None) -> bool:
        """
        Use this method to unpin specific pinned message in a supergroup chat.
        The bot must be an administrator in the chat for this to work and must have the appropriate admin rights.
        Returns True on success.

        Telegram documentation: https://core.telegram.org/bots/api#unpinchatmessage

        :param chat_id: Unique identifier for the target chat or username of the target channel
            (in the format @channelusername)
        :type chat_id: :obj:`int` or :obj:`str`

        :param message_id: Int: Identifier of a message to unpin
        :type message_id: :obj:`int`

        :return: True on success.
        :rtype: :obj:`bool`
        """
        return apihelper.unpin_chat_message(self.token, chat_id, message_id)

    def unpin_all_chat_messages(self, chat_id: Union[int, str]) -> bool:
        """
        Use this method to unpin a all pinned messages in a supergroup chat.
        The bot must be an administrator in the chat for this to work and must have the appropriate admin rights.
        Returns True on success.

        Telegram documentation: https://core.telegram.org/bots/api#unpinallchatmessages

        :param chat_id: Int or Str: Unique identifier for the target chat or username of the target channel
            (in the format @channelusername)
        :type chat_id: :obj:`int` or :obj:`str`

        :return: True on success.
        :rtype: :obj:`bool`
        """
        return apihelper.unpin_all_chat_messages(self.token, chat_id)

    def edit_message_text(
            self, text: str, 
            chat_id: Optional[Union[int, str]]=None, 
            message_id: Optional[int]=None, 
            inline_message_id: Optional[str]=None, 
            parse_mode: Optional[str]=None,
            entities: Optional[List[types.MessageEntity]]=None,
            disable_web_page_preview: Optional[bool]=None,
            reply_markup: Optional[REPLY_MARKUP_TYPES]=None) -> Union[types.Message, bool]:
        """
        Use this method to edit text and game messages.

        Telegram documentation: https://core.telegram.org/bots/api#editmessagetext

        :param text: New text of the message, 1-4096 characters after entities parsing
        :type text: :obj:`str`

        :param chat_id: Required if inline_message_id is not specified. Unique identifier for the target chat or username of the target channel (in the format @channelusername)
        :type chat_id: :obj:`int` or :obj:`str`

        :param message_id: Required if inline_message_id is not specified. Identifier of the sent message
        :type message_id: :obj:`int`

        :param inline_message_id: Required if chat_id and message_id are not specified. Identifier of the inline message
        :type inline_message_id: :obj:`str`

        :param parse_mode: Mode for parsing entities in the message text.
        :type parse_mode: :obj:`str`

        :param entities: List of special entities that appear in the message text, which can be specified instead of parse_mode
        :type entities: List of :obj:`telebot.types.MessageEntity`

        :param disable_web_page_preview: Disables link previews for links in this message
        :type disable_web_page_preview: :obj:`bool`

        :param reply_markup: A JSON-serialized object for an inline keyboard.
        :type reply_markup: :obj:`InlineKeyboardMarkup`

        :return: On success, if edited message is sent by the bot, the edited Message is returned, otherwise True is returned.
        :rtype: :obj:`types.Message` or :obj:`bool`
        """
        parse_mode = self.parse_mode if (parse_mode is None) else parse_mode

        result = apihelper.edit_message_text(self.token, text, chat_id, message_id, inline_message_id, parse_mode,
                                             entities, disable_web_page_preview, reply_markup)
        if type(result) == bool:  # if edit inline message return is bool not Message.
            return result
        return types.Message.de_json(result)

    def edit_message_media(
            self, media: Any, chat_id: Optional[Union[int, str]]=None, 
            message_id: Optional[int]=None,
            inline_message_id: Optional[str]=None, 
            reply_markup: Optional[REPLY_MARKUP_TYPES]=None) -> Union[types.Message, bool]:
        """
        Use this method to edit animation, audio, document, photo, or video messages.
        If a message is a part of a message album, then it can be edited only to a photo or a video.
        Otherwise, message type can be changed arbitrarily. When inline message is edited, new file can't be uploaded.
        Use previously uploaded file via its file_id or specify a URL.

        Telegram documentation: https://core.telegram.org/bots/api#editmessagemedia

        :param media: A JSON-serialized object for a new media content of the message
        :type media: :obj:`InputMedia`
        :param chat_id: Required if inline_message_id is not specified. Unique identifier for the target chat or username of the target channel (in the format @channelusername)
        :type chat_id: :obj:`int` or :obj:`str`

        :param message_id: Required if inline_message_id is not specified. Identifier of the sent message 
        :type message_id: :obj:`int`

        :param inline_message_id: Required if chat_id and message_id are not specified. Identifier of the inline message
        :type inline_message_id: :obj:`str`

        :param reply_markup: A JSON-serialized object for an inline keyboard.
        :type reply_markup: :obj:`telebot.types.InlineKeyboardMarkup` or :obj:`ReplyKeyboardMarkup` or :obj:`ReplyKeyboardRemove` or :obj:`ForceReply`

        :return: On success, if edited message is sent by the bot, the edited Message is returned, otherwise True is returned.
        :rtype: :obj:`types.Message` or :obj:`bool`
        """
        result = apihelper.edit_message_media(self.token, media, chat_id, message_id, inline_message_id, reply_markup)
        if type(result) == bool:  # if edit inline message return is bool not Message.
            return result
        return types.Message.de_json(result)

    def edit_message_reply_markup(
            self, chat_id: Optional[Union[int, str]]=None, 
            message_id: Optional[int]=None,
            inline_message_id: Optional[str]=None, 
            reply_markup: Optional[REPLY_MARKUP_TYPES]=None) -> Union[types.Message, bool]:
        """
        Use this method to edit only the reply markup of messages.

        Telegram documentation: https://core.telegram.org/bots/api#editmessagereplymarkup

        :param chat_id: Required if inline_message_id is not specified. Unique identifier for the target chat or username of the target channel (in the format @channelusername)
        :type chat_id: :obj:`int` or :obj:`str`

        :param message_id: Required if inline_message_id is not specified. Identifier of the sent message
        :type message_id: :obj:`int`

        :param inline_message_id: Required if chat_id and message_id are not specified. Identifier of the inline message
        :type inline_message_id: :obj:`str`

        :param reply_markup: A JSON-serialized object for an inline keyboard.
        :type reply_markup: :obj:`InlineKeyboardMarkup` or :obj:`ReplyKeyboardMarkup` or :obj:`ReplyKeyboardRemove` or :obj:`ForceReply`

        :return: On success, if edited message is sent by the bot, the edited Message is returned, otherwise True is returned.
        :rtype: :obj:`types.Message` or :obj:`bool`
        """
        result = apihelper.edit_message_reply_markup(self.token, chat_id, message_id, inline_message_id, reply_markup)
        if type(result) == bool:
            return result
        return types.Message.de_json(result)

    def send_game(
            self, chat_id: Union[int, str], game_short_name: str, 
            disable_notification: Optional[bool]=None,
            reply_to_message_id: Optional[int]=None, 
            reply_markup: Optional[REPLY_MARKUP_TYPES]=None, 
            timeout: Optional[int]=None,
            allow_sending_without_reply: Optional[bool]=None,
            protect_content: Optional[bool]=None) -> types.Message:
        """
        Used to send the game.

        Telegram documentation: https://core.telegram.org/bots/api#sendgame

        :param chat_id: Unique identifier for the target chat or username of the target channel (in the format @channelusername)
        :type chat_id: :obj:`int` or :obj:`str`

        :param game_short_name: Short name of the game, serves as the unique identifier for the game. Set up your games via @BotFather.
        :type game_short_name: :obj:`str`

        :param disable_notification: Sends the message silently. Users will receive a notification with no sound.
        :type disable_notification: :obj:`bool`

        :param reply_to_message_id: If the message is a reply, ID of the original message 
        :type reply_to_message_id: :obj:`int`

        :param reply_markup: Additional interface options. A JSON-serialized object for an inline keyboard, custom reply keyboard, instructions to remove reply keyboard or to force a reply from the user.
        :type reply_markup: :obj:`InlineKeyboardMarkup` or :obj:`ReplyKeyboardMarkup` or :obj:`ReplyKeyboardRemove` or :obj:`ForceReply`

        :param timeout: Timeout in seconds for waiting for a response from the bot.
        :type timeout: :obj:`int`

        :param allow_sending_without_reply: Pass True, if the message should be sent even if one of the specified replied-to messages is not found.
        :type allow_sending_without_reply: :obj:`bool`

        :param protect_content: Pass True, if content of the message needs to be protected from being viewed by the bot.
        :type protect_content: :obj:`bool`

        :return: On success, the sent Message is returned.
        :rtype: :obj:`types.Message`
        """
        result = apihelper.send_game(
            self.token, chat_id, game_short_name, disable_notification,
            reply_to_message_id, reply_markup, timeout, 
            allow_sending_without_reply, protect_content)
        return types.Message.de_json(result)

    def set_game_score(
            self, user_id: Union[int, str], score: int, 
            force: Optional[bool]=None, 
            chat_id: Optional[Union[int, str]]=None, 
            message_id: Optional[int]=None, 
            inline_message_id: Optional[str]=None,
            disable_edit_message: Optional[bool]=None) -> Union[types.Message, bool]:
        """
        Sets the value of points in the game to a specific user.

        Telegram documentation: https://core.telegram.org/bots/api#setgamescore

        :param user_id: User identifier
        :type user_id: :obj:`int` or :obj:`str`

        :param score: New score, must be non-negative
        :type score: :obj:`int`

        :param force: Pass True, if the high score is allowed to decrease. This can be useful when fixing mistakes or banning cheaters
        :type force: :obj:`bool`

        :param chat_id: Required if inline_message_id is not specified. Unique identifier for the target chat or username of the target channel (in the format @channelusername)
        :type chat_id: :obj:`int` or :obj:`str`

        :param message_id: Required if inline_message_id is not specified. Identifier of the sent message
        :type message_id: :obj:`int`

        :param inline_message_id: Required if chat_id and message_id are not specified. Identifier of the inline message
        :type inline_message_id: :obj:`str`

        :param disable_edit_message: Pass True, if the game message should not be automatically edited to include the current scoreboard
        :type disable_edit_message: :obj:`bool`

        :return: On success, if the message was sent by the bot, returns the edited Message, otherwise returns True.
        :rtype: :obj:`types.Message` or :obj:`bool`
        """
        result = apihelper.set_game_score(self.token, user_id, score, force, disable_edit_message, chat_id,
                                          message_id, inline_message_id)
        if type(result) == bool:
            return result
        return types.Message.de_json(result)

    def get_game_high_scores(
            self, user_id: int, chat_id: Optional[Union[int, str]]=None,
            message_id: Optional[int]=None, 
            inline_message_id: Optional[str]=None) -> List[types.GameHighScore]:
        """
        Use this method to get data for high score tables. Will return the score of the specified user and several of
        their neighbors in a game. On success, returns an Array of GameHighScore objects.

        This method will currently return scores for the target user, plus two of their closest neighbors on each side.
        Will also return the top three users if the user and their neighbors are not among them.
        Please note that this behavior is subject to change.

        Telegram documentation: https://core.telegram.org/bots/api#getgamehighscores

        :param user_id: User identifier
        :type user_id: :obj:`int`

        :param chat_id: Required if inline_message_id is not specified. Unique identifier for the target chat or username of the target channel (in the format @channelusername)
        :type chat_id: :obj:`int` or :obj:`str`

        :param message_id: Required if inline_message_id is not specified. Identifier of the sent message
        :type message_id: :obj:`int`

        :param inline_message_id: Required if chat_id and message_id are not specified. Identifier of the inline message
        :type inline_message_id: :obj:`str`

        :return: On success, returns an Array of GameHighScore objects.
        :rtype: List[types.GameHighScore]
        """
        result = apihelper.get_game_high_scores(self.token, user_id, chat_id, message_id, inline_message_id)
        return [types.GameHighScore.de_json(r) for r in result]

    # TODO: rewrite this method like in API
    def send_invoice(
            self, chat_id: Union[int, str], title: str, description: str, 
            invoice_payload: str, provider_token: str, currency: str, 
            prices: List[types.LabeledPrice], start_parameter: Optional[str]=None, 
            photo_url: Optional[str]=None, photo_size: Optional[int]=None, 
            photo_width: Optional[int]=None, photo_height: Optional[int]=None,
            need_name: Optional[bool]=None, need_phone_number: Optional[bool]=None, 
            need_email: Optional[bool]=None, need_shipping_address: Optional[bool]=None,
            send_phone_number_to_provider: Optional[bool]=None, 
            send_email_to_provider: Optional[bool]=None, 
            is_flexible: Optional[bool]=None,
            disable_notification: Optional[bool]=None, 
            reply_to_message_id: Optional[int]=None, 
            reply_markup: Optional[REPLY_MARKUP_TYPES]=None, 
            provider_data: Optional[str]=None, 
            timeout: Optional[int]=None,
            allow_sending_without_reply: Optional[bool]=None,
            max_tip_amount: Optional[int] = None,
            suggested_tip_amounts: Optional[List[int]]=None,
            protect_content: Optional[bool]=None) -> types.Message:
        """
        Sends invoice.

        Telegram documentation: https://core.telegram.org/bots/api#sendinvoice

        :param chat_id: Unique identifier for the target private chat
        :type chat_id: :obj:`int` or :obj:`str`

        :param title: Product name, 1-32 characters
        :type title: :obj:`str`

        :param description: Product description, 1-255 characters
        :type description: :obj:`str`

        :param invoice_payload: Bot-defined invoice payload, 1-128 bytes. This will not be displayed to the user,
            use for your internal processes.
        :type invoice_payload: :obj:`str`

        :param provider_token: Payments provider token, obtained via @Botfather
        :type provider_token: :obj:`str`

        :param currency: Three-letter ISO 4217 currency code,
            see https://core.telegram.org/bots/payments#supported-currencies
        :type currency: :obj:`str`

        :param prices: Price breakdown, a list of components
            (e.g. product price, tax, discount, delivery cost, delivery tax, bonus, etc.)
        :type prices: List[:obj:`types.LabeledPrice`]

        :param start_parameter: Unique deep-linking parameter that can be used to generate this invoice
            when used as a start parameter
        :type start_parameter: :obj:`str`

        :param photo_url: URL of the product photo for the invoice. Can be a photo of the goods
            or a marketing image for a service. People like it better when they see what they are paying for.
        :type photo_url: :obj:`str`

        :param photo_size: Photo size in bytes
        :type photo_size: :obj:`int`

        :param photo_width: Photo width 
        :type photo_width: :obj:`int`

        :param photo_height: Photo height
        :type photo_height: :obj:`int`

        :param need_name: Pass True, if you require the user's full name to complete the order
        :type need_name: :obj:`bool`

        :param need_phone_number: Pass True, if you require the user's phone number to complete the order
        :type need_phone_number: :obj:`bool`

        :param need_email: Pass True, if you require the user's email to complete the order
        :type need_email: :obj:`bool`

        :param need_shipping_address: Pass True, if you require the user's shipping address to complete the order
        :type need_shipping_address: :obj:`bool`

        :param is_flexible: Pass True, if the final price depends on the shipping method
        :type is_flexible: :obj:`bool`

        :param send_phone_number_to_provider: Pass True, if user's phone number should be sent to provider
        :type send_phone_number_to_provider: :obj:`bool`

        :param send_email_to_provider: Pass True, if user's email address should be sent to provider
        :type send_email_to_provider: :obj:`bool`

        :param disable_notification: Sends the message silently. Users will receive a notification with no sound.
        :type disable_notification: :obj:`bool`

        :param reply_to_message_id: If the message is a reply, ID of the original message
        :type reply_to_message_id: :obj:`int`

        :param reply_markup: A JSON-serialized object for an inline keyboard. If empty,
            one 'Pay total price' button will be shown. If not empty, the first button must be a Pay button
        :type reply_markup: :obj:`str`

        :param provider_data: A JSON-serialized data about the invoice, which will be shared with the payment provider.
            A detailed description of required fields should be provided by the payment provider.
        :type provider_data: :obj:`str`

        :param timeout: Timeout of a request, defaults to None
        :type timeout: :obj:`int`

        :param allow_sending_without_reply: Pass True, if the message should be sent even if the specified replied-to message is not found
        :type allow_sending_without_reply: :obj:`bool`

        :param max_tip_amount: The maximum accepted amount for tips in the smallest units of the currency
        :type max_tip_amount: :obj:`int`

        :param suggested_tip_amounts: A JSON-serialized array of suggested amounts of tips in the smallest
            units of the currency.  At most 4 suggested tip amounts can be specified. The suggested tip
            amounts must be positive, passed in a strictly increased order and must not exceed max_tip_amount.
        :type suggested_tip_amounts: :obj:`list` of :obj:`int`

        :param protect_content: Protects the contents of the sent message from forwarding and saving
        :type protect_content: :obj:`bool`

        :return: On success, the sent Message is returned.
        :rtype: :obj:`types.Message`
        """
        result = apihelper.send_invoice(
            self.token, chat_id, title, description, invoice_payload, provider_token,
            currency, prices, start_parameter, photo_url, photo_size, photo_width,
            photo_height, need_name, need_phone_number, need_email, need_shipping_address,
            send_phone_number_to_provider, send_email_to_provider, is_flexible, disable_notification,
            reply_to_message_id, reply_markup, provider_data, timeout, allow_sending_without_reply,
            max_tip_amount, suggested_tip_amounts, protect_content)
        return types.Message.de_json(result)

    def create_invoice_link(self,
            title: str, description: str, payload:str, provider_token: str, 
            currency: str, prices: List[types.LabeledPrice],
            max_tip_amount: Optional[int] = None, 
            suggested_tip_amounts: Optional[List[int]]=None,
            provider_data: Optional[str]=None,
            photo_url: Optional[str]=None,
            photo_size: Optional[int]=None,
            photo_width: Optional[int]=None,
            photo_height: Optional[int]=None,
            need_name: Optional[bool]=None,
            need_phone_number: Optional[bool]=None,
            need_email: Optional[bool]=None,
            need_shipping_address: Optional[bool]=None,
            send_phone_number_to_provider: Optional[bool]=None,
            send_email_to_provider: Optional[bool]=None,
            is_flexible: Optional[bool]=None) -> str:
            
        """
        Use this method to create a link for an invoice. 
        Returns the created invoice link as String on success.

        Telegram documentation:
        https://core.telegram.org/bots/api#createinvoicelink

        :param title: Product name, 1-32 characters
        :type title: :obj:`str`

        :param description: Product description, 1-255 characters
        :type description: :obj:`str`

        :param payload: Bot-defined invoice payload, 1-128 bytes. This will not be displayed to the user,
            use for your internal processes.
        :type payload: :obj:`str`

        :param provider_token: Payments provider token, obtained via @Botfather
        :type provider_token: :obj:`str`

        :param currency: Three-letter ISO 4217 currency code,
            see https://core.telegram.org/bots/payments#supported-currencies
        :type currency: :obj:`str`

        :param prices: Price breakdown, a list of components
            (e.g. product price, tax, discount, delivery cost, delivery tax, bonus, etc.)
        :type prices: :obj:`list` of :obj:`types.LabeledPrice`

        :param max_tip_amount: The maximum accepted amount for tips in the smallest units of the currency
        :type max_tip_amount: :obj:`int`

        :param suggested_tip_amounts: A JSON-serialized array of suggested amounts of tips in the smallest
            units of the currency.  At most 4 suggested tip amounts can be specified. The suggested tip
            amounts must be positive, passed in a strictly increased order and must not exceed max_tip_amount.
        :type suggested_tip_amounts: :obj:`list` of :obj:`int`

        :param provider_data: A JSON-serialized data about the invoice, which will be shared with the payment provider.
            A detailed description of required fields should be provided by the payment provider.
        :type provider_data: :obj:`str`

        :param photo_url: URL of the product photo for the invoice. Can be a photo of the goods
            or a photo of the invoice. People like it better when they see a photo of what they are paying for.
        :type photo_url: :obj:`str`

        :param photo_size: Photo size in bytes
        :type photo_size: :obj:`int`

        :param photo_width: Photo width
        :type photo_width: :obj:`int`

        :param photo_height: Photo height
        :type photo_height: :obj:`int`

        :param need_name: Pass True, if you require the user's full name to complete the order
        :type need_name: :obj:`bool`

        :param need_phone_number: Pass True, if you require the user's phone number to complete the order
        :type need_phone_number: :obj:`bool`

        :param need_email: Pass True, if you require the user's email to complete the order
        :type need_email: :obj:`bool`

        :param need_shipping_address: Pass True, if you require the user's shipping address to complete the order
        :type need_shipping_address: :obj:`bool`

        :param send_phone_number_to_provider: Pass True, if user's phone number should be sent to provider
        :type send_phone_number_to_provider: :obj:`bool`

        :param send_email_to_provider: Pass True, if user's email address should be sent to provider
        :type send_email_to_provider: :obj:`bool`

        :param is_flexible: Pass True, if the final price depends on the shipping method
        :type is_flexible: :obj:`bool`

        :return: Created invoice link as String on success.
        :rtype: :obj:`str`
        """
        result = apihelper.create_invoice_link(
            self.token, title, description, payload, provider_token,
            currency, prices, max_tip_amount, suggested_tip_amounts, provider_data,
            photo_url, photo_size, photo_width, photo_height, need_name, need_phone_number,
            need_email, need_shipping_address, send_phone_number_to_provider,
            send_email_to_provider, is_flexible)
        return result

    # noinspection PyShadowingBuiltins
    # TODO: rewrite this method like in API
    def send_poll(
            self, chat_id: Union[int, str], question: str, options: List[str],
            is_anonymous: Optional[bool]=None, type: Optional[str]=None, 
            allows_multiple_answers: Optional[bool]=None, 
            correct_option_id: Optional[int]=None,
            explanation: Optional[str]=None, 
            explanation_parse_mode: Optional[str]=None, 
            open_period: Optional[int]=None, 
            close_date: Optional[Union[int, datetime]]=None, 
            is_closed: Optional[bool]=None,
            disable_notification: Optional[bool]=False,
            reply_to_message_id: Optional[int]=None, 
            reply_markup: Optional[REPLY_MARKUP_TYPES]=None, 
            allow_sending_without_reply: Optional[bool]=None, 
            timeout: Optional[int]=None,
            explanation_entities: Optional[List[types.MessageEntity]]=None,
            protect_content: Optional[bool]=None) -> types.Message:
        """
        Use this method to send a native poll.
        On success, the sent Message is returned.

        Telegram documentation: https://core.telegram.org/bots/api#sendpoll

        :param chat_id: Unique identifier for the target chat or username of the target channel
        :type chat_id: :obj:`int` | :obj:`str`

        :param question: Poll question, 1-300 characters
        :type question: :obj:`str`

        :param options: A JSON-serialized list of answer options, 2-10 strings 1-100 characters each
        :type options: :obj:`list` of :obj:`str`

        :param is_anonymous: True, if the poll needs to be anonymous, defaults to True
        :type is_anonymous: :obj:`bool`

        :param type: Poll type, “quiz” or “regular”, defaults to “regular”
        :type type: :obj:`str`

        :param allows_multiple_answers: True, if the poll allows multiple answers, ignored for polls in quiz mode, defaults to False
        :type allows_multiple_answers: :obj:`bool`

        :param correct_option_id: 0-based identifier of the correct answer option. Available only for polls in quiz mode,
            defaults to None
        :type correct_option_id: :obj:`int`

        :param explanation: Text that is shown when a user chooses an incorrect answer or taps on the lamp icon in a quiz-style poll,
            0-200 characters with at most 2 line feeds after entities parsing
        :type explanation: :obj:`str`

        :param explanation_parse_mode: Mode for parsing entities in the explanation. See formatting options for more details.
        :type explanation_parse_mode: :obj:`str`

        :param open_period: Amount of time in seconds the poll will be active after creation, 5-600. Can't be used together with close_date.
        :type open_period: :obj:`int`

        :param close_date: Point in time (Unix timestamp) when the poll will be automatically closed.
        :type close_date: :obj:`int` | :obj:`datetime`

        :param is_closed: Pass True, if the poll needs to be immediately closed. This can be useful for poll preview.
        :type is_closed: :obj:`bool`

        :param disable_notification: Sends the message silently. Users will receive a notification with no sound.
        :type disable_notification: :obj:`bool`

        :param reply_to_message_id: If the message is a reply, ID of the original message
        :type reply_to_message_id: :obj:`int`

        :param allow_sending_without_reply: Pass True, if the poll allows multiple options to be voted simultaneously.
        :type allow_sending_without_reply: :obj:`bool`

        :param reply_markup: Additional interface options. A JSON-serialized object for an inline keyboard, custom reply keyboard,
            instructions to remove reply keyboard or to force a reply from the user.
        :type reply_markup: :obj:`InlineKeyboardMarkup` | :obj:`ReplyKeyboardMarkup` | :obj:`ReplyKeyboardRemove` | :obj:`ForceReply`

        :param timeout: Timeout in seconds for waiting for a response from the user.
        :type timeout: :obj:`int`

        :param explanation_entities: A JSON-serialized list of special entities that appear in the explanation,
            which can be specified instead of parse_mode
        :type explanation_entities: :obj:`list` of :obj:`MessageEntity`

        :param protect_content: Protects the contents of the sent message from forwarding and saving
        :type protect_content: :obj:`bool`

        :return: On success, the sent Message is returned.
        :rtype: :obj:`types.Message`
        """
        if isinstance(question, types.Poll):
            raise RuntimeError("The send_poll signature was changed, please see send_poll function details.")

        explanation_parse_mode = self.parse_mode if (explanation_parse_mode is None) else explanation_parse_mode

        return types.Message.de_json(
            apihelper.send_poll(
                self.token, chat_id,
                question, options,
                is_anonymous, type, allows_multiple_answers, correct_option_id,
                explanation, explanation_parse_mode, open_period, close_date, is_closed,
                disable_notification, reply_to_message_id, allow_sending_without_reply,
                reply_markup, timeout, explanation_entities, protect_content))

    def stop_poll(
            self, chat_id: Union[int, str], message_id: int, 
            reply_markup: Optional[REPLY_MARKUP_TYPES]=None) -> types.Poll:
        """
        Use this method to stop a poll which was sent by the bot. On success, the stopped Poll is returned.

        Telegram documentation: https://core.telegram.org/bots/api#stoppoll

        :param chat_id: Unique identifier for the target chat or username of the target channel
        :type chat_id: :obj:`int` | :obj:`str`

        :param message_id: Identifier of the original message with the poll
        :type message_id: :obj:`int`

        :param reply_markup: A JSON-serialized object for a new message markup.
        :type reply_markup: :obj:`InlineKeyboardMarkup` | :obj:`ReplyKeyboardMarkup` | :obj:`ReplyKeyboardRemove` | :obj:`ForceReply`

        :return: On success, the stopped Poll is returned.
        :rtype: :obj:`types.Poll`
        """
        return types.Poll.de_json(apihelper.stop_poll(self.token, chat_id, message_id, reply_markup))

    def answer_shipping_query(
            self, shipping_query_id: str, ok: bool, 
            shipping_options: Optional[List[types.ShippingOption]]=None, 
            error_message: Optional[str]=None) -> bool:
        """
        Asks for an answer to a shipping question.

        Telegram documentation: https://core.telegram.org/bots/api#answershippingquery

        :param shipping_query_id: Unique identifier for the query to be answered
        :type shipping_query_id: :obj:`str`

        :param ok: Specify True if delivery to the specified address is possible and False if there are any problems (for example, if delivery to the specified address is not possible)
        :type ok: :obj:`bool`

        :param shipping_options: Required if ok is True. A JSON-serialized array of available shipping options.
        :type shipping_options: :obj:`list` of :obj:`ShippingOption`

        :param error_message: Required if ok is False. Error message in human readable form that explains why it is impossible to complete the order
            (e.g. "Sorry, delivery to your desired address is unavailable'). Telegram will display this message to the user.
        :type error_message: :obj:`str`

        :return: On success, True is returned.
        :rtype: :obj:`bool`
        """
        return apihelper.answer_shipping_query(self.token, shipping_query_id, ok, shipping_options, error_message)

    def answer_pre_checkout_query(
            self, pre_checkout_query_id: int, ok: bool, 
            error_message: Optional[str]=None) -> bool:
        """
        Once the user has confirmed their payment and shipping details, the Bot API sends the final confirmation in the form of an Update with the
        field pre_checkout_query. Use this method to respond to such pre-checkout queries.
        On success, True is returned.

        .. note::
            The Bot API must receive an answer within 10 seconds after the pre-checkout query was sent.

        Telegram documentation: https://core.telegram.org/bots/api#answerprecheckoutquery

        :param pre_checkout_query_id: Unique identifier for the query to be answered 
        :type pre_checkout_query_id: :obj:`int`

        :param ok: Specify True if everything is alright (goods are available, etc.) and the bot is ready to proceed with the order. Use False if there are any problems.
        :type ok: :obj:`bool`

        :param error_message: Required if ok is False. Error message in human readable form that explains the reason for failure to proceed with the checkout
            (e.g. "Sorry, somebody just bought the last of our amazing black T-shirts while you were busy filling out your payment details. Please choose a different
            color or garment!"). Telegram will display this message to the user.
        :type error_message: :obj:`str`

        :return: On success, True is returned.
        :rtype: :obj:`bool`
        """
        return apihelper.answer_pre_checkout_query(self.token, pre_checkout_query_id, ok, error_message)

    def edit_message_caption(
            self, caption: str, chat_id: Optional[Union[int, str]]=None, 
            message_id: Optional[int]=None, 
            inline_message_id: Optional[str]=None,
            parse_mode: Optional[str]=None, 
            caption_entities: Optional[List[types.MessageEntity]]=None,
            reply_markup: Optional[REPLY_MARKUP_TYPES]=None) -> Union[types.Message, bool]:
        """
        Use this method to edit captions of messages.

        Telegram documentation: https://core.telegram.org/bots/api#editmessagecaption

        :param caption: New caption of the message
        :type caption: :obj:`str`

        :param chat_id: Required if inline_message_id is not specified. Unique identifier for the target chat or username of the target channel
        :type chat_id: :obj:`int` | :obj:`str`

        :param message_id: Required if inline_message_id is not specified.
        :type message_id: :obj:`int`

        :param inline_message_id: Required if inline_message_id is not specified. Identifier of the inline message.
        :type inline_message_id: :obj:`str`

        :param parse_mode: New caption of the message, 0-1024 characters after entities parsing
        :type parse_mode: :obj:`str`

        :param caption_entities: A JSON-serialized array of objects that describe how the caption should be parsed.
        :type caption_entities: :obj:`list` of :obj:`types.MessageEntity`

        :param reply_markup: A JSON-serialized object for an inline keyboard.
        :type reply_markup: :obj:`InlineKeyboardMarkup`

        :return: On success, if edited message is sent by the bot, the edited Message is returned, otherwise True is returned.
        :rtype: :obj:`types.Message` | :obj:`bool`
        """
        parse_mode = self.parse_mode if (parse_mode is None) else parse_mode

        result = apihelper.edit_message_caption(self.token, caption, chat_id, message_id, inline_message_id,
                                                parse_mode, caption_entities, reply_markup)
        if type(result) == bool:
            return result
        return types.Message.de_json(result)

    def reply_to(self, message: types.Message, text: str, **kwargs) -> types.Message:
        """
        Convenience function for `send_message(message.chat.id, text, reply_to_message_id=message.message_id, **kwargs)`
        
        :param message: Instance of :class:`telebot.types.Message`
        :type message: :obj:`types.Message`

        :param text: Text of the message.
        :type text: :obj:`str`

        :param kwargs: Additional keyword arguments which are passed to :meth:`telebot.TeleBot.send_message`

        :return: On success, the sent Message is returned.
        :rtype: :class:`telebot.types.Message`
        """
        return self.send_message(message.chat.id, text, reply_to_message_id=message.message_id, **kwargs)

    def answer_inline_query(
            self, inline_query_id: str, 
            results: List[Any], 
            cache_time: Optional[int]=None, 
            is_personal: Optional[bool]=None, 
            next_offset: Optional[str]=None,
            switch_pm_text: Optional[str]=None, 
            switch_pm_parameter: Optional[str]=None) -> bool:
        """
        Use this method to send answers to an inline query. On success, True is returned.
        No more than 50 results per query are allowed.

        Telegram documentation: https://core.telegram.org/bots/api#answerinlinequery

        :param inline_query_id: Unique identifier for the answered query
        :type inline_query_id: :obj:`str`

        :param results: Array of results for the inline query
        :type results: :obj:`list` of :obj:`types.InlineQueryResult`

        :param cache_time: The maximum amount of time in seconds that the result of the inline query
            may be cached on the server.
        :type cache_time: :obj:`int`

        :param is_personal: Pass True, if results may be cached on the server side only for
            the user that sent the query.
        :type is_personal: :obj:`bool`

        :param next_offset: Pass the offset that a client should send in the next query with the same text
            to receive more results.
        :type next_offset: :obj:`str`

        :param switch_pm_parameter: Deep-linking parameter for the /start message sent to the bot when user presses the switch button. 1-64 characters,
            only A-Z, a-z, 0-9, _ and - are allowed.
            Example: An inline bot that sends YouTube videos can ask the user to connect the bot to their YouTube account to adapt search results accordingly.
            To do this, it displays a 'Connect your YouTube account' button above the results, or even before showing any. The user presses the button, switches to a
            private chat with the bot and, in doing so, passes a start parameter that instructs the bot to return an OAuth link. Once done, the bot can offer a switch_inline
            button so that the user can easily return to the chat where they wanted to use the bot's inline capabilities.
        :type switch_pm_parameter: :obj:`str`

        :param switch_pm_text: Parameter for the start message sent to the bot when user presses the switch button
        :type switch_pm_text: :obj:`str`

        :return: On success, True is returned.
        :rtype: :obj:`bool`
        """
        return apihelper.answer_inline_query(self.token, inline_query_id, results, cache_time, is_personal, next_offset,
                                             switch_pm_text, switch_pm_parameter)

    def answer_callback_query(
            self, callback_query_id: int, 
            text: Optional[str]=None, show_alert: Optional[bool]=None, 
            url: Optional[str]=None, cache_time: Optional[int]=None) -> bool:
        """
        Use this method to send answers to callback queries sent from inline keyboards. The answer will be displayed to
        the user as a notification at the top of the chat screen or as an alert.

        Telegram documentation: https://core.telegram.org/bots/api#answercallbackquery

        :param callback_query_id: Unique identifier for the query to be answered
        :type callback_query_id: :obj:`int`

        :param text: Text of the notification. If not specified, nothing will be shown to the user, 0-200 characters
        :type text: :obj:`str`

        :param show_alert: If True, an alert will be shown by the client instead of a notification at the top of the chat screen. Defaults to false.
        :type show_alert: :obj:`bool`

        :param url: URL that will be opened by the user's client. If you have created a Game and accepted the conditions via @BotFather, specify the URL that opens your
            game - note that this will only work if the query comes from a callback_game button.
        :type url: :obj:`str`

        :param cache_time: The maximum amount of time in seconds that the result of the callback query may be cached client-side. Telegram apps will support caching
            starting in version 3.14. Defaults to 0.

        :return: On success, True is returned.
        :rtype: :obj:`bool`
        """
        return apihelper.answer_callback_query(self.token, callback_query_id, text, show_alert, url, cache_time)

    def set_sticker_set_thumb(
            self, name: str, user_id: int, thumb: Union[Any, str]=None):
        """
        Use this method to set the thumbnail of a sticker set. 
        Animated thumbnails can be set for animated sticker sets only. Returns True on success.

        Telegram documentation: https://core.telegram.org/bots/api#setstickersetthumb

        :param name: Sticker set name
        :type name: :obj:`str`

        :param user_id: User identifier
        :type user_id: :obj:`int`

        :param thumb:
        :type thumb: :obj:`filelike object`

        :return: On success, True is returned.
        :rtype: :obj:`bool`
        """
        return apihelper.set_sticker_set_thumb(self.token, name, user_id, thumb)

    def get_sticker_set(self, name: str) -> types.StickerSet:
        """
        Use this method to get a sticker set. On success, a StickerSet object is returned.
        
        Telegram documentation: https://core.telegram.org/bots/api#getstickerset

        :param name: Sticker set name
        :type name: :obj:`str`

        :return: On success, a StickerSet object is returned.
        :rtype: :class:`telebot.types.StickerSet`
        """
        result = apihelper.get_sticker_set(self.token, name)
        return types.StickerSet.de_json(result)

    def get_custom_emoji_stickers(self, custom_emoji_ids: List[str]) -> List[types.Sticker]:
        """
        Use this method to get information about custom emoji stickers by their identifiers.
        Returns an Array of Sticker objects.

        :param custom_emoji_ids: List of custom emoji identifiers. At most 200 custom emoji identifiers can be specified.
        :type custom_emoji_ids: :obj:`list` of :obj:`str`

        :return: Returns an Array of Sticker objects.
        :rtype: :obj:`list` of :class:`telebot.types.Sticker`
        """
        result = apihelper.get_custom_emoji_stickers(self.token, custom_emoji_ids)
        return [types.Sticker.de_json(sticker) for sticker in result]

    def upload_sticker_file(self, user_id: int, png_sticker: Union[Any, str]) -> types.File:
        """
        Use this method to upload a .png file with a sticker for later use in createNewStickerSet and addStickerToSet
        methods (can be used multiple times). Returns the uploaded File on success.
        
        Telegram documentation: https://core.telegram.org/bots/api#uploadstickerfile

        :param user_id: User identifier of sticker set owner
        :type user_id: :obj:`int`

        :param png_sticker: PNG image with the sticker, must be up to 512 kilobytes in size, dimensions must not exceed 512px,
            and either width or height must be exactly 512px.
        :type png_sticker: :obj:`filelike object`

        :return: On success, the sent file is returned.
        :rtype: :class:`telebot.types.File`
        """
        result = apihelper.upload_sticker_file(self.token, user_id, png_sticker)
        return types.File.de_json(result)

    def create_new_sticker_set(
            self, user_id: int, name: str, title: str, 
            emojis: str, 
            png_sticker: Union[Any, str]=None, 
            tgs_sticker: Union[Any, str]=None, 
            webm_sticker: Union[Any, str]=None,
            contains_masks: Optional[bool]=None,
            sticker_type: Optional[str]=None,
            mask_position: Optional[types.MaskPosition]=None) -> bool:
        """
        Use this method to create new sticker set owned by a user. 
        The bot will be able to edit the created sticker set.
        Returns True on success.

        Telegram documentation: https://core.telegram.org/bots/api#createnewstickerset

        :param user_id: User identifier of created sticker set owner
        :type user_id: :obj:`int`

        :param name: Short name of sticker set, to be used in t.me/addstickers/ URLs (e.g., animals). Can contain only English letters,
            digits and underscores. Must begin with a letter, can't contain consecutive underscores and must end in "_by_<bot_username>".
            <bot_username> is case insensitive. 1-64 characters.
        :type name: :obj:`str`

        :param title: Sticker set title, 1-64 characters
        :type title: :obj:`str`

        :param emojis: One or more emoji corresponding to the sticker
        :type emojis: :obj:`str`

        :param png_sticker: PNG image with the sticker, must be up to 512 kilobytes in size, dimensions must not exceed 512px, and either width
            or height must be exactly 512px. Pass a file_id as a String to send a file that already exists on the Telegram servers, pass an HTTP URL
            as a String for Telegram to get a file from the Internet, or upload a new one using multipart/form-data.
        :type png_sticker: :obj:`str`

        :param tgs_sticker: TGS animation with the sticker, uploaded using multipart/form-data.
        :type tgs_sticker: :obj:`str`

        :param webm_sticker: WebM animation with the sticker, uploaded using multipart/form-data.
        :type webm_sticker: :obj:`str`

        :param contains_masks: Pass True, if a set of mask stickers should be created. Deprecated since Bot API 6.2,
            use sticker_type instead.
        :type contains_masks: :obj:`bool`

        :param sticker_type: Optional, Type of stickers in the set, pass “regular” or “mask”. Custom emoji sticker sets can't be created
            via the Bot API at the moment. By default, a regular sticker set is created.
        :type sticker_type: :obj:`str`

        :param mask_position: A JSON-serialized object for position where the mask should be placed on faces
        :type mask_position: :class:`telebot.types.MaskPosition`

        :return: On success, True is returned.
        :rtype: :obj:`bool`
        """
        if contains_masks is not None:
            logger.warning('The parameter "contains_masks" is deprecated, use "sticker_type" instead')
            if sticker_type is None:
               sticker_type = 'mask' if contains_masks else 'regular'

        return apihelper.create_new_sticker_set(
            self.token, user_id, name, title, emojis, png_sticker, tgs_sticker, 
            mask_position, webm_sticker, sticker_type)

    def add_sticker_to_set(
            self, user_id: int, name: str, emojis: str,
            png_sticker: Optional[Union[Any, str]]=None, 
            tgs_sticker: Optional[Union[Any, str]]=None,  
            webm_sticker: Optional[Union[Any, str]]=None,
            mask_position: Optional[types.MaskPosition]=None) -> bool:
        """
        Use this method to add a new sticker to a set created by the bot. 
        It's required to pass `png_sticker` or `tgs_sticker`.
        Returns True on success.

        Telegram documentation: https://core.telegram.org/bots/api#addstickertoset

        :param user_id: User identifier of created sticker set owner
        :type user_id: :obj:`int`

        :param name: Sticker set name
        :type name: :obj:`str`

        :param emojis: One or more emoji corresponding to the sticker
        :type emojis: :obj:`str`

        :param png_sticker: PNG image with the sticker, must be up to 512 kilobytes in size, dimensions must not exceed 512px, and either
            width or height must be exactly 512px. Pass a file_id as a String to send a file that already exists on the Telegram servers,
            pass an HTTP URL as a String for Telegram to get a file from the Internet, or upload a new one using multipart/form-data.
        :type png_sticker: :obj:`str` or :obj:`filelike object`

        :param tgs_sticker: TGS animation with the sticker, uploaded using multipart/form-data.
        :type tgs_sticker: :obj:`str` or :obj:`filelike object`

        :param webm_sticker: WebM animation with the sticker, uploaded using multipart/form-data.
        :type webm_sticker: :obj:`str` or :obj:`filelike object`

        :param mask_position: A JSON-serialized object for position where the mask should be placed on faces
        :type mask_position: :class:`telebot.types.MaskPosition`

        :return: On success, True is returned.
        :rtype: :obj:`bool`
        """
        return apihelper.add_sticker_to_set(
            self.token, user_id, name, emojis, png_sticker, tgs_sticker, mask_position, webm_sticker)

    def set_sticker_position_in_set(self, sticker: str, position: int) -> bool:
        """
        Use this method to move a sticker in a set created by the bot to a specific position . Returns True on success.
        
        Telegram documentation: https://core.telegram.org/bots/api#setstickerpositioninset

        :param sticker: File identifier of the sticker
        :type sticker: :obj:`str`

        :param position: New sticker position in the set, zero-based
        :type position: :obj:`int`

        :return: On success, True is returned.
        :rtype: :obj:`bool`
        """
        return apihelper.set_sticker_position_in_set(self.token, sticker, position)

    def delete_sticker_from_set(self, sticker: str) -> bool:
        """
        Use this method to delete a sticker from a set created by the bot. Returns True on success.
       
        Telegram documentation: https://core.telegram.org/bots/api#deletestickerfromset

        :param sticker: File identifier of the sticker
        :return: On success, True is returned.
        :rtype: :obj:`bool`
        """
        return apihelper.delete_sticker_from_set(self.token, sticker)

    def answer_web_app_query(self, web_app_query_id: str, result: types.InlineQueryResultBase) -> types.SentWebAppMessage:
        """
        Use this method to set the result of an interaction with a Web App and
        send a corresponding message on behalf of the user to the chat from which
        the query originated. 
        On success, a SentWebAppMessage object is returned.

        Telegram Documentation: https://core.telegram.org/bots/api#answerwebappquery

        :param web_app_query_id: Unique identifier for the query to be answered
        :type web_app_query_id: :obj:`str`

        :param result: A JSON-serialized object describing the message to be sent
        :type result: :class:`telebot.types.InlineQueryResultBase`

        :return: On success, a SentWebAppMessage object is returned.
        :rtype: :class:`telebot.types.SentWebAppMessage`
        """
        return apihelper.answer_web_app_query(self.token, web_app_query_id, result)

    def register_for_reply(self, message: types.Message, callback: Callable, *args, **kwargs) -> None:
        """
        Registers a callback function to be notified when a reply to `message` arrives.

        Warning: In case `callback` as lambda function, saving reply handlers will not work.

        :param message: The message for which we are awaiting a reply.
        :type message: :class:`telebot.types.Message`

        :param callback: The callback function to be called when a reply arrives. Must accept one `message`
            parameter, which will contain the replied message.
        :type callback: :obj:`Callable[[telebot.types.Message], None]`

        :param args: Optional arguments for the callback function.
        :param kwargs: Optional keyword arguments for the callback function.
        
        :return: None
        """
        message_id = message.message_id
        self.register_for_reply_by_message_id(message_id, callback, *args, **kwargs)

    def register_for_reply_by_message_id(
            self, message_id: int, callback: Callable, *args, **kwargs) -> None:
        """
        Registers a callback function to be notified when a reply to `message` arrives.

        Warning: In case `callback` as lambda function, saving reply handlers will not work.

        :param message_id: The id of the message for which we are awaiting a reply.
        :type message_id: :obj:`int`

        :param callback: The callback function to be called when a reply arrives. Must accept one `message`
            parameter, which will contain the replied message.
        :type callback: :obj:`Callable[[telebot.types.Message], None]`

        :param args: Optional arguments for the callback function.
        :param kwargs: Optional keyword arguments for the callback function.

        :return: None
        """
        self.reply_backend.register_handler(message_id, Handler(callback, *args, **kwargs))

    def _notify_reply_handlers(self, new_messages) -> None:
        """
        Notify handlers of the answers

        :param new_messages:
        :return:
        """
        for message in new_messages:
            if hasattr(message, "reply_to_message") and message.reply_to_message is not None:
                handlers = self.reply_backend.get_handlers(message.reply_to_message.message_id)
                if handlers:
                    for handler in handlers:
                        self._exec_task(handler["callback"], message, *handler["args"], **handler["kwargs"])

    def register_next_step_handler(self, message: types.Message, callback: Callable, *args, **kwargs) -> None:
        """
        Registers a callback function to be notified when new message arrives after `message`.

        Warning: In case `callback` as lambda function, saving next step handlers will not work.

        :param message: The message for which we want to handle new message in the same chat.
        :type message: :class:`telebot.types.Message`

        :param callback: The callback function which next new message arrives.
        :type callback: :obj:`Callable[[telebot.types.Message], None]`

        :param args: Args to pass in callback func

        :param kwargs: Args to pass in callback func

        :return: None
        """
        chat_id = message.chat.id
        self.register_next_step_handler_by_chat_id(chat_id, callback, *args, **kwargs)

    def setup_middleware(self, middleware: BaseMiddleware):
        """
        Registers class-based middleware.

        :param middleware: Subclass of :class:`telebot.handler_backends.BaseMiddleware`
        :type middleware: :class:`telebot.handler_backends.BaseMiddleware`
        :return: None
        """
        if not self.use_class_middlewares:
            logger.error('Class-based middlewares are not enabled. Pass use_class_middlewares=True to enable it.')
            return

        if not hasattr(middleware, 'update_types'):
            logger.error('Middleware has no update_types parameter. Please add list of updates to handle.')
            return

        if not hasattr(middleware, 'update_sensitive'):
            logger.warning('Middleware has no update_sensitive parameter. Parameter was set to False.')
            middleware.update_sensitive = False

        self.middlewares.append(middleware)

    def set_state(self, user_id: int, state: Union[int, str, State], chat_id: Optional[int]=None) -> None:
        """
        Sets a new state of a user.

        .. note::

            You should set both user id and chat id in order to set state for a user in a chat.
            Otherwise, if you only set user_id, chat_id will equal to user_id, this means that
            state will be set for the user in his private chat with a bot.

        :param user_id: User's identifier
        :type user_id: :obj:`int`

        :param state: new state. can be string, integer, or :class:`telebot.types.State`
        :type state: :obj:`int` or :obj:`str` or :class:`telebot.types.State`

        :param chat_id: Chat's identifier
        :type chat_id: :obj:`int`

        :return: None
        """
        if chat_id is None:
            chat_id = user_id
        self.current_states.set_state(chat_id, user_id, state)

    def reset_data(self, user_id: int, chat_id: Optional[int]=None):
        """
        Reset data for a user in chat.

        :param user_id: User's identifier
        :type user_id: :obj:`int`

        :param chat_id: Chat's identifier
        :type chat_id: :obj:`int`

        :return: None
        """
        if chat_id is None:
            chat_id = user_id
        self.current_states.reset_data(chat_id, user_id)

    def delete_state(self, user_id: int, chat_id: Optional[int]=None) -> None:
        """
        Delete the current state of a user.

        :param user_id: User's identifier
        :type user_id: :obj:`int`
        
        :param chat_id: Chat's identifier
        :type chat_id: :obj:`int`

        :return: None
        """
        if chat_id is None:
            chat_id = user_id
        self.current_states.delete_state(chat_id, user_id)

    def retrieve_data(self, user_id: int, chat_id: Optional[int]=None) -> Optional[Any]:
        """
        Returns context manager with data for a user in chat.

        :param user_id: User identifier
        :type user_id: int

        :param chat_id: Chat's unique identifier, defaults to user_id
        :type chat_id: int, optional

        :return: Context manager with data for a user in chat
        :rtype: Optional[Any]
        """
        if chat_id is None:
            chat_id = user_id
        return self.current_states.get_interactive_data(chat_id, user_id)

    def get_state(self, user_id: int, chat_id: Optional[int]=None) -> Optional[Union[int, str, State]]:
        """
        Gets current state of a user.
        Not recommended to use this method. But it is ok for debugging.

        :param user_id: User's identifier
        :type user_id: :obj:`int`

        :param chat_id: Chat's identifier
        :type chat_id: :obj:`int`

        :return: state of a user
        :rtype: :obj:`int` or :obj:`str` or :class:`telebot.types.State`
        """
        if chat_id is None:
            chat_id = user_id
        return self.current_states.get_state(chat_id, user_id)

    def add_data(self, user_id: int, chat_id: Optional[int]=None, **kwargs):
        """
        Add data to states.

        :param user_id: User's identifier
        :type user_id: :obj:`int`

        :param chat_id: Chat's identifier
        :type chat_id: :obj:`int`

        :param kwargs: Data to add
        :return: None
        """
        if chat_id is None:
            chat_id = user_id
        for key, value in kwargs.items():
            self.current_states.set_data(chat_id, user_id, key, value)

    def register_next_step_handler_by_chat_id(
            self, chat_id: Union[int, str], callback: Callable, *args, **kwargs) -> None:
        """
        Registers a callback function to be notified when new message arrives after `message`.

        Warning: In case `callback` as lambda function, saving next step handlers will not work.

        :param chat_id: The chat for which we want to handle new message.
        :type chat_id: :obj:`int` or :obj:`str`

        :param callback: The callback function which next new message arrives.
        :type callback: :obj:`Callable[[telebot.types.Message], None]`

        :param args: Args to pass in callback func
        
        :param kwargs: Args to pass in callback func

        :return: None
        """
        self.next_step_backend.register_handler(chat_id, Handler(callback, *args, **kwargs))

    def clear_step_handler(self, message: types.Message) -> None:
        """
        Clears all callback functions registered by register_next_step_handler().

        :param message: The message for which we want to handle new message after that in same chat.
        :type message: :class:`telebot.types.Message`

        :return: None
        """
        chat_id = message.chat.id
        self.clear_step_handler_by_chat_id(chat_id)

    def clear_step_handler_by_chat_id(self, chat_id: Union[int, str]) -> None:
        """
        Clears all callback functions registered by register_next_step_handler().

        :param chat_id: The chat for which we want to clear next step handlers
        :type chat_id: :obj:`int` or :obj:`str`

        :return: None
        """
        self.next_step_backend.clear_handlers(chat_id)

    def clear_reply_handlers(self, message: types.Message) -> None:
        """
        Clears all callback functions registered by register_for_reply() and register_for_reply_by_message_id().

        :param message: The message for which we want to clear reply handlers
        :type message: :class:`telebot.types.Message`

        :return: None
        """
        message_id = message.message_id
        self.clear_reply_handlers_by_message_id(message_id)

    def clear_reply_handlers_by_message_id(self, message_id: int) -> None:
        """
        Clears all callback functions registered by register_for_reply() and register_for_reply_by_message_id().

        :param message_id: The message id for which we want to clear reply handlers
        :type message_id: :obj:`int`

        :return: None
        """
        self.reply_backend.clear_handlers(message_id)

    def _notify_next_handlers(self, new_messages):
        """
        Description: TBD

        :param new_messages:
        :return:
        """
        for i, message in enumerate(new_messages):
            need_pop = False
            handlers = self.next_step_backend.get_handlers(message.chat.id)
            if handlers:
                for handler in handlers:
                    need_pop = True
                    self._exec_task(handler["callback"], message, *handler["args"], **handler["kwargs"])
            if need_pop:
                # removing message that was detected with next_step_handler
                new_messages.pop(i)

    @staticmethod
    def _build_handler_dict(handler, pass_bot=False, **filters):
        """
        Builds a dictionary for a handler

        :param handler:
        :param filters:
        :return:
        """
        return {
            'function': handler,
            'pass_bot': pass_bot,
            'filters': {ftype: fvalue for ftype, fvalue in filters.items() if fvalue is not None}
            # Remove None values, they are skipped in _test_filter anyway
            #'filters': filters
        }

    def middleware_handler(self, update_types: Optional[List[str]]=None):
        """
        Function-based middleware handler decorator.

        This decorator can be used to decorate functions that must be handled as middlewares before entering any other
        message handlers
        But, be careful and check type of the update inside the handler if more than one update_type is given

        Example:

        .. code-block:: python3
            :caption: Usage of middleware_handler

            bot = TeleBot('TOKEN')

            # Print post message text before entering to any post_channel handlers
            @bot.middleware_handler(update_types=['channel_post', 'edited_channel_post'])
            def print_channel_post_text(bot_instance, channel_post):
                print(channel_post.text)

            # Print update id before entering to any handlers
            @bot.middleware_handler()
            def print_channel_post_text(bot_instance, update):
                print(update.update_id)

        :param update_types: Optional list of update types that can be passed into the middleware handler.
        :type update_types: :obj:`list` of :obj:`str`

        :return: function
        """
        def decorator(handler):
            self.add_middleware_handler(handler, update_types)
            return handler

        return decorator

    def add_middleware_handler(self, handler, update_types=None):
        """
        Add middleware handler.

        :meta private:

        :param handler:
        :param update_types:
        :return:
        """
        if not apihelper.ENABLE_MIDDLEWARE:
            raise RuntimeError("Middleware is not enabled. Use apihelper.ENABLE_MIDDLEWARE before initialising TeleBot.")

        if self.use_class_middlewares:
            logger.error("middleware_handler/register_middleware_handler/add_middleware_handler cannot be used with use_class_middlewares=True. Skipped.")
            return

        added = False
        if update_types and self.typed_middleware_handlers:
            for update_type in update_types:
                if update_type in self.typed_middleware_handlers:
                    added = True
                    self.typed_middleware_handlers[update_type].append(handler)
        if not added:
            self.default_middleware_handlers.append(handler)

    # function register_middleware_handler
    def register_middleware_handler(self, callback, update_types=None):
        """
        Adds function-based middleware handler.

        This function will register your decorator function. Function-based middlewares are executed before handlers.
        But, be careful and check type of the update inside the handler if more than one update_type is given

        Example:

        bot = TeleBot('TOKEN')

        bot.register_middleware_handler(print_channel_post_text, update_types=['channel_post', 'edited_channel_post'])
 
        :param callback: Function that will be used as a middleware handler.
        :type callback: :obj:`function`

        :param update_types: Optional list of update types that can be passed into the middleware handler.
        :type update_types: :obj:`list` of :obj:`str`

        :return: None
        """
        self.add_middleware_handler(callback, update_types)

    @staticmethod
    def check_commands_input(commands, method_name):
        """
        :meta private:
        """
        if not isinstance(commands, list) or not all(isinstance(item, str) for item in commands):
            logger.error(f"{method_name}: Commands filter should be list of strings (commands), unknown type supplied to the 'commands' filter list. Not able to use the supplied type.")

    @staticmethod
    def check_regexp_input(regexp, method_name):
        """
        :meta private:
        """
        if not isinstance(regexp, str):
            logger.error(f"{method_name}: Regexp filter should be string. Not able to use the supplied type.")

    def message_handler(self, commands: Optional[List[str]]=None, regexp: Optional[str]=None, func: Optional[Callable]=None,
                    content_types: Optional[List[str]]=None, chat_types: Optional[List[str]]=None, **kwargs):
        """
        Handles New incoming message of any kind - text, photo, sticker, etc.
        As a parameter to the decorator function, it passes :class:`telebot.types.Message` object.
        All message handlers are tested in the order they were added.

        Example:

        .. code-block:: python3
            :caption: Usage of message_handler

            bot = TeleBot('TOKEN')

            # Handles all messages which text matches regexp.
            @bot.message_handler(regexp='someregexp')
            def command_help(message):
                bot.send_message(message.chat.id, 'Did someone call for help?')

            # Handles messages in private chat
            @bot.message_handler(chat_types=['private']) # You can add more chat types
            def command_help(message):
                bot.send_message(message.chat.id, 'Private chat detected, sir!')

            # Handle all sent documents of type 'text/plain'.
            @bot.message_handler(func=lambda message: message.document.mime_type == 'text/plain',
                content_types=['document'])
            def command_handle_document(message):
                bot.send_message(message.chat.id, 'Document received, sir!')

            # Handle all other messages.
            @bot.message_handler(func=lambda message: True, content_types=['audio', 'photo', 'voice', 'video', 'document',
                'text', 'location', 'contact', 'sticker'])
            def default_command(message):
                bot.send_message(message.chat.id, "This is the default command handler.")

        :param commands: Optional list of strings (commands to handle).
        :type commands: :obj:`list` of :obj:`str`

        :param regexp: Optional regular expression.
        :type regexp: :obj:`str`

        :param func: Optional lambda function. The lambda receives the message to test as the first parameter.
            It must return True if the command should handle the message.
        :type func: :obj:`lambda`

        :param content_types: Supported message content types. Must be a list. Defaults to ['text'].
        :type content_types: :obj:`list` of :obj:`str`

        :param chat_types: list of chat types
        :type chat_types: :obj:`list` of :obj:`str`

        :param kwargs: Optional keyword arguments(custom filters)

        :return: decorated function
        """
        if content_types is None:
            content_types = ["text"]

        method_name = "message_handler"

        if commands is not None:
            self.check_commands_input(commands, method_name)
            if isinstance(commands, str):
                commands = [commands]

        if regexp is not None:
            self.check_regexp_input(regexp, method_name)

        if isinstance(content_types, str):
            logger.warning("message_handler: 'content_types' filter should be List of strings (content types), not string.")
            content_types = [content_types]

        def decorator(handler):
            handler_dict = self._build_handler_dict(handler,
                                                    chat_types=chat_types,
                                                    content_types=content_types,
                                                    commands=commands,
                                                    regexp=regexp,
                                                    func=func,
                                                    **kwargs)
            self.add_message_handler(handler_dict)
            return handler

        return decorator

    def add_message_handler(self, handler_dict):
        """
        Adds a message handler
        Note that you should use register_message_handler to add message_handler to the bot.

        :meta private:

        :param handler_dict:
        :return:
        """
        self.message_handlers.append(handler_dict)

    def register_message_handler(self, callback: Callable, content_types: Optional[List[str]]=None, commands: Optional[List[str]]=None,
            regexp: Optional[str]=None, func: Optional[Callable]=None, chat_types: Optional[List[str]]=None, pass_bot: Optional[bool]=False, **kwargs):
        """
        Registers message handler.

        :param callback: function to be called
        :type callback: :obj:`function`

        :param content_types: Supported message content types. Must be a list. Defaults to ['text'].
        :type content_types: :obj:`list` of :obj:`str`

        :param commands: list of commands
        :type commands: :obj:`list` of :obj:`str`

        :param regexp:
        :type regexp: :obj:`str`

        :param func: Function executed as a filter
        :type func: :obj:`function`

        :param chat_types: List of chat types
        :type chat_types: :obj:`list` of :obj:`str`

        :param pass_bot: True if you need to pass TeleBot instance to handler(useful for separating handlers into different files)
        :type pass_bot: :obj:`bool`

        :param kwargs: Optional keyword arguments(custom filters)

        :return: None
        """
        method_name = "register_message_handler"

        if commands is not None:
            self.check_commands_input(commands, method_name)
            if isinstance(commands, str):
                commands = [commands]

        if regexp is not None:
            self.check_regexp_input(regexp, method_name)

        if isinstance(content_types, str):
            logger.warning("register_message_handler: 'content_types' filter should be List of strings (content types), not string.")
            content_types = [content_types]

        

        handler_dict = self._build_handler_dict(callback,
                                                chat_types=chat_types,
                                                content_types=content_types,
                                                commands=commands,
                                                regexp=regexp,
                                                func=func,
                                                pass_bot=pass_bot,
                                                **kwargs)
        self.add_message_handler(handler_dict)

    def edited_message_handler(self, commands=None, regexp=None, func=None, content_types=None, chat_types=None, **kwargs):
        """
        Handles new version of a message that is known to the bot and was edited.
        As a parameter to the decorator function, it passes :class:`telebot.types.Message` object.

        :param commands: Optional list of strings (commands to handle).
        :type commands: :obj:`list` of :obj:`str`

        :param regexp: Optional regular expression.
        :type regexp: :obj:`str`

        :param func: Function executed as a filter
        :type func: :obj:`function`

        :param content_types: Supported message content types. Must be a list. Defaults to ['text'].
        :type content_types: :obj:`list` of :obj:`str`

        :param chat_types: list of chat types
        :type chat_types: :obj:`list` of :obj:`str`

        :param kwargs: Optional keyword arguments(custom filters)

        :return: None
        """
        if content_types is None:
            content_types = ["text"]

        method_name = "edited_message_handler"

        if commands is not None:
            self.check_commands_input(commands, method_name)
            if isinstance(commands, str):
                commands = [commands]

        if regexp is not None:
            self.check_regexp_input(regexp, method_name)

        if isinstance(content_types, str):
            logger.warning("edited_message_handler: 'content_types' filter should be List of strings (content types), not string.")
            content_types = [content_types]

        def decorator(handler):
            handler_dict = self._build_handler_dict(handler,
                                                    chat_types=chat_types,
                                                    content_types=content_types,
                                                    commands=commands,
                                                    regexp=regexp,
                                                    func=func,
                                                    **kwargs)
            self.add_edited_message_handler(handler_dict)
            return handler

        return decorator

    def add_edited_message_handler(self, handler_dict):
        """
        Adds the edit message handler
        Note that you should use register_edited_message_handler to add edited_message_handler to the bot.
        
        :meta private:

        :param handler_dict:
        :return:
        """
        self.edited_message_handlers.append(handler_dict)

    def register_edited_message_handler(self, callback: Callable, content_types: Optional[List[str]]=None,
        commands: Optional[List[str]]=None, regexp: Optional[str]=None, func: Optional[Callable]=None,
        chat_types: Optional[List[str]]=None, pass_bot: Optional[bool]=False, **kwargs):
        """
        Registers edited message handler.

        :param callback: function to be called
        :type callback: :obj:`function`

        :param content_types: Supported message content types. Must be a list. Defaults to ['text'].
        :type content_types: :obj:`list` of :obj:`str`

        :param commands: list of commands
        :type commands: :obj:`list` of :obj:`str`

        :param regexp: Regular expression
        :type regexp: :obj:`str`

        :param func: Function executed as a filter
        :type func: :obj:`function`

        :param chat_types: True for private chat
        :type chat_types: :obj:`bool`

        :param pass_bot: True if you need to pass TeleBot instance to handler(useful for separating handlers into different files)
        :type pass_bot: :obj:`bool`

        :param kwargs: Optional keyword arguments(custom filters)

        :return: None
        """
        method_name = "register_edited_message_handler"

        if commands is not None:
            self.check_commands_input(commands, method_name)
            if isinstance(commands, str):
                commands = [commands]

        if regexp is not None:
            self.check_regexp_input(regexp, method_name)

        if isinstance(content_types, str):
            logger.warning("register_edited_message_handler: 'content_types' filter should be List of strings (content types), not string.")
            content_types = [content_types]

        handler_dict = self._build_handler_dict(callback,
                                                chat_types=chat_types,
                                                content_types=content_types,
                                                commands=commands,
                                                regexp=regexp,
                                                func=func,
                                                pass_bot=pass_bot,
                                                **kwargs)
        self.add_edited_message_handler(handler_dict)

    def channel_post_handler(self, commands=None, regexp=None, func=None, content_types=None, **kwargs):
        """
        Handles new incoming channel post of any kind - text, photo, sticker, etc.
        As a parameter to the decorator function, it passes :class:`telebot.types.Message` object.

        :param commands: Optional list of strings (commands to handle).
        :type commands: :obj:`list` of :obj:`str`

        :param regexp: Optional regular expression.
        :type regexp: :obj:`str`

        :param func: Function executed as a filter
        :type func: :obj:`function`

        :param content_types: Supported message content types. Must be a list. Defaults to ['text'].
        :type content_types: :obj:`list` of :obj:`str`

        :param kwargs: Optional keyword arguments(custom filters)

        :return: None
        """
        if content_types is None:
            content_types = ["text"]

        method_name = "channel_post_handler"

        if commands is not None:
            self.check_commands_input(commands, method_name)
            if isinstance(commands, str):
                commands = [commands]

        if regexp is not None:
            self.check_regexp_input(regexp, method_name)

        if isinstance(content_types, str):
            logger.warning("channel_post_handler: 'content_types' filter should be List of strings (content types), not string.")
            content_types = [content_types]

        def decorator(handler):
            handler_dict = self._build_handler_dict(handler,
                                                    content_types=content_types,
                                                    commands=commands,
                                                    regexp=regexp,
                                                    func=func,
                                                    **kwargs)
            self.add_channel_post_handler(handler_dict)
            return handler

        return decorator

    def add_channel_post_handler(self, handler_dict):
        """
        Adds channel post handler
        Note that you should use register_channel_post_handler to add channel_post_handler to the bot.

        :meta private:
        
        :param handler_dict:
        :return:
        """
        self.channel_post_handlers.append(handler_dict)
    
    def register_channel_post_handler(self, callback: Callable, content_types: Optional[List[str]]=None, commands: Optional[List[str]]=None,
            regexp: Optional[str]=None, func: Optional[Callable]=None, pass_bot: Optional[bool]=False, **kwargs):
        """
        Registers channel post message handler.

        :param callback: function to be called
        :type callback: :obj:`function`

        :param content_types: Supported message content types. Must be a list. Defaults to ['text'].
        :type content_types: :obj:`list` of :obj:`str`

        :param commands: list of commands
        :type commands: :obj:`list` of :obj:`str`

        :param regexp: Regular expression
        :type regexp: :obj:`str`

        :param func: Function executed as a filter
        :type func: :obj:`function`

        :param pass_bot: True if you need to pass TeleBot instance to handler(useful for separating handlers into different files)
        :type pass_bot: :obj:`bool`

        :param kwargs: Optional keyword arguments(custom filters)

        :return: None
        """
        method_name = "register_channel_post_handler"

        if commands is not None:
            self.check_commands_input(commands, method_name)
            if isinstance(commands, str):
                commands = [commands]

        if regexp is not None:
            self.check_regexp_input(regexp, method_name)

        if isinstance(content_types, str):
            logger.warning("register_channel_post_handler: 'content_types' filter should be List of strings (content types), not string.")
            content_types = [content_types]

        handler_dict = self._build_handler_dict(callback,
                                                content_types=content_types,
                                                commands=commands,
                                                regexp=regexp,
                                                func=func,
                                                pass_bot=pass_bot,
                                                **kwargs)
        self.add_channel_post_handler(handler_dict)

    def edited_channel_post_handler(self, commands=None, regexp=None, func=None, content_types=None, **kwargs):
        """
        Handles new version of a channel post that is known to the bot and was edited.
        As a parameter to the decorator function, it passes :class:`telebot.types.Message` object.

        :param commands: Optional list of strings (commands to handle).
        :type commands: :obj:`list` of :obj:`str`

        :param regexp: Optional regular expression.
        :type regexp: :obj:`str`

        :param func: Function executed as a filter
        :type func: :obj:`function`

        :param content_types: Supported message content types. Must be a list. Defaults to ['text'].
        :type content_types: :obj:`list` of :obj:`str`

        :param kwargs: Optional keyword arguments(custom filters)

        :return:
        """
        if content_types is None:
            content_types = ["text"]

        method_name = "edited_channel_post_handler"

        if commands is not None:
            self.check_commands_input(commands, method_name)
            if isinstance(commands, str):
                commands = [commands]

        if regexp is not None:
            self.check_regexp_input(regexp, method_name)

        if isinstance(content_types, str):
            logger.warning("edited_channel_post_handler: 'content_types' filter should be List of strings (content types), not string.")
            content_types = [content_types]

        def decorator(handler):
            handler_dict = self._build_handler_dict(handler,
                                                    content_types=content_types,
                                                    commands=commands,
                                                    regexp=regexp,
                                                    func=func,
                                                    **kwargs)
            self.add_edited_channel_post_handler(handler_dict)
            return handler

        return decorator

    def add_edited_channel_post_handler(self, handler_dict):
        """
        Adds the edit channel post handler
        Note that you should use register_edited_channel_post_handler to add edited_channel_post_handler to the bot.

        :meta private:

        :param handler_dict:
        :return:
        """
        self.edited_channel_post_handlers.append(handler_dict)

    def register_edited_channel_post_handler(self, callback: Callable, content_types: Optional[List[str]]=None,
            commands: Optional[List[str]]=None, regexp: Optional[str]=None, func: Optional[Callable]=None, pass_bot: Optional[bool]=False, **kwargs):
        """
        Registers edited channel post message handler.

        :param callback: function to be called
        :type callback: :obj:`function`

        :param content_types: Supported message content types. Must be a list. Defaults to ['text'].
        :type content_types: :obj:`list` of :obj:`str`

        :param commands: list of commands
        :type commands: :obj:`list` of :obj:`str`

        :param regexp: Regular expression
        :type regexp: :obj:`str`

        :param func: Function executed as a filter
        :type func: :obj:`function`

        :param pass_bot: True if you need to pass TeleBot instance to handler(useful for separating handlers into different files)
        :type pass_bot: :obj:`bool`

        :param kwargs: Optional keyword arguments(custom filters)

        :return: decorated function
        """
        method_name = "register_edited_channel_post_handler"

        if commands is not None:
            self.check_commands_input(commands, method_name)
            if isinstance(commands, str):
                commands = [commands]

        if regexp is not None:
            self.check_regexp_input(regexp, method_name)

        if isinstance(content_types, str):
            logger.warning("register_edited_channel_post_handler: 'content_types' filter should be List of strings (content types), not string.")
            content_types = [content_types]

        handler_dict = self._build_handler_dict(callback,
                                                content_types=content_types,
                                                commands=commands,
                                                regexp=regexp,
                                                func=func,
                                                pass_bot=pass_bot,
                                                **kwargs)
        self.add_edited_channel_post_handler(handler_dict)

    def inline_handler(self, func, **kwargs):
        """
        Handles new incoming inline query.
        As a parameter to the decorator function, it passes :class:`telebot.types.InlineQuery` object.

        :param func: Function executed as a filter
        :type func: :obj:`function`

        :param kwargs: Optional keyword arguments(custom filters)

        :return: None
        """
        def decorator(handler):
            handler_dict = self._build_handler_dict(handler, func=func, **kwargs)
            self.add_inline_handler(handler_dict)
            return handler

        return decorator

    def add_inline_handler(self, handler_dict):
        """
        Adds inline call handler
        Note that you should use register_inline_handler to add inline_handler to the bot.

        :meta private:

        :param handler_dict:
        :return:
        """
        self.inline_handlers.append(handler_dict)

    def register_inline_handler(self, callback: Callable, func: Callable, pass_bot: Optional[bool]=False, **kwargs):
        """
        Registers inline handler.

        :param callback: function to be called
        :type callback: :obj:`function`

        :param func: Function executed as a filter
        :type func: :obj:`function`

        :param pass_bot: True if you need to pass TeleBot instance to handler(useful for separating handlers into different files)
        :type pass_bot: :obj:`bool`

        :param kwargs: Optional keyword arguments(custom filters)

        :return: decorated function
        """
        handler_dict = self._build_handler_dict(callback, func=func, pass_bot=pass_bot, **kwargs)
        self.add_inline_handler(handler_dict)

    def chosen_inline_handler(self, func, **kwargs):
        """
        Handles the result of an inline query that was chosen by a user and sent to their chat partner.
        Please see our documentation on the feedback collecting for details on how to enable these updates for your bot.
        As a parameter to the decorator function, it passes :class:`telebot.types.ChosenInlineResult` object.

        :param func: Function executed as a filter
        :type func: :obj:`function`
        
        :param kwargs: Optional keyword arguments(custom filters)

        :return: None
        """
        def decorator(handler):
            handler_dict = self._build_handler_dict(handler, func=func, **kwargs)
            self.add_chosen_inline_handler(handler_dict)
            return handler

        return decorator

    def add_chosen_inline_handler(self, handler_dict):
        """
        Description: TBD
        Note that you should use register_chosen_inline_handler to add chosen_inline_handler to the bot.

        :meta private:

        :param handler_dict:
        :return:
        """
        self.chosen_inline_handlers.append(handler_dict)

    def register_chosen_inline_handler(self, callback: Callable, func: Callable, pass_bot: Optional[bool]=False, **kwargs):
        """
        Registers chosen inline handler.

        :param callback: function to be called
        :type callback: :obj:`function`

        :param func: Function executed as a filter
        :type func: :obj:`function`

        :param pass_bot: True if you need to pass TeleBot instance to handler(useful for separating handlers into different files)
        :type pass_bot: :obj:`bool`

        :param kwargs: Optional keyword arguments(custom filters)

        :return: None
        """
        handler_dict = self._build_handler_dict(callback, func=func, pass_bot=pass_bot, **kwargs)
        self.add_chosen_inline_handler(handler_dict)

    def callback_query_handler(self, func, **kwargs):
        """
        Handles new incoming callback query.
        As a parameter to the decorator function, it passes :class:`telebot.types.CallbackQuery` object.

        :param func: Function executed as a filter
        :type func: :obj:`function`

        :param kwargs: Optional keyword arguments(custom filters)
        
        :return: None
        """
        def decorator(handler):
            handler_dict = self._build_handler_dict(handler, func=func, **kwargs)
            self.add_callback_query_handler(handler_dict)
            return handler

        return decorator

    def add_callback_query_handler(self, handler_dict):
        """
        Adds a callback request handler
        Note that you should use register_callback_query_handler to add callback_query_handler to the bot.

        :meta private:

        :param handler_dict:
        :return:
        """
        self.callback_query_handlers.append(handler_dict)

    def register_callback_query_handler(self, callback: Callable, func: Callable, pass_bot: Optional[bool]=False, **kwargs):
        """
        Registers callback query handler.

        :param callback: function to be called
        :type callback: :obj:`function`

        :param func: Function executed as a filter
        :type func: :obj:`function`

        :param pass_bot: True if you need to pass TeleBot instance to handler(useful for separating handlers into different files)
        :type pass_bot: :obj:`bool`

        :param kwargs: Optional keyword arguments(custom filters)

        :return: None
        """
        handler_dict = self._build_handler_dict(callback, func=func, pass_bot=pass_bot, **kwargs)
        self.add_callback_query_handler(handler_dict)

    def shipping_query_handler(self, func, **kwargs):
        """
        Handles new incoming shipping query. Only for invoices with flexible price.
        As a parameter to the decorator function, it passes :class:`telebot.types.ShippingQuery` object.

        :param func: Function executed as a filter
        :type func: :obj:`function`

        :param kwargs: Optional keyword arguments(custom filters)
        
        :return: None
        """
        def decorator(handler):
            handler_dict = self._build_handler_dict(handler, func=func, **kwargs)
            self.add_shipping_query_handler(handler_dict)
            return handler

        return decorator

    def add_shipping_query_handler(self, handler_dict):
        """
        Adds a shipping request handler.
        Note that you should use register_shipping_query_handler to add shipping_query_handler to the bot.

        :meta private:

        :param handler_dict:
        :return:
        """
        self.shipping_query_handlers.append(handler_dict)

    def register_shipping_query_handler(self, callback: Callable, func: Callable, pass_bot: Optional[bool]=False, **kwargs):
        """
        Registers shipping query handler.

        :param callback: function to be called
        :type callback: :obj:`function`

        :param func: Function executed as a filter
        :type func: :obj:`function`

        :param pass_bot: True if you need to pass TeleBot instance to handler(useful for separating handlers into different files)
        :type pass_bot: :obj:`bool`

        :param kwargs: Optional keyword arguments(custom filters)

        :return: None
        """
        handler_dict = self._build_handler_dict(callback, func=func, pass_bot=pass_bot, **kwargs)
        self.add_shipping_query_handler(handler_dict)

    def pre_checkout_query_handler(self, func, **kwargs):
        """
        New incoming pre-checkout query. Contains full information about checkout.
        As a parameter to the decorator function, it passes :class:`telebot.types.PreCheckoutQuery` object.

        :param func: Function executed as a filter
        :type func: :obj:`function`

        :param kwargs: Optional keyword arguments(custom filters)

        :return: None
        """
        def decorator(handler):
            handler_dict = self._build_handler_dict(handler, func=func, **kwargs)
            self.add_pre_checkout_query_handler(handler_dict)
            return handler

        return decorator

    def add_pre_checkout_query_handler(self, handler_dict):
        """
        Adds a pre-checkout request handler
        Note that you should use register_pre_checkout_query_handler to add pre_checkout_query_handler to the bot.

        :meta private:

        :param handler_dict:
        :return:
        """
        self.pre_checkout_query_handlers.append(handler_dict)
    
    def register_pre_checkout_query_handler(self, callback: Callable, func: Callable, pass_bot: Optional[bool]=False, **kwargs):
        """
        Registers pre-checkout request handler.

        :param callback: function to be called
        :type callback: :obj:`function`

        :param func: Function executed as a filter

        :param pass_bot: True if you need to pass TeleBot instance to handler(useful for separating handlers into different files)
        :type pass_bot: :obj:`bool`

        :param kwargs: Optional keyword arguments(custom filters)

        :return: decorated function
        """
        handler_dict = self._build_handler_dict(callback, func=func, pass_bot=pass_bot, **kwargs)
        self.add_pre_checkout_query_handler(handler_dict)

    def poll_handler(self, func, **kwargs):
        """
        Handles new state of a poll. Bots receive only updates about stopped polls and polls, which are sent by the bot
        As a parameter to the decorator function, it passes :class:`telebot.types.Poll` object.

        :param func: Function executed as a filter
        :type func: :obj:`function`

        :param kwargs: Optional keyword arguments(custom filters)
        :return: None
        """
        def decorator(handler):
            handler_dict = self._build_handler_dict(handler, func=func, **kwargs)
            self.add_poll_handler(handler_dict)
            return handler

        return decorator

    def add_poll_handler(self, handler_dict):
        """
        Adds a poll request handler
        Note that you should use register_poll_handler to add poll_handler to the bot.

        :meta private:

        :param handler_dict:
        :return:
        """
        self.poll_handlers.append(handler_dict)

    def register_poll_handler(self, callback: Callable, func: Callable, pass_bot: Optional[bool]=False, **kwargs):
        """
        Registers poll handler.

        :param callback: function to be called
        :type callback: :obj:`function`

        :param func: Function executed as a filter
        :type func: :obj:`function`

        :param pass_bot: True if you need to pass TeleBot instance to handler(useful for separating handlers into different files)
        :type pass_bot: :obj:`bool`

        :param kwargs: Optional keyword arguments(custom filters)

        :return: None
        """
        handler_dict = self._build_handler_dict(callback, func=func, pass_bot=pass_bot, **kwargs)
        self.add_poll_handler(handler_dict)

    def poll_answer_handler(self, func=None, **kwargs):
        """
        Handles change of user's answer in a non-anonymous poll(when user changes the vote).
        Bots receive new votes only in polls that were sent by the bot itself.
        As a parameter to the decorator function, it passes :class:`telebot.types.PollAnswer` object.

        :param func: Function executed as a filter
        :type func: :obj:`function`

        :param kwargs: Optional keyword arguments(custom filters)
        
        :return: None
        """
        def decorator(handler):
            handler_dict = self._build_handler_dict(handler, func=func, **kwargs)
            self.add_poll_answer_handler(handler_dict)
            return handler

        return decorator

    def add_poll_answer_handler(self, handler_dict):
        """
        Adds a poll_answer request handler.
        Note that you should use register_poll_answer_handler to add poll_answer_handler to the bot.

        :meta private:

        :param handler_dict:
        :return:
        """
        self.poll_answer_handlers.append(handler_dict)

    def register_poll_answer_handler(self, callback: Callable, func: Callable, pass_bot: Optional[bool]=False, **kwargs):
        """
        Registers poll answer handler.

        :param callback: function to be called
        :type callback: :obj:`function`

        :param func: Function executed as a filter
        :type func: :obj:`function`

        :param pass_bot: True if you need to pass TeleBot instance to handler(useful for separating handlers into different files)
        :type pass_bot: :obj:`bool`

        :param kwargs: Optional keyword arguments(custom filters)

        :return: None
        """
        handler_dict = self._build_handler_dict(callback, func=func, pass_bot=pass_bot, **kwargs)
        self.add_poll_answer_handler(handler_dict)

    def my_chat_member_handler(self, func=None, **kwargs):
        """
        Handles update in a status of a bot. For private chats,
        this update is received only when the bot is blocked or unblocked by the user.
        As a parameter to the decorator function, it passes :class:`telebot.types.ChatMemberUpdated` object.

        :param func: Function executed as a filter
        :type func: :obj:`function`

        :param kwargs: Optional keyword arguments(custom filters)

        :return: None
        """
        def decorator(handler):
            handler_dict = self._build_handler_dict(handler, func=func, **kwargs)
            self.add_my_chat_member_handler(handler_dict)
            return handler

        return decorator

    def add_my_chat_member_handler(self, handler_dict):
        """
        Adds a my_chat_member handler.
        Note that you should use register_my_chat_member_handler to add my_chat_member_handler to the bot.

        :meta private:

        :param handler_dict:
        :return:
        """
        self.my_chat_member_handlers.append(handler_dict)

    def register_my_chat_member_handler(self, callback: Callable, func: Optional[Callable]=None, pass_bot: Optional[Callable]=False, **kwargs):
        """
        Registers my chat member handler.

        :param callback: function to be called
        :type callback: :obj:`function`

        :param func: Function executed as a filter
        :type func: :obj:`function`

        :param pass_bot: True if you need to pass TeleBot instance to handler(useful for separating handlers into different files)
        :type pass_bot: :obj:`bool`

        :param kwargs: Optional keyword arguments(custom filters)

        :return: None
        """
        handler_dict = self._build_handler_dict(callback, func=func, pass_bot=pass_bot, **kwargs)
        self.add_my_chat_member_handler(handler_dict)

    def chat_member_handler(self, func=None, **kwargs):
        """
        Handles update in a status of a user in a chat.
        The bot must be an administrator in the chat and must explicitly specify “chat_member”
        in the list of allowed_updates to receive these updates.
        As a parameter to the decorator function, it passes :class:`telebot.types.ChatMemberUpdated` object.

        :param func: Function executed as a filter
        :type func: :obj:`function`

        :param kwargs: Optional keyword arguments(custom filters)

        :return: None
        """
        def decorator(handler):
            handler_dict = self._build_handler_dict(handler, func=func, **kwargs)
            self.add_chat_member_handler(handler_dict)
            return handler

        return decorator

    def add_chat_member_handler(self, handler_dict):
        """
        Adds a chat_member handler.
        Note that you should use register_chat_member_handler to add chat_member_handler to the bot.

        :meta private:

        :param handler_dict:
        :return:
        """
        self.chat_member_handlers.append(handler_dict)

    def register_chat_member_handler(self, callback: Callable, func: Optional[Callable]=None, pass_bot: Optional[bool]=False, **kwargs):
        """
        Registers chat member handler.

        :param callback: function to be called
        :type callback: :obj:`function``

        :param func: Function executed as a filter
        :type func: :obj:`function`

        :param pass_bot: True if you need to pass TeleBot instance to handler(useful for separating handlers into different files)
        :type pass_bot: :obj:`bool`

        :param kwargs: Optional keyword arguments(custom filters)

        :return:None
        """
        handler_dict = self._build_handler_dict(callback, func=func, pass_bot=pass_bot, **kwargs)
        self.add_chat_member_handler(handler_dict)

    def chat_join_request_handler(self, func=None, **kwargs):
        """
        Handles a request to join the chat has been sent. The bot must have the can_invite_users
        administrator right in the chat to receive these updates.
        As a parameter to the decorator function, it passes :class:`telebot.types.ChatJoinRequest` object.

        :param func: Function executed as a filter
        :type func: :obj:`function`

        :param kwargs: Optional keyword arguments(custom filters)
        
        :return: None
        """
        def decorator(handler):
            handler_dict = self._build_handler_dict(handler, func=func, **kwargs)
            self.add_chat_join_request_handler(handler_dict)
            return handler

        return decorator

    def add_chat_join_request_handler(self, handler_dict):
        """
        Adds a chat_join_request handler.
        Note that you should use register_chat_join_request_handler to add chat_join_request_handler to the bot.

        :meta private:

        :param handler_dict:
        :return:
        """
        self.chat_join_request_handlers.append(handler_dict)

    def register_chat_join_request_handler(self, callback: Callable, func: Optional[Callable]=None, pass_bot:Optional[bool]=False, **kwargs):
        """
        Registers chat join request handler.

        :param callback: function to be called
        :type callback: :obj:`function`

        :param func: Function executed as a filter
        :type func: :obj:`function`

        :param pass_bot: True if you need to pass TeleBot instance to handler(useful for separating handlers into different files)
        :type pass_bot: :obj:`bool`

        :param kwargs: Optional keyword arguments(custom filters)

        :return: None
        """
        handler_dict = self._build_handler_dict(callback, func=func, pass_bot=pass_bot, **kwargs)
        self.add_chat_join_request_handler(handler_dict)

    def _test_message_handler(self, message_handler, message):
        """
        Test message handler

        :param message_handler:
        :param message:
        :return:
        """
        for message_filter, filter_value in message_handler['filters'].items():
            if filter_value is None:
                continue

            if not self._test_filter(message_filter, filter_value, message):
                return False

        return True

    def add_custom_filter(self, custom_filter: Union[SimpleCustomFilter, AdvancedCustomFilter]):
        """
        Create custom filter.

        .. code-block:: python3
            :caption: Example on checking the text of a message

            class TextMatchFilter(AdvancedCustomFilter):
                key = 'text'

                async def check(self, message, text):
                    return text == message.text

        :param custom_filter: Class with check(message) method.
        :param custom_filter: Custom filter class with key.
        """
        self.custom_filters[custom_filter.key] = custom_filter

    def _test_filter(self, message_filter, filter_value, message):
        """
        Test filters

        :param message_filter: Filter type passed in handler
        :param filter_value: Filter value passed in handler
        :param message: Message to test
        :return: True if filter conforms
        """
        if message_filter == 'content_types':
            return message.content_type in filter_value
        elif message_filter == 'regexp':
            return message.content_type == 'text' and re.search(filter_value, message.text, re.IGNORECASE)
        elif message_filter == 'commands':
            return message.content_type == 'text' and util.extract_command(message.text) in filter_value
        elif message_filter == 'chat_types':
            return message.chat.type in filter_value
        elif message_filter == 'func':
            return filter_value(message)
        elif self.custom_filters and message_filter in self.custom_filters:
            return self._check_filter(message_filter,filter_value,message)
        else:
            return False

    def _check_filter(self, message_filter, filter_value, message):
        filter_check = self.custom_filters.get(message_filter)
        if not filter_check:
            return False
        elif isinstance(filter_check, SimpleCustomFilter):
            return filter_value == filter_check.check(message)
        elif isinstance(filter_check, AdvancedCustomFilter):
            return filter_check.check(message, filter_value)
        else:
            logger.error("Custom filter: wrong type. Should be SimpleCustomFilter or AdvancedCustomFilter.")
            return False

    # middleware check-up method
    def _check_middleware(self, update_type):
        """
        Check middleware

        :param update_type:
        :return:
        """
        middlewares = None
        if self.middlewares: 
            middlewares = [i for i in self.middlewares if update_type in i.update_types]
        return middlewares

    def _run_middlewares_and_handler(self, message, handlers, middlewares, update_type):
        """
        This class is made to run handler and middleware in queue.

        :param handler: handler that should be executed.
        :param middleware: middleware that should be executed.
        :return:
        """
        data = {}
        params =[]
        handler_error = None
        skip_handler = False
        if middlewares:
            for middleware in middlewares:
                if middleware.update_sensitive:
                    if hasattr(middleware, f'pre_process_{update_type}'):
                        result = getattr(middleware, f'pre_process_{update_type}')(message, data)
                    else: 
                        logger.error('Middleware {} does not have pre_process_{} method. pre_process function execution was skipped.'.format(middleware.__class__.__name__, update_type))
                        result = None
                else:
                    result = middleware.pre_process(message, data)
                # We will break this loop if CancelUpdate is returned
                # Also, we will not run other middlewares
                if isinstance(result, CancelUpdate):
                    return
                elif isinstance(result, SkipHandler) and skip_handler is False:
                    skip_handler = True

        try:
            if handlers and not skip_handler:
                for handler in handlers:
                    process_handler = self._test_message_handler(handler, message)
                    if not process_handler: continue
                    else:
                        for i in inspect.signature(handler['function']).parameters:
                            params.append(i)
                        if len(params) == 1:
                            handler['function'](message)
                        else:
                            if "data" in params:
                                if len(params) == 2:
                                    handler['function'](message, data)
                                elif len(params) == 3:
                                    handler['function'](message, data=data, bot=self)
                                else:
                                    logger.error("It is not allowed to pass data and values inside data to the handler. Check your handler: {}".format(handler['function']))
                                    return
                            
                            else:

                                data_copy = data.copy()
                                
                                for key in list(data_copy):
                                    # remove data from data_copy if handler does not accept it
                                    if key not in params:
                                        del data_copy[key]
                                if handler.get('pass_bot'): data_copy["bot"] = self
                                if len(data_copy) > len(params) - 1: # remove the message parameter
                                    logger.error("You are passing more data than the handler needs. Check your handler: {}".format(handler['function']))
                                    return
                                
                                handler["function"](message, **data_copy)
        except Exception as e:
            handler_error = e
            if self.exception_handler:
                self.exception_handler.handle(e)
            else: logging.error(str(e))
        

        if middlewares:
            for middleware in middlewares:
                if middleware.update_sensitive:
                    if hasattr(middleware, f'post_process_{update_type}'):
                        result = getattr(middleware, f'post_process_{update_type}')(message, data, handler_error)
                    else:
                        logger.error("Middleware: {} does not have post_process_{} method. Post process function was not executed.".format(middleware.__class__.__name__, update_type))
                else:
                    result = middleware.post_process(message, data, handler_error)

    def _notify_command_handlers(self, handlers, new_messages, update_type):
        """
        Notifies command handlers.

        :param handlers:
        :param new_messages:
        :return:
        """
        if len(handlers) == 0 and not self.use_class_middlewares:
            return

        for message in new_messages:
            if self.use_class_middlewares:
                middleware = self._check_middleware(update_type)
                self._exec_task(self._run_middlewares_and_handler, message, handlers=handlers, middlewares=middleware, update_type=update_type)
                return
            else:
                for message_handler in handlers:
                    if self._test_message_handler(message_handler, message):
                        self._exec_task(message_handler['function'], message, pass_bot=message_handler['pass_bot'], task_type='handler')
                        break
