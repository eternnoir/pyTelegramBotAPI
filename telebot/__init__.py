# -*- coding: utf-8 -*-
from datetime import datetime

import logging
import re
import sys
import threading
import time
import traceback
from typing import Any, Callable, List, Optional, Union, Dict

# these imports are used to avoid circular import error
import telebot.util
import telebot.types
import telebot.formatting

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
from telebot.handler_backends import (
    HandlerBackend, MemoryHandlerBackend, FileHandlerBackend, BaseMiddleware,
    CancelUpdate, SkipHandler, State, ContinueHandling
)
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

    .. note::

        Install coloredlogs module to specify colorful_logs=True


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
    
    :param disable_web_page_preview: Default value for disable_web_page_preview, defaults to None
    :type disable_web_page_preview: :obj:`bool`, optional

    :param disable_notification: Default value for disable_notification, defaults to None
    :type disable_notification: :obj:`bool`, optional

    :param protect_content: Default value for protect_content, defaults to None
    :type protect_content: :obj:`bool`, optional

    :param allow_sending_without_reply: Default value for allow_sending_without_reply, defaults to None
    :type allow_sending_without_reply: :obj:`bool`, optional
    
    :param colorful_logs: Outputs colorful logs
    :type colorful_logs: :obj:`bool`, optional

    :param validate_token: Validate token, defaults to True;
    :type validate_token: :obj:`bool`, optional

    :raises ImportError: If coloredlogs module is not installed and colorful_logs is True
    :raises ValueError: If token is invalid
    """

    def __init__(
            self, token: str, parse_mode: Optional[str]=None, threaded: Optional[bool]=True,
            skip_pending: Optional[bool]=False, num_threads: Optional[int]=2,
            next_step_backend: Optional[HandlerBackend]=None, reply_backend: Optional[HandlerBackend]=None,
            exception_handler: Optional[ExceptionHandler]=None, last_update_id: Optional[int]=0,
            suppress_middleware_excepions: Optional[bool]=False, state_storage: Optional[StateStorageBase]=StateMemoryStorage(),
            use_class_middlewares: Optional[bool]=False, 
            disable_web_page_preview: Optional[bool]=None,
            disable_notification: Optional[bool]=None,
            protect_content: Optional[bool]=None,
            allow_sending_without_reply: Optional[bool]=None,
            colorful_logs: Optional[bool]=False,
            validate_token: Optional[bool]=True
    ):

        # update-related
        self.token = token
        self.skip_pending = skip_pending # backward compatibility
        self.last_update_id = last_update_id

        # properties
        self.suppress_middleware_excepions = suppress_middleware_excepions
        self.parse_mode = parse_mode
        self.disable_web_page_preview = disable_web_page_preview
        self.disable_notification = disable_notification
        self.protect_content = protect_content
        self.allow_sending_without_reply = allow_sending_without_reply
        self.webhook_listener = None
        self._user = None

        if validate_token:
            util.validate_token(self.token)
        
        self.bot_id: Union[int, None] = util.extract_bot_id(self.token) # subject to change in future, unspecified

        # logs-related
        if colorful_logs:
            try:
                # noinspection PyPackageRequirements
                import coloredlogs
                coloredlogs.install(logger=logger, level=logger.level)
            except ImportError:
                raise ImportError(
                    'Install coloredlogs module to use colorful_logs option.'
                )

        # threading-related
        self.__stop_polling = threading.Event()
        self.exc_info = None

        # states & register_next_step_handler
        self.current_states = state_storage
        self.next_step_backend = next_step_backend
        if not self.next_step_backend:
            self.next_step_backend = MemoryHandlerBackend()

        self.reply_backend = reply_backend
        if not self.reply_backend:
            self.reply_backend = MemoryHandlerBackend()

        # handlers
        self.exception_handler = exception_handler
        self.update_listener = []

        self.message_handlers = []
        self.edited_message_handlers = []
        self.channel_post_handlers = []
        self.edited_channel_post_handlers = []
        self.message_reaction_handlers = []
        self.message_reaction_count_handlers = []
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
        self.chat_boost_handlers = []
        self.removed_chat_boost_handlers = []
        self.business_connection_handlers = []
        self.business_message_handlers = []
        self.edited_business_message_handlers = []
        self.deleted_business_messages_handlers = []
        self.purchased_paid_media_handlers = []

        self.custom_filters = {}
        self.state_handlers = []

        # middlewares
        self.use_class_middlewares = use_class_middlewares
        if apihelper.ENABLE_MIDDLEWARE and not use_class_middlewares:
            self.typed_middleware_handlers = {
                'message': [],
                'edited_message': [],
                'channel_post': [],
                'edited_channel_post': [],
                'message_reaction': [],
                'message_reaction_count': [],
                'inline_query': [],
                'chosen_inline_result': [],
                'callback_query': [],
                'shipping_query': [],
                'pre_checkout_query': [],
                'poll': [],
                'poll_answer': [],
                'my_chat_member': [],
                'chat_member': [],
                'chat_join_request': [],
                'chat_boost': [],
                'removed_chat_boost': [],
                'business_connection': [],
                'business_message': [],
                'edited_business_message': [],
                'deleted_business_messages': [],
            }
            self.default_middleware_handlers = []
        if apihelper.ENABLE_MIDDLEWARE and use_class_middlewares:
            self.typed_middleware_handlers = None
            logger.error(
                'You are using class based middlewares while having ENABLE_MIDDLEWARE set to True. This is not recommended.'
            )
        self.middlewares = [] if use_class_middlewares else None

        # threads
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
        if not self._user:
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

        return apihelper.set_webhook(
            self.token, url = url, certificate = certificate, max_connections = max_connections,
            allowed_updates = allowed_updates, ip_address = ip_address, drop_pending_updates = drop_pending_updates,
            timeout = timeout, secret_token = secret_token)


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
                    secret_token_length: Optional[int]=20):
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
            # noinspection PyTypeChecker
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
        self.webhook_listener = SyncWebhookListener(bot=self, secret_token=secret_token, host=listen, port=port, ssl_context=ssl_context, url_path='/'+url_path)
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
        return apihelper.delete_webhook(
            self.token, drop_pending_updates=drop_pending_updates, timeout=timeout)


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
        return types.WebhookInfo.de_json(
            apihelper.get_webhook_info(self.token, timeout=timeout)
        )


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
        json_updates = apihelper.get_updates(
            self.token, offset=offset, limit=limit, timeout=timeout, allowed_updates=allowed_updates,
            long_polling_timeout=long_polling_timeout)
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
        new_message_reactions = None
        new_message_reaction_counts = None
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
        new_chat_boosts = None
        new_removed_chat_boosts = None
        new_business_connections = None
        new_business_messages = None
        new_edited_business_messages = None
        new_deleted_business_messages = None
        new_purchased_paid_media = None
        
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
            if update.message_reaction:
                if new_message_reactions is None: new_message_reactions = []
                new_message_reactions.append(update.message_reaction)
            if update.message_reaction_count:
                if new_message_reaction_counts is None: new_message_reaction_counts = []
                new_message_reaction_counts.append(update.message_reaction_count)
            if update.chat_boost:
                if new_chat_boosts is None: new_chat_boosts = []
                new_chat_boosts.append(update.chat_boost)
            if update.removed_chat_boost:
                if new_removed_chat_boosts is None: new_removed_chat_boosts = []
                new_removed_chat_boosts.append(update.removed_chat_boost)
            if update.business_connection:
                if new_business_connections is None: new_business_connections = []
                new_business_connections.append(update.business_connection)
            if update.business_message:
                if new_business_messages is None: new_business_messages = []
                new_business_messages.append(update.business_message)
            if update.edited_business_message:
                if new_edited_business_messages is None: new_edited_business_messages = []
                new_edited_business_messages.append(update.edited_business_message)
            if update.deleted_business_messages:
                if new_deleted_business_messages is None: new_deleted_business_messages = []
                new_deleted_business_messages.append(update.deleted_business_messages)
            if update.purchased_paid_media:
                if new_purchased_paid_media is None: new_purchased_paid_media = []
                new_purchased_paid_media.append(update.purchased_paid_media)
                
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
        if new_message_reactions:
            self.process_new_message_reaction(new_message_reactions)
        if new_message_reaction_counts:
            self.process_new_message_reaction_count(new_message_reaction_counts)
        if new_chat_boosts:
            self.process_new_chat_boost(new_chat_boosts)
        if new_removed_chat_boosts:
            self.process_new_removed_chat_boost(new_removed_chat_boosts)
        if new_business_connections:
            self.process_new_business_connection(new_business_connections)
        if new_business_messages:
            self.process_new_business_message(new_business_messages)
        if new_edited_business_messages:
            self.process_new_edited_business_message(new_edited_business_messages)
        if new_deleted_business_messages:
            self.process_new_deleted_business_messages(new_deleted_business_messages)
        if new_purchased_paid_media:
            self.process_new_purchased_paid_media(new_purchased_paid_media)

    def process_new_messages(self, new_messages):
        """
        :meta private:
        """
        self._notify_next_handlers(new_messages)
        self._notify_reply_handlers(new_messages)
        self.__notify_update(new_messages)
        self._notify_command_handlers(self.message_handlers, new_messages, 'message')

    def process_new_edited_messages(self, new_edited_message):
        """
        :meta private:
        """
        self._notify_command_handlers(self.edited_message_handlers, new_edited_message, 'edited_message')

    def process_new_channel_posts(self, new_channel_post):
        """
        :meta private:
        """
        self._notify_command_handlers(self.channel_post_handlers, new_channel_post, 'channel_post')

    def process_new_edited_channel_posts(self, new_edited_channel_post):
        """
        :meta private:
        """
        self._notify_command_handlers(self.edited_channel_post_handlers, new_edited_channel_post, 'edited_channel_post')

    def process_new_message_reaction(self, new_message_reactions):
        """
        :meta private:
        """
        self._notify_command_handlers(self.message_reaction_handlers, new_message_reactions, 'message_reaction')
    
    def process_new_message_reaction_count(self, new_message_reaction_counts):
        """
        :meta private:
        """
        self._notify_command_handlers(self.message_reaction_count_handlers, new_message_reaction_counts, 'message_reaction_count')

    def process_new_inline_query(self, new_inline_queries):
        """
        :meta private:
        """
        self._notify_command_handlers(self.inline_handlers, new_inline_queries, 'inline_query')

    def process_new_chosen_inline_query(self, new_chosen_inline_queries):
        """
        :meta private:
        """
        self._notify_command_handlers(self.chosen_inline_handlers, new_chosen_inline_queries, 'chosen_inline_query')

    def process_new_callback_query(self, new_callback_queries):
        """
        :meta private:
        """
        self._notify_command_handlers(self.callback_query_handlers, new_callback_queries, 'callback_query')

    def process_new_shipping_query(self, new_shipping_queries):
        """
        :meta private:
        """
        self._notify_command_handlers(self.shipping_query_handlers, new_shipping_queries, 'shipping_query')

    def process_new_pre_checkout_query(self, new_pre_checkout_queries):
        """
        :meta private:
        """
        self._notify_command_handlers(self.pre_checkout_query_handlers, new_pre_checkout_queries, 'pre_checkout_query')

    def process_new_poll(self, new_polls):
        """
        :meta private:
        """
        self._notify_command_handlers(self.poll_handlers, new_polls, 'poll')

    def process_new_poll_answer(self, new_poll_answers):
        """
        :meta private:
        """
        self._notify_command_handlers(self.poll_answer_handlers, new_poll_answers, 'poll_answer')
    
    def process_new_my_chat_member(self, new_my_chat_members):
        """
        :meta private:
        """
        self._notify_command_handlers(self.my_chat_member_handlers, new_my_chat_members, 'my_chat_member')

    def process_new_chat_member(self, new_chat_members):
        """
        :meta private:
        """
        self._notify_command_handlers(self.chat_member_handlers, new_chat_members, 'chat_member')

    def process_new_chat_join_request(self, new_chat_join_request):
        """
        :meta private:
        """
        self._notify_command_handlers(self.chat_join_request_handlers, new_chat_join_request, 'chat_join_request')

    def process_new_chat_boost(self, new_chat_boosts):
        """
        :meta private:
        """
        self._notify_command_handlers(self.chat_boost_handlers, new_chat_boosts, 'chat_boost')

    def process_new_removed_chat_boost(self, new_removed_chat_boosts):
        """
        :meta private:
        """
        self._notify_command_handlers(self.removed_chat_boost_handlers, new_removed_chat_boosts, 'removed_chat_boost')

    def process_new_business_connection(self, new_business_connections):
        """
        :meta private:
        """
        self._notify_command_handlers(self.business_connection_handlers, new_business_connections, 'business_connection')

    def process_new_business_message(self, new_business_messages):
        """
        :meta private:
        """
        self._notify_command_handlers(self.business_message_handlers, new_business_messages, 'business_message')

    def process_new_edited_business_message(self, new_edited_business_messages):
        """
        :meta private:
        """
        self._notify_command_handlers(self.edited_business_message_handlers, new_edited_business_messages, 'edited_business_message')
        
    def process_new_deleted_business_messages(self, new_deleted_business_messages):
        """
        :meta private:
        """
        self._notify_command_handlers(self.deleted_business_messages_handlers, new_deleted_business_messages, 'deleted_business_messages')
    
    def process_new_purchased_paid_media(self, new_purchased_paid_media):
        """
        :meta private:
        """
        self._notify_command_handlers(self.purchased_paid_media_handlers, new_purchased_paid_media, 'purchased_paid_media')

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

    def _setup_change_detector(self, path_to_watch: str):
        try:
            # noinspection PyPackageRequirements
            from watchdog.observers import Observer
            from telebot.ext.reloader import EventHandler
        except ImportError:
            raise ImportError(
                'Please install watchdog and psutil before using restart_on_change option.'
            )

        self.event_handler = EventHandler()
        path = path_to_watch if path_to_watch else None
        if path is None:
            # Make it possible to specify --path argument to the script
            path = sys.argv[sys.argv.index('--path') + 1] if '--path' in sys.argv else '.'

            
        self.event_observer = Observer()
        self.event_observer.schedule(self.event_handler, path, recursive=True)
        self.event_observer.start()

    def __hide_token(self, message: str) -> str:
        if self.token in message:
            code = self.token.split(':')[1]
            return message.replace(code, "*" * len(code))
        else:
            return message

    def infinity_polling(self, timeout: Optional[int]=20, skip_pending: Optional[bool]=False, long_polling_timeout: Optional[int]=20,
                         logger_level: Optional[int]=logging.ERROR, allowed_updates: Optional[List[str]]=None,
                         restart_on_change: Optional[bool]=False, path_to_watch: Optional[str]=None, *args, **kwargs):
        """
        Wrap polling with infinite loop and exception handling to avoid bot stops polling.

        .. note::
        
            Install watchdog and psutil before using restart_on_change option.

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

        :param restart_on_change: Restart a file on file(s) change. Defaults to False
        :type restart_on_change: :obj:`bool`

        :param path_to_watch: Path to watch for changes. Defaults to current directory
        :type path_to_watch: :obj:`str`

        :return:
        """
        if skip_pending:
            self.__skip_updates()

        if restart_on_change:
            self._setup_change_detector(path_to_watch)

        while not self.__stop_polling.is_set():
            try:
                self.polling(non_stop=True, timeout=timeout, long_polling_timeout=long_polling_timeout,
                             logger_level=logger_level, allowed_updates=allowed_updates, restart_on_change=False,
                             *args, **kwargs)
            except Exception as e:
                if logger_level and logger_level >= logging.ERROR:
                    logger.error("Infinity polling exception: %s", self.__hide_token(str(e)))
                if logger_level and logger_level >= logging.DEBUG:
                    logger.error("Exception traceback:\n%s", self.__hide_token(traceback.format_exc()))
                time.sleep(3)
                continue
            if logger_level and logger_level >= logging.INFO:
                logger.error("Infinity polling: polling exited")
        if logger_level and logger_level >= logging.INFO:
            logger.error("Break infinity polling")


    def polling(self, non_stop: Optional[bool]=False, skip_pending: Optional[bool]=False, interval: Optional[int]=0,
                timeout: Optional[int]=20, long_polling_timeout: Optional[int]=20,
                logger_level: Optional[int]=logging.ERROR, allowed_updates: Optional[List[str]]=None,
                none_stop: Optional[bool]=None, restart_on_change: Optional[bool]=False, path_to_watch: Optional[str]=None):
        """
        This function creates a new Thread that calls an internal __retrieve_updates function.
        This allows the bot to retrieve Updates automatically and notify listeners and message handlers accordingly.

        Warning: Do not call this function more than once!
        
        Always gets updates.

        .. deprecated:: 4.1.1
            Use :meth:`infinity_polling` instead.

        .. note::
        
            Install watchdog and psutil before using restart_on_change option.

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

        :param none_stop: deprecated.
        :type none_stop: :obj:`bool`

        :param restart_on_change: Restart a file on file(s) change. Defaults to False
        :type restart_on_change: :obj:`bool`

        :param path_to_watch: Path to watch for changes. Defaults to None
        :type path_to_watch: :obj:`str`
        
        :return:
        """
        if none_stop is not None:
            logger.warning('The parameter "none_stop" is deprecated. Use "non_stop" instead.')
            non_stop = none_stop

        if skip_pending:
            self.__skip_updates()

        if restart_on_change:
            self._setup_change_detector(path_to_watch)

        logger.info('Starting your bot with username: [@%s]', self.user.username)
            
        if self.threaded:
            self.__threaded_polling(non_stop=non_stop, interval=interval, timeout=timeout, long_polling_timeout=long_polling_timeout,
                                    logger_level=logger_level, allowed_updates=allowed_updates)
        else:
            self.__non_threaded_polling(non_stop=non_stop, interval=interval, timeout=timeout, long_polling_timeout=long_polling_timeout,
                                        logger_level=logger_level, allowed_updates=allowed_updates)

    def _handle_exception(self, exception: Exception) -> bool:
        if self.exception_handler is None:
            return False

        handled = self.exception_handler.handle(exception)
        return handled

    def __threaded_polling(self, non_stop = False, interval = 0, timeout = None, long_polling_timeout = None,
                           logger_level=logging.ERROR, allowed_updates=None):
        if (not logger_level) or (logger_level < logging.INFO):
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
                handled = self._handle_exception(e)
                if not handled:
                    if logger_level and logger_level >= logging.ERROR:
                        logger.error("Threaded polling exception: %s", self.__hide_token(str(e)))
                    if logger_level and logger_level >= logging.DEBUG:
                        logger.error("Exception traceback:\n%s", self.__hide_token(traceback.format_exc()))
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
                handled = self._handle_exception(e)
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
        if (not logger_level) or (logger_level < logging.INFO):
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
                handled = self._handle_exception(e)
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
                handled = self._handle_exception(e)
                if not handled:
                    raise e
                else:
                    time.sleep(error_interval)
        #if logger_level and logger_level >= logging.INFO:   # enable in future releases. Change output to logger.error
        logger.info('Stopped polling.' + warning)


    def _exec_task(self, task, *args, **kwargs):
        if self.threaded:
            self.worker_pool.put(task, *args, **kwargs)
        else:
            try:
                task(*args, **kwargs)
            except Exception as e:
                handled = self._handle_exception(e)
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
        return types.User.de_json(
            apihelper.get_me(self.token)
        )


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
        return types.File.de_json(
            apihelper.get_file(self.token, file_id)
        )


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
    
    def set_message_reaction(self, chat_id: Union[int, str], message_id: int, reaction: Optional[List[types.ReactionType]]=None, is_big: Optional[bool]=None) -> bool:
        """
        Use this method to change the chosen reactions on a message. 
        Service messages can't be reacted to. Automatically forwarded messages from a channel to its discussion group have the same
        available reactions as messages in the channel. Returns True on success.

        Telegram documentation: https://core.telegram.org/bots/api#setmessagereaction

        :param chat_id: Unique identifier for the target chat or username of the target supergroup or channel (in the format @channelusername)
        :type chat_id: :obj:`int` or :obj:`str`

        :param message_id: Identifier of the message to set reaction to
        :type message_id: :obj:`int`

        :param reaction: New list of reaction types to set on the message. Currently, as non-premium users, bots can set up to one reaction per message.
            A custom emoji reaction can be used if it is either already present on the message or explicitly allowed by chat administrators.
        :type reaction: :obj:`list` of :class:`telebot.types.ReactionType`

        :param is_big: Pass True to set the reaction with a big animation
        :type is_big: :obj:`bool`

        :return: :obj:`bool`
        """
        return apihelper.set_message_reaction(
            self.token, chat_id, message_id, reaction = reaction, is_big = is_big)


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
        return types.UserProfilePhotos.de_json(
            apihelper.get_user_profile_photos(self.token, user_id, offset=offset, limit=limit)
        )

    def set_user_emoji_status(self, user_id: int, emoji_status_custom_emoji_id: Optional[str]=None, emoji_status_expiration_date: Optional[int]=None) -> bool:
        """
        Changes the emoji status for a given user that previously allowed the bot to manage their emoji status via the Mini App method requestEmojiStatusAccess. Returns True on success.

        Telegram documentation: https://core.telegram.org/bots/api#setuseremojistatus

        :param user_id: Unique identifier of the target user
        :type user_id: :obj:`int`

        :param emoji_status_custom_emoji_id: Custom emoji identifier of the emoji status to set. Pass an empty string to remove the status.
        :type emoji_status_custom_emoji_id: :obj:`str`

        :param emoji_status_expiration_date: Expiration date of the emoji status, if any
        :type emoji_status_expiration_date: :obj:`int`

        :return: :obj:`bool`
        """
        return apihelper.set_user_emoji_status(
            self.token, user_id, emoji_status_custom_emoji_id=emoji_status_custom_emoji_id, emoji_status_expiration_date=emoji_status_expiration_date)
    

    def get_chat(self, chat_id: Union[int, str]) -> types.ChatFullInfo:
        """
        Use this method to get up to date information about the chat (current name of the user for one-on-one
        conversations, current username of a user, group or channel, etc.). Returns a Chat object on success.

        Telegram documentation: https://core.telegram.org/bots/api#getchat

        :param chat_id: Unique identifier for the target chat or username of the target supergroup or channel (in the format @channelusername)
        :type chat_id: :obj:`int` or :obj:`str`

        :return: Chat information
        :rtype: :class:`telebot.types.ChatFullInfo`
        """
        return types.ChatFullInfo.de_json(
            apihelper.get_chat(self.token, chat_id)
        )


    def leave_chat(self, chat_id: Union[int, str]) -> bool:
        """
        Use this method for your bot to leave a group, supergroup or channel. Returns True on success.

        Telegram documentation: https://core.telegram.org/bots/api#leavechat

        :param chat_id: Unique identifier for the target chat or username of the target supergroup or channel (in the format @channelusername)
        :type chat_id: :obj:`int` or :obj:`str`

        :return: :obj:`bool`
        """
        return apihelper.leave_chat(self.token, chat_id)


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
        return apihelper.get_chat_member_count(self.token, chat_id)


    def get_chat_member_count(self, chat_id: Union[int, str]) -> int:
        """
        Use this method to get the number of members in a chat.

        Telegram documentation: https://core.telegram.org/bots/api#getchatmembercount

        :param chat_id: Unique identifier for the target chat or username of the target supergroup or channel (in the format @channelusername)
        :type chat_id: :obj:`int` or :obj:`str`

        :return: Number of members in the chat.
        :rtype: :obj:`int`
        """
        return apihelper.get_chat_member_count(self.token, chat_id)


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
        return apihelper.set_chat_sticker_set(self.token, chat_id, sticker_set_name)


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
        return apihelper.delete_chat_sticker_set(self.token, chat_id)


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
        return types.ChatMember.de_json(
            apihelper.get_chat_member(self.token, chat_id, user_id)
        )


    def send_message(
            self, chat_id: Union[int, str], text: str, 
            parse_mode: Optional[str]=None, 
            entities: Optional[List[types.MessageEntity]]=None,
            disable_web_page_preview: Optional[bool]=None,    # deprecated, for backward compatibility
            disable_notification: Optional[bool]=None, 
            protect_content: Optional[bool]=None,
            reply_to_message_id: Optional[int]=None,          # deprecated, for backward compatibility
            allow_sending_without_reply: Optional[bool]=None, # deprecated, for backward compatibility
            reply_markup: Optional[REPLY_MARKUP_TYPES]=None,
            timeout: Optional[int]=None,
            message_thread_id: Optional[int]=None,
            reply_parameters: Optional[types.ReplyParameters]=None,
            link_preview_options : Optional[types.LinkPreviewOptions]=None,
            business_connection_id: Optional[str]=None,
            message_effect_id: Optional[str]=None,
            allow_paid_broadcast: Optional[bool]=None) -> types.Message:
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

        :param disable_web_page_preview: deprecated.
        :type disable_web_page_preview: :obj:`bool`

        :param disable_notification: Sends the message silently. Users will receive a notification with no sound.
        :type disable_notification: :obj:`bool`

        :param protect_content: Protects the contents of the sent message from forwarding and saving
        :type protect_content: :obj:`bool`

        :param reply_to_message_id: deprecated.
        :type reply_to_message_id: :obj:`int`

        :param allow_sending_without_reply: deprecated.
        :type allow_sending_without_reply: :obj:`bool`

        :param reply_markup: Additional interface options. A JSON-serialized object for an inline keyboard, custom reply keyboard, instructions to remove reply keyboard or to force a reply from the user.
        :type reply_markup: :class:`telebot.types.InlineKeyboardMarkup` or :class:`telebot.types.ReplyKeyboardMarkup` or :class:`telebot.types.ReplyKeyboardRemove`
            or :class:`telebot.types.ForceReply`

        :param timeout: Timeout in seconds for the request.
        :type timeout: :obj:`int`

        :param message_thread_id: Identifier of a message thread, in which the message will be sent
        :type message_thread_id: :obj:`int`

        :param reply_parameters: Reply parameters.
        :type reply_parameters: :class:`telebot.types.ReplyParameters`

        :param link_preview_options: Link preview options.
        :type link_preview_options: :class:`telebot.types.LinkPreviewOptions`

        :param business_connection_id: Identifier of a business connection, in which the message will be sent
        :type business_connection_id: :obj:`str`

        :param message_effect_id: Unique identifier of the message effect to be added to the message; for private chats only
        :type message_effect_id: :obj:`str`

        :param allow_paid_broadcast: Pass True to allow up to 1000 messages per second, ignoring broadcasting limits for a fee
            of 0.1 Telegram Stars per message. The relevant Stars will be withdrawn from the bot's balance
        :type allow_paid_broadcast: :obj:`bool`

        :return: On success, the sent Message is returned.
        :rtype: :class:`telebot.types.Message`
        """
        parse_mode = self.parse_mode if (parse_mode is None) else parse_mode
        disable_notification = self.disable_notification if (disable_notification is None) else disable_notification
        protect_content = self.protect_content if (protect_content is None) else protect_content

        if allow_sending_without_reply is not None:
            logger.warning("The parameter 'allow_sending_without_reply' is deprecated. Use 'reply_parameters' instead.")

        if reply_to_message_id:
            logger.warning("The parameter 'reply_to_message_id' is deprecated. Use 'reply_parameters' instead.")

            if reply_parameters:
                logger.warning("Both 'reply_parameters' and 'reply_to_message_id' parameters are set: conflicting, 'reply_to_message_id' is deprecated")
            else:
                # create a ReplyParameters object
                reply_parameters = types.ReplyParameters(
                    reply_to_message_id,
                    allow_sending_without_reply=self.allow_sending_without_reply if (allow_sending_without_reply is None) else allow_sending_without_reply
                )

        if reply_parameters and (reply_parameters.allow_sending_without_reply is None):
            reply_parameters.allow_sending_without_reply = self.allow_sending_without_reply

        if disable_web_page_preview is not None:
            logger.warning("The parameter 'disable_web_page_preview' is deprecated. Use 'link_preview_options' instead.")

            if link_preview_options:
                logger.warning("Both 'link_preview_options' and 'disable_web_page_preview' parameters are set: conflicting, 'disable_web_page_preview' is deprecated")
            else:
                # create a LinkPreviewOptions object
                link_preview_options = types.LinkPreviewOptions(is_disabled=disable_web_page_preview)

        if link_preview_options and (link_preview_options.is_disabled is None):
            link_preview_options.is_disabled = self.disable_web_page_preview

        # Fix preview link options if link_preview_options not provided. Get param from class
        if not link_preview_options and self.disable_web_page_preview:
            # create a LinkPreviewOptions object
            link_preview_options = types.LinkPreviewOptions(is_disabled=self.disable_web_page_preview)

        return types.Message.de_json(
            apihelper.send_message(
                self.token, chat_id, text,
                reply_markup=reply_markup, parse_mode=parse_mode, disable_notification=disable_notification,
                timeout=timeout, entities=entities, protect_content=protect_content, message_thread_id=message_thread_id,
                reply_parameters=reply_parameters, link_preview_options=link_preview_options, business_connection_id=business_connection_id,
                message_effect_id=message_effect_id, allow_paid_broadcast=allow_paid_broadcast))


    def forward_message(
            self, chat_id: Union[int, str], from_chat_id: Union[int, str], 
            message_id: int, disable_notification: Optional[bool]=None,
            protect_content: Optional[bool]=None,
            timeout: Optional[int]=None,
            message_thread_id: Optional[int]=None,
            video_start_timestamp: Optional[int]=None) -> types.Message:
        """
        Use this method to forward messages of any kind.

        Telegram documentation: https://core.telegram.org/bots/api#forwardmessage

        :param disable_notification: Sends the message silently. Users will receive a notification with no sound
        :type disable_notification: :obj:`bool`

        :param chat_id: Unique identifier for the target chat or username of the target channel (in the format @channelusername)
        :type chat_id: :obj:`int` or :obj:`str`

        :param from_chat_id: Unique identifier for the chat where the original message was sent (or channel username in the format @channelusername)
        :type from_chat_id: :obj:`int` or :obj:`str`

        :param video_start_timestamp: New start timestamp for the forwarded video in the message
        :type video_start_timestamp: :obj:`int`

        :param message_id: Message identifier in the chat specified in from_chat_id
        :type message_id: :obj:`int`

        :param protect_content: Protects the contents of the forwarded message from forwarding and saving
        :type protect_content: :obj:`bool`

        :param timeout: Timeout in seconds for the request.
        :type timeout: :obj:`int`

        :param message_thread_id: Identifier of a message thread, in which the message will be sent
        :type message_thread_id: :obj:`int`

        :return: On success, the sent Message is returned.
        :rtype: :class:`telebot.types.Message`
        """
        disable_notification = self.disable_notification if (disable_notification is None) else disable_notification
        protect_content = self.protect_content if (protect_content is None) else protect_content

        return types.Message.de_json(
            apihelper.forward_message(
                self.token, chat_id, from_chat_id, message_id, disable_notification=disable_notification,
                timeout=timeout, protect_content=protect_content, message_thread_id=message_thread_id,
                video_start_timestamp=video_start_timestamp))


    def copy_message(
            self, chat_id: Union[int, str], 
            from_chat_id: Union[int, str], 
            message_id: int, 
            caption: Optional[str]=None, 
            parse_mode: Optional[str]=None, 
            caption_entities: Optional[List[types.MessageEntity]]=None,
            disable_notification: Optional[bool]=None, 
            protect_content: Optional[bool]=None,
            reply_to_message_id: Optional[int]=None,          # deprecated, for backward compatibility
            allow_sending_without_reply: Optional[bool]=None, # deprecated, for backward compatibility
            reply_markup: Optional[REPLY_MARKUP_TYPES]=None,
            timeout: Optional[int]=None,
            message_thread_id: Optional[int]=None,
            reply_parameters: Optional[types.ReplyParameters]=None,
            show_caption_above_media: Optional[bool]=None,
            allow_paid_broadcast: Optional[bool]=None,
            video_start_timestamp: Optional[int]=None) -> types.MessageID:
        """
        Use this method to copy messages of any kind.
        Service messages, paid media messages, giveaway messages, giveaway winners messages, and invoice messages can't be copied.
        A quiz poll can be copied only if the value of the field correct_option_id is known to the bot. The method is analogous to the method
        forwardMessage, but the copied message doesn't have a link to the original message. Returns the MessageId of the sent message on success.

        Telegram documentation: https://core.telegram.org/bots/api#copymessage

        :param chat_id: Unique identifier for the target chat or username of the target channel (in the format @channelusername)
        :type chat_id: :obj:`int` or :obj:`str`

        :param from_chat_id: Unique identifier for the chat where the original message was sent (or channel username in the format @channelusername)
        :type from_chat_id: :obj:`int` or :obj:`str`

        :param message_id: Message identifier in the chat specified in from_chat_id
        :type message_id: :obj:`int`

        :param video_start_timestamp: New start timestamp for the copied video in the message
        :type video_start_timestamp: :obj:`int`

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

        :param reply_to_message_id: deprecated.
        :type reply_to_message_id: :obj:`int`

        :param allow_sending_without_reply: deprecated.
        :type allow_sending_without_reply: :obj:`bool`

        :param reply_markup: Additional interface options. A JSON-serialized object for an inline keyboard, custom reply keyboard, instructions to remove reply keyboard
            or to force a reply from the user.
        :type reply_markup: :class:`telebot.types.InlineKeyboardMarkup` or :class:`telebot.types.ReplyKeyboardMarkup` or :class:`telebot.types.ReplyKeyboardRemove`
            or :class:`telebot.types.ForceReply`

        :param timeout: Timeout in seconds for the request.
        :type timeout: :obj:`int`

        :param message_thread_id: Identifier of a message thread, in which the message will be sent
        :type message_thread_id: :obj:`int`

        :param reply_parameters: Additional parameters for replies to messages
        :type reply_parameters: :class:`telebot.types.ReplyParameters`

        :param show_caption_above_media: Pass True, if the caption must be shown above the message media. Supported only for animation, photo and video messages.
        :type show_caption_above_media: :obj:`bool`

        :param allow_paid_broadcast: Pass True to allow up to 1000 messages per second, ignoring broadcasting limits for a fee
            of 0.1 Telegram Stars per message. The relevant Stars will be withdrawn from the bot's balance
        :type allow_paid_broadcast: :obj:`bool`
        
        :return: On success, the MessageId of the sent message is returned.
        :rtype: :class:`telebot.types.MessageID`
        """
        
        disable_notification = self.disable_notification if (disable_notification is None) else disable_notification
        parse_mode = self.parse_mode if (parse_mode is None) else parse_mode
        protect_content = self.protect_content if (protect_content is None) else protect_content

        if allow_sending_without_reply is not None:
            logger.warning("The parameter 'allow_sending_without_reply' is deprecated. Use 'reply_parameters' instead.")

        if reply_to_message_id:
            logger.warning("The parameter 'reply_to_message_id' is deprecated. Use 'reply_parameters' instead.")

            if reply_parameters:
                logger.warning("Both 'reply_parameters' and 'reply_to_message_id' parameters are set: conflicting, 'reply_to_message_id' is deprecated")
            else:
                # create a ReplyParameters object
                reply_parameters = types.ReplyParameters(
                    reply_to_message_id,
                    allow_sending_without_reply=self.allow_sending_without_reply if (allow_sending_without_reply is None) else allow_sending_without_reply
                )

        if reply_parameters and (reply_parameters.allow_sending_without_reply is None):
            reply_parameters.allow_sending_without_reply = self.allow_sending_without_reply

        return types.MessageID.de_json(
            apihelper.copy_message(self.token, chat_id, from_chat_id, message_id, caption=caption,
                parse_mode=parse_mode, caption_entities=caption_entities, disable_notification=disable_notification,
                reply_markup=reply_markup, timeout=timeout, protect_content=protect_content,
                message_thread_id=message_thread_id, reply_parameters=reply_parameters,
                show_caption_above_media=show_caption_above_media, allow_paid_broadcast=allow_paid_broadcast,
                video_start_timestamp=video_start_timestamp))


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
        return apihelper.delete_message(self.token, chat_id, message_id, timeout=timeout)

    
    def delete_messages(self, chat_id: Union[int, str], message_ids: List[int]):
        """
        Use this method to delete multiple messages simultaneously. If some of the specified messages can't be found, they are skipped.
        Returns True on success.

        Telegram documentation: https://core.telegram.org/bots/api#deletemessages

        :param chat_id: Unique identifier for the target chat or username of the target channel (in the format @channelusername)
        :type chat_id: :obj:`int` or :obj:`str`

        :param message_ids: Identifiers of the messages to be deleted
        :type message_ids: :obj:`list` of :obj:`int`

        :return: Returns True on success.
        """
        return apihelper.delete_messages(self.token, chat_id, message_ids)

    
    def forward_messages(self, chat_id: Union[str, int], from_chat_id: Union[str, int], message_ids: List[int],
                         disable_notification: Optional[bool]=None, message_thread_id: Optional[int]=None,
                         protect_content: Optional[bool]=None) -> List[types.MessageID]:
        """
        Use this method to forward multiple messages of any kind. If some of the specified messages can't be found or forwarded, they are skipped.
        Service messages and messages with protected content can't be forwarded. Album grouping is kept for forwarded messages.
        On success, an array of MessageId of the sent messages is returned.

        Telegram documentation: https://core.telegram.org/bots/api#forwardmessages

        :param chat_id: Unique identifier for the target chat or username of the target channel (in the format @channelusername)
        :type chat_id: :obj:`int` or :obj:`str`

        :param from_chat_id: Unique identifier for the chat where the original message was sent (or channel username in the format @channelusername)
        :type from_chat_id: :obj:`int` or :obj:`str`

        :param message_ids: Message identifiers in the chat specified in from_chat_id
        :type message_ids: :obj:`list`

        :param disable_notification: Sends the message silently. Users will receive a notification with no sound
        :type disable_notification: :obj:`bool`

        :param message_thread_id: Identifier of a message thread, in which the messages will be sent
        :type message_thread_id: :obj:`int`

        :param protect_content: Protects the contents of the forwarded message from forwarding and saving
        :type protect_content: :obj:`bool`

        :return: On success, the sent Message is returned.
        :rtype: :class:`telebot.types.MessageID`
        """

        disable_notification = self.disable_notification if (disable_notification is None) else disable_notification
        protect_content = self.protect_content if (protect_content is None) else protect_content

        result = apihelper.forward_messages(
            self.token, chat_id, from_chat_id, message_ids,
            disable_notification=disable_notification, message_thread_id=message_thread_id,
            protect_content=protect_content)
        return [types.MessageID.de_json(message_id) for message_id in result]

    
    def copy_messages(self, chat_id: Union[str, int], from_chat_id: Union[str, int], message_ids: List[int],
                        disable_notification: Optional[bool] = None, message_thread_id: Optional[int] = None,
                        protect_content: Optional[bool] = None, remove_caption: Optional[bool] = None) -> List[types.MessageID]:
        """
        Use this method to copy messages of any kind.
        If some of the specified messages can't be found or copied, they are skipped. Service messages, paid media messages, giveaway messages, giveaway winners messages,
        and invoice messages can't be copied. A quiz poll can be copied only if the value of the field correct_option_id is known to the bot. The method is analogous
        to the method forwardMessages, but the copied messages don't have a link to the original message. Album grouping is kept for copied messages. On success, an array
        of MessageId of the sent messages is returned.

        Telegram documentation: https://core.telegram.org/bots/api#copymessages


        :param chat_id: Unique identifier for the target chat or username of the target channel (in the format @channelusername)
        :type chat_id: :obj:`int` or :obj:`str`

        :param from_chat_id: Unique identifier for the chat where the original message was sent (or channel username in the format @channelusername)
        :type from_chat_id: :obj:`int` or :obj:`str`

        :param message_ids: Message identifiers in the chat specified in from_chat_id
        :type message_ids: :obj:`list` of :obj:`int`

        :param disable_notification: Sends the message silently. Users will receive a notification with no sound
        :type disable_notification: :obj:`bool`

        :param message_thread_id: Identifier of a message thread, in which the messages will be sent
        :type message_thread_id: :obj:`int`

        :param protect_content: Protects the contents of the forwarded message from forwarding and saving
        :type protect_content: :obj:`bool`

        :param remove_caption: Pass True to copy the messages without their captions
        :type remove_caption: :obj:`bool`

        :return: On success, an array of MessageId of the sent messages is returned.
        :rtype: :obj:`list` of :class:`telebot.types.MessageID`
        """
        disable_notification = self.disable_notification if disable_notification is None else disable_notification
        protect_content = self.protect_content if protect_content is None else protect_content

        result = apihelper.copy_messages(
            self.token, chat_id, from_chat_id, message_ids, disable_notification=disable_notification,
            message_thread_id=message_thread_id, protect_content=protect_content, remove_caption=remove_caption)
        return [types.MessageID.de_json(message_id) for message_id in result]
    

    def send_dice(
            self, chat_id: Union[int, str],
            emoji: Optional[str]=None, disable_notification: Optional[bool]=None, 
            reply_to_message_id: Optional[int]=None,          # deprecated, for backward compatibility
            reply_markup: Optional[REPLY_MARKUP_TYPES]=None, 
            timeout: Optional[int]=None,
            allow_sending_without_reply: Optional[bool]=None, # deprecated, for backward compatibility
            protect_content: Optional[bool]=None,
            message_thread_id: Optional[int]=None,
            reply_parameters: Optional[types.ReplyParameters]=None,
            business_connection_id: Optional[str]=None,
            message_effect_id: Optional[str]=None,
            allow_paid_broadcast: Optional[bool]=None) -> types.Message:
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

        :param reply_markup: Additional interface options. A JSON-serialized object for an inline keyboard, custom reply keyboard, instructions
            to remove reply keyboard or to force a reply from the user.
        :type reply_markup: :class:`telebot.types.InlineKeyboardMarkup` or :class:`telebot.types.ReplyKeyboardMarkup` or :class:`telebot.types.ReplyKeyboardRemove`
            or :class:`telebot.types.ForceReply`

        :param reply_to_message_id: deprecated.
        :type reply_to_message_id: :obj:`int`

        :param allow_sending_without_reply: deprecated.
        :type allow_sending_without_reply: :obj:`bool`

        :param timeout: Timeout in seconds for the request.
        :type timeout: :obj:`int`

        :param protect_content: Protects the contents of the sent message from forwarding and saving
        :type protect_content: :obj:`bool`

        :param message_thread_id: Identifier of a message thread, in which the message will be sent
        :type message_thread_id: :obj:`int`

        :param reply_parameters: Additional parameters for replies to messages
        :type reply_parameters: :class:`telebot.types.ReplyParameters`

        :param business_connection_id: Identifier of a business connection, in which the message will be sent
        :type business_connection_id: :obj:`str`

        :param message_effect_id: Unique identifier of the message effect to be added to the message; for private chats only
        :type message_effect_id: :obj:`str`

        :param allow_paid_broadcast: Pass True to allow up to 1000 messages per second, ignoring broadcasting limits for a fee
            of 0.1 Telegram Stars per message. The relevant Stars will be withdrawn from the bot's balance
        :type allow_paid_broadcast: :obj:`bool`

        :return: On success, the sent Message is returned.
        :rtype: :class:`telebot.types.Message`
        """
        disable_notification = self.disable_notification if (disable_notification is None) else disable_notification
        protect_content = self.protect_content if (protect_content is None) else protect_content

        if allow_sending_without_reply is not None:
            logger.warning("The parameter 'allow_sending_without_reply' is deprecated. Use 'reply_parameters' instead.")

        if reply_to_message_id:
            logger.warning("The parameter 'reply_to_message_id' is deprecated. Use 'reply_parameters' instead.")

            if reply_parameters:
                logger.warning("Both 'reply_parameters' and 'reply_to_message_id' parameters are set: conflicting, 'reply_to_message_id' is deprecated")
            else:
                # create a ReplyParameters object
                reply_parameters = types.ReplyParameters(
                    reply_to_message_id,
                    allow_sending_without_reply=self.allow_sending_without_reply if (allow_sending_without_reply is None) else allow_sending_without_reply
                )

        if reply_parameters and (reply_parameters.allow_sending_without_reply is None):
            reply_parameters.allow_sending_without_reply = self.allow_sending_without_reply

        return types.Message.de_json(
            apihelper.send_dice(
                self.token, chat_id, emoji=emoji, disable_notification=disable_notification,
                reply_markup=reply_markup, timeout=timeout, protect_content=protect_content,
                message_thread_id=message_thread_id, reply_parameters=reply_parameters, business_connection_id=business_connection_id,
                message_effect_id=message_effect_id, allow_paid_broadcast=allow_paid_broadcast))



    def send_photo(
            self, chat_id: Union[int, str], photo: Union[Any, str], 
            caption: Optional[str]=None, parse_mode: Optional[str]=None,
            caption_entities: Optional[List[types.MessageEntity]]=None,
            disable_notification: Optional[bool]=None,
            protect_content: Optional[bool]=None,
            reply_to_message_id: Optional[int]=None,          # deprecated, for backward compatibility
            allow_sending_without_reply: Optional[bool]=None, # deprecated, for backward compatibility
            reply_markup: Optional[REPLY_MARKUP_TYPES]=None,
            timeout: Optional[int]=None,
            message_thread_id: Optional[int]=None,
            has_spoiler: Optional[bool]=None,
            reply_parameters: Optional[types.ReplyParameters]=None,
            business_connection_id: Optional[str]=None,
            message_effect_id: Optional[str]=None,
            show_caption_above_media: Optional[bool]=None,
            allow_paid_broadcast: Optional[bool]=None) -> types.Message:
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

        :param reply_to_message_id: deprecated.
        :type reply_to_message_id: :obj:`int`

        :param allow_sending_without_reply: deprecated.
        :type allow_sending_without_reply: :obj:`bool`

        :param reply_markup: Additional interface options. A JSON-serialized object for an inline keyboard, custom reply keyboard, instructions
            to remove reply keyboard or to force a reply from the user.
        :type reply_markup: :class:`telebot.types.InlineKeyboardMarkup` or :class:`telebot.types.ReplyKeyboardMarkup` or :class:`telebot.types.ReplyKeyboardRemove`
            or :class:`telebot.types.ForceReply`

        :param timeout: Timeout in seconds for the request.
        :type timeout: :obj:`int`

        :param message_thread_id: Identifier of a message thread, in which the message will be sent
        :type message_thread_id: :obj:`int`

        :param has_spoiler: Pass True, if the photo should be sent as a spoiler
        :type has_spoiler: :obj:`bool`

        :param reply_parameters: Additional parameters for replies to messages
        :type reply_parameters: :class:`telebot.types.ReplyParameters`

        :param business_connection_id: Identifier of a business connection, in which the message will be sent
        :type business_connection_id: :obj:`str`

        :param message_effect_id: Unique identifier of the message effect to be added to the message; for private chats only
        :type message_effect_id: :obj:`str`

        :param show_caption_above_media: Pass True, if the caption must be shown above the message media. Supported only for animation, photo and video messages.
        :type show_caption_above_media: :obj:`bool`

        :param allow_paid_broadcast: Pass True to allow up to 1000 messages per second, ignoring broadcasting limits for a fee
            of 0.1 Telegram Stars per message. The relevant Stars will be withdrawn from the bot's balance
        :type allow_paid_broadcast: :obj:`bool`
        
        :return: On success, the sent Message is returned.
        :rtype: :class:`telebot.types.Message`
        """
        parse_mode = self.parse_mode if (parse_mode is None) else parse_mode
        disable_notification = self.disable_notification if (disable_notification is None) else disable_notification
        protect_content = self.protect_content if (protect_content is None) else protect_content

        if allow_sending_without_reply is not None:
            logger.warning("The parameter 'allow_sending_without_reply' is deprecated. Use 'reply_parameters' instead.")

        if reply_to_message_id:
            logger.warning("The parameter 'reply_to_message_id' is deprecated. Use 'reply_parameters' instead.")

            if reply_parameters:
                logger.warning("Both 'reply_parameters' and 'reply_to_message_id' parameters are set: conflicting, 'reply_to_message_id' is deprecated")
            else:
                # create a ReplyParameters object
                reply_parameters = types.ReplyParameters(
                    reply_to_message_id,
                    allow_sending_without_reply=self.allow_sending_without_reply if (allow_sending_without_reply is None) else allow_sending_without_reply
                )

        if reply_parameters and (reply_parameters.allow_sending_without_reply is None):
            reply_parameters.allow_sending_without_reply = self.allow_sending_without_reply

        return types.Message.de_json(
            apihelper.send_photo(
                self.token, chat_id, photo, caption=caption, reply_markup=reply_markup,
                parse_mode=parse_mode, disable_notification=disable_notification, timeout=timeout,
                caption_entities=caption_entities, protect_content=protect_content,
                message_thread_id=message_thread_id, has_spoiler=has_spoiler, reply_parameters=reply_parameters,
                business_connection_id=business_connection_id, message_effect_id=message_effect_id,
                show_caption_above_media=show_caption_above_media, allow_paid_broadcast=allow_paid_broadcast))


    def send_audio(
            self, chat_id: Union[int, str], audio: Union[Any, str], 
            caption: Optional[str]=None, duration: Optional[int]=None, 
            performer: Optional[str]=None, title: Optional[str]=None,
            reply_to_message_id: Optional[int]=None,          # deprecated, for backward compatibility
            reply_markup: Optional[REPLY_MARKUP_TYPES]=None, 
            parse_mode: Optional[str]=None, 
            disable_notification: Optional[bool]=None,
            timeout: Optional[int]=None, 
            thumbnail: Optional[Union[Any, str]]=None,
            caption_entities: Optional[List[types.MessageEntity]]=None,
            allow_sending_without_reply: Optional[bool]=None, # deprecated, for backward compatibility
            protect_content: Optional[bool]=None,
            message_thread_id: Optional[int]=None,
            thumb: Optional[Union[Any, str]]=None,
            reply_parameters: Optional[types.ReplyParameters]=None,
            business_connection_id: Optional[str]=None,
            message_effect_id: Optional[str]=None,
            allow_paid_broadcast: Optional[bool]=None) -> types.Message:
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

        :param reply_markup:
        :type reply_markup: :class:`telebot.types.InlineKeyboardMarkup` or :class:`telebot.types.ReplyKeyboardMarkup` or :class:`telebot.types.ReplyKeyboardRemove`
            or :class:`telebot.types.ForceReply`

        :param parse_mode: Mode for parsing entities in the audio caption. See formatting options for more details.
        :type parse_mode: :obj:`str`

        :param disable_notification: Sends the message silently. Users will receive a notification with no sound.
        :type disable_notification: :obj:`bool`

        :param reply_to_message_id: deprecated.
        :type reply_to_message_id: :obj:`int`

        :param allow_sending_without_reply: deprecated.
        :type allow_sending_without_reply: :obj:`bool`

        :param timeout: Timeout in seconds for the request.
        :type timeout: :obj:`int`

        :param thumbnail: Thumbnail of the file sent; can be ignored if thumbnail generation for the file is supported server-side.
            The thumbnail should be in JPEG format and less than 200 kB in size. A thumbnail's width and height should not exceed 320.
            Ignored if the file is not uploaded using multipart/form-data. Thumbnails can't be reused and can be only uploaded as a new file,
            so you can pass “attach://<file_attach_name>” if the thumbnail was uploaded using multipart/form-data under <file_attach_name>
        :type thumbnail: :obj:`str` or :class:`telebot.types.InputFile`

        :param caption_entities: A JSON-serialized list of special entities that appear in the caption, which can be specified instead of parse_mode
        :type caption_entities: :obj:`list` of :class:`telebot.types.MessageEntity`

        :param protect_content: Protects the contents of the sent message from forwarding and saving
        :type protect_content: :obj:`bool`

        :param message_thread_id: Identifier of a message thread, in which the message will be sent
        :type message_thread_id: :obj:`int`

        :param thumb: deprecated.
        :type thumb: :obj:`str` or :class:`telebot.types.InputFile`

        :param reply_parameters: Reply parameters.
        :type reply_parameters: :class:`telebot.types.ReplyParameters`

        :param business_connection_id: Identifier of a business connection, in which the message will be sent
        :type business_connection_id: :obj:`str`

        :param message_effect_id: Unique identifier of the message effect to be added to the message; for private chats only
        :type message_effect_id: :obj:`str`

        :param allow_paid_broadcast: Pass True to allow up to 1000 messages per second, ignoring broadcasting limits for a fee
            of 0.1 Telegram Stars per message. The relevant Stars will be withdrawn from the bot's balance
        :type allow_paid_broadcast: :obj:`bool`

        :return: On success, the sent Message is returned.
        :rtype: :class:`telebot.types.Message`
        """
        parse_mode = self.parse_mode if (parse_mode is None) else parse_mode
        disable_notification = self.disable_notification if (disable_notification is None) else disable_notification
        protect_content = self.protect_content if (protect_content is None) else protect_content

        if allow_sending_without_reply is not None:
            logger.warning("The parameter 'allow_sending_without_reply' is deprecated. Use 'reply_parameters' instead.")

        if reply_to_message_id:
            logger.warning("The parameter 'reply_to_message_id' is deprecated. Use 'reply_parameters' instead.")

            if reply_parameters:
                logger.warning("Both 'reply_parameters' and 'reply_to_message_id' parameters are set: conflicting, 'reply_to_message_id' is deprecated")
            else:
                # create a ReplyParameters object
                reply_parameters = types.ReplyParameters(
                    reply_to_message_id,
                    allow_sending_without_reply=self.allow_sending_without_reply if (allow_sending_without_reply is None) else allow_sending_without_reply
                )

        if reply_parameters and (reply_parameters.allow_sending_without_reply is None):
            reply_parameters.allow_sending_without_reply = self.allow_sending_without_reply

        if thumb is not None and thumbnail is None:
            logger.warning('The parameter "thumb" is deprecated. Use "thumbnail" instead.')
            thumbnail = thumb

        return types.Message.de_json(
            apihelper.send_audio(
                self.token, chat_id, audio, caption=caption, duration=duration, performer=performer, title=title,
                reply_markup=reply_markup, parse_mode=parse_mode, disable_notification=disable_notification,
                timeout=timeout, thumbnail=thumbnail, caption_entities=caption_entities, protect_content=protect_content,
                message_thread_id=message_thread_id, reply_parameters=reply_parameters, business_connection_id=business_connection_id,
                message_effect_id=message_effect_id, allow_paid_broadcast=allow_paid_broadcast))


    def send_voice(
            self, chat_id: Union[int, str], voice: Union[Any, str], 
            caption: Optional[str]=None, duration: Optional[int]=None, 
            reply_to_message_id: Optional[int]=None,          # deprecated, for backward compatibility
            reply_markup: Optional[REPLY_MARKUP_TYPES]=None,
            parse_mode: Optional[str]=None, 
            disable_notification: Optional[bool]=None, 
            timeout: Optional[int]=None,
            caption_entities: Optional[List[types.MessageEntity]]=None,
            allow_sending_without_reply: Optional[bool]=None, # deprecated, for backward compatibility
            protect_content: Optional[bool]=None,
            message_thread_id: Optional[int]=None,
            reply_parameters: Optional[types.ReplyParameters]=None,
            business_connection_id: Optional[str]=None,
            message_effect_id: Optional[str]=None,
            allow_paid_broadcast: Optional[bool]=None) -> types.Message:
        """
        Use this method to send audio files, if you want Telegram clients to display the file as a playable voice message. For this to work, your audio must be in an .OGG file encoded with OPUS, or in .MP3 format, or in .M4A format (other formats may be sent as Audio or Document). On success, the sent Message is returned. Bots can currently send voice messages of up to 50 MB in size, this limit may be changed in the future.

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

        :param reply_markup: Additional interface options. A JSON-serialized object for an inline keyboard, custom reply keyboard, instructions
            to remove reply keyboard or to force a reply from the user.
        :type reply_markup: :class:`telebot.types.InlineKeyboardMarkup` or :class:`telebot.types.ReplyKeyboardMarkup` or :class:`telebot.types.ReplyKeyboardRemove`
            or :class:`telebot.types.ForceReply`

        :param parse_mode: Mode for parsing entities in the voice message caption. See formatting options for more details.
        :type parse_mode: :obj:`str`

        :param disable_notification: Sends the message silently. Users will receive a notification with no sound.
        :type disable_notification: :obj:`bool`

        :param reply_to_message_id: deprecated.
        :type reply_to_message_id: :obj:`int`

        :param allow_sending_without_reply: deprecated.
        :type allow_sending_without_reply: :obj:`bool`

        :param timeout: Timeout in seconds for the request.
        :type timeout: :obj:`int`

        :param caption_entities: A JSON-serialized list of special entities that appear in the caption, which can be specified instead of parse_mode
        :type caption_entities: :obj:`list` of :class:`telebot.types.MessageEntity`

        :param protect_content: Protects the contents of the sent message from forwarding and saving
        :type protect_content: :obj:`bool`

        :param message_thread_id: Identifier of a message thread, in which the message will be sent
        :type message_thread_id: :obj:`int`

        :param reply_parameters: Reply parameters.
        :type reply_parameters: :class:`telebot.types.ReplyParameters`

        :param business_connection_id: Identifier of a business connection, in which the message will be sent
        :type business_connection_id: :obj:`str`

        :param message_effect_id: Unique identifier of the message effect to be added to the message; for private chats only
        :type message_effect_id: :obj:`str`

        :param allow_paid_broadcast: Pass True to allow up to 1000 messages per second, ignoring broadcasting limits for a fee
            of 0.1 Telegram Stars per message. The relevant Stars will be withdrawn from the bot's balance
        :type allow_paid_broadcast: :obj:`bool`

        :return: On success, the sent Message is returned.
        """
        parse_mode = self.parse_mode if (parse_mode is None) else parse_mode
        disable_notification = self.disable_notification if (disable_notification is None) else disable_notification
        protect_content = self.protect_content if (protect_content is None) else protect_content

        if allow_sending_without_reply is not None:
            logger.warning("The parameter 'allow_sending_without_reply' is deprecated. Use 'reply_parameters' instead.")

        if reply_to_message_id:
            logger.warning("The parameter 'reply_to_message_id' is deprecated. Use 'reply_parameters' instead.")

            if reply_parameters:
                logger.warning("Both 'reply_parameters' and 'reply_to_message_id' parameters are set: conflicting, 'reply_to_message_id' is deprecated")
            else:
                # create a ReplyParameters object
                reply_parameters = types.ReplyParameters(
                    reply_to_message_id,
                    allow_sending_without_reply=self.allow_sending_without_reply if (allow_sending_without_reply is None) else allow_sending_without_reply
                )

        if reply_parameters and (reply_parameters.allow_sending_without_reply is None):
            reply_parameters.allow_sending_without_reply = self.allow_sending_without_reply

        return types.Message.de_json(
            apihelper.send_voice(
                self.token, chat_id, voice, caption=caption, duration=duration, reply_markup=reply_markup,
                parse_mode=parse_mode, disable_notification=disable_notification, timeout=timeout,
                caption_entities=caption_entities, protect_content=protect_content,
                message_thread_id=message_thread_id, reply_parameters=reply_parameters, business_connection_id=business_connection_id,
                message_effect_id=message_effect_id, allow_paid_broadcast=allow_paid_broadcast)
        )


    def send_document(
            self, chat_id: Union[int, str], document: Union[Any, str],
            reply_to_message_id: Optional[int]=None,          # deprecated, for backward compatibility
            caption: Optional[str]=None, 
            reply_markup: Optional[REPLY_MARKUP_TYPES]=None,
            parse_mode: Optional[str]=None, 
            disable_notification: Optional[bool]=None, 
            timeout: Optional[int]=None, 
            thumbnail: Optional[Union[Any, str]]=None,
            caption_entities: Optional[List[types.MessageEntity]]=None,
            allow_sending_without_reply: Optional[bool]=None, # deprecated, for backward compatibility
            visible_file_name: Optional[str]=None,
            disable_content_type_detection: Optional[bool]=None,
            data: Optional[Union[Any, str]]=None,
            protect_content: Optional[bool]=None, message_thread_id: Optional[int]=None,
            thumb: Optional[Union[Any, str]]=None,
            reply_parameters: Optional[types.ReplyParameters]=None,
            business_connection_id: Optional[str]=None,
            message_effect_id: Optional[str]=None,
            allow_paid_broadcast: Optional[bool]=None) -> types.Message:
        """
        Use this method to send general files.

        Telegram documentation: https://core.telegram.org/bots/api#senddocument
        
        :param chat_id: Unique identifier for the target chat or username of the target channel (in the format @channelusername)
        :type chat_id: :obj:`int` or :obj:`str`

        :param document: (document) File to send. Pass a file_id as String to send a file that exists on the Telegram servers (recommended), pass an HTTP URL as a
            String for Telegram to get a file from the Internet, or upload a new one using multipart/form-data
        :type document: :obj:`str` or :class:`telebot.types.InputFile`

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

        :param reply_to_message_id: deprecated.
        :type reply_to_message_id: :obj:`int`

        :param allow_sending_without_reply: deprecated.
        :type allow_sending_without_reply: :obj:`bool`

        :param timeout: Timeout in seconds for the request.
        :type timeout: :obj:`int`

        :param thumbnail: InputFile or String : Thumbnail of the file sent; can be ignored if thumbnail generation for the file is supported server-side. The thumbnail should be in JPEG format and less than 200 kB in size. A thumbnail's width and height should not exceed 320. Ignored if the file is not uploaded using multipart/form-data. Thumbnails can't be reused and can be only uploaded as a new file, so you can pass “attach://<file_attach_name>” if the thumbnail was uploaded using multipart/form-data under <file_attach_name>
        :type thumbnail: :obj:`str` or :class:`telebot.types.InputFile`

        :param caption_entities: A JSON-serialized list of special entities that appear in the caption, which can be specified instead of parse_mode
        :type caption_entities: :obj:`list` of :class:`telebot.types.MessageEntity`

        :param visible_file_name: allows to define file name that will be visible in the Telegram instead of original file name
        :type visible_file_name: :obj:`str`

        :param disable_content_type_detection: Disables automatic server-side content type detection for files uploaded using multipart/form-data
        :type disable_content_type_detection: :obj:`bool`

        :param data: function typo miss compatibility: do not use it
        :type data: :obj:`str`

        :param protect_content: Protects the contents of the sent message from forwarding and saving
        :type protect_content: :obj:`bool`

        :param message_thread_id: The thread to which the message will be sent
        :type message_thread_id: :obj:`int`

        :param thumb: deprecated.
        :type thumb: :obj:`str` or :class:`telebot.types.InputFile`

        :param reply_parameters: Reply parameters.
        :type reply_parameters: :class:`telebot.types.ReplyParameters`

        :param business_connection_id: Identifier of a business connection, in which the message will be sent
        :type business_connection_id: :obj:`str`

        :param message_effect_id: Unique identifier of the message effect to be added to the message; for private chats only
        :type message_effect_id: :obj:`str`

        :param allow_paid_broadcast: Pass True to allow up to 1000 messages per second, ignoring broadcasting limits for a fee
            of 0.1 Telegram Stars per message. The relevant Stars will be withdrawn from the bot's balance
        :type allow_paid_broadcast: :obj:`bool`

        :return: On success, the sent Message is returned.
        :rtype: :class:`telebot.types.Message`
        """
        parse_mode = self.parse_mode if (parse_mode is None) else parse_mode
        disable_notification = self.disable_notification if (disable_notification is None) else disable_notification
        protect_content = self.protect_content if (protect_content is None) else protect_content

        if allow_sending_without_reply is not None:
            logger.warning("The parameter 'allow_sending_without_reply' is deprecated. Use 'reply_parameters' instead.")

        if reply_to_message_id:
            logger.warning("The parameter 'reply_to_message_id' is deprecated. Use 'reply_parameters' instead.")

            if reply_parameters:
                logger.warning("Both 'reply_parameters' and 'reply_to_message_id' parameters are set: conflicting, 'reply_to_message_id' is deprecated")
            else:
                # create a ReplyParameters object
                reply_parameters = types.ReplyParameters(
                    reply_to_message_id,
                    allow_sending_without_reply=self.allow_sending_without_reply if (allow_sending_without_reply is None) else allow_sending_without_reply
                )

        if reply_parameters and (reply_parameters.allow_sending_without_reply is None):
            reply_parameters.allow_sending_without_reply = self.allow_sending_without_reply

        if data and (not document):
            logger.warning('The parameter "data" is deprecated. Use "document" instead.')
            document = data

        if thumb is not None and thumbnail is None:
            logger.warning('The parameter "thumb" is deprecated. Use "thumbnail" instead.')
            thumbnail = thumb

        if isinstance(document, types.InputFile) and visible_file_name:
            # inputfile name ignored, warn
            logger.warning('Cannot use both InputFile and visible_file_name. InputFile name will be ignored.')

        return types.Message.de_json(
            apihelper.send_data(
                self.token, chat_id, document, 'document',
                reply_markup=reply_markup, parse_mode=parse_mode, disable_notification=disable_notification,
                timeout=timeout, caption=caption, thumbnail=thumbnail, caption_entities=caption_entities,
                disable_content_type_detection=disable_content_type_detection, visible_file_name=visible_file_name,
                protect_content=protect_content, message_thread_id=message_thread_id, reply_parameters=reply_parameters,
                business_connection_id=business_connection_id, message_effect_id=message_effect_id, allow_paid_broadcast=allow_paid_broadcast)
        )


    def send_sticker(
            self, chat_id: Union[int, str],
            sticker: Union[Any, str],
            reply_to_message_id: Optional[int]=None,          # deprecated, for backward compatibility
            reply_markup: Optional[REPLY_MARKUP_TYPES]=None,
            disable_notification: Optional[bool]=None,
            timeout: Optional[int]=None,
            allow_sending_without_reply: Optional[bool]=None, # deprecated, for backward compatibility
            protect_content:Optional[bool]=None,
            data: Union[Any, str]=None,
            message_thread_id: Optional[int]=None,
            emoji: Optional[str]=None,
            reply_parameters: Optional[types.ReplyParameters]=None,
            business_connection_id: Optional[str]=None,
            message_effect_id: Optional[str]=None,
            allow_paid_broadcast: Optional[bool]=None) -> types.Message:
        """
        Use this method to send static .WEBP, animated .TGS, or video .WEBM stickers.
        On success, the sent Message is returned.

        Telegram documentation: https://core.telegram.org/bots/api#sendsticker

        :param chat_id: Unique identifier for the target chat or username of the target channel (in the format @channelusername)
        :type chat_id: :obj:`int` or :obj:`str`

        :param sticker: Sticker to send. Pass a file_id as String to send a file that exists on the Telegram servers (recommended), pass an HTTP URL
            as a String for Telegram to get a .webp file from the Internet, or upload a new one using multipart/form-data.
        :type sticker: :obj:`str` or :class:`telebot.types.InputFile`

        :param reply_markup: Additional interface options. A JSON-serialized object for an inline keyboard, custom reply keyboard, instructions to remove reply keyboard
            or to force a reply from the user.
        :type reply_markup: :class:`telebot.types.InlineKeyboardMarkup` or :class:`telebot.types.ReplyKeyboardMarkup` or :class:`telebot.types.ReplyKeyboardRemove`
            or :class:`telebot.types.ForceReply`

        :param disable_notification: to disable the notification
        :type disable_notification: :obj:`bool`

        :param reply_to_message_id: deprecated.
        :type reply_to_message_id: :obj:`int`

        :param allow_sending_without_reply: deprecated.
        :type allow_sending_without_reply: :obj:`bool`

        :param timeout: Timeout in seconds for the request.
        :type timeout: :obj:`int`

        :param protect_content: Protects the contents of the sent message from forwarding and saving
        :type protect_content: :obj:`bool`

        :param data: function typo miss compatibility: do not use it
        :type data: :obj:`str`

        :param message_thread_id: The thread to which the message will be sent
        :type message_thread_id: :obj:`int`

        :param emoji: Emoji associated with the sticker; only for just uploaded stickers
        :type emoji: :obj:`str`

        :param reply_parameters: Reply parameters.
        :type reply_parameters: :class:`telebot.types.ReplyParameters`

        :param business_connection_id: Identifier of a business connection, in which the message will be sent
        :type business_connection_id: :obj:`str`

        :param message_effect_id: Unique identifier of the message effect to be added to the message; for private chats only
        :type message_effect_id: :obj:`str`

        :param allow_paid_broadcast: Pass True to allow up to 1000 messages per second, ignoring broadcasting limits for a fee
            of 0.1 Telegram Stars per message. The relevant Stars will be withdrawn from the bot's balance
        :type allow_paid_broadcast: :obj:`bool`

        :return: On success, the sent Message is returned.
        :rtype: :class:`telebot.types.Message`
        """
        disable_notification = self.disable_notification if (disable_notification is None) else disable_notification
        protect_content = self.protect_content if (protect_content is None) else protect_content

        if allow_sending_without_reply is not None:
            logger.warning("The parameter 'allow_sending_without_reply' is deprecated. Use 'reply_parameters' instead.")

        if reply_to_message_id:
            logger.warning("The parameter 'reply_to_message_id' is deprecated. Use 'reply_parameters' instead.")

            if reply_parameters:
                logger.warning("Both 'reply_parameters' and 'reply_to_message_id' parameters are set: conflicting, 'reply_to_message_id' is deprecated")
            else:
                # create a ReplyParameters object
                reply_parameters = types.ReplyParameters(
                    reply_to_message_id,
                    allow_sending_without_reply=self.allow_sending_without_reply if (allow_sending_without_reply is None) else allow_sending_without_reply
                )

        if reply_parameters and (reply_parameters.allow_sending_without_reply is None):
            reply_parameters.allow_sending_without_reply = self.allow_sending_without_reply

        if data and (not sticker):
            logger.warning('The parameter "data" is deprecated. Use "sticker" instead.')
            sticker = data
            
        return types.Message.de_json(
            apihelper.send_data(
                self.token, chat_id, sticker, 'sticker',
                reply_markup=reply_markup, disable_notification=disable_notification, timeout=timeout,
                protect_content=protect_content, message_thread_id=message_thread_id, emoji=emoji,
                reply_parameters=reply_parameters, business_connection_id=business_connection_id,
                message_effect_id=message_effect_id, allow_paid_broadcast=allow_paid_broadcast)
        )


    def send_video(
            self, chat_id: Union[int, str], video: Union[Any, str], 
            duration: Optional[int]=None,
            width: Optional[int]=None,
            height: Optional[int]=None,
            thumbnail: Optional[Union[Any, str]]=None, 
            caption: Optional[str]=None, 
            parse_mode: Optional[str]=None, 
            caption_entities: Optional[List[types.MessageEntity]]=None,
            supports_streaming: Optional[bool]=None, 
            disable_notification: Optional[bool]=None,
            protect_content: Optional[bool]=None,
            reply_to_message_id: Optional[int]=None,          # deprecated, for backward compatibility
            allow_sending_without_reply: Optional[bool]=None, # deprecated, for backward compatibility
            reply_markup: Optional[REPLY_MARKUP_TYPES]=None,
            timeout: Optional[int]=None,
            data: Optional[Union[Any, str]]=None,
            message_thread_id: Optional[int]=None,
            has_spoiler: Optional[bool]=None,
            thumb: Optional[Union[Any, str]]=None,
            reply_parameters: Optional[types.ReplyParameters]=None,
            business_connection_id: Optional[str]=None,
            message_effect_id: Optional[str]=None,
            show_caption_above_media: Optional[bool]=None,
            allow_paid_broadcast: Optional[bool]=None,
            cover: Optional[Union[Any, str]]=None,
            start_timestamp: Optional[int]=None) -> types.Message:
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

        :param thumbnail: Thumbnail of the file sent; can be ignored if thumbnail generation for the file is supported server-side. The thumbnail should be in JPEG format and less than 200 kB in size.
            A thumbnail's width and height should not exceed 320. Ignored if the file is not uploaded using multipart/form-data. Thumbnails can't be reused and can be only uploaded as a new file,
            so you can pass “attach://<file_attach_name>” if the thumbnail was uploaded using multipart/form-data under <file_attach_name>.
        :type thumbnail: :obj:`str` or :class:`telebot.types.InputFile`

        :param cover: Cover for the video in the message. Pass a file_id to send a file that exists on the Telegram servers (recommended),
            pass an HTTP URL for Telegram to get a file from the Internet, or pass “attach://<file_attach_name>” to upload a new one using multipart/form-data under
            <file_attach_name> name. More information on Sending Files »
        :type cover: :obj:`str` or :class:`telebot.types.InputFile`

        :param start_timestamp: Start timestamp for the video in the message
        :type start_timestamp: :obj:`int`
        
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

        :param reply_to_message_id: deprecated.
        :type reply_to_message_id: :obj:`int`

        :param allow_sending_without_reply: deprecated.
        :type allow_sending_without_reply: :obj:`bool`

        :param reply_markup: Additional interface options. A JSON-serialized object for an inline keyboard, custom reply keyboard, instructions to remove reply keyboard
            or to force a reply from the user.
        :type reply_markup: :class:`telebot.types.InlineKeyboardMarkup` or :class:`telebot.types.ReplyKeyboardMarkup` or :class:`telebot.types.ReplyKeyboardRemove`
            or :class:`telebot.types.ForceReply`

        :param timeout: Timeout in seconds for the request.
        :type timeout: :obj:`int`

        :param data: function typo miss compatibility: do not use it
        :type data: :obj:`str`

        :param message_thread_id: Identifier of a message thread, in which the video will be sent
        :type message_thread_id: :obj:`int`

        :param has_spoiler: Pass True, if the video should be sent as a spoiler
        :type has_spoiler: :obj:`bool`

        :param thumb: deprecated.
        :type thumb: :obj:`str` or :class:`telebot.types.InputFile`

        :param reply_parameters: Reply parameters
        :type reply_parameters: :class:`telebot.types.ReplyParameters`

        :param business_connection_id: Identifier of a business connection
        :type business_connection_id: :obj:`str`

        :param message_effect_id: Identifier of a message effect
        :type message_effect_id: :obj:`str`

        :param show_caption_above_media: Pass True, if the caption must be shown above the message media. Supported only for animation, photo and video messages.
        :type show_caption_above_media: :obj:`bool`

        :param allow_paid_broadcast: Pass True to allow up to 1000 messages per second, ignoring broadcasting limits for a fee
            of 0.1 Telegram Stars per message. The relevant Stars will be withdrawn from the bot's balance
        :type allow_paid_broadcast: :obj:`bool`

        :return: On success, the sent Message is returned.
        :rtype: :class:`telebot.types.Message`
        """
        parse_mode = self.parse_mode if (parse_mode is None) else parse_mode
        disable_notification = self.disable_notification if (disable_notification is None) else disable_notification
        protect_content = self.protect_content if (protect_content is None) else protect_content

        if allow_sending_without_reply is not None:
            logger.warning("The parameter 'allow_sending_without_reply' is deprecated. Use 'reply_parameters' instead.")

        if reply_to_message_id:
            logger.warning("The parameter 'reply_to_message_id' is deprecated. Use 'reply_parameters' instead.")

            if reply_parameters:
                logger.warning("Both 'reply_parameters' and 'reply_to_message_id' parameters are set: conflicting, 'reply_to_message_id' is deprecated")
            else:
                # create a ReplyParameters object
                reply_parameters = types.ReplyParameters(
                    reply_to_message_id,
                    allow_sending_without_reply=self.allow_sending_without_reply if (allow_sending_without_reply is None) else allow_sending_without_reply
                )

        if reply_parameters and (reply_parameters.allow_sending_without_reply is None):
            reply_parameters.allow_sending_without_reply = self.allow_sending_without_reply

        if data and (not video):
            logger.warning('The parameter "data" is deprecated. Use "video" instead.')
            video = data

        if thumb is not None and thumbnail is None:
            logger.warning('The parameter "thumb" is deprecated. Use "thumbnail" instead.')
            thumbnail = thumb

        return types.Message.de_json(
            apihelper.send_video(
                self.token, chat_id, video,
                duration=duration, caption=caption, reply_markup=reply_markup, parse_mode=parse_mode,
                supports_streaming=supports_streaming, disable_notification=disable_notification, timeout=timeout,
                thumbnail=thumbnail, height=height, width=width, caption_entities=caption_entities,
                protect_content=protect_content, message_thread_id=message_thread_id, has_spoiler=has_spoiler,
                reply_parameters=reply_parameters, business_connection_id=business_connection_id, message_effect_id=message_effect_id,
                show_caption_above_media=show_caption_above_media, allow_paid_broadcast=allow_paid_broadcast,
                cover=cover, start_timestamp=start_timestamp)
        )


    def send_animation(
            self, chat_id: Union[int, str], animation: Union[Any, str], 
            duration: Optional[int]=None,
            width: Optional[int]=None,
            height: Optional[int]=None,
            thumbnail: Optional[Union[Any, str]]=None,
            caption: Optional[str]=None, 
            parse_mode: Optional[str]=None,
            caption_entities: Optional[List[types.MessageEntity]]=None,
            disable_notification: Optional[bool]=None,
            protect_content: Optional[bool]=None,
            reply_to_message_id: Optional[int]=None,          # deprecated, for backward compatibility
            allow_sending_without_reply: Optional[bool]=None, # deprecated, for backward compatibility
            reply_markup: Optional[REPLY_MARKUP_TYPES]=None, 
            timeout: Optional[int]=None,
            message_thread_id: Optional[int]=None,
            has_spoiler: Optional[bool]=None,
            thumb: Optional[Union[Any, str]]=None,
            reply_parameters: Optional[types.ReplyParameters]=None,
            business_connection_id: Optional[str]=None,
            message_effect_id: Optional[str]=None,
            show_caption_above_media: Optional[bool]=None,
            allow_paid_broadcast: Optional[bool]=None) -> types.Message:
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
        
        :param thumbnail: Thumbnail of the file sent; can be ignored if thumbnail generation for the file is supported server-side.
            The thumbnail should be in JPEG format and less than 200 kB in size. A thumbnail's width and height should not exceed 320.
            Ignored if the file is not uploaded using multipart/form-data. Thumbnails can't be reused and can be only uploaded as a new file,
            so you can pass “attach://<file_attach_name>” if the thumbnail was uploaded using multipart/form-data under <file_attach_name>.
        :type thumbnail: :obj:`str` or :class:`telebot.types.InputFile`

        :param caption: Animation caption (may also be used when resending animation by file_id), 0-1024 characters after entities parsing
        :type caption: :obj:`str`

        :param parse_mode: Mode for parsing entities in the animation caption
        :type parse_mode: :obj:`str`

        :param protect_content: Protects the contents of the sent message from forwarding and saving
        :type protect_content: :obj:`bool`

        :param reply_to_message_id: deprecated.
        :type reply_to_message_id: :obj:`int`

        :param allow_sending_without_reply: deprecated.
        :type allow_sending_without_reply: :obj:`bool`

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

        :param message_thread_id: Identifier of a message thread, in which the video will be sent
        :type message_thread_id: :obj:`int`

        :param has_spoiler: Pass True, if the animation should be sent as a spoiler
        :type has_spoiler: :obj:`bool`

        :param thumb: deprecated.
        :type thumb: :obj:`str` or :class:`telebot.types.InputFile`

        :param reply_parameters: Reply parameters.
        :type reply_parameters: :class:`telebot.types.ReplyParameters`

        :param business_connection_id: Identifier of a business connection
        :type business_connection_id: :obj:`str`

        :param message_effect_id: Unique identifier of the message effect to be added to the message; for private chats only
        :type message_effect_id: :obj:`str`

        :param show_caption_above_media: Pass True, if the caption must be shown above the message media. Supported only for animation, photo and video messages.
        :type show_caption_above_media: :obj:`bool`

        :param allow_paid_broadcast: Pass True to allow up to 1000 messages per second, ignoring broadcasting limits for a fee
            of 0.1 Telegram Stars per message. The relevant Stars will be withdrawn from the bot's balance
        :type allow_paid_broadcast: :obj:`bool`

        :return: On success, the sent Message is returned.
        :rtype: :class:`telebot.types.Message`
        """
        parse_mode = self.parse_mode if (parse_mode is None) else parse_mode
        disable_notification = self.disable_notification if (disable_notification is None) else disable_notification
        protect_content = self.protect_content if (protect_content is None) else protect_content

        if allow_sending_without_reply is not None:
            logger.warning("The parameter 'allow_sending_without_reply' is deprecated. Use 'reply_parameters' instead.")

        if reply_to_message_id:
            logger.warning("The parameter 'reply_to_message_id' is deprecated. Use 'reply_parameters' instead.")

            if reply_parameters:
                logger.warning("Both 'reply_parameters' and 'reply_to_message_id' parameters are set: conflicting, 'reply_to_message_id' is deprecated")
            else:
                # create a ReplyParameters object
                reply_parameters = types.ReplyParameters(
                    reply_to_message_id,
                    allow_sending_without_reply=self.allow_sending_without_reply if (allow_sending_without_reply is None) else allow_sending_without_reply
                )

        if reply_parameters and (reply_parameters.allow_sending_without_reply is None):
            reply_parameters.allow_sending_without_reply = self.allow_sending_without_reply

        if thumbnail is None and thumb is not None:
            logger.warning('The parameter "thumb" is deprecated. Use "thumbnail" instead.')
            thumbnail = thumb

        return types.Message.de_json(
            apihelper.send_animation(
                self.token, chat_id, animation, duration=duration, caption=caption, reply_markup=reply_markup,
                parse_mode=parse_mode, disable_notification=disable_notification, timeout=timeout,
                thumbnail=thumbnail, caption_entities=caption_entities, protect_content=protect_content,
                width=width, height=height, message_thread_id=message_thread_id, reply_parameters=reply_parameters,
                has_spoiler=has_spoiler, business_connection_id=business_connection_id, message_effect_id=message_effect_id,
                show_caption_above_media=show_caption_above_media, allow_paid_broadcast=allow_paid_broadcast)
            )


    def send_video_note(
            self, chat_id: Union[int, str], data: Union[Any, str], 
            duration: Optional[int]=None, 
            length: Optional[int]=None,
            reply_to_message_id: Optional[int]=None,          # deprecated, for backward compatibility
            reply_markup: Optional[REPLY_MARKUP_TYPES]=None,
            disable_notification: Optional[bool]=None, 
            timeout: Optional[int]=None, 
            thumbnail: Optional[Union[Any, str]]=None,
            allow_sending_without_reply: Optional[bool]=None, # deprecated, for backward compatibility
            protect_content: Optional[bool]=None,
            message_thread_id: Optional[int]=None,
            thumb: Optional[Union[Any, str]]=None,
            reply_parameters: Optional[types.ReplyParameters]=None,
            business_connection_id: Optional[str]=None,
            message_effect_id: Optional[str]=None,
            allow_paid_broadcast: Optional[bool]=None) -> types.Message:
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

        :param reply_markup: Additional interface options. A JSON-serialized object for an inline keyboard, custom reply keyboard, instructions to remove reply keyboard
            or to force a reply from the user.
        :type reply_markup: :class:`telebot.types.InlineKeyboardMarkup` or :class:`telebot.types.ReplyKeyboardMarkup` or :class:`telebot.types.ReplyKeyboardRemove`
            or :class:`telebot.types.ForceReply`

        :param disable_notification: Sends the message silently. Users will receive a notification with no sound.
        :type disable_notification: :obj:`bool`

        :param reply_to_message_id: deprecated.
        :type reply_to_message_id: :obj:`int`

        :param allow_sending_without_reply: deprecated.
        :type allow_sending_without_reply: :obj:`bool`

        :param timeout: Timeout in seconds for the request.
        :type timeout: :obj:`int`

        :param thumbnail: Thumbnail of the file sent; can be ignored if thumbnail generation for the file is supported server-side.
            The thumbnail should be in JPEG format and less than 200 kB in size. A thumbnail's width and height should not exceed 320.
            Ignored if the file is not uploaded using multipart/form-data. Thumbnails can't be reused and can be only uploaded as a new file,
            so you can pass “attach://<file_attach_name>” if the thumbnail was uploaded using multipart/form-data under <file_attach_name>. 
        :type thumbnail: :obj:`str` or :class:`telebot.types.InputFile`

        :param protect_content: Protects the contents of the sent message from forwarding and saving
        :type protect_content: :obj:`bool`

        :param message_thread_id: Identifier of a message thread, in which the video note will be sent
        :type message_thread_id: :obj:`int`

        :param thumb: deprecated.
        :type thumb: :obj:`str` or :class:`telebot.types.InputFile`

        :param reply_parameters: Reply parameters.
        :type reply_parameters: :class:`telebot.types.ReplyParameters`

        :param business_connection_id: Identifier of a business connection, in which the message will be sent
        :type business_connection_id: :obj:`str`

        :param message_effect_id: Unique identifier of the message effect to be added to the message; for private chats only
        :type message_effect_id: :obj:`str`

        :param allow_paid_broadcast: Pass True to allow up to 1000 messages per second, ignoring broadcasting limits for a fee
            of 0.1 Telegram Stars per message. The relevant Stars will be withdrawn from the bot's balance
        :type allow_paid_broadcast: :obj:`bool`

        :return: On success, the sent Message is returned.
        :rtype: :class:`telebot.types.Message`
        """
        disable_notification = self.disable_notification if (disable_notification is None) else disable_notification
        protect_content = self.protect_content if (protect_content is None) else protect_content

        if allow_sending_without_reply is not None:
            logger.warning("The parameter 'allow_sending_without_reply' is deprecated. Use 'reply_parameters' instead.")

        if reply_to_message_id:
            logger.warning("The parameter 'reply_to_message_id' is deprecated. Use 'reply_parameters' instead.")

            if reply_parameters:
                logger.warning("Both 'reply_parameters' and 'reply_to_message_id' parameters are set: conflicting, 'reply_to_message_id' is deprecated")
            else:
                # create a ReplyParameters object
                reply_parameters = types.ReplyParameters(
                    reply_to_message_id,
                    allow_sending_without_reply=self.allow_sending_without_reply if (allow_sending_without_reply is None) else allow_sending_without_reply
                )

        if reply_parameters and (reply_parameters.allow_sending_without_reply is None):
            reply_parameters.allow_sending_without_reply = self.allow_sending_without_reply

        if thumbnail is None and thumb is not None:
            logger.warning('The parameter "thumb" is deprecated. Use "thumbnail" instead.')
            thumbnail = thumb

        return types.Message.de_json(
            apihelper.send_video_note(
                self.token, chat_id, data, duration=duration, length=length, reply_markup=reply_markup,
                disable_notification=disable_notification, timeout=timeout, thumbnail=thumbnail,
                protect_content=protect_content, message_thread_id=message_thread_id, reply_parameters=reply_parameters,
                business_connection_id=business_connection_id, message_effect_id=message_effect_id, allow_paid_broadcast=allow_paid_broadcast)
        )
    
    def send_paid_media(
            self, chat_id: Union[int, str], star_count: int, media: List[types.InputPaidMedia],
            caption: Optional[str]=None, parse_mode: Optional[str]=None, caption_entities: Optional[List[types.MessageEntity]]=None,
            show_caption_above_media: Optional[bool]=None, disable_notification: Optional[bool]=None,
            protect_content: Optional[bool]=None, reply_parameters: Optional[types.ReplyParameters]=None,
            reply_markup: Optional[REPLY_MARKUP_TYPES]=None, business_connection_id: Optional[str]=None,
            payload: Optional[str]=None, allow_paid_broadcast: Optional[bool]=None
    ) -> types.Message:
        """
        Use this method to send paid media to channel chats. On success, the sent Message is returned.

        Telegram documentation: https://core.telegram.org/bots/api#sendpaidmedia

        :param chat_id: Unique identifier for the target chat or username of the target channel (in the format @channelusername)
        :type chat_id: :obj:`int` or :obj:`str`

        :param star_count: The number of Telegram Stars that must be paid to buy access to the media
        :type star_count: :obj:`int`

        :param media: A JSON-serialized array describing the media to be sent; up to 10 items
        :type media: :obj:`list` of :class:`telebot.types.InputPaidMedia`

        :param caption: Media caption, 0-1024 characters after entities parsing
        :type caption: :obj:`str`

        :param parse_mode: Mode for parsing entities in the media caption
        :type parse_mode: :obj:`str`

        :param caption_entities: List of special entities that appear in the caption, which can be specified instead of parse_mode
        :type caption_entities: :obj:`list` of :class:`telebot.types.MessageEntity`

        :param show_caption_above_media: Pass True, if the caption must be shown above the message media
        :type show_caption_above_media: :obj:`bool`

        :param disable_notification: Sends the message silently. Users will receive a notification with no sound.
        :type disable_notification: :obj:`bool`

        :param protect_content: Protects the contents of the sent message from forwarding and saving
        :type protect_content: :obj:`bool`

        :param reply_parameters: Description of the message to reply to
        :type reply_parameters: :class:`telebot.types.ReplyParameters`

        :param reply_markup: Additional interface options. A JSON-serialized object for an inline keyboard, custom reply keyboard, instructions to remove a reply keyboard or to force a reply from the user
        :type reply_markup: :class:`telebot.types.InlineKeyboardMarkup` or :class:`telebot.types.ReplyKeyboardMarkup` or :class:`telebot.types.ReplyKeyboardRemove` or :class:`telebot.types.ForceReply`

        :param business_connection_id: Identifier of a business connection, in which the message will be sent
        :type business_connection_id: :obj:`str`

        :param payload: Bot-defined paid media payload, 0-128 bytes. This will not be displayed to the user, use it for your internal processes.
        :type payload: :obj:`str`

        :param allow_paid_broadcast: Pass True to allow up to 1000 messages per second, ignoring broadcasting limits for a fee
            of 0.1 Telegram Stars per message. The relevant Stars will be withdrawn from the bot's balance
        :type allow_paid_broadcast: :obj:`bool`

        :return: On success, the sent Message is returned.
        :rtype: :class:`telebot.types.Message`
        """
        return types.Message.de_json(
            apihelper.send_paid_media(
                self.token, chat_id, star_count, media, caption=caption, parse_mode=parse_mode,
                caption_entities=caption_entities, show_caption_above_media=show_caption_above_media,
                disable_notification=disable_notification, protect_content=protect_content,
                reply_parameters=reply_parameters, reply_markup=reply_markup, business_connection_id=business_connection_id,
                payload=payload, allow_paid_broadcast=allow_paid_broadcast)
        )


    def send_media_group(
            self, chat_id: Union[int, str], 
            media: List[Union[
                types.InputMediaAudio, types.InputMediaDocument, 
                types.InputMediaPhoto, types.InputMediaVideo]],
            disable_notification: Optional[bool]=None, 
            protect_content: Optional[bool]=None,
            reply_to_message_id: Optional[int]=None,          # deprecated, for backward compatibility
            timeout: Optional[int]=None,
            allow_sending_without_reply: Optional[bool]=None, # deprecated, for backward compatibility
            message_thread_id: Optional[int]=None,
            reply_parameters: Optional[types.ReplyParameters]=None,
            business_connection_id: Optional[str]=None,
            message_effect_id: Optional[str]=None,
            allow_paid_broadcast: Optional[bool]=None) -> List[types.Message]:
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

        :param reply_to_message_id: deprecated.
        :type reply_to_message_id: :obj:`int`

        :param allow_sending_without_reply: deprecated.
        :type allow_sending_without_reply: :obj:`bool`

        :param timeout: Timeout in seconds for the request.
        :type timeout: :obj:`int`

        :param message_thread_id: Identifier of a message thread, in which the media group will be sent
        :type message_thread_id: :obj:`int`

        :param reply_parameters: Reply parameters.
        :type reply_parameters: :class:`telebot.types.ReplyParameters`

        :param business_connection_id: Identifier of a business connection, in which the message will be sent
        :type business_connection_id: :obj:`str`

        :param message_effect_id: Unique identifier of the message effect to be added to the message; for private chats only
        :type message_effect_id: :obj:`str`

        :param allow_paid_broadcast: Pass True to allow up to 1000 messages per second, ignoring broadcasting limits for a fee
            of 0.1 Telegram Stars per message. The relevant Stars will be withdrawn from the bot's balance
        :type allow_paid_broadcast: :obj:`bool`

        :return: On success, an array of Messages that were sent is returned.
        :rtype: List[types.Message]
        """
        if media:
            # Pass default parse mode to Media items
            for media_item in media:
                if media_item.parse_mode is None:
                    media_item.parse_mode = self.parse_mode

        disable_notification = self.disable_notification if (disable_notification is None) else disable_notification
        protect_content = self.protect_content if (protect_content is None) else protect_content

        if allow_sending_without_reply is not None:
            logger.warning("The parameter 'allow_sending_without_reply' is deprecated. Use 'reply_parameters' instead.")

        if reply_to_message_id:
            logger.warning("The parameter 'reply_to_message_id' is deprecated. Use 'reply_parameters' instead.")

            if reply_parameters:
                logger.warning("Both 'reply_parameters' and 'reply_to_message_id' parameters are set: conflicting, 'reply_to_message_id' is deprecated")
            else:
                # create a ReplyParameters object
                reply_parameters = types.ReplyParameters(
                    reply_to_message_id,
                    allow_sending_without_reply=self.allow_sending_without_reply if (allow_sending_without_reply is None) else allow_sending_without_reply
                )

        if reply_parameters and (reply_parameters.allow_sending_without_reply is None):
            reply_parameters.allow_sending_without_reply = self.allow_sending_without_reply

        result = apihelper.send_media_group(
            self.token, chat_id, media, disable_notification=disable_notification, timeout=timeout,
            protect_content=protect_content, message_thread_id=message_thread_id, reply_parameters=reply_parameters,
            business_connection_id=business_connection_id, message_effect_id=message_effect_id, allow_paid_broadcast=allow_paid_broadcast)
        return [types.Message.de_json(msg) for msg in result]


    def send_location(
            self, chat_id: Union[int, str], 
            latitude: float, longitude: float, 
            live_period: Optional[int]=None,
            reply_to_message_id: Optional[int]=None,          # deprecated, for backward compatibility 
            reply_markup: Optional[REPLY_MARKUP_TYPES]=None, 
            disable_notification: Optional[bool]=None, 
            timeout: Optional[int]=None,
            horizontal_accuracy: Optional[float]=None, 
            heading: Optional[int]=None, 
            proximity_alert_radius: Optional[int]=None,
            allow_sending_without_reply: Optional[bool]=None, # deprecated, for backward compatibility 
            protect_content: Optional[bool]=None,
            message_thread_id: Optional[int]=None,
            reply_parameters: Optional[types.ReplyParameters]=None,
            business_connection_id: Optional[str]=None,
            message_effect_id: Optional[str]=None,
            allow_paid_broadcast: Optional[bool]=None) -> types.Message:
        """
        Use this method to send point on the map. On success, the sent Message is returned.

        Telegram documentation: https://core.telegram.org/bots/api#sendlocation

        :param chat_id: Unique identifier for the target chat or username of the target channel (in the format @channelusername)
        :type chat_id: :obj:`int` or :obj:`str`

        :param latitude: Latitude of the location
        :type latitude: :obj:`float`

        :param longitude: Longitude of the location
        :type longitude: :obj:`float`

        :param live_period: Period in seconds during which the location will be updated (see Live Locations, should be between 60 and 86400, or 0x7FFFFFFF for live locations that can be edited indefinitely.
        :type live_period: :obj:`int`

        :param reply_markup: Additional interface options. A JSON-serialized object for an inline keyboard, custom reply keyboard, instructions to remove reply keyboard
            or to force a reply from the user.
        :type reply_markup: :class:`telebot.types.InlineKeyboardMarkup` or :class:`telebot.types.ReplyKeyboardMarkup` or :class:`telebot.types.ReplyKeyboardRemove`
            or :class:`telebot.types.ForceReply`

        :param disable_notification: Sends the message silently. Users will receive a notification with no sound.
        :type disable_notification: :obj:`bool`

        :param reply_to_message_id: deprecated.
        :type reply_to_message_id: :obj:`int`

        :param allow_sending_without_reply: deprecated.
        :type allow_sending_without_reply: :obj:`bool`

        :param timeout: Timeout in seconds for the request.
        :type timeout: :obj:`int`

        :param horizontal_accuracy: The radius of uncertainty for the location, measured in meters; 0-1500
        :type horizontal_accuracy: :obj:`float`

        :param heading: For live locations, a direction in which the user is moving, in degrees. Must be between 1 and 360 if specified.
        :type heading: :obj:`int`

        :param proximity_alert_radius: For live locations, a maximum distance for proximity alerts about approaching another chat member, in meters. Must be between 1 and 100000 if specified.
        :type proximity_alert_radius: :obj:`int`

        :param protect_content: Protects the contents of the sent message from forwarding and saving
        :type protect_content: :obj:`bool`

        :param message_thread_id: Identifier of a message thread, in which the message will be sent
        :type message_thread_id: :obj:`int`

        :param reply_parameters: Reply parameters.
        :type reply_parameters: :class:`telebot.types.ReplyParameters`

        :param business_connection_id: Identifier of a business connection, in which the message will be sent
        :type business_connection_id: :obj:`str`

        :parameter message_effect_id: Unique identifier of the message effect to be added to the message; for private chats only
        :type message_effect_id: :obj:`str`

        :param allow_paid_broadcast: Pass True to allow up to 1000 messages per second, ignoring broadcasting limits for a fee
            of 0.1 Telegram Stars per message. The relevant Stars will be withdrawn from the bot's balance
        :type allow_paid_broadcast: :obj:`bool`

        :return: On success, the sent Message is returned.
        :rtype: :class:`telebot.types.Message`
        """
        disable_notification = self.disable_notification if (disable_notification is None) else disable_notification
        protect_content = self.protect_content if (protect_content is None) else protect_content

        if allow_sending_without_reply is not None:
            logger.warning("The parameter 'allow_sending_without_reply' is deprecated. Use 'reply_parameters' instead.")

        if reply_to_message_id:
            logger.warning("The parameter 'reply_to_message_id' is deprecated. Use 'reply_parameters' instead.")

            if reply_parameters:
                logger.warning("Both 'reply_parameters' and 'reply_to_message_id' parameters are set: conflicting, 'reply_to_message_id' is deprecated")
            else:
                # create a ReplyParameters object
                reply_parameters = types.ReplyParameters(
                    reply_to_message_id,
                    allow_sending_without_reply=self.allow_sending_without_reply if (allow_sending_without_reply is None) else allow_sending_without_reply
                )

        if reply_parameters and (reply_parameters.allow_sending_without_reply is None):
            reply_parameters.allow_sending_without_reply = self.allow_sending_without_reply

        return types.Message.de_json(
            apihelper.send_location(
                self.token, chat_id, latitude, longitude, live_period=live_period, reply_markup=reply_markup,
                disable_notification=disable_notification, timeout=timeout, horizontal_accuracy=horizontal_accuracy,
                heading=heading, proximity_alert_radius=proximity_alert_radius, protect_content=protect_content,
                message_thread_id=message_thread_id, reply_parameters=reply_parameters, business_connection_id=business_connection_id,
                message_effect_id=message_effect_id, allow_paid_broadcast=allow_paid_broadcast)
            )


    def edit_message_live_location(
            self, latitude: float, longitude: float, 
            chat_id: Optional[Union[int, str]]=None, 
            message_id: Optional[int]=None,
            inline_message_id: Optional[str]=None, 
            reply_markup: Optional[types.InlineKeyboardMarkup]=None,
            timeout: Optional[int]=None,
            horizontal_accuracy: Optional[float]=None, 
            heading: Optional[int]=None, 
            proximity_alert_radius: Optional[int]=None,
            live_period: Optional[int]=None,
            business_connection_id: Optional[str]=None
    ) -> types.Message or bool:
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

        :param live_period: New period in seconds during which the location can be updated, starting from the message send date. If 0x7FFFFFFF is specified, then the location can be updated forever. Otherwise, the new value must not exceed the current live_period by more than a day, and the live location expiration date must remain within the next 90 days. If not specified, then live_period remains unchanged
        :type live_period: :obj:`int`

        :param business_connection_id: Identifier of a business connection
        :type business_connection_id: :obj:`str`

        :return: On success, if the edited message is not an inline message, the edited Message is returned, otherwise True is returned.
        :rtype: :class:`telebot.types.Message` or bool
        """
        return types.Message.de_json(
            apihelper.edit_message_live_location(
                self.token, latitude, longitude, chat_id=chat_id, message_id=message_id, inline_message_id=inline_message_id,
                reply_markup=reply_markup, timeout=timeout, horizontal_accuracy=horizontal_accuracy, heading=heading,
                proximity_alert_radius=proximity_alert_radius, live_period=live_period, business_connection_id=business_connection_id)
            )


    def stop_message_live_location(
            self, chat_id: Optional[Union[int, str]]=None, 
            message_id: Optional[int]=None,
            inline_message_id: Optional[str]=None, 
            reply_markup: Optional[types.InlineKeyboardMarkup]=None,
            timeout: Optional[int]=None,
            business_connection_id: Optional[str]=None) -> types.Message or bool:
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

        :param business_connection_id: Identifier of a business connection
        :type business_connection_id: :obj:`str`

        :return: On success, if the message is not an inline message, the edited Message is returned, otherwise True is returned.
        :rtype: :class:`telebot.types.Message` or bool
        """
        return types.Message.de_json(
            apihelper.stop_message_live_location(
                self.token, chat_id=chat_id, message_id=message_id, inline_message_id=inline_message_id,
                reply_markup=reply_markup, timeout=timeout, business_connection_id=business_connection_id)
        )


    def send_venue(
            self, chat_id: Union[int, str], 
            latitude: Optional[float], longitude: Optional[float], 
            title: str, address: str, 
            foursquare_id: Optional[str]=None, 
            foursquare_type: Optional[str]=None,
            disable_notification: Optional[bool]=None, 
            reply_to_message_id: Optional[int]=None,          # deprecated, for backward compatibility
            reply_markup: Optional[REPLY_MARKUP_TYPES]=None, 
            timeout: Optional[int]=None,
            allow_sending_without_reply: Optional[bool]=None, # deprecated, for backward compatibility
            google_place_id: Optional[str]=None,
            google_place_type: Optional[str]=None,
            protect_content: Optional[bool]=None,
            message_thread_id: Optional[int]=None,
            reply_parameters: Optional[types.ReplyParameters]=None,
            business_connection_id: Optional[str]=None,
            message_effect_id: Optional[str]=None,
            allow_paid_broadcast: Optional[bool]=None) -> types.Message:
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

        :param reply_to_message_id: deprecated.
        :type reply_to_message_id: :obj:`int`

        :param allow_sending_without_reply: deprecated.
        :type allow_sending_without_reply: :obj:`bool`

        :param reply_markup: Additional interface options. A JSON-serialized object for an inline keyboard,
            custom reply keyboard, instructions to remove reply keyboard or to force a reply from the user.
        :type reply_markup: :class:`telebot.types.InlineKeyboardMarkup` or :class:`telebot.types.ReplyKeyboardMarkup` or :class:`telebot.types.ReplyKeyboardRemove`
            or :class:`telebot.types.ForceReply`

        :param timeout: Timeout in seconds for the request.
        :type timeout: :obj:`int`

        :param google_place_id: Google Places identifier of the venue
        :type google_place_id: :obj:`str`

        :param google_place_type: Google Places type of the venue.
        :type google_place_type: :obj:`str`

        :param protect_content: Protects the contents of the sent message from forwarding and saving
        :type protect_content: :obj:`bool`

        :param message_thread_id: The thread identifier of a message from which the reply will be sent
        :type message_thread_id: :obj:`int`

        :param reply_parameters: Reply parameters.
        :type reply_parameters: :class:`telebot.types.ReplyParameters`

        :param business_connection_id: Identifier of a business connection
        :type business_connection_id: :obj:`str`

        :param message_effect_id: Unique identifier of the message effect to be added to the message; for private chats only
        :type message_effect_id: :obj:`str`

        :param allow_paid_broadcast: Pass True to allow up to 1000 messages per second, ignoring broadcasting limits for a fee
            of 0.1 Telegram Stars per message. The relevant Stars will be withdrawn from the bot's balance
        :type allow_paid_broadcast: :obj:`bool`

        :return: On success, the sent Message is returned.
        :rtype: :class:`telebot.types.Message`
        """
        disable_notification = self.disable_notification if (disable_notification is None) else disable_notification
        protect_content = self.protect_content if (protect_content is None) else protect_content

        if allow_sending_without_reply is not None:
            logger.warning("The parameter 'allow_sending_without_reply' is deprecated. Use 'reply_parameters' instead.")

        if reply_to_message_id:
            logger.warning("The parameter 'reply_to_message_id' is deprecated. Use 'reply_parameters' instead.")

            if reply_parameters:
                logger.warning("Both 'reply_parameters' and 'reply_to_message_id' parameters are set: conflicting, 'reply_to_message_id' is deprecated")
            else:
                # create a ReplyParameters object
                reply_parameters = types.ReplyParameters(
                    reply_to_message_id,
                    allow_sending_without_reply=self.allow_sending_without_reply if (allow_sending_without_reply is None) else allow_sending_without_reply
                )

        if reply_parameters and (reply_parameters.allow_sending_without_reply is None):
            reply_parameters.allow_sending_without_reply = self.allow_sending_without_reply

        return types.Message.de_json(
            apihelper.send_venue(
                self.token, chat_id, latitude, longitude, title, address, foursquare_id=foursquare_id,
                foursquare_type=foursquare_type, disable_notification=disable_notification, reply_markup=reply_markup,
                timeout=timeout, google_place_id=google_place_id, google_place_type=google_place_type,
                protect_content=protect_content, message_thread_id=message_thread_id, reply_parameters=reply_parameters, business_connection_id=business_connection_id,
                message_effect_id=message_effect_id, allow_paid_broadcast=allow_paid_broadcast)
            )


    def send_contact(
            self, chat_id: Union[int, str], phone_number: str, 
            first_name: str, last_name: Optional[str]=None, 
            vcard: Optional[str]=None,
            disable_notification: Optional[bool]=None, 
            reply_to_message_id: Optional[int]=None,          # deprecated, for backward compatibility
            reply_markup: Optional[REPLY_MARKUP_TYPES]=None, 
            timeout: Optional[int]=None,
            allow_sending_without_reply: Optional[bool]=None, # deprecated, for backward compatibility
            protect_content: Optional[bool]=None, message_thread_id: Optional[int]=None,
            reply_parameters: Optional[types.ReplyParameters]=None,
            business_connection_id: Optional[str]=None,
            message_effect_id: Optional[str]=None,
            allow_paid_broadcast: Optional[bool]=None) -> types.Message:
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

        :param reply_to_message_id: deprecated.
        :type reply_to_message_id: :obj:`int`

        :param allow_sending_without_reply: deprecated.
        :type allow_sending_without_reply: :obj:`bool`

        :param reply_markup: Additional interface options. A JSON-serialized object for an inline keyboard,
            custom reply keyboard, instructions to remove reply keyboard or to force a reply from the user.
        :type reply_markup: :class:`telebot.types.InlineKeyboardMarkup` or :class:`telebot.types.ReplyKeyboardMarkup` or :class:`telebot.types.ReplyKeyboardRemove`
            or :class:`telebot.types.ForceReply`

        :param timeout: Timeout in seconds for the request.
        :type timeout: :obj:`int`

        :param protect_content: Protects the contents of the sent message from forwarding and saving
        :type protect_content: :obj:`bool`

        :param message_thread_id: The thread identifier of a message from which the reply will be sent
        :type message_thread_id: :obj:`int`

        :param reply_parameters: Reply parameters.
        :type reply_parameters: :class:`telebot.types.ReplyParameters`

        :param business_connection_id: Identifier of a business connection
        :type business_connection_id: :obj:`str`

        :param message_effect_id: Unique identifier of the message effect to be added to the message; for private chats only
        :type message_effect_id: :obj:`str`

        :param allow_paid_broadcast: Pass True to allow up to 1000 messages per second, ignoring broadcasting limits for a fee
            of 0.1 Telegram Stars per message. The relevant Stars will be withdrawn from the bot's balance
        :type allow_paid_broadcast: :obj:`bool`

        :return: On success, the sent Message is returned.
        :rtype: :class:`telebot.types.Message`
        """
        disable_notification = self.disable_notification if (disable_notification is None) else disable_notification
        protect_content = self.protect_content if (protect_content is None) else protect_content

        if allow_sending_without_reply is not None:
            logger.warning("The parameter 'allow_sending_without_reply' is deprecated. Use 'reply_parameters' instead.")

        if reply_to_message_id:
            logger.warning("The parameter 'reply_to_message_id' is deprecated. Use 'reply_parameters' instead.")

            if reply_parameters:
                logger.warning("Both 'reply_parameters' and 'reply_to_message_id' parameters are set: conflicting, 'reply_to_message_id' is deprecated")
            else:
                # create a ReplyParameters object
                reply_parameters = types.ReplyParameters(
                    reply_to_message_id,
                    allow_sending_without_reply=self.allow_sending_without_reply if (allow_sending_without_reply is None) else allow_sending_without_reply
                )

        if reply_parameters and (reply_parameters.allow_sending_without_reply is None):
            reply_parameters.allow_sending_without_reply = self.allow_sending_without_reply

        return types.Message.de_json(
            apihelper.send_contact(
                self.token, chat_id, phone_number, first_name, last_name=last_name, vcard=vcard,
                disable_notification=disable_notification, reply_markup=reply_markup, timeout=timeout,
                protect_content=protect_content, message_thread_id=message_thread_id, reply_parameters=reply_parameters,
                business_connection_id=business_connection_id, message_effect_id=message_effect_id, allow_paid_broadcast=allow_paid_broadcast)
            )


    def send_chat_action(
            self, chat_id: Union[int, str], action: str, timeout: Optional[int]=None, message_thread_id: Optional[int]=None,
            business_connection_id: Optional[str]=None) -> bool:
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

        :param message_thread_id: The thread identifier of a message from which the reply will be sent(supergroups only)
        :type message_thread_id: :obj:`int`

        :param business_connection_id: Identifier of a business connection
        :type business_connection_id: :obj:`str`

        :return: Returns True on success.
        :rtype: :obj:`bool`
        """
        return apihelper.send_chat_action(
            self.token, chat_id, action, timeout=timeout, message_thread_id=message_thread_id, business_connection_id=business_connection_id)

    
    @util.deprecated(deprecation_text="Use ban_chat_member instead")
    def kick_chat_member(
            self, chat_id: Union[int, str], user_id: int, 
            until_date:Optional[Union[int, datetime]]=None, 
            revoke_messages: Optional[bool]=None) -> bool:
        """
        This function is deprecated. Use `ban_chat_member` instead.
        """
        return apihelper.ban_chat_member(
            self.token, chat_id, user_id, until_date=until_date, revoke_messages=revoke_messages)


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

        :param revoke_messages: Pass True to delete all messages from the chat for the user that is being removed.
            If False, the user will be able to see messages in the group that were sent before the user was removed. 
            Always True for supergroups and channels.
        :type revoke_messages: :obj:`bool`
        
        :return: Returns True on success.
        :rtype: :obj:`bool`
        """
        return apihelper.ban_chat_member(
            self.token, chat_id, user_id, until_date=until_date, revoke_messages=revoke_messages)


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
            can_pin_messages: Optional[bool]=None,
            permissions: Optional[types.ChatPermissions]=None,
            use_independent_chat_permissions: Optional[bool]=None) -> bool:
        """
        Use this method to restrict a user in a supergroup.
        The bot must be an administrator in the supergroup for this to work and must have
        the appropriate admin rights. Pass True for all boolean parameters to lift restrictions from a user.

        Telegram documentation: https://core.telegram.org/bots/api#restrictchatmember

        .. warning::
            Individual parameters are deprecated and will be removed, use 'permissions' instead.

        :param chat_id: Unique identifier for the target group or username of the target supergroup
            or channel (in the format @channelusername)
        :type chat_id: :obj:`int` or :obj:`str`

        :param user_id: Unique identifier of the target user
        :type user_id: :obj:`int`

        :param until_date: Date when restrictions will be lifted for the user, unix time.
            If user is restricted for more than 366 days or less than 30 seconds from the current time,
            they are considered to be restricted forever
        :type until_date: :obj:`int` or :obj:`datetime`, optional

        :param can_send_messages: deprecated
        :type can_send_messages: :obj:`bool`
        
        :param can_send_media_messages: deprecated
        :type can_send_media_messages: :obj:`bool`
        
        :param can_send_polls: deprecated
        :type can_send_polls: :obj:`bool`

        :param can_send_other_messages: deprecated
        :type can_send_other_messages: :obj:`bool`

        :param can_add_web_page_previews: deprecated
        :type can_add_web_page_previews: :obj:`bool`

        :param can_change_info: deprecated
        :type can_change_info: :obj:`bool`

        :param can_invite_users: deprecated
        :type can_invite_users: :obj:`bool`

        :param can_pin_messages: deprecated
        :type can_pin_messages: :obj:`bool`

        :param use_independent_chat_permissions: Pass True if chat permissions are set independently.
            Otherwise, the can_send_other_messages and can_add_web_page_previews permissions will imply the can_send_messages,
            can_send_audios, can_send_documents, can_send_photos, can_send_videos, can_send_video_notes, and can_send_voice_notes
            permissions; the can_send_polls permission will imply the can_send_messages permission.
        :type use_independent_chat_permissions: :obj:`bool`, optional

        :param permissions: ChatPermissions object defining permissions.
        :type permissions: :class:`telebot.types.ChatPermissions`

        :return: True on success
        :rtype: :obj:`bool`
        """
        if permissions is None:
            logger.warning('The parameters "can_..." are deprecated, use "permissions" instead.')
            permissions = types.ChatPermissions(
                can_send_messages=can_send_messages,
                can_send_media_messages=can_send_media_messages,
                can_send_polls=can_send_polls,
                can_send_other_messages=can_send_other_messages,
                can_add_web_page_previews=can_add_web_page_previews,
                can_change_info=can_change_info,
                can_invite_users=can_invite_users,
                can_pin_messages=can_pin_messages
            )

        return apihelper.restrict_chat_member(
            self.token, chat_id, user_id, permissions, until_date=until_date,
            use_independent_chat_permissions=use_independent_chat_permissions)


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
            can_manage_voice_chats: Optional[bool]=None,
            can_manage_topics: Optional[bool]=None,
            can_post_stories: Optional[bool]=None,
            can_edit_stories: Optional[bool]=None,
            can_delete_stories: Optional[bool]=None) -> bool:
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

        :param can_manage_topics: Pass True if the user is allowed to create, rename, close,
            and reopen forum topics, supergroups only
        :type can_manage_topics: :obj:`bool`

        :param can_post_stories: Pass True if the administrator can create the channel's stories
        :type can_post_stories: :obj:`bool`

        :param can_edit_stories: Pass True if the administrator can edit the channel's stories
        :type can_edit_stories: :obj:`bool`

        :param can_delete_stories: Pass True if the administrator can delete the channel's stories
        :type can_delete_stories: :obj:`bool`

        :return: True on success.
        :rtype: :obj:`bool`
        """
        if can_manage_voice_chats is not None:
            logger.warning('The parameter "can_manage_voice_chats" is deprecated. Use "can_manage_video_chats" instead.')
            if can_manage_video_chats is None:
                can_manage_video_chats = can_manage_voice_chats

        return apihelper.promote_chat_member(
            self.token, chat_id, user_id, can_change_info=can_change_info, can_post_messages=can_post_messages,
            can_edit_messages=can_edit_messages, can_delete_messages=can_delete_messages,
            can_invite_users=can_invite_users, can_restrict_members=can_restrict_members,
            can_pin_messages=can_pin_messages, can_promote_members=can_promote_members,
            is_anonymous=is_anonymous, can_manage_chat=can_manage_chat,
            can_manage_video_chats=can_manage_video_chats, can_manage_topics=can_manage_topics,
            can_post_stories=can_post_stories, can_edit_stories=can_edit_stories,
            can_delete_stories=can_delete_stories)


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
            self, chat_id: Union[int, str], permissions: types.ChatPermissions,
            use_independent_chat_permissions: Optional[bool]=None) -> bool:
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

        :param use_independent_chat_permissions: Pass True if chat permissions are set independently. Otherwise,
            the can_send_other_messages and can_add_web_page_previews permissions will imply the can_send_messages,
            can_send_audios, can_send_documents, can_send_photos, can_send_videos, can_send_video_notes, and
            can_send_voice_notes permissions; the can_send_polls permission will imply the can_send_messages permission.
        :type use_independent_chat_permissions: :obj:`bool`

        :return: True on success
        :rtype: :obj:`bool`
        """
        return apihelper.set_chat_permissions(
            self.token, chat_id, permissions, use_independent_chat_permissions=use_independent_chat_permissions)


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
            apihelper.edit_chat_invite_link(self.token, chat_id, invite_link, name, expire_date, member_limit, creates_join_request)
        )

    def create_chat_subscription_invite_link(
            self, chat_id: Union[int, str], subscription_period: int, subscription_price: int,
            name: Optional[str]=None) -> types.ChatInviteLink:
        """
        Use this method to create a subscription invite link for a channel chat. The bot must have the can_invite_users administrator rights.
        The link can be edited using the method editChatSubscriptionInviteLink or revoked using the method revokeChatInviteLink.
        Returns the new invite link as a ChatInviteLink object.

        Telegram documentation: https://core.telegram.org/bots/api#createchatsubscriptioninvitelink

        :param chat_id: Unique identifier for the target channel chat or username of the target channel
            (in the format @channelusername)
        :type chat_id: :obj:`int` or :obj:`str`
        
        :param name: Invite link name; 0-32 characters
        :type name: :obj:`str`

        :param subscription_period: The number of seconds the subscription will be active for before the next payment.
            Currently, it must always be 2592000 (30 days).
        :type subscription_period: :obj:`int`

        :param subscription_price: The amount of Telegram Stars a user must pay initially and after each subsequent
            subscription period to be a member of the chat; 1-2500
        :type subscription_price: :obj:`int`

        :return: Returns the new invite link as a ChatInviteLink object.
        :rtype: :class:`telebot.types.ChatInviteLink`
        """
        return types.ChatInviteLink.de_json(
            apihelper.create_chat_subscription_invite_link(self.token, chat_id, subscription_period, subscription_price, name=name)
        )
    
    def edit_chat_subscription_invite_link(
            self, chat_id: Union[int, str], invite_link: str, name: Optional[str]=None) -> types.ChatInviteLink:
        """
        Use this method to edit a subscription invite link created by the bot. The bot must have the can_invite_users administrator rights.
        Returns the edited invite link as a ChatInviteLink object.

        Telegram documentation: https://core.telegram.org/bots/api#editchatsubscriptioninvitelink

        :param chat_id: Unique identifier for the target chat or username of the target channel
            (in the format @channelusername)
        :type chat_id: :obj:`int` or :obj:`str`

        :param invite_link: The invite link to edit
        :type invite_link: :obj:`str`

        :param name: Invite link name; 0-32 characters
        :type name: :obj:`str`

        :return: Returns the edited invite link as a ChatInviteLink object.
        :rtype: :class:`telebot.types.ChatInviteLink`
        """
        return types.ChatInviteLink.de_json(
            apihelper.edit_chat_subscription_invite_link(self.token, chat_id, invite_link, name=name)
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
        result = apihelper.get_my_commands(self.token, scope=scope, language_code=language_code)
        return [types.BotCommand.de_json(cmd) for cmd in result]


    def set_my_name(self, name: Optional[str]=None, language_code: Optional[str]=None):
        """
        Use this method to change the bot's name. Returns True on success.

        Telegram documentation: https://core.telegram.org/bots/api#setmyname

        :param name: Optional. New bot name; 0-64 characters. Pass an empty string to remove the dedicated name for the given language.
        :type name: :obj:`str`

        :param language_code: Optional. A two-letter ISO 639-1 language code. If empty, the name will be shown to all users for whose
            language there is no dedicated name.
        :type language_code: :obj:`str`

        :return: True on success.
        """
        return apihelper.set_my_name(self.token, name=name, language_code=language_code)

    
    def get_my_name(self, language_code: Optional[str]=None):
        """
        Use this method to get the current bot name for the given user language.
        Returns BotName on success.

        Telegram documentation: https://core.telegram.org/bots/api#getmyname

        :param language_code: Optional. A two-letter ISO 639-1 language code or an empty string
        :type language_code: :obj:`str`

        :return: :class:`telebot.types.BotName`
        """
        return types.BotName.de_json(
            apihelper.get_my_name(self.token, language_code=language_code)
        )


    def set_my_description(self, description: Optional[str]=None, language_code: Optional[str]=None):
        """
        Use this method to change the bot's description, which is shown in
        the chat with the bot if the chat is empty.
        Returns True on success.

        Telegram documentation: https://core.telegram.org/bots/api#setmydescription

        :param description: New bot description; 0-512 characters. Pass an empty string to remove the dedicated description for the given language.
        :type description: :obj:`str`

        :param language_code: A two-letter ISO 639-1 language code. If empty, the description will be applied to all users for
            whose language there is no dedicated description.
        :type language_code: :obj:`str`

        :return: True on success.
        """

        return apihelper.set_my_description(
            self.token, description=description, language_code=language_code)

    
    def get_my_description(self, language_code: Optional[str]=None):
        """
        Use this method to get the current bot description for the given user language.
        Returns BotDescription on success.

        Telegram documentation: https://core.telegram.org/bots/api#getmydescription

        :param language_code: A two-letter ISO 639-1 language code or an empty string
        :type language_code: :obj:`str`

        :return: :class:`telebot.types.BotDescription`
        """
        return types.BotDescription.de_json(
            apihelper.get_my_description(self.token, language_code=language_code))

    
    def set_my_short_description(self, short_description:Optional[str]=None, language_code:Optional[str]=None):
        """
        Use this method to change the bot's short description, which is shown on the bot's profile page and
        is sent together with the link when users share the bot. 
        Returns True on success.

        Telegram documentation: https://core.telegram.org/bots/api#setmyshortdescription

        :param short_description: New short description for the bot; 0-120 characters. Pass an empty string to remove the dedicated short description for the given language.
        :type short_description: :obj:`str`

        :param language_code: A two-letter ISO 639-1 language code.
            If empty, the short description will be applied to all users for whose language there is no dedicated short description.
        :type language_code: :obj:`str`

        :return: True on success.
        """
        return apihelper.set_my_short_description(
            self.token, short_description=short_description, language_code=language_code)

    
    def get_my_short_description(self, language_code: Optional[str]=None):
        """
        Use this method to get the current bot short description for the given user language.
        Returns BotShortDescription on success.

        Telegram documentation: https://core.telegram.org/bots/api#getmyshortdescription

        :param language_code: A two-letter ISO 639-1 language code or an empty string
        :type language_code: :obj:`str`

        :return: :class:`telebot.types.BotShortDescription`
        """
        return types.BotShortDescription.de_json(
            apihelper.get_my_short_description(self.token, language_code=language_code))


    def set_chat_menu_button(self, chat_id: Union[int, str]=None, menu_button: types.MenuButton=None) -> bool:
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
        return apihelper.set_chat_menu_button(self.token, chat_id=chat_id, menu_button=menu_button)


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
        return types.MenuButton.de_json(
            apihelper.get_chat_menu_button(self.token, chat_id=chat_id))


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
        return apihelper.set_my_default_administrator_rights(self.token, rights=rights, for_channels=for_channels)


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
        return types.ChatAdministratorRights.de_json(
            apihelper.get_my_default_administrator_rights(self.token, for_channels=for_channels)
        )


    def get_business_connection(self, business_connection_id: str) -> types.BusinessConnection:
        """
        Use this method to get information about the connection of the bot with a business account.
        Returns a BusinessConnection object on success.

        Telegram documentation: https://core.telegram.org/bots/api#getbusinessconnection

        :param business_connection_id: Unique identifier of the business connection
        :type business_connection_id: :obj:`str`

        :return: Returns a BusinessConnection object on success.
        :rtype: :class:`telebot.types.BusinessConnection`
        """

        return types.BusinessConnection.de_json(
            apihelper.get_business_connection(self.token, business_connection_id)
        )
    
        
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
        return apihelper.set_my_commands(self.token, commands, scope=scope, language_code=language_code)

    
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
        return apihelper.delete_my_commands(self.token, scope=scope, language_code=language_code)


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
            disable_notification: Optional[bool]=False, business_connection_id: Optional[str]=None) -> bool:
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

        :param business_connection_id: Unique identifier of the business connection
        :type business_connection_id: :obj:`str`

        :return: True on success.
        :rtype: :obj:`bool`
        """
        disable_notification = self.disable_notification if (disable_notification is None) else disable_notification

        return apihelper.pin_chat_message(self.token, chat_id, message_id, disable_notification=disable_notification,
                                            business_connection_id=business_connection_id)


    def unpin_chat_message(self, chat_id: Union[int, str], message_id: Optional[int]=None, business_connection_id: Optional[str]=None) -> bool:
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

        :param business_connection_id: Unique identifier of the business connection
        :type business_connection_id: :obj:`str`

        :return: True on success.
        :rtype: :obj:`bool`
        """
        return apihelper.unpin_chat_message(self.token, chat_id, message_id, business_connection_id=business_connection_id)


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
            disable_web_page_preview: Optional[bool]=None,        # deprecated, for backward compatibility
            reply_markup: Optional[types.InlineKeyboardMarkup]=None,
            link_preview_options : Optional[types.LinkPreviewOptions]=None,
            business_connection_id: Optional[str]=None,
            timeout: Optional[int]=None) -> Union[types.Message, bool]:
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

        :param disable_web_page_preview: deprecated.
        :type disable_web_page_preview: :obj:`bool`

        :param reply_markup: A JSON-serialized object for an inline keyboard.
        :type reply_markup: :obj:`InlineKeyboardMarkup`

        :param link_preview_options: A JSON-serialized object for options used to automatically generate previews for links.
        :type link_preview_options: :obj:`LinkPreviewOptions`

        :param business_connection_id: Unique identifier of the business connection
        :type business_connection_id: :obj:`str`

        :param timeout: Timeout in seconds for the request.
        :type timeout: :obj:`int`

        :return: On success, if edited message is sent by the bot, the edited Message is returned, otherwise True is returned.
        :rtype: :obj:`types.Message` or :obj:`bool`
        """
        parse_mode = self.parse_mode if (parse_mode is None) else parse_mode
                
        if disable_web_page_preview is not None:
            # show a deprecation warning
            logger.warning("The parameter 'disable_web_page_preview' is deprecated. Use 'link_preview_options' instead.")

            if link_preview_options:
                # show a conflict warning
                logger.warning("Both 'link_preview_options' and 'disable_web_page_preview' parameters are set: conflicting, 'disable_web_page_preview' is deprecated")
            else:
                # create a LinkPreviewOptions object
                link_preview_options = types.LinkPreviewOptions(is_disabled=disable_web_page_preview)

        if link_preview_options and (link_preview_options.is_disabled is None):
            link_preview_options.is_disabled = self.disable_web_page_preview

        # Fix preview link options if link_preview_options not provided. Get param from class
        if not link_preview_options and self.disable_web_page_preview:
            # create a LinkPreviewOptions object
            link_preview_options = types.LinkPreviewOptions(is_disabled=self.disable_web_page_preview)

        result = apihelper.edit_message_text(
            self.token, text, chat_id=chat_id, message_id=message_id, inline_message_id=inline_message_id,
            parse_mode=parse_mode, entities=entities, reply_markup=reply_markup, link_preview_options=link_preview_options,
            business_connection_id=business_connection_id, timeout=timeout)

        if isinstance(result, bool):  # if edit inline message return is bool not Message.
            return result
        return types.Message.de_json(result)


    def edit_message_media(
            self, media: Any, chat_id: Optional[Union[int, str]]=None, 
            message_id: Optional[int]=None,
            inline_message_id: Optional[str]=None, 
            reply_markup: Optional[types.InlineKeyboardMarkup]=None,
            business_connection_id: Optional[str]=None,
            timeout: Optional[int]=None) -> Union[types.Message, bool]:
        """
        Use this method to edit animation, audio, document, photo, or video messages, or to add media to text messages.
        If a message is part of a message album, then it can be edited only to an audio for audio albums, only to a document for document albums and to a photo or a video otherwise.
        When an inline message is edited, a new file can't be uploaded; use a previously uploaded file via its file_id or specify a URL.
        On success, if the edited message is not an inline message, the edited Message is returned, otherwise True is returned.
        Note that business messages that were not sent by the bot and do not contain an inline keyboard can only be edited within 48 hours from the time they were sent. 

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

        :param business_connection_id: Unique identifier of the business connection
        :type business_connection_id: :obj:`str`

        :param timeout: Timeout in seconds for the request.
        :type timeout: :obj:`int`

        :return: On success, if edited message is sent by the bot, the edited Message is returned, otherwise True is returned.
        :rtype: :obj:`types.Message` or :obj:`bool`
        """
        result = apihelper.edit_message_media(
            self.token, media, chat_id=chat_id, message_id=message_id, inline_message_id=inline_message_id,
            reply_markup=reply_markup, business_connection_id=business_connection_id, timeout=timeout)

        if isinstance(result, bool):  # if edit inline message return is bool not Message.
            return result
        return types.Message.de_json(result)


    def edit_message_reply_markup(
            self, chat_id: Optional[Union[int, str]]=None, 
            message_id: Optional[int]=None,
            inline_message_id: Optional[str]=None, 
            reply_markup: Optional[types.InlineKeyboardMarkup]=None,
            business_connection_id: Optional[str]=None,
            timeout: Optional[int]=None) -> Union[types.Message, bool]:
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

        :param business_connection_id: Unique identifier of the business connection
        :type business_connection_id: :obj:`str`

        :param timeout: Timeout in seconds for the request.
        :type timeout: :obj:`int`

        :return: On success, if edited message is sent by the bot, the edited Message is returned, otherwise True is returned.
        :rtype: :obj:`types.Message` or :obj:`bool`
        """
        result = apihelper.edit_message_reply_markup(
            self.token, chat_id=chat_id, message_id=message_id, inline_message_id=inline_message_id,
            reply_markup=reply_markup, business_connection_id=business_connection_id, timeout=timeout)

        if isinstance(result, bool):
            return result
        return types.Message.de_json(result)


    def send_game(
            self, chat_id: Union[int, str], game_short_name: str, 
            disable_notification: Optional[bool]=None,
            reply_to_message_id: Optional[int]=None,          # deprecated, for backward compatibility
            reply_markup: Optional[REPLY_MARKUP_TYPES]=None, 
            timeout: Optional[int]=None,
            allow_sending_without_reply: Optional[bool]=None, # deprecated, for backward compatibility
            protect_content: Optional[bool]=None,
            message_thread_id: Optional[int]=None,
            reply_parameters: Optional[types.ReplyParameters]=None,
            business_connection_id: Optional[str]=None,
            message_effect_id: Optional[str]=None,
            allow_paid_broadcast: Optional[bool]=None) -> types.Message:
        """
        Used to send the game.

        Telegram documentation: https://core.telegram.org/bots/api#sendgame

        :param chat_id: Unique identifier for the target chat or username of the target channel (in the format @channelusername)
        :type chat_id: :obj:`int` or :obj:`str`

        :param game_short_name: Short name of the game, serves as the unique identifier for the game. Set up your games via @BotFather.
        :type game_short_name: :obj:`str`

        :param disable_notification: Sends the message silently. Users will receive a notification with no sound.
        :type disable_notification: :obj:`bool`

        :param reply_to_message_id: deprecated. If the message is a reply, ID of the original message
        :type reply_to_message_id: :obj:`int`

        :param allow_sending_without_reply: deprecated. Pass True, if the message should be sent even if the specified replied-to message is not found
        :type allow_sending_without_reply: :obj:`bool`

        :param reply_markup: Additional interface options. A JSON-serialized object for an inline keyboard, custom reply keyboard, instructions to remove reply keyboard or to force a reply from the user.
        :type reply_markup: :obj:`InlineKeyboardMarkup` or :obj:`ReplyKeyboardMarkup` or :obj:`ReplyKeyboardRemove` or :obj:`ForceReply`

        :param timeout: Timeout in seconds for waiting for a response from the bot.
        :type timeout: :obj:`int`

        :param protect_content: Protects the contents of the sent message from forwarding and saving
        :type protect_content: :obj:`bool`

        :param message_thread_id: The identifier of a message thread, in which the game message will be sent.
        :type message_thread_id: :obj:`int`

        :param reply_parameters: Reply parameters
        :type reply_parameters: :obj:`ReplyParameters`

        :param business_connection_id: Unique identifier of the business connection
        :type business_connection_id: :obj:`str`

        :param message_effect_id: Unique identifier of the message effect
        :type message_effect_id: :obj:`str`

        :param allow_paid_broadcast: Pass True to allow up to 1000 messages per second, ignoring broadcasting limits for a fee
            of 0.1 Telegram Stars per message. The relevant Stars will be withdrawn from the bot's balance
        :type allow_paid_broadcast: :obj:`bool`

        :return: On success, the sent Message is returned.
        :rtype: :obj:`types.Message`
        """
        disable_notification = self.disable_notification if (disable_notification is None) else disable_notification
        protect_content = self.protect_content if (protect_content is None) else protect_content

        if allow_sending_without_reply is not None:
            # show a deprecation warning
            logger.warning("The parameter 'allow_sending_without_reply' is deprecated. Use 'reply_parameters' instead.")

        if reply_to_message_id:
            # show a deprecation warning
            logger.warning("The parameter 'reply_to_message_id' is deprecated. Use 'reply_parameters' instead.")

            if reply_parameters:
                # show a conflict warning
                logger.warning("Both 'reply_parameters' and 'reply_to_message_id' parameters are set: conflicting, 'reply_to_message_id' is deprecated")
            else:
                # create a ReplyParameters object
                reply_parameters = types.ReplyParameters(
                    reply_to_message_id,
                    allow_sending_without_reply=self.allow_sending_without_reply if (allow_sending_without_reply is None) else allow_sending_without_reply
                )

        if reply_parameters and (reply_parameters.allow_sending_without_reply is None):
            reply_parameters.allow_sending_without_reply = self.allow_sending_without_reply

        return types.Message.de_json(
            apihelper.send_game(
                self.token, chat_id, game_short_name, disable_notification=disable_notification,
                reply_markup=reply_markup, timeout=timeout, protect_content=protect_content,
                message_thread_id=message_thread_id, reply_parameters=reply_parameters, business_connection_id=business_connection_id,
                message_effect_id=message_effect_id, allow_paid_broadcast=allow_paid_broadcast)
        )


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
        result = apihelper.set_game_score(
            self.token, user_id, score, force=force, disable_edit_message=disable_edit_message,
            chat_id=chat_id, message_id=message_id, inline_message_id=inline_message_id)

        if isinstance(result, bool):
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
        result = apihelper.get_game_high_scores(
            self.token, user_id, chat_id=chat_id, message_id=message_id, inline_message_id=inline_message_id)
        return [types.GameHighScore.de_json(r) for r in result]


    def send_invoice(
            self, chat_id: Union[int, str], title: str, description: str, 
            invoice_payload: str, provider_token: Union[str, None], currency: str, 
            prices: List[types.LabeledPrice], start_parameter: Optional[str]=None, 
            photo_url: Optional[str]=None, photo_size: Optional[int]=None, 
            photo_width: Optional[int]=None, photo_height: Optional[int]=None,
            need_name: Optional[bool]=None, need_phone_number: Optional[bool]=None, 
            need_email: Optional[bool]=None, need_shipping_address: Optional[bool]=None,
            send_phone_number_to_provider: Optional[bool]=None, 
            send_email_to_provider: Optional[bool]=None, 
            is_flexible: Optional[bool]=None,
            disable_notification: Optional[bool]=None, 
            reply_to_message_id: Optional[int]=None,          # deprecated, for backward compatibility
            reply_markup: Optional[REPLY_MARKUP_TYPES]=None, 
            provider_data: Optional[str]=None, 
            timeout: Optional[int]=None,
            allow_sending_without_reply: Optional[bool]=None, # deprecated, for backward compatibility
            max_tip_amount: Optional[int] = None,
            suggested_tip_amounts: Optional[List[int]]=None,
            protect_content: Optional[bool]=None,
            message_thread_id: Optional[int]=None,
            reply_parameters: Optional[types.ReplyParameters]=None,
            message_effect_id: Optional[str]=None,
            allow_paid_broadcast: Optional[bool]=None) -> types.Message:
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

        :param provider_token: Payments provider token, obtained via @Botfather; Pass None to omit the parameter
            to use "XTR" currency
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

        :param reply_to_message_id: deprecated. If the message is a reply, ID of the original message
        :type reply_to_message_id: :obj:`int`

        :param allow_sending_without_reply: deprecated. Pass True, if the message should be sent even if the specified replied-to message is not found
        :type allow_sending_without_reply: :obj:`bool`

        :param reply_markup: A JSON-serialized object for an inline keyboard. If empty,
            one 'Pay total price' button will be shown. If not empty, the first button must be a Pay button
        :type reply_markup: :obj:`str`

        :param provider_data: A JSON-serialized data about the invoice, which will be shared with the payment provider.
            A detailed description of required fields should be provided by the payment provider.
        :type provider_data: :obj:`str`

        :param timeout: Timeout of a request, defaults to None
        :type timeout: :obj:`int`

        :param max_tip_amount: The maximum accepted amount for tips in the smallest units of the currency
        :type max_tip_amount: :obj:`int`

        :param suggested_tip_amounts: A JSON-serialized array of suggested amounts of tips in the smallest
            units of the currency.  At most 4 suggested tip amounts can be specified. The suggested tip
            amounts must be positive, passed in a strictly increased order and must not exceed max_tip_amount.
        :type suggested_tip_amounts: :obj:`list` of :obj:`int`

        :param protect_content: Protects the contents of the sent message from forwarding and saving
        :type protect_content: :obj:`bool`

        :param message_thread_id: The identifier of a message thread, in which the invoice message will be sent
        :type message_thread_id: :obj:`int`

        :param reply_parameters: Required if the message is a reply. Additional interface options.
        :type reply_parameters: :obj:`types.ReplyParameters`

        :param message_effect_id: The identifier of a message effect, which will be applied to the sent message
        :type message_effect_id: :obj:`str`

        :param allow_paid_broadcast: Pass True to allow up to 1000 messages per second, ignoring broadcasting limits for a fee
            of 0.1 Telegram Stars per message. The relevant Stars will be withdrawn from the bot's balance
        :type allow_paid_broadcast: :obj:`bool`

        :return: On success, the sent Message is returned.
        :rtype: :obj:`types.Message`
        """
        disable_notification = self.disable_notification if (disable_notification is None) else disable_notification
        protect_content = self.protect_content if (protect_content is None) else protect_content

        if allow_sending_without_reply is not None:
            # show a deprecation warning
            logger.warning("The parameter 'allow_sending_without_reply' is deprecated. Use 'reply_parameters' instead.")

        if reply_to_message_id:
            # show a deprecation warning
            logger.warning("The parameter 'reply_to_message_id' is deprecated. Use 'reply_parameters' instead.")

            if reply_parameters:
                # show a conflict warning
                logger.warning("Both 'reply_parameters' and 'reply_to_message_id' parameters are set: conflicting, 'reply_to_message_id' is deprecated")
            else:
                # create a ReplyParameters object
                reply_parameters = types.ReplyParameters(
                    reply_to_message_id,
                    allow_sending_without_reply=self.allow_sending_without_reply if (allow_sending_without_reply is None) else allow_sending_without_reply
                )

        if reply_parameters and (reply_parameters.allow_sending_without_reply is None):
            reply_parameters.allow_sending_without_reply = self.allow_sending_without_reply

        return types.Message.de_json(
            apihelper.send_invoice(
                self.token, chat_id, title, description, invoice_payload, provider_token,
                currency, prices, start_parameter=start_parameter, photo_url=photo_url,
                photo_size=photo_size, photo_width=photo_width, photo_height=photo_height,
                need_name=need_name, need_phone_number=need_phone_number, need_email=need_email,
                need_shipping_address=need_shipping_address, send_phone_number_to_provider=send_phone_number_to_provider,
                send_email_to_provider=send_email_to_provider, is_flexible=is_flexible,
                disable_notification=disable_notification, reply_markup=reply_markup,
                provider_data=provider_data, timeout=timeout, protect_content=protect_content,
                message_thread_id=message_thread_id, reply_parameters=reply_parameters,
                max_tip_amount=max_tip_amount, suggested_tip_amounts=suggested_tip_amounts,
                message_effect_id=message_effect_id, allow_paid_broadcast=allow_paid_broadcast)
        )

    def create_invoice_link(self,
            title: str, description: str, payload:str, provider_token: Union[str, None], 
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
            is_flexible: Optional[bool]=None,
            subscription_period: Optional[int]=None,
            business_connection_id: Optional[str]=None) -> str:
            
        """
        Use this method to create a link for an invoice. 
        Returns the created invoice link as String on success.

        Telegram documentation:
        https://core.telegram.org/bots/api#createinvoicelink

        :param business_connection_id: Unique identifier of the business connection on behalf of which the link will be created
        :type business_connection_id: :obj:`str`

        :param title: Product name, 1-32 characters
        :type title: :obj:`str`

        :param description: Product description, 1-255 characters
        :type description: :obj:`str`

        :param payload: Bot-defined invoice payload, 1-128 bytes. This will not be displayed to the user,
            use for your internal processes.
        :type payload: :obj:`str`

        :param provider_token: Payments provider token, obtained via @Botfather; Pass None to omit the parameter
            to use "XTR" currency
        :type provider_token: :obj:`str`

        :param currency: Three-letter ISO 4217 currency code,
            see https://core.telegram.org/bots/payments#supported-currencies
        :type currency: :obj:`str`

        :param prices: Price breakdown, a list of components
            (e.g. product price, tax, discount, delivery cost, delivery tax, bonus, etc.)
        :type prices: :obj:`list` of :obj:`types.LabeledPrice`

        :param subscription_period: The number of seconds the subscription will be active for before the next payment.
            The currency must be set to “XTR” (Telegram Stars) if the parameter is used. Currently, it must always
            be 2592000 (30 days) if specified.
        :type subscription_period: :obj:`int`

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
        return apihelper.create_invoice_link(
            self.token, title, description, payload, provider_token,
            currency, prices, max_tip_amount=max_tip_amount, suggested_tip_amounts=suggested_tip_amounts,
            provider_data=provider_data, photo_url=photo_url, photo_size=photo_size,
            photo_width=photo_width, photo_height=photo_height, need_name=need_name,
            need_phone_number=need_phone_number, need_email=need_email,
            need_shipping_address=need_shipping_address, send_phone_number_to_provider=send_phone_number_to_provider,
            send_email_to_provider=send_email_to_provider, is_flexible=is_flexible ,subscription_period=subscription_period,
            business_connection_id=business_connection_id)


    # noinspection PyShadowingBuiltins
    def send_poll(
            self, chat_id: Union[int, str], question: str, options: List[Union[str, types.InputPollOption]],
            is_anonymous: Optional[bool]=None, type: Optional[str]=None, 
            allows_multiple_answers: Optional[bool]=None, 
            correct_option_id: Optional[int]=None,
            explanation: Optional[str]=None, 
            explanation_parse_mode: Optional[str]=None, 
            open_period: Optional[int]=None, 
            close_date: Optional[Union[int, datetime]]=None, 
            is_closed: Optional[bool]=None,
            disable_notification: Optional[bool]=False,
            reply_to_message_id: Optional[int]=None,          # deprecated, for backward compatibility
            reply_markup: Optional[REPLY_MARKUP_TYPES]=None, 
            allow_sending_without_reply: Optional[bool]=None, # deprecated, for backward compatibility
            timeout: Optional[int]=None,
            explanation_entities: Optional[List[types.MessageEntity]]=None,
            protect_content: Optional[bool]=None,
            message_thread_id: Optional[int]=None,
            reply_parameters: Optional[types.ReplyParameters]=None,
            business_connection_id: Optional[str]=None,
            question_parse_mode: Optional[str] = None,
            question_entities: Optional[List[types.MessageEntity]] = None,
            message_effect_id: Optional[str]=None,
            allow_paid_broadcast: Optional[bool]=None) -> types.Message:
        """
        Use this method to send a native poll.
        On success, the sent Message is returned.

        Telegram documentation: https://core.telegram.org/bots/api#sendpoll

        :param chat_id: Unique identifier for the target chat or username of the target channel
        :type chat_id: :obj:`int` | :obj:`str`

        :param question: Poll question, 1-300 characters
        :type question: :obj:`str`

        :param options: A JSON-serialized list of 2-10 answer options
        :type options: :obj:`list` of :obj:`InputPollOption` | :obj:`list` of :obj:`str`

        :param is_anonymous: True, if the poll needs to be anonymous, defaults to True
        :type is_anonymous: :obj:`bool`

        :param type: Poll type, “quiz” or “regular”, defaults to “regular”
        :type type: :obj:`str`

        :param allows_multiple_answers: True, if the poll allows multiple answers, ignored for polls in quiz mode, defaults to False
        :type allows_multiple_answers: :obj:`bool`

        :param correct_option_id: 0-based identifier of the correct answer option. Available only for polls in quiz mode, defaults to None
        :type correct_option_id: :obj:`int`

        :param explanation: Text that is shown when a user chooses an incorrect answer or taps on the lamp icon in a quiz-style poll, 0-200 characters with at most 2 line feeds after entities parsing
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

        :param reply_to_message_id: deprecated. If the message is a reply, ID of the original message
        :type reply_to_message_id: :obj:`int`

        :param allow_sending_without_reply: deprecated. Pass True, if the message should be sent even if the specified replied-to message is not found
        :type allow_sending_without_reply: :obj:`bool`

        :param reply_markup: Additional interface options. A JSON-serialized object for an inline keyboard, custom reply keyboard, instructions to remove reply keyboard or to force a reply from the user.
        :type reply_markup: :obj:`InlineKeyboardMarkup` | :obj:`ReplyKeyboardMarkup` | :obj:`ReplyKeyboardRemove` | :obj:`ForceReply`

        :param timeout: Timeout in seconds for waiting for a response from the user.
        :type timeout: :obj:`int`

        :param explanation_entities: A JSON-serialized list of special entities that appear in the explanation, which can be specified instead of parse_mode
        :type explanation_entities: :obj:`list` of :obj:`MessageEntity`

        :param protect_content: Protects the contents of the sent message from forwarding and saving
        :type protect_content: :obj:`bool`

        :param message_thread_id: The identifier of a message thread, in which the poll will be sent
        :type message_thread_id: :obj:`int`

        :param reply_parameters: reply parameters.
        :type reply_parameters: :obj:`ReplyParameters`

        :param business_connection_id: Identifier of the business connection to use for the poll
        :type business_connection_id: :obj:`str`

        :param question_parse_mode: Mode for parsing entities in the question. See formatting options for more details. Currently, only custom emoji entities are allowed
        :type question_parse_mode: :obj:`str`

        :param question_entities: A JSON-serialized list of special entities that appear in the poll question. It can be specified instead of question_parse_mode
        :type question_entities: :obj:`list` of :obj:`MessageEntity`

        :param message_effect_id: Unique identifier of the message effect to apply to the sent message
        :type message_effect_id: :obj:`str`

        :param allow_paid_broadcast: Pass True to allow up to 1000 messages per second, ignoring broadcasting limits for a fee
            of 0.1 Telegram Stars per message. The relevant Stars will be withdrawn from the bot's balance
        :type allow_paid_broadcast: :obj:`bool`

        :return: On success, the sent Message is returned.
        :rtype: :obj:`types.Message`
        """
        disable_notification = self.disable_notification if (disable_notification is None) else disable_notification
        protect_content = self.protect_content if (protect_content is None) else protect_content

        if allow_sending_without_reply is not None:
            # show a deprecation warning
            logger.warning("The parameter 'allow_sending_without_reply' is deprecated. Use 'reply_parameters' instead.")

        if reply_to_message_id:
            # show a deprecation warning
            logger.warning("The parameter 'reply_to_message_id' is deprecated. Use 'reply_parameters' instead.")

            if reply_parameters:
                # show a conflict warning
                logger.warning("Both 'reply_parameters' and 'reply_to_message_id' parameters are set: conflicting, 'reply_to_message_id' is deprecated")
            else:
                # create a ReplyParameters object
                reply_parameters = types.ReplyParameters(
                    reply_to_message_id,
                    allow_sending_without_reply=self.allow_sending_without_reply if (allow_sending_without_reply is None) else allow_sending_without_reply
                )

        if reply_parameters and (reply_parameters.allow_sending_without_reply is None):
            reply_parameters.allow_sending_without_reply = self.allow_sending_without_reply

        if isinstance(question, types.Poll):
            raise RuntimeError("The send_poll signature was changed, please see send_poll function details.")

        explanation_parse_mode = self.parse_mode if (explanation_parse_mode is None) else explanation_parse_mode
        question_parse_mode = self.parse_mode if (question_parse_mode is None) else question_parse_mode

        if options and (not isinstance(options[0], types.InputPollOption)):
            # show a deprecation warning
            logger.warning("The parameter 'options' changed, should be List[types.InputPollOption], other types are deprecated.")
            # convert options to appropriate type
            if isinstance(options[0], str):
                options = [types.InputPollOption(option) for option in options]
            elif isinstance(options[0], types.PollOption):
                options = [types.InputPollOption(option.text, text_entities=option.text_entities) for option in options]
            else:
                raise RuntimeError("Type of 'options' items is unknown. Options should be List[types.InputPollOption], other types are deprecated.")

        return types.Message.de_json(
            apihelper.send_poll(
                self.token, chat_id, question, options,
                is_anonymous=is_anonymous, type=type, allows_multiple_answers=allows_multiple_answers,
                correct_option_id=correct_option_id, explanation=explanation,
                explanation_parse_mode=explanation_parse_mode, open_period=open_period,
                close_date=close_date, is_closed=is_closed, disable_notification=disable_notification,
                reply_markup=reply_markup, timeout=timeout, explanation_entities=explanation_entities,
                protect_content=protect_content, message_thread_id=message_thread_id,
                reply_parameters=reply_parameters, business_connection_id=business_connection_id,
                question_parse_mode=question_parse_mode, question_entities=question_entities,
                message_effect_id=message_effect_id, allow_paid_broadcast=allow_paid_broadcast)
            )


    def stop_poll(
            self, chat_id: Union[int, str], message_id: int, 
            reply_markup: Optional[types.InlineKeyboardMarkup]=None,
            business_connection_id: Optional[str]=None) -> types.Poll:
        """
        Use this method to stop a poll which was sent by the bot. On success, the stopped Poll is returned.

        Telegram documentation: https://core.telegram.org/bots/api#stoppoll

        :param chat_id: Unique identifier for the target chat or username of the target channel
        :type chat_id: :obj:`int` | :obj:`str`

        :param message_id: Identifier of the original message with the poll
        :type message_id: :obj:`int`

        :param reply_markup: A JSON-serialized object for a new message markup.
        :type reply_markup: :obj:`InlineKeyboardMarkup`

        :param business_connection_id: Identifier of the business connection to use for the poll
        :type business_connection_id: :obj:`str`

        :return: On success, the stopped Poll is returned.
        :rtype: :obj:`types.Poll`
        """
        return types.Poll.de_json(
            apihelper.stop_poll(self.token, chat_id, message_id, reply_markup=reply_markup, business_connection_id=business_connection_id)
        )


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
        return apihelper.answer_shipping_query(
            self.token, shipping_query_id, ok, shipping_options=shipping_options, error_message=error_message)


    def answer_pre_checkout_query(
            self, pre_checkout_query_id: str, ok: bool, 
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
        return apihelper.answer_pre_checkout_query(
            self.token, pre_checkout_query_id, ok, error_message=error_message)


    def get_star_transactions(self, offset: Optional[int]=None, limit: Optional[int]=None) -> types.StarTransactions:
        """
        Returns the bot's Telegram Star transactions in chronological order. On success, returns a StarTransactions object.

        Telegram documentation: https://core.telegram.org/bots/api#getstartransactions

        :param offset: Number of transactions to skip in the response
        :type offset: :obj:`int`

        :param limit: The maximum number of transactions to be retrieved. Values between 1-100 are accepted. Defaults to 100.
        :type limit: :obj:`int`

        :return: On success, returns a StarTransactions object.
        :rtype: :obj:`types.StarTransactions`
        """
        return types.StarTransactions.de_json(
            apihelper.get_star_transactions(self.token, offset=offset, limit=limit)
        )
    
    
    def refund_star_payment(self, user_id: int, telegram_payment_charge_id: str) -> bool:
        """
        Refunds a successful payment in Telegram Stars. Returns True on success.

        Telegram documentation: https://core.telegram.org/bots/api#refundstarpayment

        :param user_id: Identifier of the user whose payment will be refunded
        :type user_id: :obj:`int`

        :param telegram_payment_charge_id: Telegram payment identifier
        :type telegram_payment_charge_id: :obj:`str`

        :return: On success, True is returned.
        :rtype: :obj:`bool`
        """
        return apihelper.refund_star_payment(self.token, user_id, telegram_payment_charge_id)

    def edit_user_star_subscription(self, user_id: int, telegram_payment_charge_id: str, is_canceled: bool) -> bool:
        """
        Allows the bot to cancel or re-enable extension of a subscription paid in Telegram Stars. Returns True on success.

        Telegram documentation: https://core.telegram.org/bots/api#edituserstarsubscription

        :param user_id: Identifier of the user whose subscription will be edited
        :type user_id: :obj:`int`

        :param telegram_payment_charge_id: Telegram payment identifier for the subscription
        :type telegram_payment_charge_id: :obj:`str`

        :param is_canceled: Pass True to cancel extension of the user subscription; the subscription must be active up to the end of the current subscription period. Pass False to allow the user to re-enable a subscription that was previously canceled by the bot.
        :type is_canceled: :obj:`bool`

        :return: On success, True is returned.
        :rtype: :obj:`bool`
        """
        return apihelper.edit_user_star_subscription(self.token, user_id, telegram_payment_charge_id, is_canceled)

    def edit_message_caption(
            self, caption: str, chat_id: Optional[Union[int, str]]=None, 
            message_id: Optional[int]=None, 
            inline_message_id: Optional[str]=None,
            parse_mode: Optional[str]=None, 
            caption_entities: Optional[List[types.MessageEntity]]=None,
            reply_markup: Optional[types.InlineKeyboardMarkup]=None,
            show_caption_above_media: Optional[bool]=None,
            business_connection_id: Optional[str]=None,
            timeout: Optional[int]=None) -> Union[types.Message, bool]:
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

        :param show_caption_above_media: Pass True, if the caption must be shown above the message media. Supported only for animation, photo and video messages.
        :type show_caption_above_media: :obj:`bool`

        :param business_connection_id: Identifier of the business connection to use for the message
        :type business_connection_id: :obj:`str`

        :param timeout: Timeout in seconds for the request.
        :type timeout: :obj:`int`

        :return: On success, if edited message is sent by the bot, the edited Message is returned, otherwise True is returned.
        :rtype: :obj:`types.Message` | :obj:`bool`
        """
        parse_mode = self.parse_mode if (parse_mode is None) else parse_mode

        result = apihelper.edit_message_caption(
            self.token, caption, chat_id=chat_id, message_id=message_id, inline_message_id=inline_message_id,
            parse_mode=parse_mode, caption_entities=caption_entities, reply_markup=reply_markup,
            show_caption_above_media=show_caption_above_media, business_connection_id=business_connection_id,
            timeout=timeout)

        if isinstance(result, bool):
            return result
        return types.Message.de_json(result)


    def reply_to(self, message: types.Message, text: str, **kwargs) -> types.Message:
        """
        Convenience function for `send_message(message.chat.id, text, reply_parameters=(message.message_id...), **kwargs)`

        :param message: Instance of :class:`telebot.types.Message`
        :type message: :obj:`types.Message`

        :param text: Text of the message.
        :type text: :obj:`str`

        :param kwargs: Additional keyword arguments which are passed to :meth:`telebot.TeleBot.send_message`

        :return: On success, the sent Message is returned.
        :rtype: :class:`telebot.types.Message`
        """
        if kwargs:
            reply_parameters = kwargs.pop("reply_parameters", None)
            if "allow_sending_without_reply" in kwargs:
                logger.warning("The parameter 'allow_sending_without_reply' is deprecated. Use 'reply_parameters' instead.")
        else:
            reply_parameters = None

        if not reply_parameters:
            reply_parameters = types.ReplyParameters(
                message.message_id,
                allow_sending_without_reply=kwargs.pop("allow_sending_without_reply", None) if kwargs else None
            )

        if not reply_parameters.message_id:
            reply_parameters.message_id = message.message_id

        return self.send_message(message.chat.id, text, reply_parameters=reply_parameters, **kwargs)


    def answer_inline_query(
            self, inline_query_id: str, 
            results: List[Any], 
            cache_time: Optional[int]=None, 
            is_personal: Optional[bool]=None, 
            next_offset: Optional[str]=None,
            switch_pm_text: Optional[str]=None, 
            switch_pm_parameter: Optional[str]=None,
            button: Optional[types.InlineQueryResultsButton]=None) -> bool:
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

        :param button: A JSON-serialized object describing a button to be shown above inline query results
        :type button: :obj:`types.InlineQueryResultsButton`

        :return: On success, True is returned.
        :rtype: :obj:`bool`
        """
        if not button and (switch_pm_text or switch_pm_parameter):
            logger.warning("switch_pm_text and switch_pm_parameter are deprecated for answer_inline_query. Use button instead.")
            button = types.InlineQueryResultsButton(text=switch_pm_text, start_parameter=switch_pm_parameter)
        
        return apihelper.answer_inline_query(
            self.token, inline_query_id, results, cache_time=cache_time, is_personal=is_personal,
            next_offset=next_offset, button=button)


    def unpin_all_general_forum_topic_messages(self, chat_id: Union[int, str]) -> bool:
        """
        Use this method to clear the list of pinned messages in a General forum topic. 
        The bot must be an administrator in the chat for this to work and must have the
        can_pin_messages administrator right in the supergroup.
        Returns True on success.

        Telegram documentation: https://core.telegram.org/bots/api#unpinAllGeneralForumTopicMessages

        :param chat_id: Unique identifier for the target chat or username of chat
        :type chat_id: :obj:`int` | :obj:`str`

        :return: On success, True is returned.
        :rtype: :obj:`bool`
        """
        return apihelper.unpin_all_general_forum_topic_messages(self.token, chat_id)


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
        return apihelper.answer_callback_query(
            self.token, callback_query_id, text=text, show_alert=show_alert, url=url, cache_time=cache_time)

    
    def get_user_chat_boosts(self, chat_id: Union[int, str], user_id: int) -> types.UserChatBoosts:
        """
        Use this method to get the list of boosts added to a chat by a user. Requires administrator rights in the chat. Returns a UserChatBoosts object.

        Telegram documentation: https://core.telegram.org/bots/api#getuserchatboosts

        :param chat_id: Unique identifier for the target chat or username of the target channel
        :type chat_id: :obj:`int` | :obj:`str`

        :param user_id: Unique identifier of the target user
        :type user_id: :obj:`int`

        :return: On success, a UserChatBoosts object is returned.
        :rtype: :class:`telebot.types.UserChatBoosts`
        """
        return types.UserChatBoosts.de_json(
            apihelper.get_user_chat_boosts(self.token, chat_id, user_id)
        )

    # noinspection PyShadowingBuiltins
    def set_sticker_set_thumbnail(self, name: str, user_id: int, thumbnail: Union[Any, str]=None, format: Optional[str]=None) -> bool:
        """
        Use this method to set the thumbnail of a sticker set. 
        Animated thumbnails can be set for animated sticker sets only. Returns True on success.

        Telegram documentation: https://core.telegram.org/bots/api#setstickersetthumbnail

        :param name: Sticker set name
        :type name: :obj:`str`

        :param user_id: User identifier
        :type user_id: :obj:`int`

        :param thumbnail: A .WEBP or .PNG image with the thumbnail, must be up to 128 kilobytes in size and have a width and height of exactly 100px, or a .TGS animation
            with a thumbnail up to 32 kilobytes in size (see https://core.telegram.org/stickers#animated-sticker-requirements for animated sticker technical requirements),
            or a WEBM video with the thumbnail up to 32 kilobytes in size; see https://core.telegram.org/stickers#video-sticker-requirements for video sticker technical
            requirements. Pass a file_id as a String to send a file that already exists on the Telegram servers, pass an HTTP URL as a String for Telegram to get a file from
            the Internet, or upload a new one using multipart/form-data. More information on Sending Files ». Animated and video sticker set thumbnails can't be uploaded via
            HTTP URL. If omitted, then the thumbnail is dropped and the first sticker is used as the thumbnail.
        :type thumbnail: :obj:`filelike object`

        :param format: Format of the thumbnail, must be one of “static” for a .WEBP or .PNG image, “animated” for a .TGS animation, or “video” for a WEBM video
        :type format: :obj:`str`

        :return: On success, True is returned.
        :rtype: :obj:`bool`
        """
        if not format:
            logger.warning("Deprecation warning. 'format' parameter is required in set_sticker_set_thumbnail. Setting format to 'static'.")
            format = "static"

        return apihelper.set_sticker_set_thumbnail(self.token, name, user_id, thumbnail, format)

    
    @util.deprecated(deprecation_text="Use set_sticker_set_thumbnail instead")
    def set_sticker_set_thumb(self, name: str, user_id: int, thumb: Union[Any, str]=None):
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
        # deprecated
        return self.set_sticker_set_thumbnail(name, user_id, thumbnail=thumb)


    def get_sticker_set(self, name: str) -> types.StickerSet:
        """
        Use this method to get a sticker set. On success, a StickerSet object is returned.
        
        Telegram documentation: https://core.telegram.org/bots/api#getstickerset

        :param name: Sticker set name
        :type name: :obj:`str`

        :return: On success, a StickerSet object is returned.
        :rtype: :class:`telebot.types.StickerSet`
        """
        return types.StickerSet.de_json(
            apihelper.get_sticker_set(self.token, name)
        )

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

    
    def set_sticker_keywords(self, sticker: str, keywords: List[str]=None) -> bool:
        """
        Use this method to change search keywords assigned to a regular or custom emoji sticker.
        The sticker must belong to a sticker set created by the bot.
        Returns True on success.

        :param sticker: File identifier of the sticker.
        :type sticker: :obj:`str`

        :param keywords: A JSON-serialized list of 0-20 search keywords for the sticker with total length of up to 64 characters
        :type keywords: :obj:`list` of :obj:`str`

        :return: On success, True is returned.
        :rtype: :obj:`bool`
        """
        return apihelper.set_sticker_keywords(self.token, sticker, keywords=keywords)

    
    def set_sticker_mask_position(self, sticker: str, mask_position: types.MaskPosition=None) -> bool:
        """
        Use this method to change the mask position of a mask sticker.
        The sticker must belong to a sticker set that was created by the bot.
        Returns True on success.

        :param sticker: File identifier of the sticker.
        :type sticker: :obj:`str`

        :param mask_position: A JSON-serialized object for position where the mask should be placed on faces.
        :type mask_position: :class:`telebot.types.MaskPosition`

        :return: Returns True on success.
        :rtype: :obj:`bool`
        """
        return apihelper.set_sticker_mask_position(self.token, sticker, mask_position=mask_position)
    

    def set_custom_emoji_sticker_set_thumbnail(self, name: str, custom_emoji_id: Optional[str]=None) -> bool:
        """
        Use this method to set the thumbnail of a custom emoji sticker set.
        Returns True on success.

        :param name: Sticker set name
        :type name: :obj:`str`

        :param custom_emoji_id: Custom emoji identifier of a sticker from the sticker set; pass an empty string to drop the thumbnail and use the first sticker as the thumbnail.
        :type custom_emoji_id: :obj:`str`

        :return: Returns True on success.
        :rtype: :obj:`bool`
        """
        return apihelper.set_custom_emoji_sticker_set_thumbnail(self.token, name, custom_emoji_id=custom_emoji_id)

    
    def set_sticker_set_title(self, name: str, title: str) -> bool:
        """
        Use this method to set the title of a created sticker set.
        Returns True on success.

        :param name: Sticker set name
        :type name: :obj:`str`

        :param title: New sticker set title
        :type title: :obj:`str`

        :return: Returns True on success.
        :rtype: :obj:`bool`
        """
        return apihelper.set_sticker_set_title(self.token, name, title)

    
    def delete_sticker_set(self, name:str) -> bool:
        """
        Use this method to delete a sticker set. Returns True on success.

        :param name: Sticker set name
        :type name: :obj:`str`

        :return: Returns True on success.
        :rtype: :obj:`bool`
        """
        return apihelper.delete_sticker_set(self.token, name)

    def send_gift(self, user_id: Optional[Union[str, int]] = None, gift_id: str=None, text: Optional[str]=None, text_parse_mode: Optional[str]=None, 
                  text_entities: Optional[List[types.MessageEntity]]=None, pay_for_upgrade: Optional[bool]=None,
                  chat_id: Optional[Union[str, int]] = None) -> bool:
        """
        Sends a gift to the given user. The gift can't be converted to Telegram Stars by the user. Returns True on success.

        Telegram documentation: https://core.telegram.org/bots/api#sendgift

        :param gift_id: Identifier of the gift
        :type gift_id: :obj:`str`

        :param user_id: Required if chat_id is not specified. Unique identifier of the target user who will receive the gift.
        :type user_id::obj:`int` | :obj:`str`

        :param chat_id: Required if user_id is not specified. Unique identifier for the chat or username of the channel
            (in the format @channelusername) that will receive the gift.
        :type chat_id: :obj:`int` | :obj:`str`

        :param pay_for_upgrade: Pass True to pay for the gift upgrade from the bot's balance, thereby making the upgrade free for the receiver
        :type pay_for_upgrade: :obj:`bool`

        :param text: Text that will be shown along with the gift; 0-255 characters
        :type text: :obj:`str`

        :param text_parse_mode: Mode for parsing entities in the text. See formatting options for more details. Entities other than “bold”, “italic”, “underline”, “strikethrough”, “spoiler”, and “custom_emoji” are ignored.
        :type text_parse_mode: :obj:`str`

        :param text_entities: A JSON-serialized list of special entities that appear in the gift text. It can be specified instead of text_parse_mode. Entities other than “bold”, “italic”, “underline”, “strikethrough”, “spoiler”, and “custom_emoji” are ignored.
        :type text_entities: :obj:`list` of :obj:`types.MessageEntity`

        :return: Returns True on success.
        :rtype: :obj:`bool`
        """
        if user_id is None and chat_id is None:
            raise ValueError("Either user_id or chat_id must be specified.")
        
        if gift_id is None:
            raise ValueError("gift_id must be specified.")
        
        return apihelper.send_gift(self.token, gift_id, text=text, text_parse_mode=text_parse_mode, text_entities=text_entities,
                                      pay_for_upgrade=pay_for_upgrade, chat_id=chat_id, user_id=user_id)
    
    def verify_user(self, user_id: int, custom_description: Optional[str]=None) -> bool:
        """
        Verifies a user on behalf of the organization which is represented by the bot. Returns True on success.

        Telegram documentation: https://core.telegram.org/bots/api#verifyuser

        :param user_id: Unique identifier of the target user
        :type user_id: :obj:`int`

        :param custom_description: Custom description for the verification; 0-70 characters. Must be empty if the organization isn't allowed to provide a custom verification description.
        :type custom_description: :obj:`str`

        :return: Returns True on success.
        :rtype: :obj:`bool`
        """
        return apihelper.verify_user(self.token, user_id, custom_description=custom_description)

    def verify_chat(self, chat_id: Union[int, str], custom_description: Optional[str]=None) -> bool:
        """
        Verifies a chat on behalf of the organization which is represented by the bot. Returns True on success.

        Telegram documentation: https://core.telegram.org/bots/api#verifychat

        :param chat_id: Unique identifier for the target chat or username of the target channel (in the format @channelusername)
        :type chat_id: :obj:`int` | :obj:`str`

        :param custom_description: Custom description for the verification; 0-70 characters. Must be empty if the organization isn't allowed to provide a custom verification description.
        :type custom_description: :obj:`str`

        :return: Returns True on success.
        :rtype: :obj:`bool`
        """
        return apihelper.verify_chat(self.token, chat_id, custom_description=custom_description)

    def remove_user_verification(self, user_id: int) -> bool:
        """
        Removes verification from a user who is currently verified on behalf of the organization represented by the bot. Returns True on success.

        Telegram documentation: https://core.telegram.org/bots/api#removeuserverification

        :param user_id: Unique identifier of the target user
        :type user_id: :obj:`int`

        :return: Returns True on success.
        :rtype: :obj:`bool`
        """

        return apihelper.remove_user_verification(self.token, user_id)

    def remove_chat_verification(self, chat_id: int) -> bool:
        """
        Removes verification from a chat that is currently verified on behalf of the organization represented by the bot. Returns True on success.

        Telegram documentation: https://core.telegram.org/bots/api#removechatverification

        :param chat_id: Unique identifier for the target chat or username of the target channel (in the format @channelusername)
        :type chat_id: :obj:`int` | :obj:`str`

        :return: Returns True on success.
        :rtype: :obj:`bool`
        """
        return apihelper.remove_chat_verification(self.token, chat_id)

    def read_business_message(self, business_connection_id: str, chat_id: Union[int, str], message_id: int) -> bool:
        """
        Marks incoming message as read on behalf of a business account. Requires the can_read_messages business bot right. Returns True on success.

        Telegram documentation: https://core.telegram.org/bots/api#readbusinessmessage

        :param business_connection_id: Unique identifier of the business connection on behalf of which to read the message
        :type business_connection_id: :obj:`str`

        :param chat_id: Unique identifier of the chat in which the message was received. The chat must have been active in the last 24 hours.
        :type chat_id: :obj:`int` | :obj:`str`

        :param message_id: Unique identifier of the message to mark as read
        :type message_id: :obj:`int`

        :return: Returns True on success.
        :rtype: :obj:`bool`
        """
        return apihelper.read_business_message(self.token, business_connection_id, chat_id, message_id)

    def delete_business_messages(self, business_connection_id: str, message_ids: List[int]) -> bool:
        """
        Delete messages on behalf of a business account. Requires the can_delete_outgoing_messages business bot right to delete messages sent by the bot itself, or the can_delete_all_messages business bot right to delete any message. Returns True on success.

        Telegram documentation: https://core.telegram.org/bots/api#deletebusinessmessages

        :param business_connection_id: Unique identifier of the business connection on behalf of which to delete the messages
        :type business_connection_id: :obj:`str`

        :param message_ids: A JSON-serialized list of 1-100 identifiers of messages to delete. All messages must be from the same chat. See deleteMessage for limitations on which messages can be deleted
        :type message_ids: :obj:`list` of :obj:`int`

        :return: Returns True on success.
        :rtype: :obj:`bool`
        """
        return apihelper.delete_business_messages(self.token, business_connection_id, message_ids)

    def set_business_account_name(self, business_connection_id: str, first_name: str, last_name: Optional[str]=None) -> bool:
        """
        Changes the first and last name of a managed business account. Requires the can_change_name business bot right. Returns True on success.

        Telegram documentation: https://core.telegram.org/bots/api#setbusinessaccountname

        :param business_connection_id: Unique identifier of the business connection
        :type business_connection_id: :obj:`str`

        :param first_name: The new value of the first name for the business account; 1-64 characters
        :type first_name: :obj:`str`

        :param last_name: The new value of the last name for the business account; 0-64 characters
        :type last_name: :obj:`str`

        :return: Returns True on success.
        :rtype: :obj:`bool`
        """
        return apihelper.set_business_account_name(self.token, business_connection_id, first_name, last_name=last_name)

    def set_business_account_username(self, business_connection_id: str, username: Optional[str]=None) -> bool:
        """
        Changes the username of a managed business account. Requires the can_change_username business bot right. Returns True on success.

        Telegram documentation: https://core.telegram.org/bots/api#setbusinessaccountusername

        :param business_connection_id: Unique identifier of the business connection
        :type business_connection_id: :obj:`str`

        :param username: The new value of the username for the business account; 0-32 characters
        :type username: :obj:`str`

        :return: Returns True on success.
        :rtype: :obj:`bool`

        """
        return apihelper.set_business_account_username(self.token, business_connection_id, username=username)

    def set_business_account_bio(self, business_connection_id: str, bio: Optional[str]=None) -> bool:
        """
        Changes the bio of a managed business account. Requires the can_change_bio business bot right. Returns True on success.

        Telegram documentation: https://core.telegram.org/bots/api#setbusinessaccountbio

        :param business_connection_id: Unique identifier of the business connection
        :type business_connection_id: :obj:`str`

        :param bio: The new value of the bio for the business account; 0-140 characters
        :type bio: :obj:`str`

        :return: Returns True on success.
        :rtype: :obj:`bool`
        """
        return apihelper.set_business_account_bio(self.token, business_connection_id, bio=bio)

    def set_business_account_gift_settings(
            self, business_connection_id: str, show_gift_button: bool, accepted_gift_types: types.AcceptedGiftTypes) -> bool:
        """
        Changes the privacy settings pertaining to incoming gifts in a managed business account. Requires the can_change_gift_settings business bot right. Returns True on success.

        Telegram documentation: https://core.telegram.org/bots/api#setbusinessaccountgiftsettings

        :param business_connection_id: Unique identifier of the business connection
        :type business_connection_id: :obj:`str`

        :param show_gift_button: Pass True, if a button for sending a gift to the user or by the business account must always be shown in the input field
        :type show_gift_button: :obj:`bool`

        :param accepted_gift_types: Types of gifts accepted by the business account
        :type accepted_gift_types: :class:`telebot.types.AcceptedGiftTypes`

        :return: Returns True on success.
        :rtype: :obj:`bool`
        """
        return apihelper.set_business_account_gift_settings(self.token, business_connection_id, show_gift_button, accepted_gift_types)
    

    def get_business_account_star_balance(self, business_connection_id: str) -> types.StarAmount:
        """
        Returns the amount of Telegram Stars owned by a managed business account. Requires the can_view_gifts_and_stars business bot right. Returns StarAmount on success.
        
        Telegram documentation: https://core.telegram.org/bots/api#getbusinessaccountstarbalance

        :param business_connection_id: Unique identifier of the business connection
        :type business_connection_id: :obj:`str`

        :return: On success, a StarAmount object is returned.
        :rtype: :class:`telebot.types.StarAmount`
        """
        return types.StarAmount.de_json(
            apihelper.get_business_account_star_balance(self.token, business_connection_id)
        )
    
    def transfer_business_account_stars(self, business_connection_id: str, star_count: int) -> bool:
        """
        Transfers Telegram Stars from the business account balance to the bot's balance. Requires the can_transfer_stars business bot right. Returns True on success.

        Telegram documentation: https://core.telegram.org/bots/api#transferbusinessaccountstars

        :param business_connection_id: Unique identifier of the business connection
        :type business_connection_id: :obj:`str`

        :param star_count: Number of Telegram Stars to transfer; 1-10000
        :type star_count: :obj:`int`

        :return: Returns True on success.
        :rtype: :obj:`bool`
        """
        return apihelper.transfer_business_account_stars(self.token, business_connection_id, star_count)
    
    def get_business_account_gifts(
            self, business_connection_id: str,
            exclude_unsaved: Optional[bool]=None,
            exclude_saved: Optional[bool]=None,
            exclude_unlimited: Optional[bool]=None,
            exclude_limited: Optional[bool]=None,
            exclude_unique: Optional[bool]=None,
            sort_by_price: Optional[bool]=None,
            offset: Optional[str]=None,
            limit: Optional[int]=None) -> types.OwnedGifts:
        """
        Returns the gifts received and owned by a managed business account. Requires the can_view_gifts_and_stars business bot right. Returns OwnedGifts on success.
        
        Telegram documentation: https://core.telegram.org/bots/api#getbusinessaccountgifts

        :param business_connection_id: Unique identifier of the business connection
        :type business_connection_id: :obj:`str`

        :param exclude_unsaved: Pass True to exclude gifts that aren't saved to the account's profile page
        :type exclude_unsaved: :obj:`bool`

        :param exclude_saved: Pass True to exclude gifts that are saved to the account's profile page
        :type exclude_saved: :obj:`bool`

        :param exclude_unlimited: Pass True to exclude gifts that can be purchased an unlimited number of times
        :type exclude_unlimited: :obj:`bool`

        :param exclude_limited: Pass True to exclude gifts that can be purchased a limited number of times
        :type exclude_limited: :obj:`bool`

        :param exclude_unique: Pass True to exclude unique gifts
        :type exclude_unique: :obj:`bool`

        :param sort_by_price: Pass True to sort results by gift price instead of send date. Sorting is applied before pagination.
        :type sort_by_price: :obj:`bool`

        :param offset: Offset of the first entry to return as received from the previous request; use empty string to get the first chunk of results
        :type offset: :obj:`str`

        :param limit: The maximum number of gifts to be returned; 1-100. Defaults to 100
        :type limit: :obj:`int`

        :return: On success, a OwnedGifts object is returned.
        :rtype: :class:`telebot.types.OwnedGifts`
        """
        return types.OwnedGifts.de_json(
            apihelper.get_business_account_gifts(
                self.token, business_connection_id,
                exclude_unsaved=exclude_unsaved,
                exclude_saved=exclude_saved,
                exclude_unlimited=exclude_unlimited,
                exclude_limited=exclude_limited,
                exclude_unique=exclude_unique,
                sort_by_price=sort_by_price,
                offset=offset,
                limit=limit
            )
        )

    def convert_gift_to_stars(self, business_connection_id: str, owned_gift_id: str) -> bool:
        """
        Converts a given regular gift to Telegram Stars. Requires the can_convert_gifts_to_stars business bot right. Returns True on success.

        Telegram documentation: https://core.telegram.org/bots/api#convertgifttostars

        :param business_connection_id: Unique identifier of the business connection
        :type business_connection_id: :obj:`str`

        :param owned_gift_id: Unique identifier of the regular gift that should be converted to Telegram Stars
        :type owned_gift_id: :obj:`str`

        :return: Returns True on success.
        :rtype: :obj:`bool`
        """
        return apihelper.convert_gift_to_stars(self.token, business_connection_id, owned_gift_id)
    
    def upgrade_gift(
            self, business_connection_id: str, owned_gift_id: str,
            keep_original_details: Optional[bool]=None,
            star_count: Optional[int]=None) -> bool:
        """
        Upgrades a given regular gift to a unique gift. Requires the can_transfer_and_upgrade_gifts business bot right.
        Additionally requires the can_transfer_stars business bot right if the upgrade is paid. Returns True on success.

        Telegram documentation: https://core.telegram.org/bots/api#upgradegift

        :param business_connection_id: Unique identifier of the business connection
        :type business_connection_id: :obj:`str`

        :param owned_gift_id: Unique identifier of the regular gift that should be upgraded to a unique one
        :type owned_gift_id: :obj:`str`

        :param keep_original_details: Pass True to keep the original gift text, sender and receiver in the upgraded gift
        :type keep_original_details: :obj:`bool`

        :param star_count: The amount of Telegram Stars that will be paid for the upgrade from the business account balance.
            If gift.prepaid_upgrade_star_count > 0, then pass 0, otherwise, the can_transfer_stars business bot right is required and gift.upgrade_star_count must be passed.
        :type star_count: :obj:`int`

        :return: Returns True on success.
        :rtype: :obj:`bool`
        """
        return apihelper.upgrade_gift(
            self.token, business_connection_id, owned_gift_id,
            keep_original_details=keep_original_details,
            star_count=star_count
        )

    def transfer_gift(
            self, business_connection_id: str, owned_gift_id: str,
            new_owner_chat_id: int,
            star_count: Optional[int]=None) -> bool:
        """
        Transfers an owned unique gift to another user. Requires the can_transfer_and_upgrade_gifts business bot right.
        Requires can_transfer_stars business bot right if the transfer is paid. Returns True on success.

        Telegram documentation: https://core.telegram.org/bots/api#transfergift

        :param business_connection_id: Unique identifier of the business connection
        :type business_connection_id: :obj:`str`

        :param owned_gift_id: Unique identifier of the regular gift that should be transferred
        :type owned_gift_id: :obj:`str`

        :param new_owner_chat_id: Unique identifier of the chat which will own the gift. The chat must be active in the last 24 hours.
        :type new_owner_chat_id: :obj:`int`

        :param star_count: The amount of Telegram Stars that will be paid for the transfer from the business account balance.
            If positive, then the can_transfer_stars business bot right is required.
        :type star_count: :obj:`int`

        :return: Returns True on success.
        :rtype: :obj:`bool`
        """
        return apihelper.transfer_gift(
            self.token, business_connection_id, owned_gift_id,
            new_owner_chat_id,
            star_count=star_count
        )
    
    def post_story(
            self, business_connection_id: str, content: types.InputStoryContent,
            active_period: int, caption: Optional[str]=None,
            parse_mode: Optional[str]=None,
            caption_entities: Optional[List[types.MessageEntity]]=None,
            areas: Optional[List[types.StoryArea]]=None,
            post_to_chat_page: Optional[bool]=None,
            protect_content: Optional[bool]=None) -> types.Story:

        """
        Posts a story on behalf of a managed business account. Requires the can_manage_stories business bot right. Returns Story on success.

        Telegram documentation: https://core.telegram.org/bots/api#poststory

        :param business_connection_id: Unique identifier of the business connection
        :type business_connection_id: :obj:`str`

        :param content: Content of the story
        :type content: :class:`telebot.types.InputStoryContent`

        :param active_period: Period after which the story is moved to the archive, in seconds; must be one of 6 * 3600, 12 * 3600, 86400, or 2 * 86400
        :type active_period: :obj:`int`

        :param caption: Caption of the story, 0-2048 characters after entities parsing
        :type caption: :obj:`str`

        :param parse_mode: Mode for parsing entities in the story caption. See formatting options for more details.
        :type parse_mode: :obj:`str`

        :param caption_entities: A JSON-serialized list of special entities that appear in the caption, which can be specified instead of parse_mode
        :type caption_entities: :obj:`list` of :class:`telebot.types.MessageEntity`

        :param areas: A JSON-serialized list of clickable areas to be shown on the story
        :type areas: :obj:`list` of :class:`telebot.types.StoryArea`

        :param post_to_chat_page: Pass True to keep the story accessible after it expires
        :type post_to_chat_page: :obj:`bool`

        :param protect_content: Pass True if the content of the story must be protected from forwarding and screenshotting
        :type protect_content: :obj:`bool`

        :return: On success, a Story object is returned.
        :rtype: :class:`telebot.types.Story`
        """
        return types.Story.de_json(
            apihelper.post_story(
                self.token, business_connection_id, content,
                active_period, caption=caption,
                parse_mode=parse_mode,
                caption_entities=caption_entities,
                areas=areas,
                post_to_chat_page=post_to_chat_page,
                protect_content=protect_content
            )
        )

    def edit_story(
            self, business_connection_id: str, story_id: int,
            content: types.InputStoryContent,
            caption: Optional[str]=None,
            parse_mode: Optional[str]=None,
            caption_entities: Optional[List[types.MessageEntity]]=None,
            areas: Optional[List[types.StoryArea]]=None) -> types.Story:
        """
        Edits a story previously posted by the bot on behalf of a managed business account. Requires the can_manage_stories business bot right. Returns Story on success.

        Telegram documentation: https://core.telegram.org/bots/api#editstory

        :param business_connection_id: Unique identifier of the business connection
        :type business_connection_id: :obj:`str`

        :param story_id: Unique identifier of the story to edit
        :type story_id: :obj:`int`

        :param content: Content of the story
        :type content: :class:`telebot.types.InputStoryContent`

        :param caption: Caption of the story, 0-2048 characters after entities parsing
        :type caption: :obj:`str`

        :param parse_mode: Mode for parsing entities in the story caption. See formatting options for more details.
        :type parse_mode: :obj:`str`

        :param caption_entities: A JSON-serialized list of special entities that appear in the caption, which can be specified instead of parse_mode
        :type caption_entities: :obj:`list` of :class:`telebot.types.MessageEntity`

        :param areas: A JSON-serialized list of clickable areas to be shown on the story
        :type areas: :obj:`list` of :class:`telebot.types.StoryArea`

        :return: On success, a Story object is returned.
        :rtype: :class:`telebot.types.Story`

        """
        return types.Story.de_json(
            apihelper.edit_story(
                self.token, business_connection_id, story_id,
                content, caption=caption,
                parse_mode=parse_mode,
                caption_entities=caption_entities,
                areas=areas
            )
    )

    def delete_story(self, business_connection_id: str, story_id: int) -> bool:
        """
        Deletes a story previously posted by the bot on behalf of a managed business account. Requires the can_manage_stories business bot right. Returns True on success.
        
        Telegram documentation: https://core.telegram.org/bots/api#deletestory

        :param business_connection_id: Unique identifier of the business connection
        :type business_connection_id: :obj:`str`

        :param story_id: Unique identifier of the story to delete
        :type story_id: :obj:`int`

        :return: Returns True on success.
        :rtype: :obj:`bool`
        """
        return apihelper.delete_story(self.token, business_connection_id, story_id)

    def gift_premium_subscription(
            self, user_id: int, month_count: int, star_count: int,
            text: Optional[str]=None, text_parse_mode: Optional[str]=None,
            text_entities: Optional[List[types.MessageEntity]]=None) -> bool:
        """
        Gifts a Telegram Premium subscription to the given user. Returns True on success.

        Telegram documentation: https://core.telegram.org/bots/api#giftpremiumsubscription

        :param user_id: Unique identifier of the target user who will receive a Telegram Premium subscription
        :type user_id: :obj:`int`

        :param month_count: Number of months the Telegram Premium subscription will be active for the user; must be one of 3, 6, or 12
        :type month_count: :obj:`int`

        :param star_count: Number of Telegram Stars to pay for the Telegram Premium subscription; must be 1000 for 3 months, 1500 for 6 months, and 2500 for 12 months
        :type star_count: :obj:`int`

        :param text: Text that will be shown along with the service message about the subscription; 0-128 characters
        :type text: :obj:`str`

        :param text_parse_mode: Mode for parsing entities in the text. See formatting options for more details. Entities other than “bold”, “italic”, “underline”, “strikethrough”, “spoiler”, and “custom_emoji” are ignored.
        :type text_parse_mode: :obj:`str`

        :param text_entities: A JSON-serialized list of special entities that appear in the gift text. It can be specified instead of text_parse_mode. Entities other than “bold”, “italic”, “underline”, “strikethrough”, “spoiler”, and “custom_emoji” are ignored.
        :type text_entities: :obj:`list` of :class:`telebot.types.MessageEntity`

        :return: Returns True on success.
        :rtype: :obj:`bool`
        """
        return apihelper.gift_premium_subscription(
            self.token, user_id, month_count, star_count,
            text=text, text_parse_mode=text_parse_mode,
            text_entities=text_entities
        )
    
    def set_business_account_profile_photo(
            self, business_connection_id: str, photo: types.InputProfilePhoto,
            is_public: Optional[bool]=None) -> bool:
        """
        Changes the profile photo of a managed business account. Requires the can_edit_profile_photo business bot right. Returns True on success.

        Telegram documentation: https://core.telegram.org/bots/api#setbusinessaccountprofilephoto

        :param business_connection_id: Unique identifier of the business connection
        :type business_connection_id: :obj:`str`

        :param photo: The new profile photo to set
        :type photo: :class:`telebot.types.InputProfilePhoto`

        :param is_public: Pass True to set the public photo, which will be visible even if the main photo is hidden by the business account's privacy settings. An account can have only one public photo.
        :type is_public: :obj:`bool`

        :return: Returns True on success.
        :rtype: :obj:`bool`
        """
        return apihelper.set_business_account_profile_photo(self.token, business_connection_id, photo, is_public=is_public)


    def remove_business_account_profile_photo(
            self, business_connection_id: str,
            is_public: Optional[bool]=None) -> bool:
        """
        Removes the current profile photo of a managed business account. Requires the can_edit_profile_photo business bot right. Returns True on success.

        Telegram documentation: https://core.telegram.org/bots/api#removebusinessaccountprofilephoto

        :param business_connection_id: Unique identifier of the business connection
        :type business_connection_id: :obj:`str`

        :param is_public: Pass True to remove the public photo, which is visible even if the main photo is hidden by the business account's privacy settings. After the main photo is removed, the previous profile photo (if present) becomes the main photo.
        :type is_public: :obj:`bool`

        :return: Returns True on success.
        :rtype: :obj:`bool`
        """
        return apihelper.remove_business_account_profile_photo(self.token, business_connection_id, is_public=is_public)

    def get_available_gifts(self) -> types.Gifts:
        """
        Returns the list of gifts that can be sent by the bot to users. Requires no parameters. Returns a Gifts object.

        Telegram documentation: https://core.telegram.org/bots/api#getavailablegifts

        :return: On success, a Gifts object is returned.
        :rtype: :class:`telebot.types.Gifts`
        """
        return types.Gifts.de_json(
            apihelper.get_available_gifts(self.token)
        )

    def replace_sticker_in_set(self, user_id: int, name: str, old_sticker: str, sticker: types.InputSticker) -> bool:
        """
        Use this method to replace an existing sticker in a sticker set with a new one. The method is equivalent to calling deleteStickerFromSet, then addStickerToSet,
            then setStickerPositionInSet. Returns True on success.

        Telegram documentation: https://core.telegram.org/bots/api#replaceStickerInSet

        :param user_id: User identifier of the sticker set owner
        :type user_id: :obj:`int`

        :param name: Sticker set name
        :type name: :obj:`str`

        :param old_sticker: File identifier of the replaced sticker
        :type old_sticker: :obj:`str`

        :param sticker: A JSON-serialized object with information about the added sticker. If exactly the same sticker had already been added to the set, then the set remains unchanged.
        :type sticker: :class:`telebot.types.InputSticker`

        :return: Returns True on success.
        :rtype: :obj:`bool`
        """
        return apihelper.replace_sticker_in_set(self.token, user_id, name, old_sticker, sticker)
    
    
    def set_sticker_emoji_list(self, sticker: str, emoji_list: List[str]) -> bool:
        """
        Use this method to set the emoji list of a custom emoji sticker set.
        Returns True on success.

        :param sticker: Sticker identifier
        :type sticker: :obj:`str`

        :param emoji_list: List of emoji
        :type emoji_list: :obj:`list` of :obj:`str`

        :return: Returns True on success.
        :rtype: :obj:`bool`
        """
        return apihelper.set_sticker_emoji_list(self.token, sticker, emoji_list)


    def upload_sticker_file(self, user_id: int, png_sticker: Union[Any, str]=None, sticker: Optional[types.InputFile]=None, sticker_format: Optional[str]=None) -> types.File:
        """
        Use this method to upload a .png file with a sticker for later use in createNewStickerSet and addStickerToSet
        methods (can be used multiple times). Returns the uploaded File on success.
        
        Telegram documentation: https://core.telegram.org/bots/api#uploadstickerfile

        :param user_id: User identifier of sticker set owner
        :type user_id: :obj:`int`

        :param png_sticker: DEPRECATED: PNG image with the sticker, must be up to 512 kilobytes in size, dimensions must not exceed 512px,
            and either width or height must be exactly 512px.
        :type png_sticker: :obj:`filelike object`

        :param sticker: A file with the sticker in .WEBP, .PNG, .TGS, or .WEBM format.
            See https://core.telegram.org/stickers for technical requirements. More information on Sending Files »
        :type sticker: :class:`telebot.types.InputFile`

        :param sticker_format: One of "static", "animated", "video". 
        :type sticker_format: :obj:`str`

        :return: On success, the sent file is returned.
        :rtype: :class:`telebot.types.File`
        """
        if png_sticker:
            logger.warning('The parameter "png_sticker" is deprecated. Use "sticker" instead.')
            sticker = png_sticker
            sticker_format = "static"
        
        return types.File.de_json(
            apihelper.upload_sticker_file(self.token, user_id, sticker, sticker_format)
        )


    def create_new_sticker_set(
            self, user_id: int, name: str, title: str, 
            emojis: Optional[List[str]]=None, 
            png_sticker: Union[Any, str]=None, 
            tgs_sticker: Union[Any, str]=None, 
            webm_sticker: Union[Any, str]=None,
            contains_masks: Optional[bool]=None,
            sticker_type: Optional[str]=None,
            mask_position: Optional[types.MaskPosition]=None,
            needs_repainting: Optional[bool]=None,
            stickers: List[types.InputSticker]=None,
            sticker_format: Optional[str]=None) -> bool:
        """
        Use this method to create new sticker set owned by a user. 
        The bot will be able to edit the created sticker set.
        Returns True on success.

        Telegram documentation: https://core.telegram.org/bots/api#createnewstickerset

        .. note::
            Fields *_sticker are deprecated, pass a list of stickers to stickers parameter instead.

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

        :param sticker_type: Type of stickers in the set, pass “regular”, “mask”, or “custom_emoji”. By default, a regular sticker set is created.
        :type sticker_type: :obj:`str`

        :param mask_position: A JSON-serialized object for position where the mask should be placed on faces
        :type mask_position: :class:`telebot.types.MaskPosition`

        :param needs_repainting: Pass True if stickers in the sticker set must be repainted to the color of text when used in messages,
            the accent color if used as emoji status, white on chat photos, or another appropriate color based on context;
            for custom emoji sticker sets only
        :type needs_repainting: :obj:`bool`

        :param stickers: List of stickers to be added to the set
        :type stickers: :obj:`list` of :class:`telebot.types.InputSticker`

        :param sticker_format: deprecated
        :type sticker_format: :obj:`str`

        :return: On success, True is returned.
        :rtype: :obj:`bool`
        """
        if tgs_sticker:
            sticker_format = 'animated'
        elif webm_sticker:
            sticker_format = 'video'
        elif png_sticker:
            sticker_format = 'static'
        
        if contains_masks is not None:
            logger.warning('The parameter "contains_masks" is deprecated, use "sticker_type" instead')
            if sticker_type is None:
               sticker_type = 'mask' if contains_masks else 'regular'

        if stickers is None:
            stickers = png_sticker or tgs_sticker or webm_sticker
            if stickers is None:
                raise ValueError('You must pass at least one sticker')
            stickers = [types.InputSticker(sticker=stickers, emoji_list=emojis, mask_position=mask_position)]

        if sticker_format:
            logger.warning('The parameter "sticker_format" is deprecated since Bot API 7.2. Stickers can now be mixed')

        return apihelper.create_new_sticker_set(
            self.token, user_id, name, title, stickers, sticker_type=sticker_type, needs_repainting=needs_repainting)


    def add_sticker_to_set(
            self, user_id: int, name: str, emojis: Union[List[str], str],
            png_sticker: Optional[Union[Any, str]]=None, 
            tgs_sticker: Optional[Union[Any, str]]=None,  
            webm_sticker: Optional[Union[Any, str]]=None,
            mask_position: Optional[types.MaskPosition]=None,
            sticker: Optional[types.InputSticker]=None) -> bool:
        """
        Use this method to add a new sticker to a set created by the bot.
        The format of the added sticker must match the format of the other stickers in the set.
        Emoji sticker sets can have up to 200 stickers. Animated and video sticker sets can have up to 50 stickers.
        Static sticker sets can have up to 120 stickers.
        Returns True on success.

        Telegram documentation: https://core.telegram.org/bots/api#addstickertoset

        .. note::
            **_sticker, mask_position, emojis parameters are deprecated, use stickers instead

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

        :param sticker: A JSON-serialized object for sticker to be added to the sticker set
        :type sticker: :class:`telebot.types.InputSticker`

        :return: On success, True is returned.
        :rtype: :obj:`bool`
        """

        # split emojis if string
        if isinstance(emojis, str):
            emojis = list(emojis)
        # Replaced the parameters png_sticker, tgs_sticker, webm_sticker, emojis and mask_position
        if sticker is None:
            old_sticker = png_sticker or tgs_sticker or webm_sticker
            if old_sticker is not None:
                logger.warning('The parameters "..._sticker", "emojis" and "mask_position" are deprecated, use "sticker" instead')
            if not old_sticker:
                raise ValueError('You must pass at least one sticker.')
            sticker = types.InputSticker(old_sticker, emojis, mask_position)

        return apihelper.add_sticker_to_set(self.token, user_id, name, sticker)


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


    def create_forum_topic(self,
            chat_id: int, name: str, icon_color: Optional[int]=None,
            icon_custom_emoji_id: Optional[str]=None) -> types.ForumTopic:
        """
        Use this method to create a topic in a forum supergroup chat. The bot must be an administrator
        in the chat for this to work and must have the can_manage_topics administrator rights.
        Returns information about the created topic as a ForumTopic object.

        Telegram documentation: https://core.telegram.org/bots/api#createforumtopic

        :param chat_id: Unique identifier for the target chat or username of the target channel (in the format @channelusername)
        :type chat_id: :obj:`int` or :obj:`str`

        :param name: Name of the topic, 1-128 characters
        :type name: :obj:`str`

        :param icon_color: Color of the topic icon in RGB format. Currently, must be one of 0x6FB9F0, 0xFFD67E, 0xCB86DB, 0x8EEE98, 0xFF93B2, or 0xFB6F5F
        :type icon_color: :obj:`int`

        :param icon_custom_emoji_id: Custom emoji for the topic icon. Must be an emoji of type “tgs” and must be exactly 1 character long
        :type icon_custom_emoji_id: :obj:`str`

        :return: On success, information about the created topic is returned as a ForumTopic object.
        :rtype: :class:`telebot.types.ForumTopic`
        """
        return types.ForumTopic.de_json(
            apihelper.create_forum_topic(
                self.token, chat_id, name, icon_color=icon_color, icon_custom_emoji_id=icon_custom_emoji_id)
        )


    def edit_forum_topic(
            self, chat_id: Union[int, str],
            message_thread_id: int, name: Optional[str]=None,
            icon_custom_emoji_id: Optional[str]=None
        ) -> bool:
        """
        Use this method to edit name and icon of a topic in a forum supergroup chat. The bot must be an
        administrator in the chat for this to work and must have can_manage_topics administrator rights,
        unless it is the creator of the topic. Returns True on success.

        Telegram Documentation: https://core.telegram.org/bots/api#editforumtopic

        :param chat_id: Unique identifier for the target chat or username of the target channel (in the format @channelusername)
        :type chat_id: :obj:`int` or :obj:`str`

        :param message_thread_id: Identifier of the topic to edit
        :type message_thread_id: :obj:`int`

        :param name: Optional, New name of the topic, 1-128 characters. If not specififed or empty,
            the current name of the topic will be kept
        :type name: :obj:`str`

        :param icon_custom_emoji_id: Optional, New unique identifier of the custom emoji shown as the topic icon.
            Use getForumTopicIconStickers to get all allowed custom emoji identifiers. Pass an empty string to remove the
            icon. If not specified, the current icon will be kept
        :type icon_custom_emoji_id: :obj:`str`

        :return: On success, True is returned.
        :rtype: :obj:`bool`
        """
        return apihelper.edit_forum_topic(
            self.token, chat_id, message_thread_id, name=name, icon_custom_emoji_id=icon_custom_emoji_id)


    def close_forum_topic(self, chat_id: Union[str, int], message_thread_id: int) -> bool:
        """
        Use this method to close an open topic in a forum supergroup chat. The bot must be an administrator
        in the chat for this to work and must have the can_manage_topics administrator rights, unless it is
        the creator of the topic. Returns True on success.

        Telegram documentation: https://core.telegram.org/bots/api#closeforumtopic

        :aram chat_id: Unique identifier for the target chat or username of the target channel (in the format @channelusername)
        :type chat_id: :obj:`int` or :obj:`str`

        :param message_thread_id: Identifier of the topic to close
        :type message_thread_id: :obj:`int`

        :return: On success, True is returned.
        :rtype: :obj:`bool`
        """
        return apihelper.close_forum_topic(self.token, chat_id, message_thread_id)


    def reopen_forum_topic(self, chat_id: Union[str, int], message_thread_id: int) -> bool:
        """
        Use this method to reopen a closed topic in a forum supergroup chat. The bot must be an administrator in the chat
        for this to work and must have the can_manage_topics administrator rights, unless it is the creator of the topic.
        Returns True on success.

        Telegram documentation: https://core.telegram.org/bots/api#reopenforumtopic

        :param chat_id: Unique identifier for the target chat or username of the target channel (in the format @channelusername)
        :type chat_id: :obj:`int` or :obj:`str`

        :param message_thread_id: Identifier of the topic to reopen
        :type message_thread_id: :obj:`int`

        :return: On success, True is returned.
        :rtype: :obj:`bool`
        """
        return apihelper.reopen_forum_topic(self.token, chat_id, message_thread_id)


    def delete_forum_topic(self, chat_id: Union[str, int], message_thread_id: int) -> bool:
        """
        Use this method to delete a topic in a forum supergroup chat. The bot must be an administrator in the chat for this
        to work and must have the can_manage_topics administrator rights, unless it is the creator of the topic. Returns True
        on success.

        Telegram documentation: https://core.telegram.org/bots/api#deleteforumtopic

        :param chat_id: Unique identifier for the target chat or username of the target channel (in the format @channelusername)
        :type chat_id: :obj:`int` or :obj:`str`

        :param message_thread_id: Identifier of the topic to delete
        :type message_thread_id: :obj:`int`

        :return: On success, True is returned.
        :rtype: :obj:`bool`
        """
        return apihelper.delete_forum_topic(self.token, chat_id, message_thread_id)


    def unpin_all_forum_topic_messages(self, chat_id: Union[str, int], message_thread_id: int) -> bool:
        """
        Use this method to clear the list of pinned messages in a forum topic. The bot must be an administrator in the
        chat for this to work and must have the can_pin_messages administrator right in the supergroup.
        Returns True on success.

        Telegram documentation: https://core.telegram.org/bots/api#unpinallforumtopicmessages

        :param chat_id: Unique identifier for the target chat or username of the target channel (in the format @channelusername)
        :type chat_id: :obj:`int` or :obj:`str`

        :param message_thread_id: Identifier of the topic
        :type message_thread_id: :obj:`int`

        :return: On success, True is returned.
        :rtype: :obj:`bool`
        """
        return apihelper.unpin_all_forum_topic_messages(self.token, chat_id, message_thread_id)


    def edit_general_forum_topic(self, chat_id: Union[int, str], name: str) -> bool:
        """
        Use this method to edit the name of the 'General' topic in a forum supergroup chat.
        The bot must be an administrator in the chat for this to work and must have can_manage_topics administrator rights.
        Returns True on success.
        
        Telegram documentation: https://core.telegram.org/bots/api#editgeneralforumtopic
        
        :param chat_id: Unique identifier for the target chat or username of the target channel (in the format @channelusername)
        :type chat_id: :obj:`int` or :obj:`str`

        :param name: New topic name, 1-128 characters
        :type name: :obj:`str`
        """
        return apihelper.edit_general_forum_topic(self.token, chat_id, name)


    def close_general_forum_topic(self, chat_id: Union[int, str]) -> bool:
        """
        Use this method to close the 'General' topic in a forum supergroup chat.
        The bot must be an administrator in the chat for this to work and must have can_manage_topics administrator rights.
        Returns True on success.

        Telegram documentation: https://core.telegram.org/bots/api#closegeneralforumtopic

        :param chat_id: Unique identifier for the target chat or username of the target channel (in the format @channelusername)
        :type chat_id: :obj:`int` or :obj:`str`
        """
        return apihelper.close_general_forum_topic(self.token, chat_id)


    def reopen_general_forum_topic(self, chat_id: Union[int, str]) -> bool:
        """
        Use this method to reopen the 'General' topic in a forum supergroup chat.
        The bot must be an administrator in the chat for this to work and must have can_manage_topics administrator rights.
        Returns True on success.

        Telegram documentation: https://core.telegram.org/bots/api#reopengeneralforumtopic

        :param chat_id: Unique identifier for the target chat or username of the target channel (in the format @channelusername)
        :type chat_id: :obj:`int` or :obj:`str`
        """
        return apihelper.reopen_general_forum_topic(self.token, chat_id)


    def hide_general_forum_topic(self, chat_id: Union[int, str]) -> bool:
        """
        Use this method to hide the 'General' topic in a forum supergroup chat.
        The bot must be an administrator in the chat for this to work and must have can_manage_topics administrator rights.
        Returns True on success.

        Telegram documentation: https://core.telegram.org/bots/api#hidegeneralforumtopic

        :param chat_id: Unique identifier for the target chat or username of the target channel (in the format @channelusername)
        :type chat_id: :obj:`int` or :obj:`str`
        """
        return apihelper.hide_general_forum_topic(self.token, chat_id)


    def unhide_general_forum_topic(self, chat_id: Union[int, str]) -> bool:
        """
        Use this method to unhide the 'General' topic in a forum supergroup chat.
        The bot must be an administrator in the chat for this to work and must have can_manage_topics administrator rights.
        Returns True on success.

        Telegram documentation: https://core.telegram.org/bots/api#unhidegeneralforumtopic

        :param chat_id: Unique identifier for the target chat or username of the target channel (in the format @channelusername)
        :type chat_id: :obj:`int` or :obj:`str`
        """
        return apihelper.unhide_general_forum_topic(self.token, chat_id)


    def get_forum_topic_icon_stickers(self) -> List[types.Sticker]:
        """
        Use this method to get custom emoji stickers, which can be used as a forum topic icon by any user.
        Requires no parameters. Returns an Array of Sticker objects.

        Telegram documentation: https://core.telegram.org/bots/api#getforumtopiciconstickers

        :return: On success, a list of StickerSet objects is returned.
        :rtype: List[:class:`telebot.types.StickerSet`]
        """
        return apihelper.get_forum_topic_icon_stickers(self.token)


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

    def save_prepared_inline_message(
            self, user_id: int, result: types.InlineQueryResultBase, allow_user_chats: Optional[bool]=None,
            allow_bot_chats: Optional[bool]=None, allow_group_chats: Optional[bool]=None,
            allow_channel_chats: Optional[bool]=None) -> types.PreparedInlineMessage:
        """
        Use this method to store a message that can be sent by a user of a Mini App.
        Returns a PreparedInlineMessage object.

        Telegram Documentation: https://core.telegram.org/bots/api#savepreparedinlinemessage

        :param user_id: Unique identifier of the target user that can use the prepared message
        :type user_id: :obj:`int`

        :param result: A JSON-serialized object describing the message to be sent
        :type result: :class:`telebot.types.InlineQueryResultBase`

        :param allow_user_chats: Pass True if the message can be sent to private chats with users
        :type allow_user_chats: :obj:`bool`

        :param allow_bot_chats: Pass True if the message can be sent to private chats with bots
        :type allow_bot_chats: :obj:`bool`

        :param allow_group_chats: Pass True if the message can be sent to group and supergroup chats
        :type allow_group_chats: :obj:`bool`

        :param allow_channel_chats: Pass True if the message can be sent to channel chats
        :type allow_channel_chats: :obj:`bool`

        :return: On success, a PreparedInlineMessage object is returned.
        :rtype: :class:`telebot.types.PreparedInlineMessage`
        """
        return types.PreparedInlineMessage.de_json(
            apihelper.save_prepared_inline_message(
                self.token, user_id, result, allow_user_chats=allow_user_chats, allow_bot_chats=allow_bot_chats,
                allow_group_chats=allow_group_chats, allow_channel_chats=allow_channel_chats)
        )

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
        self.register_for_reply_by_message_id(message.message_id, callback, *args, **kwargs)


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
        self.register_next_step_handler_by_chat_id(message.chat.id, callback, *args, **kwargs)


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


    def set_state(self, user_id: int, state: Union[str, State], chat_id: Optional[int]=None,
                    business_connection_id: Optional[str]=None, message_thread_id: Optional[int]=None,
                    bot_id: Optional[int]=None) -> bool:
        """
        Sets a new state of a user.

        .. note::

            You should set both user id and chat id in order to set state for a user in a chat.
            Otherwise, if you only set user_id, chat_id will equal to user_id, this means that
            state will be set for the user in his private chat with a bot.

        .. versionchanged:: 4.23.0

            Added additional parameters to support topics, business connections, and message threads.

        .. seealso:: 
        
            For more details, visit the `custom_states.py example <https://github.com/eternnoir/pyTelegramBotAPI/blob/master/examples/custom_states.py>`_.

        :param user_id: User's identifier
        :type user_id: :obj:`int`

        :param state: new state. can be string, or :class:`telebot.types.State`
        :type state: :obj:`int` or :obj:`str` or :class:`telebot.types.State`

        :param chat_id: Chat's identifier
        :type chat_id: :obj:`int`

        :param bot_id: Bot's identifier, defaults to current bot id
        :type bot_id: :obj:`int`

        :param business_connection_id: Business identifier
        :type business_connection_id: :obj:`str`

        :param message_thread_id: Identifier of the message thread
        :type message_thread_id: :obj:`int`

        :return: True on success
        :rtype: :obj:`bool`
        """
        if chat_id is None:
            chat_id = user_id
        if bot_id is None:
            bot_id = self.bot_id
        return self.current_states.set_state(chat_id, user_id, state,
            bot_id=bot_id, business_connection_id=business_connection_id, message_thread_id=message_thread_id)


    def reset_data(self, user_id: int, chat_id: Optional[int]=None, 
                     business_connection_id: Optional[str]=None,
                     message_thread_id: Optional[int]=None, bot_id: Optional[int]=None) -> bool:
        """
        Reset data for a user in chat: sets the 'data' field to an empty dictionary.

        :param user_id: User's identifier
        :type user_id: :obj:`int`

        :param chat_id: Chat's identifier
        :type chat_id: :obj:`int`

        :param bot_id: Bot's identifier, defaults to current bot id
        :type bot_id: :obj:`int`

        :param business_connection_id: Business identifier
        :type business_connection_id: :obj:`str`

        :param message_thread_id: Identifier of the message thread
        :type message_thread_id: :obj:`int`

        :return: True on success
        :rtype: :obj:`bool`
        """
        if chat_id is None:
            chat_id = user_id
        if bot_id is None:
            bot_id = self.bot_id
        return self.current_states.reset_data(chat_id, user_id,
            bot_id=bot_id, business_connection_id=business_connection_id, message_thread_id=message_thread_id)


    def delete_state(self, user_id: int, chat_id: Optional[int]=None, business_connection_id: Optional[str]=None,
                     message_thread_id: Optional[int]=None, bot_id: Optional[int]=None) -> bool:
        """
        Fully deletes the storage record of a user in chat.

        .. warning::

            This does NOT set state to None, but deletes the object from storage.

        :param user_id: User's identifier
        :type user_id: :obj:`int`
        
        :param chat_id: Chat's identifier
        :type chat_id: :obj:`int`

        :param bot_id: Bot's identifier, defaults to current bot id
        :type bot_id: :obj:`int`

        :param business_connection_id: Business identifier
        :type business_connection_id: :obj:`str`

        :param message_thread_id: Identifier of the message thread
        :type message_thread_id: :obj:`int`

        :return: True on success
        :rtype: :obj:`bool`
        """
        if chat_id is None:
            chat_id = user_id
        if bot_id is None:
            bot_id = self.bot_id
        return self.current_states.delete_state(chat_id, user_id,
            bot_id=bot_id, business_connection_id=business_connection_id, message_thread_id=message_thread_id)


    def retrieve_data(self, user_id: int, chat_id: Optional[int]=None, business_connection_id: Optional[str]=None,
                      message_thread_id: Optional[int]=None, bot_id: Optional[int]=None) -> Optional[Dict[str, Any]]:
        """
        Returns context manager with data for a user in chat.

        :param user_id: User identifier
        :type user_id: int

        :param chat_id: Chat's unique identifier, defaults to user_id
        :type chat_id: int, optional

        :param bot_id: Bot's identifier, defaults to current bot id
        :type bot_id: int, optional

        :param business_connection_id: Business identifier
        :type business_connection_id: str, optional

        :param message_thread_id: Identifier of the message thread
        :type message_thread_id: int, optional

        :return: Context manager with data for a user in chat
        :rtype: Optional[Any]
        """
        if chat_id is None:
            chat_id = user_id
        if bot_id is None:
            bot_id = self.bot_id
        return self.current_states.get_interactive_data(chat_id, user_id,
            bot_id=bot_id, business_connection_id=business_connection_id, message_thread_id=message_thread_id)


    def get_state(self, user_id: int, chat_id: Optional[int]=None, 
                    business_connection_id: Optional[str]=None,
                    message_thread_id: Optional[int]=None, bot_id: Optional[int]=None) -> str:
        """
        Gets current state of a user.
        Not recommended to use this method. But it is ok for debugging.

        .. warning::

            Even if you are using :class:`telebot.types.State`, this method will return a string.
            When comparing(not recommended), you should compare this string with :class:`telebot.types.State`.name

        :param user_id: User's identifier
        :type user_id: :obj:`int`

        :param chat_id: Chat's identifier
        :type chat_id: :obj:`int`

        :param bot_id: Bot's identifier, defaults to current bot id
        :type bot_id: :obj:`int`

        :param business_connection_id: Business identifier
        :type business_connection_id: :obj:`str`

        :param message_thread_id: Identifier of the message thread
        :type message_thread_id: :obj:`int`

        :return: state of a user
        :rtype: :obj:`int` or :obj:`str` or :class:`telebot.types.State`
        """
        if chat_id is None:
            chat_id = user_id
        if bot_id is None:
            bot_id = self.bot_id
        return self.current_states.get_state(chat_id, user_id,
            bot_id=bot_id, business_connection_id=business_connection_id, message_thread_id=message_thread_id)


    def add_data(self, user_id: int, chat_id: Optional[int]=None, 
                    business_connection_id: Optional[str]=None,
                    message_thread_id: Optional[int]=None, 
                    bot_id: Optional[int]=None,
                    **kwargs) -> None:
        """
        Add data to states.

        :param user_id: User's identifier
        :type user_id: :obj:`int`

        :param chat_id: Chat's identifier
        :type chat_id: :obj:`int`

        :param bot_id: Bot's identifier, defaults to current bot id
        :type bot_id: :obj:`int`

        :param business_connection_id: Business identifier
        :type business_connection_id: :obj:`str`

        :param message_thread_id: Identifier of the message thread
        :type message_thread_id: :obj:`int`

        :param kwargs: Data to add
        :return: None
        """
        if chat_id is None:
            chat_id = user_id
        if bot_id is None:
            bot_id = self.bot_id
        for key, value in kwargs.items():
            self.current_states.set_data(chat_id, user_id, key, value,
                bot_id=bot_id, business_connection_id=business_connection_id, message_thread_id=message_thread_id)


    def register_next_step_handler_by_chat_id(
            self, chat_id: int, callback: Callable, *args, **kwargs) -> None:
        """
        Registers a callback function to be notified when new message arrives in the given chat.

        Warning: In case `callback` as lambda function, saving next step handlers will not work.

        :param chat_id: The chat (chat ID) for which we want to handle new message.
        :type chat_id: :obj:`int`

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
        self.clear_step_handler_by_chat_id(message.chat.id)


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
        self.clear_reply_handlers_by_message_id(message.message_id)


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


    def message_handler(
            self,
            commands: Optional[List[str]]=None,
            regexp: Optional[str]=None,
            func: Optional[Callable]=None,
            content_types: Optional[List[str]]=None,
            chat_types: Optional[List[str]]=None,
            **kwargs):
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

        :param regexp: Regular expression
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


    def register_channel_post_handler(
            self, callback: Callable, content_types: Optional[List[str]]=None, commands: Optional[List[str]]=None,
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


    def register_edited_channel_post_handler(
            self, callback: Callable, content_types: Optional[List[str]]=None, commands: Optional[List[str]]=None,
            regexp: Optional[str]=None, func: Optional[Callable]=None, pass_bot: Optional[bool]=False, **kwargs):
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


    def message_reaction_handler(self, func=None, **kwargs):
        """
        Handles new incoming message reaction.
        As a parameter to the decorator function, it passes :class:`telebot.types.MessageReactionUpdated` object.

        :param func: Function executed as a filter
        :type func: :obj:`function`

        :param kwargs: Optional keyword arguments(custom filters)

        :return:
        """
        def decorator(handler):
            handler_dict = self._build_handler_dict(handler, func=func, **kwargs)
            self.add_message_reaction_handler(handler_dict)
            return handler

        return decorator


    def add_message_reaction_handler(self, handler_dict):
        """
        Adds message reaction handler
        Note that you should use register_message_reaction_handler to add message_reaction_handler to the bot.

        :meta private:

        :param handler_dict:
        :return:
        """
        self.message_reaction_handlers.append(handler_dict)


    def register_message_reaction_handler(self, callback: Callable, func: Callable=None, pass_bot: Optional[bool]=False, **kwargs):
        """
        Registers message reaction handler.

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
        self.add_message_reaction_handler(handler_dict)


    def message_reaction_count_handler(self, func=None, **kwargs):
        """
        Handles new incoming message reaction count.
        As a parameter to the decorator function, it passes :class:`telebot.types.MessageReactionCountUpdated` object.

        :param func: Function executed as a filter
        :type func: :obj:`function`

        :param kwargs: Optional keyword arguments(custom filters)

        :return:
        """
        def decorator(handler):
            handler_dict = self._build_handler_dict(handler, func=func, **kwargs)
            self.add_message_reaction_count_handler(handler_dict)
            return handler

        return decorator

    
    def add_message_reaction_count_handler(self, handler_dict):
        """
        Adds message reaction count handler
        Note that you should use register_message_reaction_count_handler to add message_reaction_count_handler to the bot.

        :meta private:

        :param handler_dict:
        :return:
        """
        self.message_reaction_count_handlers.append(handler_dict)


    def register_message_reaction_count_handler(self, callback: Callable, func: Callable=None, pass_bot: Optional[bool]=False, **kwargs):
        """
        Registers message reaction count handler.

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
        self.add_message_reaction_count_handler(handler_dict)


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


    def callback_query_handler(self, func=None, **kwargs):
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

    def purchased_paid_media_handler(self, func=None, **kwargs):
        """
        Handles new incoming purchased paid media.

        :param func: Function executed as a filter
        :type func: :obj:`function`

        :param kwargs: Optional keyword arguments(custom filters)

        :return: None
        """
        def decorator(handler):
            handler_dict = self._build_handler_dict(handler, func=func, **kwargs)
            self.add_purchased_paid_media_handler(handler_dict)
            return handler
        
        return decorator
    
    def add_purchased_paid_media_handler(self, handler_dict):
        """
        Adds a purchased paid media handler
        Note that you should use register_purchased_paid_media_handler to add purchased_paid_media_handler to the bot.

        :meta private:

        :param handler_dict:
        :return:
        """
        self.purchased_paid_media_handlers.append(handler_dict)

    def register_purchased_paid_media_handler(self, callback: Callable, func: Callable, pass_bot: Optional[bool]=False, **kwargs):
        """
        Registers purchased paid media handler.

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
        self.add_purchased_paid_media_handler(handler_dict)

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


    def register_my_chat_member_handler(self, callback: Callable, func: Optional[Callable]=None, pass_bot: Optional[bool]=False, **kwargs):
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


    def register_chat_member_handler(
            self, callback: Callable, func: Optional[Callable]=None, pass_bot: Optional[bool]=False, **kwargs):
        """
        Registers chat member handler.

        :param callback: function to be called
        :type callback: :obj:`function`

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


    def register_chat_join_request_handler(
            self, callback: Callable, func: Optional[Callable]=None, pass_bot:Optional[bool]=False, **kwargs):
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


    def chat_boost_handler(self, func=None, **kwargs):
        """
        Handles new incoming chat boost state. 
        it passes :class:`telebot.types.ChatBoostUpdated` object.

        :param func: Function executed as a filter
        :type func: :obj:`function`

        :param kwargs: Optional keyword arguments(custom filters)
        :return: None
        """
        def decorator(handler):
            handler_dict = self._build_handler_dict(handler, func=func, **kwargs)
            self.add_chat_boost_handler(handler_dict)
            return handler

        return decorator


    def add_chat_boost_handler(self, handler_dict):
        """
        Adds a chat_boost handler.
        Note that you should use register_chat_boost_handler to add chat_boost_handler to the bot.

        :meta private:

        :param handler_dict:
        :return:
        """
        self.chat_boost_handlers.append(handler_dict)


    def register_chat_boost_handler(
            self, callback: Callable, func: Optional[Callable]=None, pass_bot:Optional[bool]=False, **kwargs):
        """
        Registers chat boost handler.

        :param callback: function to be called
        :type callback: :obj:`function`
        
        :param func: Function executed as a filter
        :type func: :obj:`function`

        :param pass_bot: True if you need to pass TeleBot instance to handler(useful for separating handlers into different files)

        :param kwargs: Optional keyword arguments(custom filters)

        :return: None
        """
        handler_dict = self._build_handler_dict(callback, func=func, pass_bot=pass_bot, **kwargs)
        self.add_chat_boost_handler(handler_dict)


    def removed_chat_boost_handler(self, func=None, **kwargs):
        """
        Handles new incoming chat boost state. 
        it passes :class:`telebot.types.ChatBoostRemoved` object.

        :param func: Function executed as a filter
        :type func: :obj:`function`

        :param kwargs: Optional keyword arguments(custom filters)
        :return: None
        """
        def decorator(handler):
            handler_dict = self._build_handler_dict(handler, func=func, **kwargs)
            self.add_removed_chat_boost_handler(handler_dict)
            return handler

        return decorator

    
    def add_removed_chat_boost_handler(self, handler_dict):
        """
        Adds a removed_chat_boost handler.
        Note that you should use register_removed_chat_boost_handler to add removed_chat_boost_handler to the bot.

        :meta private:

        :param handler_dict:
        :return:
        """
        self.removed_chat_boost_handlers.append(handler_dict)


    def register_removed_chat_boost_handler(
            self, callback: Callable, func: Optional[Callable]=None, pass_bot:Optional[bool]=False, **kwargs):
        """
        Registers removed chat boost handler.

        :param callback: function to be called
        :type callback: :obj:`function`
        
        :param func: Function executed as a filter
        :type func: :obj:`function`

        :param pass_bot: True if you need to pass TeleBot instance to handler(useful for separating handlers into different files)

        :param kwargs: Optional keyword arguments(custom filters)

        :return: None
        """
        handler_dict = self._build_handler_dict(callback, func=func, pass_bot=pass_bot, **kwargs)
        self.add_removed_chat_boost_handler(handler_dict)


    def business_connection_handler(self, func=None, **kwargs):
        """
        Handles new incoming business connection state.

        :param func: Function executed as a filter
        :type func: :obj:`function`

        :param kwargs: Optional keyword arguments(custom filters)
        :return: None
        """
        def decorator(handler):
            handler_dict = self._build_handler_dict(handler, func=func, **kwargs)
            self.add_business_connection_handler(handler_dict)
            return handler
        
        return decorator


    def add_business_connection_handler(self, handler_dict):
        """
        Adds a business_connection handler.
        Note that you should use register_business_connection_handler to add business_connection_handler to the bot.

        :meta private:

        :param handler_dict:
        :return:
        """
        self.business_connection_handlers.append(handler_dict)


    def register_business_connection_handler(
            self, callback: Callable, func: Optional[Callable]=None, pass_bot:Optional[bool]=False, **kwargs):
        """
        Registers business connection handler.

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
        self.add_business_connection_handler(handler_dict)


    def business_message_handler(
            self,
            commands: Optional[List[str]]=None,
            regexp: Optional[str]=None,
            func: Optional[Callable]=None,
            content_types: Optional[List[str]]=None,
            **kwargs):
        """
        Handles New incoming message of any kind(for business accounts, see bot api 7.2 for more) - text, photo, sticker, etc.
        As a parameter to the decorator function, it passes :class:`telebot.types.Message` object.
        All message handlers are tested in the order they were added.

        Example:

        .. code-block:: python3
            :caption: Usage of business_message_handler

            bot = TeleBot('TOKEN')

            # Handles all messages which text matches regexp.
            @bot.business_message_handler(regexp='someregexp')
            def command_help(message):
                bot.send_message(message.chat.id, 'Did someone call for help?')

            # Handle all sent documents of type 'text/plain'.
            @bot.business_message_handler(func=lambda message: message.document.mime_type == 'text/plain',
                content_types=['document'])
            def command_handle_document(message):
                bot.send_message(message.chat.id, 'Document received, sir!')

            # Handle all other messages.
            @bot.business_message_handler(func=lambda message: True, content_types=['audio', 'photo', 'voice', 'video', 'document',
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

        :param kwargs: Optional keyword arguments(custom filters)

        :return: decorated function
        """
        if content_types is None:
            content_types = ["text"]

        method_name = "business_message_handler"

        if commands is not None:
            self.check_commands_input(commands, method_name)
            if isinstance(commands, str):
                commands = [commands]

        if regexp is not None:
            self.check_regexp_input(regexp, method_name)

        if isinstance(content_types, str):
            logger.warning("business_message_handler: 'content_types' filter should be List of strings (content types), not string.")
            content_types = [content_types]

        def decorator(handler):
            handler_dict = self._build_handler_dict(handler,
                                                    content_types=content_types,
                                                    commands=commands,
                                                    regexp=regexp,
                                                    func=func,
                                                    **kwargs)
            self.add_business_message_handler(handler_dict)
            return handler

        return decorator


    def add_business_message_handler(self, handler_dict):
        """
        Adds a business_message handler.
        Note that you should use register_business_message_handler to add business_message_handler to the bot.

        :meta private:

        :param handler_dict:
        :return:
        """
        self.business_message_handlers.append(handler_dict)


    def register_business_message_handler(self,
            callback: Callable,
            commands: Optional[List[str]]=None,
            regexp: Optional[str]=None,
            func: Optional[Callable]=None,
            content_types: Optional[List[str]]=None,
            pass_bot: Optional[bool]=False,
            **kwargs):
        """
        Registers business connection handler.

        :param callback: function to be called
        :type callback: :obj:`function`

        :param commands: list of commands
        :type commands: :obj:`list` of :obj:`str`

        :param regexp: Regular expression
        :type regexp: :obj:`str`

        :param func: Function executed as a filter
        :type func: :obj:`function`

        :param content_types: Supported message content types. Must be a list. Defaults to ['text'].
        :type content_types: :obj:`list` of :obj:`str`

        :param pass_bot: True, if bot instance should be passed to handler
        :type pass_bot: :obj:`bool`

        :param kwargs: Optional keyword arguments(custom filters)

        :return: None
        """
        handler_dict = self._build_handler_dict(callback, content_types=content_types, commands=commands, regexp=regexp, func=func, 
                                                pass_bot=pass_bot, **kwargs)
        self.add_business_message_handler(handler_dict)


    def edited_business_message_handler(self, commands=None, regexp=None, func=None, content_types=None, **kwargs):
        """
        Handles new version of a message(business accounts) that is known to the bot and was edited.
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

        method_name = "edited_business_message_handler"

        if commands is not None:
            self.check_commands_input(commands, method_name)
            if isinstance(commands, str):
                commands = [commands]

        if regexp is not None:
            self.check_regexp_input(regexp, method_name)

        if isinstance(content_types, str):
            logger.warning("edited_business_message_handler: 'content_types' filter should be List of strings (content types), not string.")
            content_types = [content_types]

        def decorator(handler):
            handler_dict = self._build_handler_dict(handler,
                                                    content_types=content_types,
                                                    commands=commands,
                                                    regexp=regexp,
                                                    func=func,
                                                    **kwargs)
            self.add_edited_business_message_handler(handler_dict)
            return handler

        return decorator


    def add_edited_business_message_handler(self, handler_dict):
        """
        Adds the edit message handler
        Note that you should use register_edited_business_message_handler to add edited_business_message_handler to the bot.
        
        :meta private:

        :param handler_dict:
        :return:
        """
        self.edited_business_message_handlers.append(handler_dict)


    def register_edited_business_message_handler(self, callback: Callable, content_types: Optional[List[str]]=None,
        commands: Optional[List[str]]=None, regexp: Optional[str]=None, func: Optional[Callable]=None,
        pass_bot: Optional[bool]=False, **kwargs):
        """
        Registers edited message handler for business accounts.

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
        method_name = "edited_business_message_handler"

        if commands is not None:
            self.check_commands_input(commands, method_name)
            if isinstance(commands, str):
                commands = [commands]

        if regexp is not None:
            self.check_regexp_input(regexp, method_name)

        if isinstance(content_types, str):
            logger.warning("edited_business_message_handler: 'content_types' filter should be List of strings (content types), not string.")
            content_types = [content_types]

        handler_dict = self._build_handler_dict(callback,
                                                content_types=content_types,
                                                commands=commands,
                                                regexp=regexp,
                                                func=func,
                                                pass_bot=pass_bot,
                                                **kwargs)
        self.add_edited_business_message_handler(handler_dict)


    def deleted_business_messages_handler(self, func=None, **kwargs):
        """
        Handles new incoming deleted messages state.

        :param func: Function executed as a filter
        :type func: :obj:`function`

        :param kwargs: Optional keyword arguments(custom filters)
        :return: None

        """
        def decorator(handler):
            handler_dict = self._build_handler_dict(handler, func=func, **kwargs)

            self.add_deleted_business_messages_handler(handler_dict)
            return handler
        
        return decorator


    def add_deleted_business_messages_handler(self, handler_dict):
        """
        Adds a deleted_business_messages handler.
        Note that you should use register_deleted_business_messages_handler to add deleted_business_messages_handler to the bot.

        :meta private:
        """
        self.deleted_business_messages_handlers.append(handler_dict)


    def register_deleted_business_messages_handler(self, callback: Callable, func: Optional[Callable]=None, pass_bot: Optional[bool]=False, **kwargs):
        """
        Registers deleted business messages handler.

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
        self.add_deleted_business_messages_handler(handler_dict)


    def add_custom_filter(self, custom_filter: Union[SimpleCustomFilter, AdvancedCustomFilter]):
        """
        Create custom filter.

        .. code-block:: python3
            :caption: Example on checking the text of a message

            class TextMatchFilter(AdvancedCustomFilter):
                key = 'text'

                def check(self, message, text):
                    return text == message.text

        :param custom_filter: Class with check(message) method.
        :param custom_filter: Custom filter class with key.
        """
        self.custom_filters[custom_filter.key] = custom_filter


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
    def _get_middlewares(self, update_type):
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
        This method is made to run handlers and middlewares in queue.

        :param message: received message (update part) to process with handlers and/or middlewares
        :param handlers: all created handlers (not filtered)
        :param middlewares: middlewares that should be executed (already filtered)
        :param update_type: handler/update type (Update field name)
        :return:
        """
        if not self.use_class_middlewares:
            if handlers:
                for handler in handlers:
                    if self._test_message_handler(handler, message):
                        if handler.get('pass_bot', False):
                            result = handler['function'](message, bot=self)
                        else:
                            result = handler['function'](message)
                        if not isinstance(result, ContinueHandling):
                            break
            return

        data = {}
        handler_error = None
        skip_handlers = False

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
                elif isinstance(result, SkipHandler):
                    skip_handlers = True

        if handlers and not skip_handlers:
            try:
                for handler in handlers:
                    params = []
                    process_handler = self._test_message_handler(handler, message)
                    if not process_handler: continue
                    for i in inspect.signature(handler['function']).parameters:
                        params.append(i)
                    if len(params) == 1:
                        result = handler['function'](message)
                    elif "data" in params:
                        if len(params) == 2:
                            result = handler['function'](message, data)
                        elif len(params) == 3:
                            result = handler['function'](message, data=data, bot=self)
                        else:
                            logger.error("It is not allowed to pass data and values inside data to the handler. Check your handler: {}".format(handler['function']))
                            return
                    else:
                        data_copy = data.copy()
                        for key in list(data_copy):
                            # remove data from data_copy if handler does not accept it
                            if key not in params:
                                del data_copy[key]
                        if handler.get('pass_bot'):
                            data_copy["bot"] = self
                        if len(data_copy) > len(params) - 1: # remove the message parameter
                            logger.error("You are passing more parameters than the handler needs. Check your handler: {}".format(handler['function']))
                            return
                        result = handler["function"](message, **data_copy)
                    if not isinstance(result, ContinueHandling):
                        break
            except Exception as e:
                handler_error = e
                handled = self._handle_exception(e)
                if not handled:
                    logger.error(str(e))
                    logger.debug("Exception traceback:\n%s", traceback.format_exc())

        if middlewares:
            for middleware in middlewares:
                if middleware.update_sensitive:
                    if hasattr(middleware, f'post_process_{update_type}'):
                        getattr(middleware, f'post_process_{update_type}')(message, data, handler_error)
                    else:
                        logger.error("Middleware: {} does not have post_process_{} method. Post process function was not executed.".format(middleware.__class__.__name__, update_type))
                else:
                    middleware.post_process(message, data, handler_error)


    def _notify_command_handlers(self, handlers, new_messages, update_type):
        """
        Notifies command handlers.

        :param handlers: all created handlers
        :param new_messages: received messages to proceed
        :param update_type: handler/update type (Update fields)
        :return:
        """
        if (not handlers) and (not self.use_class_middlewares):
            return

        if self.use_class_middlewares:
            middlewares = self._get_middlewares(update_type)
        else:
            middlewares = None
        for message in new_messages:
            self._exec_task(
                self._run_middlewares_and_handler,
                message,
                handlers=handlers,
                middlewares=middlewares,
                update_type=update_type)
