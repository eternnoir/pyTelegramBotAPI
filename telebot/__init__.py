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
        deleteMessage
        sendPhoto
        sendAudio
        sendDocument
        sendSticker
        sendVideo
        sendVideoNote
        sendLocation
        sendChatAction
        getUserProfilePhotos
        getUpdates
        getFile
        kickChatMember
        unbanChatMember
        restrictChatMember
        promoteChatMember
        exportChatInviteLink
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
        answerInlineQuery
        """

    def __init__(self, token, threaded=True, skip_pending=False, num_threads=2):
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
        self.edited_message_handlers = []
        self.channel_post_handlers = []
        self.edited_channel_post_handlers = []
        self.inline_handlers = []
        self.chosen_inline_handlers = []
        self.callback_query_handlers = []
        self.shipping_query_handlers = []
        self.pre_checkout_query_handlers = []

        self.threaded = threaded
        if self.threaded:
            self.worker_pool = util.ThreadPool(num_threads=num_threads)

    def set_webhook(self, url=None, certificate=None, max_connections=None, allowed_updates=None):
        return apihelper.set_webhook(self.token, url, certificate, max_connections, allowed_updates)

    def delete_webhook(self):
        """
        Use this method to remove webhook integration if you decide to switch back to getUpdates.
        :return: bool
        """
        return apihelper.delete_webhook(self.token)

    def get_webhook_info(self):
        result = apihelper.get_webhook_info(self.token)
        return types.WebhookInfo.de_json(result)

    def remove_webhook(self):
        return self.set_webhook()  # No params resets webhook

    def get_updates(self, offset=None, limit=None, timeout=20, allowed_updates=None):
        """
        Use this method to receive incoming updates using long polling (wiki). An Array of Update objects is returned.
        :param allowed_updates: Array of string. List the types of updates you want your bot to receive.
        :param offset: Integer. Identifier of the first update to be returned.
        :param limit: Integer. Limits the number of updates to be retrieved.
        :param timeout: Integer. Timeout in seconds for long polling.
        :return: array of Updates
        """
        json_updates = apihelper.get_updates(self.token, offset, limit, timeout, allowed_updates)
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
        edited_new_messages = []
        new_channel_posts = []
        new_edited_channel_posts = []
        new_inline_querys = []
        new_chosen_inline_results = []
        new_callback_querys = []
        new_shipping_querys = []
        new_pre_checkout_querys = []

        for update in updates:
            if update.update_id > self.last_update_id:
                self.last_update_id = update.update_id
            if update.message:
                new_messages.append(update.message)
            if update.edited_message:
                edited_new_messages.append(update.edited_message)
            if update.channel_post:
                new_channel_posts.append(update.channel_post)
            if update.edited_channel_post:
                new_edited_channel_posts.append(update.edited_channel_post)
            if update.inline_query:
                new_inline_querys.append(update.inline_query)
            if update.chosen_inline_result:
                new_chosen_inline_results.append(update.chosen_inline_result)
            if update.callback_query:
                new_callback_querys.append(update.callback_query)
            if update.shipping_query:
                new_shipping_querys.append(update.shipping_query)
            if update.pre_checkout_query:
                new_pre_checkout_querys.append(update.pre_checkout_query)

        logger.debug('Received {0} new updates'.format(len(updates)))
        if len(new_messages) > 0:
            self.process_new_messages(new_messages)
        if len(edited_new_messages) > 0:
            self.process_new_edited_messages(edited_new_messages)
        if len(new_channel_posts) > 0:
            self.process_new_channel_posts(new_channel_posts)
        if len(new_edited_channel_posts) > 0:
            self.process_new_edited_channel_posts(new_edited_channel_posts)
        if len(new_inline_querys) > 0:
            self.process_new_inline_query(new_inline_querys)
        if len(new_chosen_inline_results) > 0:
            self.process_new_chosen_inline_query(new_chosen_inline_results)
        if len(new_callback_querys) > 0:
            self.process_new_callback_query(new_callback_querys)
        if len(new_pre_checkout_querys) > 0:
            self.process_new_pre_checkout_query(new_pre_checkout_querys)
        if len(new_shipping_querys) > 0:
            self.process_new_shipping_query(new_shipping_querys)

    def process_new_messages(self, new_messages):
        self._append_pre_next_step_handler()
        self.__notify_update(new_messages)
        self._notify_command_handlers(self.message_handlers, new_messages)
        self._notify_message_subscribers(new_messages)
        self._notify_message_next_handler(new_messages)

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

    def __notify_update(self, new_messages):
        for listener in self.update_listener:
            self._exec_task(listener, new_messages)

    def polling(self, none_stop=False, interval=0, timeout=20):
        """
        This function creates a new Thread that calls an internal __retrieve_updates function.
        This allows the bot to retrieve Updates automagically and notify listeners and message handlers accordingly.

        Warning: Do not call this function more than once!

        Always get updates.
        :param interval:
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

    def _exec_task(self, task, *args, **kwargs):
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

    def get_chat(self, chat_id):
        """
        Use this method to get up to date information about the chat (current name of the user for one-on-one
        conversations, current username of a user, group or channel, etc.). Returns a Chat object on success.
        :param chat_id:
        :return:
        """
        result = apihelper.get_chat(self.token, chat_id)
        return types.Chat.de_json(result)

    def leave_chat(self, chat_id):
        """
        Use this method for your bot to leave a group, supergroup or channel. Returns True on success.
        :param chat_id:
        :return:
        """
        result = apihelper.leave_chat(self.token, chat_id)
        return result

    def get_chat_administrators(self, chat_id):
        """
        Use this method to get a list of administrators in a chat. On success, returns an Array of ChatMember objects
        that contains information about all chat administrators except other bots.
        :param chat_id:
        :return:
        """
        result = apihelper.get_chat_administrators(self.token, chat_id)
        ret = []
        for r in result:
            ret.append(types.ChatMember.de_json(r))
        return ret

    def get_chat_members_count(self, chat_id):
        """
        Use this method to get the number of members in a chat. Returns Int on success.
        :param chat_id:
        :return:
        """
        result = apihelper.get_chat_members_count(self.token, chat_id)
        return result

    def set_chat_sticker_set(self, chat_id, sticker_set_name):
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

    def delete_chat_sticker_set(self, chat_id):
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

    def get_chat_member(self, chat_id, user_id):
        """
        Use this method to get information about a member of a chat. Returns a ChatMember object on success.
        :param chat_id:
        :param user_id:
        :return:
        """
        result = apihelper.get_chat_member(self.token, chat_id, user_id)
        return types.ChatMember.de_json(result)

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

    def delete_message(self, chat_id, message_id):
        """
        Use this method to delete message. Returns True on success. 
        :param chat_id: in which chat to delete
        :param message_id: which message to delete
        :return: API reply.
        """
        return apihelper.delete_message(self.token, chat_id, message_id)

    def send_photo(self, chat_id, photo, caption=None, reply_to_message_id=None, reply_markup=None,
                   disable_notification=None):
        """
        Use this method to send photos.
        :param disable_notification:
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

    def send_audio(self, chat_id, audio, caption=None, duration=None, performer=None, title=None,
                   reply_to_message_id=None,
                   reply_markup=None, disable_notification=None, timeout=None):
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
            apihelper.send_audio(self.token, chat_id, audio, caption, duration, performer, title, reply_to_message_id,
                                 reply_markup, disable_notification, timeout))

    def send_voice(self, chat_id, voice, caption=None, duration=None, reply_to_message_id=None, reply_markup=None,
                   disable_notification=None, timeout=None):
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
            apihelper.send_voice(self.token, chat_id, voice, caption, duration, reply_to_message_id, reply_markup,
                                 disable_notification, timeout))

    def send_document(self, chat_id, data, reply_to_message_id=None, caption=None, reply_markup=None,
                      disable_notification=None, timeout=None):
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
                                disable_notification, timeout, caption=caption))

    def send_sticker(self, chat_id, data, reply_to_message_id=None, reply_markup=None, disable_notification=None,
                     timeout=None):
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
                                disable_notification, timeout))

    def send_video(self, chat_id, data, duration=None, caption=None, reply_to_message_id=None, reply_markup=None,
                   disable_notification=None, timeout=None):
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
                                 disable_notification, timeout))

    def send_video_note(self, chat_id, data, duration=None, length=None, reply_to_message_id=None, reply_markup=None,
                        disable_notification=None, timeout=None):
        """
        Use this method to send video files, Telegram clients support mp4 videos.
        :param chat_id: Integer : Unique identifier for the message recipient — User or GroupChat id
        :param data: InputFile or String : Video note to send. You can either pass a file_id as String to resend a video that is already on the Telegram server
        :param duration: Integer : Duration of sent video in seconds
        :param length: Integer : Video width and height, Can't be None and should be in range of (0, 640)
        :param reply_to_message_id:
        :param reply_markup:
        :return:
        """
        return types.Message.de_json(
            apihelper.send_video_note(self.token, chat_id, data, duration, length, reply_to_message_id, reply_markup,
                                      disable_notification, timeout))

    def send_media_group(self, chat_id, media, disable_notification=None, reply_to_message_id=None):
        """
        send a group of photos or videos as an album. On success, an array of the sent Messages is returned.
        :param chat_id:
        :param media:
        :param disable_notification:
        :param reply_to_message_id:
        :return:
        """
        result = apihelper.send_media_group(self.token, chat_id, media, disable_notification, reply_to_message_id)
        ret = []
        for msg in result:
            ret.append(types.Message.de_json(msg))
        return ret

    def send_location(self, chat_id, latitude, longitude, live_period=None, reply_to_message_id=None, reply_markup=None,
                      disable_notification=None):
        """
        Use this method to send point on the map.
        :param chat_id:
        :param latitude:
        :param longitude:
        :param live_period
        :param reply_to_message_id:
        :param reply_markup:
        :return: API reply.
        """
        return types.Message.de_json(
            apihelper.send_location(self.token, chat_id, latitude, longitude, live_period, reply_to_message_id,
                                    reply_markup,
                                    disable_notification))

    def edit_message_live_location(self, latitude, longitude, chat_id=None, message_id=None,
                                   inline_message_id=None, reply_markup=None):
        """
        Use this method to edit live location
        :param latitude:
        :param longitude:
        :param chat_id:
        :param message_id:
        :param inline_message_id:
        :param reply_markup:
        :return:
        """
        return types.Message.de_json(
            apihelper.edit_message_live_location(self.token, latitude, longitude, chat_id, message_id,
                                                 inline_message_id, reply_markup))

    def stop_message_live_location(self, chat_id=None, message_id=None, inline_message_id=None, reply_markup=None):
        """
        Use this method to stop updating a live location message sent by the bot
        or via the bot (for inline bots) before live_period expires
        :param chat_id:
        :param message_id:
        :param inline_message_id:
        :param reply_markup:
        :return:
        """
        return types.Message.de_json(
            apihelper.stop_message_live_location(self.token, chat_id, message_id, inline_message_id, reply_markup))

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
                        'record_audio', 'upload_audio', 'upload_document', 'find_location', 'record_video_note', 'upload_video_note'.
        :return: API reply. :type: boolean
        """
        return apihelper.send_chat_action(self.token, chat_id, action)

    def kick_chat_member(self, chat_id, user_id, until_date=None):
        """
        Use this method to kick a user from a group or a supergroup.
        :param chat_id: Int or string : Unique identifier for the target group or username of the target supergroup
        :param user_id: Int : Unique identifier of the target user
        :param until_date: Date when the user will be unbanned, unix time. If user is banned for more than 366 days or
               less than 30 seconds from the current time they are considered to be banned forever
        :return: types.Message
        """
        return apihelper.kick_chat_member(self.token, chat_id, user_id, until_date)

    def unban_chat_member(self, chat_id, user_id):
        return apihelper.unban_chat_member(self.token, chat_id, user_id)

    def restrict_chat_member(self, chat_id, user_id, until_date=None, can_send_messages=None,
                             can_send_media_messages=None, can_send_other_messages=None,
                             can_add_web_page_previews=None):
        """
        Use this method to restrict a user in a supergroup.
        The bot must be an administrator in the supergroup for this to work and must have
        the appropriate admin rights. Pass True for all boolean parameters to lift restrictions from a user.
        Returns True on success.
        :param chat_id: Int or String : 	Unique identifier for the target group or username of the target supergroup
            or channel (in the format @channelusername)
        :param user_id: Int : Unique identifier of the target user
        :param until_date: Date when restrictions will be lifted for the user, unix time.
            If user is restricted for more than 366 days or less than 30 seconds from the current time,
            they are considered to be restricted forever
        :param can_send_messages: Pass True, if the user can send text messages, contacts, locations and venues
        :param can_send_media_messages Pass True, if the user can send audios, documents, photos, videos, video notes
            and voice notes, implies can_send_messages
        :param can_send_other_messages: Pass True, if the user can send animations, games, stickers and
            use inline bots, implies can_send_media_messages
        :param can_add_web_page_previews: Pass True, if the user may add web page previews to their messages,
            implies can_send_media_messages
        :return: types.Message
        """
        return apihelper.restrict_chat_member(self.token, chat_id, user_id, until_date, can_send_messages,
                                              can_send_media_messages, can_send_other_messages,
                                              can_add_web_page_previews)

    def promote_chat_member(self, chat_id, user_id, can_change_info=None, can_post_messages=None,
                            can_edit_messages=None, can_delete_messages=None, can_invite_users=None,
                            can_restrict_members=None, can_pin_messages=None, can_promote_members=None):
        """
        Use this method to promote or demote a user in a supergroup or a channel. The bot must be an administrator
        in the chat for this to work and must have the appropriate admin rights.
        Pass False for all boolean parameters to demote a user. Returns True on success.
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
        :return:
        """
        return apihelper.promote_chat_member(self.token, chat_id, user_id, can_change_info, can_post_messages,
                                             can_edit_messages, can_delete_messages, can_invite_users,
                                             can_restrict_members, can_pin_messages, can_promote_members)

    def export_chat_invite_link(self, chat_id):
        """
        Use this method to export an invite link to a supergroup or a channel. The bot must be an administrator
        in the chat for this to work and must have the appropriate admin rights.
        Returns exported invite link as String on success.
        :param chat_id: Id: Unique identifier for the target chat or username of the target channel
            (in the format @channelusername)
        :return:
        """
        return apihelper.export_chat_invite_link(self.token, chat_id)

    def set_chat_photo(self, chat_id, photo):
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

    def delete_chat_photo(self, chat_id):
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

    def set_chat_title(self, chat_id, title):
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

    def set_chat_description(self, chat_id, description):
        """
        Use this method to change the description of a supergroup or a channel.
        The bot must be an administrator in the chat for this to work and must have the appropriate admin rights.
        Returns True on success.
        :param chat_id: Int or Str: Unique identifier for the target chat or username of the target channel
            (in the format @channelusername)
        :param description: Str: New chat description, 0-255 characters
        :return:
        """
        return apihelper.set_chat_description(self.token, chat_id, description)

    def pin_chat_message(self, chat_id, message_id, disable_notification=False):
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

    def unpin_chat_message(self, chat_id):
        """
        Use this method to unpin a message in a supergroup chat.
        The bot must be an administrator in the chat for this to work and must have the appropriate admin rights.
        Returns True on success.
        :param chat_id: Int or Str: Unique identifier for the target chat or username of the target channel
            (in the format @channelusername)
        :return:
        """
        return apihelper.unpin_chat_message(self.token, chat_id)

    def edit_message_text(self, text, chat_id=None, message_id=None, inline_message_id=None, parse_mode=None,
                          disable_web_page_preview=None, reply_markup=None):
        result = apihelper.edit_message_text(self.token, text, chat_id, message_id, inline_message_id, parse_mode,
                                             disable_web_page_preview, reply_markup)
        if type(result) == bool:  # if edit inline message return is bool not Message.
            return result
        return types.Message.de_json(result)

    def edit_message_reply_markup(self, chat_id=None, message_id=None, inline_message_id=None, reply_markup=None):
        result = apihelper.edit_message_reply_markup(self.token, chat_id, message_id, inline_message_id, reply_markup)
        if type(result) == bool:
            return result
        return types.Message.de_json(result)

    def send_game(self, chat_id, game_short_name, disable_notification=None, reply_to_message_id=None,
                  reply_markup=None):
        result = apihelper.send_game(self.token, chat_id, game_short_name, disable_notification, reply_to_message_id,
                                     reply_markup)
        return types.Message.de_json(result)

    def set_game_score(self, user_id, score, force=None, chat_id=None, message_id=None, inline_message_id=None,
                       edit_message=None):
        result = apihelper.set_game_score(self.token, user_id, score, force, chat_id, message_id, inline_message_id,
                                          edit_message)
        if type(result) == bool:
            return result
        return types.Message.de_json(result)

    def get_game_high_scores(self, user_id, chat_id=None, message_id=None, inline_message_id=None):
        result = apihelper.get_game_high_scores(self.token, user_id, chat_id, message_id, inline_message_id)
        ret = []
        for r in result:
            ret.append(types.GameHighScore.de_json(r))
        return ret

    def send_invoice(self, chat_id, title, description, invoice_payload, provider_token, currency, prices,
                     start_parameter, photo_url=None, photo_size=None, photo_width=None, photo_height=None,
                     need_name=None, need_phone_number=None, need_email=None, need_shipping_address=None,
                     is_flexible=None,
                     disable_notification=None, reply_to_message_id=None, reply_markup=None, provider_data=None):
        result = apihelper.send_invoice(self.token, chat_id, title, description, invoice_payload, provider_token,
                                        currency, prices, start_parameter, photo_url, photo_size, photo_width,
                                        photo_height,
                                        need_name, need_phone_number, need_email, need_shipping_address, is_flexible,
                                        disable_notification, reply_to_message_id, reply_markup, provider_data)
        return types.Message.de_json(result)

    def answer_shipping_query(self, shipping_query_id, ok, shipping_options=None, error_message=None):
        return apihelper.answer_shipping_query(self.token, shipping_query_id, ok, shipping_options, error_message)

    def answer_pre_checkout_query(self, pre_checkout_query_id, ok, error_message=None):
        return apihelper.answer_pre_checkout_query(self.token, pre_checkout_query_id, ok, error_message)

    def edit_message_caption(self, caption, chat_id=None, message_id=None, inline_message_id=None, reply_markup=None):
        result = apihelper.edit_message_caption(self.token, caption, chat_id, message_id, inline_message_id,
                                                reply_markup)
        if type(result) == bool:
            return result
        return types.Message.de_json(result)

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

    def answer_callback_query(self, callback_query_id, text=None, show_alert=None, url=None, cache_time=None):
        """
        Use this method to send answers to callback queries sent from inline keyboards. The answer will be displayed to
        the user as a notification at the top of the chat screen or as an alert.
        :param callback_query_id:
        :param text:
        :param show_alert:
        :return:
        """
        return apihelper.answer_callback_query(self.token, callback_query_id, text, show_alert, url, cache_time)

    # def send_sticker(self, chat_id, sticker, disable_notification=None, reply_to_message_id=None, reply_markup=None):
    #     """
    #     Use this method to send .webp stickers. On success, the sent Message is returned.
    #     :param chat_id:
    #     :param sticker:
    #     :param disable_notification:
    #     :param reply_to_message_id:
    #     :param reply_markup:
    #     :return:
    #     """
    #     result = apihelper.send_sticker(self.token, chat_id, sticker, disable_notification, reply_markup, reply_markup)
    #     return types.Message.de_json(result)

    def get_sticker_set(self, name):
        """
        Use this method to get a sticker set. On success, a StickerSet object is returned.
        :param token:
        :param name:
        :return:
        """
        result = apihelper.get_sticker_set(self.token, name)
        return types.StickerSet.de_json(result)

    def upload_sticker_file(self, user_id, png_sticker):
        """
        Use this method to upload a .png file with a sticker for later use in createNewStickerSet and addStickerToSet
        methods (can be used multiple times). Returns the uploaded File on success.
        :param user_id:
        :param png_sticker:
        :return:
        """
        result = apihelper.upload_sticker_file(self.token, user_id, png_sticker)
        return types.File.de_json(result)

    def create_new_sticker_set(self, user_id, name, title, png_sticker, emojis, contains_masks=None,
                               mask_position=None):
        """
        Use this method to create new sticker set owned by a user. The bot will be able to edit the created sticker set.
        Returns True on success.
        :param user_id:
        :param name:
        :param title:
        :param png_sticker:
        :param emojis:
        :param contains_masks:
        :param mask_position:
        :return:
        """
        return apihelper.create_new_sticker_set(self.token, user_id, name, title, png_sticker, emojis, contains_masks,
                                                mask_position)

    def add_sticker_to_set(self, user_id, name, png_sticker, emojis, mask_position=None):
        """
        Use this method to add a new sticker to a set created by the bot. Returns True on success.
        :param user_id:
        :param name:
        :param png_sticker:
        :param emojis:
        :param mask_position:
        :return:
        """
        return apihelper.add_sticker_to_set(self.token, user_id, name, png_sticker, emojis, mask_position)

    def set_sticker_position_in_set(self, sticker, position):
        """
        Use this method to move a sticker in a set created by the bot to a specific position . Returns True on success.
        :param sticker:
        :param position:
        :return:
        """
        return apihelper.set_sticker_position_in_set(self.token, sticker, position)

    def delete_sticker_from_set(self, sticker):
        """
        Use this method to delete a sticker from a set created by the bot. Returns True on success.
        :param sticker:
        :return:
        """
        return apihelper.delete_sticker_from_set(self.token, sticker)

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

    def clear_step_handler(self, message):
        """
        Clears all callback functions registered by register_next_step_handler().

        :param message:     The message for which we want to handle new message after that in same chat.
        """
        chat_id = message.chat.id
        self.pre_message_subscribers_next_step[chat_id] = []

    def _notify_message_next_handler(self, new_messages):
        for message in new_messages:
            chat_id = message.chat.id
            if chat_id in self.message_subscribers_next_step:
                handlers = self.message_subscribers_next_step[chat_id]
                for handler in handlers:
                    self._exec_task(handler, message)
                self.message_subscribers_next_step.pop(chat_id, None)

    def _append_pre_next_step_handler(self):
        for k in self.pre_message_subscribers_next_step.keys():
            if k in self.message_subscribers_next_step:
                self.message_subscribers_next_step[k].extend(self.pre_message_subscribers_next_step[k])
            else:
                self.message_subscribers_next_step[k] = self.pre_message_subscribers_next_step[k]
        self.pre_message_subscribers_next_step = {}

    def _build_handler_dict(self, handler, **filters):
        return {
            'function': handler,
            'filters': filters
        }

    def message_handler(self, commands=None, regexp=None, func=None, content_types=['text'], **kwargs):
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
            handler_dict = self._build_handler_dict(handler,
                                                    commands=commands,
                                                    regexp=regexp,
                                                    func=func,
                                                    content_types=content_types,
                                                    **kwargs)

            self.add_message_handler(handler_dict)

            return handler

        return decorator

    def add_message_handler(self, handler_dict):
        self.message_handlers.append(handler_dict)

    def edited_message_handler(self, commands=None, regexp=None, func=None, content_types=['text'], **kwargs):
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
        self.edited_message_handlers.append(handler_dict)

    def channel_post_handler(self, commands=None, regexp=None, func=None, content_types=['text'], **kwargs):
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
        self.channel_post_handlers.append(handler_dict)

    def edited_channel_post_handler(self, commands=None, regexp=None, func=None, content_types=['text'], **kwargs):
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
        self.edited_channel_post_handlers.append(handler_dict)

    def inline_handler(self, func, **kwargs):
        def decorator(handler):
            handler_dict = self._build_handler_dict(handler, func=func, **kwargs)
            self.add_inline_handler(handler_dict)
            return handler

        return decorator

    def add_inline_handler(self, handler_dict):
        self.inline_handlers.append(handler_dict)

    def chosen_inline_handler(self, func, **kwargs):
        def decorator(handler):
            handler_dict = self._build_handler_dict(handler, func=func, **kwargs)
            self.add_chosen_inline_handler(handler_dict)
            return handler

        return decorator

    def add_chosen_inline_handler(self, handler_dict):
        self.chosen_inline_handlers.append(handler_dict)

    def callback_query_handler(self, func, **kwargs):
        def decorator(handler):
            handler_dict = self._build_handler_dict(handler, func=func, **kwargs)
            self.add_callback_query_handler(handler_dict)
            return handler

        return decorator

    def add_callback_query_handler(self, handler_dict):
        self.callback_query_handlers.append(handler_dict)

    def shipping_query_handler(self, func, **kwargs):
        def decorator(handler):
            handler_dict = self._build_handler_dict(handler, func=func, **kwargs)
            self.add_shipping_query_handler(handler_dict)
            return handler

        return decorator

    def add_shipping_query_handler(self, handler_dict):
        self.shipping_query_handlers.append(handler_dict)

    def pre_checkout_query_handler(self, func, **kwargs):
        def decorator(handler):
            handler_dict = self._build_handler_dict(handler, func=func, **kwargs)
            self.add_pre_checkout_query_handler(handler_dict)
            return handler

        return decorator

    def add_pre_checkout_query_handler(self, handler_dict):
        self.pre_checkout_query_handlers.append(handler_dict)

    def _test_message_handler(self, message_handler, message):
        for filter, filter_value in six.iteritems(message_handler['filters']):
            if filter_value is None:
                continue

            if not self._test_filter(filter, filter_value, message):
                return False

        return True

    def _test_filter(self, filter, filter_value, message):
        test_cases = {
            'content_types': lambda msg: msg.content_type in filter_value,
            'regexp': lambda msg: msg.content_type == 'text' and re.search(filter_value, msg.text, re.IGNORECASE),
            'commands': lambda msg: msg.content_type == 'text' and util.extract_command(msg.text) in filter_value,
            'func': lambda msg: filter_value(msg)
        }

        return test_cases.get(filter, lambda msg: False)(message)

    def _notify_command_handlers(self, handlers, new_messages):
        for message in new_messages:
            # if message has next step handler, dont exec command handlers
            if hasattr(message, 'chat') and message.chat and (message.chat.id in self.message_subscribers_next_step):
                continue
            for message_handler in handlers:
                if self._test_message_handler(message_handler, message):
                    self._exec_task(message_handler['function'], message)
                    break


