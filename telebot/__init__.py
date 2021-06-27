# -*- coding: utf-8 -*-
from __future__ import print_function
from datetime import datetime

import logging
import re
import sys
import threading
import time
import traceback
from typing import Any, Callable, List, Optional, Union

# this imports are used to avoid circular import error
import telebot.util
import telebot.types



logger = logging.getLogger('TeleBot')
formatter = logging.Formatter(
    '%(asctime)s (%(filename)s:%(lineno)d %(threadName)s) %(levelname)s - %(name)s: "%(message)s"'
)

console_output_handler = logging.StreamHandler(sys.stderr)
console_output_handler.setFormatter(formatter)
logger.addHandler(console_output_handler)

logger.setLevel(logging.ERROR)

from telebot import apihelper, util, types
from telebot.handler_backends import MemoryHandlerBackend, FileHandlerBackend


REPLY_MARKUP_TYPES = Union[
    types.InlineKeyboardMarkup, types.ReplyKeyboardMarkup, 
    types.ReplyKeyboardRemove, types.ForceReply]


"""
Module : telebot
"""


class Handler:
    """
    Class for (next step|reply) handlers
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
    """ This is TeleBot Class
    Methods:
        getMe
        logOut
        close
        sendMessage
        forwardMessage
        copyMessage
        deleteMessage
        sendPhoto
        sendAudio
        sendDocument
        sendSticker
        sendVideo
        sendVenue
        sendAnimation
        sendVideoNote
        sendLocation
        sendChatAction
        sendDice
        sendContact
        sendInvoice
        sendMediaGroup
        getUserProfilePhotos
        getUpdates
        getFile
        sendPoll
        stopPoll
        sendGame
        setGameScore
        getGameHighScores
        editMessageText
        editMessageCaption
        editMessageMedia
        editMessageReplyMarkup
        editMessageLiveLocation
        stopMessageLiveLocation
        kickChatMember
        unbanChatMember
        restrictChatMember
        promoteChatMember
        setChatAdministratorCustomTitle
        setChatPermissions
        createChatInviteLink
        editChatInviteLink
        revokeChatInviteLink
        exportChatInviteLink
        setChatStickerSet
        deleteChatStickerSet
        createNewStickerSet
        addStickerToSet
        deleteStickerFromSet
        setStickerPositionInSet
        uploadStickerFile
        setStickerSetThumb
        getStickerSet
        setChatPhoto
        deleteChatPhoto
        setChatTitle
        setChatDescription
        pinChatMessage
        unpinChatMessage
        leaveChat
        getChat
        getChatAdministrators
        getChatMembersCount
        getChatMember
        answerCallbackQuery
        getMyCommands
        setMyCommands
        answerInlineQuery
        answerShippingQuery
        answerPreCheckoutQuery
        """

    def __init__(
            self, token, parse_mode=None, threaded=True, skip_pending=False, num_threads=2,
            next_step_backend=None, reply_backend=None, exception_handler=None, last_update_id=0,
            suppress_middleware_excepions=False # <- Typo in exceptions 
    ):
        """
        :param token: bot API token
        :param parse_mode: default parse_mode
        :return: Telebot object.
        """

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

        if apihelper.ENABLE_MIDDLEWARE:
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
                'chat_member': []
            }
            self.default_middleware_handlers = []

        self.threaded = threaded
        if self.threaded:
            self.worker_pool = util.ThreadPool(num_threads=num_threads)

    def enable_save_next_step_handlers(self, delay=120, filename="./.handler-saves/step.save"):
        """
        Enable saving next step handlers (by default saving disabled)

        This function explicitly assigns FileHandlerBackend (instead of Saver) just to keep backward
        compatibility whose purpose was to enable file saving capability for handlers. And the same
        implementation is now available with FileHandlerBackend

        Most probably this function should be deprecated in future major releases

        :param delay: Delay between changes in handlers and saving
        :param filename: Filename of save file
        """
        self.next_step_backend = FileHandlerBackend(self.next_step_backend.handlers, filename, delay)

    def enable_save_reply_handlers(self, delay=120, filename="./.handler-saves/reply.save"):
        """
        Enable saving reply handlers (by default saving disable)

        This function explicitly assigns FileHandlerBackend (instead of Saver) just to keep backward
        compatibility whose purpose was to enable file saving capability for handlers. And the same
        implementation is now available with FileHandlerBackend

        Most probably this function should be deprecated in future major releases

        :param delay: Delay between changes in handlers and saving
        :param filename: Filename of save file
        """
        self.reply_backend = FileHandlerBackend(self.reply_backend.handlers, filename, delay)

    def disable_save_next_step_handlers(self):
        """
        Disable saving next step handlers (by default saving disable)

        This function is left to keep backward compatibility whose purpose was to disable file saving capability
        for handlers. For the same purpose, MemoryHandlerBackend is reassigned as a new next_step_backend backend
        instead of FileHandlerBackend.

        Most probably this function should be deprecated in future major releases
        """
        self.next_step_backend = MemoryHandlerBackend(self.next_step_backend.handlers)

    def disable_save_reply_handlers(self):
        """
        Disable saving next step handlers (by default saving disable)

        This function is left to keep backward compatibility whose purpose was to disable file saving capability
        for handlers. For the same purpose, MemoryHandlerBackend is reassigned as a new reply_backend backend
        instead of FileHandlerBackend.

        Most probably this function should be deprecated in future major releases
        """
        self.reply_backend = MemoryHandlerBackend(self.reply_backend.handlers)

    def load_next_step_handlers(self, filename="./.handler-saves/step.save", del_file_after_loading=True):
        """
        Load next step handlers from save file

        This function is left to keep backward compatibility whose purpose was to load handlers from file with the
        help of FileHandlerBackend and is only recommended to use if next_step_backend was assigned as
        FileHandlerBackend before entering this function

        Most probably this function should be deprecated in future major releases

        :param filename: Filename of the file where handlers was saved
        :param del_file_after_loading: Is passed True, after loading save file will be deleted
        """
        self.next_step_backend.load_handlers(filename, del_file_after_loading)

    def load_reply_handlers(self, filename="./.handler-saves/reply.save", del_file_after_loading=True):
        """
        Load reply handlers from save file

        This function is left to keep backward compatibility whose purpose was to load handlers from file with the
        help of FileHandlerBackend and is only recommended to use if reply_backend was assigned as
        FileHandlerBackend before entering this function

        Most probably this function should be deprecated in future major releases

        :param filename: Filename of the file where handlers was saved
        :param del_file_after_loading: Is passed True, after loading save file will be deleted
        """
        self.reply_backend.load_handlers(filename, del_file_after_loading)

    def set_webhook(self, url=None, certificate=None, max_connections=None, allowed_updates=None, ip_address=None,
                    drop_pending_updates = None, timeout=None):
        """
        Use this method to specify a url and receive incoming updates via an outgoing webhook. Whenever there is an
        update for the bot, we will send an HTTPS POST request to the specified url,
        containing a JSON-serialized Update.
        In case of an unsuccessful request, we will give up after a reasonable amount of attempts.
        Returns True on success.

        :param url: HTTPS url to send updates to. Use an empty string to remove webhook integration
        :param certificate: Upload your public key certificate so that the root certificate in use can be checked.
            See our self-signed guide for details.
        :param max_connections: Maximum allowed number of simultaneous HTTPS connections to the webhook
            for update delivery, 1-100. Defaults to 40. Use lower values to limit the load on your bot's server,
            and higher values to increase your bot's throughput.
        :param allowed_updates: A JSON-serialized list of the update types you want your bot to receive.
            For example, specify [“message”, “edited_channel_post”, “callback_query”] to only receive updates
            of these types. See Update for a complete list of available update types.
            Specify an empty list to receive all updates regardless of type (default).
            If not specified, the previous setting will be used.
        :param ip_address: The fixed IP address which will be used to send webhook requests instead of the IP address
            resolved through DNS
        :param drop_pending_updates: Pass True to drop all pending updates
        :param timeout: Integer. Request connection timeout
        :return:
        """
        return apihelper.set_webhook(self.token, url, certificate, max_connections, allowed_updates, ip_address,
                                     drop_pending_updates, timeout)

    def delete_webhook(self, drop_pending_updates=None, timeout=None):
        """
        Use this method to remove webhook integration if you decide to switch back to getUpdates.

        :param drop_pending_updates: Pass True to drop all pending updates
        :param timeout: Integer. Request connection timeout
        :return: bool
        """
        return apihelper.delete_webhook(self.token, drop_pending_updates, timeout)

    def get_webhook_info(self, timeout=None):
        """
        Use this method to get current webhook status. Requires no parameters.
        If the bot is using getUpdates, will return an object with the url field empty.

        :param timeout: Integer. Request connection timeout
        :return: On success, returns a WebhookInfo object.
        """
        result = apihelper.get_webhook_info(self.token, timeout)
        return types.WebhookInfo.de_json(result)

    def remove_webhook(self):
        return self.set_webhook()  # No params resets webhook

    def get_updates(self, offset: Optional[int]=None, limit: Optional[int]=None, 
            timeout: Optional[int]=20, allowed_updates: Optional[List[str]]=None, 
            long_polling_timeout: int=20) -> List[types.Update]:
        """
        Use this method to receive incoming updates using long polling (wiki). An Array of Update objects is returned.
        :param allowed_updates: Array of string. List the types of updates you want your bot to receive.
        :param offset: Integer. Identifier of the first update to be returned.
        :param limit: Integer. Limits the number of updates to be retrieved.
        :param timeout: Integer. Request connection timeout
        :param long_polling_timeout. Timeout in seconds for long polling.
        :return: array of Updates
        """
        json_updates = apihelper.get_updates(self.token, offset, limit, timeout, allowed_updates, long_polling_timeout)
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
        updates = self.get_updates(offset=self.last_update_id, long_polling_timeout=1)
        while updates:
            total += len(updates)
            for update in updates:
                if update.update_id > self.last_update_id:
                    self.last_update_id = update.update_id
            updates = self.get_updates(offset=self.last_update_id + 1, long_polling_timeout=1)
        return total

    def __retrieve_updates(self, timeout=20, long_polling_timeout=20, allowed_updates=None):
        """
        Retrieves any updates from the Telegram API.
        Registered listeners and applicable message handlers will be notified when a new message arrives.
        :raises ApiException when a call has failed.
        """
        if self.skip_pending:
            logger.debug('Skipped {0} pending messages'.format(self.__skip_updates()))
            self.skip_pending = False
        updates = self.get_updates(offset=(self.last_update_id + 1), 
                                   allowed_updates=allowed_updates,
                                   timeout=timeout, long_polling_timeout=long_polling_timeout)
        self.process_new_updates(updates)

    def process_new_updates(self, updates):
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
        
        for update in updates:
            if apihelper.ENABLE_MIDDLEWARE:
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

    def process_new_messages(self, new_messages):
        self._notify_next_handlers(new_messages)
        self._notify_reply_handlers(new_messages)
        self.__notify_update(new_messages)
        self._notify_command_handlers(self.message_handlers, new_messages)

    def process_new_edited_messages(self, edited_message):
        self._notify_command_handlers(self.edited_message_handlers, edited_message)

    def process_new_channel_posts(self, channel_post):
        self._notify_command_handlers(self.channel_post_handlers, channel_post)

    def process_new_edited_channel_posts(self, edited_channel_post):
        self._notify_command_handlers(self.edited_channel_post_handlers, edited_channel_post)

    def process_new_inline_query(self, new_inline_querys):
        self._notify_command_handlers(self.inline_handlers, new_inline_querys)

    def process_new_chosen_inline_query(self, new_chosen_inline_querys):
        self._notify_command_handlers(self.chosen_inline_handlers, new_chosen_inline_querys)

    def process_new_callback_query(self, new_callback_querys):
        self._notify_command_handlers(self.callback_query_handlers, new_callback_querys)

    def process_new_shipping_query(self, new_shipping_querys):
        self._notify_command_handlers(self.shipping_query_handlers, new_shipping_querys)

    def process_new_pre_checkout_query(self, pre_checkout_querys):
        self._notify_command_handlers(self.pre_checkout_query_handlers, pre_checkout_querys)

    def process_new_poll(self, polls):
        self._notify_command_handlers(self.poll_handlers, polls)

    def process_new_poll_answer(self, poll_answers):
        self._notify_command_handlers(self.poll_answer_handlers, poll_answers)
    
    def process_new_my_chat_member(self, my_chat_members):
        self._notify_command_handlers(self.my_chat_member_handlers, my_chat_members)

    def process_new_chat_member(self, chat_members):
        self._notify_command_handlers(self.chat_member_handlers, chat_members)

    def process_middlewares(self, update):
        for update_type, middlewares in self.typed_middleware_handlers.items():
            if getattr(update, update_type) is not None:
                for typed_middleware_handler in middlewares:
                    try:
                        typed_middleware_handler(self, getattr(update, update_type))
                    except Exception as e:
                        e.args = e.args + (f'Typed middleware handler "{typed_middleware_handler.__qualname__}"',)
                        raise

        if len(self.default_middleware_handlers) > 0:
            for default_middleware_handler in self.default_middleware_handlers:
                try:
                    default_middleware_handler(self, update)
                except Exception as e:
                    e.args = e.args + (f'Default middleware handler "{default_middleware_handler.__qualname__}"',)
                    raise

    def __notify_update(self, new_messages):
        if len(self.update_listener) == 0:
            return
        for listener in self.update_listener:
            self._exec_task(listener, new_messages)

    def infinity_polling(self, timeout=20, long_polling_timeout=20, logger_level=logging.ERROR,
            allowed_updates=None, *args, **kwargs):
        """
        Wrap polling with infinite loop and exception handling to avoid bot stops polling.

        :param timeout: Request connection timeout
        :param long_polling_timeout: Timeout in seconds for long polling (see API docs)
        :param logger_level: Custom logging level for infinity_polling logging.
            Use logger levels from logging as a value. None/NOTSET = no error logging
        :param allowed_updates: A list of the update types you want your bot to receive.
            For example, specify [“message”, “edited_channel_post”, “callback_query”] to only receive updates of these types. 
            See util.update_types for a complete list of available update types. 
            Specify an empty list to receive all update types except chat_member (default). 
            If not specified, the previous setting will be used.
            
            Please note that this parameter doesn't affect updates created before the call to the get_updates, 
            so unwanted updates may be received for a short period of time.
        """
        while not self.__stop_polling.is_set():
            try:
                self.polling(none_stop=True, timeout=timeout, long_polling_timeout=long_polling_timeout,
                             allowed_updates=allowed_updates, *args, **kwargs)
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

    def polling(self, none_stop: bool=False, interval: int=0, timeout: int=20, 
            long_polling_timeout: int=20, allowed_updates: Optional[List[str]]=None):
        """
        This function creates a new Thread that calls an internal __retrieve_updates function.
        This allows the bot to retrieve Updates automagically and notify listeners and message handlers accordingly.

        Warning: Do not call this function more than once!

        Always get updates.
        :param interval: Delay between two update retrivals
        :param none_stop: Do not stop polling when an ApiException occurs.
        :param timeout: Request connection timeout
        :param long_polling_timeout: Timeout in seconds for long polling (see API docs)
        :param allowed_updates: A list of the update types you want your bot to receive.
            For example, specify [“message”, “edited_channel_post”, “callback_query”] to only receive updates of these types. 
            See util.update_types for a complete list of available update types. 
            Specify an empty list to receive all update types except chat_member (default). 
            If not specified, the previous setting will be used.
            
            Please note that this parameter doesn't affect updates created before the call to the get_updates, 
            so unwanted updates may be received for a short period of time.
        :return:
        """
        if self.threaded:
            self.__threaded_polling(none_stop, interval, timeout, long_polling_timeout, allowed_updates)
        else:
            self.__non_threaded_polling(none_stop, interval, timeout, long_polling_timeout, allowed_updates)

    def __threaded_polling(self, non_stop=False, interval=0, timeout = None, long_polling_timeout = None, allowed_updates=None):
        logger.info('Started polling.')
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
                    logger.error(e)
                    if not non_stop:
                        self.__stop_polling.set()
                        logger.info("Exception occurred. Stopping.")
                    else:
                        # polling_thread.clear_exceptions()
                        # self.worker_pool.clear_exceptions()
                        logger.info("Waiting for {0} seconds until retry".format(error_interval))
                        time.sleep(error_interval)
                        error_interval *= 2
                else:
                    # polling_thread.clear_exceptions()
                    # self.worker_pool.clear_exceptions()
                    time.sleep(error_interval)
                polling_thread.clear_exceptions()   #*
                self.worker_pool.clear_exceptions() #*
            except KeyboardInterrupt:
                logger.info("KeyboardInterrupt received.")
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
        polling_thread.clear_exceptions()   #*
        self.worker_pool.clear_exceptions() #*
        logger.info('Stopped polling.')

    def __non_threaded_polling(self, non_stop=False, interval=0, timeout=None, long_polling_timeout=None, allowed_updates=None):
        logger.info('Started polling.')
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
                    logger.error(e)
                    if not non_stop:
                        self.__stop_polling.set()
                        logger.info("Exception occurred. Stopping.")
                    else:
                        logger.info("Waiting for {0} seconds until retry".format(error_interval))
                        time.sleep(error_interval)
                        error_interval *= 2
                else:
                    time.sleep(error_interval)
            except KeyboardInterrupt:
                logger.info("KeyboardInterrupt received.")
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

        logger.info('Stopped polling.')

    def _exec_task(self, task, *args, **kwargs):
        if self.threaded:
            self.worker_pool.put(task, *args, **kwargs)
        else:
            task(*args, **kwargs)

    def stop_polling(self):
        self.__stop_polling.set()

    def stop_bot(self):
        self.stop_polling()
        if self.worker_pool:
            self.worker_pool.close()

    def set_update_listener(self, listener):
        self.update_listener.append(listener)

    def get_me(self) -> types.User:
        """
        Returns basic information about the bot in form of a User object.
        """
        result = apihelper.get_me(self.token)
        return types.User.de_json(result)

    def get_file(self, file_id: str) -> types.File:
        """
        Use this method to get basic info about a file and prepare it for downloading.
        For the moment, bots can download files of up to 20MB in size. 
        On success, a File object is returned. 
        It is guaranteed that the link will be valid for at least 1 hour. 
        When the link expires, a new one can be requested by calling get_file again.
        """
        return types.File.de_json(apihelper.get_file(self.token, file_id))

    def get_file_url(self, file_id: str) -> str:
        return apihelper.get_file_url(self.token, file_id)

    def download_file(self, file_path: str) -> bytes:
        return apihelper.download_file(self.token, file_path)

    def log_out(self) -> bool:
        """
        Use this method to log out from the cloud Bot API server before launching the bot locally. 
        You MUST log out the bot before running it locally, otherwise there is no guarantee
        that the bot will receive updates.
        After a successful call, you can immediately log in on a local server, 
        but will not be able to log in back to the cloud Bot API server for 10 minutes. 
        Returns True on success.
        """
        return apihelper.log_out(self.token)
    
    def close(self) -> bool:
        """
        Use this method to close the bot instance before moving it from one local server to another. 
        You need to delete the webhook before calling this method to ensure that the bot isn't launched again
        after server restart.
        The method will return error 429 in the first 10 minutes after the bot is launched. 
        Returns True on success.
        """
        return apihelper.close(self.token)

    def get_user_profile_photos(self, user_id: int, offset: Optional[int]=None, 
            limit: Optional[int]=None) -> types.UserProfilePhotos:
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

    def get_chat(self, chat_id: Union[int, str]) -> types.Chat:
        """
        Use this method to get up to date information about the chat (current name of the user for one-on-one
        conversations, current username of a user, group or channel, etc.). Returns a Chat object on success.
        :param chat_id:
        :return:
        """
        result = apihelper.get_chat(self.token, chat_id)
        return types.Chat.de_json(result)

    def leave_chat(self, chat_id: Union[int, str]) -> bool:
        """
        Use this method for your bot to leave a group, supergroup or channel. Returns True on success.
        :param chat_id:
        :return:
        """
        result = apihelper.leave_chat(self.token, chat_id)
        return result

    def get_chat_administrators(self, chat_id: Union[int, str]) -> List[types.ChatMember]:
        """
        Use this method to get a list of administrators in a chat.
        On success, returns an Array of ChatMember objects that contains
            information about all chat administrators except other bots.
        :param chat_id: Unique identifier for the target chat or username
            of the target supergroup or channel (in the format @channelusername)
        :return:
        """
        result = apihelper.get_chat_administrators(self.token, chat_id)
        ret = []
        for r in result:
            ret.append(types.ChatMember.de_json(r))
        return ret

    def get_chat_members_count(self, chat_id: Union[int, str]) -> int:
        """
        Use this method to get the number of members in a chat. Returns Int on success.
        :param chat_id:
        :return:
        """
        result = apihelper.get_chat_members_count(self.token, chat_id)
        return result

    def set_chat_sticker_set(self, chat_id: Union[int, str], sticker_set_name: str) -> types.StickerSet:
        """
        Use this method to set a new group sticker set for a supergroup. The bot must be an administrator
        in the chat for this to work and must have the appropriate admin rights.
        Use the field can_set_sticker_set optionally returned in getChat requests to check
        if the bot can use this method. Returns True on success.
        :param chat_id: Unique identifier for the target chat or username of the target supergroup
        (in the format @supergroupusername)
        :param sticker_set_name: Name of the sticker set to be set as the group sticker set
        :return:
        """
        result = apihelper.set_chat_sticker_set(self.token, chat_id, sticker_set_name)
        return result

    def delete_chat_sticker_set(self, chat_id: Union[int, str]) -> bool:
        """
        Use this method to delete a group sticker set from a supergroup. The bot must be an administrator in the chat
        for this to work and must have the appropriate admin rights. Use the field can_set_sticker_set
        optionally returned in getChat requests to check if the bot can use this method. Returns True on success.
        :param chat_id:	Unique identifier for the target chat or username of the target supergroup
        (in the format @supergroupusername)
        :return:
        """
        result = apihelper.delete_chat_sticker_set(self.token, chat_id)
        return result

    def get_chat_member(self, chat_id: Union[int, str], user_id: int) -> types.ChatMember:
        """
        Use this method to get information about a member of a chat. Returns a ChatMember object on success.
        :param chat_id:
        :param user_id:
        :return:
        """
        result = apihelper.get_chat_member(self.token, chat_id, user_id)
        return types.ChatMember.de_json(result)

    def send_message(
            self, chat_id: Union[int, str], text: str, 
            disable_web_page_preview: Optional[bool]=None, 
            reply_to_message_id: Optional[int]=None, 
            reply_markup: Optional[REPLY_MARKUP_TYPES]=None,
            parse_mode: Optional[str]=None, 
            disable_notification: Optional[bool]=None, 
            timeout: Optional[int]=None,
            entities: Optional[List[types.MessageEntity]]=None,
            allow_sending_without_reply: Optional[bool]=None) -> types.Message:
        """
        Use this method to send text messages.

        Warning: Do not send more than about 4000 characters each message, otherwise you'll risk an HTTP 414 error.
        If you must send more than 4000 characters, 
        use the `split_string` or `smart_split` function in util.py.

        :param chat_id:
        :param text:
        :param disable_web_page_preview:
        :param reply_to_message_id:
        :param reply_markup:
        :param parse_mode:
        :param disable_notification: Boolean, Optional. Sends the message silently.
        :param timeout:
        :param entities:
        :param allow_sending_without_reply:
        :return: API reply.
        """
        parse_mode = self.parse_mode if (parse_mode is None) else parse_mode

        return types.Message.de_json(
            apihelper.send_message(
                self.token, chat_id, text, disable_web_page_preview, reply_to_message_id,
                reply_markup, parse_mode, disable_notification, timeout,
                entities, allow_sending_without_reply))

    def forward_message(
            self, chat_id: Union[int, str], from_chat_id: Union[int, str], 
            message_id: int, disable_notification: Optional[bool]=None, 
            timeout: Optional[int]=None) -> types.Message:
        """
        Use this method to forward messages of any kind.
        :param disable_notification:
        :param chat_id: which chat to forward
        :param from_chat_id: which chat message from
        :param message_id: message id
        :param timeout:
        :return: API reply.
        """
        return types.Message.de_json(
            apihelper.forward_message(self.token, chat_id, from_chat_id, message_id, disable_notification, timeout))

    def copy_message(
            self, chat_id: Union[int, str], 
            from_chat_id: Union[int, str], 
            message_id: int, 
            caption: Optional[str]=None, 
            parse_mode: Optional[str]=None, 
            caption_entities: Optional[List[types.MessageEntity]]=None,
            disable_notification: Optional[bool]=None, 
            reply_to_message_id: Optional[int]=None, 
            allow_sending_without_reply: Optional[bool]=None,
            reply_markup: Optional[REPLY_MARKUP_TYPES]=None, 
            timeout: Optional[int]=None) -> int:
        """
        Use this method to copy messages of any kind.
        :param chat_id: which chat to forward
        :param from_chat_id: which chat message from
        :param message_id: message id
        :param caption:
        :param parse_mode:
        :param caption_entities:
        :param disable_notification:
        :param reply_to_message_id:
        :param allow_sending_without_reply:
        :param reply_markup:
        :param timeout:
        :return: API reply.
        """
        return types.MessageID.de_json(
            apihelper.copy_message(self.token, chat_id, from_chat_id, message_id, caption, parse_mode, caption_entities,
                                   disable_notification, reply_to_message_id, allow_sending_without_reply, reply_markup,
                                   timeout))

    def delete_message(self, chat_id: Union[int, str], message_id: int, 
            timeout: Optional[int]=None) -> bool:
        """
        Use this method to delete message. Returns True on success.
        :param chat_id: in which chat to delete
        :param message_id: which message to delete
        :param timeout:
        :return: API reply.
        """
        return apihelper.delete_message(self.token, chat_id, message_id, timeout)

    def send_dice(
            self, chat_id: Union[int, str],
            emoji: Optional[str]=None, disable_notification: Optional[bool]=None, 
            reply_to_message_id: Optional[int]=None,
            reply_markup: Optional[REPLY_MARKUP_TYPES]=None, 
            timeout: Optional[int]=None,
            allow_sending_without_reply: Optional[bool]=None) -> types.Message:
        """
        Use this method to send dices.
        :param chat_id:
        :param emoji:
        :param disable_notification:
        :param reply_to_message_id:
        :param reply_markup:
        :param timeout:
        :param allow_sending_without_reply:
        :return: Message
        """
        return types.Message.de_json(
            apihelper.send_dice(
                self.token, chat_id, emoji, disable_notification, reply_to_message_id,
                reply_markup, timeout, allow_sending_without_reply)
        )

    def send_photo(
            self, chat_id: Union[int, str], photo: Union[Any, str], 
            caption: Optional[str]=None, reply_to_message_id: Optional[int]=None, 
            reply_markup: Optional[REPLY_MARKUP_TYPES]=None,
            parse_mode: Optional[str]=None, disable_notification: Optional[bool]=None, 
            timeout: Optional[int]=None,
            caption_entities: Optional[List[types.MessageEntity]]=None,
            allow_sending_without_reply: Optional[bool]=None) -> types.Message:
        """
        Use this method to send photos.
        :param chat_id:
        :param photo:
        :param caption:
        :param parse_mode:
        :param disable_notification:
        :param reply_to_message_id:
        :param reply_markup:
        :param timeout:
        :param caption_entities:
        :param allow_sending_without_reply:
        :return: API reply.
        """
        parse_mode = self.parse_mode if (parse_mode is None) else parse_mode

        return types.Message.de_json(
            apihelper.send_photo(
                self.token, chat_id, photo, caption, reply_to_message_id, reply_markup,
                parse_mode, disable_notification, timeout, caption_entities,
                allow_sending_without_reply))

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
            allow_sending_without_reply: Optional[bool]=None) -> types.Message:
        """
        Use this method to send audio files, if you want Telegram clients to display them in the music player.
        Your audio must be in the .mp3 format.
        :param chat_id:Unique identifier for the message recipient
        :param audio:Audio file to send.
        :param caption:
        :param duration:Duration of the audio in seconds
        :param performer:Performer
        :param title:Track name
        :param reply_to_message_id:If the message is a reply, ID of the original message
        :param reply_markup:
        :param parse_mode
        :param disable_notification:
        :param timeout:
        :param thumb:
        :param caption_entities:
        :param allow_sending_without_reply:
        :return: Message
        """
        parse_mode = self.parse_mode if (parse_mode is None) else parse_mode

        return types.Message.de_json(
            apihelper.send_audio(
                self.token, chat_id, audio, caption, duration, performer, title, reply_to_message_id,
                reply_markup, parse_mode, disable_notification, timeout, thumb,
                caption_entities, allow_sending_without_reply))

    def send_voice(
            self, chat_id: Union[int, str], voice: Union[Any, str], 
            caption: Optional[str]=None, duration: Optional[int]=None, 
            reply_to_message_id: Optional[int]=None, 
            reply_markup: Optional[REPLY_MARKUP_TYPES]=None,
            parse_mode: Optional[str]=None, 
            disable_notification: Optional[bool]=None, 
            timeout: Optional[int]=None,
            caption_entities: Optional[List[types.MessageEntity]]=None,
            allow_sending_without_reply: Optional[bool]=None) -> types.Message:
        """
        Use this method to send audio files, if you want Telegram clients to display the file
        as a playable voice message.
        :param chat_id:Unique identifier for the message recipient.
        :param voice:
        :param caption:
        :param duration:Duration of sent audio in seconds
        :param reply_to_message_id:
        :param reply_markup:
        :param parse_mode
        :param disable_notification:
        :param timeout:
        :param caption_entities:
        :param allow_sending_without_reply:
        :return: Message
        """
        parse_mode = self.parse_mode if (parse_mode is None) else parse_mode

        return types.Message.de_json(
            apihelper.send_voice(
                self.token, chat_id, voice, caption, duration, reply_to_message_id, reply_markup,
                parse_mode, disable_notification, timeout, caption_entities,
                allow_sending_without_reply))

    def send_document(
            self, chat_id: Union[int, str], data: Union[Any, str],
            reply_to_message_id: Optional[int]=None, 
            caption: Optional[str]=None, 
            reply_markup: Optional[REPLY_MARKUP_TYPES]=None,
            parse_mode: Optional[str]=None, 
            disable_notification: Optional[bool]=None, 
            timeout: Optional[int]=None, 
            thumb: Optional[Union[Any, str]]=None,
            caption_entities: Optional[List[types.MessageEntity]]=None,
            allow_sending_without_reply: Optional[bool]=None) -> types.Message:
        """
        Use this method to send general files.
        :param chat_id:
        :param data:
        :param reply_to_message_id:
        :param caption:
        :param reply_markup:
        :param parse_mode:
        :param disable_notification:
        :param timeout:
        :param thumb: InputFile or String : Thumbnail of the file sent
        :param caption_entities:
        :param allow_sending_without_reply:
        :return: API reply.
        """
        parse_mode = self.parse_mode if (parse_mode is None) else parse_mode

        return types.Message.de_json(
            apihelper.send_data(
                self.token, chat_id, data, 'document', reply_to_message_id, reply_markup,
                parse_mode, disable_notification, timeout, caption, thumb, caption_entities,
                allow_sending_without_reply))

    def send_sticker(
            self, chat_id: Union[int, str], data: Union[Any, str], 
            reply_to_message_id: Optional[int]=None, 
            reply_markup: Optional[REPLY_MARKUP_TYPES]=None,
            disable_notification: Optional[bool]=None, 
            timeout: Optional[int]=None,
            allow_sending_without_reply: Optional[bool]=None) -> types.Message:
        """
        Use this method to send .webp stickers.
        :param chat_id:
        :param data:
        :param reply_to_message_id:
        :param reply_markup:
        :param disable_notification: to disable the notification
        :param timeout: timeout
        :param allow_sending_without_reply:
        :return: API reply.
        """
        return types.Message.de_json(
            apihelper.send_data(
                self.token, chat_id=chat_id, data=data, data_type='sticker', 
                reply_to_message_id=reply_to_message_id, reply_markup=reply_markup,
                disable_notification=disable_notification, timeout=timeout, 
                allow_sending_without_reply=allow_sending_without_reply))

    def send_video(
            self, chat_id: Union[int, str], data: Union[Any, str], 
            duration: Optional[int]=None, 
            caption: Optional[str]=None, 
            reply_to_message_id: Optional[int]=None, 
            reply_markup: Optional[REPLY_MARKUP_TYPES]=None,
            parse_mode: Optional[str]=None, 
            supports_streaming: Optional[bool]=None, 
            disable_notification: Optional[bool]=None, 
            timeout: Optional[int]=None, 
            thumb: Optional[Union[Any, str]]=None, 
            width: Optional[int]=None, 
            height: Optional[int]=None,
            caption_entities: Optional[List[types.MessageEntity]]=None,
            allow_sending_without_reply: Optional[bool]=None) -> types.Message:
        """
        Use this method to send video files, Telegram clients support mp4 videos.
        :param chat_id: Integer : Unique identifier for the message recipient — User or GroupChat id
        :param data: InputFile or String : Video to send. You can either pass a file_id as String to resend
            a video that is already on the Telegram server
        :param duration: Integer : Duration of sent video in seconds
        :param caption: String : Video caption (may also be used when resending videos by file_id).
        :param parse_mode:
        :param supports_streaming:
        :param reply_to_message_id:
        :param reply_markup:
        :param disable_notification:
        :param timeout:
        :param thumb: InputFile or String : Thumbnail of the file sent
        :param width:
        :param height:
        :param caption_entities:
        :param allow_sending_without_reply:
        :return:
        """
        parse_mode = self.parse_mode if (parse_mode is None) else parse_mode

        return types.Message.de_json(
            apihelper.send_video(
                self.token, chat_id, data, duration, caption, reply_to_message_id, reply_markup,
                parse_mode, supports_streaming, disable_notification, timeout, thumb, width, height,
                caption_entities, allow_sending_without_reply))

    def send_animation(
            self, chat_id: Union[int, str], animation: Union[Any, str], 
            duration: Optional[int]=None,
            caption: Optional[str]=None, 
            reply_to_message_id: Optional[int]=None,
            reply_markup: Optional[REPLY_MARKUP_TYPES]=None, 
            parse_mode: Optional[str]=None,
            disable_notification: Optional[bool]=None, 
            timeout: Optional[int]=None, 
            thumb: Optional[Union[Any, str]]=None,
            caption_entities: Optional[List[types.MessageEntity]]=None,
            allow_sending_without_reply: Optional[bool]=None) -> types.Message:
        """
        Use this method to send animation files (GIF or H.264/MPEG-4 AVC video without sound).
        :param chat_id: Integer : Unique identifier for the message recipient — User or GroupChat id
        :param animation: InputFile or String : Animation to send. You can either pass a file_id as String to resend an
            animation that is already on the Telegram server
        :param duration: Integer : Duration of sent video in seconds
        :param caption: String : Animation caption (may also be used when resending animation by file_id).
        :param parse_mode:
        :param reply_to_message_id:
        :param reply_markup:
        :param disable_notification:
        :param timeout:
        :param thumb: InputFile or String : Thumbnail of the file sent
        :param caption_entities:
        :param allow_sending_without_reply:
        :return:
        """
        parse_mode = self.parse_mode if (parse_mode is None) else parse_mode

        return types.Message.de_json(
            apihelper.send_animation(
                self.token, chat_id, animation, duration, caption, reply_to_message_id,
                reply_markup, parse_mode, disable_notification, timeout, thumb,
                caption_entities, allow_sending_without_reply))

    def send_video_note(
            self, chat_id: Union[int, str], data: Union[Any, str], 
            duration: Optional[int]=None, 
            length: Optional[int]=None,
            reply_to_message_id: Optional[int]=None, 
            reply_markup: Optional[REPLY_MARKUP_TYPES]=None,
            disable_notification: Optional[bool]=None, 
            timeout: Optional[int]=None, 
            thumb: Optional[Union[Any, str]]=None,
            allow_sending_without_reply: Optional[bool]=None) -> types.Message:
        """
        As of v.4.0, Telegram clients support rounded square mp4 videos of up to 1 minute long. Use this method to send
            video messages.
        :param chat_id: Integer : Unique identifier for the message recipient — User or GroupChat id
        :param data: InputFile or String : Video note to send. You can either pass a file_id as String to resend
            a video that is already on the Telegram server
        :param duration: Integer : Duration of sent video in seconds
        :param length: Integer : Video width and height, Can't be None and should be in range of (0, 640)
        :param reply_to_message_id:
        :param reply_markup:
        :param disable_notification:
        :param timeout:
        :param thumb: InputFile or String : Thumbnail of the file sent
        :param allow_sending_without_reply:
        :return:
        """
        return types.Message.de_json(
            apihelper.send_video_note(
                self.token, chat_id, data, duration, length, reply_to_message_id, reply_markup,
                disable_notification, timeout, thumb, allow_sending_without_reply))

    def send_media_group(
            self, chat_id: Union[int, str], 
            media: List[Union[
                types.InputMediaAudio, types.InputMediaDocument, 
                types.InputMediaPhoto, types.InputMediaVideo]],
            disable_notification: Optional[bool]=None, 
            reply_to_message_id: Optional[int]=None, 
            timeout: Optional[int]=None,
            allow_sending_without_reply: Optional[bool]=None) -> List[types.Message]:
        """
        send a group of photos or videos as an album. On success, an array of the sent Messages is returned.
        :param chat_id:
        :param media:
        :param disable_notification:
        :param reply_to_message_id:
        :param timeout:
        :param allow_sending_without_reply:
        :return:
        """
        result = apihelper.send_media_group(
            self.token, chat_id, media, disable_notification, reply_to_message_id, timeout, 
            allow_sending_without_reply)
        ret = []
        for msg in result:
            ret.append(types.Message.de_json(msg))
        return ret

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
            allow_sending_without_reply: Optional[bool]=None) -> types.Message:

            
        """
        Use this method to send point on the map.
        :param chat_id:
        :param latitude:
        :param longitude:
        :param live_period:
        :param reply_to_message_id:
        :param reply_markup:
        :param disable_notification:
        :param timeout:
        :param horizontal_accuracy:
        :param heading:
        :param proximity_alert_radius:
        :param allow_sending_without_reply:
        :return: API reply.
        """
        return types.Message.de_json(
            apihelper.send_location(
                self.token, chat_id, latitude, longitude, live_period, 
                reply_to_message_id, reply_markup, disable_notification, timeout, 
                horizontal_accuracy, heading, proximity_alert_radius, 
                allow_sending_without_reply))

    def edit_message_live_location(
            self, latitude: float, longitude: float, 
            chat_id: Optional[Union[int, str]]=None, 
            message_id: Optional[int]=None,
            inline_message_id: Optional[str]=None, 
            reply_markup: Optional[REPLY_MARKUP_TYPES]=None, 
            timeout: Optional[int]=None,
            horizontal_accuracy: Optional[float]=None, 
            heading: Optional[int]=None, 
            proximity_alert_radius: Optional[int]=None) -> types.Message:
        """
        Use this method to edit live location
        :param latitude:
        :param longitude:
        :param chat_id:
        :param message_id:
        :param reply_markup:
        :param timeout:
        :param inline_message_id:
        :param horizontal_accuracy:
        :param heading:
        :param proximity_alert_radius:
        :return:
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
            timeout: Optional[int]=None) -> types.Message:
        """
        Use this method to stop updating a live location message sent by the bot
        or via the bot (for inline bots) before live_period expires
        :param chat_id:
        :param message_id:
        :param inline_message_id:
        :param reply_markup:
        :param timeout:
        :return:
        """
        return types.Message.de_json(
            apihelper.stop_message_live_location(
                self.token, chat_id, message_id, inline_message_id, reply_markup, timeout))

    def send_venue(
            self, chat_id: Union[int, str], 
            latitude: float, longitude: float, 
            title: str, address: str, 
            foursquare_id: Optional[str]=None, 
            foursquare_type: Optional[str]=None,
            disable_notification: Optional[bool]=None, 
            reply_to_message_id: Optional[int]=None, 
            reply_markup: Optional[REPLY_MARKUP_TYPES]=None, 
            timeout: Optional[int]=None,
            allow_sending_without_reply: Optional[bool]=None,
            google_place_id: Optional[str]=None,
            google_place_type: Optional[str]=None) -> types.Message:
        """
        Use this method to send information about a venue.
        :param chat_id: Integer or String : Unique identifier for the target chat or username of the target channel
        :param latitude: Float : Latitude of the venue
        :param longitude: Float : Longitude of the venue
        :param title: String : Name of the venue
        :param address: String : Address of the venue
        :param foursquare_id: String : Foursquare identifier of the venue
        :param foursquare_type: Foursquare type of the venue, if known. (For example, “arts_entertainment/default”,
            “arts_entertainment/aquarium” or “food/icecream”.)
        :param disable_notification:
        :param reply_to_message_id:
        :param reply_markup:
        :param timeout:
        :param allow_sending_without_reply:
        :param google_place_id:
        :param google_place_type:
        :return:
        """
        return types.Message.de_json(
            apihelper.send_venue(
                self.token, chat_id, latitude, longitude, title, address, foursquare_id, foursquare_type,
                disable_notification, reply_to_message_id, reply_markup, timeout,
                allow_sending_without_reply, google_place_id, google_place_type)
        )

    def send_contact(
            self, chat_id: Union[int, str], phone_number: str, 
            first_name: str, last_name: Optional[str]=None, 
            vcard: Optional[str]=None,
            disable_notification: Optional[bool]=None, 
            reply_to_message_id: Optional[int]=None, 
            reply_markup: Optional[REPLY_MARKUP_TYPES]=None, 
            timeout: Optional[int]=None,
            allow_sending_without_reply: Optional[bool]=None) -> types.Message:
        return types.Message.de_json(
            apihelper.send_contact(
                self.token, chat_id, phone_number, first_name, last_name, vcard,
                disable_notification, reply_to_message_id, reply_markup, timeout,
                allow_sending_without_reply)
        )

    def send_chat_action(
            self, chat_id: Union[int, str], action: str, timeout: Optional[int]=None) -> bool:
        """
        Use this method when you need to tell the user that something is happening on the bot's side.
        The status is set for 5 seconds or less (when a message arrives from your bot, Telegram clients clear
        its typing status).
        :param chat_id:
        :param action:  One of the following strings: 'typing', 'upload_photo', 'record_video', 'upload_video',
                        'record_audio', 'upload_audio', 'upload_document', 'find_location', 'record_video_note',
                        'upload_video_note'.
        :param timeout:
        :return: API reply. :type: boolean
        """
        return apihelper.send_chat_action(self.token, chat_id, action, timeout)

    def kick_chat_member(
            self, chat_id: Union[int, str], user_id: int, 
            until_date:Optional[Union[int, datetime]]=None, 
            revoke_messages: Optional[bool]=None) -> bool:
        """
        Use this method to kick a user from a group or a supergroup.
        :param chat_id: Int or string : Unique identifier for the target group or username of the target supergroup
        :param user_id: Int : Unique identifier of the target user
        :param until_date: Date when the user will be unbanned, unix time. If user is banned for more than 366 days or
               less than 30 seconds from the current time they are considered to be banned forever
        :param revoke_messages: Bool: Pass True to delete all messages from the chat for the user that is being removed.
                If False, the user will be able to see messages in the group that were sent before the user was removed. 
                Always True for supergroups and channels.
        :return: boolean
        """
        return apihelper.kick_chat_member(self.token, chat_id, user_id, until_date, revoke_messages)

    def unban_chat_member(
            self, chat_id: Union[int, str], user_id: int, 
            only_if_banned: Optional[bool]=False) -> bool:
        """
        Use this method to unban a previously kicked user in a supergroup or channel.
        The user will not return to the group or channel automatically, but will be able to join via link, etc.
        The bot must be an administrator for this to work. By default, this method guarantees that after the call
        the user is not a member of the chat, but will be able to join it. So if the user is a member of the chat
        they will also be removed from the chat. If you don't want this, use the parameter only_if_banned.

        :param chat_id: Unique identifier for the target group or username of the target supergroup or channel
            (in the format @username)
        :param user_id: Unique identifier of the target user
        :param only_if_banned: Do nothing if the user is not banned
        :return: True on success
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

        :param chat_id: Int or String : 	Unique identifier for the target group or username of the target supergroup
            or channel (in the format @channelusername)
        :param user_id: Int : Unique identifier of the target user
        :param until_date: Date when restrictions will be lifted for the user, unix time.
            If user is restricted for more than 366 days or less than 30 seconds from the current time,
            they are considered to be restricted forever
        :param can_send_messages: Pass True, if the user can send text messages, contacts, locations and venues
        :param can_send_media_messages Pass True, if the user can send audios, documents, photos, videos, video notes
            and voice notes, implies can_send_messages
        :param can_send_polls: Pass True, if the user is allowed to send polls, implies can_send_messages
        :param can_send_other_messages: Pass True, if the user can send animations, games, stickers and
            use inline bots, implies can_send_media_messages
        :param can_add_web_page_previews: Pass True, if the user may add web page previews to their messages,
            implies can_send_media_messages
        :param can_change_info: Pass True, if the user is allowed to change the chat title, photo and other settings.
            Ignored in public supergroups
        :param can_invite_users: Pass True, if the user is allowed to invite new users to the chat,
            implies can_invite_users
        :param can_pin_messages: Pass True, if the user is allowed to pin messages. Ignored in public supergroups
        :return: True on success
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
            can_manage_voice_chats: Optional[bool]=None) -> bool:
        """
        Use this method to promote or demote a user in a supergroup or a channel. The bot must be an administrator
        in the chat for this to work and must have the appropriate admin rights.
        Pass False for all boolean parameters to demote a user.

        :param chat_id: Unique identifier for the target chat or username of the target channel (
            in the format @channelusername)
        :param user_id: Int : Unique identifier of the target user
        :param can_change_info: Bool: Pass True, if the administrator can change chat title, photo and other settings
        :param can_post_messages: Bool : Pass True, if the administrator can create channel posts, channels only
        :param can_edit_messages: Bool : Pass True, if the administrator can edit messages of other users, channels only
        :param can_delete_messages: Bool : Pass True, if the administrator can delete messages of other users
        :param can_invite_users: Bool : Pass True, if the administrator can invite new users to the chat
        :param can_restrict_members: Bool: Pass True, if the administrator can restrict, ban or unban chat members
        :param can_pin_messages: Bool: Pass True, if the administrator can pin messages, supergroups only
        :param can_promote_members: Bool: Pass True, if the administrator can add new administrators with a subset
            of his own privileges or demote administrators that he has promoted, directly or indirectly
            (promoted by administrators that were appointed by him)
        :param is_anonymous: Bool: Pass True, if the administrator's presence in the chat is hidden
        :param can_manage_chat: Bool: Pass True, if the administrator can access the chat event log, chat statistics, 
            message statistics in channels, see channel members, 
            see anonymous administrators in supergroups and ignore slow mode. 
            Implied by any other administrator privilege
        :param can_manage_voice_chats: Bool: Pass True, if the administrator can manage voice chats
            For now, bots can use this privilege only for passing to other administrators.
        :return: True on success.
        """
        return apihelper.promote_chat_member(
            self.token, chat_id, user_id, can_change_info, can_post_messages,
            can_edit_messages, can_delete_messages, can_invite_users,
            can_restrict_members, can_pin_messages, can_promote_members,
            is_anonymous, can_manage_chat, can_manage_voice_chats)

    def set_chat_administrator_custom_title(
            self, chat_id: Union[int, str], user_id: int, custom_title: str) -> bool:
        """
        Use this method to set a custom title for an administrator
        in a supergroup promoted by the bot.

        :param chat_id: Unique identifier for the target chat or username of the target supergroup
            (in the format @supergroupusername)
        :param user_id: Unique identifier of the target user
        :param custom_title: New custom title for the administrator;
            0-16 characters, emoji are not allowed
        :return: True on success.
        """
        return apihelper.set_chat_administrator_custom_title(self.token, chat_id, user_id, custom_title)

    def set_chat_permissions(
            self, chat_id: Union[int, str], permissions: types.ChatPermissions) -> bool:
        """
        Use this method to set default chat permissions for all members.
        The bot must be an administrator in the group or a supergroup for this to work
        and must have the can_restrict_members admin rights.

        :param chat_id: Unique identifier for the target chat or username of the target supergroup
            (in the format @supergroupusername)
        :param permissions: New default chat permissions
        :return: True on success
        """
        return apihelper.set_chat_permissions(self.token, chat_id, permissions)

    def create_chat_invite_link(
            self, chat_id: Union[int, str], 
            expire_date: Optional[Union[int, datetime]]=None, 
            member_limit: Optional[int]=None) -> types.ChatInviteLink:
        """
        Use this method to create an additional invite link for a chat.
        The bot must be an administrator in the chat for this to work and must have the appropriate admin rights.

        :param chat_id: Id: Unique identifier for the target chat or username of the target channel
            (in the format @channelusername)
        :expire_date: Point in time (Unix timestamp) when the link will expire
        :member_limit: Maximum number of users that can be members of the chat simultaneously
        :return:
        """
        return types.ChatInviteLink.de_json(
            apihelper.create_chat_invite_link(self.token, chat_id, expire_date, member_limit)
        )

    def edit_chat_invite_link(
            self, chat_id: Union[int, str], invite_link: str, 
            expire_date: Optional[Union[int, datetime]]=None, 
            member_limit: Optional[int]=None) -> types.ChatInviteLink:
        """
        Use this method to edit a non-primary invite link created by the bot.
        The bot must be an administrator in the chat for this to work and must have the appropriate admin rights.

        :param chat_id: Id: Unique identifier for the target chat or username of the target channel
            (in the format @channelusername)
        :invite_link: The invite link to edit
        :expire_date: Point in time (Unix timestamp) when the link will expire
        :member_limit: Maximum number of users that can be members of the chat simultaneously
        :return:
        """
        return types.ChatInviteLink.de_json(
            apihelper.edit_chat_invite_link(self.token, chat_id, invite_link, expire_date, member_limit)
        )

    def revoke_chat_invite_link(
            self, chat_id: Union[int, str], invite_link: str) -> types.ChatInviteLink:
        """
        Use this method to revoke an invite link created by the bot.
        Note: If the primary link is revoked, a new link is automatically generated The bot must be an administrator 
            in the chat for this to work and must have the appropriate admin rights.

        :param chat_id: Id: Unique identifier for the target chat or username of the target channel
            (in the format @channelusername)
        :invite_link: The invite link to revoke
        :return:
        """
        return types.ChatInviteLink.de_json(
            apihelper.revoke_chat_invite_link(self.token, chat_id, invite_link)
        )

    def export_chat_invite_link(self, chat_id: Union[int, str]) -> str:
        """
        Use this method to export an invite link to a supergroup or a channel. The bot must be an administrator
        in the chat for this to work and must have the appropriate admin rights.

        :param chat_id: Id: Unique identifier for the target chat or username of the target channel
            (in the format @channelusername)
        :return: exported invite link as String on success.
        """
        return apihelper.export_chat_invite_link(self.token, chat_id)

    def set_chat_photo(self, chat_id: Union[int, str], photo: Any) -> bool:
        """
        Use this method to set a new profile photo for the chat. Photos can't be changed for private chats.
        The bot must be an administrator in the chat for this to work and must have the appropriate admin rights.
        Returns True on success.
        Note: In regular groups (non-supergroups), this method will only work if the ‘All Members Are Admins’
            setting is off in the target group.
        :param chat_id: Int or Str: Unique identifier for the target chat or username of the target channel
            (in the format @channelusername)
        :param photo: InputFile: New chat photo, uploaded using multipart/form-data
        :return:
        """
        return apihelper.set_chat_photo(self.token, chat_id, photo)

    def delete_chat_photo(self, chat_id: Union[int, str]) -> bool:
        """
        Use this method to delete a chat photo. Photos can't be changed for private chats.
        The bot must be an administrator in the chat for this to work and must have the appropriate admin rights.
        Returns True on success.
        Note: In regular groups (non-supergroups), this method will only work if the ‘All Members Are Admins’
            setting is off in the target group.
        :param chat_id: Int or Str: Unique identifier for the target chat or username of the target channel
            (in the format @channelusername)
        :return:
        """
        return apihelper.delete_chat_photo(self.token, chat_id)
    
    def get_my_commands(self,
                        scope: Optional[Union[
                            types.BotCommandScopeDefault, types.BotCommandScopeAllPrivateChats,
                            types.BotCommandScopeAllGroupChats, types.BotCommandScopeAllChatAdministrators,
                            types.BotCommandScopeChat,
                            types.BotCommandScopeChatAdministrators, types.BotCommandScopeChatMember]]=None,
                        language_code: Optional[str]=None) -> List[types.BotCommand]:
        """
        Use this method to get the current list of the bot's commands for the given scope and user language
        :param scope: scope of users for which the commands are relevant
        :param language_code: A two-letter ISO 639-1 language code
        Returns List of BotCommand on success.
        """
        result = apihelper.get_my_commands(self.token, scope, language_code)
        return [types.BotCommand.de_json(cmd) for cmd in result]

    def set_my_commands(self, commands: List[types.BotCommand],
                        scope: Optional[Union[
                            types.BotCommandScopeDefault, types.BotCommandScopeAllPrivateChats,
                            types.BotCommandScopeAllGroupChats, types.BotCommandScopeAllChatAdministrators,
                            types.BotCommandScopeChat,
                            types.BotCommandScopeChatAdministrators, types.BotCommandScopeChatMember]] = None,
                        language_code: Optional[str]=None) -> bool:
        """
        Use this method to change the list of the bot's commands.
        :param commands: List of BotCommand. At most 100 commands can be specified.
        :param scope: scope of users for which the commands are relevant
        :param language_code: A two-letter ISO 639-1 language code
        :return:
        """
        return apihelper.set_my_commands(self.token, commands, scope, language_code)

    def delete_my_commands(self,
                           scope: Optional[Union[
                               types.BotCommandScopeDefault, types.BotCommandScopeAllPrivateChats,
                               types.BotCommandScopeAllGroupChats, types.BotCommandScopeAllChatAdministrators,
                               types.BotCommandScopeChat,
                               types.BotCommandScopeChatAdministrators, types.BotCommandScopeChatMember]]=None,
                           language_code: Optional[str]=None) -> bool:
        """
        Use this method to delete the list of the bot's commands for the given scope and user language.
        :param scope: scope of users for which the commands are relevant
        :param language_code: A two-letter ISO 639-1 language code
        :return:
        """
        return apihelper.delete_my_commands(self.token, scope, language_code)

    def set_chat_title(self, chat_id: Union[int, str], title: str) -> bool:
        """
        Use this method to change the title of a chat. Titles can't be changed for private chats.
        The bot must be an administrator in the chat for this to work and must have the appropriate admin rights.
        Returns True on success.
        Note: In regular groups (non-supergroups), this method will only work if the ‘All Members Are Admins’
            setting is off in the target group.
        :param chat_id: Int or Str: Unique identifier for the target chat or username of the target channel
            (in the format @channelusername)
        :param title: New chat title, 1-255 characters
        :return:
        """
        return apihelper.set_chat_title(self.token, chat_id, title)

    def set_chat_description(self, chat_id: Union[int, str], description: Optional[str]=None) -> bool:
        """
        Use this method to change the description of a supergroup or a channel.
        The bot must be an administrator in the chat for this to work and must have the appropriate admin rights.

        :param chat_id: Int or Str: Unique identifier for the target chat or username of the target channel
            (in the format @channelusername)
        :param description: Str: New chat description, 0-255 characters
        :return: True on success.
        """
        return apihelper.set_chat_description(self.token, chat_id, description)

    def pin_chat_message(
            self, chat_id: Union[int, str], message_id: int, 
            disable_notification: Optional[bool]=False) -> bool:
        """
        Use this method to pin a message in a supergroup.
        The bot must be an administrator in the chat for this to work and must have the appropriate admin rights.
        Returns True on success.
        :param chat_id: Int or Str: Unique identifier for the target chat or username of the target channel
            (in the format @channelusername)
        :param message_id: Int: Identifier of a message to pin
        :param disable_notification: Bool: Pass True, if it is not necessary to send a notification
            to all group members about the new pinned message
        :return:
        """
        return apihelper.pin_chat_message(self.token, chat_id, message_id, disable_notification)

    def unpin_chat_message(self, chat_id: Union[int, str], message_id: Optional[int]=None) -> bool:
        """
        Use this method to unpin specific pinned message in a supergroup chat.
        The bot must be an administrator in the chat for this to work and must have the appropriate admin rights.
        Returns True on success.
        :param chat_id: Int or Str: Unique identifier for the target chat or username of the target channel
            (in the format @channelusername)
        :param message_id: Int: Identifier of a message to unpin
        :return:
        """
        return apihelper.unpin_chat_message(self.token, chat_id, message_id)

    def unpin_all_chat_messages(self, chat_id: Union[int, str]) -> bool:
        """
        Use this method to unpin a all pinned messages in a supergroup chat.
        The bot must be an administrator in the chat for this to work and must have the appropriate admin rights.
        Returns True on success.
        :param chat_id: Int or Str: Unique identifier for the target chat or username of the target channel
            (in the format @channelusername)
        :return:
        """
        return apihelper.unpin_all_chat_messages(self.token, chat_id)

    def edit_message_text(
            self, text: str, 
            chat_id: Optional[Union[int, str]]=None, 
            message_id: Optional[int]=None, 
            inline_message_id: Optional[str]=None, 
            parse_mode: Optional[str]=None,
            disable_web_page_preview: Optional[bool]=None, 
            reply_markup: Optional[REPLY_MARKUP_TYPES]=None) -> Union[types.Message, bool]:
        """
        Use this method to edit text and game messages.
        :param text:
        :param chat_id:
        :param message_id:
        :param inline_message_id:
        :param parse_mode:
        :param disable_web_page_preview:
        :param reply_markup:
        :return:
        """
        parse_mode = self.parse_mode if (parse_mode is None) else parse_mode

        result = apihelper.edit_message_text(self.token, text, chat_id, message_id, inline_message_id, parse_mode,
                                             disable_web_page_preview, reply_markup)
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
        :param media:
        :param chat_id:
        :param message_id:
        :param inline_message_id:
        :param reply_markup:
        :return:
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
        :param chat_id:
        :param message_id:
        :param inline_message_id:
        :param reply_markup:
        :return:
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
            allow_sending_without_reply: Optional[bool]=None) -> types.Message:
        """
        Used to send the game
        :param chat_id:
        :param game_short_name:
        :param disable_notification:
        :param reply_to_message_id:
        :param reply_markup:
        :param timeout:
        :param allow_sending_without_reply:
        :return:
        """
        result = apihelper.send_game(
            self.token, chat_id, game_short_name, disable_notification,
            reply_to_message_id, reply_markup, timeout, 
            allow_sending_without_reply)
        return types.Message.de_json(result)

    def set_game_score(
            self, user_id: Union[int, str], score: int, 
            force: Optional[bool]=None, 
            chat_id: Optional[Union[int, str]]=None, 
            message_id: Optional[int]=None, 
            inline_message_id: Optional[str]=None,
            disable_edit_message: Optional[bool]=None) -> Union[types.Message, bool]:
        """
        Sets the value of points in the game to a specific user
        :param user_id:
        :param score:
        :param force:
        :param chat_id:
        :param message_id:
        :param inline_message_id:
        :param disable_edit_message:
        :return:
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
        Gets top points and game play
        :param user_id:
        :param chat_id:
        :param message_id:
        :param inline_message_id:
        :return:
        """
        result = apihelper.get_game_high_scores(self.token, user_id, chat_id, message_id, inline_message_id)
        ret = []
        for r in result:
            ret.append(types.GameHighScore.de_json(r))
        return ret

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
            allow_sending_without_reply: Optional[bool]=None) -> types.Message:
        """
        Sends invoice
        :param chat_id: Unique identifier for the target private chat
        :param title: Product name
        :param description: Product description
        :param invoice_payload: Bot-defined invoice payload, 1-128 bytes. This will not be displayed to the user,
            use for your internal processes.
        :param provider_token: Payments provider token, obtained via @Botfather
        :param currency: Three-letter ISO 4217 currency code,
            see https://core.telegram.org/bots/payments#supported-currencies
        :param prices: Price breakdown, a list of components
            (e.g. product price, tax, discount, delivery cost, delivery tax, bonus, etc.)
        :param start_parameter: Unique deep-linking parameter that can be used to generate this invoice
            when used as a start parameter
        :param photo_url: URL of the product photo for the invoice. Can be a photo of the goods
            or a marketing image for a service. People like it better when they see what they are paying for.
        :param photo_size: Photo size
        :param photo_width: Photo width
        :param photo_height: Photo height
        :param need_name: Pass True, if you require the user's full name to complete the order
        :param need_phone_number: Pass True, if you require the user's phone number to complete the order
        :param need_email: Pass True, if you require the user's email to complete the order
        :param need_shipping_address: Pass True, if you require the user's shipping address to complete the order
        :param is_flexible: Pass True, if the final price depends on the shipping method
        :param send_phone_number_to_provider: Pass True, if user's phone number should be sent to provider
        :param send_email_to_provider: Pass True, if user's email address should be sent to provider
        :param disable_notification: Sends the message silently. Users will receive a notification with no sound.
        :param reply_to_message_id: If the message is a reply, ID of the original message
        :param reply_markup: A JSON-serialized object for an inline keyboard. If empty,
            one 'Pay total price' button will be shown. If not empty, the first button must be a Pay button
        :param provider_data: A JSON-serialized data about the invoice, which will be shared with the payment provider.
            A detailed description of required fields should be provided by the payment provider.
        :param timeout:
        :param allow_sending_without_reply:
        :return:
        """
        result = apihelper.send_invoice(
            self.token, chat_id, title, description, invoice_payload, provider_token,
            currency, prices, start_parameter, photo_url, photo_size, photo_width,
            photo_height, need_name, need_phone_number, need_email, need_shipping_address,
            send_phone_number_to_provider, send_email_to_provider, is_flexible, disable_notification,
            reply_to_message_id, reply_markup, provider_data, timeout, allow_sending_without_reply)
        return types.Message.de_json(result)

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
            disable_notifications: Optional[bool]=False, 
            reply_to_message_id: Optional[int]=None, 
            reply_markup: Optional[REPLY_MARKUP_TYPES]=None, 
            allow_sending_without_reply: Optional[bool]=None, 
            timeout: Optional[int]=None,
            explanation_entities: Optional[List[types.MessageEntity]]=None) -> types.Message:
        """
        Send polls
        :param chat_id:
        :param question:
        :param options: array of str with answers
        :param is_anonymous:
        :param type:
        :param allows_multiple_answers:
        :param correct_option_id:
        :param explanation:
        :param explanation_parse_mode:
        :param open_period:
        :param close_date:
        :param is_closed:
        :param disable_notifications:
        :param reply_to_message_id:
        :param allow_sending_without_reply:
        :param reply_markup:
        :param timeout:
        :param explanation_entities:
        :return:
        """

        if isinstance(question, types.Poll):
            raise RuntimeError("The send_poll signature was changed, please see send_poll function details.")

        return types.Message.de_json(
            apihelper.send_poll(
                self.token, chat_id,
                question, options,
                is_anonymous, type, allows_multiple_answers, correct_option_id,
                explanation, explanation_parse_mode, open_period, close_date, is_closed,
                disable_notifications, reply_to_message_id, allow_sending_without_reply, 
                reply_markup, timeout, explanation_entities))

    def stop_poll(
            self, chat_id: Union[int, str], message_id: int, 
            reply_markup: Optional[REPLY_MARKUP_TYPES]=None) -> types.Poll:
        """
        Stops poll
        :param chat_id:
        :param message_id:
        :param reply_markup:
        :return:
        """
        return types.Poll.de_json(apihelper.stop_poll(self.token, chat_id, message_id, reply_markup))

    def answer_shipping_query(
            self, shipping_query_id: str, ok: bool, 
            shipping_options: Optional[List[types.ShippingOption]]=None, 
            error_message: Optional[str]=None) -> bool:
        """
        Asks for an answer to a shipping question
        :param shipping_query_id:
        :param ok:
        :param shipping_options:
        :param error_message:
        :return:
        """
        return apihelper.answer_shipping_query(self.token, shipping_query_id, ok, shipping_options, error_message)

    def answer_pre_checkout_query(
            self, pre_checkout_query_id: int, ok: bool, 
            error_message: Optional[str]=None) -> bool:
        """
        Response to a request for pre-inspection
        :param pre_checkout_query_id:
        :param ok:
        :param error_message:
        :return:
        """
        return apihelper.answer_pre_checkout_query(self.token, pre_checkout_query_id, ok, error_message)

    def edit_message_caption(
            self, caption: str, chat_id: Optional[Union[int, str]]=None, 
            message_id: Optional[int]=None, 
            inline_message_id: Optional[str]=None,
            parse_mode: Optional[str]=None, 
            reply_markup: Optional[REPLY_MARKUP_TYPES]=None) -> Union[types.Message, bool]:
        """
        Use this method to edit captions of messages
        :param caption:
        :param chat_id:
        :param message_id:
        :param inline_message_id:
        :param parse_mode:
        :param reply_markup:
        :return:
        """
        parse_mode = self.parse_mode if (parse_mode is None) else parse_mode

        result = apihelper.edit_message_caption(self.token, caption, chat_id, message_id, inline_message_id,
                                                parse_mode, reply_markup)
        if type(result) == bool:
            return result
        return types.Message.de_json(result)

    def reply_to(self, message: types.Message, text: str, **kwargs) -> types.Message:
        """
        Convenience function for `send_message(message.chat.id, text, reply_to_message_id=message.message_id, **kwargs)`
        :param message:
        :param text:
        :param kwargs:
        :return:
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
        :param inline_query_id: Unique identifier for the answered query
        :param results: Array of results for the inline query
        :param cache_time: The maximum amount of time in seconds that the result of the inline query
            may be cached on the server.
        :param is_personal: Pass True, if results may be cached on the server side only for
            the user that sent the query.
        :param next_offset: Pass the offset that a client should send in the next query with the same text
            to receive more results.
        :param switch_pm_parameter: If passed, clients will display a button with specified text that switches the user
            to a private chat with the bot and sends the bot a start message with the parameter switch_pm_parameter
        :param switch_pm_text: 	Parameter for the start message sent to the bot when user presses the switch button
        :return: True means success.
        """
        return apihelper.answer_inline_query(self.token, inline_query_id, results, cache_time, is_personal, next_offset,
                                             switch_pm_text, switch_pm_parameter)

    def answer_callback_query(
            self, callback_query_id: str, 
            text: Optional[str]=None, show_alert: Optional[bool]=None, 
            url: Optional[str]=None, cache_time: Optional[int]=None) -> bool:
        """
        Use this method to send answers to callback queries sent from inline keyboards. The answer will be displayed to
        the user as a notification at the top of the chat screen or as an alert.
        :param callback_query_id:
        :param text:
        :param show_alert:
        :param url:
        :param cache_time:
        :return:
        """
        return apihelper.answer_callback_query(self.token, callback_query_id, text, show_alert, url, cache_time)

    def set_sticker_set_thumb(
            self, name: str, user_id: int, thumb: Union[Any, str]=None):
        """
        Use this method to set the thumbnail of a sticker set. 
        Animated thumbnails can be set for animated sticker sets only. Returns True on success.
        """
        return apihelper.set_sticker_set_thumb(self.token, name, user_id, thumb)

    def get_sticker_set(self, name: str) -> types.StickerSet:
        """
        Use this method to get a sticker set. On success, a StickerSet object is returned.
        :param name:
        :return:
        """
        result = apihelper.get_sticker_set(self.token, name)
        return types.StickerSet.de_json(result)

    def upload_sticker_file(self, user_id: int, png_sticker: Union[Any, str]) -> types.File:
        """
        Use this method to upload a .png file with a sticker for later use in createNewStickerSet and addStickerToSet
        methods (can be used multiple times). Returns the uploaded File on success.
        :param user_id:
        :param png_sticker:
        :return:
        """
        result = apihelper.upload_sticker_file(self.token, user_id, png_sticker)
        return types.File.de_json(result)

    def create_new_sticker_set(
            self, user_id: int, name: str, title: str, 
            emojis: str, 
            png_sticker: Union[Any, str], 
            tgs_sticker: Union[Any, str], 
            contains_masks: Optional[bool]=None,
            mask_position: Optional[types.MaskPosition]=None) -> bool:
        """
        Use this method to create new sticker set owned by a user. 
        The bot will be able to edit the created sticker set.
        Returns True on success.
        :param user_id:
        :param name:
        :param title:
        :param emojis:
        :param png_sticker: 
        :param tgs_sticker:
        :param contains_masks:
        :param mask_position:
        :return:
        """
        return apihelper.create_new_sticker_set(
            self.token, user_id, name, title, emojis, png_sticker, tgs_sticker, 
            contains_masks, mask_position)


    def add_sticker_to_set(
            self, user_id: int, name: str, emojis: str,
            png_sticker: Optional[Union[Any, str]]=None, 
            tgs_sticker: Optional[Union[Any, str]]=None,  
            mask_position: Optional[types.MaskPosition]=None) -> bool:
        """
        Use this method to add a new sticker to a set created by the bot. 
        It's required to pass `png_sticker` or `tgs_sticker`.
        Returns True on success.
        :param user_id:
        :param name:
        :param emojis:
        :param png_sticker: Required if `tgs_sticker` is None
        :param tgs_sticker: Required if `png_sticker` is None
        :param mask_position:
        :return:
        """
        return apihelper.add_sticker_to_set(
            self.token, user_id, name, emojis, png_sticker, tgs_sticker, mask_position)


    def set_sticker_position_in_set(self, sticker: str, position: int) -> bool:
        """
        Use this method to move a sticker in a set created by the bot to a specific position . Returns True on success.
        :param sticker:
        :param position:
        :return:
        """
        return apihelper.set_sticker_position_in_set(self.token, sticker, position)

    def delete_sticker_from_set(self, sticker: str) -> bool:
        """
        Use this method to delete a sticker from a set created by the bot. Returns True on success.
        :param sticker:
        :return:
        """
        return apihelper.delete_sticker_from_set(self.token, sticker)

    def register_for_reply(
            self, message: types.Message, callback: Callable, *args, **kwargs) -> None:
        """
        Registers a callback function to be notified when a reply to `message` arrives.

        Warning: In case `callback` as lambda function, saving reply handlers will not work.

        :param message:     The message for which we are awaiting a reply.
        :param callback:    The callback function to be called when a reply arrives. Must accept one `message`
                            parameter, which will contain the replied message.
        """
        message_id = message.message_id
        self.register_for_reply_by_message_id(message_id, callback, *args, **kwargs)

    def register_for_reply_by_message_id(
            self, message_id: int, callback: Callable, *args, **kwargs) -> None:
        """
        Registers a callback function to be notified when a reply to `message` arrives.

        Warning: In case `callback` as lambda function, saving reply handlers will not work.

        :param message_id:  The id of the message for which we are awaiting a reply.
        :param callback:    The callback function to be called when a reply arrives. Must accept one `message`
                            parameter, which will contain the replied message.
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

    def register_next_step_handler(
            self, message: types.Message, callback: Callable, *args, **kwargs) -> None:
        """
        Registers a callback function to be notified when new message arrives after `message`.

        Warning: In case `callback` as lambda function, saving next step handlers will not work.

        :param message:     The message for which we want to handle new message in the same chat.
        :param callback:    The callback function which next new message arrives.
        :param args:        Args to pass in callback func
        :param kwargs:      Args to pass in callback func
        """
        chat_id = message.chat.id
        self.register_next_step_handler_by_chat_id(chat_id, callback, *args, **kwargs)

    def register_next_step_handler_by_chat_id(
            self, chat_id: Union[int, str], callback: Callable, *args, **kwargs) -> None:
        """
        Registers a callback function to be notified when new message arrives after `message`.

        Warning: In case `callback` as lambda function, saving next step handlers will not work.

        :param chat_id:     The chat for which we want to handle new message.
        :param callback:    The callback function which next new message arrives.
        :param args:        Args to pass in callback func
        :param kwargs:      Args to pass in callback func
        """
        self.next_step_backend.register_handler(chat_id, Handler(callback, *args, **kwargs))

    def clear_step_handler(self, message: types.Message) -> None:
        """
        Clears all callback functions registered by register_next_step_handler().

        :param message:     The message for which we want to handle new message after that in same chat.
        """
        chat_id = message.chat.id
        self.clear_step_handler_by_chat_id(chat_id)

    def clear_step_handler_by_chat_id(self, chat_id: Union[int, str]) -> None:
        """
        Clears all callback functions registered by register_next_step_handler().

        :param chat_id: The chat for which we want to clear next step handlers
        """
        self.next_step_backend.clear_handlers(chat_id)

    def clear_reply_handlers(self, message: types.Message) -> None:
        """
        Clears all callback functions registered by register_for_reply() and register_for_reply_by_message_id().

        :param message: The message for which we want to clear reply handlers
        """
        message_id = message.message_id
        self.clear_reply_handlers_by_message_id(message_id)

    def clear_reply_handlers_by_message_id(self, message_id: int) -> None:
        """
        Clears all callback functions registered by register_for_reply() and register_for_reply_by_message_id().

        :param message_id: The message id for which we want to clear reply handlers
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
                new_messages.pop(i)  # removing message that was detected with next_step_handler

    @staticmethod
    def _build_handler_dict(handler, **filters):
        """
        Builds a dictionary for a handler
        :param handler:
        :param filters:
        :return:
        """
        return {
            'function': handler,
            'filters': filters
        }

    def middleware_handler(self, update_types=None):
        """
        Middleware handler decorator.

        This decorator can be used to decorate functions that must be handled as middlewares before entering any other
        message handlers
        But, be careful and check type of the update inside the handler if more than one update_type is given

        Example:

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

        """

        def decorator(handler):
            self.add_middleware_handler(handler, update_types)
            return handler

        return decorator

    def add_middleware_handler(self, handler, update_types=None):
        """
        Add middleware handler
        :param handler:
        :param update_types:
        :return:
        """
        if not apihelper.ENABLE_MIDDLEWARE:
            raise RuntimeError("Middleware is not enabled. Use apihelper.ENABLE_MIDDLEWARE.")

        if update_types:
            for update_type in update_types:
                self.typed_middleware_handlers[update_type].append(handler)
        else:
            self.default_middleware_handlers.append(handler)

    def message_handler(self, commands=None, regexp=None, func=None, content_types=None, **kwargs):
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
        :param regexp: Optional regular expression.
        :param func: Optional lambda function. The lambda receives the message to test as the first parameter.
            It must return True if the command should handle the message.
        :param content_types: Supported message content types. Must be a list. Defaults to ['text'].
        """

        if content_types is None:
            content_types = ["text"]

        def decorator(handler):
            handler_dict = self._build_handler_dict(handler,
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
        :param handler_dict:
        :return:
        """
        self.message_handlers.append(handler_dict)

    def edited_message_handler(self, commands=None, regexp=None, func=None, content_types=None, **kwargs):
        """
        Edit message handler decorator
        :param commands:
        :param regexp:
        :param func:
        :param content_types:
        :param kwargs:
        :return:
        """

        if content_types is None:
            content_types = ["text"]

        def decorator(handler):
            handler_dict = self._build_handler_dict(handler,
                                                    commands=commands,
                                                    regexp=regexp,
                                                    func=func,
                                                    content_types=content_types,
                                                    **kwargs)
            self.add_edited_message_handler(handler_dict)
            return handler

        return decorator

    def add_edited_message_handler(self, handler_dict):
        """
        Adds the edit message handler
        :param handler_dict:
        :return:
        """
        self.edited_message_handlers.append(handler_dict)

    def channel_post_handler(self, commands=None, regexp=None, func=None, content_types=None, **kwargs):
        """
        Channel post handler decorator
        :param commands:
        :param regexp:
        :param func:
        :param content_types:
        :param kwargs:
        :return:
        """

        if content_types is None:
            content_types = ["text"]

        def decorator(handler):
            handler_dict = self._build_handler_dict(handler,
                                                    commands=commands,
                                                    regexp=regexp,
                                                    func=func,
                                                    content_types=content_types,
                                                    **kwargs)
            self.add_channel_post_handler(handler_dict)
            return handler

        return decorator

    def add_channel_post_handler(self, handler_dict):
        """
        Adds channel post handler
        :param handler_dict:
        :return:
        """
        self.channel_post_handlers.append(handler_dict)

    def edited_channel_post_handler(self, commands=None, regexp=None, func=None, content_types=None, **kwargs):
        """
        Edit channel post handler decorator
        :param commands:
        :param regexp:
        :param func:
        :param content_types:
        :param kwargs:
        :return:
        """

        if content_types is None:
            content_types = ["text"]

        def decorator(handler):
            handler_dict = self._build_handler_dict(handler,
                                                    commands=commands,
                                                    regexp=regexp,
                                                    func=func,
                                                    content_types=content_types,
                                                    **kwargs)
            self.add_edited_channel_post_handler(handler_dict)
            return handler

        return decorator

    def add_edited_channel_post_handler(self, handler_dict):
        """
        Adds the edit channel post handler
        :param handler_dict:
        :return:
        """
        self.edited_channel_post_handlers.append(handler_dict)

    def inline_handler(self, func, **kwargs):
        """
        Inline call handler decorator
        :param func:
        :param kwargs:
        :return:
        """

        def decorator(handler):
            handler_dict = self._build_handler_dict(handler, func=func, **kwargs)
            self.add_inline_handler(handler_dict)
            return handler

        return decorator

    def add_inline_handler(self, handler_dict):
        """
        Adds inline call handler
        :param handler_dict:
        :return:
        """
        self.inline_handlers.append(handler_dict)

    def chosen_inline_handler(self, func, **kwargs):
        """
        Description: TBD
        :param func:
        :param kwargs:
        :return:
        """

        def decorator(handler):
            handler_dict = self._build_handler_dict(handler, func=func, **kwargs)
            self.add_chosen_inline_handler(handler_dict)
            return handler

        return decorator

    def add_chosen_inline_handler(self, handler_dict):
        """
        Description: TBD
        :param handler_dict:
        :return:
        """
        self.chosen_inline_handlers.append(handler_dict)

    def callback_query_handler(self, func, **kwargs):
        """
        Callback request handler decorator
        :param func:
        :param kwargs:
        :return:
        """

        def decorator(handler):
            handler_dict = self._build_handler_dict(handler, func=func, **kwargs)
            self.add_callback_query_handler(handler_dict)
            return handler

        return decorator

    def add_callback_query_handler(self, handler_dict):
        """
        Adds a callback request handler
        :param handler_dict:
        :return:
        """
        self.callback_query_handlers.append(handler_dict)

    def shipping_query_handler(self, func, **kwargs):
        """
        Shipping request handler
        :param func:
        :param kwargs:
        :return:
        """

        def decorator(handler):
            handler_dict = self._build_handler_dict(handler, func=func, **kwargs)
            self.add_shipping_query_handler(handler_dict)
            return handler

        return decorator

    def add_shipping_query_handler(self, handler_dict):
        """
        Adds a shipping request handler
        :param handler_dict:
        :return:
        """
        self.shipping_query_handlers.append(handler_dict)

    def pre_checkout_query_handler(self, func, **kwargs):
        """
        Pre-checkout request handler
        :param func:
        :param kwargs:
        :return:
        """

        def decorator(handler):
            handler_dict = self._build_handler_dict(handler, func=func, **kwargs)
            self.add_pre_checkout_query_handler(handler_dict)
            return handler

        return decorator

    def add_pre_checkout_query_handler(self, handler_dict):
        """
        Adds a pre-checkout request handler
        :param handler_dict:
        :return:
        """
        self.pre_checkout_query_handlers.append(handler_dict)

    def poll_handler(self, func, **kwargs):
        """
        Poll request handler
        :param func:
        :param kwargs:
        :return:
        """

        def decorator(handler):
            handler_dict = self._build_handler_dict(handler, func=func, **kwargs)
            self.add_poll_handler(handler_dict)
            return handler

        return decorator

    def add_poll_handler(self, handler_dict):
        """
        Adds a poll request handler
        :param handler_dict:
        :return:
        """
        self.poll_handlers.append(handler_dict)

    def poll_answer_handler(self, func=None, **kwargs):
        """
        Poll_answer request handler
        :param func:
        :param kwargs:
        :return:
        """

        def decorator(handler):
            handler_dict = self._build_handler_dict(handler, func=func, **kwargs)
            self.add_poll_answer_handler(handler_dict)
            return handler

        return decorator

    def add_poll_answer_handler(self, handler_dict):
        """
        Adds a poll_answer request handler
        :param handler_dict:
        :return:
        """
        self.poll_answer_handlers.append(handler_dict)
    
    def my_chat_member_handler(self, func=None, **kwargs):
        """
        my_chat_member handler
        :param func:
        :param kwargs:
        :return:
        """

        def decorator(handler):
            handler_dict = self._build_handler_dict(handler, func=func, **kwargs)
            self.add_my_chat_member_handler(handler_dict)
            return handler

        return decorator

    def add_my_chat_member_handler(self, handler_dict):
        """
        Adds a my_chat_member handler
        :param handler_dict:
        :return:
        """
        self.my_chat_member_handlers.append(handler_dict)

    def chat_member_handler(self, func=None, **kwargs):
        """
        chat_member handler
        :param func:
        :param kwargs:
        :return:
        """

        def decorator(handler):
            handler_dict = self._build_handler_dict(handler, func=func, **kwargs)
            self.add_chat_member_handler(handler_dict)
            return handler

        return decorator

    def add_chat_member_handler(self, handler_dict):
        """
        Adds a chat_member handler
        :param handler_dict:
        :return:
        """
        self.chat_member_handlers.append(handler_dict)


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

    @staticmethod
    def _test_filter(message_filter, filter_value, message):
        """
        Test filters
        :param message_filter:
        :param filter_value:
        :param message:
        :return:
        """
        test_cases = {
            'content_types': lambda msg: msg.content_type in filter_value,
            'regexp': lambda msg: msg.content_type == 'text' and re.search(filter_value, msg.text, re.IGNORECASE),
            'commands': lambda msg: msg.content_type == 'text' and util.extract_command(msg.text) in filter_value,
            'func': lambda msg: filter_value(msg)
        }

        return test_cases.get(message_filter, lambda msg: False)(message)

    def _notify_command_handlers(self, handlers, new_messages):
        """
        Notifies command handlers
        :param handlers:
        :param new_messages:
        :return:
        """
        if len(handlers) == 0:
            return
        for message in new_messages:
            for message_handler in handlers:
                if self._test_message_handler(message_handler, message):
                    self._exec_task(message_handler['function'], message)
                    break


class AsyncTeleBot(TeleBot):
    def __init__(self, *args, **kwargs):
        TeleBot.__init__(self, *args, **kwargs)
    
    # I'm not sure if `get_updates` should be added here too

    @util.async_dec()
    def enable_save_next_step_handlers(self, delay=120, filename="./.handler-saves/step.save"):
        return TeleBot.enable_save_next_step_handlers(self, delay, filename)

    @util.async_dec()
    def enable_save_reply_handlers(self, delay=120, filename="./.handler-saves/reply.save"):
        return TeleBot.enable_save_reply_handlers(self, delay, filename)

    @util.async_dec()
    def disable_save_next_step_handlers(self):
        return TeleBot.disable_save_next_step_handlers(self)

    @util.async_dec()
    def disable_save_reply_handlers(self):
        return TeleBot.enable_save_reply_handlers(self)

    @util.async_dec()
    def load_next_step_handlers(self, filename="./.handler-saves/step.save", del_file_after_loading=True):
        return TeleBot.load_next_step_handlers(self, filename, del_file_after_loading)

    @util.async_dec()
    def load_reply_handlers(self, filename="./.handler-saves/reply.save", del_file_after_loading=True):
        return TeleBot.load_reply_handlers(self, filename, del_file_after_loading)

    @util.async_dec()
    def get_me(self):
        return TeleBot.get_me(self)

    @util.async_dec()
    def log_out(self):
        return TeleBot.log_out(self)

    @util.async_dec()
    def close(self):
        return TeleBot.close(self)

    @util.async_dec()
    def get_my_commands(self):
        return TeleBot.get_my_commands(self)

    @util.async_dec()
    def set_my_commands(self, *args, **kwargs):
        return TeleBot.set_my_commands(self, *args, **kwargs)

    @util.async_dec()
    def get_file(self, *args):
        return TeleBot.get_file(self, *args)

    @util.async_dec()
    def download_file(self, *args):
        return TeleBot.download_file(self, *args)

    @util.async_dec()
    def get_user_profile_photos(self, *args, **kwargs):
        return TeleBot.get_user_profile_photos(self, *args, **kwargs)

    @util.async_dec()
    def get_chat(self, *args):
        return TeleBot.get_chat(self, *args)

    @util.async_dec()
    def leave_chat(self, *args):
        return TeleBot.leave_chat(self, *args)

    @util.async_dec()
    def get_chat_administrators(self, *args):
        return TeleBot.get_chat_administrators(self, *args)

    @util.async_dec()
    def get_chat_members_count(self, *args):
        return TeleBot.get_chat_members_count(self, *args)

    @util.async_dec()
    def set_chat_sticker_set(self, *args):
        return TeleBot.set_chat_sticker_set(self, *args)

    @util.async_dec()
    def delete_chat_sticker_set(self, *args):
        return TeleBot.delete_chat_sticker_set(self, *args)

    @util.async_dec()
    def get_chat_member(self, *args):
        return TeleBot.get_chat_member(self, *args)

    @util.async_dec()
    def send_message(self, *args, **kwargs):
        return TeleBot.send_message(self, *args, **kwargs)

    @util.async_dec()
    def send_dice(self, *args, **kwargs):
        return TeleBot.send_dice(self, *args, **kwargs)

    @util.async_dec()
    def send_animation(self, *args, **kwargs):
        return TeleBot.send_animation(self, *args, **kwargs)

    @util.async_dec()
    def forward_message(self, *args, **kwargs):
        return TeleBot.forward_message(self, *args, **kwargs)

    @util.async_dec()
    def copy_message(self, *args, **kwargs):
        return TeleBot.copy_message(self, *args, **kwargs)

    @util.async_dec()
    def delete_message(self, *args):
        return TeleBot.delete_message(self, *args)

    @util.async_dec()
    def send_photo(self, *args, **kwargs):
        return TeleBot.send_photo(self, *args, **kwargs)

    @util.async_dec()
    def send_audio(self, *args, **kwargs):
        return TeleBot.send_audio(self, *args, **kwargs)

    @util.async_dec()
    def send_voice(self, *args, **kwargs):
        return TeleBot.send_voice(self, *args, **kwargs)

    @util.async_dec()
    def send_document(self, *args, **kwargs):
        return TeleBot.send_document(self, *args, **kwargs)

    @util.async_dec()
    def send_sticker(self, *args, **kwargs):
        return TeleBot.send_sticker(self, *args, **kwargs)

    @util.async_dec()
    def send_video(self, *args, **kwargs):
        return TeleBot.send_video(self, *args, **kwargs)

    @util.async_dec()
    def send_video_note(self, *args, **kwargs):
        return TeleBot.send_video_note(self, *args, **kwargs)

    @util.async_dec()
    def send_media_group(self, *args, **kwargs):
        return TeleBot.send_media_group(self, *args, **kwargs)

    @util.async_dec()
    def send_location(self, *args, **kwargs):
        return TeleBot.send_location(self, *args, **kwargs)

    @util.async_dec()
    def edit_message_live_location(self, *args, **kwargs):
        return TeleBot.edit_message_live_location(self, *args, **kwargs)

    @util.async_dec()
    def stop_message_live_location(self, *args, **kwargs):
        return TeleBot.stop_message_live_location(self, *args, **kwargs)

    @util.async_dec()
    def send_venue(self, *args, **kwargs):
        return TeleBot.send_venue(self, *args, **kwargs)

    @util.async_dec()
    def send_contact(self, *args, **kwargs):
        return TeleBot.send_contact(self, *args, **kwargs)

    @util.async_dec()
    def send_chat_action(self, *args, **kwargs):
        return TeleBot.send_chat_action(self, *args, **kwargs)

    @util.async_dec()
    def kick_chat_member(self, *args, **kwargs):
        return TeleBot.kick_chat_member(self, *args, **kwargs)

    @util.async_dec()
    def unban_chat_member(self, *args, **kwargs):
        return TeleBot.unban_chat_member(self, *args, **kwargs)

    @util.async_dec()
    def restrict_chat_member(self, *args, **kwargs):
        return TeleBot.restrict_chat_member(self, *args, **kwargs)

    @util.async_dec()
    def promote_chat_member(self, *args, **kwargs):
        return TeleBot.promote_chat_member(self, *args, **kwargs)
    
    @util.async_dec()
    def set_chat_administrator_custom_title(self, *args, **kwargs):
        return TeleBot.set_chat_administrator_custom_title(self, *args, **kwargs)

    @util.async_dec()
    def set_chat_permissions(self, *args, **kwargs):
        return TeleBot.set_chat_permissions(self, *args, **kwargs)

    @util.async_dec()
    def create_chat_invite_link(self, *args, **kwargs):
        return TeleBot.create_chat_invite_link(self, *args, **kwargs)
    
    @util.async_dec()
    def edit_chat_invite_link(self, *args, **kwargs):
        return TeleBot.edit_chat_invite_link(self, *args, **kwargs)
    
    @util.async_dec()
    def revoke_chat_invite_link(self, *args, **kwargs):
        return TeleBot.revoke_chat_invite_link(self, *args, **kwargs)
    
    @util.async_dec()
    def export_chat_invite_link(self, *args):
        return TeleBot.export_chat_invite_link(self, *args)

    @util.async_dec()
    def set_chat_photo(self, *args):
        return TeleBot.set_chat_photo(self, *args)

    @util.async_dec()
    def delete_chat_photo(self, *args):
        return TeleBot.delete_chat_photo(self, *args)

    @util.async_dec()
    def set_chat_title(self, *args):
        return TeleBot.set_chat_title(self, *args)

    @util.async_dec()
    def set_chat_description(self, *args):
        return TeleBot.set_chat_description(self, *args)

    @util.async_dec()
    def pin_chat_message(self, *args, **kwargs):
        return TeleBot.pin_chat_message(self, *args, **kwargs)

    @util.async_dec()
    def unpin_chat_message(self, *args):
        return TeleBot.unpin_chat_message(self, *args)

    @util.async_dec()
    def unpin_all_chat_messages(self, *args):
        return TeleBot.unpin_all_chat_messages(self, *args)

    @util.async_dec()
    def edit_message_text(self, *args, **kwargs):
        return TeleBot.edit_message_text(self, *args, **kwargs)

    @util.async_dec()
    def edit_message_media(self, *args, **kwargs):
        return TeleBot.edit_message_media(self, *args, **kwargs)

    @util.async_dec()
    def edit_message_reply_markup(self, *args, **kwargs):
        return TeleBot.edit_message_reply_markup(self, *args, **kwargs)

    @util.async_dec()
    def send_game(self, *args, **kwargs):
        return TeleBot.send_game(self, *args, **kwargs)

    @util.async_dec()
    def set_game_score(self, *args, **kwargs):
        return TeleBot.set_game_score(self, *args, **kwargs)

    @util.async_dec()
    def get_game_high_scores(self, *args, **kwargs):
        return TeleBot.get_game_high_scores(self, *args, **kwargs)

    @util.async_dec()
    def send_invoice(self, *args, **kwargs):
        return TeleBot.send_invoice(self, *args, **kwargs)

    @util.async_dec()
    def answer_shipping_query(self, *args, **kwargs):
        return TeleBot.answer_shipping_query(self, *args, **kwargs)

    @util.async_dec()
    def answer_pre_checkout_query(self, *args, **kwargs):
        return TeleBot.answer_pre_checkout_query(self, *args, **kwargs)

    @util.async_dec()
    def edit_message_caption(self, *args, **kwargs):
        return TeleBot.edit_message_caption(self, *args, **kwargs)

    @util.async_dec()
    def answer_inline_query(self, *args, **kwargs):
        return TeleBot.answer_inline_query(self, *args, **kwargs)

    @util.async_dec()
    def answer_callback_query(self, *args, **kwargs):
        return TeleBot.answer_callback_query(self, *args, **kwargs)

    @util.async_dec()
    def get_sticker_set(self, *args, **kwargs):
        return TeleBot.get_sticker_set(self, *args, **kwargs)

    @util.async_dec()
    def upload_sticker_file(self, *args, **kwargs):
        return TeleBot.upload_sticker_file(self, *args, **kwargs)

    @util.async_dec()
    def create_new_sticker_set(self, *args, **kwargs):
        return TeleBot.create_new_sticker_set(self, *args, **kwargs)

    @util.async_dec()
    def add_sticker_to_set(self, *args, **kwargs):
        return TeleBot.add_sticker_to_set(self, *args, **kwargs)

    @util.async_dec()
    def set_sticker_position_in_set(self, *args, **kwargs):
        return TeleBot.set_sticker_position_in_set(self, *args, **kwargs)

    @util.async_dec()
    def delete_sticker_from_set(self, *args, **kwargs):
        return TeleBot.delete_sticker_from_set(self, *args, **kwargs)
    
    @util.async_dec()
    def set_sticker_set_thumb(self, *args, **kwargs):
        return TeleBot.set_sticker_set_thumb(self, *args, **kwargs)

    @util.async_dec()
    def send_poll(self, *args, **kwargs):
        return TeleBot.send_poll(self, *args, **kwargs)

    @util.async_dec()
    def stop_poll(self, *args, **kwargs):
        return TeleBot.stop_poll(self, *args, **kwargs)