class AsyncTeleBot(TeleBot):
    def __init__(self, *args, **kwargs):
        TeleBot.__init__(self, *args, **kwargs)

    @util.async()
    def get_me(self):
        return TeleBot.get_me(self)

    @util.async()
    def get_file(self, *args):
        return TeleBot.get_file(self, *args)

    @util.async()
    def download_file(self, *args):
        return TeleBot.download_file(self, *args)

    @util.async()
    def get_user_profile_photos(self, *args, **kwargs):
        return TeleBot.get_user_profile_photos(self, *args, **kwargs)

    @util.async()
    def get_chat(self, *args):
        return TeleBot.get_chat(self, *args)

    @util.async()
    def leave_chat(self, *args):
        return TeleBot.leave_chat(self, *args)

    @util.async()
    def get_chat_administrators(self, *args):
        return TeleBot.get_chat_administrators(self, *args)

    @util.async()
    def get_chat_members_count(self, *args):
        return TeleBot.get_chat_members_count(self, *args)

    @util.async()
    def set_chat_sticker_set(self, *args):
        return TeleBot.set_chat_sticker_set(self, *args)

    @util.async()
    def delete_chat_sticker_set(self, *args):
        return TeleBot.delete_chat_sticker_set(self, *args)

    @util.async()
    def get_chat_member(self, *args):
        return TeleBot.get_chat_member(self, *args)

    @util.async()
    def send_message(self, *args, **kwargs):
        return TeleBot.send_message(self, *args, **kwargs)

    @util.async()
    def forward_message(self, *args, **kwargs):
        return TeleBot.forward_message(self, *args, **kwargs)

    @util.async()
    def delete_message(self, *args):
        return TeleBot.delete_message(self, *args)

    @util.async()
    def send_photo(self, *args, **kwargs):
        return TeleBot.send_photo(self, *args, **kwargs)

    @util.async()
    def send_audio(self, *args, **kwargs):
        return TeleBot.send_audio(self, *args, **kwargs)

    @util.async()
    def send_voice(self, *args, **kwargs):
        return TeleBot.send_voice(self, *args, **kwargs)

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
    def send_video_note(self, *args, **kwargs):
        return TeleBot.send_video_note(self, *args, **kwargs)

    @util.async()
    def send_media_group(self, *args, **kwargs):
        return TeleBot.send_media_group(self, *args, **kwargs)

    @util.async()
    def send_location(self, *args, **kwargs):
        return TeleBot.send_location(self, *args, **kwargs)

    @util.async()
    def edit_message_live_location(self, *args, **kwargs):
        return TeleBot.edit_message_live_location(self, *args, **kwargs)

    @util.async()
    def stop_message_live_location(self, *args, **kwargs):
        return TeleBot.stop_message_live_location(self, *args, **kwargs)

    @util.async()
    def send_venue(self, *args, **kwargs):
        return TeleBot.send_venue(self, *args, **kwargs)

    @util.async()
    def send_contact(self, *args, **kwargs):
        return TeleBot.send_contact(self, *args, **kwargs)

    @util.async()
    def send_chat_action(self, *args, **kwargs):
        return TeleBot.send_chat_action(self, *args, **kwargs)

    @util.async()
    def kick_chat_member(self, *args, **kwargs):
        return TeleBot.kick_chat_member(self, *args, **kwargs)

    @util.async()
    def unban_chat_member(self, *args):
        return TeleBot.unban_chat_member(self, *args)

    @util.async()
    def restrict_chat_member(self, *args, **kwargs):
        return TeleBot.restrict_chat_member(self, *args, **kwargs)

    @util.async()
    def promote_chat_member(self, *args, **kwargs):
        return TeleBot.promote_chat_member(self, *args, **kwargs)

    @util.async()
    def export_chat_invite_link(self, *args):
        return TeleBot.export_chat_invite_link(self, *args)

    @util.async()
    def set_chat_photo(self, *args):
        return TeleBot.set_chat_photo(self, *args)

    @util.async()
    def delete_chat_photo(self, *args):
        return TeleBot.delete_chat_photo(self, *args)

    @util.async()
    def set_chat_title(self, *args):
        return TeleBot.set_chat_title(self, *args)

    @util.async()
    def set_chat_description(self, *args):
        return TeleBot.set_chat_description(self, *args)

    @util.async()
    def pin_chat_message(self, *args, **kwargs):
        return TeleBot.pin_chat_message(self, *args, **kwargs)

    @util.async()
    def unpin_chat_message(self, *args):
        return TeleBot.unpin_chat_message(self, *args)

    @util.async()
    def edit_message_text(self, *args, **kwargs):
        return TeleBot.edit_message_text(self, *args, **kwargs)

    @util.async()
    def edit_message_reply_markup(self, *args, **kwargs):
        return TeleBot.edit_message_reply_markup(self, *args, **kwargs)

    @util.async()
    def send_game(self, *args, **kwargs):
        return TeleBot.send_game(self, *args, **kwargs)

    @util.async()
    def set_game_score(self, *args, **kwargs):
        return TeleBot.set_game_score(self, *args, **kwargs)

    @util.async()
    def get_game_high_scores(self, *args, **kwargs):
        return TeleBot.get_game_high_scores(self, *args, **kwargs)

    @util.async()
    def send_invoice(self, *args, **kwargs):
        return TeleBot.send_invoice(self, *args, **kwargs)

    @util.async()
    def answer_shipping_query(self, *args, **kwargs):
        return TeleBot.answer_shipping_query(self, *args, **kwargs)

    @util.async()
    def answer_pre_checkout_query(self, *args, **kwargs):
        return TeleBot.answer_pre_checkout_query(self, *args, **kwargs)

    @util.async()
    def edit_message_caption(self, *args, **kwargs):
        return TeleBot.edit_message_caption(self, *args, **kwargs)

    @util.async()
    def answer_inline_query(self, *args, **kwargs):
        return TeleBot.answer_inline_query(self, *args, **kwargs)

    @util.async()
    def answer_callback_query(self, *args, **kwargs):
        return TeleBot.answer_callback_query(self, *args, **kwargs)

    @util.async()
    def send_sticker(self, *args, **kwargs):
        return TeleBot.send_sticker(self, *args, **kwargs)

    @util.async()
    def get_sticker_set(self, *args, **kwargs):
        return TeleBot.get_sticker_set(self, *args, **kwargs)

    @util.async()
    def upload_sticker_file(self, *args, **kwargs):
        return TeleBot.upload_sticker_file(self, *args, **kwargs)

    @util.async()
    def create_new_sticker_set(self, *args, **kwargs):
        return TeleBot.create_new_sticker_set(self, *args, **kwargs)

    @util.async()
    def add_sticker_to_set(self, *args, **kwargs):
        return TeleBot.add_sticker_to_set(self, *args, **kwargs)

    @util.async()
    def set_sticker_position_in_set(self, *args, **kwargs):
        return TeleBot.set_sticker_position_in_set(self, *args, **kwargs)

    @util.async()
    def delete_sticker_from_set(self, *args, **kwargs):
        return TeleBot.delete_sticker_from_set(self, *args, **kwargs)
