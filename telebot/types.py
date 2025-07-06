# -*- coding: utf-8 -*-
from __future__ import annotations

from io import IOBase
import logging
import os
import traceback
from pathlib import Path
from typing import Dict, List, Optional, Union, Any, Tuple
from abc import ABC

try:
    # noinspection PyPackageRequirements
    import ujson as json
except ImportError:
    import json

from telebot import service_utils
from telebot.formatting import apply_html_entities


DISABLE_KEYLEN_ERROR = False
DEPRECATION_STACK_SHOW_DEPTH = 0

logger = logging.getLogger('TeleBot')


def log_deprecation_warning(warning_message, logging_level=logging.WARNING):
    """
    Logs a deprecation warning message.
    """
    logger.log(logging_level, warning_message)
    if DEPRECATION_STACK_SHOW_DEPTH:
        logger.log(logging_level, "".join(traceback.format_stack(limit=DEPRECATION_STACK_SHOW_DEPTH)))


class JsonSerializable(object):
    """
    Subclasses of this class are guaranteed to be able to be converted to JSON format.
    All subclasses of this class must override to_json.
    """

    def to_json(self):
        """
        Returns a JSON string representation of this class.

        :meta private:

        This function must be overridden by subclasses.
        :return: a JSON formatted string.
        """
        raise NotImplementedError


class Dictionaryable(object):
    """
    Subclasses of this class are guaranteed to be able to be converted to dictionary.
    All subclasses of this class must override to_dict.
    """

    def to_dict(self):
        """
        Returns a DICT with class field values

        :meta private:

        This function must be overridden by subclasses.
        :return: a DICT
        """
        raise NotImplementedError


class JsonDeserializable(object):
    """
    Subclasses of this class are guaranteed to be able to be created from a json-style dict or json formatted string.
    All subclasses of this class must override de_json.
    """

    @classmethod
    def de_json(cls, json_string):
        """
        Returns an instance of this class from the given json dict or string.

        :meta private:

        This function must be overridden by subclasses.
        :return: an instance of this class created from the given json dict or string.
        """
        raise NotImplementedError

    @staticmethod
    def check_json(json_type, dict_copy = True):
        """
        Checks whether json_type is a dict or a string. If it is already a dict, it is returned as-is.
        If it is not, it is converted to a dict by means of json.loads(json_type)

        :meta private:
        
        :param json_type: input json or parsed dict
        :param dict_copy: if dict is passed and it is changed outside - should be True!
        :return: Dictionary parsed from json or original dict
        """
        if service_utils.is_dict(json_type):
            return json_type.copy() if dict_copy else json_type
        elif service_utils.is_string(json_type):
            return json.loads(json_type)
        else:
            raise ValueError("json_type should be a json dict or string.")

    def __str__(self):
        d = {
            x: y.__dict__ if hasattr(y, '__dict__') else y
            for x, y in self.__dict__.items()
        }
        return str(d)


class Update(JsonDeserializable):
    """
    This object represents an incoming update.At most one of the optional parameters can be present in any given update.

    Telegram Documentation: https://core.telegram.org/bots/api#update

    :param update_id: The update's unique identifier. Update identifiers start from a certain positive number and 
        increase sequentially. This ID becomes especially handy if you're using webhooks, since it allows you to ignore 
        repeated updates or to restore the correct update sequence, should they get out of order. If there are no new updates 
        for at least a week, then identifier of the next update will be chosen randomly instead of sequentially.
    :type update_id: :obj:`int`

    :param message: Optional. New incoming message of any kind - text, photo, sticker, etc.
    :type message: :class:`telebot.types.Message`

    :param edited_message: Optional. New version of a message that is known to the bot and was edited
    :type edited_message: :class:`telebot.types.Message`

    :param channel_post: Optional. New incoming channel post of any kind - text, photo, sticker, etc.
    :type channel_post: :class:`telebot.types.Message`

    :param edited_channel_post: Optional. New version of a channel post that is known to the bot and was edited
    :type edited_channel_post: :class:`telebot.types.Message`

    :param message_reaction: Optional. A reaction to a message was changed by a user. The bot must be an administrator in the chat
        and must explicitly specify "message_reaction" in the list of allowed_updates to receive these updates. The update isn't received for reactions set by bots.
    :type message_reaction: :class:`telebot.types.MessageReactionUpdated`

    :param message_reaction_count: Optional. Reactions to a message with anonymous reactions were changed. The bot must be an administrator in the chat and must explicitly specify
        "message_reaction_count" in the list of allowed_updates to receive these updates.
    :type message_reaction_count: :class:`telebot.types.MessageReactionCountUpdated`

    :param inline_query: Optional. New incoming inline query
    :type inline_query: :class:`telebot.types.InlineQuery`

    :param chosen_inline_result: Optional. The result of an inline query that was chosen by a user and sent to their chat 
        partner. Please see our documentation on the feedback collecting for details on how to enable these updates for your 
        bot.
    :type chosen_inline_result: :class:`telebot.types.ChosenInlineResult`

    :param callback_query: Optional. New incoming callback query
    :type callback_query: :class:`telebot.types.CallbackQuery`

    :param shipping_query: Optional. New incoming shipping query. Only for invoices with flexible price
    :type shipping_query: :class:`telebot.types.ShippingQuery`

    :param pre_checkout_query: Optional. New incoming pre-checkout query. Contains full information about 
        checkout
    :type pre_checkout_query: :class:`telebot.types.PreCheckoutQuery`

    :purchased_paid_media: Optional. A user purchased paid media with a non-empty payload sent by the bot in a non-channel chat
    :type purchased_paid_media: :class:`telebot.types.PaidMediaPurchased`

    :param poll: Optional. New poll state. Bots receive only updates about stopped polls and polls, which are sent by the 
        bot
    :type poll: :class:`telebot.types.Poll`

    :param poll_answer: Optional. A user changed their answer in a non-anonymous poll. Bots receive new votes only in 
        polls that were sent by the bot itself.
    :type poll_answer: :class:`telebot.types.PollAnswer`

    :param my_chat_member: Optional. The bot's chat member status was updated in a chat. For private chats, this update 
        is received only when the bot is blocked or unblocked by the user.
    :type my_chat_member: :class:`telebot.types.ChatMemberUpdated`

    :param chat_member: Optional. A chat member's status was updated in a chat. The bot must be an administrator in the 
        chat and must explicitly specify “chat_member” in the list of allowed_updates to receive these updates.
    :type chat_member: :class:`telebot.types.ChatMemberUpdated`

    :param chat_join_request: Optional. A request to join the chat has been sent. The bot must have the 
        can_invite_users administrator right in the chat to receive these updates.
    :type chat_join_request: :class:`telebot.types.ChatJoinRequest`

    :param chat_boost: Optional. A chat boost was added or changed. The bot must be an administrator in the chat to receive these updates.
    :type chat_boost: :class:`telebot.types.ChatBoostUpdated`

    :param removed_chat_boost: Optional. A chat boost was removed. The bot must be an administrator in the chat to receive these updates.
    :type removed_chat_boost: :class:`telebot.types.RemovedChatBoost`

    :param business_connection: Optional. The bot was connected to or disconnected from a business account, or a user edited an existing connection with the bot
    :type business_connection: :class:`telebot.types.BusinessConnection`

    :param business_message: Optional. New non-service message from a connected business account
    :type business_message: :class:`telebot.types.Message`

    :param edited_business_message: Optional. New version of a non-service message from a connected business account that is known to the bot and was edited
    :type edited_business_message: :class:`telebot.types.Message`

    :param deleted_business_messages: Optional. Service message: the chat connected to the business account was deleted
    :type deleted_business_messages: :class:`telebot.types.BusinessMessagesDeleted`

    :return: Instance of the class
    :rtype: :class:`telebot.types.Update`

    """
    @classmethod
    def de_json(cls, json_string):
        if json_string is None: return None
        obj = cls.check_json(json_string, dict_copy=False)
        update_id = obj['update_id']
        message = Message.de_json(obj.get('message'))
        edited_message = Message.de_json(obj.get('edited_message'))
        channel_post = Message.de_json(obj.get('channel_post'))
        edited_channel_post = Message.de_json(obj.get('edited_channel_post'))
        inline_query = InlineQuery.de_json(obj.get('inline_query'))
        chosen_inline_result = ChosenInlineResult.de_json(obj.get('chosen_inline_result'))
        callback_query = CallbackQuery.de_json(obj.get('callback_query'))
        shipping_query = ShippingQuery.de_json(obj.get('shipping_query'))
        pre_checkout_query = PreCheckoutQuery.de_json(obj.get('pre_checkout_query'))
        poll = Poll.de_json(obj.get('poll'))
        poll_answer = PollAnswer.de_json(obj.get('poll_answer'))
        my_chat_member = ChatMemberUpdated.de_json(obj.get('my_chat_member'))
        chat_member = ChatMemberUpdated.de_json(obj.get('chat_member'))
        chat_join_request = ChatJoinRequest.de_json(obj.get('chat_join_request'))
        message_reaction = MessageReactionUpdated.de_json(obj.get('message_reaction'))
        message_reaction_count = MessageReactionCountUpdated.de_json(obj.get('message_reaction_count'))
        removed_chat_boost = ChatBoostRemoved.de_json(obj.get('removed_chat_boost'))
        chat_boost = ChatBoostUpdated.de_json(obj.get('chat_boost'))
        business_connection = BusinessConnection.de_json(obj.get('business_connection'))
        business_message = Message.de_json(obj.get('business_message'))
        edited_business_message = Message.de_json(obj.get('edited_business_message'))
        deleted_business_messages = BusinessMessagesDeleted.de_json(obj.get('deleted_business_messages'))
        purchased_paid_media = PaidMediaPurchased.de_json(obj.get('purchased_paid_media'))

        return cls(update_id, message, edited_message, channel_post, edited_channel_post, inline_query,
                   chosen_inline_result, callback_query, shipping_query, pre_checkout_query, poll, poll_answer,
                   my_chat_member, chat_member, chat_join_request, message_reaction, message_reaction_count,
                   removed_chat_boost, chat_boost, business_connection, business_message, edited_business_message,
                   deleted_business_messages, purchased_paid_media)

    def __init__(self, update_id, message, edited_message, channel_post, edited_channel_post, inline_query,
                 chosen_inline_result, callback_query, shipping_query, pre_checkout_query, poll, poll_answer,
                 my_chat_member, chat_member, chat_join_request, message_reaction, message_reaction_count,
                 removed_chat_boost, chat_boost, business_connection, business_message, edited_business_message,
                 deleted_business_messages, purchased_paid_media):
        self.update_id: int = update_id
        self.message: Optional[Message] = message
        self.edited_message: Optional[Message] = edited_message
        self.channel_post: Optional[Message] = channel_post
        self.edited_channel_post: Optional[Message] = edited_channel_post
        self.inline_query: Optional[InlineQuery] = inline_query
        self.chosen_inline_result: Optional[ChosenInlineResult] = chosen_inline_result
        self.callback_query: Optional[CallbackQuery] = callback_query
        self.shipping_query: Optional[ShippingQuery] = shipping_query
        self.pre_checkout_query: Optional[PreCheckoutQuery] = pre_checkout_query
        self.poll: Optional[Poll] = poll
        self.poll_answer: Optional[PollAnswer] = poll_answer
        self.my_chat_member: Optional[ChatMemberUpdated] = my_chat_member
        self.chat_member: Optional[ChatMemberUpdated] = chat_member
        self.chat_join_request: Optional[ChatJoinRequest] = chat_join_request
        self.message_reaction: Optional[MessageReactionUpdated] = message_reaction
        self.message_reaction_count: Optional[MessageReactionCountUpdated] = message_reaction_count
        self.removed_chat_boost: Optional[ChatBoostRemoved] = removed_chat_boost
        self.chat_boost: Optional[ChatBoostUpdated] = chat_boost
        self.business_connection: Optional[BusinessConnection] = business_connection
        self.business_message: Optional[Message] = business_message
        self.edited_business_message: Optional[Message] = edited_business_message
        self.deleted_business_messages: Optional[BusinessMessagesDeleted] = deleted_business_messages
        self.purchased_paid_media: Optional[PaidMediaPurchased] = purchased_paid_media



class ChatMemberUpdated(JsonDeserializable):
    """
    This object represents changes in the status of a chat member.

    Telegram Documentation: https://core.telegram.org/bots/api#chatmemberupdated

    :param chat: Chat the user belongs to
    :type chat: :class:`telebot.types.Chat`

    :param from_user: Performer of the action, which resulted in the change
    :type from_user: :class:`telebot.types.User`

    :param date: Date the change was done in Unix time
    :type date: :obj:`int`

    :param old_chat_member: Previous information about the chat member
    :type old_chat_member: :class:`telebot.types.ChatMember`

    :param new_chat_member: New information about the chat member
    :type new_chat_member: :class:`telebot.types.ChatMember`

    :param invite_link: Optional. Chat invite link, which was used by the user to join the chat; for joining by invite 
        link events only.
    :type invite_link: :class:`telebot.types.ChatInviteLink`

    :param via_join_request: Optional. True, if the user joined the chat after sending a direct join request without using an invite link and being approved by an administrator
    :type via_join_request: :obj:`bool`

    :param via_chat_folder_invite_link: Optional. True, if the user joined the chat via a chat folder invite link
    :type via_chat_folder_invite_link: :obj:`bool`

    :return: Instance of the class
    :rtype: :class:`telebot.types.ChatMemberUpdated`
    """
    @classmethod
    def de_json(cls, json_string):
        if json_string is None: return None
        obj = cls.check_json(json_string)
        obj['chat'] = Chat.de_json(obj['chat'])
        obj['from_user'] = User.de_json(obj.pop('from'))
        obj['old_chat_member'] = ChatMember.de_json(obj['old_chat_member'])
        obj['new_chat_member'] = ChatMember.de_json(obj['new_chat_member'])
        obj['invite_link'] = ChatInviteLink.de_json(obj.get('invite_link'))
        return cls(**obj)
    
    def __init__(self, chat, from_user, date, old_chat_member, new_chat_member, invite_link=None,
                 via_join_request=None, via_chat_folder_invite_link=None,
                 **kwargs):
        self.chat: Chat = chat
        self.from_user: User = from_user
        self.date: int = date
        self.old_chat_member: ChatMember = old_chat_member
        self.new_chat_member: ChatMember = new_chat_member
        self.invite_link: Optional[ChatInviteLink] = invite_link
        self.via_join_request: Optional[bool] = via_join_request
        self.via_chat_folder_invite_link: Optional[bool] = via_chat_folder_invite_link

    @property
    def difference(self) -> Dict[str, List]:
        """
        Get the difference between `old_chat_member` and `new_chat_member`
        as a dict in the following format {'parameter': [old_value, new_value]}
        E.g {'status': ['member', 'kicked'], 'until_date': [None, 1625055092]}


        :return: Dict of differences
        :rtype: Dict[str, List]
        """
        old: Dict = self.old_chat_member.__dict__
        new: Dict = self.new_chat_member.__dict__
        dif = {}
        for key in new:
            if key == 'user': continue
            if new[key] != old[key]:
                dif[key] = [old[key], new[key]]
        return dif
    

class ChatJoinRequest(JsonDeserializable):
    """
    Represents a join request sent to a chat.

    Telegram Documentation: https://core.telegram.org/bots/api#chatjoinrequest

    :param chat: Chat to which the request was sent
    :type chat: :class:`telebot.types.Chat`

    :param from_user: User that sent the join request
    :type from_user: :class:`telebot.types.User`

    :param user_chat_id: Optional. Identifier of a private chat with the user who sent the join request.
        This number may have more than 32 significant bits and some programming languages may have difficulty/silent
        defects in interpreting it. But it has at most 52 significant bits, so a 64-bit integer or double-precision
        float type are safe for storing this identifier. The bot can use this identifier for 24 hours to send messages
        until the join request is processed, assuming no other administrator contacted the user.
    :type user_chat_id: :obj:`int`

    :param date: Date the request was sent in Unix time
    :type date: :obj:`int`

    :param bio: Optional. Bio of the user.
    :type bio: :obj:`str`

    :param invite_link: Optional. Chat invite link that was used by the user to send the join request
    :type invite_link: :class:`telebot.types.ChatInviteLink`

    :return: Instance of the class
    :rtype: :class:`telebot.types.ChatJoinRequest`
    """
    @classmethod
    def de_json(cls, json_string):
        if json_string is None: return None
        obj = cls.check_json(json_string)
        obj['chat'] = Chat.de_json(obj['chat'])
        obj['from_user'] = User.de_json(obj['from'])
        obj['invite_link'] = ChatInviteLink.de_json(obj.get('invite_link'))
        return cls(**obj)
    
    def __init__(self, chat, from_user, user_chat_id, date, bio=None, invite_link=None, **kwargs):
        self.chat: Chat = chat
        self.from_user: User = from_user
        self.date: str = date
        self.bio: Optional[str] = bio
        self.invite_link: Optional[ChatInviteLink] = invite_link
        self.user_chat_id: int = user_chat_id

class WebhookInfo(JsonDeserializable):
    """
    Describes the current status of a webhook.

    Telegram Documentation: https://core.telegram.org/bots/api#webhookinfo

    :param url: Webhook URL, may be empty if webhook is not set up
    :type url: :obj:`str`

    :param has_custom_certificate: True, if a custom certificate was provided for webhook certificate checks
    :type has_custom_certificate: :obj:`bool`

    :param pending_update_count: Number of updates awaiting delivery
    :type pending_update_count: :obj:`int`

    :param ip_address: Optional. Currently used webhook IP address
    :type ip_address: :obj:`str`

    :param last_error_date: Optional. Unix time for the most recent error that happened when trying to deliver an 
        update via webhook
    :type last_error_date: :obj:`int`

    :param last_error_message: Optional. Error message in human-readable format for the most recent error that 
        happened when trying to deliver an update via webhook
    :type last_error_message: :obj:`str`

    :param last_synchronization_error_date: Optional. Unix time of the most recent error that happened when trying 
        to synchronize available updates with Telegram datacenters
    :type last_synchronization_error_date: :obj:`int`

    :param max_connections: Optional. The maximum allowed number of simultaneous HTTPS connections to the webhook 
        for update delivery
    :type max_connections: :obj:`int`

    :param allowed_updates: Optional. A list of update types the bot is subscribed to. Defaults to all update types 
        except chat_member
    :type allowed_updates: :obj:`list` of :obj:`str`

    :return: Instance of the class
    :rtype: :class:`telebot.types.WebhookInfo`
    """
    @classmethod
    def de_json(cls, json_string):
        if json_string is None: return None
        obj = cls.check_json(json_string, dict_copy=False)
        return cls(**obj)

    def __init__(self, url, has_custom_certificate, pending_update_count, ip_address=None, 
                 last_error_date=None, last_error_message=None, last_synchronization_error_date=None,
                 max_connections=None, allowed_updates=None, **kwargs):
        self.url: str = url
        self.has_custom_certificate: bool = has_custom_certificate
        self.pending_update_count: int = pending_update_count
        self.ip_address: Optional[str] = ip_address
        self.last_error_date: Optional[int] = last_error_date
        self.last_error_message: Optional[str] = last_error_message
        self.last_synchronization_error_date: Optional[int] = last_synchronization_error_date
        self.max_connections: Optional[int] = max_connections
        self.allowed_updates: Optional[int] = allowed_updates


class User(JsonDeserializable, Dictionaryable, JsonSerializable):
    """
    This object represents a Telegram user or bot.

    Telegram Documentation: https://core.telegram.org/bots/api#user

    :param id: Unique identifier for this user or bot. This number may have more than 32 significant bits and some 
        programming languages may have difficulty/silent defects in interpreting it. But it has at most 52 significant 
        bits, so a 64-bit integer or double-precision float type are safe for storing this identifier.
    :type id: :obj:`int`

    :param is_bot: True, if this user is a bot
    :type is_bot: :obj:`bool`

    :param first_name: User's or bot's first name
    :type first_name: :obj:`str`

    :param last_name: Optional. User's or bot's last name
    :type last_name: :obj:`str`

    :param username: Optional. User's or bot's username
    :type username: :obj:`str`

    :param language_code: Optional. IETF language tag of the user's language
    :type language_code: :obj:`str`

    :param is_premium: Optional. :obj:`bool`, if this user is a Telegram Premium user
    :type is_premium: :obj:`bool`

    :param added_to_attachment_menu: Optional. :obj:`bool`, if this user added the bot to the attachment menu
    :type added_to_attachment_menu: :obj:`bool`

    :param can_join_groups: Optional. True, if the bot can be invited to groups. Returned only in getMe.
    :type can_join_groups: :obj:`bool`

    :param can_read_all_group_messages: Optional. True, if privacy mode is disabled for the bot. Returned only in 
        getMe.
    :type can_read_all_group_messages: :obj:`bool`

    :param supports_inline_queries: Optional. True, if the bot supports inline queries. Returned only in getMe.
    :type supports_inline_queries: :obj:`bool`

    :param can_connect_to_business: Optional. True, if the bot can be connected to a Telegram Business account to receive its messages. Returned only in getMe.
    :type can_connect_to_business: :obj:`bool`

    :param has_main_web_app: Optional. True, if the bot has a main Web App. Returned only in getMe.
    :type has_main_web_app: :obj:`bool`

    :return: Instance of the class
    :rtype: :class:`telebot.types.User`
    """
    @classmethod
    def de_json(cls, json_string):
        if json_string is None: return None
        obj = cls.check_json(json_string, dict_copy=False)
        return cls(**obj)

    # noinspection PyShadowingBuiltins
    def __init__(self, id, is_bot, first_name, last_name=None, username=None, language_code=None,
                 can_join_groups=None, can_read_all_group_messages=None, supports_inline_queries=None, 
                 is_premium=None, added_to_attachment_menu=None, can_connect_to_business=None, 
                 has_main_web_app=None, **kwargs):
        self.id: int = id
        self.is_bot: bool = is_bot
        self.first_name: str = first_name
        self.username: Optional[str] = username
        self.last_name: Optional[str] = last_name
        self.language_code: Optional[str] = language_code
        self.can_join_groups: Optional[bool] = can_join_groups
        self.can_read_all_group_messages: Optional[bool] = can_read_all_group_messages
        self.supports_inline_queries: Optional[bool] = supports_inline_queries
        self.is_premium: Optional[bool] = is_premium
        self.added_to_attachment_menu: Optional[bool] = added_to_attachment_menu
        self.can_connect_to_business: Optional[bool] = can_connect_to_business
        self.has_main_web_app: Optional[bool] = has_main_web_app

    @property
    def full_name(self) -> str:
        """
        :return: User's full name
        """
        full_name = self.first_name
        if self.last_name:
            full_name += ' {0}'.format(self.last_name)
        return full_name

    def to_json(self):
        return json.dumps(self.to_dict())

    def to_dict(self):
        return {'id': self.id,
                'is_bot': self.is_bot,
                'first_name': self.first_name,
                'last_name': self.last_name,
                'username': self.username,
                'language_code': self.language_code,
                'can_join_groups': self.can_join_groups,
                'can_read_all_group_messages': self.can_read_all_group_messages,
                'supports_inline_queries': self.supports_inline_queries,
                'is_premium': self.is_premium,
                'added_to_attachment_menu': self.added_to_attachment_menu,
                'can_connect_to_business': self.can_connect_to_business,
                'has_main_web_app': self.has_main_web_app}


# noinspection PyShadowingBuiltins
class GroupChat(JsonDeserializable):
    """
    :meta private:
    """
    @classmethod
    def de_json(cls, json_string):
        if json_string is None: return None
        obj = cls.check_json(json_string, dict_copy=False)
        return cls(**obj)

    def __init__(self, id, title, **kwargs):
        self.id: int = id
        self.title: str = title


# noinspection PyShadowingBuiltins
class ChatFullInfo(JsonDeserializable):
    """
    This object represents a chat.

    Telegram Documentation: https://core.telegram.org/bots/api#chat

    :param id: Unique identifier for this chat. This number may have more than 32 significant bits and some programming 
        languages may have difficulty/silent defects in interpreting it. But it has at most 52 significant bits, so a signed 
        64-bit integer or double-precision float type are safe for storing this identifier.
    :type id: :obj:`int`

    :param type: Type of chat, can be either “private”, “group”, “supergroup” or “channel”
    :type type: :obj:`str`

    :param title: Optional. Title, for supergroups, channels and group chats
    :type title: :obj:`str`

    :param username: Optional. Username, for private chats, supergroups and channels if available
    :type username: :obj:`str`

    :param first_name: Optional. First name of the other party in a private chat
    :type first_name: :obj:`str`

    :param last_name: Optional. Last name of the other party in a private chat
    :type last_name: :obj:`str`

    :param is_forum: Optional. True, if the supergroup chat is a forum (has topics enabled)
    :type is_forum: :obj:`bool`

    :param max_reaction_count: Optional. The maximum number of reactions that can be set on a message in the chat
    :type max_reaction_count: :obj:`int`

    :param photo: Optional. Chat photo. Returned only in getChat.
    :type photo: :class:`telebot.types.ChatPhoto`

    :param active_usernames: Optional. If non-empty, the list of all active chat usernames; for private chats, supergroups and channels. Returned only in getChat.
    :type active_usernames: :obj:`list` of :obj:`str`

    :param birthdate: Optional. Birthdate of the other party in a private chat. Returned only in getChat.
    :type birthdate: :obj:`str`

    :param business_intro: Optional. Business intro for the chat. Returned only in getChat.
    :type business_intro: :class:`telebot.types.BusinessIntro`

    :param business_location: Optional. Business location for the chat. Returned only in getChat.
    :type business_location: :class:`telebot.types.BusinessLocation`

    :param business_opening_hours : Optional. Business opening hours for the chat. Returned only in getChat.
    :type business_opening_hours: :class:`telebot.types.BusinessHours`

    :param personal_chat: Optional. For private chats, the personal channel of the user. Returned only in getChat.
    :type personal_chat: :class:`telebot.types.Chat`

    :param available_reactions: Optional. List of available chat reactions; for private chats, supergroups and channels. Returned only in getChat.
    :type available_reactions: :obj:`list` of :class:`telebot.types.ReactionType`

    :param accent_color_id: Optional. Optional. Identifier of the accent color for the chat name and backgrounds of the chat photo,
        reply header, and link preview. See accent colors for more details. Returned only in getChat. Always returned in getChat.
    :type accent_color_id: :obj:`int`

    :param background_custom_emoji_id: Optional. Custom emoji identifier of emoji chosen by the chat for the reply header and link preview background. Returned only in getChat.
    :type background_custom_emoji_id: :obj:`str`

    :param profile_accent_color_id: Optional. Identifier of the accent color for the chat's profile background. See profile accent colors for more details. Returned only in getChat.
    :type profile_accent_color_id: :obj:`int`

    :param profile_background_custom_emoji_id: Optional. Custom emoji identifier of the emoji chosen by the chat for its profile background. Returned only in getChat.
    :type profile_background_custom_emoji_id: :obj:`str`

    :param emoji_status_custom_emoji_id: Optional. Custom emoji identifier of emoji status of the other party in a private chat. Returned only in getChat.
    :type emoji_status_custom_emoji_id: :obj:`str`

    :param emoji_status_expiration_date: Optional. Expiration date of the emoji status of the other party in a private chat, if any. Returned only in getChat.
    :type emoji_status_expiration_date: :obj:`int`

    :param bio: Optional. Bio of the other party in a private chat. Returned only in getChat.
    :type bio: :obj:`str`

    :param has_private_forwards: Optional. :obj:`bool`, if privacy settings of the other party in the private chat allows to use tg://user?id=<user_id> links only in chats with the user. Returned only in getChat.
    :type has_private_forwards: :obj:`bool`

    :param has_restricted_voice_and_video_messages: Optional. True, if the privacy settings of the other party restrict sending voice and video note messages in the private chat. Returned only in getChat.
    :type :obj:`bool`

    :param join_to_send_messages: Optional. :obj:`bool`, if users need to join the supergroup before they can send messages. Returned only in getChat.
    :type join_to_send_messages: :obj:`bool`

    :param join_by_request: Optional. :obj:`bool`, if all users directly joining the supergroup need to be approved by supergroup administrators. Returned only in getChat.
    :type join_by_request: :obj:`bool`

    :param description: Optional. Description, for groups, supergroups and channel chats. Returned only in getChat.
    :type description: :obj:`str`

    :param invite_link: Optional. Primary invite link, for groups, supergroups and channel chats. Returned only in getChat.
    :type invite_link: :obj:`str`

    :param pinned_message: Optional. The most recent pinned message (by sending date). Returned only in getChat.
    :type pinned_message: :class:`telebot.types.Message`

    :param permissions: Optional. Default chat member permissions, for groups and supergroups. Returned only in getChat.
    :type permissions: :class:`telebot.types.ChatPermissions`

    :param can_send_gift: deprecated, use accepted_gift_types instead.
    :type can_send_gift: :obj:`bool`

    :param accepted_gift_types: Information about types of gifts that are accepted by the chat or by the corresponding user for private chats
    :type accepted_gift_types: :class:`telebot.types.AcceptedGiftTypes`

    :param can_send_paid_media: Optional. True, if paid media messages can be sent or forwarded to the channel chat.
        The field is available only for channel chats.
    :type can_send_paid_media: :obj:`bool`

    :param slow_mode_delay: Optional. For supergroups, the minimum allowed delay between consecutive messages sent by each unpriviledged user; in seconds. Returned only in getChat.
    :type slow_mode_delay: :obj:`int`

    :param unrestrict_boost_count: Optional. For supergroups, the minimum number of boosts that a non-administrator user needs to add in order to ignore slow mode and chat permissions. Returned only in getChat.
    :type unrestrict_boost_count: :obj:`int`

    :param message_auto_delete_time: Optional. The time after which all messages sent to the chat will be automatically deleted; in seconds. Returned only in getChat.
    :type message_auto_delete_time: :obj:`int`

    :param has_aggressive_anti_spam_enabled: Optional. :obj:`bool`, if the chat has enabled aggressive anti-spam protection. Returned only in getChat.
    :type has_aggressive_anti_spam_enabled: :obj:`bool`

    :param has_hidden_members: Optional. :obj:`bool`, if the chat has enabled hidden members. Returned only in getChat.
    :type has_hidden_members: :obj:`bool`

    :param has_protected_content: Optional. :obj:`bool`, if messages from the chat can't be forwarded to other chats. Returned only in getChat.
    :type has_protected_content: :obj:`bool`

    :param has_visible_history: Optional. True, if new chat members will have access to old messages; available only to chat administrators. Returned only in getChat.
    :type has_visible_history: :obj:`bool`

    :param sticker_set_name: Optional. For supergroups, name of group sticker set. Returned only in getChat.
    :type sticker_set_name: :obj:`str`

    :param can_set_sticker_set: Optional. :obj:`bool`, if the bot can change the group sticker set. Returned only in getChat.
    :type can_set_sticker_set: :obj:`bool`

    :param custom_emoji_sticker_set_name: Optional. For supergroups, the name of the group's custom emoji sticker set.
        Custom emoji from this set can be used by all users and bots in the group. Returned only in getChat.
    :param custom_emoji_sticker_set_name: :obj:`str`

    :param linked_chat_id: Optional. Unique identifier for the linked chat, i.e. the discussion group identifier for 
        a channel and vice versa; for supergroups and channel chats. This identifier may be greater than 32 bits and some 
        programming languages may have difficulty/silent defects in interpreting it. But it is smaller than 52 bits, so a 
        signed 64 bit integer or double-precision float type are safe for storing this identifier. Returned only in getChat.
    :type linked_chat_id: :obj:`int`

    :param location: Optional. For supergroups, the location to which the supergroup is connected. Returned only in getChat.
    :type location: :class:`telebot.types.ChatLocation`

    :return: Instance of the class
    :rtype: :class:`telebot.types.ChatFullInfo`
    """
    @classmethod
    def de_json(cls, json_string):
        if json_string is None: return None
        obj = cls.check_json(json_string)
        if 'photo' in obj:
            obj['photo'] = ChatPhoto.de_json(obj['photo'])
        if 'pinned_message' in obj:
            obj['pinned_message'] = Message.de_json(obj['pinned_message'])
        if 'permissions' in obj:
            obj['permissions'] = ChatPermissions.de_json(obj['permissions'])
        if 'location' in obj:
            obj['location'] = ChatLocation.de_json(obj['location'])
        if 'available_reactions' in obj:
            obj['available_reactions'] = [ReactionType(reaction) for reaction in obj['available_reactions']]
        if 'business_intro' in obj:
            obj['business_intro'] = BusinessIntro.de_json(obj['business_intro'])
        if 'business_location' in obj:
            obj['business_location'] = BusinessLocation.de_json(obj['business_location'])
        if 'business_opening_hours' in obj:
            obj['business_opening_hours'] = BusinessOpeningHours.de_json(obj['business_opening_hours'])
        if 'personal_chat' in obj:
            obj['personal_chat'] = Chat.de_json(obj['personal_chat'])
        if 'birthdate' in obj:
            obj['birthdate'] = Birthdate.de_json(obj['birthdate'])
        if 'accepted_gift_types' in obj:
            obj['accepted_gift_types'] = AcceptedGiftTypes.de_json(obj['accepted_gift_types'])
        return cls(**obj)

    def __init__(self, id, type, title=None, username=None, first_name=None,
                 last_name=None, photo=None, bio=None, has_private_forwards=None,
                 description=None, invite_link=None, pinned_message=None, 
                 permissions=None, slow_mode_delay=None,
                 message_auto_delete_time=None, has_protected_content=None, sticker_set_name=None,
                 can_set_sticker_set=None, linked_chat_id=None, location=None, 
                 join_to_send_messages=None, join_by_request=None, has_restricted_voice_and_video_messages=None, 
                 is_forum=None, max_reaction_count=None, active_usernames=None, emoji_status_custom_emoji_id=None,
                 has_hidden_members=None, has_aggressive_anti_spam_enabled=None, emoji_status_expiration_date=None, 
                 available_reactions=None, accent_color_id=None, background_custom_emoji_id=None, profile_accent_color_id=None,
                 profile_background_custom_emoji_id=None, has_visible_history=None, 
                 unrestrict_boost_count=None, custom_emoji_sticker_set_name=None, business_intro=None, business_location=None,
                    business_opening_hours=None, personal_chat=None, birthdate=None, 
                    can_send_paid_media=None,
                    accepted_gift_types=None, **kwargs):
        self.id: int = id
        self.type: str = type
        self.title: Optional[str] = title
        self.username: Optional[str] = username
        self.first_name: Optional[str] = first_name
        self.last_name: Optional[str] = last_name
        self.is_forum: Optional[bool] = is_forum
        self.max_reaction_count: Optional[int] = max_reaction_count
        self.photo: Optional[ChatPhoto] = photo
        self.bio: Optional[str] = bio
        self.join_to_send_messages: Optional[bool] = join_to_send_messages
        self.join_by_request: Optional[bool] = join_by_request
        self.has_private_forwards: Optional[bool] = has_private_forwards
        self.has_restricted_voice_and_video_messages: Optional[bool] = has_restricted_voice_and_video_messages
        self.description: Optional[str] = description
        self.invite_link: Optional[str] = invite_link
        self.pinned_message: Optional[Message] = pinned_message
        self.permissions: Optional[ChatPermissions] = permissions
        self.slow_mode_delay: Optional[int] = slow_mode_delay
        self.message_auto_delete_time: Optional[int] = message_auto_delete_time
        self.has_protected_content: Optional[bool] = has_protected_content
        self.sticker_set_name: Optional[str] = sticker_set_name
        self.can_set_sticker_set: Optional[bool] = can_set_sticker_set
        self.linked_chat_id: Optional[int] = linked_chat_id
        self.location: Optional[ChatLocation] = location
        self.active_usernames: Optional[List[str]] = active_usernames
        self.emoji_status_custom_emoji_id: Optional[str] = emoji_status_custom_emoji_id
        self.has_hidden_members: Optional[bool] = has_hidden_members
        self.has_aggressive_anti_spam_enabled: Optional[bool] = has_aggressive_anti_spam_enabled
        self.emoji_status_expiration_date: Optional[int] = emoji_status_expiration_date
        self.available_reactions: Optional[List[ReactionType]] = available_reactions
        self.accent_color_id: Optional[int] = accent_color_id
        self.background_custom_emoji_id: Optional[str] = background_custom_emoji_id
        self.profile_accent_color_id: Optional[int] = profile_accent_color_id
        self.profile_background_custom_emoji_id: Optional[str] = profile_background_custom_emoji_id
        self.has_visible_history: Optional[bool] = has_visible_history
        self.unrestrict_boost_count: Optional[int] = unrestrict_boost_count
        self.custom_emoji_sticker_set_name: Optional[str] = custom_emoji_sticker_set_name
        self.business_intro: Optional[BusinessIntro] = business_intro
        self.business_location: Optional[BusinessLocation] = business_location
        self.business_opening_hours: Optional[BusinessOpeningHours] = business_opening_hours
        self.personal_chat: Optional[Chat] = personal_chat
        self.birthdate: Optional[Birthdate] = birthdate
        self.can_send_paid_media: Optional[bool] = can_send_paid_media
        self.accepted_gift_types: AcceptedGiftTypes = accepted_gift_types
    @property
    def can_send_gift(self) -> bool:
        """
        Deprecated. Use `accepted_gift_types` instead.

        :return: True if the chat can send gifts
        """
        log_deprecation_warning("The parameter 'can_send_gift' is deprecated. Use 'accepted_gift_types' instead.")
        if self.accepted_gift_types is not None: # just in case
            return any([self.accepted_gift_types.unique_gifts, self.accepted_gift_types.unlimited_gifts, self.accepted_gift_types.limited_gifts])
        return False


class Chat(ChatFullInfo):
    """
    In BotAPI 7.3 Chat was reduced and full info moved to ChatFullInfo:
    "Split out the class ChatFullInfo from the class Chat and changed the return type of the method getChat to ChatFullInfo."

    https://core.telegram.org/bots/api#chatfullinfo

    Currently Chat is left as full copy of ChatFullInfo for compatibility.
    """
    pass


class MessageID(JsonDeserializable):
    """
    This object represents a unique message identifier.

    Telegram Documentation: https://core.telegram.org/bots/api#messageid

    :param message_id: Unique message identifier
    :type message_id: :obj:`int`

    :return: Instance of the class
    :rtype: :class:`telebot.types.MessageId`
    """
    @classmethod
    def de_json(cls, json_string):
        if json_string is None: return None
        obj = cls.check_json(json_string, dict_copy=False)
        return cls(**obj)

    def __init__(self, message_id, **kwargs):
        self.message_id: int = message_id


class WebAppData(JsonDeserializable, Dictionaryable):
    """
    Describes data sent from a Web App to the bot.

    Telegram Documentation: https://core.telegram.org/bots/api#webappdata

    :param data: The data. Be aware that a bad client can send arbitrary data in this field.
    :type data: :obj:`str`

    :param button_text: Text of the web_app keyboard button from which the Web App was opened. Be aware that a bad client 
        can send arbitrary data in this field.
    :type button_text: :obj:`str`

    :return: Instance of the class
    :rtype: :class:`telebot.types.WebAppData`
    """

    @classmethod
    def de_json(cls, json_string):
        if json_string is None: return None
        obj = cls.check_json(json_string)
        return cls(**obj)

    def __init__(self, data, button_text, **kwargs):
        self.data: str = data
        self.button_text: str = button_text
    def to_dict(self):
        return {'data': self.data, 'button_text': self.button_text}


# noinspection PyUnresolvedReferences
class Message(JsonDeserializable):
    """
    This object represents a message.

    Telegram Documentation: https://core.telegram.org/bots/api#message

    :param message_id: Unique message identifier inside this chat
    :type message_id: :obj:`int`

    :param message_thread_id: Optional. Unique identifier of a message thread to which the message belongs; for supergroups only
    :type message_thread_id: :obj:`int`

    :param from_user: Optional. Sender of the message; empty for messages sent to channels. For backward compatibility, the
        field contains a fake sender user in non-channel chats, if the message was sent on behalf of a chat.
    :type from_user: :class:`telebot.types.User`

    :param sender_chat: Optional. Sender of the message, sent on behalf of a chat. For example, the channel itself for
        channel posts, the supergroup itself for messages from anonymous group administrators, the linked channel for
        messages automatically forwarded to the discussion group. For backward compatibility, the field from contains a
        fake sender user in non-channel chats, if the message was sent on behalf of a chat.
    :type sender_chat: :class:`telebot.types.Chat`

    :param sender_boost_count: Optional. If the sender of the message boosted the chat, the number of boosts added by the user
    :type sender_boost_count: :obj:`int`

    :param sender_business_bot info: Optional. Information about the business bot that sent the message
    :type sender_business_bot_info: :class:`telebot.types.User`

    :param date: Date the message was sent in Unix time
    :type date: :obj:`int`

    :param business_connection_id: Optional. Unique identifier of the business connection from which the message was received. If non-empty,
        the message belongs to a chat of the corresponding business account that is independent from any potential bot chat which might share the same identifier.
    :type business_connection_id: :obj:`str`

    :param chat: Conversation the message belongs to
    :type chat: :class:`telebot.types.Chat`

    :forward_origin: Optional. For forwarded messages, information about the original message;
    :type forward_origin: :class:`telebot.types.MessageOrigin`

    :param is_topic_message: Optional. True, if the message is sent to a forum topic
    :type is_topic_message: :obj:`bool`

    :param is_automatic_forward: Optional. :obj:`bool`, if the message is a channel post that was automatically
        forwarded to the connected discussion group
    :type is_automatic_forward: :obj:`bool`

    :param reply_to_message: Optional. For replies, the original message. Note that the Message object in this field
        will not contain further reply_to_message fields even if it itself is a reply.
    :type reply_to_message: :class:`telebot.types.Message`

    :param external_reply: Optional. Information about the message that is being replied to, which may come from another chat or forum topic
    :type external_reply: :class:`telebot.types.ExternalReplyInfo`

    :param quote: Optional. For replies that quote part of the original message, the quoted part of the message
    :type quote: :class:`telebot.types.TextQuote`

    :param reply_to_story: Optional. For replies to a story, the original story
    :type reply_to_story: :class:`telebot.types.Story`

    :param via_bot: Optional. Bot through which the message was sent
    :type via_bot: :class:`telebot.types.User`

    :param edit_date: Optional. Date the message was last edited in Unix time
    :type edit_date: :obj:`int`

    :param has_protected_content: Optional. :obj:`bool`, if the message can't be forwarded
    :type has_protected_content: :obj:`bool`

    :param is_from_offline: Optional. True, if the message was sent by an implicit action, for example,
        as an away or a greeting business message, or as a scheduled message
    :type is_from_offline: :obj:`bool`

    :param media_group_id: Optional. The unique identifier of a media message group this message belongs to
    :type media_group_id: :obj:`str`

    :param author_signature: Optional. Signature of the post author for messages in channels, or the custom title of an
        anonymous group administrator
    :type author_signature: :obj:`str`

    :param paid_star_count: Optional. The number of Telegram Stars that were paid by the sender of the message to send it
    :type paid_star_count: :obj:`int`

    :param text: Optional. For text messages, the actual UTF-8 text of the message
    :type text: :obj:`str`

    :param entities: Optional. For text messages, special entities like usernames, URLs, bot commands, etc. that
        appear in the text
    :type entities: :obj:`list` of :class:`telebot.types.MessageEntity`

    :param link_preview_options: Optional. Options used for link preview generation for the message,
        if it is a text message and link preview options were changed
    :type link_preview_options: :class:`telebot.types.LinkPreviewOptions`

    :param effect_id: Optional. Unique identifier of the message effect added to the message
    :type effect_id: :obj:`str`

    :param animation: Optional. Message is an animation, information about the animation. For backward
        compatibility, when this field is set, the document field will also be set
    :type animation: :class:`telebot.types.Animation`

    :param audio: Optional. Message is an audio file, information about the file
    :type audio: :class:`telebot.types.Audio`

    :param document: Optional. Message is a general file, information about the file
    :type document: :class:`telebot.types.Document`

    :param paid_media: Optional. Message contains paid media; information about the paid media
    :type paid_media: :class:`telebot.types.PaidMediaInfo`

    :param photo: Optional. Message is a photo, available sizes of the photo
    :type photo: :obj:`list` of :class:`telebot.types.PhotoSize`

    :param sticker: Optional. Message is a sticker, information about the sticker
    :type sticker: :class:`telebot.types.Sticker`

    :param story: Optional. Message is a forwarded story
    :type story: :class:`telebot.types.Story`

    :param video: Optional. Message is a video, information about the video
    :type video: :class:`telebot.types.Video`

    :param video_note: Optional. Message is a video note, information about the video message
    :type video_note: :class:`telebot.types.VideoNote`

    :param voice: Optional. Message is a voice message, information about the file
    :type voice: :class:`telebot.types.Voice`

    :param caption: Optional. Caption for the animation, audio, document, photo, video or voice
    :type caption: :obj:`str`

    :param caption_entities: Optional. For messages with a caption, special entities like usernames, URLs, bot
        commands, etc. that appear in the caption
    :type caption_entities: :obj:`list` of :class:`telebot.types.MessageEntity`

    :param show_caption_above_media: Optional. True, if the caption must be shown above the message media
    :type show_caption_above_media: :obj:`bool`

    :param has_media_spoiler: Optional. True, if the message media is covered by a spoiler animation
    :type has_media_spoiler: :obj:`bool`

    :param checklist: Optional. Message is a checklist
    :type checklist: :class:`telebot.types.Checklist`

    :param contact: Optional. Message is a shared contact, information about the contact
    :type contact: :class:`telebot.types.Contact`

    :param dice: Optional. Message is a dice with random value
    :type dice: :class:`telebot.types.Dice`

    :param game: Optional. Message is a game, information about the game. More about games »
    :type game: :class:`telebot.types.Game`

    :param poll: Optional. Message is a native poll, information about the poll
    :type poll: :class:`telebot.types.Poll`

    :param venue: Optional. Message is a venue, information about the venue. For backward compatibility, when this
        field is set, the location field will also be set
    :type venue: :class:`telebot.types.Venue`

    :param location: Optional. Message is a shared location, information about the location
    :type location: :class:`telebot.types.Location`

    :param new_chat_members: Optional. New members that were added to the group or supergroup and information about
        them (the bot itself may be one of these members)
    :type new_chat_members: :obj:`list` of :class:`telebot.types.User`

    :param left_chat_member: Optional. A member was removed from the group, information about them (this member may be
        the bot itself)
    :type left_chat_member: :class:`telebot.types.User`

    :param new_chat_title: Optional. A chat title was changed to this value
    :type new_chat_title: :obj:`str`

    :param new_chat_photo: Optional. A chat photo was change to this value
    :type new_chat_photo: :obj:`list` of :class:`telebot.types.PhotoSize`

    :param delete_chat_photo: Optional. Service message: the chat photo was deleted
    :type delete_chat_photo: :obj:`bool`

    :param group_chat_created: Optional. Service message: the group has been created
    :type group_chat_created: :obj:`bool`

    :param supergroup_chat_created: Optional. Service message: the supergroup has been created. This field can't be
        received in a message coming through updates, because bot can't be a member of a supergroup when it is created. It can
        only be found in reply_to_message if someone replies to a very first message in a directly created supergroup.
    :type supergroup_chat_created: :obj:`bool`

    :param channel_chat_created: Optional. Service message: the channel has been created. This field can't be
        received in a message coming through updates, because bot can't be a member of a channel when it is created. It can only
        be found in reply_to_message if someone replies to a very first message in a channel.
    :type channel_chat_created: :obj:`bool`

    :param message_auto_delete_timer_changed: Optional. Service message: auto-delete timer settings changed in
        the chat
    :type message_auto_delete_timer_changed: :class:`telebot.types.MessageAutoDeleteTimerChanged`

    :param migrate_to_chat_id: Optional. The group has been migrated to a supergroup with the specified identifier.
        This number may have more than 32 significant bits and some programming languages may have difficulty/silent
        defects in interpreting it. But it has at most 52 significant bits, so a signed 64-bit integer or double-precision
        float type are safe for storing this identifier.
    :type migrate_to_chat_id: :obj:`int`

    :param migrate_from_chat_id: Optional. The supergroup has been migrated from a group with the specified
        identifier. This number may have more than 32 significant bits and some programming languages may have
        difficulty/silent defects in interpreting it. But it has at most 52 significant bits, so a signed 64-bit integer or
        double-precision float type are safe for storing this identifier.
    :type migrate_from_chat_id: :obj:`int`

    :param pinned_message: Optional. Specified message was pinned. Note that the Message object in this field will not
        contain further reply_to_message fields even if it is itself a reply.
    :type pinned_message: :class:`telebot.types.Message` or :class:`telebot.types.InaccessibleMessage`

    :param invoice: Optional. Message is an invoice for a payment, information about the invoice. More about payments »
    :type invoice: :class:`telebot.types.Invoice`

    :param successful_payment: Optional. Message is a service message about a successful payment, information about
        the payment. More about payments »
    :type successful_payment: :class:`telebot.types.SuccessfulPayment`

    :param refunded_payment: Optional. Message is a service message about a refunded payment, information about the payment. More about payments »
    :type refunded_payment: :class:`telebot.types.RefundedPayment`

    :param users_shared: Optional. Service message: a user was shared with the bot
    :type users_shared: :class:`telebot.types.UsersShared`

    :param chat_shared: Optional. Service message: a chat was shared with the bot
    :type chat_shared: :class:`telebot.types.ChatShared`

    :param gift: Optional. Service message: a regular gift was sent or received
    :type gift: :class:`telebot.types.GiftInfo`

    :param unique_gift: Optional. Service message: a unique gift was sent or received
    :type unique_gift: :class:`telebot.types.UniqueGiftInfo`

    :param connected_website: Optional. The domain name of the website on which the user has logged in. More about
        Telegram Login »
    :type connected_website: :obj:`str`

    :param write_access_allowed: Optional. Service message: the user allowed the bot added to the attachment
        menu to write messages
    :type write_access_allowed: :class:`telebot.types.WriteAccessAllowed`

    :param passport_data: Optional. Telegram Passport data
    :type passport_data: :class:`telebot.types.PassportData`

    :param proximity_alert_triggered: Optional. Service message. A user in the chat triggered another user's
        proximity alert while sharing Live Location.
    :type proximity_alert_triggered: :class:`telebot.types.ProximityAlertTriggered`

    :param boost_added: Optional. Service message: user boosted the chat
    :type boost_added: :class:`telebot.types.ChatBoostAdded`

    :param chat_background_set: Optional. Service message: chat background set
    :type chat_background_set: :class:`telebot.types.ChatBackground`

    :param checklist_tasks_done: Optional. Service message: some tasks in a checklist were marked as done or not done
    :type checklist_tasks_done: :class:`telebot.types.ChecklistTasksDone`

    :param checklist_tasks_added: Optional. Service message: tasks were added to a checklist
    :type checklist_tasks_added: :class:`telebot.types.ChecklistTasksAdded`

    :param direct_message_price_changed: Optional. Service message: the price for paid messages in the corresponding direct messages chat of a channel has changed
    :type direct_message_price_changed: :class:`telebot.types.DirectMessagePriceChanged`

    :param forum_topic_created: Optional. Service message: forum topic created
    :type forum_topic_created: :class:`telebot.types.ForumTopicCreated`

    :param forum_topic_edited: Optional. Service message: forum topic edited
    :type forum_topic_edited: :class:`telebot.types.ForumTopicEdited`

    :param forum_topic_closed: Optional. Service message: forum topic closed
    :type forum_topic_closed: :class:`telebot.types.ForumTopicClosed`

    :param forum_topic_reopened: Optional. Service message: forum topic reopened
    :type forum_topic_reopened: :class:`telebot.types.ForumTopicReopened`

    :param general_forum_topic_hidden: Optional. Service message: the 'General' forum topic hidden
    :type general_forum_topic_hidden: :class:`telebot.types.GeneralForumTopicHidden`

    :param general_forum_topic_unhidden: Optional. Service message: the 'General' forum topic unhidden
    :type general_forum_topic_unhidden: :class:`telebot.types.GeneralForumTopicUnhidden`

    :param giveaway_created: Optional. Service message: a giveaway has been created
    :type giveaway_created: :class:`telebot.types.GiveawayCreated`

    :param giveaway: Optional. The message is a scheduled giveaway message
    :type giveaway: :class:`telebot.types.Giveaway`

    :param giveaway_winners: Optional. Service message: giveaway winners(public winners)
    :type giveaway_winners: :class:`telebot.types.GiveawayWinners`

    :param giveaway_completed: Optional. Service message: giveaway completed, without public winners
    :type giveaway_completed: :class:`telebot.types.GiveawayCompleted`

    :param paid_message_price_changed: Optional. Service message: the price for paid messages has changed in the chat
    :type paid_message_price_changed: :class:`telebot.types.PaidMessagePriceChanged`

    :param video_chat_scheduled: Optional. Service message: video chat scheduled
    :type video_chat_scheduled: :class:`telebot.types.VideoChatScheduled`

    :param video_chat_started: Optional. Service message: video chat started
    :type video_chat_started: :class:`telebot.types.VideoChatStarted`

    :param video_chat_ended: Optional. Service message: video chat ended
    :type video_chat_ended: :class:`telebot.types.VideoChatEnded`

    :param video_chat_participants_invited: Optional. Service message: new participants invited to a video chat
    :type video_chat_participants_invited: :class:`telebot.types.VideoChatParticipantsInvited`

    :param web_app_data: Optional. Service message: data sent by a Web App
    :type web_app_data: :class:`telebot.types.WebAppData`

    :param reply_markup: Optional. Inline keyboard attached to the message. login_url buttons are represented as ordinary url buttons.
    :type reply_markup: :class:`telebot.types.InlineKeyboardMarkup`

    :return: Instance of the class
    :rtype: :class:`telebot.types.Message`
    """
    @classmethod
    def de_json(cls, json_string):
        if json_string is None: return None
        obj = cls.check_json(json_string, dict_copy=False)
        message_id = obj['message_id']
        from_user = User.de_json(obj.get('from'))
        date = obj['date']
        chat = Chat.de_json(obj['chat'])
        content_type = None
        opts = {}
        if 'sender_chat' in obj:
            opts['sender_chat'] = Chat.de_json(obj['sender_chat'])
        if 'is_automatic_forward' in obj:
            opts['is_automatic_forward'] = obj.get('is_automatic_forward')
        if 'is_topic_message' in obj:
            opts['is_topic_message'] = obj.get('is_topic_message')
        if 'message_thread_id' in obj:
            opts['message_thread_id'] = obj.get('message_thread_id')
        if 'reply_to_message' in obj:
            opts['reply_to_message'] = Message.de_json(obj['reply_to_message'])
        if 'via_bot' in obj:
            opts['via_bot'] = User.de_json(obj['via_bot'])
        if 'edit_date' in obj:
            opts['edit_date'] = obj.get('edit_date')
        if 'has_protected_content' in obj:
            opts['has_protected_content'] = obj.get('has_protected_content')
        if 'media_group_id' in obj:
            opts['media_group_id'] = obj.get('media_group_id')
        if 'author_signature' in obj:
            opts['author_signature'] = obj.get('author_signature')
        if 'text' in obj:
            opts['text'] = obj['text']
            content_type = 'text'
        if 'entities' in obj:
            opts['entities'] = Message.parse_entities(obj['entities'])
        if 'caption_entities' in obj:
            opts['caption_entities'] = Message.parse_entities(obj['caption_entities'])
        if 'audio' in obj:
            opts['audio'] = Audio.de_json(obj['audio'])
            content_type = 'audio'
        if 'document' in obj:
            opts['document'] = Document.de_json(obj['document'])
            content_type = 'document'
        if 'animation' in obj:
            # Document content type accompanies "animation", so "animation" should be checked after "document" to override it
            opts['animation'] = Animation.de_json(obj['animation'])
            content_type = 'animation'
        if 'game' in obj:
            opts['game'] = Game.de_json(obj['game'])
            content_type = 'game'
        if 'photo' in obj:
            opts['photo'] = Message.parse_photo(obj['photo'])
            content_type = 'photo'
        if 'sticker' in obj:
            opts['sticker'] = Sticker.de_json(obj['sticker'])
            content_type = 'sticker'
        if 'video' in obj:
            opts['video'] = Video.de_json(obj['video'])
            content_type = 'video'
        if 'video_note' in obj:
            opts['video_note'] = VideoNote.de_json(obj['video_note'])
            content_type = 'video_note'
        if 'voice' in obj:
            opts['voice'] = Audio.de_json(obj['voice'])
            content_type = 'voice'
        if 'caption' in obj:
            opts['caption'] = obj['caption']
        if 'contact' in obj:
            opts['contact'] = Contact.de_json(obj['contact'])
            content_type = 'contact'
        if 'location' in obj:
            opts['location'] = Location.de_json(obj['location'])
            content_type = 'location'
        if 'venue' in obj:
            opts['venue'] = Venue.de_json(obj['venue'])
            content_type = 'venue'
        if 'dice' in obj:
            opts['dice'] = Dice.de_json(obj['dice'])
            content_type = 'dice'
        if 'new_chat_members' in obj:
            new_chat_members = []
            for member in obj['new_chat_members']:
                new_chat_members.append(User.de_json(member))
            opts['new_chat_members'] = new_chat_members
            content_type = 'new_chat_members'
        if 'left_chat_member' in obj:
            opts['left_chat_member'] = User.de_json(obj['left_chat_member'])
            content_type = 'left_chat_member'
        if 'new_chat_title' in obj:
            opts['new_chat_title'] = obj['new_chat_title']
            content_type = 'new_chat_title'
        if 'new_chat_photo' in obj:
            opts['new_chat_photo'] = Message.parse_photo(obj['new_chat_photo'])
            content_type = 'new_chat_photo'
        if 'delete_chat_photo' in obj:
            opts['delete_chat_photo'] = obj['delete_chat_photo']
            content_type = 'delete_chat_photo'
        if 'group_chat_created' in obj:
            opts['group_chat_created'] = obj['group_chat_created']
            content_type = 'group_chat_created'
        if 'supergroup_chat_created' in obj:
            opts['supergroup_chat_created'] = obj['supergroup_chat_created']
            content_type = 'supergroup_chat_created'
        if 'channel_chat_created' in obj:
            opts['channel_chat_created'] = obj['channel_chat_created']
            content_type = 'channel_chat_created'
        if 'migrate_to_chat_id' in obj:
            opts['migrate_to_chat_id'] = obj['migrate_to_chat_id']
            content_type = 'migrate_to_chat_id'
        if 'migrate_from_chat_id' in obj:
            opts['migrate_from_chat_id'] = obj['migrate_from_chat_id']
            content_type = 'migrate_from_chat_id'
        if 'pinned_message' in obj:
            pinned_message = obj['pinned_message']
            if pinned_message['date'] == 0:
                # date.	Always 0. The field can be used to differentiate regular and inaccessible messages.
                opts['pinned_message'] = InaccessibleMessage.de_json(pinned_message)
            else:
                opts['pinned_message'] = Message.de_json(pinned_message)
            content_type = 'pinned_message'
        if 'invoice' in obj:
            opts['invoice'] = Invoice.de_json(obj['invoice'])
            content_type = 'invoice'
        if 'successful_payment' in obj:
            opts['successful_payment'] = SuccessfulPayment.de_json(obj['successful_payment'])
            content_type = 'successful_payment'
        if 'connected_website' in obj:
            opts['connected_website'] = obj['connected_website']
            content_type = 'connected_website'
        if 'poll' in obj:
            opts['poll'] = Poll.de_json(obj['poll'])
            content_type = 'poll'
        if 'passport_data' in obj:
            opts['passport_data'] = obj['passport_data']
            content_type = 'passport_data'
        if 'proximity_alert_triggered' in obj:
            opts['proximity_alert_triggered'] = ProximityAlertTriggered.de_json(obj[
                'proximity_alert_triggered'])
            content_type = 'proximity_alert_triggered'
        if 'video_chat_scheduled' in obj:
            opts['video_chat_scheduled'] = VideoChatScheduled.de_json(obj['video_chat_scheduled'])
            content_type = 'video_chat_scheduled'
        if 'video_chat_started' in obj:
            opts['video_chat_started'] = VideoChatStarted.de_json(obj['video_chat_started'])
            content_type = 'video_chat_started'
        if 'video_chat_ended' in obj:
            opts['video_chat_ended'] = VideoChatEnded.de_json(obj['video_chat_ended'])
            content_type = 'video_chat_ended'
        if 'video_chat_participants_invited' in obj:
            opts['video_chat_participants_invited'] = VideoChatParticipantsInvited.de_json(obj['video_chat_participants_invited'])
            content_type = 'video_chat_participants_invited'
        if 'web_app_data' in obj:
            opts['web_app_data'] = WebAppData.de_json(obj['web_app_data'])
            content_type = 'web_app_data'
        if 'message_auto_delete_timer_changed' in obj:
            opts['message_auto_delete_timer_changed'] = MessageAutoDeleteTimerChanged.de_json(obj['message_auto_delete_timer_changed'])
            content_type = 'message_auto_delete_timer_changed'
        if 'reply_markup' in obj:
            opts['reply_markup'] = InlineKeyboardMarkup.de_json(obj['reply_markup'])
        if 'chat_background_set' in obj:
            opts['chat_background_set'] = ChatBackground.de_json(obj['chat_background_set'])
            content_type = 'chat_background_set'
        if 'forum_topic_created' in obj:
            opts['forum_topic_created'] = ForumTopicCreated.de_json(obj['forum_topic_created'])
            content_type = 'forum_topic_created'
        if 'forum_topic_closed' in obj:
            opts['forum_topic_closed'] = ForumTopicClosed.de_json(obj['forum_topic_closed'])
            content_type = 'forum_topic_closed'
        if 'forum_topic_reopened' in obj:
            opts['forum_topic_reopened'] = ForumTopicReopened.de_json(obj['forum_topic_reopened'])
            content_type = 'forum_topic_reopened'
        if 'has_media_spoiler' in obj:
            opts['has_media_spoiler'] = obj['has_media_spoiler']
        if 'forum_topic_edited' in obj:
            opts['forum_topic_edited'] = ForumTopicEdited.de_json(obj['forum_topic_edited'])
            content_type = 'forum_topic_edited'
        if 'general_forum_topic_hidden' in obj:
            opts['general_forum_topic_hidden'] = GeneralForumTopicHidden.de_json(obj['general_forum_topic_hidden'])
            content_type = 'general_forum_topic_hidden'
        if 'general_forum_topic_unhidden' in obj:
            opts['general_forum_topic_unhidden'] = GeneralForumTopicUnhidden.de_json(obj['general_forum_topic_unhidden'])
            content_type = 'general_forum_topic_unhidden'
        if 'write_access_allowed' in obj:
            opts['write_access_allowed'] = WriteAccessAllowed.de_json(obj['write_access_allowed'])
            content_type = 'write_access_allowed'
        if 'users_shared' in obj:
            opts['users_shared'] = UsersShared.de_json(obj['users_shared'])
            content_type = 'users_shared' # COMPATIBILITY BROKEN!
        if 'chat_shared' in obj:
            opts['chat_shared'] = ChatShared.de_json(obj['chat_shared'])
            content_type = 'chat_shared'
        if 'story' in obj:
            opts['story'] = Story.de_json(obj['story'])
            content_type = 'story'
        if 'external_reply' in obj:
            opts['external_reply'] = ExternalReplyInfo.de_json(obj['external_reply'])
        if 'quote' in obj:
            opts['quote'] = TextQuote.de_json(obj['quote'])
        if 'link_preview_options' in obj:
            opts['link_preview_options'] = LinkPreviewOptions.de_json(obj['link_preview_options'])
        if 'giveaway_created' in obj:
            opts['giveaway_created'] = GiveawayCreated.de_json(obj['giveaway_created'])
            content_type = 'giveaway_created'
        if 'giveaway' in obj:
            opts['giveaway'] = Giveaway.de_json(obj['giveaway'])
            content_type = 'giveaway'
        if 'giveaway_winners' in obj:
            opts['giveaway_winners'] = GiveawayWinners.de_json(obj['giveaway_winners'])
            content_type = 'giveaway_winners'
        if 'giveaway_completed' in obj:
            opts['giveaway_completed'] = GiveawayCompleted.de_json(obj['giveaway_completed'])
            content_type = 'giveaway_completed'
        if 'forward_origin' in obj:
            opts['forward_origin'] = MessageOrigin.de_json(obj['forward_origin'])
        if 'boost_added' in obj:
            opts['boost_added'] = ChatBoostAdded.de_json(obj['boost_added'])
            content_type = 'boost_added'
        if 'sender_boost_count' in obj:
            opts['sender_boost_count'] = obj['sender_boost_count']
        if 'reply_to_story' in obj:
            opts['reply_to_story'] = Story.de_json(obj['reply_to_story'])
        if 'sender_business_bot' in obj:
            opts['sender_business_bot'] = User.de_json(obj['sender_business_bot'])
        if 'business_connection_id' in obj:
            opts['business_connection_id'] = obj['business_connection_id']
        if 'is_from_offline' in obj:
            opts['is_from_offline'] = obj['is_from_offline']
        if 'effect_id' in obj:
            opts['effect_id'] = obj['effect_id']
        if 'show_caption_above_media' in obj:
            opts['show_caption_above_media'] = obj['show_caption_above_media']
        if 'paid_media' in obj:
            opts['paid_media'] = PaidMediaInfo.de_json(obj['paid_media'])
        if 'refunded_payment' in obj:
            opts['refunded_payment'] = RefundedPayment.de_json(obj['refunded_payment'])
        if 'gift' in obj:
            opts['gift'] = GiftInfo.de_json(obj['gift'])
            content_type = 'gift'
        if 'unique_gift' in obj:
            opts['unique_gift'] = UniqueGiftInfo.de_json(obj['unique_gift'])
            content_type = 'unique_gift'
        if 'paid_message_price_changed' in obj:
            opts['paid_message_price_changed'] = PaidMessagePriceChanged.de_json(obj['paid_message_price_changed'])
            content_type = 'paid_message_price_changed'
        if 'paid_star_count' in obj:
            opts['paid_star_count'] = obj['paid_star_count']
        if 'checklist' in obj:
            opts['checklist'] = Checklist.de_json(obj['checklist'])
        if 'checklist_tasks_done' in obj:
            opts['checklist_tasks_done'] = ChecklistTasksDone.de_json(obj['checklist_tasks_done'])
            content_type = 'checklist_tasks_done'
        if 'checklist_tasks_added' in obj:
            opts['checklist_tasks_added'] = ChecklistTasksAdded.de_json(obj['checklist_tasks_added'])
            content_type = 'checklist_tasks_added'
        if 'direct_message_price_changed' in obj:
            opts['direct_message_price_changed'] = DirectMessagePriceChanged.de_json(obj['direct_message_price_changed'])
            content_type = 'direct_message_price_changed'
            
        return cls(message_id, from_user, date, chat, content_type, opts, json_string)

    @classmethod
    def parse_chat(cls, chat) -> Union[User, GroupChat]:
        """
        Parses chat.
        """
        if 'first_name' not in chat:
            return GroupChat.de_json(chat)
        else:
            return User.de_json(chat)

    @classmethod
    def parse_photo(cls, photo_size_array) -> List[PhotoSize]:
        """
        Parses photo array.
        """
        ret = []
        for ps in photo_size_array:
            ret.append(PhotoSize.de_json(ps))
        return ret

    @classmethod
    def parse_entities(cls, message_entity_array) -> List[MessageEntity]:
        """
        Parses message entity array.
        """
        ret = []
        for me in message_entity_array:
            ret.append(MessageEntity.de_json(me))
        return ret

    def __init__(self, message_id, from_user, date, chat, content_type, options, json_string):
        self.content_type: str = content_type
        self.id: int = message_id           # Lets fix the telegram usability ####up with ID in Message :)
        self.message_id: int = message_id
        self.from_user: Optional[User] = from_user
        self.date: int = date
        self.chat: Chat = chat
        self.sender_chat: Optional[Chat] = None
        self.is_automatic_forward: Optional[bool] = None
        self.reply_to_message: Optional[Message] = None
        self.via_bot: Optional[User] = None
        self.edit_date: Optional[int] = None
        self.has_protected_content: Optional[bool] = None
        self.media_group_id: Optional[str] = None
        self.author_signature: Optional[str] = None
        self.text: Optional[str] = None
        self.entities: Optional[List[MessageEntity]] = None
        self.caption_entities: Optional[List[MessageEntity]] = None
        self.audio: Optional[Audio] = None
        self.document: Optional[Document] = None
        self.photo: Optional[List[PhotoSize]] = None
        self.sticker: Optional[Sticker] = None
        self.video: Optional[Video] = None
        self.video_note: Optional[VideoNote] = None
        self.voice: Optional[Voice] = None
        self.caption: Optional[str] = None
        self.contact: Optional[Contact] = None
        self.location: Optional[Location] = None
        self.venue: Optional[Venue] = None
        self.animation: Optional[Animation] = None
        self.dice: Optional[Dice] = None
        self.new_chat_members: Optional[List[User]] = None
        self.left_chat_member: Optional[User] = None
        self.new_chat_title: Optional[str] = None
        self.new_chat_photo: Optional[List[PhotoSize]] = None
        self.delete_chat_photo: Optional[bool] = None
        self.group_chat_created: Optional[bool] = None
        self.supergroup_chat_created: Optional[bool] = None
        self.channel_chat_created: Optional[bool] = None
        self.migrate_to_chat_id: Optional[int] = None
        self.migrate_from_chat_id: Optional[int] = None
        self.pinned_message: Optional[Union[Message, InaccessibleMessage]] = None
        self.invoice: Optional[Invoice] = None
        self.successful_payment: Optional[SuccessfulPayment] = None
        self.connected_website: Optional[str] = None
        self.reply_markup: Optional[InlineKeyboardMarkup] = None
        self.message_thread_id: Optional[int] = None
        self.is_topic_message: Optional[bool] = None
        self.chat_background_set: Optional[ChatBackground] = None
        self.forum_topic_created: Optional[ForumTopicCreated] = None
        self.forum_topic_closed: Optional[ForumTopicClosed] = None
        self.forum_topic_reopened: Optional[ForumTopicReopened] = None
        self.has_media_spoiler: Optional[bool] = None
        self.forum_topic_edited: Optional[ForumTopicEdited] = None
        self.general_forum_topic_hidden: Optional[GeneralForumTopicHidden] = None
        self.general_forum_topic_unhidden: Optional[GeneralForumTopicUnhidden] = None
        self.write_access_allowed: Optional[WriteAccessAllowed] = None
        self.users_shared: Optional[UsersShared] = None
        self.chat_shared: Optional[ChatShared] = None
        self.story: Optional[Story] = None
        self.external_reply: Optional[ExternalReplyInfo] = None
        self.quote: Optional[TextQuote] = None
        self.link_preview_options: Optional[LinkPreviewOptions] = None
        self.giveaway_created: Optional[GiveawayCreated] = None
        self.giveaway: Optional[Giveaway] = None
        self.giveaway_winners: Optional[GiveawayWinners] = None
        self.giveaway_completed: Optional[GiveawayCompleted] = None
        self.forward_origin: Optional[MessageOrigin] = None
        self.boost_added: Optional[ChatBoostAdded] = None
        self.sender_boost_count: Optional[int] = None
        self.reply_to_story: Optional[Story] = None
        self.sender_business_bot: Optional[User] = None
        self.business_connection_id: Optional[str] = None
        self.is_from_offline: Optional[bool] = None
        self.effect_id: Optional[str] = None
        self.show_caption_above_media: Optional[bool] = None
        self.paid_media : Optional[PaidMediaInfo] = None
        self.refunded_payment : Optional[RefundedPayment] = None
        self.proximity_alert_triggered: Optional[ProximityAlertTriggered] = None
        self.video_chat_scheduled: Optional[VideoChatScheduled] = None
        self.video_chat_started: Optional[VideoChatStarted] = None
        self.video_chat_ended: Optional[VideoChatEnded] = None
        self.video_chat_participants_invited: Optional[VideoChatParticipantsInvited] = None
        self.web_app_data: Optional[WebAppData] = None
        self.message_auto_delete_timer_changed: Optional[MessageAutoDeleteTimerChanged] = None
        self.gift : Optional[GiftInfo] = None
        self.unique_gift : Optional[UniqueGiftInfo] = None
        self.paid_message_price_changed: Optional[PaidMessagePriceChanged] = None
        self.paid_star_count: Optional[int] = None
        self.checklist: Optional[Checklist] = None
        self.checklist_tasks_done: Optional[ChecklistTasksDone] = None
        self.checklist_tasks_added: Optional[List[ChecklistTasksAdded]] = None
        self.direct_message_price_changed: Optional[DirectMessagePriceChanged] = None

        for key in options:
            setattr(self, key, options[key])
        self.json = json_string

    @property
    def html_text(self) -> Optional[str]:
        """
        Returns html-rendered text.
        """
        if self.text is None:
            return None
        return apply_html_entities(self.text, self.entities, getattr(self, "custom_subs", None))

    @property
    def html_caption(self) -> Optional[str]:
        """
        Returns html-rendered caption.
        """
        if self.caption is None:
            return None
        return apply_html_entities(self.caption, self.caption_entities, getattr(self, "custom_subs", None))

    @property
    def voice_chat_scheduled(self):
        log_deprecation_warning('The parameter "voice_chat_scheduled" is deprecated, use "video_chat_scheduled" instead')
        return self.video_chat_scheduled

    @property
    def voice_chat_started(self):
        log_deprecation_warning('The parameter "voice_chat_started" is deprecated, use "video_chat_started" instead')
        return self.video_chat_started

    @property
    def voice_chat_ended(self):
        log_deprecation_warning('The parameter "voice_chat_ended" is deprecated, use "video_chat_ended" instead')
        return self.video_chat_ended

    @property
    def voice_chat_participants_invited(self):
        log_deprecation_warning('The parameter "voice_chat_participants_invited" is deprecated, use "video_chat_participants_invited" instead')
        return self.video_chat_participants_invited

    @property
    def new_chat_member(self):
        log_deprecation_warning('The parameter "new_chat_member" is deprecated, use "new_chat_members" instead')
        return None

    @property
    def forward_from(self):
        log_deprecation_warning('The parameter "forward_from" is deprecated, use "forward_origin" instead')
        if self.forward_origin and isinstance(self.forward_origin, MessageOriginUser):
            return self.forward_origin.sender_user
        return None

    @property
    def forward_from_chat(self):
        log_deprecation_warning('The parameter "forward_from_chat" is deprecated, use "forward_origin" instead')
        if self.forward_origin and isinstance(self.forward_origin, MessageOriginChat):
            return self.forward_origin.sender_chat
        elif self.forward_origin and isinstance(self.forward_origin, MessageOriginChannel):
            return self.forward_origin.chat
        return None

    @property
    def forward_from_message_id(self):
        log_deprecation_warning('The parameter "forward_from_message_id" is deprecated, use "forward_origin" instead')
        if self.forward_origin and isinstance(self.forward_origin, MessageOriginChannel):
            return self.forward_origin.message_id
        return None

    @property
    def forward_signature(self):
        log_deprecation_warning('The parameter "forward_signature" is deprecated, use "forward_origin" instead')
        if self.forward_origin and isinstance(self.forward_origin, MessageOriginChat):
            return self.forward_origin.author_signature
        elif self.forward_origin and isinstance(self.forward_origin, MessageOriginChannel):
            return self.forward_origin.author_signature
        return None

    @property
    def forward_sender_name(self):
        log_deprecation_warning('The parameter "forward_sender_name" is deprecated, use "forward_origin" instead')
        if self.forward_origin and isinstance(self.forward_origin, MessageOriginHiddenUser):
            return self.forward_origin.sender_user_name
        return None

    @property
    def forward_date(self):
        log_deprecation_warning('The parameter "forward_date" is deprecated, use "forward_origin" instead')
        if self.forward_origin:
            return self.forward_origin.date
        return None

    @property
    def user_shared(self):
        log_deprecation_warning('The parameter "user_shared" is deprecated, use "users_shared" instead')
        return self.users_shared

    @property
    def any_text(self) -> Optional[str]:
        return self.caption if (self.caption is not None) else self.text

    @property
    def any_entities(self) -> Optional[List[MessageEntity]]:
        return self.caption_entities if (self.caption_entities is not None) else self.entities


# noinspection PyShadowingBuiltins
class MessageEntity(Dictionaryable, JsonSerializable, JsonDeserializable):
    """
    This object represents one special entity in a text message. For example, hashtags, usernames, URLs, etc.

    Telegram Documentation: https://core.telegram.org/bots/api#messageentity

    :param type: Type of the entity. Currently, can be “mention” (@username), “hashtag” (#hashtag or #hashtag@chatusername), “cashtag” ($USD or $USD@chatusername),
        “bot_command” (/start@jobs_bot), “url” (https://telegram.org), “email” (do-not-reply@telegram.org), “phone_number” (+1-212-555-0123), “bold” (bold text),
        “italic” (italic text), “underline” (underlined text), “strikethrough” (strikethrough text), “spoiler” (spoiler message), “blockquote” (block quotation),
        “expandable_blockquote” (collapsed-by-default block quotation), “code” (monowidth string), “pre” (monowidth block), “text_link” (for clickable text URLs),
        “text_mention” (for users without usernames), “custom_emoji” (for inline custom emoji stickers)
    :type type: :obj:`str`

    :param offset: Offset in UTF-16 code units to the start of the entity
    :type offset: :obj:`int`

    :param length: Length of the entity in UTF-16 code units
    :type length: :obj:`int`

    :param url: Optional. For “text_link” only, URL that will be opened after user taps on the text
    :type url: :obj:`str`

    :param user: Optional. For “text_mention” only, the mentioned user
    :type user: :class:`telebot.types.User`

    :param language: Optional. For “pre” only, the programming language of the entity text
    :type language: :obj:`str`

    :param custom_emoji_id: Optional. For “custom_emoji” only, unique identifier of the custom emoji.
        Use get_custom_emoji_stickers to get full information about the sticker.
    :type custom_emoji_id: :obj:`str`

    :return: Instance of the class
    :rtype: :class:`telebot.types.MessageEntity`
    """
    @staticmethod
    def to_list_of_dicts(entity_list) -> Union[List[Dict], None]:
        """
        Converts a list of MessageEntity objects to a list of dictionaries.
        """
        if entity_list is None or len(entity_list) == 0:
            return None
        elif isinstance(entity_list[0], MessageEntity):
            return [MessageEntity.to_dict(e) for e in entity_list]
        else:
            return entity_list

    @classmethod
    def de_json(cls, json_string):
        if json_string is None: return None
        obj = cls.check_json(json_string)
        if 'user' in obj:
            obj['user'] = User.de_json(obj['user'])
        return cls(**obj)

    def __init__(self, type, offset, length, url=None, user=None, language=None, custom_emoji_id=None, **kwargs):
        self.type: str = type
        self.offset: int = offset
        self.length: int = length
        self.url: str = url
        self.user: User = user
        self.language: str = language
        self.custom_emoji_id: Optional[str] = custom_emoji_id

    def to_json(self):
        return json.dumps(self.to_dict())

    def to_dict(self):
        return {"type": self.type,
                "offset": self.offset,
                "length": self.length,
                "url": self.url,
                "user": self.user.to_dict() if self.user else None,
                "language": self.language,
                "custom_emoji_id": self.custom_emoji_id}


class Dice(JsonSerializable, Dictionaryable, JsonDeserializable):
    """
    This object represents an animated emoji that displays a random value.

    Telegram Documentation: https://core.telegram.org/bots/api#dice

    :param emoji: Emoji on which the dice throw animation is based
    :type emoji: :obj:`str`

    :param value: Value of the dice, 1-6 for “🎲”, “🎯” and “🎳” base emoji, 1-5 for “🏀” and “⚽” base emoji, 1-64 for “🎰” base emoji
    :type value: :obj:`int`

    :return: Instance of the class
    :rtype: :class:`telebot.types.Dice`
    """
    @classmethod
    def de_json(cls, json_string):
        if json_string is None: return None
        obj = cls.check_json(json_string, dict_copy=False)
        return cls(**obj)

    def __init__(self, value, emoji, **kwargs):
        self.value: int = value
        self.emoji: str = emoji

    def to_json(self):
        return json.dumps(self.to_dict())

    def to_dict(self):
        return {'value': self.value,
                'emoji': self.emoji}


class PhotoSize(JsonDeserializable):
    """
    This object represents one size of a photo or a file / sticker thumbnail.

    Telegram Documentation: https://core.telegram.org/bots/api#photosize

    :param file_id: Identifier for this file, which can be used to download or reuse the file
    :type file_id: :obj:`str`

    :param file_unique_id: Unique identifier for this file, which is supposed to be the same over time and for different 
        bots. Can't be used to download or reuse the file.
    :type file_unique_id: :obj:`str`

    :param width: Photo width
    :type width: :obj:`int`

    :param height: Photo height
    :type height: :obj:`int`

    :param file_size: Optional. File size in bytes
    :type file_size: :obj:`int`

    :return: Instance of the class
    :rtype: :class:`telebot.types.PhotoSize`
    """
    @classmethod
    def de_json(cls, json_string):
        if json_string is None: return None
        obj = cls.check_json(json_string, dict_copy=False)
        return cls(**obj)

    def __init__(self, file_id, file_unique_id, width, height, file_size=None, **kwargs):
        self.file_id: str = file_id
        self.file_unique_id: str = file_unique_id
        self.width: int = width
        self.height: int = height
        self.file_size: Optional[int] = file_size


class Audio(JsonDeserializable):
    """
    This object represents an audio file to be treated as music by the Telegram clients.

    Telegram Documentation: https://core.telegram.org/bots/api#audio

    :param file_id: Identifier for this file, which can be used to download or reuse the file
    :type file_id: :obj:`str`

    :param file_unique_id: Unique identifier for this file, which is supposed to be the same over time and for different 
        bots. Can't be used to download or reuse the file.
    :type file_unique_id: :obj:`str`

    :param duration: Duration of the audio in seconds as defined by sender
    :type duration: :obj:`int`

    :param performer: Optional. Performer of the audio as defined by sender or by audio tags
    :type performer: :obj:`str`

    :param title: Optional. Title of the audio as defined by sender or by audio tags
    :type title: :obj:`str`

    :param file_name: Optional. Original filename as defined by sender
    :type file_name: :obj:`str`

    :param mime_type: Optional. MIME type of the file as defined by sender
    :type mime_type: :obj:`str`

    :param file_size: Optional. File size in bytes. It can be bigger than 2^31 and some programming languages may have 
        difficulty/silent defects in interpreting it. But it has at most 52 significant bits, so a signed 64-bit integer or 
        double-precision float type are safe for storing this value.
    :type file_size: :obj:`int`

    :param thumbnail: Optional. Thumbnail of the album cover to which the music file belongs
    :type thumbnail: :class:`telebot.types.PhotoSize`

    :return: Instance of the class
    :rtype: :class:`telebot.types.Audio`
    """
    @classmethod
    def de_json(cls, json_string):
        if json_string is None: return None
        obj = cls.check_json(json_string)
        if 'thumbnail' in obj and 'file_id' in obj['thumbnail']:
            obj['thumbnail'] = PhotoSize.de_json(obj['thumbnail'])
        else: 
            obj['thumbnail'] = None
        return cls(**obj)

    def __init__(self, file_id, file_unique_id, duration, performer=None, title=None, file_name=None, mime_type=None, 
                 file_size=None, thumbnail=None, **kwargs):
        self.file_id: str = file_id
        self.file_unique_id: str = file_unique_id
        self.duration: int = duration
        self.performer: Optional[str] = performer
        self.title: Optional[str] = title
        self.file_name: Optional[str] = file_name
        self.mime_type: Optional[str] = mime_type
        self.file_size: Optional[int] = file_size
        self.thumbnail: Optional[PhotoSize] = thumbnail

    @property
    def thumb(self) -> Optional[PhotoSize]:
        log_deprecation_warning('The parameter "thumb" is deprecated, use "thumbnail" instead')
        return self.thumbnail


class Voice(JsonDeserializable):
    """
    This object represents a voice note.

    Telegram Documentation: https://core.telegram.org/bots/api#voice

    :param file_id: Identifier for this file, which can be used to download or reuse the file
    :type file_id: :obj:`str`

    :param file_unique_id: Unique identifier for this file, which is supposed to be the same over time and for different 
        bots. Can't be used to download or reuse the file.
    :type file_unique_id: :obj:`str`

    :param duration: Duration of the audio in seconds as defined by sender
    :type duration: :obj:`int`

    :param mime_type: Optional. MIME type of the file as defined by sender
    :type mime_type: :obj:`str`

    :param file_size: Optional. File size in bytes. It can be bigger than 2^31 and some programming languages may have 
        difficulty/silent defects in interpreting it. But it has at most 52 significant bits, so a signed 64-bit integer or 
        double-precision float type are safe for storing this value.
    :type file_size: :obj:`int`

    :return: Instance of the class
    :rtype: :class:`telebot.types.Voice`
    """
    @classmethod
    def de_json(cls, json_string):
        if json_string is None: return None
        obj = cls.check_json(json_string, dict_copy=False)
        return cls(**obj)

    def __init__(self, file_id, file_unique_id, duration, mime_type=None, file_size=None, **kwargs):
        self.file_id: str = file_id
        self.file_unique_id: str = file_unique_id
        self.duration: int = duration
        self.mime_type: Optional[str] = mime_type
        self.file_size: Optional[int] = file_size


class Document(JsonDeserializable):
    """
    This object represents a general file (as opposed to photos, voice messages and audio files).

    Telegram Documentation: https://core.telegram.org/bots/api#document

    :param file_id: Identifier for this file, which can be used to download or reuse the file
    :type file_id: :obj:`str`

    :param file_unique_id: Unique identifier for this file, which is supposed to be the same over time and for different 
        bots. Can't be used to download or reuse the file.
    :type file_unique_id: :obj:`str`

    :param thumbnail: Optional. Document thumbnail as defined by sender
    :type thumbnail: :class:`telebot.types.PhotoSize`

    :param file_name: Optional. Original filename as defined by sender
    :type file_name: :obj:`str`

    :param mime_type: Optional. MIME type of the file as defined by sender
    :type mime_type: :obj:`str`

    :param file_size: Optional. File size in bytes. It can be bigger than 2^31 and some programming languages may have 
        difficulty/silent defects in interpreting it. But it has at most 52 significant bits, so a signed 64-bit integer or 
        double-precision float type are safe for storing this value.
    :type file_size: :obj:`int`

    :return: Instance of the class
    :rtype: :class:`telebot.types.Document`
    """
    @classmethod
    def de_json(cls, json_string):
        if json_string is None: return None
        obj = cls.check_json(json_string)
        if 'thumbnail' in obj and 'file_id' in obj['thumbnail']:
            obj['thumbnail'] = PhotoSize.de_json(obj['thumbnail'])
        else: 
            obj['thumbnail'] = None
        return cls(**obj)

    def __init__(self, file_id, file_unique_id, thumbnail=None, file_name=None, mime_type=None, file_size=None, **kwargs):
        self.file_id: str = file_id
        self.file_unique_id: str = file_unique_id
        self.thumbnail: Optional[PhotoSize] = thumbnail
        self.file_name: Optional[str] = file_name
        self.mime_type: Optional[str] = mime_type
        self.file_size: Optional[int] = file_size

    @property
    def thumb(self) -> Optional[PhotoSize]:
        log_deprecation_warning('The parameter "thumb" is deprecated, use "thumbnail" instead')
        return self.thumbnail


class Video(JsonDeserializable):
    """
    This object represents a video file.

    Telegram Documentation: https://core.telegram.org/bots/api#video

    :param file_id: Identifier for this file, which can be used to download or reuse the file
    :type file_id: :obj:`str`

    :param file_unique_id: Unique identifier for this file, which is supposed to be the same over time and for different 
        bots. Can't be used to download or reuse the file.
    :type file_unique_id: :obj:`str`

    :param width: Video width as defined by sender
    :type width: :obj:`int`

    :param height: Video height as defined by sender
    :type height: :obj:`int`

    :param duration: Duration of the video in seconds as defined by sender
    :type duration: :obj:`int`

    :param thumbnail: Optional. Video thumbnail
    :type thumbnail: :class:`telebot.types.PhotoSize`

    :param cover: Optional. Available sizes of the cover of the video in the message
    :type cover: List[:class:`telebot.types.PhotoSize`]

    :param start_timestamp: Optional. Timestamp in seconds from which the video will play in the message
    :type start_timestamp: :obj:`int`

    :param file_name: Optional. Original filename as defined by sender
    :type file_name: :obj:`str`

    :param mime_type: Optional. MIME type of the file as defined by sender
    :type mime_type: :obj:`str`

    :param file_size: Optional. File size in bytes. It can be bigger than 2^31 and some programming languages may have 
        difficulty/silent defects in interpreting it. But it has at most 52 significant bits, so a signed 64-bit integer or 
        double-precision float type are safe for storing this value.
    :type file_size: :obj:`int`

    :return: Instance of the class
    :rtype: :class:`telebot.types.Video`
    """
    @classmethod
    def de_json(cls, json_string):
        if json_string is None: return None
        obj = cls.check_json(json_string)
        if 'thumbnail' in obj and 'file_id' in obj['thumbnail']:
            obj['thumbnail'] = PhotoSize.de_json(obj['thumbnail'])
        if 'cover' in obj:
            obj['cover'] = [PhotoSize.de_json(c) for c in obj['cover']]
        return cls(**obj)

    def __init__(self, file_id, file_unique_id, width, height, duration, thumbnail=None, file_name=None, mime_type=None, file_size=None,
                    cover=None, start_timestamp=None, **kwargs):
        self.file_id: str = file_id
        self.file_unique_id: str = file_unique_id
        self.width: int = width
        self.height: int = height
        self.duration: int = duration
        self.thumbnail: PhotoSize = thumbnail
        self.file_name: Optional[str] = file_name
        self.mime_type: Optional[str] = mime_type
        self.file_size: Optional[int] = file_size
        self.cover: Optional[List[PhotoSize]] = cover
        self.start_timestamp: Optional[int] = start_timestamp

    @property
    def thumb(self) -> Optional[PhotoSize]:
        log_deprecation_warning('The parameter "thumb" is deprecated, use "thumbnail" instead')
        return self.thumbnail


class VideoNote(JsonDeserializable):
    """
    This object represents a video message (available in Telegram apps as of v.4.0).

    Telegram Documentation: https://core.telegram.org/bots/api#videonote

    :param file_id: Identifier for this file, which can be used to download or reuse the file
    :type file_id: :obj:`str`

    :param file_unique_id: Unique identifier for this file, which is supposed to be the same over time and for different 
        bots. Can't be used to download or reuse the file.
    :type file_unique_id: :obj:`str`

    :param length: Video width and height (diameter of the video message) as defined by sender
    :type length: :obj:`int`

    :param duration: Duration of the video in seconds as defined by sender
    :type duration: :obj:`int`

    :param thumbnail: Optional. Video thumbnail
    :type thumbnail: :class:`telebot.types.PhotoSize`

    :param file_size: Optional. File size in bytes
    :type file_size: :obj:`int`

    :return: Instance of the class
    :rtype: :class:`telebot.types.VideoNote`
    """
    @classmethod
    def de_json(cls, json_string):
        if json_string is None: return None
        obj = cls.check_json(json_string)
        if 'thumbnail' in obj and 'file_id' in obj['thumbnail']:
            obj['thumbnail'] = PhotoSize.de_json(obj['thumbnail'])
        return cls(**obj)

    def __init__(self, file_id, file_unique_id, length, duration, thumbnail=None, file_size=None, **kwargs):
        self.file_id: str = file_id
        self.file_unique_id: str = file_unique_id
        self.length: int = length
        self.duration: int = duration
        self.thumbnail: Optional[PhotoSize] = thumbnail
        self.file_size: Optional[int] = file_size

    @property
    def thumb(self) -> Optional[PhotoSize]:
        log_deprecation_warning('The parameter "thumb" is deprecated, use "thumbnail" instead')
        return self.thumbnail


class Contact(JsonDeserializable):
    """
    This object represents a phone contact.

    Telegram Documentation: https://core.telegram.org/bots/api#contact

    :param phone_number: Contact's phone number
    :type phone_number: :obj:`str`

    :param first_name: Contact's first name
    :type first_name: :obj:`str`

    :param last_name: Optional. Contact's last name
    :type last_name: :obj:`str`

    :param user_id: Optional. Contact's user identifier in Telegram. This number may have more than 32 significant bits 
        and some programming languages may have difficulty/silent defects in interpreting it. But it has at most 52 
        significant bits, so a 64-bit integer or double-precision float type are safe for storing this identifier.
    :type user_id: :obj:`int`

    :param vcard: Optional. Additional data about the contact in the form of a vCard
    :type vcard: :obj:`str`

    :return: Instance of the class
    :rtype: :class:`telebot.types.Contact`
    """
    @classmethod
    def de_json(cls, json_string):
        if json_string is None: return None
        obj = cls.check_json(json_string, dict_copy=False)
        return cls(**obj)

    def __init__(self, phone_number, first_name, last_name=None, user_id=None, vcard=None, **kwargs):
        self.phone_number: str = phone_number
        self.first_name: str = first_name
        self.last_name: Optional[str] = last_name
        self.user_id: Optional[int] = user_id
        self.vcard: Optional[str] = vcard


class Location(JsonDeserializable, JsonSerializable, Dictionaryable):
    """
    This object represents a point on the map.

    Telegram Documentation: https://core.telegram.org/bots/api#location

    :param longitude: Longitude as defined by sender
    :type longitude: :obj:`float`

    :param latitude: Latitude as defined by sender
    :type latitude: :obj:`float`

    :param horizontal_accuracy: Optional. The radius of uncertainty for the location, measured in meters; 0-1500
    :type horizontal_accuracy: :obj:`float` number

    :param live_period: Optional. Time relative to the message sending date, during which the location can be updated; 
        in seconds. For active live locations only.
    :type live_period: :obj:`int`

    :param heading: Optional. The direction in which user is moving, in degrees; 1-360. For active live locations only.
    :type heading: :obj:`int`

    :param proximity_alert_radius: Optional. The maximum distance for proximity alerts about approaching another 
        chat member, in meters. For sent live locations only.
    :type proximity_alert_radius: :obj:`int`

    :return: Instance of the class
    :rtype: :class:`telebot.types.Location`
    """
    @classmethod
    def de_json(cls, json_string):
        if json_string is None: return None
        obj = cls.check_json(json_string, dict_copy=False)
        return cls(**obj)

    def __init__(self, longitude, latitude, horizontal_accuracy=None,
                 live_period=None, heading=None, proximity_alert_radius=None, **kwargs):
        self.longitude: float = longitude
        self.latitude: float = latitude
        self.horizontal_accuracy: Optional[float] = horizontal_accuracy
        self.live_period: Optional[int] = live_period
        self.heading: Optional[int] = heading
        self.proximity_alert_radius: Optional[int] = proximity_alert_radius
    
    def to_json(self):
        return json.dumps(self.to_dict())
    
    def to_dict(self):
        return {
            "longitude": self.longitude,
            "latitude": self.latitude,
            "horizontal_accuracy": self.horizontal_accuracy,
            "live_period": self.live_period,
            "heading": self.heading,
            "proximity_alert_radius": self.proximity_alert_radius,
        }


class Venue(JsonDeserializable):
    """
    This object represents a venue.

    Telegram Documentation: https://core.telegram.org/bots/api#venue

    :param location: Venue location. Can't be a live location
    :type location: :class:`telebot.types.Location`

    :param title: Name of the venue
    :type title: :obj:`str`

    :param address: Address of the venue
    :type address: :obj:`str`

    :param foursquare_id: Optional. Foursquare identifier of the venue
    :type foursquare_id: :obj:`str`

    :param foursquare_type: Optional. Foursquare type of the venue. (For example, “arts_entertainment/default”, 
        “arts_entertainment/aquarium” or “food/icecream”.)
    :type foursquare_type: :obj:`str`

    :param google_place_id: Optional. Google Places identifier of the venue
    :type google_place_id: :obj:`str`

    :param google_place_type: Optional. Google Places type of the venue. (See supported types.)
    :type google_place_type: :obj:`str`

    :return: Instance of the class
    :rtype: :class:`telebot.types.Venue`
    """
    @classmethod
    def de_json(cls, json_string):
        if json_string is None: return None
        obj = cls.check_json(json_string)
        obj['location'] = Location.de_json(obj['location'])
        return cls(**obj)

    def __init__(self, location, title, address, foursquare_id=None, foursquare_type=None, 
                 google_place_id=None, google_place_type=None, **kwargs):
        self.location: Location = location
        self.title: str = title
        self.address: str = address
        self.foursquare_id: Optional[str] = foursquare_id
        self.foursquare_type: Optional[str] = foursquare_type
        self.google_place_id: Optional[str] = google_place_id
        self.google_place_type: Optional[str] = google_place_type


class UserProfilePhotos(JsonDeserializable):
    """
    This object represent a user's profile pictures.

    Telegram Documentation: https://core.telegram.org/bots/api#userprofilephotos

    :param total_count: Total number of profile pictures the target user has
    :type total_count: :obj:`int`

    :param photos: Requested profile pictures (in up to 4 sizes each)
    :type photos: :obj:`list` of :obj:`list` of :class:`telebot.types.PhotoSize`

    :return: Instance of the class
    :rtype: :class:`telebot.types.UserProfilePhotos`
    """
    @classmethod
    def de_json(cls, json_string):
        if json_string is None: return None
        obj = cls.check_json(json_string)
        if 'photos' in obj:
            photos = [[PhotoSize.de_json(y) for y in x] for x in obj['photos']]
            obj['photos'] = photos
        return cls(**obj)

    def __init__(self, total_count, photos=None, **kwargs):
        self.total_count: int = total_count
        self.photos: List[PhotoSize] = photos


class File(JsonDeserializable):
    """
    This object represents a file ready to be downloaded. The file can be downloaded via the link https://api.telegram.org/file/bot<token>/<file_path>. It is guaranteed that the link will be valid for at least 1 hour. When the link expires, a new one can be requested by calling getFile.

    Telegram Documentation: https://core.telegram.org/bots/api#file

    :param file_id: Identifier for this file, which can be used to download or reuse the file
    :type file_id: :obj:`str`

    :param file_unique_id: Unique identifier for this file, which is supposed to be the same over time and for different 
        bots. Can't be used to download or reuse the file.
    :type file_unique_id: :obj:`str`

    :param file_size: Optional. File size in bytes. It can be bigger than 2^31 and some programming languages may have 
        difficulty/silent defects in interpreting it. But it has at most 52 significant bits, so a signed 64-bit integer or 
        double-precision float type are safe for storing this value.
    :type file_size: :obj:`int`

    :param file_path: Optional. File path. Use https://api.telegram.org/file/bot<token>/<file_path> to get the 
        file.
    :type file_path: :obj:`str`

    :return: Instance of the class
    :rtype: :class:`telebot.types.File`
    """
    @classmethod
    def de_json(cls, json_string):
        if json_string is None: return None
        obj = cls.check_json(json_string, dict_copy=False)
        return cls(**obj)

    def __init__(self, file_id, file_unique_id, file_size=None, file_path=None, **kwargs):
        self.file_id: str = file_id
        self.file_unique_id: str = file_unique_id
        self.file_size: Optional[int] = file_size
        self.file_path: Optional[str] = file_path


# noinspection PyUnresolvedReferences
class ForceReply(JsonSerializable):
    """
    Upon receiving a message with this object, Telegram clients will display a reply interface to the user (act as if the user has selected the bot's message and tapped 'Reply'). This can be extremely useful if you want to create user-friendly step-by-step interfaces without having to sacrifice privacy mode.

    Telegram Documentation: https://core.telegram.org/bots/api#forcereply

    :param force_reply: Shows reply interface to the user, as if they manually selected the bot's message and tapped 
        'Reply'
    :type force_reply: :obj:`bool`

    :param input_field_placeholder: Optional. The placeholder to be shown in the input field when the reply is active; 
        1-64 characters
    :type input_field_placeholder: :obj:`str`

    :param selective: Optional. Use this parameter if you want to force reply from specific users only. Targets: 1) users
        that are @mentioned in the text of the Message object; 2) if the bot's message is a reply to a message in the same
        chat and forum topic, sender of the original message.
    :type selective: :obj:`bool`

    :return: Instance of the class
    :rtype: :class:`telebot.types.ForceReply`
    """
    def __init__(self, selective: Optional[bool]=None, input_field_placeholder: Optional[str]=None):
        self.selective: Optional[bool] = selective
        self.input_field_placeholder: Optional[str] = input_field_placeholder

    def to_json(self):
        json_dict = {'force_reply': True}
        if self.selective is not None:
            json_dict['selective'] = self.selective
        if self.input_field_placeholder:
            json_dict['input_field_placeholder'] = self.input_field_placeholder
        return json.dumps(json_dict)


# noinspection PyUnresolvedReferences
class ReplyKeyboardRemove(JsonSerializable):
    """
    Upon receiving a message with this object, Telegram clients will remove the current custom keyboard and display the default letter-keyboard. By default, custom keyboards are displayed until a new keyboard is sent by a bot. An exception is made for one-time keyboards that are hidden immediately after the user presses a button (see ReplyKeyboardMarkup).

    Telegram Documentation: https://core.telegram.org/bots/api#replykeyboardremove

    :param remove_keyboard: Requests clients to remove the custom keyboard (user will not be able to summon this 
        keyboard; if you want to hide the keyboard from sight but keep it accessible, use one_time_keyboard in 
        ReplyKeyboardMarkup)
        Note that this parameter is set to True by default by the library. You cannot modify it.
    :type remove_keyboard: :obj:`bool`

    :param selective: Optional. Use this parameter if you want to remove the keyboard for specific users only. Targets: 
        1) users that are @mentioned in the text of the Message object; 2) if the bot's message is a reply (has 
        reply_to_message_id), sender of the original message.Example: A user votes in a poll, bot returns confirmation 
        message in reply to the vote and removes the keyboard for that user, while still showing the keyboard with poll options 
        to users who haven't voted yet.
    :type selective: :obj:`bool`

    :return: Instance of the class
    :rtype: :class:`telebot.types.ReplyKeyboardRemove`
    """
    def __init__(self, selective: Optional[bool]=None):
        self.selective: Optional[bool] = selective

    def to_json(self):
        json_dict = {'remove_keyboard': True}
        if self.selective:
            json_dict['selective'] = self.selective
        return json.dumps(json_dict)


class WebAppInfo(JsonDeserializable, Dictionaryable):
    """
    Describes a Web App.

    Telegram Documentation: https://core.telegram.org/bots/api#webappinfo

    :param url: An HTTPS URL of a Web App to be opened with additional data as specified in Initializing Web Apps
    :type url: :obj:`str`

    :return: Instance of the class
    :rtype: :class:`telebot.types.WebAppInfo`
    """
    @classmethod
    def de_json(cls, json_string):
        if json_string is None: return None
        obj = cls.check_json(json_string)
        return cls(**obj)

    def __init__(self, url, **kwargs):
        self.url: str = url

    def to_dict(self):
        return {'url': self.url}


# noinspection PyUnresolvedReferences
class ReplyKeyboardMarkup(JsonSerializable):
    """
    This object represents a custom keyboard with reply options (see Introduction to bots for details and examples).

    .. code-block:: python3
        :caption: Example on creating ReplyKeyboardMarkup object

        from telebot.types import ReplyKeyboardMarkup, KeyboardButton

        markup = ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add(KeyboardButton('Text'))
        # or:
        markup.add('Text')

        # display this markup:
        bot.send_message(chat_id, 'Text', reply_markup=markup)

    Telegram Documentation: https://core.telegram.org/bots/api#replykeyboardmarkup

    :param keyboard: :obj:`list` of button rows, each represented by an :obj:`list` of 
        :class:`telebot.types.KeyboardButton` objects
    :type keyboard: :obj:`list` of :obj:`list` of :class:`telebot.types.KeyboardButton`

    :param resize_keyboard: Optional. Requests clients to resize the keyboard vertically for optimal fit (e.g., make 
        the keyboard smaller if there are just two rows of buttons). Defaults to false, in which case the custom keyboard is 
        always of the same height as the app's standard keyboard.
    :type resize_keyboard: :obj:`bool`

    :param one_time_keyboard: Optional. Requests clients to hide the keyboard as soon as it's been used. The keyboard 
        will still be available, but clients will automatically display the usual letter-keyboard in the chat - the user can 
        press a special button in the input field to see the custom keyboard again. Defaults to false.
    :type one_time_keyboard: :obj:`bool`

    :param input_field_placeholder: Optional. The placeholder to be shown in the input field when the keyboard is 
        active; 1-64 characters
    :type input_field_placeholder: :obj:`str`

    :param selective: Optional. Use this parameter if you want to show the keyboard to specific users only. Targets:
        1) users that are @mentioned in the text of the Message object; 2) if the bot's message is a reply to a message
        in the same chat and forum topic, sender of the original message. Example: A user requests to change the bot's
        language, bot replies to the request with a keyboard to select the new language. Other users in the group don't
        see the keyboard.
    :type selective: :obj:`bool`

    :param is_persistent: Optional. Use this parameter if you want to show the keyboard to specific users only.
        Targets: 1) users that are @mentioned in the text of the Message object; 2) if the bot's message is a
        reply (has reply_to_message_id), sender of the original message.
        
        Example: A user requests to change the bot's language, bot replies to the request with a keyboard to
        select the new language. Other users in the group don't see the keyboard.

    :return: Instance of the class
    :rtype: :class:`telebot.types.ReplyKeyboardMarkup`
    """
    max_row_keys = 12

    def __init__(self, resize_keyboard: Optional[bool]=None, one_time_keyboard: Optional[bool]=None, 
            selective: Optional[bool]=None, row_width: int=3, input_field_placeholder: Optional[str]=None,
            is_persistent: Optional[bool]=None):
        if row_width > self.max_row_keys:
            # Todo: Will be replaced with Exception in future releases
            if not DISABLE_KEYLEN_ERROR:
                logger.error('Telegram does not support reply keyboard row width over %d.' % self.max_row_keys)
            row_width = self.max_row_keys

        self.resize_keyboard: Optional[bool] = resize_keyboard
        self.one_time_keyboard: Optional[bool] = one_time_keyboard
        self.selective: Optional[bool] = selective
        self.row_width: Optional[int] = row_width
        self.input_field_placeholder: Optional[str] = input_field_placeholder
        self.keyboard: List[List[KeyboardButton]] = []
        self.is_persistent: Optional[bool] = is_persistent

    def add(self, *args, row_width=None) -> 'ReplyKeyboardMarkup':
        """
        This function adds strings to the keyboard, while not exceeding row_width.
        E.g. ReplyKeyboardMarkup#add("A", "B", "C") yields the json result {keyboard: [["A"], ["B"], ["C"]]}
        when row_width is set to 1.
        When row_width is set to 2, the following is the result of this function: {keyboard: [["A", "B"], ["C"]]}
        See https://core.telegram.org/bots/api#replykeyboardmarkup

        :param args: KeyboardButton to append to the keyboard
        :type args: :obj:`str` or :class:`telebot.types.KeyboardButton`

        :param row_width: width of row
        :type row_width: :obj:`int`

        :return: self, to allow function chaining.
        :rtype: :class:`telebot.types.ReplyKeyboardMarkup`
        """
        if row_width is None:
            row_width = self.row_width

        if row_width > self.max_row_keys:
            # Todo: Will be replaced with Exception in future releases
            if not DISABLE_KEYLEN_ERROR:
                logger.error('Telegram does not support reply keyboard row width over %d.' % self.max_row_keys)
            row_width = self.max_row_keys
        
        for row in service_utils.chunks(args, row_width):
            button_array = []
            for button in row:
                if service_utils.is_string(button):
                    button_array.append({'text': button})
                elif service_utils.is_bytes(button):
                    button_array.append({'text': button.decode('utf-8')})
                else:
                    button_array.append(button.to_dict())
            self.keyboard.append(button_array)

        return self

    def row(self, *args) -> 'ReplyKeyboardMarkup':
        """
        Adds a list of KeyboardButton to the keyboard. This function does not consider row_width.
        ReplyKeyboardMarkup#row("A")#row("B", "C")#to_json() outputs '{keyboard: [["A"], ["B", "C"]]}'
        See https://core.telegram.org/bots/api#replykeyboardmarkup

        :param args: strings
        :type args: :obj:`str`

        :return: self, to allow function chaining.
        :rtype: :class:`telebot.types.ReplyKeyboardMarkup`
        """

        return self.add(*args, row_width=self.max_row_keys)

    def to_json(self):
        json_dict = {'keyboard': self.keyboard}
        if self.one_time_keyboard is not None:
            json_dict['one_time_keyboard'] = self.one_time_keyboard
        if self.resize_keyboard is not None:
            json_dict['resize_keyboard'] = self.resize_keyboard
        if self.selective is not None:
            json_dict['selective'] = self.selective
        if self.input_field_placeholder:
            json_dict['input_field_placeholder'] = self.input_field_placeholder
        if self.is_persistent is not None:
            json_dict['is_persistent'] = self.is_persistent
        return json.dumps(json_dict)


# noinspection PyShadowingBuiltins
class KeyboardButtonPollType(Dictionaryable):
    """
    This object represents type of a poll, which is allowed to be created and sent when the corresponding button is pressed.

    Telegram Documentation: https://core.telegram.org/bots/api#keyboardbuttonpolltype

    :param type: Optional. If quiz is passed, the user will be allowed to create only polls in the quiz mode. If regular is passed, only regular polls will be allowed. Otherwise, the user will be allowed to create a poll of any type.
    :type type: :obj:`str`

    :return: Instance of the class
    :rtype: :class:`telebot.types.KeyboardButtonPollType`
    """
    def __init__(self, type=None):
        self.type: str = type

    def to_dict(self):
        return {'type': self.type}
    
 
class KeyboardButtonRequestUsers(Dictionaryable):
    """
    This object defines the criteria used to request a suitable user.
    The identifier of the selected user will be shared with the bot when the corresponding button is pressed.

    Telegram documentation: https://core.telegram.org/bots/api#keyboardbuttonrequestusers

    :param request_id: Signed 32-bit identifier of the request, which will be received back in the UsersShared object.
        Must be unique within the message
    :type request_id: :obj:`int`

    :param user_is_bot: Optional. Pass True to request a bot, pass False to request a regular user.
        If not specified, no additional restrictions are applied.
    :type user_is_bot: :obj:`bool`

    :param user_is_premium: Optional. Pass True to request a premium user, pass False to request a non-premium user.
        If not specified, no additional restrictions are applied.
    :type user_is_premium: :obj:`bool`

    :param max_quantity: Optional. The maximum number of users to be selected; 1-10. Defaults to 1.
    :type max_quantity: :obj:`int`

    :param request_name: Optional. Request name
    :type request_name: :obj:`bool`

    :param request_username: Optional. Request username
    :type request_username: :obj:`bool`

    :param request_photo: Optional. Request photo
    :type request_photo: :obj:`bool`

    :return: Instance of the class
    :rtype: :class:`telebot.types.KeyboardButtonRequestUsers`
    """
    def __init__(
            self, request_id: int, user_is_bot: Optional[bool]=None, user_is_premium: Optional[bool]=None,
            max_quantity: Optional[int]=None, request_name: Optional[bool]=None, request_username: Optional[bool]=None,
            request_photo: Optional[bool]=None) -> None:
        self.request_id: int = request_id
        self.user_is_bot: Optional[bool] = user_is_bot
        self.user_is_premium: Optional[bool] = user_is_premium
        self.max_quantity: Optional[int] = max_quantity
        self.request_name: Optional[bool] = request_name
        self.request_username: Optional[bool] = request_username
        self.request_photo: Optional[bool] = request_photo

    def to_dict(self) -> dict:
        data = {'request_id': self.request_id}
        if self.user_is_bot is not None:
            data['user_is_bot'] = self.user_is_bot
        if self.user_is_premium is not None:
            data['user_is_premium'] = self.user_is_premium
        if self.max_quantity is not None:
            data['max_quantity'] = self.max_quantity
        if self.request_name is not None:
            data['request_name'] = self.request_name
        if self.request_username is not None:
            data['request_username'] = self.request_username
        if self.request_photo is not None:
            data['request_photo'] = self.request_photo
        return data


class KeyboardButtonRequestUser(KeyboardButtonRequestUsers):
    """Deprecated. Use KeyboardButtonRequestUsers instead."""
    def __init__(
            self, request_id: int, user_is_bot: Optional[bool]=None, user_is_premium: Optional[bool]=None,
            max_quantity: Optional[int]=None) -> None:
        log_deprecation_warning('The class "KeyboardButtonRequestUser" is deprecated, use "KeyboardButtonRequestUsers" instead')
        super().__init__(request_id, user_is_bot=user_is_bot, user_is_premium=user_is_premium, max_quantity=max_quantity)


class KeyboardButtonRequestChat(Dictionaryable):
    """
    This object defines the criteria used to request a suitable chat. The identifier of the selected chat will
    be shared with the bot when the corresponding button is pressed.

    Telegram documentation: https://core.telegram.org/bots/api#keyboardbuttonrequestchat

    :param request_id: Signed 32-bit identifier of the request, which will be received back in the ChatShared object.
        Must be unique within the message
    :type request_id: :obj:`int`

    :param chat_is_channel: Pass True to request a channel chat, pass False to request a group or a supergroup chat.
    :type chat_is_channel: :obj:`bool`

    :param chat_is_forum: Optional. Pass True to request a forum supergroup, pass False to request a non-forum chat.
        If not specified, no additional restrictions are applied.
    :type chat_is_forum: :obj:`bool`

    :param chat_has_username: Optional. Pass True to request a supergroup or a channel with a username, pass False to request a
        chat without a username. If not specified, no additional restrictions are applied.
    :type chat_has_username: :obj:`bool`

    :param chat_is_created: Optional. Pass True to request a chat owned by the user. Otherwise, no additional restrictions are applied.
    :type chat_is_created: :obj:`bool`

    :param user_administrator_rights: Optional. A JSON-serialized object listing the required administrator rights of the user in the chat.
        The rights must be a superset of bot_administrator_rights. If not specified, no additional restrictions are applied.
    :type user_administrator_rights: :class:`telebot.types.ChatAdministratorRights`

    :param bot_administrator_rights: Optional. A JSON-serialized object listing the required administrator rights of the bot in the chat.
        The rights must be a subset of user_administrator_rights. If not specified, no additional restrictions are applied.
    :type bot_administrator_rights: :class:`telebot.types.ChatAdministratorRights`

    :param bot_is_member: Optional. Pass True to request a chat where the bot is a member. Otherwise, no additional restrictions are applied.
    :type bot_is_member: :obj:`bool`

    :param request_title: Optional. Request title
    :type request_title: :obj:`bool`

    :param request_photo: Optional. Request photo
    :type request_photo: :obj:`bool`

    :param request_username: Optional. Request username
    :type request_username: :obj:`bool`

    :return: Instance of the class
    :rtype: :class:`telebot.types.KeyboardButtonRequestChat`
    """

    def __init__(self, request_id: int, chat_is_channel: bool, chat_is_forum: Optional[bool]=None,
                 chat_has_username: Optional[bool]=None, chat_is_created: Optional[bool]=None,
                 user_administrator_rights: Optional[ChatAdministratorRights]=None,
                 bot_administrator_rights: Optional[ChatAdministratorRights]=None, bot_is_member: Optional[bool]=None,
                 request_title: Optional[bool]=None, request_photo: Optional[bool]=None, request_username: Optional[bool]=None):
        self.request_id: int = request_id
        self.chat_is_channel: bool = chat_is_channel
        self.chat_is_forum: Optional[bool] = chat_is_forum
        self.chat_has_username: Optional[bool] = chat_has_username
        self.chat_is_created: Optional[bool] = chat_is_created
        self.user_administrator_rights: Optional[ChatAdministratorRights] = user_administrator_rights
        self.bot_administrator_rights: Optional[ChatAdministratorRights] = bot_administrator_rights
        self.bot_is_member: Optional[bool] = bot_is_member
        self.request_title: Optional[bool] = request_title
        self.request_photo: Optional[bool] = request_photo
        self.request_username: Optional[bool] = request_username


    def to_dict(self) -> dict:
        data = {'request_id': self.request_id, 'chat_is_channel': self.chat_is_channel}
        if self.chat_is_forum is not None:
            data['chat_is_forum'] = self.chat_is_forum
        if self.chat_has_username is not None:
            data['chat_has_username'] = self.chat_has_username
        if self.chat_is_created is not None:
            data['chat_is_created'] = self.chat_is_created
        if self.user_administrator_rights is not None:
            data['user_administrator_rights'] = self.user_administrator_rights.to_dict()
        if self.bot_administrator_rights is not None:
            data['bot_administrator_rights'] = self.bot_administrator_rights.to_dict()
        if self.bot_is_member is not None:
            data['bot_is_member'] = self.bot_is_member
        if self.request_title is not None:
            data['request_title'] = self.request_title
        if self.request_photo is not None:
            data['request_photo'] = self.request_photo
        if self.request_username is not None:
            data['request_username'] = self.request_username
        return data



class KeyboardButton(Dictionaryable, JsonSerializable):
    """
    This object represents one button of the reply keyboard. For simple text buttons String can be used instead of this object to specify text of the button. Optional fields web_app, request_contact, request_location, and request_poll are mutually exclusive.

    Telegram Documentation: https://core.telegram.org/bots/api#keyboardbutton

    :param text: Text of the button. If none of the optional fields are used, it will be sent as a message when the button is 
        pressed
    :type text: :obj:`str`

    :param request_contact: Optional. If True, the user's phone number will be sent as a contact when the button is 
        pressed. Available in private chats only.
    :type request_contact: :obj:`bool`

    :param request_location: Optional. If True, the user's current location will be sent when the button is pressed. 
        Available in private chats only.
    :type request_location: :obj:`bool`

    :param request_poll: Optional. If specified, the user will be asked to create a poll and send it to the bot when the 
        button is pressed. Available in private chats only.
    :type request_poll: :class:`telebot.types.KeyboardButtonPollType`

    :param web_app: Optional. If specified, the described Web App will be launched when the button is pressed. The Web App 
        will be able to send a “web_app_data” service message. Available in private chats only.
    :type web_app: :class:`telebot.types.WebAppInfo`

    :param request_user: deprecated
    :type request_user: :class:`telebot.types.KeyboardButtonRequestUser`

    :param request_users: Optional. If specified, pressing the button will open a list of suitable users.
        Identifiers of selected users will be sent to the bot in a “users_shared” service message. Available in private chats only.
    :type request_users: :class:`telebot.types.KeyboardButtonRequestUsers`

    :param request_chat: Optional. If specified, pressing the button will open a list of suitable chats. Tapping on a chat will
        send its identifier to the bot in a “chat_shared” service message. Available in private chats only.
    :type request_chat: :class:`telebot.types.KeyboardButtonRequestChat`

    :return: Instance of the class
    :rtype: :class:`telebot.types.KeyboardButton`
    """
    def __init__(self, text: str, request_contact: Optional[bool]=None, 
            request_location: Optional[bool]=None, request_poll: Optional[KeyboardButtonPollType]=None,
            web_app: Optional[WebAppInfo]=None, request_user: Optional[KeyboardButtonRequestUser]=None,
            request_chat: Optional[KeyboardButtonRequestChat]=None, request_users: Optional[KeyboardButtonRequestUsers]=None):
        self.text: str = text
        self.request_contact: Optional[bool] = request_contact
        self.request_location: Optional[bool] = request_location
        self.request_poll: Optional[KeyboardButtonPollType] = request_poll
        self.web_app: Optional[WebAppInfo] = web_app
        self.request_chat: Optional[KeyboardButtonRequestChat] = request_chat
        self.request_users: Optional[KeyboardButtonRequestUsers] = request_users
        if request_user is not None:
            log_deprecation_warning('The parameter "request_user" is deprecated, use "request_users" instead')
            if self.request_users is None:
                # noinspection PyTypeChecker
                self.request_users = request_user


    def to_json(self):
        return json.dumps(self.to_dict())

    def to_dict(self):
        json_dict = {'text': self.text}
        if self.request_contact is not None:
            json_dict['request_contact'] = self.request_contact
        if self.request_location is not None:
            json_dict['request_location'] = self.request_location
        if self.request_poll is not None:
            json_dict['request_poll'] = self.request_poll.to_dict()
        if self.web_app is not None:
            json_dict['web_app'] = self.web_app.to_dict()
        if self.request_users is not None:
            json_dict['request_users'] = self.request_users.to_dict()
        if self.request_chat is not None:
            json_dict['request_chat'] = self.request_chat.to_dict()
        return json_dict


class InlineKeyboardMarkup(Dictionaryable, JsonSerializable, JsonDeserializable):
    """
    This object represents an inline keyboard that appears right next to the message it belongs to.

    .. note::
        It is recommended to use :meth:`telebot.util.quick_markup` instead.

    .. code-block:: python3
        :caption: Example of a custom keyboard with buttons.

        from telebot.util import quick_markup

        markup = quick_markup({
            'Twitter': {'url': 'https://twitter.com'},
            'Facebook': {'url': 'https://facebook.com'},
            'Back': {'callback_data': 'whatever'}
        }, row_width=2)
        # returns an InlineKeyboardMarkup with two buttons in a row, one leading to Twitter, the other to facebook
        # and a back button below

    Telegram Documentation: https://core.telegram.org/bots/api#inlinekeyboardmarkup

    :param keyboard: :obj:`list` of button rows, each represented by an :obj:`list` of 
        :class:`telebot.types.InlineKeyboardButton` objects
    :type keyboard: :obj:`list` of :obj:`list` of :class:`telebot.types.InlineKeyboardButton`

    :param row_width: number of :class:`telebot.types.InlineKeyboardButton` objects on each row
    :type row_width: :obj:`int`

    :return: Instance of the class
    :rtype: :class:`telebot.types.InlineKeyboardMarkup`
    """
    max_row_keys = 8
    
    @classmethod
    def de_json(cls, json_string):
        if json_string is None: return None
        obj = cls.check_json(json_string, dict_copy=False)
        keyboard = [[InlineKeyboardButton.de_json(button) for button in row] for row in obj['inline_keyboard']]
        return cls(keyboard = keyboard)

    def __init__(self, keyboard=None, row_width=3):
        if row_width > self.max_row_keys:
            # Todo: Will be replaced with Exception in future releases
            logger.error('Telegram does not support inline keyboard row width over %d.' % self.max_row_keys)
            row_width = self.max_row_keys
        
        self.row_width: int = row_width
        self.keyboard: List[List[InlineKeyboardButton]] = keyboard or []

    def add(self, *args, row_width=None) -> 'InlineKeyboardMarkup':
        """
        This method adds buttons to the keyboard without exceeding row_width.

        E.g. InlineKeyboardMarkup.add("A", "B", "C") yields the json result:
        {keyboard: [["A"], ["B"], ["C"]]}
        when row_width is set to 1.
        When row_width is set to 2, the result:
        {keyboard: [["A", "B"], ["C"]]}
        See https://core.telegram.org/bots/api#inlinekeyboardmarkup
        
        :param args: Array of InlineKeyboardButton to append to the keyboard
        :type args: :obj:`list` of :class:`telebot.types.InlineKeyboardButton`

        :param row_width: width of row
        :type row_width: :obj:`int`

        :return: self, to allow function chaining.
        :rtype: :class:`telebot.types.InlineKeyboardMarkup`
        """
        if row_width is None:
            row_width = self.row_width
        
        if row_width > self.max_row_keys:
            # Todo: Will be replaced with Exception in future releases
            logger.error('Telegram does not support inline keyboard row width over %d.' % self.max_row_keys)
            row_width = self.max_row_keys
        
        for row in service_utils.chunks(args, row_width):
            button_array = [button for button in row]
            self.keyboard.append(button_array)
        
        return self
        
    def row(self, *args) -> 'InlineKeyboardMarkup':
        """
        Adds a list of InlineKeyboardButton to the keyboard.
        This method does not consider row_width.

        InlineKeyboardMarkup.row("A").row("B", "C").to_json() outputs:
        '{keyboard: [["A"], ["B", "C"]]}'
        See https://core.telegram.org/bots/api#inlinekeyboardmarkup
        
        :param args: Array of InlineKeyboardButton to append to the keyboard
        :type args: :obj:`list` of :class:`telebot.types.InlineKeyboardButton`

        :return: self, to allow function chaining.
        :rtype: :class:`telebot.types.InlineKeyboardMarkup`
        """
         
        return self.add(*args, row_width=self.max_row_keys)

    def to_json(self):
        return json.dumps(self.to_dict())

    def to_dict(self):
        json_dict = dict()
        json_dict['inline_keyboard'] = [[button.to_dict() for button in row] for row in self.keyboard]
        return json_dict


class InlineKeyboardButton(Dictionaryable, JsonSerializable, JsonDeserializable):
    """
    This object represents one button of an inline keyboard. You must use exactly one of the optional fields.

    Telegram Documentation: https://core.telegram.org/bots/api#inlinekeyboardbutton

    :param text: Label text on the button
    :type text: :obj:`str`

    :param url: Optional. HTTP or tg:// URL to be opened when the button is pressed. Links tg://user?id=<user_id> can be 
        used to mention a user by their ID without using a username, if this is allowed by their privacy settings.
    :type url: :obj:`str`

    :param callback_data: Optional. Data to be sent in a callback query to the bot when button is pressed, 1-64 bytes
    :type callback_data: :obj:`str`

    :param web_app: Optional. Description of the Web App that will be launched when the user presses the button. The Web 
        App will be able to send an arbitrary message on behalf of the user using the method answerWebAppQuery. Available only 
        in private chats between a user and the bot.
    :type web_app: :class:`telebot.types.WebAppInfo`

    :param login_url: Optional. An HTTPS URL used to automatically authorize the user. Can be used as a replacement for 
        the Telegram Login Widget.
    :type login_url: :class:`telebot.types.LoginUrl`

    :param switch_inline_query: Optional. If set, pressing the button will prompt the user to select one of their chats, 
        open that chat and insert the bot's username and the specified inline query in the input field. May be empty, in which 
        case just the bot's username will be inserted.Note: This offers an easy way for users to start using your bot in inline 
        mode when they are currently in a private chat with it. Especially useful when combined with switch_pm… actions - in 
        this case the user will be automatically returned to the chat they switched from, skipping the chat selection screen.
    :type switch_inline_query: :obj:`str`

    :param switch_inline_query_current_chat: Optional. If set, pressing the button will insert the bot's username 
        and the specified inline query in the current chat's input field. May be empty, in which case only the bot's username 
        will be inserted.This offers a quick way for the user to open your bot in inline mode in the same chat - good for selecting 
        something from multiple options.
    :type switch_inline_query_current_chat: :obj:`str`

    :param switch_inline_query_chosen_chat: Optional. If set, pressing the button will prompt the user to select one of their chats of the
        specified type, open that chat and insert the bot's username and the specified inline query in the input field
    :type switch_inline_query_chosen_chat: :class:`telebot.types.SwitchInlineQueryChosenChat`

    :param callback_game: Optional. Description of the game that will be launched when the user presses the 
        button. NOTE: This type of button must always be the first button in the first row.
    :type callback_game: :class:`telebot.types.CallbackGame`

    :param pay: Optional. Specify True, to send a Pay button. NOTE: This type of button must always be the first button in 
        the first row and can only be used in invoice messages.
    :type pay: :obj:`bool`

    :param copy_text: Optional. Description of the button that copies the specified text to the clipboard.
    :type copy_text: :class:`telebot.types.CopyTextButton`

    :return: Instance of the class
    :rtype: :class:`telebot.types.InlineKeyboardButton`
    """
    @classmethod
    def de_json(cls, json_string):
        if json_string is None: return None
        obj = cls.check_json(json_string)
        if 'login_url' in obj:
            obj['login_url'] = LoginUrl.de_json(obj.get('login_url'))
        if 'web_app' in obj:
            obj['web_app'] = WebAppInfo.de_json(obj.get('web_app'))
        if 'switch_inline_query_chosen_chat' in obj:
            obj['switch_inline_query_chosen_chat'] = SwitchInlineQueryChosenChat.de_json(obj.get('switch_inline_query_chosen_chat'))
        if 'copy_text' in obj:
            obj['copy_text'] = CopyTextButton.de_json(obj.get('copy_text'))
        
        return cls(**obj)

    def __init__(self, text: str, url: Optional[str]=None, callback_data: Optional[str]=None, web_app: Optional[WebAppInfo]=None,
            switch_inline_query: Optional[str]=None, switch_inline_query_current_chat: Optional[str]=None,
            switch_inline_query_chosen_chat: Optional[SwitchInlineQueryChosenChat]=None, callback_game=None, pay: Optional[bool]=None,
            login_url: Optional[LoginUrl]=None, copy_text: Optional[CopyTextButton]=None, **kwargs):
        self.text: str = text
        self.url: Optional[str] = url
        self.callback_data: Optional[str] = callback_data
        self.web_app: Optional[WebAppInfo] = web_app
        self.switch_inline_query: Optional[str] = switch_inline_query
        self.switch_inline_query_current_chat: Optional[str] = switch_inline_query_current_chat
        self.switch_inline_query_chosen_chat: Optional[SwitchInlineQueryChosenChat] = switch_inline_query_chosen_chat
        self.callback_game = callback_game # Not Implemented
        self.pay: Optional[bool] = pay
        self.login_url: Optional[LoginUrl] = login_url
        self.copy_text: Optional[CopyTextButton] = copy_text

    def to_json(self):
        return json.dumps(self.to_dict())

    def to_dict(self):
        json_dict = {'text': self.text}
        if self.url:
            json_dict['url'] = self.url
        if self.callback_data:
            json_dict['callback_data'] = self.callback_data
        if self.web_app:
            json_dict['web_app'] = self.web_app.to_dict()
        if self.switch_inline_query is not None:
            json_dict['switch_inline_query'] = self.switch_inline_query
        if self.switch_inline_query_current_chat is not None:
            json_dict['switch_inline_query_current_chat'] = self.switch_inline_query_current_chat
        if self.callback_game is not None:
            json_dict['callback_game'] = self.callback_game
        if self.pay is not None:
            json_dict['pay'] = self.pay
        if self.login_url is not None:
            json_dict['login_url'] = self.login_url.to_dict()
        if self.switch_inline_query_chosen_chat is not None:
            json_dict['switch_inline_query_chosen_chat'] = self.switch_inline_query_chosen_chat.to_dict()
        if self.copy_text is not None:
            json_dict['copy_text'] = self.copy_text.to_dict()
        return json_dict


class LoginUrl(Dictionaryable, JsonSerializable, JsonDeserializable):
    """
    This object represents a parameter of the inline keyboard button used to automatically authorize a user. Serves as a great replacement for the Telegram Login Widget when the user is coming from Telegram. All the user needs to do is tap/click a button and confirm that they want to log in:

    Telegram Documentation: https://core.telegram.org/bots/api#loginurl

    :param url: An HTTPS URL to be opened with user authorization data added to the query string when the button is pressed. 
        If the user refuses to provide authorization data, the original URL without information about the user will be 
        opened. The data added is the same as described in Receiving authorization data. NOTE: You must always check the hash 
        of the received data to verify the authentication and the integrity of the data as described in Checking 
        authorization.
    :type url: :obj:`str`

    :param forward_text: Optional. New text of the button in forwarded messages.
    :type forward_text: :obj:`str`

    :param bot_username: Optional. Username of a bot, which will be used for user authorization. See Setting up a bot for 
        more details. If not specified, the current bot's username will be assumed. The url's domain must be the same as the 
        domain linked with the bot. See Linking your domain to the bot for more details.
    :type bot_username: :obj:`str`

    :param request_write_access: Optional. Pass True to request the permission for your bot to send messages to the 
        user.
    :type request_write_access: :obj:`bool`

    :return: Instance of the class
    :rtype: :class:`telebot.types.LoginUrl`
    """
    @classmethod
    def de_json(cls, json_string):
        if json_string is None: return None
        obj = cls.check_json(json_string, dict_copy=False)
        return cls(**obj)

    def __init__(self, url: str, forward_text: Optional[str]=None, bot_username: Optional[str]=None, request_write_access: Optional[bool]=None,
            **kwargs):
        self.url: str = url
        self.forward_text: Optional[str] = forward_text
        self.bot_username: Optional[str] = bot_username
        self.request_write_access: Optional[bool] = request_write_access

    def to_json(self):
        return json.dumps(self.to_dict())

    def to_dict(self):
        json_dict = {'url': self.url}
        if self.forward_text:
            json_dict['forward_text'] = self.forward_text
        if self.bot_username:
            json_dict['bot_username'] = self.bot_username
        if self.request_write_access is not None:
            json_dict['request_write_access'] = self.request_write_access
        return json_dict


# noinspection PyShadowingBuiltins
class CallbackQuery(JsonDeserializable):
    """
    This object represents an incoming callback query from a callback button in an inline keyboard. If the button that originated the query was attached to a message sent by the bot, the field message will be present. If the button was attached to a message sent via the bot (in inline mode), the field inline_message_id will be present. Exactly one of the fields data or game_short_name will be present.

    Telegram Documentation: https://core.telegram.org/bots/api#callbackquery

    :param id: Unique identifier for this query
    :type id: :obj:`str`

    :param from_user: Sender
    :type from_user: :class:`telebot.types.User`

    :param message: Optional. Message sent by the bot with the callback button that originated the query
    :type message: :class:`telebot.types.Message` or :class:`telebot.types.InaccessibleMessage`

    :param inline_message_id: Optional. Identifier of the message sent via the bot in inline mode, that originated the 
        query.
    :type inline_message_id: :obj:`str`

    :param chat_instance: Global identifier, uniquely corresponding to the chat to which the message with the callback 
        button was sent. Useful for high scores in games.
    :type chat_instance: :obj:`str`

    :param data: Optional. Data associated with the callback button. Be aware that the message originated the query can 
        contain no callback buttons with this data.
    :type data: :obj:`str`

    :param game_short_name: Optional. Short name of a Game to be returned, serves as the unique identifier for the game
    :type game_short_name: :obj:`str`

    :return: Instance of the class
    :rtype: :class:`telebot.types.CallbackQuery`
    """
    @classmethod
    def de_json(cls, json_string):
        if json_string is None: return None
        obj = cls.check_json(json_string)
        if not "data" in obj:
            # "data" field is Optional in the API, but historically is mandatory in the class constructor
            obj['data'] = None
        obj['from_user'] = User.de_json(obj.pop('from'))
        if 'message' in obj:
            message = obj['message']
            if message['date'] == 0:
                # date.	Always 0. The field can be used to differentiate regular and inaccessible messages.
                obj['message'] = InaccessibleMessage.de_json(message)
            else:
                obj['message'] = Message.de_json(message)
        obj['json_string'] = json_string
        return cls(**obj)

    def __init__(
            self, id, from_user, data, chat_instance, json_string, message=None, inline_message_id=None,
            game_short_name=None, **kwargs):
        self.id: int = id
        self.from_user: User = from_user
        self.message: Union[Message, InaccessibleMessage] = message
        self.inline_message_id: Optional[str] = inline_message_id
        self.chat_instance: Optional[str] = chat_instance
        self.data: Optional[str] = data
        self.game_short_name: Optional[str] = game_short_name
        self.json = json_string
        
        
class ChatPhoto(JsonDeserializable):
    """
    This object represents a chat photo.

    Telegram Documentation: https://core.telegram.org/bots/api#chatphoto

    :param small_file_id: File identifier of small (160x160) chat photo. This file_id can be used only for photo 
        download and only for as long as the photo is not changed.
    :type small_file_id: :obj:`str`

    :param small_file_unique_id: Unique file identifier of small (160x160) chat photo, which is supposed to be the same 
        over time and for different bots. Can't be used to download or reuse the file.
    :type small_file_unique_id: :obj:`str`

    :param big_file_id: File identifier of big (640x640) chat photo. This file_id can be used only for photo download and 
        only for as long as the photo is not changed.
    :type big_file_id: :obj:`str`

    :param big_file_unique_id: Unique file identifier of big (640x640) chat photo, which is supposed to be the same over 
        time and for different bots. Can't be used to download or reuse the file.
    :type big_file_unique_id: :obj:`str`

    :return: Instance of the class
    :rtype: :class:`telebot.types.ChatPhoto`
    """
    @classmethod
    def de_json(cls, json_string):
        if json_string is None: return None
        obj = cls.check_json(json_string, dict_copy=False)
        return cls(**obj)

    def __init__(self, small_file_id, small_file_unique_id, big_file_id, big_file_unique_id, **kwargs):
        self.small_file_id: str = small_file_id
        self.small_file_unique_id: str = small_file_unique_id
        self.big_file_id: str = big_file_id
        self.big_file_unique_id: str = big_file_unique_id


class ChatMember(JsonDeserializable):
    """
    This object contains information about one member of a chat.
    Currently, the following 6 types of chat members are supported:
    
    * :class:`telebot.types.ChatMemberOwner`
    * :class:`telebot.types.ChatMemberAdministrator`
    * :class:`telebot.types.ChatMemberMember`
    * :class:`telebot.types.ChatMemberRestricted`
    * :class:`telebot.types.ChatMemberLeft`
    * :class:`telebot.types.ChatMemberBanned`

    Telegram Documentation: https://core.telegram.org/bots/api#chatmember
    """

    @classmethod
    def de_json(cls, json_string):
        if json_string is None: return None
        obj = cls.check_json(json_string)
        obj['user'] = User.de_json(obj['user'])
        member_type = obj['status']
        # Ordered according to estimated appearance frequency.
        if member_type == "member":
            return ChatMemberMember(**obj)
        elif member_type == "left":
            return ChatMemberLeft(**obj)
        elif member_type == "kicked":
            return ChatMemberBanned(**obj)
        elif member_type == "restricted":
            return ChatMemberRestricted(**obj)
        elif member_type == "administrator":
            return ChatMemberAdministrator(**obj)
        elif member_type == "creator":
            return ChatMemberOwner(**obj)
        else:
            # Should not be here. For "if something happen" compatibility
            return cls(**obj)

    def __init__(self, user, status, custom_title=None, is_anonymous=None, can_be_edited=None,
                 can_post_messages=None, can_edit_messages=None, can_delete_messages=None,
                 can_restrict_members=None, can_promote_members=None, can_change_info=None,
                 can_invite_users=None,  can_pin_messages=None, is_member=None,
                 can_send_messages=None, can_send_audios=None, can_send_documents=None,
                 can_send_photos=None, can_send_videos=None, can_send_video_notes=None,
                 can_send_voice_notes=None,
                 can_send_polls=None,
                 can_send_other_messages=None, can_add_web_page_previews=None,  
                 can_manage_chat=None, can_manage_video_chats=None, 
                 until_date=None, can_manage_topics=None, 
                 can_post_stories=None, can_edit_stories=None, can_delete_stories=None,
                 **kwargs):
        self.user: User = user
        self.status: str = status
        self.custom_title: str = custom_title
        self.is_anonymous: bool = is_anonymous 
        self.can_be_edited: bool = can_be_edited
        self.can_post_messages: bool = can_post_messages
        self.can_edit_messages: bool = can_edit_messages
        self.can_delete_messages: bool = can_delete_messages
        self.can_restrict_members: bool = can_restrict_members
        self.can_promote_members: bool = can_promote_members
        self.can_change_info: bool = can_change_info
        self.can_invite_users: bool = can_invite_users
        self.can_pin_messages: bool = can_pin_messages
        self.is_member: bool = is_member
        self.can_send_messages: bool = can_send_messages
        self.can_send_polls: bool = can_send_polls
        self.can_send_other_messages: bool = can_send_other_messages
        self.can_add_web_page_previews: bool = can_add_web_page_previews
        self.can_manage_chat: bool = can_manage_chat
        self.can_manage_video_chats: bool = can_manage_video_chats
        self.until_date: int = until_date
        self.can_manage_topics: bool = can_manage_topics
        self.can_send_audios: bool = can_send_audios
        self.can_send_documents: bool = can_send_documents
        self.can_send_photos: bool = can_send_photos
        self.can_send_videos: bool = can_send_videos
        self.can_send_video_notes: bool = can_send_video_notes
        self.can_send_voice_notes: bool = can_send_voice_notes
        self.can_post_stories: bool = can_post_stories
        self.can_edit_stories: bool = can_edit_stories
        self.can_delete_stories: bool = can_delete_stories

    @property
    def can_manage_voice_chats(self):
        log_deprecation_warning('The parameter "can_manage_voice_chats" is deprecated. Use "can_manage_video_chats" instead.')
        return self.can_manage_video_chats


# noinspection PyUnresolvedReferences
class ChatMemberOwner(ChatMember):
    """
    Represents a chat member that owns the chat and has all administrator privileges.

    Telegram Documentation: https://core.telegram.org/bots/api#chatmemberowner

    :param status: The member's status in the chat, always “creator”
    :type status: :obj:`str`

    :param user: Information about the user
    :type user: :class:`telebot.types.User`

    :param is_anonymous: True, if the user's presence in the chat is hidden
    :type is_anonymous: :obj:`bool`

    :param custom_title: Optional. Custom title for this user
    :type custom_title: :obj:`str`

    :return: Instance of the class
    :rtype: :class:`telebot.types.ChatMemberOwner`
    """
    pass


# noinspection PyUnresolvedReferences
class ChatMemberAdministrator(ChatMember):
    """
    Represents a chat member that has some additional privileges.

    Telegram Documentation: https://core.telegram.org/bots/api#chatmemberadministrator

    :param status: The member's status in the chat, always “administrator”
    :type status: :obj:`str`

    :param user: Information about the user
    :type user: :class:`telebot.types.User`

    :param can_be_edited: True, if the bot is allowed to edit administrator privileges of that user
    :type can_be_edited: :obj:`bool`

    :param is_anonymous: True, if the user's presence in the chat is hidden
    :type is_anonymous: :obj:`bool`

    :param can_manage_chat: True, if the administrator can access the chat event log, chat statistics, message 
        statistics in channels, see channel members, see anonymous administrators in supergroups and ignore slow mode. 
        Implied by any other administrator privilege
    :type can_manage_chat: :obj:`bool`

    :param can_delete_messages: True, if the administrator can delete messages of other users
    :type can_delete_messages: :obj:`bool`

    :param can_manage_video_chats: True, if the administrator can manage video chats
    :type can_manage_video_chats: :obj:`bool`

    :param can_restrict_members: True, if the administrator can restrict, ban or unban chat members
    :type can_restrict_members: :obj:`bool`

    :param can_promote_members: True, if the administrator can add new administrators with a subset of their own 
        privileges or demote administrators that he has promoted, directly or indirectly (promoted by administrators that 
        were appointed by the user)
    :type can_promote_members: :obj:`bool`

    :param can_change_info: True, if the user is allowed to change the chat title, photo and other settings
    :type can_change_info: :obj:`bool`

    :param can_invite_users: True, if the user is allowed to invite new users to the chat
    :type can_invite_users: :obj:`bool`

    :param can_post_messages: Optional. True, if the administrator can post in the channel; channels only
    :type can_post_messages: :obj:`bool`

    :param can_edit_messages: Optional. True, if the administrator can edit messages of other users and can pin 
        messages; channels only
    :type can_edit_messages: :obj:`bool`

    :param can_pin_messages: Optional. True, if the user is allowed to pin messages; groups and supergroups only
    :type can_pin_messages: :obj:`bool`

    :param can_manage_topics: Optional. True, if the user is allowed to create, rename, close, and reopen forum topics;
        supergroups only
    :type can_manage_topics: :obj:`bool`

    :param custom_title: Optional. Custom title for this user
    :type custom_title: :obj:`str`

    :param can_post_stories: Optional. True, if the administrator can post channel stories
    :type can_post_stories: :obj:`bool`

    :param can_edit_stories: Optional. True, if the administrator can edit stories
    :type can_edit_stories: :obj:`bool`

    :param can_delete_stories: Optional. True, if the administrator can delete stories of other users
    :type can_delete_stories: :obj:`bool`

    :return: Instance of the class
    :rtype: :class:`telebot.types.ChatMemberAdministrator`
    """
    pass


# noinspection PyUnresolvedReferences
class ChatMemberMember(ChatMember):
    """
    Represents a chat member that has no additional privileges or restrictions.

    Telegram Documentation: https://core.telegram.org/bots/api#chatmembermember

    :param status: The member's status in the chat, always “member”
    :type status: :obj:`str`

    :param user: Information about the user
    :type user: :class:`telebot.types.User`

    :return: Instance of the class
    :rtype: :class:`telebot.types.ChatMemberMember`
    """
    pass


# noinspection PyUnresolvedReferences
class ChatMemberRestricted(ChatMember):
    """
    Represents a chat member that is under certain restrictions in the chat. Supergroups only.

    Telegram Documentation: https://core.telegram.org/bots/api#chatmemberrestricted

    :param status: The member's status in the chat, always “restricted”
    :type status: :obj:`str`

    :param user: Information about the user
    :type user: :class:`telebot.types.User`

    :param is_member: True, if the user is a member of the chat at the moment of the request
    :type is_member: :obj:`bool`

    :param can_change_info: True, if the user is allowed to change the chat title, photo and other settings
    :type can_change_info: :obj:`bool`

    :param can_invite_users: True, if the user is allowed to invite new users to the chat
    :type can_invite_users: :obj:`bool`

    :param can_pin_messages: True, if the user is allowed to pin messages
    :type can_pin_messages: :obj:`bool`

    :param can_manage_topics: True, if the user is allowed to create forum topics
    :type can_manage_topics: :obj:`bool`

    :param can_send_messages: True, if the user is allowed to send text messages, contacts, locations and venues
    :type can_send_messages: :obj:`bool`

    :param can_send_audios: True, if the user is allowed to send audios
    :type can_send_audios: :obj:`bool`

    :param can_send_documents: True, if the user is allowed to send documents
    :type can_send_documents: :obj:`bool`

    :param can_send_photos: True, if the user is allowed to send photos
    :type can_send_photos: :obj:`bool`

    :param can_send_videos: True, if the user is allowed to send videos
    :type can_send_videos: :obj:`bool`

    :param can_send_video_notes: True, if the user is allowed to send video notes
    :type can_send_video_notes: :obj:`bool`

    :param can_send_voice_notes: True, if the user is allowed to send voice notes
    :type can_send_voice_notes: :obj:`bool`

    :param can_send_polls: True, if the user is allowed to send polls
    :type can_send_polls: :obj:`bool`

    :param can_send_other_messages: True, if the user is allowed to send animations, games, stickers and use inline 
        bots
    :type can_send_other_messages: :obj:`bool`

    :param can_add_web_page_previews: True, if the user is allowed to add web page previews to their messages
    :type can_add_web_page_previews: :obj:`bool`

    :param until_date: Date when restrictions will be lifted for this user; unix time. If 0, then the user is restricted 
        forever
    :type until_date: :obj:`int`

    :return: Instance of the class
    :rtype: :class:`telebot.types.ChatMemberRestricted`
    """
    pass


# noinspection PyUnresolvedReferences
class ChatMemberLeft(ChatMember):
    """
    Represents a chat member that isn't currently a member of the chat, but may join it themselves.

    Telegram Documentation: https://core.telegram.org/bots/api#chatmemberleft

    :param status: The member's status in the chat, always “left”
    :type status: :obj:`str`

    :param user: Information about the user
    :type user: :class:`telebot.types.User`

    :return: Instance of the class
    :rtype: :class:`telebot.types.ChatMemberLeft`
    """
    pass


# noinspection PyUnresolvedReferences
class ChatMemberBanned(ChatMember):
    """
    Represents a chat member that was banned in the chat and can't return to the chat or view chat messages.

    Telegram Documentation: https://core.telegram.org/bots/api#chatmemberbanned

    :param status: The member's status in the chat, always “kicked”
    :type status: :obj:`str`

    :param user: Information about the user
    :type user: :class:`telebot.types.User`

    :param until_date: Date when restrictions will be lifted for this user; unix time. If 0, then the user is banned 
        forever
    :type until_date: :obj:`int`

    :return: Instance of the class
    :rtype: :class:`telebot.types.ChatMemberBanned`
    """
    pass


class ChatPermissions(JsonDeserializable, JsonSerializable, Dictionaryable):
    """
    Describes actions that a non-administrator user is allowed to take in a chat.

    Telegram Documentation: https://core.telegram.org/bots/api#chatpermissions

    :param can_send_messages: Optional. True, if the user is allowed to send text messages, contacts, locations and 
        venues
    :type can_send_messages: :obj:`bool`

    :param can_send_audios: Optional. True, if the user is allowed to send audios
    :type can_send_audios: :obj:`bool`

    :param can_send_documents: Optional. True, if the user is allowed to send documents
    :type can_send_documents: :obj:`bool`

    :param can_send_photos: Optional. True, if the user is allowed to send photos
    :type can_send_photos: :obj:`bool`

    :param can_send_videos: Optional. True, if the user is allowed to send videos
    :type can_send_videos: :obj:`bool`

    :param can_send_video_notes: Optional. True, if the user is allowed to send video notes
    :type can_send_video_notes: :obj:`bool`

    :param can_send_voice_notes: Optional. True, if the user is allowed to send voice notes
    :type can_send_voice_notes: :obj:`bool`

    :param can_send_polls: Optional. True, if the user is allowed to send polls, implies can_send_messages
    :type can_send_polls: :obj:`bool`

    :param can_send_other_messages: Optional. True, if the user is allowed to send animations, games, stickers and use 
        inline bots
    :type can_send_other_messages: :obj:`bool`

    :param can_add_web_page_previews: Optional. True, if the user is allowed to add web page previews to their 
        messages
    :type can_add_web_page_previews: :obj:`bool`

    :param can_change_info: Optional. True, if the user is allowed to change the chat title, photo and other settings. 
        Ignored in public supergroups
    :type can_change_info: :obj:`bool`

    :param can_invite_users: Optional. True, if the user is allowed to invite new users to the chat
    :type can_invite_users: :obj:`bool`

    :param can_pin_messages: Optional. True, if the user is allowed to pin messages. Ignored in public supergroups
    :type can_pin_messages: :obj:`bool`

    :param can_manage_topics: Optional. True, if the user is allowed to create forum topics. If omitted defaults to the
        value of can_pin_messages
    :type can_manage_topics: :obj:`bool`    

    :param can_send_media_messages: deprecated.
    :type can_send_media_messages: :obj:`bool`

    :return: Instance of the class
    :rtype: :class:`telebot.types.ChatPermissions`
    """
    @classmethod
    def de_json(cls, json_string):
        if json_string is None: return None
        obj = cls.check_json(json_string, dict_copy=False)
        return cls(**obj, de_json = True)

    def __init__(self, can_send_messages=None, can_send_media_messages=None,can_send_audios=None,
                    can_send_documents=None, can_send_photos=None,
                    can_send_videos=None, can_send_video_notes=None,
                    can_send_voice_notes=None, can_send_polls=None, can_send_other_messages=None,
                    can_add_web_page_previews=None, can_change_info=None,
                    can_invite_users=None, can_pin_messages=None, 
                    can_manage_topics=None, **kwargs):
        self.can_send_messages: Optional[bool] = can_send_messages
        self.can_send_polls: Optional[bool] = can_send_polls
        self.can_send_other_messages: Optional[bool] = can_send_other_messages
        self.can_add_web_page_previews: Optional[bool] = can_add_web_page_previews
        self.can_change_info: Optional[bool] = can_change_info
        self.can_invite_users: Optional[bool] = can_invite_users
        self.can_pin_messages: Optional[bool] = can_pin_messages
        self.can_manage_topics: Optional[bool] = can_manage_topics
        self.can_send_audios: Optional[bool] = can_send_audios
        self.can_send_documents: Optional[bool] = can_send_documents
        self.can_send_photos: Optional[bool] = can_send_photos
        self.can_send_videos: Optional[bool] = can_send_videos
        self.can_send_video_notes: Optional[bool] = can_send_video_notes
        self.can_send_voice_notes: Optional[bool] = can_send_voice_notes

        if kwargs.get("de_json", False) and can_send_media_messages is not None:
            # Telegram passes can_send_media_messages in Chat.permissions. Temporary created parameter "de_json" allows avoid
            # deprection warning and individual parameters overriding.
            log_deprecation_warning('The parameter "can_send_media_messages" is deprecated. Use individual parameters like "can_send_audios", "can_send_documents" etc.')
            self.can_send_audios: Optional[bool] = can_send_media_messages
            self.can_send_documents: Optional[bool] = can_send_media_messages
            self.can_send_photos: Optional[bool] = can_send_media_messages
            self.can_send_videos: Optional[bool] = can_send_media_messages
            self.can_send_video_notes: Optional[bool] = can_send_media_messages
            self.can_send_voice_notes: Optional[bool] = can_send_media_messages


    def to_json(self):
        return json.dumps(self.to_dict())

    def to_dict(self):
        json_dict = dict()
        if self.can_send_messages is not None:
            json_dict['can_send_messages'] = self.can_send_messages
        if self.can_send_audios is not None:
            json_dict['can_send_audios'] = self.can_send_audios

        if self.can_send_documents is not None:
            json_dict['can_send_documents'] = self.can_send_documents
        if self.can_send_photos is not None:
            json_dict['can_send_photos'] = self.can_send_photos
        if self.can_send_videos is not None:
            json_dict['can_send_videos'] = self.can_send_videos
        if self.can_send_video_notes is not None:
            json_dict['can_send_video_notes'] = self.can_send_video_notes
        if self.can_send_voice_notes is not None:
            json_dict['can_send_voice_notes'] = self.can_send_voice_notes
        if self.can_send_polls is not None:
            json_dict['can_send_polls'] = self.can_send_polls
        if self.can_send_other_messages is not None:
            json_dict['can_send_other_messages'] = self.can_send_other_messages
        if self.can_add_web_page_previews is not None:
            json_dict['can_add_web_page_previews'] = self.can_add_web_page_previews
        if self.can_change_info is not None:
            json_dict['can_change_info'] = self.can_change_info
        if self.can_invite_users is not None:
            json_dict['can_invite_users'] = self.can_invite_users
        if self.can_pin_messages is not None:
            json_dict['can_pin_messages'] = self.can_pin_messages
        if self.can_manage_topics is not None:
            json_dict['can_manage_topics'] = self.can_manage_topics
        
        return json_dict


class BotCommand(JsonSerializable, JsonDeserializable, Dictionaryable):
    """
    This object represents a bot command.

    Telegram Documentation: https://core.telegram.org/bots/api#botcommand

    :param command: Text of the command; 1-32 characters. Can contain only lowercase English letters, digits and 
        underscores.
    :type command: :obj:`str`

    :param description: Description of the command; 1-256 characters.
    :type description: :obj:`str`

    :return: Instance of the class
    :rtype: :class:`telebot.types.BotCommand`
    """
    @classmethod
    def de_json(cls, json_string):
        if json_string is None: return None
        obj = cls.check_json(json_string, dict_copy=False)
        return cls(**obj)

    def __init__(self, command, description, **kwargs):
        self.command: str = command
        self.description: str = description

    def to_json(self):
        return json.dumps(self.to_dict())

    def to_dict(self):
        return {'command': self.command, 'description': self.description}


# BotCommandScopes

# noinspection PyShadowingBuiltins
class BotCommandScope(ABC, JsonSerializable):
    """
    This object represents the scope to which bot commands are applied. Currently, the following 7 scopes are supported:

    * :class:`BotCommandScopeDefault`
    * :class:`BotCommandScopeAllPrivateChats`
    * :class:`BotCommandScopeAllGroupChats`
    * :class:`BotCommandScopeAllChatAdministrators`
    * :class:`BotCommandScopeChat`
    * :class:`BotCommandScopeChatAdministrators`
    * :class:`BotCommandScopeChatMember`

    Determining list of commands
    The following algorithm is used to determine the list of commands for a particular user viewing the bot menu. The first list of commands which is set is returned:

    Commands in the chat with the bot:

    * :class:`BotCommandScopeChat` + language_code
    * :class:`BotCommandScopeChat`
    * :class:`BotCommandScopeAllPrivateChats` + language_code
    * :class:`BotCommandScopeAllPrivateChats`
    * :class:`BotCommandScopeDefault` + language_code
    * :class:`BotCommandScopeDefault`

    Commands in group and supergroup chats:

    * :class:`BotCommandScopeChatMember` + language_code
    * :class:`BotCommandScopeChatMember`
    * :class:`BotCommandScopeChatAdministrators` + language_code (administrators only)
    * :class:`BotCommandScopeChatAdministrators` (administrators only)
    * :class:`BotCommandScopeChat` + language_code
    * :class:`BotCommandScopeChat`
    * :class:`BotCommandScopeAllChatAdministrators` + language_code (administrators only)
    * :class:`BotCommandScopeAllChatAdministrators` (administrators only)
    * :class:`BotCommandScopeAllGroupChats` + language_code
    * :class:`BotCommandScopeAllGroupChats`
    * :class:`BotCommandScopeDefault` + language_code
    * :class:`BotCommandScopeDefault`

    :return: Instance of the class
    :rtype: :class:`telebot.types.BotCommandScope`
    """
    def __init__(self, type='default', chat_id=None, user_id=None):
        self.type: str = type
        self.chat_id: Optional[Union[int, str]] = chat_id
        self.user_id: Optional[Union[int, str]] = user_id

    def to_json(self):
        json_dict = {'type': self.type}
        if self.chat_id:
            json_dict['chat_id'] = self.chat_id
        if self.user_id:
            json_dict['user_id'] = self.user_id
        return json.dumps(json_dict)


# noinspection PyUnresolvedReferences
class BotCommandScopeDefault(BotCommandScope):
    """
    Represents the default scope of bot commands. Default commands are used if no commands with a narrower scope are specified for the user.

    Telegram Documentation: https://core.telegram.org/bots/api#botcommandscopedefault

    :param type: Scope type, must be default
    :type type: :obj:`str`

    :return: Instance of the class
    :rtype: :class:`telebot.types.BotCommandScopeDefault`
    """
    def __init__(self):
        """
        Represents the default scope of bot commands.
        Default commands are used if no commands with a narrower scope are specified for the user.
        """
        super(BotCommandScopeDefault, self).__init__(type='default')


# noinspection PyUnresolvedReferences
class BotCommandScopeAllPrivateChats(BotCommandScope):
    """
    Represents the scope of bot commands, covering all private chats.

    Telegram Documentation: https://core.telegram.org/bots/api#botcommandscopeallprivatechats

    :param type: Scope type, must be all_private_chats
    :type type: :obj:`str`

    :return: Instance of the class
    :rtype: :class:`telebot.types.BotCommandScopeAllPrivateChats`
    """
    def __init__(self):
        """
        Represents the scope of bot commands, covering all private chats.
        """
        super(BotCommandScopeAllPrivateChats, self).__init__(type='all_private_chats')


# noinspection PyUnresolvedReferences
class BotCommandScopeAllGroupChats(BotCommandScope):
    """
    Represents the scope of bot commands, covering all group and supergroup chats.

    Telegram Documentation: https://core.telegram.org/bots/api#botcommandscopeallgroupchats

    :param type: Scope type, must be all_group_chats
    :type type: :obj:`str`

    :return: Instance of the class
    :rtype: :class:`telebot.types.BotCommandScopeAllGroupChats`
    """
    def __init__(self):
        """
        Represents the scope of bot commands, covering all group and supergroup chats.
        """
        super(BotCommandScopeAllGroupChats, self).__init__(type='all_group_chats')


# noinspection PyUnresolvedReferences
class BotCommandScopeAllChatAdministrators(BotCommandScope):
    """
    Represents the scope of bot commands, covering all group and supergroup chat administrators.

    Telegram Documentation: https://core.telegram.org/bots/api#botcommandscopeallchatadministrators

    :param type: Scope type, must be all_chat_administrators
    :type type: :obj:`str`

    :return: Instance of the class
    :rtype: :class:`telebot.types.BotCommandScopeAllChatAdministrators`
    """
    def __init__(self):
        """
        Represents the scope of bot commands, covering all group and supergroup chat administrators.
        """
        super(BotCommandScopeAllChatAdministrators, self).__init__(type='all_chat_administrators')


# noinspection PyUnresolvedReferences
class BotCommandScopeChat(BotCommandScope):
    """
    Represents the scope of bot commands, covering a specific chat.

    Telegram Documentation: https://core.telegram.org/bots/api#botcommandscopechat

    :param type: Scope type, must be chat
    :type type: :obj:`str`

    :param chat_id: Unique identifier for the target chat or username of the target supergroup (in the format 
        @supergroupusername)
    :type chat_id: :obj:`int` or :obj:`str`

    :return: Instance of the class
    :rtype: :class:`telebot.types.BotCommandScopeChat`
    """
    def __init__(self, chat_id: Optional[Union[str, int]]=None):
        super(BotCommandScopeChat, self).__init__(type='chat', chat_id=chat_id)


# noinspection PyUnresolvedReferences
class BotCommandScopeChatAdministrators(BotCommandScope):
    """
    Represents the scope of bot commands, covering all administrators of a specific group or supergroup chat.

    Telegram Documentation: https://core.telegram.org/bots/api#botcommandscopechatadministrators

    :param type: Scope type, must be chat_administrators
    :type type: :obj:`str`

    :param chat_id: Unique identifier for the target chat or username of the target supergroup (in the format 
        @supergroupusername)
    :type chat_id: :obj:`int` or :obj:`str`

    :return: Instance of the class
    :rtype: :class:`telebot.types.BotCommandScopeChatAdministrators`
    """
    def __init__(self, chat_id: Optional[Union[str, int]]=None):
        super(BotCommandScopeChatAdministrators, self).__init__(type='chat_administrators', chat_id=chat_id)


# noinspection PyUnresolvedReferences
class BotCommandScopeChatMember(BotCommandScope):
    """
    Represents the scope of bot commands, covering a specific member of a group or supergroup chat.

    Telegram Documentation: https://core.telegram.org/bots/api#botcommandscopechatmember

    :param type: Scope type, must be chat_member
    :type type: :obj:`str`

    :param chat_id: Unique identifier for the target chat or username of the target supergroup (in the format 
        @supergroupusername)
    :type chat_id: :obj:`int` or :obj:`str`

    :param user_id: Unique identifier of the target user
    :type user_id: :obj:`int`

    :return: Instance of the class
    :rtype: :class:`telebot.types.BotCommandScopeChatMember`
    """
    def __init__(self, chat_id: Optional[Union[str, int]]=None, user_id: Optional[Union[str, int]]=None):
        super(BotCommandScopeChatMember, self).__init__(type='chat_member', chat_id=chat_id, user_id=user_id)


# InlineQuery

# noinspection PyShadowingBuiltins
class InlineQuery(JsonDeserializable):
    """
    This object represents an incoming inline query. When the user sends an empty query, your bot could return some default or trending results.

    Telegram Documentation: https://core.telegram.org/bots/api#inlinequery

    :param id: Unique identifier for this query
    :type id: :obj:`str`

    :param from_user: Sender
    :type from_user: :class:`telebot.types.User`

    :param query: Text of the query (up to 256 characters)
    :type query: :obj:`str`

    :param offset: Offset of the results to be returned, can be controlled by the bot
    :type offset: :obj:`str`

    :param chat_type: Optional. Type of the chat from which the inline query was sent. Can be either “sender” for a private 
        chat with the inline query sender, “private”, “group”, “supergroup”, or “channel”. The chat type should be always 
        known for requests sent from official clients and most third-party clients, unless the request was sent from a secret 
        chat
    :type chat_type: :obj:`str`

    :param location: Optional. Sender location, only for bots that request user location
    :type location: :class:`telebot.types.Location`

    :return: Instance of the class
    :rtype: :class:`telebot.types.InlineQuery`
    """
    @classmethod
    def de_json(cls, json_string):
        if json_string is None: return None
        obj = cls.check_json(json_string)
        obj['from_user'] = User.de_json(obj.pop('from'))
        if 'location' in obj:
            obj['location'] = Location.de_json(obj['location'])
        return cls(**obj)

    def __init__(self, id, from_user, query, offset, chat_type=None, location=None, **kwargs):
        self.id: str = id
        self.from_user: User = from_user
        self.query: str = query
        self.offset: str = offset
        self.chat_type: Optional[str] = chat_type
        self.location: Optional[Location] = location


class InputTextMessageContent(Dictionaryable):
    """
    Represents the content of a text message to be sent as the result of an inline query.

    Telegram Documentation: https://core.telegram.org/bots/api#inputtextmessagecontent

    :param message_text: Text of the message to be sent, 1-4096 characters
    :type message_text: :obj:`str`

    :param parse_mode: Optional. Mode for parsing entities in the message text. See formatting options for more 
        details.
    :type parse_mode: :obj:`str`

    :param entities: Optional. List of special entities that appear in message text, which can be specified instead of 
        parse_mode
    :type entities: :obj:`list` of :class:`telebot.types.MessageEntity`

    :param disable_web_page_preview: deprecated
    :type disable_web_page_preview: :obj:`bool`

    :param link_preview_options: Optional. Link preview generation options for the message
    :type link_preview_options: :class:`telebot.types.LinkPreviewOptions`

    :return: Instance of the class
    :rtype: :class:`telebot.types.InputTextMessageContent`
    """
    def __init__(self, message_text: str, parse_mode: Optional[str] = None, entities: Optional[List[MessageEntity]] = None,
                    disable_web_page_preview: Optional[bool] = None, link_preview_options: Optional[LinkPreviewOptions] = None):
        self.message_text: str = message_text
        self.parse_mode: Optional[str] = parse_mode
        self.entities: Optional[List[MessageEntity]] = entities
        self.link_preview_options: Optional[LinkPreviewOptions] = link_preview_options
        if disable_web_page_preview is not None:
            log_deprecation_warning('The parameter "disable_web_page_preview" is deprecated. Use "link_preview_options" instead.')

            if link_preview_options:
                log_deprecation_warning('Both "link_preview_options" and "disable_web_page_preview" parameters are set: conflicting, "disable_web_page_preview" is deprecated')
            else:
                self.link_preview_options: Optional[LinkPreviewOptions] = LinkPreviewOptions(is_disabled=disable_web_page_preview)

    def to_dict(self):
        json_dict = {'message_text': self.message_text}
        if self.parse_mode:
            json_dict['parse_mode'] = self.parse_mode
        if self.entities:
            json_dict['entities'] = MessageEntity.to_list_of_dicts(self.entities)
        if self.link_preview_options:
            json_dict['link_preview_options'] = self.link_preview_options.to_dict()
        return json_dict


class InputLocationMessageContent(Dictionaryable):
    """
    Represents the content of a location message to be sent as the result of an inline query.

    Telegram Documentation: https://core.telegram.org/bots/api#inputlocationmessagecontent

    :param latitude: Latitude of the location in degrees
    :type latitude: :obj:`float`

    :param longitude: Longitude of the location in degrees
    :type longitude: :obj:`float`

    :param horizontal_accuracy: Optional. The radius of uncertainty for the location, measured in meters; 0-1500
    :type horizontal_accuracy: :obj:`float` number

    :param live_period: Optional. Period in seconds during which the location can be updated, should be between 60 and 86400, or 0x7FFFFFFF for live locations that can be edited indefinitely.
    :type live_period: :obj:`int`

    :param heading: Optional. For live locations, a direction in which the user is moving, in degrees. Must be between 1 and 360 if specified.
    :type heading: :obj:`int`

    :param proximity_alert_radius: Optional. For live locations, a maximum distance for proximity alerts about approaching another chat member, in meters. Must be between 1 and 100000 if specified.
    :type proximity_alert_radius: :obj:`int`

    :return: Instance of the class
    :rtype: :class:`telebot.types.InputLocationMessageContent`
    """
    def __init__(self, latitude, longitude, horizontal_accuracy=None, live_period=None, heading=None, proximity_alert_radius=None):
        self.latitude: float = latitude
        self.longitude: float = longitude
        self.horizontal_accuracy: Optional[float] = horizontal_accuracy
        self.live_period: Optional[int] = live_period
        self.heading: Optional[int] = heading
        self.proximity_alert_radius: Optional[int] = proximity_alert_radius

    def to_dict(self):
        json_dict = {'latitude': self.latitude, 'longitude': self.longitude}
        if self.horizontal_accuracy:
            json_dict['horizontal_accuracy'] = self.horizontal_accuracy
        if self.live_period:
            json_dict['live_period'] = self.live_period
        if self.heading:
            json_dict['heading'] = self.heading
        if self.proximity_alert_radius:
            json_dict['proximity_alert_radius'] = self.proximity_alert_radius
        return json_dict


class InputVenueMessageContent(Dictionaryable):
    """
    Represents the content of a venue message to be sent as the result of an inline query.

    Telegram Documentation: https://core.telegram.org/bots/api#inputvenuemessagecontent

    :param latitude: Latitude of the venue in degrees
    :type latitude: :obj:`float`

    :param longitude: Longitude of the venue in degrees
    :type longitude: :obj:`float`

    :param title: Name of the venue
    :type title: :obj:`str`

    :param address: Address of the venue
    :type address: :obj:`str`

    :param foursquare_id: Optional. Foursquare identifier of the venue, if known
    :type foursquare_id: :obj:`str`

    :param foursquare_type: Optional. Foursquare type of the venue, if known. (For example, 
        “arts_entertainment/default”, “arts_entertainment/aquarium” or “food/icecream”.)
    :type foursquare_type: :obj:`str`

    :param google_place_id: Optional. Google Places identifier of the venue
    :type google_place_id: :obj:`str`

    :param google_place_type: Optional. Google Places type of the venue. (See supported types.)
    :type google_place_type: :obj:`str`

    :return: Instance of the class
    :rtype: :class:`telebot.types.InputVenueMessageContent`
    """
    def __init__(self, latitude, longitude, title, address, foursquare_id=None, foursquare_type=None, 
                 google_place_id=None, google_place_type=None):
        self.latitude: float = latitude
        self.longitude: float = longitude
        self.title: str = title
        self.address: str = address
        self.foursquare_id: Optional[str] = foursquare_id
        self.foursquare_type: Optional[str] = foursquare_type
        self.google_place_id: Optional[str] = google_place_id
        self.google_place_type: Optional[str] = google_place_type

    def to_dict(self):
        json_dict = {
            'latitude': self.latitude,
            'longitude': self.longitude,
            'title': self.title,
            'address' : self.address
        }
        if self.foursquare_id:
            json_dict['foursquare_id'] = self.foursquare_id
        if self.foursquare_type:
            json_dict['foursquare_type'] = self.foursquare_type
        if self.google_place_id:
            json_dict['google_place_id'] = self.google_place_id
        if self.google_place_type:
            json_dict['google_place_type'] = self.google_place_type
        return json_dict


class InputContactMessageContent(Dictionaryable):
    """
    Represents the content of a contact message to be sent as the result of an inline query.

    Telegram Documentation: https://core.telegram.org/bots/api#inputcontactmessagecontent

    :param phone_number: Contact's phone number
    :type phone_number: :obj:`str`

    :param first_name: Contact's first name
    :type first_name: :obj:`str`

    :param last_name: Optional. Contact's last name
    :type last_name: :obj:`str`

    :param vcard: Optional. Additional data about the contact in the form of a vCard, 0-2048 bytes
    :type vcard: :obj:`str`

    :return: Instance of the class
    :rtype: :class:`telebot.types.InputContactMessageContent`
    """
    def __init__(self, phone_number, first_name, last_name=None, vcard=None):
        self.phone_number: str = phone_number
        self.first_name: str = first_name
        self.last_name: Optional[str] = last_name
        self.vcard: Optional[str] = vcard

    def to_dict(self):
        json_dict = {'phone_number': self.phone_number, 'first_name': self.first_name}
        if self.last_name:
            json_dict['last_name'] = self.last_name
        if self.vcard:
            json_dict['vcard'] = self.vcard
        return json_dict


class InputInvoiceMessageContent(Dictionaryable):
    """
    Represents the content of an invoice message to be sent as the result of an inline query.

    Telegram Documentation: https://core.telegram.org/bots/api#inputinvoicemessagecontent

    :param title: Product name, 1-32 characters
    :type title: :obj:`str`

    :param description: Product description, 1-255 characters
    :type description: :obj:`str`

    :param payload: Bot-defined invoice payload, 1-128 bytes. This will not be displayed to the user, use for your 
        internal processes.
    :type payload: :obj:`str`

    :param provider_token: Payment provider token, obtained via @BotFather; To create invoice in stars,
        provide an empty token.
    :type provider_token: :obj:`str` or :obj:`None`

    :param currency: Three-letter ISO 4217 currency code, see more on currencies
    :type currency: :obj:`str`

    :param prices: Price breakdown, a JSON-serialized list of components (e.g. product price, tax, discount, delivery 
        cost, delivery tax, bonus, etc.)
    :type prices: :obj:`list` of :class:`telebot.types.LabeledPrice`

    :param max_tip_amount: Optional. The maximum accepted amount for tips in the smallest units of the currency 
        (integer, not float/double). For example, for a maximum tip of US$ 1.45 pass max_tip_amount = 145. See the exp 
        parameter in currencies.json, it shows the number of digits past the decimal point for each currency (2 for the 
        majority of currencies). Defaults to 0
    :type max_tip_amount: :obj:`int`

    :param suggested_tip_amounts: Optional. A JSON-serialized array of suggested amounts of tip in the smallest units 
        of the currency (integer, not float/double). At most 4 suggested tip amounts can be specified. The suggested tip 
        amounts must be positive, passed in a strictly increased order and must not exceed max_tip_amount.
    :type suggested_tip_amounts: :obj:`list` of :obj:`int`

    :param provider_data: Optional. A JSON-serialized object for data about the invoice, which will be shared with the 
        payment provider. A detailed description of the required fields should be provided by the payment provider.
    :type provider_data: :obj:`str`

    :param photo_url: Optional. URL of the product photo for the invoice. Can be a photo of the goods or a marketing image 
        for a service.
    :type photo_url: :obj:`str`

    :param photo_size: Optional. Photo size in bytes
    :type photo_size: :obj:`int`

    :param photo_width: Optional. Photo width
    :type photo_width: :obj:`int`

    :param photo_height: Optional. Photo height
    :type photo_height: :obj:`int`

    :param need_name: Optional. Pass True, if you require the user's full name to complete the order
    :type need_name: :obj:`bool`

    :param need_phone_number: Optional. Pass True, if you require the user's phone number to complete the order
    :type need_phone_number: :obj:`bool`

    :param need_email: Optional. Pass True, if you require the user's email address to complete the order
    :type need_email: :obj:`bool`

    :param need_shipping_address: Optional. Pass True, if you require the user's shipping address to complete the 
        order
    :type need_shipping_address: :obj:`bool`

    :param send_phone_number_to_provider: Optional. Pass True, if the user's phone number should be sent to provider
    :type send_phone_number_to_provider: :obj:`bool`

    :param send_email_to_provider: Optional. Pass True, if the user's email address should be sent to provider
    :type send_email_to_provider: :obj:`bool`

    :param is_flexible: Optional. Pass True, if the final price depends on the shipping method
    :type is_flexible: :obj:`bool`

    :return: Instance of the class
    :rtype: :class:`telebot.types.InputInvoiceMessageContent`
    """
    
    def __init__(self, title: str, description: str, payload: str, provider_token: Optional[str], currency: str, prices: List[LabeledPrice],
                    max_tip_amount: Optional[int] = None, suggested_tip_amounts: Optional[List[int]] = None, provider_data: Optional[str] = None,
                    photo_url: Optional[str] = None, photo_size: Optional[int] = None, photo_width: Optional[int] = None, photo_height: Optional[int] = None,
                    need_name: Optional[bool] = None, need_phone_number: Optional[bool] = None, need_email: Optional[bool] = None, need_shipping_address: Optional[bool] = None,
                    send_phone_number_to_provider: Optional[bool] = None, send_email_to_provider: Optional[bool] = None, is_flexible: Optional[bool] = None):
        self.title: str = title
        self.description: str = description
        self.payload: str = payload
        self.provider_token: Optional[str] = provider_token
        self.currency: str = currency
        self.prices: List[LabeledPrice] = prices
        self.max_tip_amount: Optional[int] = max_tip_amount
        self.suggested_tip_amounts: Optional[List[int]] = suggested_tip_amounts
        self.provider_data: Optional[str] = provider_data
        self.photo_url: Optional[str] = photo_url
        self.photo_size: Optional[int] = photo_size
        self.photo_width: Optional[int] = photo_width
        self.photo_height: Optional[int] = photo_height
        self.need_name: Optional[bool] = need_name
        self.need_phone_number: Optional[bool] = need_phone_number
        self.need_email: Optional[bool] = need_email
        self.need_shipping_address: Optional[bool] = need_shipping_address
        self.send_phone_number_to_provider: Optional[bool] = send_phone_number_to_provider
        self.send_email_to_provider: Optional[bool] = send_email_to_provider
        self.is_flexible: Optional[bool] = is_flexible
    
    def to_dict(self):
        json_dict = {
            'title': self.title, 
            'description': self.description,
            'payload': self.payload,
            'provider_token': self.provider_token,
            'currency': self.currency,
            'prices': [LabeledPrice.to_dict(lp) for lp in self.prices]
        }
        if self.max_tip_amount:
            json_dict['max_tip_amount'] = self.max_tip_amount 
        if self.suggested_tip_amounts:
            json_dict['suggested_tip_amounts'] = self.suggested_tip_amounts 
        if self.provider_data:
            json_dict['provider_data'] = self.provider_data 
        if self.photo_url:
            json_dict['photo_url'] = self.photo_url 
        if self.photo_size:
            json_dict['photo_size'] = self.photo_size 
        if self.photo_width:
            json_dict['photo_width'] = self.photo_width 
        if self.photo_height:
            json_dict['photo_height'] = self.photo_height 
        if self.need_name is not None:
            json_dict['need_name'] = self.need_name 
        if self.need_phone_number is not None:
            json_dict['need_phone_number'] = self.need_phone_number 
        if self.need_email is not None:
            json_dict['need_email'] = self.need_email 
        if self.need_shipping_address is not None:
            json_dict['need_shipping_address'] = self.need_shipping_address 
        if self.send_phone_number_to_provider is not None:
            json_dict['send_phone_number_to_provider'] = self.send_phone_number_to_provider      
        if self.send_email_to_provider is not None:
            json_dict['send_email_to_provider'] = self.send_email_to_provider 
        if self.is_flexible is not None:
            json_dict['is_flexible'] = self.is_flexible 
        return json_dict

InputMessageContent = Union[InputTextMessageContent, InputLocationMessageContent, InputVenueMessageContent, InputContactMessageContent, InputInvoiceMessageContent]

class ChosenInlineResult(JsonDeserializable):
    """
    Represents a result of an inline query that was chosen by the user and sent to their chat partner.

    Telegram Documentation: https://core.telegram.org/bots/api#choseninlineresult

    :param result_id: The unique identifier for the result that was chosen
    :type result_id: :obj:`str`

    :param from: The user that chose the result
    :type from: :class:`telebot.types.User`

    :param location: Optional. Sender location, only for bots that require user location
    :type location: :class:`telebot.types.Location`

    :param inline_message_id: Optional. Identifier of the sent inline message. Available only if there is an inline 
        keyboard attached to the message. Will be also received in callback queries and can be used to edit the message.
    :type inline_message_id: :obj:`str`

    :param query: The query that was used to obtain the result
    :type query: :obj:`str`

    :return: Instance of the class
    :rtype: :class:`telebot.types.ChosenInlineResult`
    """
    @classmethod
    def de_json(cls, json_string):
        if json_string is None: return None
        obj = cls.check_json(json_string)
        obj['from_user'] = User.de_json(obj.pop('from'))
        if 'location' in obj:
            obj['location'] = Location.de_json(obj['location'])
        return cls(**obj)

    def __init__(self, result_id, from_user, query, location=None, inline_message_id=None, **kwargs):
        self.result_id: str = result_id
        self.from_user: User = from_user
        self.location: Optional[Location] = location
        self.inline_message_id: Optional[str] = inline_message_id
        self.query: str = query


# noinspection PyShadowingBuiltins
class InlineQueryResultBase(ABC, Dictionaryable, JsonSerializable):
    """
    This object represents one result of an inline query. Telegram clients currently support results of the following 20 types:

    * :class:`InlineQueryResultCachedAudio`
    * :class:`InlineQueryResultCachedDocument`
    * :class:`InlineQueryResultCachedGif`
    * :class:`InlineQueryResultCachedMpeg4Gif`
    * :class:`InlineQueryResultCachedPhoto`
    * :class:`InlineQueryResultCachedSticker`
    * :class:`InlineQueryResultCachedVideo`
    * :class:`InlineQueryResultCachedVoice`
    * :class:`InlineQueryResultArticle`
    * :class:`InlineQueryResultAudio`
    * :class:`InlineQueryResultContact`
    * :class:`InlineQueryResultGame`
    * :class:`InlineQueryResultDocument`
    * :class:`InlineQueryResultGif`
    * :class:`InlineQueryResultLocation`
    * :class:`InlineQueryResultMpeg4Gif`
    * :class:`InlineQueryResultPhoto`
    * :class:`InlineQueryResultVenue`
    * :class:`InlineQueryResultVideo`
    * :class:`InlineQueryResultVoice`

    Telegram Documentation: https://core.telegram.org/bots/api#inlinequeryresult
    """
    
    def __init__(self, type: str, id: str, title: Optional[str] = None, caption: Optional[str] = None, input_message_content: Optional[InputMessageContent] = None,
                    reply_markup: Optional[InlineKeyboardMarkup] = None, caption_entities: Optional[List[MessageEntity]] = None, parse_mode: Optional[str] = None):
        self.type: str = type
        self.id: str = id
        self.title: Optional[str] = title
        self.caption: Optional[str] = caption
        self.input_message_content: Optional[InputMessageContent] = input_message_content
        self.reply_markup: Optional[InlineKeyboardMarkup] = reply_markup
        self.caption_entities: Optional[List[MessageEntity]] = caption_entities
        self.parse_mode: Optional[str] = parse_mode

    def to_json(self):
        return json.dumps(self.to_dict())

    def to_dict(self):
        json_dict = {
            'type': self.type,
            'id': self.id
        }
        if self.title:
            json_dict['title'] = self.title
        if self.caption:
            json_dict['caption'] = self.caption
        if self.input_message_content:
            json_dict['input_message_content'] = self.input_message_content.to_dict()
        if self.reply_markup:
            json_dict['reply_markup'] = self.reply_markup.to_dict()
        if self.caption_entities:
            json_dict['caption_entities'] = MessageEntity.to_list_of_dicts(self.caption_entities)
        if self.parse_mode:
            json_dict['parse_mode'] = self.parse_mode
        return json_dict


class SentWebAppMessage(JsonDeserializable, Dictionaryable):
    """
    Describes an inline message sent by a Web App on behalf of a user.

    Telegram Documentation: https://core.telegram.org/bots/api#sentwebappmessage

    :param inline_message_id: Optional. Identifier of the sent inline message. Available only if there is an inline 
        keyboard attached to the message.
    :type inline_message_id: :obj:`str`

    :return: Instance of the class
    :rtype: :class:`telebot.types.SentWebAppMessage`
    """
    @classmethod
    def de_json(cls, json_string):
        if json_string is None: return None
        obj = cls.check_json(json_string)
        return cls(**obj)

    def __init__(self, inline_message_id=None, **kwargs):
        self.inline_message_id: Optional[str] = inline_message_id

    def to_dict(self):
        json_dict = {}
        if self.inline_message_id:
            json_dict['inline_message_id'] = self.inline_message_id
        return json_dict


# noinspection PyUnresolvedReferences,PyShadowingBuiltins
class InlineQueryResultArticle(InlineQueryResultBase):
    """
    Represents a link to an article or web page.

    Telegram Documentation: https://core.telegram.org/bots/api#inlinequeryresultarticle

    :param type: Type of the result, must be article
    :type type: :obj:`str`

    :param id: Unique identifier for this result, 1-64 Bytes
    :type id: :obj:`str`

    :param title: Title of the result
    :type title: :obj:`str`

    :param input_message_content: Content of the message to be sent
    :type input_message_content: :class:`telebot.types.InputMessageContent`

    :param reply_markup: Optional. Inline keyboard attached to the message
    :type reply_markup: :class:`telebot.types.InlineKeyboardMarkup`

    :param url: Optional. URL of the result
    :type url: :obj:`str`

    :param hide_url: Optional. Pass True, if you don't want the URL to be shown in the message
    :type hide_url: :obj:`bool`

    :param description: Optional. Short description of the result
    :type description: :obj:`str`

    :param thumbnail_url: Optional. Url of the thumbnail for the result
    :type thumbnail_url: :obj:`str`

    :param thumbnail_width: Optional. Thumbnail width
    :type thumbnail_width: :obj:`int`

    :param thumbnail_height: Optional. Thumbnail height
    :type thumbnail_height: :obj:`int`

    :return: Instance of the class
    :rtype: :class:`telebot.types.InlineQueryResultArticle`
    """
        
    def __init__(self, id: str, title: str, input_message_content: InputMessageContent, reply_markup: Optional[InlineKeyboardMarkup] = None,
                 url: Optional[str] = None, hide_url: Optional[bool] = None, description: Optional[str] = None,
                 thumbnail_url: Optional[str] = None, thumbnail_width: Optional[int] = None, thumbnail_height: Optional[int] = None):
                 
        super().__init__('article', id, title = title, input_message_content = input_message_content, reply_markup = reply_markup)
        self.url: Optional[str] = url
        self.hide_url: Optional[bool] = hide_url
        self.description: Optional[str] = description
        self.thumbnail_url: Optional[str] = thumbnail_url
        self.thumbnail_width: Optional[int] = thumbnail_width
        self.thumbnail_height: Optional[int] = thumbnail_height

        if hide_url:
            log_deprecation_warning('The parameter "hide_url" is deprecated. Pass an empty string as url instead.')
            self.url = ''


    @property
    def thumb_url(self) -> str:
        log_deprecation_warning('The parameter "thumb_url" is deprecated, use "thumbnail_url" instead')
        return self.thumbnail_url

    @property
    def thumb_width(self) -> int:
        log_deprecation_warning('The parameter "thumb_width" is deprecated, use "thumbnail_width" instead')
        return self.thumbnail_width

    @property
    def thumb_height(self) -> int:
        log_deprecation_warning('The parameter "thumb_height" is deprecated, use "thumbnail_height" instead')
        return self.thumbnail_height

    def to_dict(self):
        json_dict = super().to_dict()
        if self.url:
            json_dict['url'] = self.url
        if self.hide_url:
            json_dict['hide_url'] = self.hide_url
        if self.description:
            json_dict['description'] = self.description
        if self.thumbnail_url:
            json_dict['thumbnail_url'] = self.thumbnail_url
        if self.thumbnail_width:
            json_dict['thumbnail_width'] = self.thumbnail_width
        if self.thumbnail_height:
            json_dict['thumbnail_height'] = self.thumbnail_height
        return json_dict


# noinspection PyUnresolvedReferences,PyShadowingBuiltins
class InlineQueryResultPhoto(InlineQueryResultBase):
    """
    Represents a link to a photo. By default, this photo will be sent by the user with optional caption. Alternatively, you can use input_message_content to send a message with the specified content instead of the photo.

    Telegram Documentation: https://core.telegram.org/bots/api#inlinequeryresultphoto

    :param type: Type of the result, must be photo
    :type type: :obj:`str`

    :param id: Unique identifier for this result, 1-64 bytes
    :type id: :obj:`str`

    :param photo_url: A valid URL of the photo. Photo must be in JPEG format. Photo size must not exceed 5MB
    :type photo_url: :obj:`str`

    :param thumbnail_url: URL of the thumbnail for the photo
    :type thumbnail_url: :obj:`str`

    :param photo_width: Optional. Width of the photo
    :type photo_width: :obj:`int`

    :param photo_height: Optional. Height of the photo
    :type photo_height: :obj:`int`

    :param title: Optional. Title for the result
    :type title: :obj:`str`

    :param description: Optional. Short description of the result
    :type description: :obj:`str`

    :param caption: Optional. Caption of the photo to be sent, 0-1024 characters after entities parsing
    :type caption: :obj:`str`

    :param parse_mode: Optional. Mode for parsing entities in the photo caption. See formatting options for more 
        details.
    :type parse_mode: :obj:`str`

    :param caption_entities: Optional. List of special entities that appear in the caption, which can be specified 
        instead of parse_mode
    :type caption_entities: :obj:`list` of :class:`telebot.types.MessageEntity`

    :param reply_markup: Optional. Inline keyboard attached to the message
    :type reply_markup: :class:`telebot.types.InlineKeyboardMarkup`

    :param input_message_content: Optional. Content of the message to be sent instead of the photo
    :type input_message_content: :class:`telebot.types.InputMessageContent`

    :param show_caption_above_media: Optional. If true, a caption is shown over the photo or video
    :type show_caption_above_media: :obj:`bool`

    :return: Instance of the class
    :rtype: :class:`telebot.types.InlineQueryResultPhoto`
    """
    def __init__(self, id: str, photo_url: str, thumbnail_url: str, photo_width: Optional[int] = None, photo_height: Optional[int] = None,
                    title: Optional[str] = None, description: Optional[str] = None, caption: Optional[str] = None, caption_entities: Optional[List[MessageEntity]] = None,
                    parse_mode: Optional[str] = None, reply_markup: Optional[InlineKeyboardMarkup] = None, input_message_content: Optional[InputMessageContent] = None,
                    show_caption_above_media: Optional[bool] = None):
        super().__init__('photo', id, title = title, caption = caption,
                         input_message_content = input_message_content, reply_markup = reply_markup,
                         parse_mode = parse_mode, caption_entities = caption_entities)
        self.photo_url: str = photo_url
        self.thumbnail_url: str = thumbnail_url
        self.photo_width: Optional[int] = photo_width
        self.photo_height: Optional[int] = photo_height
        self.description: Optional[str] = description
        self.show_caption_above_media: Optional[bool] = show_caption_above_media


    @property
    def thumb_url(self) -> str:
        log_deprecation_warning('The parameter "thumb_url" is deprecated, use "thumbnail_url" instead')
        return self.thumbnail_url

    def to_dict(self):
        json_dict = super().to_dict()
        json_dict['photo_url'] = self.photo_url
        json_dict['thumbnail_url'] = self.thumbnail_url
        if self.photo_width:
            json_dict['photo_width'] = self.photo_width
        if self.photo_height:
            json_dict['photo_height'] = self.photo_height
        if self.description:
            json_dict['description'] = self.description
        if self.show_caption_above_media is not None:
            json_dict['show_caption_above_media'] = self.show_caption_above_media
        return json_dict


# noinspection PyUnresolvedReferences,PyShadowingBuiltins
class InlineQueryResultGif(InlineQueryResultBase):
    """
    Represents a link to an animated GIF file. By default, this animated GIF file will be sent by the user with optional caption. Alternatively, you can use input_message_content to send a message with the specified content instead of the animation.

    Telegram Documentation: https://core.telegram.org/bots/api#inlinequeryresultgif

    :param type: Type of the result, must be gif
    :type type: :obj:`str`

    :param id: Unique identifier for this result, 1-64 bytes
    :type id: :obj:`str`

    :param gif_url: A valid URL for the GIF file. File size must not exceed 1MB
    :type gif_url: :obj:`str`

    :param gif_width: Optional. Width of the GIF
    :type gif_width: :obj:`int`

    :param gif_height: Optional. Height of the GIF
    :type gif_height: :obj:`int`

    :param gif_duration: Optional. Duration of the GIF in seconds
    :type gif_duration: :obj:`int`

    :param thumbnail_url: URL of the static (JPEG or GIF) or animated (MPEG4) thumbnail for the result
    :type thumbnail_url: :obj:`str`

    :param thumbnail_mime_type: Optional. MIME type of the thumbnail, must be one of “image/jpeg”, “image/gif”, or 
        “video/mp4”. Defaults to “image/jpeg”
    :type thumbnail_mime_type: :obj:`str`

    :param title: Optional. Title for the result
    :type title: :obj:`str`

    :param caption: Optional. Caption of the GIF file to be sent, 0-1024 characters after entities parsing
    :type caption: :obj:`str`

    :param parse_mode: Optional. Mode for parsing entities in the caption. See formatting options for more details.
    :type parse_mode: :obj:`str`

    :param caption_entities: Optional. List of special entities that appear in the caption, which can be specified 
        instead of parse_mode
    :type caption_entities: :obj:`list` of :class:`telebot.types.MessageEntity`

    :param reply_markup: Optional. Inline keyboard attached to the message
    :type reply_markup: :class:`telebot.types.InlineKeyboardMarkup`

    :param input_message_content: Optional. Content of the message to be sent instead of the GIF animation
    :type input_message_content: :class:`telebot.types.InputMessageContent`

    :param show_caption_above_media: Optional. If true, a caption is shown over the photo or video
    :type show_caption_above_media: :obj:`bool`

    :return: Instance of the class
    :rtype: :class:`telebot.types.InlineQueryResultGif`
    """
    def __init__(self, id: str, gif_url: str, thumbnail_url: str, gif_width: Optional[int] = None, gif_height: Optional[int] = None,
                    title: Optional[str] = None, caption: Optional[str] = None, caption_entities: Optional[List[MessageEntity]] = None,
                    reply_markup: Optional[InlineKeyboardMarkup] = None, input_message_content: Optional[InputMessageContent] = None,
                    gif_duration: Optional[int] = None, parse_mode: Optional[str] = None, thumbnail_mime_type: Optional[str] = None,
                    show_caption_above_media: Optional[bool] = None):
        
        super().__init__('gif', id, title = title, caption = caption,
                         input_message_content = input_message_content, reply_markup = reply_markup,
                         parse_mode = parse_mode, caption_entities = caption_entities)
        self.gif_url: str = gif_url
        self.thumbnail_url: str = thumbnail_url
        self.gif_width: Optional[int] = gif_width
        self.gif_height: Optional[int] = gif_height
        self.gif_duration: Optional[int] = gif_duration
        self.thumbnail_mime_type: Optional[str] = thumbnail_mime_type
        self.show_caption_above_media: Optional[bool] = show_caption_above_media

    @property
    def thumb_url(self) -> str:
        log_deprecation_warning('The parameter "thumb_url" is deprecated, use "thumbnail_url" instead')
        return self.thumbnail_url

    @property
    def thumb_mime_type(self) -> str:
        log_deprecation_warning('The parameter "thumb_mime_type" is deprecated, use "thumbnail_mime_type" instead')
        return self.thumbnail_mime_type

    def to_dict(self):
        json_dict = super().to_dict()
        json_dict['gif_url'] = self.gif_url
        if self.gif_width:
            json_dict['gif_width'] = self.gif_width
        if self.gif_height:
            json_dict['gif_height'] = self.gif_height
        json_dict['thumbnail_url'] = self.thumbnail_url
        if self.gif_duration:
            json_dict['gif_duration'] = self.gif_duration
        if self.thumbnail_mime_type:
            json_dict['thumbnail_mime_type'] = self.thumbnail_mime_type
        if self.show_caption_above_media is not None:
            json_dict['show_caption_above_media'] = self.show_caption_above_media
        return json_dict


# noinspection PyUnresolvedReferences,PyShadowingBuiltins
class InlineQueryResultMpeg4Gif(InlineQueryResultBase):
    """
    Represents a link to a video animation (H.264/MPEG-4 AVC video without sound). By default, this animated MPEG-4 file will be sent by the user with optional caption. Alternatively, you can use input_message_content to send a message with the specified content instead of the animation.

    Telegram Documentation: https://core.telegram.org/bots/api#inlinequeryresultmpeg4gif

    :param type: Type of the result, must be mpeg4_gif
    :type type: :obj:`str`

    :param id: Unique identifier for this result, 1-64 bytes
    :type id: :obj:`str`

    :param mpeg4_url: A valid URL for the MPEG4 file. File size must not exceed 1MB
    :type mpeg4_url: :obj:`str`

    :param mpeg4_width: Optional. Video width
    :type mpeg4_width: :obj:`int`

    :param mpeg4_height: Optional. Video height
    :type mpeg4_height: :obj:`int`

    :param mpeg4_duration: Optional. Video duration in seconds
    :type mpeg4_duration: :obj:`int`

    :param thumbnail_url: URL of the static (JPEG or GIF) or animated (MPEG4) thumbnail for the result
    :type thumbnail_url: :obj:`str`

    :param thumbnail_mime_type: Optional. MIME type of the thumbnail, must be one of “image/jpeg”, “image/gif”, or 
        “video/mp4”. Defaults to “image/jpeg”
    :type thumbnail_mime_type: :obj:`str`

    :param title: Optional. Title for the result
    :type title: :obj:`str`

    :param caption: Optional. Caption of the MPEG-4 file to be sent, 0-1024 characters after entities parsing
    :type caption: :obj:`str`

    :param parse_mode: Optional. Mode for parsing entities in the caption. See formatting options for more details.
    :type parse_mode: :obj:`str`

    :param caption_entities: Optional. List of special entities that appear in the caption, which can be specified 
        instead of parse_mode
    :type caption_entities: :obj:`list` of :class:`telebot.types.MessageEntity`

    :param reply_markup: Optional. Inline keyboard attached to the message
    :type reply_markup: :class:`telebot.types.InlineKeyboardMarkup`

    :param input_message_content: Optional. Content of the message to be sent instead of the video animation
    :type input_message_content: :class:`telebot.types.InputMessageContent`

    :param show_caption_above_media: Optional. If true, a caption is shown over the photo or video
    :type show_caption_above_media: :obj:`bool`

    :return: Instance of the class
    :rtype: :class:`telebot.types.InlineQueryResultMpeg4Gif`
    """
    def __init__(self, id: str, mpeg4_url: str, thumbnail_url: str, mpeg4_width: Optional[int] = None, mpeg4_height: Optional[int] = None,
                    title: Optional[str] = None, caption: Optional[str] = None, caption_entities: Optional[List[MessageEntity]] = None,
                    parse_mode: Optional[str] = None, reply_markup: Optional[InlineKeyboardMarkup] = None, input_message_content: Optional[InputMessageContent] = None,
                    mpeg4_duration: Optional[int] = None, thumbnail_mime_type: Optional[str] = None, show_caption_above_media: Optional[bool] = None):
        
        super().__init__('mpeg4_gif', id, title = title, caption = caption,
                         input_message_content = input_message_content, reply_markup = reply_markup,
                         parse_mode = parse_mode, caption_entities = caption_entities)
        self.mpeg4_url: str = mpeg4_url
        self.thumbnail_url: str = thumbnail_url
        self.mpeg4_width: Optional[int] = mpeg4_width
        self.mpeg4_height: Optional[int] = mpeg4_height
        self.mpeg4_duration: Optional[int] = mpeg4_duration
        self.thumbnail_mime_type: Optional[str] = thumbnail_mime_type
        self.show_caption_above_media: Optional[bool] = show_caption_above_media

    @property
    def thumb_url(self) -> str:
        log_deprecation_warning('The parameter "thumb_url" is deprecated, use "thumbnail_url" instead')
        return self.thumbnail_url

    @property
    def thumb_mime_type(self) -> str:
        log_deprecation_warning('The parameter "thumb_mime_type" is deprecated, use "thumbnail_mime_type" instead')
        return self.thumbnail_mime_type

    def to_dict(self):
        json_dict = super().to_dict()
        json_dict['mpeg4_url'] = self.mpeg4_url
        if self.mpeg4_width:
            json_dict['mpeg4_width'] = self.mpeg4_width
        if self.mpeg4_height:
            json_dict['mpeg4_height'] = self.mpeg4_height
        json_dict['thumbnail_url'] = self.thumbnail_url
        if self.mpeg4_duration:
            json_dict['mpeg4_duration '] = self.mpeg4_duration
        if self.thumbnail_mime_type:
            json_dict['thumbnail_mime_type'] = self.thumbnail_mime_type
        if self.show_caption_above_media is not None:
            json_dict['show_caption_above_media'] = self.show_caption_above_media
        return json_dict


# noinspection PyUnresolvedReferences,PyShadowingBuiltins
class InlineQueryResultVideo(InlineQueryResultBase):
    """
    Represents a link to a page containing an embedded video player or a video file. By default, this video file will be sent by the user with an optional caption. Alternatively, you can use input_message_content to send a message with the specified content instead of the video.

    Telegram Documentation: https://core.telegram.org/bots/api#inlinequeryresultvideo

    :param type: Type of the result, must be video
    :type type: :obj:`str`

    :param id: Unique identifier for this result, 1-64 bytes
    :type id: :obj:`str`

    :param video_url: A valid URL for the embedded video player or video file
    :type video_url: :obj:`str`

    :param mime_type: MIME type of the content of the video URL, “text/html” or “video/mp4”
    :type mime_type: :obj:`str`

    :param thumbnail_url: URL of the thumbnail (JPEG only) for the video
    :type thumbnail_url: :obj:`str`

    :param title: Title for the result
    :type title: :obj:`str`

    :param caption: Optional. Caption of the video to be sent, 0-1024 characters after entities parsing
    :type caption: :obj:`str`

    :param parse_mode: Optional. Mode for parsing entities in the video caption. See formatting options for more 
        details.
    :type parse_mode: :obj:`str`

    :param caption_entities: Optional. List of special entities that appear in the caption, which can be specified 
        instead of parse_mode
    :type caption_entities: :obj:`list` of :class:`telebot.types.MessageEntity`

    :param video_width: Optional. Video width
    :type video_width: :obj:`int`

    :param video_height: Optional. Video height
    :type video_height: :obj:`int`

    :param video_duration: Optional. Video duration in seconds
    :type video_duration: :obj:`int`

    :param description: Optional. Short description of the result
    :type description: :obj:`str`

    :param reply_markup: Optional. Inline keyboard attached to the message
    :type reply_markup: :class:`telebot.types.InlineKeyboardMarkup`

    :param input_message_content: Optional. Content of the message to be sent instead of the video. This field is 
        required if InlineQueryResultVideo is used to send an HTML-page as a result (e.g., a YouTube video).
    :type input_message_content: :class:`telebot.types.InputMessageContent`

    :param show_caption_above_media: Optional. If true, a caption is shown over the video
    :type show_caption_above_media: :obj:`bool`

    :return: Instance of the class
    :rtype: :class:`telebot.types.InlineQueryResultVideo`
    """
    def __init__(self, id: str, video_url: str, mime_type: str, thumbnail_url: str, title: str,
                 caption: Optional[str] = None, caption_entities: Optional[List[MessageEntity]] = None,
                 parse_mode: Optional[str] = None, video_width: Optional[int] = None, video_height: Optional[int] = None,
                 video_duration: Optional[int] = None, description: Optional[str] = None, reply_markup: Optional[InlineKeyboardMarkup] = None,
                 input_message_content: Optional[InputMessageContent] = None, show_caption_above_media: Optional[bool] = None):
        
        super().__init__('video', id, title = title, caption = caption,
                         input_message_content = input_message_content, reply_markup = reply_markup,
                         parse_mode = parse_mode, caption_entities = caption_entities)
        self.video_url: str = video_url
        self.mime_type: str = mime_type
        self.thumbnail_url: str = thumbnail_url
        self.video_width: Optional[int] = video_width
        self.video_height: Optional[int] = video_height
        self.video_duration: Optional[int] = video_duration
        self.description: Optional[str] = description
        self.show_caption_above_media: Optional[bool] = show_caption_above_media

    @property
    def thumb_url(self) -> str:
        log_deprecation_warning('The parameter "thumb_url" is deprecated, use "thumbnail_url" instead')
        return self.thumbnail_url

    def to_dict(self):
        json_dict = super().to_dict()
        json_dict['video_url'] = self.video_url
        json_dict['mime_type'] = self.mime_type
        json_dict['thumbnail_url'] = self.thumbnail_url
        if self.video_height:
            json_dict['video_height'] = self.video_height
        if self.video_duration:
            json_dict['video_duration'] = self.video_duration
        if self.description:
            json_dict['description'] = self.description
        if self.show_caption_above_media is not None:
            json_dict['show_caption_above_media'] = self.show_caption_above_media
        return json_dict


# noinspection PyUnresolvedReferences,PyShadowingBuiltins
class InlineQueryResultAudio(InlineQueryResultBase):
    """
    Represents a link to an MP3 audio file. By default, this audio file will be sent by the user. Alternatively, you can use input_message_content to send a message with the specified content instead of the audio.

    Telegram Documentation: https://core.telegram.org/bots/api#inlinequeryresultaudio

    :param type: Type of the result, must be audio
    :type type: :obj:`str`

    :param id: Unique identifier for this result, 1-64 bytes
    :type id: :obj:`str`

    :param audio_url: A valid URL for the audio file
    :type audio_url: :obj:`str`

    :param title: Title
    :type title: :obj:`str`

    :param caption: Optional. Caption, 0-1024 characters after entities parsing
    :type caption: :obj:`str`

    :param parse_mode: Optional. Mode for parsing entities in the audio caption. See formatting options for more 
        details.
    :type parse_mode: :obj:`str`

    :param caption_entities: Optional. List of special entities that appear in the caption, which can be specified 
        instead of parse_mode
    :type caption_entities: :obj:`list` of :class:`telebot.types.MessageEntity`

    :param performer: Optional. Performer
    :type performer: :obj:`str`

    :param audio_duration: Optional. Audio duration in seconds
    :type audio_duration: :obj:`int`

    :param reply_markup: Optional. Inline keyboard attached to the message
    :type reply_markup: :class:`telebot.types.InlineKeyboardMarkup`

    :param input_message_content: Optional. Content of the message to be sent instead of the audio
    :type input_message_content: :class:`telebot.types.InputMessageContent`

    :return: Instance of the class
    :rtype: :class:`telebot.types.InlineQueryResultAudio`
    """
    def __init__(self, id: str, audio_url: str, title: str, caption: Optional[str] = None, caption_entities: Optional[List[MessageEntity]] = None,
                 parse_mode: Optional[str] = None, performer: Optional[str] = None, audio_duration: Optional[int] = None,
                 reply_markup: Optional[InlineKeyboardMarkup] = None, input_message_content: Optional[InputMessageContent] = None):
        
        super().__init__('audio', id, title = title, caption = caption,
                         input_message_content = input_message_content, reply_markup = reply_markup,
                         parse_mode = parse_mode, caption_entities = caption_entities)
        self.audio_url: str = audio_url
        self.performer: Optional[str] = performer
        self.audio_duration: Optional[int] = audio_duration

    def to_dict(self):
        json_dict = super().to_dict()
        json_dict['audio_url'] = self.audio_url
        if self.performer:
            json_dict['performer'] = self.performer
        if self.audio_duration:
            json_dict['audio_duration'] = self.audio_duration
        return json_dict


# noinspection PyUnresolvedReferences,PyShadowingBuiltins
class InlineQueryResultVoice(InlineQueryResultBase):
    """
    Represents a link to a voice recording in an .OGG container encoded with OPUS. By default, this voice recording will be sent by the user. Alternatively, you can use input_message_content to send a message with the specified content instead of the the voice message.

    Telegram Documentation: https://core.telegram.org/bots/api#inlinequeryresultvoice

    :param type: Type of the result, must be voice
    :type type: :obj:`str`

    :param id: Unique identifier for this result, 1-64 bytes
    :type id: :obj:`str`

    :param voice_url: A valid URL for the voice recording
    :type voice_url: :obj:`str`

    :param title: Recording title
    :type title: :obj:`str`

    :param caption: Optional. Caption, 0-1024 characters after entities parsing
    :type caption: :obj:`str`

    :param parse_mode: Optional. Mode for parsing entities in the voice message caption. See formatting options for 
        more details.
    :type parse_mode: :obj:`str`

    :param caption_entities: Optional. List of special entities that appear in the caption, which can be specified 
        instead of parse_mode
    :type caption_entities: :obj:`list` of :class:`telebot.types.MessageEntity`

    :param voice_duration: Optional. Recording duration in seconds
    :type voice_duration: :obj:`int`

    :param reply_markup: Optional. Inline keyboard attached to the message
    :type reply_markup: :class:`telebot.types.InlineKeyboardMarkup`

    :param input_message_content: Optional. Content of the message to be sent instead of the voice recording
    :type input_message_content: :class:`telebot.types.InputMessageContent`

    :return: Instance of the class
    :rtype: :class:`telebot.types.InlineQueryResultVoice`
    """
    def __init__(self, id: str, voice_url: str, title: str, caption: Optional[str] = None, caption_entities: Optional[List[MessageEntity]] = None,
                    parse_mode: Optional[str] = None, voice_duration: Optional[int] = None, reply_markup: Optional[InlineKeyboardMarkup] = None,
                    input_message_content: Optional[InputMessageContent] = None):
        
        super().__init__('voice', id, title = title, caption = caption,
                         input_message_content = input_message_content, reply_markup = reply_markup,
                         parse_mode = parse_mode, caption_entities = caption_entities)
        self.voice_url: str = voice_url
        self.voice_duration: Optional[int] = voice_duration

    def to_dict(self):
        json_dict = super().to_dict()
        json_dict['voice_url'] = self.voice_url
        if self.voice_duration:
            json_dict['voice_duration'] = self.voice_duration
        return json_dict


# noinspection PyUnresolvedReferences,PyShadowingBuiltins
class InlineQueryResultDocument(InlineQueryResultBase):
    """
    Represents a link to a file. By default, this file will be sent by the user with an optional caption. Alternatively, you can use input_message_content to send a message with the specified content instead of the file. Currently, only .PDF and .ZIP files can be sent using this method.

    Telegram Documentation: https://core.telegram.org/bots/api#inlinequeryresultdocument

    :param type: Type of the result, must be document
    :type type: :obj:`str`

    :param id: Unique identifier for this result, 1-64 bytes
    :type id: :obj:`str`

    :param title: Title for the result
    :type title: :obj:`str`

    :param caption: Optional. Caption of the document to be sent, 0-1024 characters after entities parsing
    :type caption: :obj:`str`

    :param parse_mode: Optional. Mode for parsing entities in the document caption. See formatting options for more 
        details.
    :type parse_mode: :obj:`str`

    :param caption_entities: Optional. List of special entities that appear in the caption, which can be specified 
        instead of parse_mode
    :type caption_entities: :obj:`list` of :class:`telebot.types.MessageEntity`

    :param document_url: A valid URL for the file
    :type document_url: :obj:`str`

    :param mime_type: MIME type of the content of the file, either “application/pdf” or “application/zip”
    :type mime_type: :obj:`str`

    :param description: Optional. Short description of the result
    :type description: :obj:`str`

    :param reply_markup: Optional. Inline keyboard attached to the message
    :type reply_markup: :class:`telebot.types.InlineKeyboardMarkup`

    :param input_message_content: Optional. Content of the message to be sent instead of the file
    :type input_message_content: :class:`telebot.types.InputMessageContent`

    :param thumbnail_url: Optional. URL of the thumbnail (JPEG only) for the file
    :type thumbnail_url: :obj:`str`

    :param thumbnail_width: Optional. Thumbnail width
    :type thumbnail_width: :obj:`int`

    :param thumbnail_height: Optional. Thumbnail height
    :type thumbnail_height: :obj:`int`

    :return: Instance of the class
    :rtype: :class:`telebot.types.InlineQueryResultDocument`
    """
    def __init__(self, id: str, title: str, document_url: str, mime_type: str, caption: Optional[str] = None, caption_entities: Optional[List[MessageEntity]] = None,
                    parse_mode: Optional[str] = None, description: Optional[str] = None, reply_markup: Optional[InlineKeyboardMarkup] = None,
                    input_message_content: Optional[InputMessageContent] = None, thumbnail_url: Optional[str] = None, thumbnail_width: Optional[int] = None,
                    thumbnail_height: Optional[int] = None):
        
        super().__init__('document', id, title = title, caption = caption,
                         input_message_content = input_message_content, reply_markup = reply_markup,
                         parse_mode = parse_mode, caption_entities = caption_entities)
        self.document_url: str = document_url
        self.mime_type: str = mime_type
        self.description: Optional[str] = description
        self.thumbnail_url: Optional[str] = thumbnail_url
        self.thumbnail_width: Optional[int] = thumbnail_width
        self.thumbnail_height: Optional[int] = thumbnail_height


    @property
    def thumb_url(self) -> str:
        log_deprecation_warning('The parameter "thumb_url" is deprecated, use "thumbnail_url" instead')
        return self.thumbnail_url

    @property
    def thumb_width(self) -> int:
        log_deprecation_warning('The parameter "thumb_width" is deprecated, use "thumbnail_width" instead')
        return self.thumbnail_width

    @property
    def thumb_height(self) -> int:
        log_deprecation_warning('The parameter "thumb_height" is deprecated, use "thumbnail_height" instead')
        return self.thumbnail_height

    def to_dict(self):
        json_dict = super().to_dict()
        json_dict['document_url'] = self.document_url
        json_dict['mime_type'] = self.mime_type
        if self.description:
            json_dict['description'] = self.description
        if self.thumbnail_url:
            json_dict['thumbnail_url'] = self.thumbnail_url
        if self.thumbnail_width:
            json_dict['thumbnail_width'] = self.thumbnail_width
        if self.thumbnail_height:
            json_dict['thumbnail_height'] = self.thumbnail_height
        return json_dict


# noinspection PyUnresolvedReferences,PyShadowingBuiltins
class InlineQueryResultLocation(InlineQueryResultBase):
    """
    Represents a location on a map. By default, the location will be sent by the user. Alternatively, you can use input_message_content to send a message with the specified content instead of the location.

    Telegram Documentation: https://core.telegram.org/bots/api#inlinequeryresultlocation

    :param type: Type of the result, must be location
    :type type: :obj:`str`

    :param id: Unique identifier for this result, 1-64 Bytes
    :type id: :obj:`str`

    :param latitude: Location latitude in degrees
    :type latitude: :obj:`float` number

    :param longitude: Location longitude in degrees
    :type longitude: :obj:`float` number

    :param title: Location title
    :type title: :obj:`str`

    :param horizontal_accuracy: Optional. The radius of uncertainty for the location, measured in meters; 0-1500
    :type horizontal_accuracy: :obj:`float` number

    :param live_period: Optional. Period in seconds during which the location can be updated, should be between 60 and 86400, or 0x7FFFFFFF for live locations that can be edited indefinitely.
    :type live_period: :obj:`int`

    :param heading: Optional. For live locations, a direction in which the user is moving, in degrees. Must be between 1 and 360 if specified.
    :type heading: :obj:`int`

    :param proximity_alert_radius: Optional. For live locations, a maximum distance for proximity alerts about approaching another chat member, in meters. Must be between 1 and 100000 if specified.
    :type proximity_alert_radius: :obj:`int`

    :param reply_markup: Optional. Inline keyboard attached to the message
    :type reply_markup: :class:`telebot.types.InlineKeyboardMarkup`

    :param input_message_content: Optional. Content of the message to be sent instead of the location
    :type input_message_content: :class:`telebot.types.InputMessageContent`

    :param thumbnail_url: Optional. Url of the thumbnail for the result
    :type thumbnail_url: :obj:`str`

    :param thumbnail_width: Optional. Thumbnail width
    :type thumbnail_width: :obj:`int`

    :param thumbnail_height: Optional. Thumbnail height
    :type thumbnail_height: :obj:`int`

    :return: Instance of the class
    :rtype: :class:`telebot.types.InlineQueryResultLocation`
    """
    def __init__(self, id: str, title: str, latitude: float, longitude: float, horizontal_accuracy: float, live_period: Optional[int] = None,
                    reply_markup: Optional[InlineKeyboardMarkup] = None, input_message_content: Optional[InputMessageContent] = None,
                    thumbnail_url: Optional[str] = None, thumbnail_width: Optional[int] = None, thumbnail_height: Optional[int] = None,
                    heading: Optional[int] = None, proximity_alert_radius: Optional[int] = None):
        
        super().__init__('location', id, title = title,
                         input_message_content = input_message_content, reply_markup = reply_markup)
        self.latitude: float = latitude
        self.longitude: float = longitude
        self.horizontal_accuracy: float = horizontal_accuracy
        self.live_period: Optional[int] = live_period
        self.heading: Optional[int] = heading
        self.proximity_alert_radius: Optional[int] = proximity_alert_radius
        self.thumbnail_url: Optional[str] = thumbnail_url
        self.thumbnail_width: Optional[int] = thumbnail_width
        self.thumbnail_height: Optional[int] = thumbnail_height

    @property
    def thumb_url(self) -> str:
        log_deprecation_warning('The parameter "thumb_url" is deprecated, use "thumbnail_url" instead')
        return self.thumbnail_url

    @property
    def thumb_width(self) -> int:
        log_deprecation_warning('The parameter "thumb_width" is deprecated, use "thumbnail_width" instead')
        return self.thumbnail_width

    @property
    def thumb_height(self) -> int:
        log_deprecation_warning('The parameter "thumb_height" is deprecated, use "thumbnail_height" instead')
        return self.thumbnail_height

    def to_dict(self):
        json_dict = super().to_dict()
        json_dict['latitude'] = self.latitude
        json_dict['longitude'] = self.longitude
        if self.horizontal_accuracy:
            json_dict['horizontal_accuracy'] = self.horizontal_accuracy
        if self.live_period:
            json_dict['live_period'] = self.live_period
        if self.heading:
            json_dict['heading'] = self.heading
        if self.proximity_alert_radius:
            json_dict['proximity_alert_radius'] = self.proximity_alert_radius
        if self.thumbnail_url:
            json_dict['thumbnail_url'] = self.thumbnail_url
        if self.thumbnail_width:
            json_dict['thumbnail_width'] = self.thumbnail_width
        if self.thumbnail_height:
            json_dict['thumbnail_height'] = self.thumbnail_height
        return json_dict


# noinspection PyUnresolvedReferences,PyShadowingBuiltins
class InlineQueryResultVenue(InlineQueryResultBase):
    """
    Represents a venue. By default, the venue will be sent by the user. Alternatively, you can use input_message_content to send a message with the specified content instead of the venue.

    Telegram Documentation: https://core.telegram.org/bots/api#inlinequeryresultvenue

    :param type: Type of the result, must be venue
    :type type: :obj:`str`

    :param id: Unique identifier for this result, 1-64 Bytes
    :type id: :obj:`str`

    :param latitude: Latitude of the venue location in degrees
    :type latitude: :obj:`float`

    :param longitude: Longitude of the venue location in degrees
    :type longitude: :obj:`float`

    :param title: Title of the venue
    :type title: :obj:`str`

    :param address: Address of the venue
    :type address: :obj:`str`

    :param foursquare_id: Optional. Foursquare identifier of the venue if known
    :type foursquare_id: :obj:`str`

    :param foursquare_type: Optional. Foursquare type of the venue, if known. (For example, 
        “arts_entertainment/default”, “arts_entertainment/aquarium” or “food/icecream”.)
    :type foursquare_type: :obj:`str`

    :param google_place_id: Optional. Google Places identifier of the venue
    :type google_place_id: :obj:`str`

    :param google_place_type: Optional. Google Places type of the venue. (See supported types.)
    :type google_place_type: :obj:`str`

    :param reply_markup: Optional. Inline keyboard attached to the message
    :type reply_markup: :class:`telebot.types.InlineKeyboardMarkup`

    :param input_message_content: Optional. Content of the message to be sent instead of the venue
    :type input_message_content: :class:`telebot.types.InputMessageContent`

    :param thumbnail_url: Optional. Url of the thumbnail for the result
    :type thumbnail_url: :obj:`str`

    :param thumbnail_width: Optional. Thumbnail width
    :type thumbnail_width: :obj:`int`

    :param thumbnail_height: Optional. Thumbnail height
    :type thumbnail_height: :obj:`int`

    :return: Instance of the class
    :rtype: :class:`telebot.types.InlineQueryResultVenue`
    """
    def __init__(self, id: str, title: str, latitude: float, longitude: float, address: str, foursquare_id: Optional[str] = None,
                    foursquare_type: Optional[str] = None, google_place_id: Optional[str] = None, google_place_type: Optional[str] = None,
                    reply_markup: Optional[InlineKeyboardMarkup] = None, input_message_content: Optional[InputMessageContent] = None,
                    thumbnail_url: Optional[str] = None, thumbnail_width: Optional[int] = None, thumbnail_height: Optional[int] = None):

        super().__init__('venue', id, title = title,
                         input_message_content = input_message_content, reply_markup = reply_markup)
        self.latitude: float = latitude
        self.longitude: float = longitude
        self.address: str = address
        self.foursquare_id: Optional[str] = foursquare_id
        self.foursquare_type: Optional[str] = foursquare_type
        self.google_place_id: Optional[str] = google_place_id
        self.google_place_type: Optional[str] = google_place_type
        self.thumbnail_url: Optional[str] = thumbnail_url
        self.thumbnail_width: Optional[int] = thumbnail_width
        self.thumbnail_height: Optional[int] = thumbnail_height

    @property
    def thumb_url(self) -> str:
        log_deprecation_warning('The parameter "thumb_url" is deprecated, use "thumbnail_url" instead')
        return self.thumbnail_url

    @property
    def thumb_width(self) -> int:
        log_deprecation_warning('The parameter "thumb_width" is deprecated, use "thumbnail_width" instead')
        return self.thumbnail_width

    @property
    def thumb_height(self) -> int:
        log_deprecation_warning('The parameter "thumb_height" is deprecated, use "thumbnail_height" instead')
        return self.thumbnail_height

    def to_dict(self):
        json_dict = super().to_dict()
        json_dict['latitude'] = self.latitude
        json_dict['longitude'] = self.longitude
        json_dict['address'] = self.address
        if self.foursquare_id:
            json_dict['foursquare_id'] = self.foursquare_id
        if self.foursquare_type:
            json_dict['foursquare_type'] = self.foursquare_type
        if self.google_place_id:
            json_dict['google_place_id'] = self.google_place_id
        if self.google_place_type:
            json_dict['google_place_type'] = self.google_place_type
        if self.thumbnail_url:
            json_dict['thumbnail_url'] = self.thumbnail_url
        if self.thumbnail_width:
            json_dict['thumbnail_width'] = self.thumbnail_width
        if self.thumbnail_height:
            json_dict['thumbnail_height'] = self.thumbnail_height
        return json_dict


# noinspection PyUnresolvedReferences,PyShadowingBuiltins
class InlineQueryResultContact(InlineQueryResultBase):
    """
    Represents a contact with a phone number. By default, this contact will be sent by the user. Alternatively, you can use input_message_content to send a message with the specified content instead of the contact.

    Telegram Documentation: https://core.telegram.org/bots/api#inlinequeryresultcontact

    :param type: Type of the result, must be contact
    :type type: :obj:`str`

    :param id: Unique identifier for this result, 1-64 Bytes
    :type id: :obj:`str`

    :param phone_number: Contact's phone number
    :type phone_number: :obj:`str`

    :param first_name: Contact's first name
    :type first_name: :obj:`str`

    :param last_name: Optional. Contact's last name
    :type last_name: :obj:`str`

    :param vcard: Optional. Additional data about the contact in the form of a vCard, 0-2048 bytes
    :type vcard: :obj:`str`

    :param reply_markup: Optional. Inline keyboard attached to the message
    :type reply_markup: :class:`telebot.types.InlineKeyboardMarkup`

    :param input_message_content: Optional. Content of the message to be sent instead of the contact
    :type input_message_content: :class:`telebot.types.InputMessageContent`

    :param thumbnail_url: Optional. Url of the thumbnail for the result
    :type thumbnail_url: :obj:`str`

    :param thumbnail_width: Optional. Thumbnail width
    :type thumbnail_width: :obj:`int`

    :param thumbnail_height: Optional. Thumbnail height
    :type thumbnail_height: :obj:`int`

    :return: Instance of the class
    :rtype: :class:`telebot.types.InlineQueryResultContact`
    """
        
    def __init__(self, id: str, phone_number: str, first_name: str, last_name: Optional[str] = None, vcard: Optional[str] = None,
                    reply_markup: Optional[InlineKeyboardMarkup] = None, input_message_content: Optional[InputMessageContent] = None,
                    thumbnail_url: Optional[str] = None, thumbnail_width: Optional[int] = None, thumbnail_height: Optional[int] = None):
        super().__init__('contact', id,
                         input_message_content = input_message_content, reply_markup = reply_markup)
        self.phone_number: str = phone_number
        self.first_name: str = first_name
        self.last_name: Optional[str] = last_name
        self.vcard: Optional[str] = vcard
        self.thumbnail_url: Optional[str] = thumbnail_url
        self.thumbnail_width: Optional[int] = thumbnail_width
        self.thumbnail_height: Optional[int] = thumbnail_height


    @property
    def thumb_url(self) -> str:
        log_deprecation_warning('The parameter "thumb_url" is deprecated, use "thumbnail_url" instead')
        return self.thumbnail_url

    @property
    def thumb_width(self) -> int:
        log_deprecation_warning('The parameter "thumb_width" is deprecated, use "thumbnail_width" instead')
        return self.thumbnail_width

    @property
    def thumb_height(self) -> int:
        log_deprecation_warning('The parameter "thumb_height" is deprecated, use "thumbnail_height" instead')
        return self.thumbnail_height

    def to_dict(self):
        json_dict = super().to_dict()
        json_dict['phone_number'] = self.phone_number
        json_dict['first_name'] = self.first_name
        if self.last_name:
            json_dict['last_name'] = self.last_name
        if self.vcard:
            json_dict['vcard'] = self.vcard
        if self.thumbnail_url:
            json_dict['thumbnail_url'] = self.thumbnail_url
        if self.thumbnail_width:
            json_dict['thumbnail_width'] = self.thumbnail_width
        if self.thumbnail_height:
            json_dict['thumbnail_height'] = self.thumbnail_height
        return json_dict


# noinspection PyUnresolvedReferences,PyShadowingBuiltins
class InlineQueryResultGame(InlineQueryResultBase):
    """
    Represents a Game.

    Telegram Documentation: https://core.telegram.org/bots/api#inlinequeryresultgame

    :param type: Type of the result, must be game
    :type type: :obj:`str`

    :param id: Unique identifier for this result, 1-64 bytes
    :type id: :obj:`str`

    :param game_short_name: Short name of the game
    :type game_short_name: :obj:`str`

    :param reply_markup: Optional. Inline keyboard attached to the message
    :type reply_markup: :class:`telebot.types.InlineKeyboardMarkup`

    :return: Instance of the class
    :rtype: :class:`telebot.types.InlineQueryResultGame`
    """
    def __init__(self, id: str, game_short_name: str, reply_markup: Optional[InlineKeyboardMarkup] = None):
        super().__init__('game', id, reply_markup = reply_markup)
        self.game_short_name: str = game_short_name

    def to_dict(self):
        json_dict = super().to_dict()
        json_dict['game_short_name'] = self.game_short_name
        return json_dict


class InlineQueryResultCachedBase(ABC, JsonSerializable):
    """
    Base class of all InlineQueryResultCached* classes.
    """
    def __init__(self):
        self.type: str = ""
        self.id: str = ""
        self.title: Optional[str] = None
        self.description: Optional[str] = None
        self.caption: Optional[str] = None
        self.reply_markup: Optional[InlineKeyboardMarkup] = None
        self.input_message_content: Optional[InputMessageContent] = None
        self.parse_mode: Optional[str] = None
        self.caption_entities: Optional[List[MessageEntity]] = None
        # noinspection PyTypeChecker
        self.payload_dic: Dict[str] = {}
        self.show_caption_above_media: Optional[bool] = None

    def to_json(self):
        json_dict = self.payload_dic
        json_dict['type'] = self.type
        json_dict['id'] = self.id
        if self.title:
            json_dict['title'] = self.title
        if self.description:
            json_dict['description'] = self.description
        if self.caption:
            json_dict['caption'] = self.caption
        if self.reply_markup:
            json_dict['reply_markup'] = self.reply_markup.to_dict()
        if self.input_message_content:
            json_dict['input_message_content'] = self.input_message_content.to_dict()
        if self.parse_mode:
            json_dict['parse_mode'] = self.parse_mode
        if self.caption_entities:
            json_dict['caption_entities'] = MessageEntity.to_list_of_dicts(self.caption_entities)
        if self.show_caption_above_media is not None:
            json_dict['show_caption_above_media'] = self.show_caption_above_media
        return json.dumps(json_dict)


# noinspection PyUnresolvedReferences,PyShadowingBuiltins
class InlineQueryResultCachedPhoto(InlineQueryResultCachedBase):
    """
    Represents a link to a photo stored on the Telegram servers. By default, this photo will be sent by the user with an optional caption. Alternatively, you can use input_message_content to send a message with the specified content instead of the photo.

    Telegram Documentation: https://core.telegram.org/bots/api#inlinequeryresultcachedphoto

    :param type: Type of the result, must be photo
    :type type: :obj:`str`

    :param id: Unique identifier for this result, 1-64 bytes
    :type id: :obj:`str`

    :param photo_file_id: A valid file identifier of the photo
    :type photo_file_id: :obj:`str`

    :param title: Optional. Title for the result
    :type title: :obj:`str`

    :param description: Optional. Short description of the result
    :type description: :obj:`str`

    :param caption: Optional. Caption of the photo to be sent, 0-1024 characters after entities parsing
    :type caption: :obj:`str`

    :param parse_mode: Optional. Mode for parsing entities in the photo caption. See formatting options for more 
        details.
    :type parse_mode: :obj:`str`

    :param caption_entities: Optional. List of special entities that appear in the caption, which can be specified 
        instead of parse_mode
    :type caption_entities: :obj:`list` of :class:`telebot.types.MessageEntity`

    :param reply_markup: Optional. Inline keyboard attached to the message
    :type reply_markup: :class:`telebot.types.InlineKeyboardMarkup`

    :param input_message_content: Optional. Content of the message to be sent instead of the photo
    :type input_message_content: :class:`telebot.types.InputMessageContent`

    :param show_caption_above_media: Optional. Pass True, if a caption is not required for the media
    :type show_caption_above_media: :obj:`bool`

    :return: Instance of the class
    :rtype: :class:`telebot.types.InlineQueryResultCachedPhoto`
    """
    def __init__(self, id: str, photo_file_id: str, title: Optional[str] = None, description: Optional[str] = None,
                    caption: Optional[str] = None, caption_entities: Optional[List[MessageEntity]] = None,
                    parse_mode: Optional[str] = None, reply_markup: Optional[InlineKeyboardMarkup] = None,
                    input_message_content: Optional[InputMessageContent] = None, show_caption_above_media: Optional[bool] = None):

        InlineQueryResultCachedBase.__init__(self)
        self.type: str = 'photo'
        self.id: str = id
        self.photo_file_id: str = photo_file_id
        self.title: Optional[str] = title
        self.description: Optional[str] = description
        self.caption: Optional[str] = caption
        self.caption_entities: Optional[List[MessageEntity]] = caption_entities
        self.reply_markup: Optional[InlineKeyboardMarkup] = reply_markup
        self.input_message_content: Optional[InputMessageContent] = input_message_content
        self.parse_mode: Optional[str] = parse_mode
        self.payload_dic['photo_file_id'] = photo_file_id
        self.show_caption_above_media: Optional[bool] = show_caption_above_media



# noinspection PyUnresolvedReferences,PyShadowingBuiltins
class InlineQueryResultCachedGif(InlineQueryResultCachedBase):
    """
    Represents a link to an animated GIF file stored on the Telegram servers. By default, this animated GIF file will be sent by the user with an optional caption. Alternatively, you can use input_message_content to send a message with specified content instead of the animation.

    Telegram Documentation: https://core.telegram.org/bots/api#inlinequeryresultcachedgif

    :param type: Type of the result, must be gif
    :type type: :obj:`str`

    :param id: Unique identifier for this result, 1-64 bytes
    :type id: :obj:`str`

    :param gif_file_id: A valid file identifier for the GIF file
    :type gif_file_id: :obj:`str`

    :param title: Optional. Title for the result
    :type title: :obj:`str`

    :param caption: Optional. Caption of the GIF file to be sent, 0-1024 characters after entities parsing
    :type caption: :obj:`str`

    :param parse_mode: Optional. Mode for parsing entities in the caption. See formatting options for more details.
    :type parse_mode: :obj:`str`

    :param caption_entities: Optional. List of special entities that appear in the caption, which can be specified 
        instead of parse_mode
    :type caption_entities: :obj:`list` of :class:`telebot.types.MessageEntity`

    :param reply_markup: Optional. Inline keyboard attached to the message
    :type reply_markup: :class:`telebot.types.InlineKeyboardMarkup`

    :param input_message_content: Optional. Content of the message to be sent instead of the GIF animation
    :type input_message_content: :class:`telebot.types.InputMessageContent`

    :param show_caption_above_media: Optional. Pass True, if a caption is not required for the media
    :type show_caption_above_media: :obj:`bool`

    :return: Instance of the class
    :rtype: :class:`telebot.types.InlineQueryResultCachedGif`
    """
    def __init__(self, id: str, gif_file_id: str, title: Optional[str] = None, description: Optional[str] = None,
                    caption: Optional[str] = None, caption_entities: Optional[List[MessageEntity]] = None,
                    parse_mode: Optional[str] = None, reply_markup: Optional[InlineKeyboardMarkup] = None,
                    input_message_content: Optional[InputMessageContent] = None, show_caption_above_media: Optional[bool] = None):
        
        InlineQueryResultCachedBase.__init__(self)
        self.type: str = 'gif'
        self.id: str = id
        self.gif_file_id: str = gif_file_id
        self.title: Optional[str] = title
        self.description: Optional[str] = description
        self.caption: Optional[str] = caption
        self.caption_entities: Optional[List[MessageEntity]] = caption_entities
        self.reply_markup: Optional[InlineKeyboardMarkup] = reply_markup
        self.input_message_content: Optional[InputMessageContent] = input_message_content
        self.parse_mode: Optional[str] = parse_mode
        self.payload_dic['gif_file_id'] = gif_file_id
        self.show_caption_above_media: Optional[bool] = show_caption_above_media


# noinspection PyUnresolvedReferences,PyShadowingBuiltins
class InlineQueryResultCachedMpeg4Gif(InlineQueryResultCachedBase):
    """
    Represents a link to a video animation (H.264/MPEG-4 AVC video without sound) stored on the Telegram servers. By default, this animated MPEG-4 file will be sent by the user with an optional caption. Alternatively, you can use input_message_content to send a message with the specified content instead of the animation.

    Telegram Documentation: https://core.telegram.org/bots/api#inlinequeryresultcachedmpeg4gif

    :param type: Type of the result, must be mpeg4_gif
    :type type: :obj:`str`

    :param id: Unique identifier for this result, 1-64 bytes
    :type id: :obj:`str`

    :param mpeg4_file_id: A valid file identifier for the MPEG4 file
    :type mpeg4_file_id: :obj:`str`

    :param title: Optional. Title for the result
    :type title: :obj:`str`

    :param caption: Optional. Caption of the MPEG-4 file to be sent, 0-1024 characters after entities parsing
    :type caption: :obj:`str`

    :param parse_mode: Optional. Mode for parsing entities in the caption. See formatting options for more details.
    :type parse_mode: :obj:`str`

    :param caption_entities: Optional. List of special entities that appear in the caption, which can be specified 
        instead of parse_mode
    :type caption_entities: :obj:`list` of :class:`telebot.types.MessageEntity`

    :param reply_markup: Optional. Inline keyboard attached to the message
    :type reply_markup: :class:`telebot.types.InlineKeyboardMarkup`

    :param input_message_content: Optional. Content of the message to be sent instead of the video animation
    :type input_message_content: :class:`telebot.types.InputMessageContent`

    :param show_caption_above_media: Optional. Pass True, if caption should be shown above the media
    :type show_caption_above_media: :obj:`bool`

    :return: Instance of the class
    :rtype: :class:`telebot.types.InlineQueryResultCachedMpeg4Gif`
    """
    def __init__(self, id: str, mpeg4_file_id: str, title: Optional[str] = None, description: Optional[str] = None,
                    caption: Optional[str] = None, caption_entities: Optional[List[MessageEntity]] = None,
                    parse_mode: Optional[str] = None, reply_markup: Optional[InlineKeyboardMarkup] = None,
                    input_message_content: Optional[InputMessageContent] = None, show_caption_above_media: Optional[bool] = None):
        
        InlineQueryResultCachedBase.__init__(self)
        self.type: str = 'mpeg4_gif'
        self.id: str = id
        self.mpeg4_file_id: str = mpeg4_file_id
        self.title: Optional[str] = title
        self.description: Optional[str] = description
        self.caption: Optional[str] = caption
        self.caption_entities: Optional[List[MessageEntity]] = caption_entities
        self.reply_markup: Optional[InlineKeyboardMarkup] = reply_markup
        self.input_message_content: Optional[InputMessageContent] = input_message_content
        self.parse_mode: Optional[str] = parse_mode
        self.payload_dic['mpeg4_file_id'] = mpeg4_file_id
        self.show_caption_above_media: Optional[bool] = show_caption_above_media

# noinspection PyUnresolvedReferences,PyShadowingBuiltins
class InlineQueryResultCachedSticker(InlineQueryResultCachedBase):
    """
    Represents a link to a sticker stored on the Telegram servers. By default, this sticker will be sent by the user. Alternatively, you can use input_message_content to send a message with the specified content instead of the sticker.

    Telegram Documentation: https://core.telegram.org/bots/api#inlinequeryresultcachedsticker

    :param type: Type of the result, must be sticker
    :type type: :obj:`str`

    :param id: Unique identifier for this result, 1-64 bytes
    :type id: :obj:`str`

    :param sticker_file_id: A valid file identifier of the sticker
    :type sticker_file_id: :obj:`str`

    :param reply_markup: Optional. Inline keyboard attached to the message
    :type reply_markup: :class:`telebot.types.InlineKeyboardMarkup`

    :param input_message_content: Optional. Content of the message to be sent instead of the sticker
    :type input_message_content: :class:`telebot.types.InputMessageContent`

    :return: Instance of the class
    :rtype: :class:`telebot.types.InlineQueryResultCachedSticker`
    """
    def __init__(self, id: str, sticker_file_id: str, reply_markup: Optional[InlineKeyboardMarkup] = None,
                    input_message_content: Optional[InputMessageContent] = None):
        InlineQueryResultCachedBase.__init__(self)
        self.type: str = 'sticker'
        self.id: str = id
        self.sticker_file_id: str = sticker_file_id
        self.reply_markup: Optional[InlineKeyboardMarkup] = reply_markup
        self.input_message_content: Optional[InputMessageContent] = input_message_content
        self.payload_dic['sticker_file_id'] = sticker_file_id



# noinspection PyUnresolvedReferences,PyShadowingBuiltins
class InlineQueryResultCachedDocument(InlineQueryResultCachedBase):
    """
    Represents a link to a file stored on the Telegram servers. By default, this file will be sent by the user with an optional caption. Alternatively, you can use input_message_content to send a message with the specified content instead of the file.

    Telegram Documentation: https://core.telegram.org/bots/api#inlinequeryresultcacheddocument

    :param type: Type of the result, must be document
    :type type: :obj:`str`

    :param id: Unique identifier for this result, 1-64 bytes
    :type id: :obj:`str`

    :param title: Title for the result
    :type title: :obj:`str`

    :param document_file_id: A valid file identifier for the file
    :type document_file_id: :obj:`str`

    :param description: Optional. Short description of the result
    :type description: :obj:`str`

    :param caption: Optional. Caption of the document to be sent, 0-1024 characters after entities parsing
    :type caption: :obj:`str`

    :param parse_mode: Optional. Mode for parsing entities in the document caption. See formatting options for more 
        details.
    :type parse_mode: :obj:`str`

    :param caption_entities: Optional. List of special entities that appear in the caption, which can be specified 
        instead of parse_mode
    :type caption_entities: :obj:`list` of :class:`telebot.types.MessageEntity`

    :param reply_markup: Optional. Inline keyboard attached to the message
    :type reply_markup: :class:`telebot.types.InlineKeyboardMarkup`

    :param input_message_content: Optional. Content of the message to be sent instead of the file
    :type input_message_content: :class:`telebot.types.InputMessageContent`

    :return: Instance of the class
    :rtype: :class:`telebot.types.InlineQueryResultCachedDocument`
    """

    def __init__(self, id: str, document_file_id: str, title: str, description: Optional[str] = None,
                    caption: Optional[str] = None, caption_entities: Optional[List[MessageEntity]] = None,
                    parse_mode: Optional[str] = None, reply_markup: Optional[InlineKeyboardMarkup] = None,
                    input_message_content: Optional[InputMessageContent] = None):
        
        InlineQueryResultCachedBase.__init__(self)
        self.type: str = 'document'
        self.id: str = id
        self.title: str = title
        self.document_file_id: str = document_file_id
        self.description: Optional[str] = description
        self.caption: Optional[str] = caption
        self.caption_entities: Optional[List[MessageEntity]] = caption_entities
        self.reply_markup: Optional[InlineKeyboardMarkup] = reply_markup
        self.input_message_content: Optional[InputMessageContent] = input_message_content
        self.parse_mode: Optional[str] = parse_mode
        self.payload_dic['document_file_id'] = document_file_id


# noinspection PyUnresolvedReferences,PyShadowingBuiltins
class InlineQueryResultCachedVideo(InlineQueryResultCachedBase):
    """
    Represents a link to a video file stored on the Telegram servers. By default, this video file will be sent by the user with an optional caption. Alternatively, you can use input_message_content to send a message with the specified content instead of the video.

    Telegram Documentation: https://core.telegram.org/bots/api#inlinequeryresultcachedvideo

    :param type: Type of the result, must be video
    :type type: :obj:`str`

    :param id: Unique identifier for this result, 1-64 bytes
    :type id: :obj:`str`

    :param video_file_id: A valid file identifier for the video file
    :type video_file_id: :obj:`str`

    :param title: Title for the result
    :type title: :obj:`str`

    :param description: Optional. Short description of the result
    :type description: :obj:`str`

    :param caption: Optional. Caption of the video to be sent, 0-1024 characters after entities parsing
    :type caption: :obj:`str`

    :param parse_mode: Optional. Mode for parsing entities in the video caption. See formatting options for more 
        details.
    :type parse_mode: :obj:`str`

    :param caption_entities: Optional. List of special entities that appear in the caption, which can be specified 
        instead of parse_mode
    :type caption_entities: :obj:`list` of :class:`telebot.types.MessageEntity`

    :param reply_markup: Optional. Inline keyboard attached to the message
    :type reply_markup: :class:`telebot.types.InlineKeyboardMarkup`

    :param input_message_content: Optional. Content of the message to be sent instead of the video
    :type input_message_content: :class:`telebot.types.InputMessageContent`

    :param show_caption_above_media: Optional. Pass True, if a caption is not required for the media
    :type show_caption_above_media: :obj:`bool`

    :return: Instance of the class
    :rtype: :class:`telebot.types.InlineQueryResultCachedVideo`
    """

    def __init__(self, id: str, video_file_id: str, title: str, description: Optional[str] = None,
                    caption: Optional[str] = None, caption_entities: Optional[List[MessageEntity]] = None,
                    parse_mode: Optional[str] = None, reply_markup: Optional[InlineKeyboardMarkup] = None,
                    input_message_content: Optional[InputMessageContent] = None, show_caption_above_media: Optional[bool] = None):
        
        InlineQueryResultCachedBase.__init__(self)
        self.type: str = 'video'
        self.id: str = id
        self.video_file_id: str = video_file_id
        self.title: str = title
        self.description: Optional[str] = description
        self.caption: Optional[str] = caption
        self.caption_entities: Optional[List[MessageEntity]] = caption_entities
        self.reply_markup: Optional[InlineKeyboardMarkup] = reply_markup
        self.input_message_content: Optional[InputMessageContent] = input_message_content
        self.parse_mode: Optional[str] = parse_mode
        self.payload_dic['video_file_id'] = video_file_id
        self.show_caption_above_media: Optional[bool] = show_caption_above_media


# noinspection PyUnresolvedReferences,PyShadowingBuiltins
class InlineQueryResultCachedVoice(InlineQueryResultCachedBase):
    """
    Represents a link to a voice message stored on the Telegram servers. By default, this voice message will be sent by the user. Alternatively, you can use input_message_content to send a message with the specified content instead of the voice message.

    Telegram Documentation: https://core.telegram.org/bots/api#inlinequeryresultcachedvoice

    :param type: Type of the result, must be voice
    :type type: :obj:`str`

    :param id: Unique identifier for this result, 1-64 bytes
    :type id: :obj:`str`

    :param voice_file_id: A valid file identifier for the voice message
    :type voice_file_id: :obj:`str`

    :param title: Voice message title
    :type title: :obj:`str`

    :param caption: Optional. Caption, 0-1024 characters after entities parsing
    :type caption: :obj:`str`

    :param parse_mode: Optional. Mode for parsing entities in the voice message caption. See formatting options for 
        more details.
    :type parse_mode: :obj:`str`

    :param caption_entities: Optional. List of special entities that appear in the caption, which can be specified 
        instead of parse_mode
    :type caption_entities: :obj:`list` of :class:`telebot.types.MessageEntity`

    :param reply_markup: Optional. Inline keyboard attached to the message
    :type reply_markup: :class:`telebot.types.InlineKeyboardMarkup`

    :param input_message_content: Optional. Content of the message to be sent instead of the voice message
    :type input_message_content: :class:`telebot.types.InputMessageContent`

    :return: Instance of the class
    :rtype: :class:`telebot.types.InlineQueryResultCachedVoice`
    """
        
    def __init__(self, id: str, voice_file_id: str, title: str, caption: Optional[str] = None,
                    caption_entities: Optional[List[MessageEntity]] = None, parse_mode: Optional[str] = None,
                    reply_markup: Optional[InlineKeyboardMarkup] = None, input_message_content: Optional[InputMessageContent] = None):
        InlineQueryResultCachedBase.__init__(self)
        self.type: str = 'voice'
        self.id: str = id
        self.voice_file_id: str = voice_file_id
        self.title: str = title
        self.caption: Optional[str] = caption
        self.caption_entities: Optional[List[MessageEntity]] = caption_entities
        self.reply_markup: Optional[InlineKeyboardMarkup] = reply_markup
        self.input_message_content: Optional[InputMessageContent] = input_message_content
        self.parse_mode: Optional[str] = parse_mode
        self.payload_dic['voice_file_id'] = voice_file_id
        


# noinspection PyUnresolvedReferences,PyShadowingBuiltins
class InlineQueryResultCachedAudio(InlineQueryResultCachedBase):
    """
    Represents a link to an MP3 audio file stored on the Telegram servers. By default, this audio file will be sent by the user. Alternatively, you can use input_message_content to send a message with the specified content instead of the audio.

    Telegram Documentation: https://core.telegram.org/bots/api#inlinequeryresultcachedaudio

    :param type: Type of the result, must be audio
    :type type: :obj:`str`

    :param id: Unique identifier for this result, 1-64 bytes
    :type id: :obj:`str`

    :param audio_file_id: A valid file identifier for the audio file
    :type audio_file_id: :obj:`str`

    :param caption: Optional. Caption, 0-1024 characters after entities parsing
    :type caption: :obj:`str`

    :param parse_mode: Optional. Mode for parsing entities in the audio caption. See formatting options for more 
        details.
    :type parse_mode: :obj:`str`

    :param caption_entities: Optional. List of special entities that appear in the caption, which can be specified 
        instead of parse_mode
    :type caption_entities: :obj:`list` of :class:`telebot.types.MessageEntity`

    :param reply_markup: Optional. Inline keyboard attached to the message
    :type reply_markup: :class:`telebot.types.InlineKeyboardMarkup`

    :param input_message_content: Optional. Content of the message to be sent instead of the audio
    :type input_message_content: :class:`telebot.types.InputMessageContent`

    :return: Instance of the class
    :rtype: :class:`telebot.types.InlineQueryResultCachedAudio`
    """
        
    def __init__(self, id: str, audio_file_id: str, caption: Optional[str] = None, caption_entities: Optional[List[MessageEntity]] = None,
                    parse_mode: Optional[str] = None, reply_markup: Optional[InlineKeyboardMarkup] = None,
                    input_message_content: Optional[InputMessageContent] = None):
        InlineQueryResultCachedBase.__init__(self)
        self.type: str = 'audio'
        self.id: str = id
        self.audio_file_id: str = audio_file_id
        self.caption: Optional[str] = caption
        self.caption_entities: Optional[List[MessageEntity]] = caption_entities
        self.reply_markup: Optional[InlineKeyboardMarkup] = reply_markup
        self.input_message_content: Optional[InputMessageContent] = input_message_content
        self.parse_mode: Optional[str] = parse_mode
        self.payload_dic['audio_file_id'] = audio_file_id


# Games

class Game(JsonDeserializable):
    """
    This object represents a game. Use BotFather to create and edit games, their short names will act as unique identifiers.

    Telegram Documentation: https://core.telegram.org/bots/api#game

    :param title: Title of the game
    :type title: :obj:`str`

    :param description: Description of the game
    :type description: :obj:`str`

    :param photo: Photo that will be displayed in the game message in chats.
    :type photo: :obj:`list` of :class:`telebot.types.PhotoSize`

    :param text: Optional. Brief description of the game or high scores included in the game message. Can be 
        automatically edited to include current high scores for the game when the bot calls setGameScore, or manually edited 
        using editMessageText. 0-4096 characters.
    :type text: :obj:`str`

    :param text_entities: Optional. Special entities that appear in text, such as usernames, URLs, bot commands, etc.
    :type text_entities: :obj:`list` of :class:`telebot.types.MessageEntity`

    :param animation: Optional. Animation that will be displayed in the game message in chats. Upload via BotFather
    :type animation: :class:`telebot.types.Animation`

    :return: Instance of the class
    :rtype: :class:`telebot.types.Game`
    """
    @classmethod
    def de_json(cls, json_string):
        if json_string is None: return None
        obj = cls.check_json(json_string)
        obj['photo'] = Game.parse_photo(obj['photo'])
        if 'text_entities' in obj:
            obj['text_entities'] = Game.parse_entities(obj['text_entities'])
        if 'animation' in obj:
            obj['animation'] = Animation.de_json(obj['animation'])
        return cls(**obj)

    @classmethod
    def parse_photo(cls, photo_size_array) -> List[PhotoSize]:
        """
        Parse the photo array into a list of PhotoSize objects
        """
        ret = []
        for ps in photo_size_array:
            ret.append(PhotoSize.de_json(ps))
        return ret

    @classmethod
    def parse_entities(cls, message_entity_array) -> List[MessageEntity]:
        """
        Parse the message entity array into a list of MessageEntity objects
        """
        ret = []
        for me in message_entity_array:
            ret.append(MessageEntity.de_json(me))
        return ret

    def __init__(self, title, description, photo, text=None, text_entities=None, animation=None, **kwargs):
        self.title: str = title
        self.description: str = description
        self.photo: List[PhotoSize] = photo
        self.text: str = text
        self.text_entities: List[MessageEntity] = text_entities
        self.animation: Animation = animation


class Animation(JsonDeserializable):
    """
    This object represents an animation file (GIF or H.264/MPEG-4 AVC video without sound).

    Telegram Documentation: https://core.telegram.org/bots/api#animation

    :param file_id: Identifier for this file, which can be used to download or reuse the file
    :type file_id: :obj:`str`

    :param file_unique_id: Unique identifier for this file, which is supposed to be the same over time and for different 
        bots. Can't be used to download or reuse the file.
    :type file_unique_id: :obj:`str`

    :param width: Video width as defined by sender
    :type width: :obj:`int`

    :param height: Video height as defined by sender
    :type height: :obj:`int`

    :param duration: Duration of the video in seconds as defined by sender
    :type duration: :obj:`int`

    :param thumbnail: Optional. Animation thumbnail as defined by sender
    :type thumbnail: :class:`telebot.types.PhotoSize`

    :param file_name: Optional. Original animation filename as defined by sender
    :type file_name: :obj:`str`

    :param mime_type: Optional. MIME type of the file as defined by sender
    :type mime_type: :obj:`str`

    :param file_size: Optional. File size in bytes. It can be bigger than 2^31 and some programming languages may have 
        difficulty/silent defects in interpreting it. But it has at most 52 significant bits, so a signed 64-bit integer or 
        double-precision float type are safe for storing this value.
    :type file_size: :obj:`int`

    :return: Instance of the class
    :rtype: :class:`telebot.types.Animation`
    """
    @classmethod
    def de_json(cls, json_string):
        if json_string is None: return None
        obj = cls.check_json(json_string)
        if 'thumbnail' in obj and 'file_id' in obj['thumbnail']:
            obj["thumbnail"] = PhotoSize.de_json(obj['thumbnail'])
        else:
            obj['thumbnail'] = None
        return cls(**obj)

    def __init__(self, file_id, file_unique_id, width=None, height=None, duration=None, 
                 thumbnail=None, file_name=None, mime_type=None, file_size=None, **kwargs):
        self.file_id: str = file_id
        self.file_unique_id: str = file_unique_id
        self.width: Optional[int] = width
        self.height: Optional[int] = height
        self.duration: Optional[int] = duration
        self.thumbnail: Optional[PhotoSize] = thumbnail
        self.file_name: Optional[str] = file_name
        self.mime_type: Optional[str] = mime_type
        self.file_size: Optional[int] = file_size

    @property
    def thumb(self) -> Optional[PhotoSize]:
        log_deprecation_warning('The parameter "thumb" is deprecated, use "thumbnail" instead')
        return self.thumbnail


class GameHighScore(JsonDeserializable):
    """
    This object represents one row of the high scores table for a game.

    Telegram Documentation: https://core.telegram.org/bots/api#gamehighscore

    :param position: Position in high score table for the game
    :type position: :obj:`int`

    :param user: User
    :type user: :class:`telebot.types.User`

    :param score: Score
    :type score: :obj:`int`

    :return: Instance of the class
    :rtype: :class:`telebot.types.GameHighScore`
    """
    @classmethod
    def de_json(cls, json_string):
        if json_string is None: return None
        obj = cls.check_json(json_string)
        obj['user'] = User.de_json(obj['user'])
        return cls(**obj)

    def __init__(self, position: int, user: User, score: int, **kwargs):
        self.position: int = position
        self.user: User = user
        self.score: int = score


# Payments

class LabeledPrice(JsonSerializable, Dictionaryable):
    """
    This object represents a portion of the price for goods or services.

    Telegram Documentation: https://core.telegram.org/bots/api#labeledprice

    :param label: Portion label
    :type label: :obj:`str`

    :param amount: Price of the product in the smallest units of the currency (integer, not float/double). For example, 
        for a price of US$ 1.45 pass amount = 145. See the exp parameter in currencies.json, it shows the number of digits past 
        the decimal point for each currency (2 for the majority of currencies).
    :type amount: :obj:`int`

    :return: Instance of the class
    :rtype: :class:`telebot.types.LabeledPrice`
    """
    def __init__(self, label, amount):
        self.label: str = label
        self.amount: int = amount

    def to_dict(self):
        return {
            'label': self.label, 'amount': self.amount
        }

    def to_json(self):
        return json.dumps(self.to_dict())


class Invoice(JsonDeserializable):
    """
    This object contains basic information about an invoice.

    Telegram Documentation: https://core.telegram.org/bots/api#invoice

    :param title: Product name
    :type title: :obj:`str`

    :param description: Product description
    :type description: :obj:`str`

    :param start_parameter: Unique bot deep-linking parameter that can be used to generate this invoice
    :type start_parameter: :obj:`str`

    :param currency: Three-letter ISO 4217 currency code
    :type currency: :obj:`str`

    :param total_amount: Total price in the smallest units of the currency (integer, not float/double). For example, 
        for a price of US$ 1.45 pass amount = 145. See the exp parameter in currencies.json, it shows the number of digits past 
        the decimal point for each currency (2 for the majority of currencies).
    :type total_amount: :obj:`int`

    :return: Instance of the class
    :rtype: :class:`telebot.types.Invoice`
    """
    @classmethod
    def de_json(cls, json_string):
        if json_string is None: return None
        obj = cls.check_json(json_string, dict_copy=False)
        return cls(**obj)

    def __init__(self, title, description, start_parameter, currency, total_amount, **kwargs):
        self.title: str = title
        self.description: str = description
        self.start_parameter: str = start_parameter
        self.currency: str = currency
        self.total_amount: int = total_amount


class ShippingAddress(JsonDeserializable):
    """
    This object represents a shipping address.

    Telegram Documentation: https://core.telegram.org/bots/api#shippingaddress

    :param country_code: Two-letter ISO 3166-1 alpha-2 country code
    :type country_code: :obj:`str`

    :param state: State, if applicable
    :type state: :obj:`str`

    :param city: City
    :type city: :obj:`str`

    :param street_line1: First line for the address
    :type street_line1: :obj:`str`

    :param street_line2: Second line for the address
    :type street_line2: :obj:`str`

    :param post_code: Address post code
    :type post_code: :obj:`str`

    :return: Instance of the class
    :rtype: :class:`telebot.types.ShippingAddress`
    """
    @classmethod
    def de_json(cls, json_string):
        if json_string is None: return None
        obj = cls.check_json(json_string, dict_copy=False)
        return cls(**obj)

    def __init__(self, country_code, state, city, street_line1, street_line2, post_code, **kwargs):
        self.country_code: str = country_code
        self.state: str = state
        self.city: str = city
        self.street_line1: str = street_line1
        self.street_line2: str = street_line2
        self.post_code: str = post_code


class OrderInfo(JsonDeserializable):
    """
    This object represents information about an order.

    Telegram Documentation: https://core.telegram.org/bots/api#orderinfo

    :param name: Optional. User name
    :type name: :obj:`str`

    :param phone_number: Optional. User's phone number
    :type phone_number: :obj:`str`

    :param email: Optional. User email
    :type email: :obj:`str`

    :param shipping_address: Optional. User shipping address
    :type shipping_address: :class:`telebot.types.ShippingAddress`

    :return: Instance of the class
    :rtype: :class:`telebot.types.OrderInfo`
    """
    @classmethod
    def de_json(cls, json_string):
        if json_string is None: return None
        obj = cls.check_json(json_string)
        obj['shipping_address'] = ShippingAddress.de_json(obj.get('shipping_address'))
        return cls(**obj)

    def __init__(self, name=None, phone_number=None, email=None, shipping_address=None, **kwargs):
        self.name: str = name
        self.phone_number: str = phone_number
        self.email: Optional[str] = email
        self.shipping_address: Optional[ShippingAddress] = shipping_address


# noinspection PyUnresolvedReferences,PyShadowingBuiltins
class ShippingOption(JsonSerializable):
    """
    This object represents one shipping option.

    Telegram Documentation: https://core.telegram.org/bots/api#shippingoption

    :param id: Shipping option identifier
    :type id: :obj:`str`

    :param title: Option title
    :type title: :obj:`str`

    :param prices: List of price portions
    :type prices: :obj:`list` of :class:`telebot.types.LabeledPrice`

    :return: Instance of the class
    :rtype: :class:`telebot.types.ShippingOption`
    """
    def __init__(self, id, title):
        self.id: str = id
        self.title: str = title
        self.prices: List[LabeledPrice] = []

    def add_price(self, *args) -> 'ShippingOption':
        """
        Add LabeledPrice to ShippingOption
        
        :param args: LabeledPrices
        :type args: :obj:`LabeledPrice`

        :return: None
        """
        for price in args:
            self.prices.append(price)
        return self

    def to_json(self):
        price_list = []
        for p in self.prices:
            price_list.append(p.to_dict())
        json_dict = json.dumps({'id': self.id, 'title': self.title, 'prices': price_list})
        return json_dict


class SuccessfulPayment(JsonDeserializable):
    """
    This object contains basic information about a successful payment.

    Telegram Documentation: https://core.telegram.org/bots/api#successfulpayment

    :param currency: Three-letter ISO 4217 currency code
    :type currency: :obj:`str`

    :param total_amount: Total price in the smallest units of the currency (integer, not float/double). For example, 
        for a price of US$ 1.45 pass amount = 145. See the exp parameter in currencies.json, it shows the number of digits past 
        the decimal point for each currency (2 for the majority of currencies).
    :type total_amount: :obj:`int`

    :param invoice_payload: Bot specified invoice payload
    :type invoice_payload: :obj:`str`

    :param subscription_expiration_date: Optional. Expiration date of the subscription, in Unix time; for recurring payments only
    :type subscription_expiration_date: :obj:`int`

    :param is_recurring: Optional. True, if the payment is a recurring payment, false otherwise
    :type is_recurring: :obj:`bool`

    :param is_first_recurring: Optional. True, if the payment is the first payment for a subscription
    :type is_first_recurring: :obj:`bool`

    :param shipping_option_id: Optional. Identifier of the shipping option chosen by the user
    :type shipping_option_id: :obj:`str`

    :param order_info: Optional. Order information provided by the user
    :type order_info: :class:`telebot.types.OrderInfo`

    :param telegram_payment_charge_id: Telegram payment identifier
    :type telegram_payment_charge_id: :obj:`str`

    :param provider_payment_charge_id: Provider payment identifier
    :type provider_payment_charge_id: :obj:`str`

    :return: Instance of the class
    :rtype: :class:`telebot.types.SuccessfulPayment`
    """
    @classmethod
    def de_json(cls, json_string):
        if json_string is None: return None
        obj = cls.check_json(json_string)
        obj['order_info'] = OrderInfo.de_json(obj.get('order_info'))
        return cls(**obj)

    def __init__(self, currency, total_amount, invoice_payload, shipping_option_id=None, order_info=None,
                 telegram_payment_charge_id=None, provider_payment_charge_id=None, 
                    subscription_expiration_date=None, is_recurring=None, is_first_recurring=None, **kwargs):
        self.currency: str = currency
        self.total_amount: int = total_amount
        self.invoice_payload: str = invoice_payload
        self.shipping_option_id: str = shipping_option_id
        self.order_info: OrderInfo = order_info
        self.telegram_payment_charge_id: str = telegram_payment_charge_id
        self.provider_payment_charge_id: str = provider_payment_charge_id
        self.subscription_expiration_date: Optional[int] = subscription_expiration_date
        self.is_recurring: Optional[bool] = is_recurring
        self.is_first_recurring: Optional[bool] = is_first_recurring


# noinspection PyShadowingBuiltins
class ShippingQuery(JsonDeserializable):
    """
    This object contains information about an incoming shipping query.

    Telegram Documentation: https://core.telegram.org/bots/api#shippingquery

    :param id: Unique query identifier
    :type id: :obj:`str`

    :param from: User who sent the query
    :type from: :class:`telebot.types.User`

    :param invoice_payload: Bot specified invoice payload
    :type invoice_payload: :obj:`str`

    :param shipping_address: User specified shipping address
    :type shipping_address: :class:`telebot.types.ShippingAddress`

    :return: Instance of the class
    :rtype: :class:`telebot.types.ShippingQuery`
    """
    @classmethod
    def de_json(cls, json_string):
        if json_string is None: return None
        obj = cls.check_json(json_string)
        obj['from_user'] = User.de_json(obj.pop('from'))
        obj['shipping_address'] = ShippingAddress.de_json(obj['shipping_address'])
        return cls(**obj)

    def __init__(self, id, from_user, invoice_payload, shipping_address, **kwargs):
        self.id: str = id
        self.from_user: User = from_user
        self.invoice_payload: str = invoice_payload
        self.shipping_address: ShippingAddress = shipping_address


# noinspection PyShadowingBuiltins
class PreCheckoutQuery(JsonDeserializable):
    """
    This object contains information about an incoming pre-checkout query.

    Telegram Documentation: https://core.telegram.org/bots/api#precheckoutquery

    :param id: Unique query identifier
    :type id: :obj:`str`

    :param from: User who sent the query
    :type from: :class:`telebot.types.User`

    :param currency: Three-letter ISO 4217 currency code
    :type currency: :obj:`str`

    :param total_amount: Total price in the smallest units of the currency (integer, not float/double). For example, 
        for a price of US$ 1.45 pass amount = 145. See the exp parameter in currencies.json, it shows the number of digits past 
        the decimal point for each currency (2 for the majority of currencies).
    :type total_amount: :obj:`int`

    :param invoice_payload: Bot specified invoice payload
    :type invoice_payload: :obj:`str`

    :param shipping_option_id: Optional. Identifier of the shipping option chosen by the user
    :type shipping_option_id: :obj:`str`

    :param order_info: Optional. Order information provided by the user
    :type order_info: :class:`telebot.types.OrderInfo`

    :return: Instance of the class
    :rtype: :class:`telebot.types.PreCheckoutQuery`
    """
    @classmethod
    def de_json(cls, json_string):
        if json_string is None: return None
        obj = cls.check_json(json_string)
        obj['from_user'] = User.de_json(obj.pop('from'))
        obj['order_info'] = OrderInfo.de_json(obj.get('order_info'))
        return cls(**obj)

    def __init__(self, id, from_user, currency, total_amount, invoice_payload, shipping_option_id=None, order_info=None, **kwargs):
        self.id: str = id
        self.from_user: User = from_user
        self.currency: str = currency
        self.total_amount: int = total_amount
        self.invoice_payload: str = invoice_payload
        self.shipping_option_id: Optional[str] = shipping_option_id
        self.order_info: Optional[OrderInfo] = order_info


# Stickers

class StickerSet(JsonDeserializable):
    """
    This object represents a sticker set.

    Telegram Documentation: https://core.telegram.org/bots/api#stickerset

    :param name: Sticker set name
    :type name: :obj:`str`

    :param title: Sticker set title
    :type title: :obj:`str`

    :param sticker_type: Type of stickers in the set, currently one of “regular”, “mask”, “custom_emoji”
    :type sticker_type: :obj:`str`

    :param stickers: List of all set stickers
    :type stickers: :obj:`list` of :class:`telebot.types.Sticker`

    :param thumbnail: Optional. Sticker set thumbnail in the .WEBP, .TGS, or .WEBM format
    :type thumbnail: :class:`telebot.types.PhotoSize`

    :return: Instance of the class
    :rtype: :class:`telebot.types.StickerSet`
    """
    @classmethod
    def de_json(cls, json_string):
        if json_string is None: return None
        obj = cls.check_json(json_string)
        stickers = []
        for s in obj['stickers']:
            stickers.append(Sticker.de_json(s))
        obj['stickers'] = stickers
        if 'thumbnail' in obj and 'file_id' in obj['thumbnail']:
            obj['thumbnail'] = PhotoSize.de_json(obj['thumbnail'])
        else:
            obj['thumbnail'] = None
        return cls(**obj)

    def __init__(self, name, title, sticker_type, stickers, thumbnail=None, **kwargs):
        self.name: str = name
        self.title: str = title
        self.sticker_type: str = sticker_type
        self.stickers: List[Sticker] = stickers
        self.thumbnail: Optional[PhotoSize] = thumbnail

    @property
    def thumb(self) -> Optional[PhotoSize]:
        log_deprecation_warning('The parameter "thumb" is deprecated, use "thumbnail" instead')
        return self.thumbnail

    @property
    def contains_masks(self) -> bool:
        log_deprecation_warning('The parameter "contains_masks" is deprecated, use "sticker_type instead"')
        return self.sticker_type == 'mask'

    @property
    def is_animated(self) -> bool:
        log_deprecation_warning('The parameter "is_animated" is deprecated since Bot API 7.2. Stickers can now be mixed')
        return False

    @property
    def is_video(self) -> bool:
        log_deprecation_warning('The parameter "is_video" is deprecated since Bot API 7.2. Stickers can now be mixed')
        return False


# noinspection PyShadowingBuiltins
class Sticker(JsonDeserializable):
    """
    This object represents a sticker.

    Telegram Documentation: https://core.telegram.org/bots/api#sticker

    :param file_id: Identifier for this file, which can be used to download or reuse the file
    :type file_id: :obj:`str`

    :param file_unique_id: Unique identifier for this file, which is supposed to be the same over time and for different 
        bots. Can't be used to download or reuse the file.
    :type file_unique_id: :obj:`str`

    :param type: Type of the sticker, currently one of “regular”, “mask”, “custom_emoji”. The type of the sticker is
        independent from its format, which is determined by the fields is_animated and is_video.
    :type type: :obj:`str`

    :param width: Sticker width
    :type width: :obj:`int`

    :param height: Sticker height
    :type height: :obj:`int`

    :param is_animated: True, if the sticker is animated
    :type is_animated: :obj:`bool`

    :param is_video: True, if the sticker is a video sticker
    :type is_video: :obj:`bool`

    :param thumbnail: Optional. Sticker thumbnail in the .WEBP or .JPG format
    :type thumbnail: :class:`telebot.types.PhotoSize`

    :param emoji: Optional. Emoji associated with the sticker
    :type emoji: :obj:`str`

    :param set_name: Optional. Name of the sticker set to which the sticker belongs
    :type set_name: :obj:`str`

    :param premium_animation: Optional. Premium animation for the sticker, if the sticker is premium
    :type premium_animation: :class:`telebot.types.File`

    :param mask_position: Optional. For mask stickers, the position where the mask should be placed
    :type mask_position: :class:`telebot.types.MaskPosition`

    :param custom_emoji_id: Optional. For custom emoji stickers, unique identifier of the custom emoji
    :type custom_emoji_id: :obj:`str`

    :param needs_repainting: Optional. True, if the sticker must be repainted to a text color in messages,
        the color of the Telegram Premium badge in emoji status, white color on chat photos, or another
        appropriate color in other places
    :type needs_repainting: :obj:`bool`

    :param file_size: Optional. File size in bytes
    :type file_size: :obj:`int`

    :return: Instance of the class
    :rtype: :class:`telebot.types.Sticker`
    """

    @classmethod
    def de_json(cls, json_string):
        if json_string is None: return None
        obj = cls.check_json(json_string)
        if 'thumbnail' in obj and 'file_id' in obj['thumbnail']:
            obj['thumbnail'] = PhotoSize.de_json(obj['thumbnail'])
        else:
            obj['thumbnail'] = None
        if 'mask_position' in obj:
            obj['mask_position'] = MaskPosition.de_json(obj['mask_position'])
        if 'premium_animation' in obj:
            obj['premium_animation'] = File.de_json(obj['premium_animation'])
        return cls(**obj)

    def __init__(self, file_id, file_unique_id, type, width, height, is_animated, 
                is_video, thumbnail=None, emoji=None, set_name=None, mask_position=None, file_size=None, 
                premium_animation=None, custom_emoji_id=None, needs_repainting=None, **kwargs):
        self.file_id: str = file_id
        self.file_unique_id: str = file_unique_id
        self.type: str = type
        self.width: int = width
        self.height: int = height
        self.is_animated: bool = is_animated
        self.is_video: bool = is_video
        self.thumbnail: Optional[PhotoSize] = thumbnail
        self.emoji: Optional[str] = emoji
        self.set_name: Optional[str] = set_name
        self.mask_position: Optional[MaskPosition] = mask_position
        self.file_size: Optional[int] = file_size
        self.premium_animation: Optional[File] = premium_animation
        self.custom_emoji_id: Optional[str] = custom_emoji_id
        self.needs_repainting: Optional[bool] = needs_repainting

    @property
    def thumb(self) -> Optional[PhotoSize]:
        log_deprecation_warning('The parameter "thumb" is deprecated, use "thumbnail" instead')
        return self.thumbnail


class MaskPosition(Dictionaryable, JsonDeserializable, JsonSerializable):
    """
    This object describes the position on faces where a mask should be placed by default.

    Telegram Documentation: https://core.telegram.org/bots/api#maskposition

    :param point: The part of the face relative to which the mask should be placed. One of “forehead”, “eyes”, “mouth”, or 
        “chin”.
    :type point: :obj:`str`

    :param x_shift: Shift by X-axis measured in widths of the mask scaled to the face size, from left to right. For example, 
        choosing -1.0 will place mask just to the left of the default mask position.
    :type x_shift: :obj:`float` number

    :param y_shift: Shift by Y-axis measured in heights of the mask scaled to the face size, from top to bottom. For 
        example, 1.0 will place the mask just below the default mask position.
    :type y_shift: :obj:`float` number

    :param scale: Mask scaling coefficient. For example, 2.0 means double size.
    :type scale: :obj:`float` number

    :return: Instance of the class
    :rtype: :class:`telebot.types.MaskPosition`
    """

    @classmethod
    def de_json(cls, json_string):
        if json_string is None: return None
        obj = cls.check_json(json_string, dict_copy=False)
        return cls(**obj)

    def __init__(self, point, x_shift, y_shift, scale, **kwargs):
        self.point: str = point
        self.x_shift: float = x_shift
        self.y_shift: float = y_shift
        self.scale: float = scale

    def to_json(self):
        return json.dumps(self.to_dict())

    def to_dict(self):
        return {'point': self.point, 'x_shift': self.x_shift, 'y_shift': self.y_shift, 'scale': self.scale}


# InputMedia

# noinspection PyShadowingBuiltins
class InputMedia(Dictionaryable, JsonSerializable):
    """
    This object represents the content of a media message to be sent. It should be one of

    * :class:`InputMediaAnimation`
    * :class:`InputMediaDocument`
    * :class:`InputMediaAudio`
    * :class:`InputMediaPhoto`
    * :class:`InputMediaVideo`
    """
    def __init__(self, type, media, caption=None, parse_mode=None, caption_entities=None, thumbnail=None):
        self.type: str = type
        self.media: str = media
        self.caption: Optional[str] = caption
        self.parse_mode: Optional[str] = parse_mode
        self.caption_entities: Optional[List[MessageEntity]] = caption_entities
        self.thumbnail: Optional[Union[str, InputFile]] = thumbnail

        if thumbnail is None:
            self._thumbnail_name = ''
            self._thumbnail_dic = None
        elif service_utils.is_string(self.thumbnail):
            self._thumbnail_name = ''
            self._thumbnail_dic = self.thumbnail
        else:
            self._thumbnail_name = service_utils.generate_random_token()
            self._thumbnail_dic = 'attach://{0}'.format(self._thumbnail_name)

        if service_utils.is_string(self.media):
            self._media_name = ''
            self._media_dic = self.media
        else:
            self._media_name = service_utils.generate_random_token()
            self._media_dic = 'attach://{0}'.format(self._media_name)

    def to_json(self):
        return json.dumps(self.to_dict())

    def to_dict(self):
        json_dict = {'type': self.type, 'media': self._media_dic}
        if self._thumbnail_dic:
            json_dict['thumbnail'] = self._thumbnail_dic
        if self.caption:
            json_dict['caption'] = self.caption
        if self.parse_mode:
            json_dict['parse_mode'] = self.parse_mode
        if self.caption_entities:
            json_dict['caption_entities'] = MessageEntity.to_list_of_dicts(self.caption_entities)
        return json_dict

    def convert_input_media(self):
        """
        :meta private:
        """
        if service_utils.is_string(self.media):
            return self.to_json(), None
        
        media_dict = {self._media_name: self.media}
        if self._thumbnail_name:
            media_dict[self._thumbnail_name] = self.thumbnail

        return self.to_json(), media_dict


class InputMediaPhoto(InputMedia):
    """
    Represents a photo to be sent.

    Telegram Documentation: https://core.telegram.org/bots/api#inputmediaphoto

    :param media: File to send. Pass a file_id to send a file that exists on the Telegram servers (recommended), pass an 
        HTTP URL for Telegram to get a file from the Internet, or pass “attach://<file_attach_name>” to upload a new one using 
        multipart/form-data under <file_attach_name> name. More information on Sending Files »
    :type media: :obj:`str`

    :param caption: Optional. Caption of the photo to be sent, 0-1024 characters after entities parsing
    :type caption: :obj:`str`

    :param parse_mode: Optional. Mode for parsing entities in the photo caption. See formatting options for more 
        details.
    :type parse_mode: :obj:`str`

    :param caption_entities: Optional. List of special entities that appear in the caption, which can be specified 
        instead of parse_mode
    :type caption_entities: :obj:`list` of :class:`telebot.types.MessageEntity`

    :param has_spoiler: Optional. True, if the uploaded photo is a spoiler
    :type has_spoiler: :obj:`bool`

    :param show_caption_above_media: Optional. True, if the caption should be shown above the photo
    :type show_caption_above_media: :obj:`bool`

    :return: Instance of the class
    :rtype: :class:`telebot.types.InputMediaPhoto`
    """
    def __init__(self, media: Union[str, InputFile], caption: Optional[str] = None,
                 parse_mode: Optional[str] = None, caption_entities: Optional[List[MessageEntity]] = None,
                 has_spoiler: Optional[bool] = None, show_caption_above_media: Optional[bool] = None):
        if service_utils.is_pil_image(media):
            media = service_utils.pil_image_to_file(media)
    
        super(InputMediaPhoto, self).__init__(
            type="photo", media=media, caption=caption, parse_mode=parse_mode, caption_entities=caption_entities)

        self.has_spoiler: Optional[bool] = has_spoiler
        self.show_caption_above_media: Optional[bool] = show_caption_above_media

    def to_dict(self):
        ret = super(InputMediaPhoto, self).to_dict()
        if self.has_spoiler is not None:
            ret['has_spoiler'] = self.has_spoiler
        if self.show_caption_above_media is not None:
            ret['show_caption_above_media'] = self.show_caption_above_media
        return ret


class InputMediaVideo(InputMedia):
    """
    Represents a video to be sent.

    Telegram Documentation: https://core.telegram.org/bots/api#inputmediavideo

    :param media: File to send. Pass a file_id to send a file that exists on the Telegram servers (recommended), pass an 
        HTTP URL for Telegram to get a file from the Internet, or pass “attach://<file_attach_name>” to upload a new one using 
        multipart/form-data under <file_attach_name> name. More information on Sending Files »
    :type media: :obj:`str`

    :param thumbnail: Optional. Thumbnail of the file sent; can be ignored if thumbnail generation for the file is supported 
        server-side. The thumbnail should be in JPEG format and less than 200 kB in size. A thumbnail's width and height should 
        not exceed 320. Ignored if the file is not uploaded using multipart/form-data. Thumbnails can't be reused and can be 
        only uploaded as a new file, so you can pass “attach://<file_attach_name>” if the thumbnail was uploaded using 
        multipart/form-data under <file_attach_name>. More information on Sending Files »
    :type thumbnail: InputFile or :obj:`str`

    :param cover: Cover for the video in the message. Pass a file_id to send a file that exists on the Telegram servers (recommended),
        pass an HTTP URL for Telegram to get a file from the Internet, or pass “attach://<file_attach_name>” to upload a new one using multipart/form-data under
        <file_attach_name> name. More information on Sending Files »
    :type cover: :obj:`str` or :class:`telebot.types.InputFile`

    :param start_timestamp: Start timestamp for the video in the message
    :type start_timestamp: :obj:`int`

    :param caption: Optional. Caption of the video to be sent, 0-1024 characters after entities parsing
    :type caption: :obj:`str`

    :param parse_mode: Optional. Mode for parsing entities in the video caption. See formatting options for more 
        details.
    :type parse_mode: :obj:`str`

    :param caption_entities: Optional. List of special entities that appear in the caption, which can be specified 
        instead of parse_mode
    :type caption_entities: :obj:`list` of :class:`telebot.types.MessageEntity`

    :param width: Optional. Video width
    :type width: :obj:`int`

    :param height: Optional. Video height
    :type height: :obj:`int`

    :param duration: Optional. Video duration in seconds
    :type duration: :obj:`int`

    :param supports_streaming: Optional. Pass True, if the uploaded video is suitable for streaming
    :type supports_streaming: :obj:`bool`

    :param has_spoiler: Optional. True, if the uploaded video is a spoiler
    :type has_spoiler: :obj:`bool`

    :param show_caption_above_media: Optional. True, if the caption should be shown above the video
    :type show_caption_above_media: :obj:`bool`

    :return: Instance of the class
    :rtype: :class:`telebot.types.InputMediaVideo`
    """
    def __init__(self, media: Union[str, InputFile], thumbnail: Optional[Union[str, InputFile]] = None,
                    caption: Optional[str] = None, parse_mode: Optional[str] = None,
                    caption_entities: Optional[List[MessageEntity]] = None, width: Optional[int] = None,
                    height: Optional[int] = None, duration: Optional[int] = None,
                    supports_streaming: Optional[bool] = None, has_spoiler: Optional[bool] = None,
                    show_caption_above_media: Optional[bool] = None, cover: Optional[Union[str, InputFile]] = None,
                    start_timestamp: Optional[int] = None):
        super(InputMediaVideo, self).__init__(
            type="video", media=media, caption=caption, parse_mode=parse_mode, caption_entities=caption_entities, thumbnail=thumbnail)
        self.width: Optional[int] = width
        self.height: Optional[int] = height
        self.duration: Optional[int] = duration
        self.supports_streaming: Optional[bool] = supports_streaming
        self.has_spoiler: Optional[bool] = has_spoiler
        self.show_caption_above_media: Optional[bool] = show_caption_above_media
        self.cover: Optional[str] = cover
        self.start_timestamp: Optional[int] = start_timestamp

    @property
    def thumb(self) -> Optional[Union[str, Any]]:
        log_deprecation_warning('The parameter "thumb" is deprecated, use "thumbnail" instead')
        return self.thumbnail

    def to_dict(self):
        ret = super(InputMediaVideo, self).to_dict()
        if self.width:
            ret['width'] = self.width
        if self.height:
            ret['height'] = self.height
        if self.duration:
            ret['duration'] = self.duration
        if self.supports_streaming is not None:
            ret['supports_streaming'] = self.supports_streaming
        if self.has_spoiler is not None:
            ret['has_spoiler'] = self.has_spoiler
        if self.show_caption_above_media is not None:
            ret['show_caption_above_media'] = self.show_caption_above_media
        if self.cover:
            ret['cover'] = self.cover
        if self.start_timestamp:
            ret['start_timestamp'] = self.start_timestamp
        return ret


class InputMediaAnimation(InputMedia):
    """
    Represents an animation file (GIF or H.264/MPEG-4 AVC video without sound) to be sent.

    Telegram Documentation: https://core.telegram.org/bots/api#inputmediaanimation

    :param media: File to send. Pass a file_id to send a file that exists on the Telegram servers (recommended), pass an 
        HTTP URL for Telegram to get a file from the Internet, or pass “attach://<file_attach_name>” to upload a new one using 
        multipart/form-data under <file_attach_name> name. More information on Sending Files »
    :type media: :obj:`str`

    :param thumbnail: Optional. Thumbnail of the file sent; can be ignored if thumbnail generation for the file is supported
        server-side. The thumbnail should be in JPEG format and less than 200 kB in size. A thumbnail's width and height should 
        not exceed 320. Ignored if the file is not uploaded using multipart/form-data. Thumbnails can't be reused and can be 
        only uploaded as a new file, so you can pass “attach://<file_attach_name>” if the thumbnail was uploaded using 
        multipart/form-data under <file_attach_name>. More information on Sending Files »
    :type thumbnail: InputFile or :obj:`str`

    :param caption: Optional. Caption of the animation to be sent, 0-1024 characters after entities parsing
    :type caption: :obj:`str`

    :param parse_mode: Optional. Mode for parsing entities in the animation caption. See formatting options for more 
        details.
    :type parse_mode: :obj:`str`

    :param caption_entities: Optional. List of special entities that appear in the caption, which can be specified 
        instead of parse_mode
    :type caption_entities: :obj:`list` of :class:`telebot.types.MessageEntity`

    :param width: Optional. Animation width
    :type width: :obj:`int`

    :param height: Optional. Animation height
    :type height: :obj:`int`

    :param duration: Optional. Animation duration in seconds
    :type duration: :obj:`int`

    :param has_spoiler: Optional. True, if the uploaded animation is a spoiler
    :type has_spoiler: :obj:`bool`

    :param show_caption_above_media: Optional. True, if the caption should be shown above the animation
    :type show_caption_above_media: :obj:`bool`

    :return: Instance of the class
    :rtype: :class:`telebot.types.InputMediaAnimation`
    """

    def __init__(self, media: Union[str, InputFile], thumbnail: Optional[Union[str, InputFile]] = None,
                    caption: Optional[str] = None, parse_mode: Optional[str] = None,
                    caption_entities: Optional[List[MessageEntity]] = None, width: Optional[int] = None,
                    height: Optional[int] = None, duration: Optional[int] = None,
                    has_spoiler: Optional[bool] = None, show_caption_above_media: Optional[bool] = None):
        super(InputMediaAnimation, self).__init__(
            type="animation", media=media, caption=caption, parse_mode=parse_mode, caption_entities=caption_entities, thumbnail=thumbnail)
        self.width: Optional[int] = width
        self.height: Optional[int] = height
        self.duration: Optional[int] = duration
        self.has_spoiler: Optional[bool] = has_spoiler
        self.show_caption_above_media: Optional[bool] = show_caption_above_media


    @property
    def thumb(self) -> Optional[Union[str, Any]]:
        log_deprecation_warning('The parameter "thumb" is deprecated, use "thumbnail" instead')
        return self.thumbnail

    def to_dict(self):
        ret = super(InputMediaAnimation, self).to_dict()
        if self.width:
            ret['width'] = self.width
        if self.height:
            ret['height'] = self.height
        if self.duration:
            ret['duration'] = self.duration
        if self.has_spoiler is not None:
            ret['has_spoiler'] = self.has_spoiler
        if self.show_caption_above_media is not None:
            ret['show_caption_above_media'] = self.show_caption_above_media
        return ret


class InputMediaAudio(InputMedia):
    """
    Represents an audio file to be treated as music to be sent.

    Telegram Documentation: https://core.telegram.org/bots/api#inputmediaaudio

    :param media: File to send. Pass a file_id to send a file that exists on the Telegram servers (recommended), pass an 
        HTTP URL for Telegram to get a file from the Internet, or pass “attach://<file_attach_name>” to upload a new one using 
        multipart/form-data under <file_attach_name> name. More information on Sending Files »
    :type media: :obj:`str`

    :param thumbnail: Optional. Thumbnail of the file sent; can be ignored if thumbnail generation for the file is supported 
        server-side. The thumbnail should be in JPEG format and less than 200 kB in size. A thumbnail's width and height should 
        not exceed 320. Ignored if the file is not uploaded using multipart/form-data. Thumbnails can't be reused and can be 
        only uploaded as a new file, so you can pass “attach://<file_attach_name>” if the thumbnail was uploaded using 
        multipart/form-data under <file_attach_name>. More information on Sending Files »
    :type thumbnail: InputFile or :obj:`str`

    :param caption: Optional. Caption of the audio to be sent, 0-1024 characters after entities parsing
    :type caption: :obj:`str`

    :param parse_mode: Optional. Mode for parsing entities in the audio caption. See formatting options for more 
        details.
    :type parse_mode: :obj:`str`

    :param caption_entities: Optional. List of special entities that appear in the caption, which can be specified 
        instead of parse_mode
    :type caption_entities: :obj:`list` of :class:`telebot.types.MessageEntity`

    :param duration: Optional. Duration of the audio in seconds
    :type duration: :obj:`int`

    :param performer: Optional. Performer of the audio
    :type performer: :obj:`str`

    :param title: Optional. Title of the audio
    :type title: :obj:`str`

    :return: Instance of the class
    :rtype: :class:`telebot.types.InputMediaAudio`
    """
    def __init__(self, media: Union[str, InputFile], thumbnail: Optional[Union[str, InputFile]] = None,
                    caption: Optional[str] = None, parse_mode: Optional[str] = None,
                    caption_entities: Optional[List[MessageEntity]] = None, duration: Optional[int] = None,
                    performer: Optional[str] = None, title: Optional[str] = None):
        super(InputMediaAudio, self).__init__(
            type="audio", media=media, caption=caption, parse_mode=parse_mode, caption_entities=caption_entities, thumbnail=thumbnail)
        self.duration: Optional[int] = duration
        self.performer: Optional[str] = performer
        self.title: Optional[str] = title

    @property
    def thumb(self) -> Optional[Union[str, Any]]:
        log_deprecation_warning('The parameter "thumb" is deprecated, use "thumbnail" instead')
        return self.thumbnail

    def to_dict(self):
        ret = super(InputMediaAudio, self).to_dict()
        if self.duration:
            ret['duration'] = self.duration
        if self.performer:
            ret['performer'] = self.performer
        if self.title:
            ret['title'] = self.title
        return ret


class InputMediaDocument(InputMedia):
    """
    Represents a general file to be sent.

    Telegram Documentation: https://core.telegram.org/bots/api#inputmediadocument

    :param media: File to send. Pass a file_id to send a file that exists on the Telegram servers (recommended), pass an
        HTTP URL for Telegram to get a file from the Internet, or pass “attach://<file_attach_name>” to upload a new one using 
        multipart/form-data under <file_attach_name> name. More information on Sending Files »
    :type media: :obj:`str`

    :param thumbnail: Optional. Thumbnail of the file sent; can be ignored if thumbnail generation for the file is supported 
        server-side. The thumbnail should be in JPEG format and less than 200 kB in size. A thumbnail's width and height should 
        not exceed 320. Ignored if the file is not uploaded using multipart/form-data. Thumbnails can't be reused and can be 
        only uploaded as a new file, so you can pass “attach://<file_attach_name>” if the thumbnail was uploaded using 
        multipart/form-data under <file_attach_name>. More information on Sending Files »
    :type thumbnail: InputFile or :obj:`str`

    :param caption: Optional. Caption of the document to be sent, 0-1024 characters after entities parsing
    :type caption: :obj:`str`

    :param parse_mode: Optional. Mode for parsing entities in the document caption. See formatting options for more 
        details.
    :type parse_mode: :obj:`str`

    :param caption_entities: Optional. List of special entities that appear in the caption, which can be specified 
        instead of parse_mode
    :type caption_entities: :obj:`list` of :class:`telebot.types.MessageEntity`

    :param disable_content_type_detection: Optional. Disables automatic server-side content type detection for 
        files uploaded using multipart/form-data. Always True, if the document is sent as part of an album.
    :type disable_content_type_detection: :obj:`bool`

    :return: Instance of the class
    :rtype: :class:`telebot.types.InputMediaDocument`
    """
    def __init__(self, media: Union[str, InputFile], thumbnail: Optional[Union[str, InputFile]] = None,
                    caption: Optional[str] = None, parse_mode: Optional[str] = None,
                    caption_entities: Optional[List[MessageEntity]] = None,
                    disable_content_type_detection: Optional[bool] = None):
        super(InputMediaDocument, self).__init__(
            type="document", media=media, caption=caption, parse_mode=parse_mode, caption_entities=caption_entities, thumbnail=thumbnail)
        self.disable_content_type_detection: Optional[bool] = disable_content_type_detection

    @property
    def thumb(self) -> Optional[Union[str, Any]]:
        log_deprecation_warning('The parameter "thumb" is deprecated, use "thumbnail" instead')
        return self.thumbnail

    def to_dict(self):
        ret = super(InputMediaDocument, self).to_dict()
        if self.disable_content_type_detection is not None:
            ret['disable_content_type_detection'] = self.disable_content_type_detection
        return ret


class PollOption(JsonDeserializable):
    """
    This object contains information about one answer option in a poll.

    Telegram Documentation: https://core.telegram.org/bots/api#polloption

    :param text: Option text, 1-100 characters
    :type text: :obj:`str`

    :param voter_count: Number of users that voted for this option
    :type voter_count: :obj:`int`

    :param text_entities: Optional. Special entities that appear in the option text. Currently, only custom emoji entities are allowed in poll option texts
    :type text_entities: :obj:`list` of :class:`telebot.types.MessageEntity`

    :return: Instance of the class
    :rtype: :class:`telebot.types.PollOption`
    """
    @classmethod
    def de_json(cls, json_string):
        if json_string is None: return None
        obj = cls.check_json(json_string, dict_copy=False)
        if 'text_entities' in obj:
            obj['text_entities'] = Message.parse_entities(obj['text_entities'])
        return cls(**obj)

    def __init__(self, text, voter_count = 0, text_entities=None, **kwargs):
        self.text: str = text
        self.voter_count: int = voter_count
        self.text_entities: Optional[List[MessageEntity]] = text_entities
    # Converted in _convert_poll_options
    # def to_json(self):
    #     # send_poll Option is a simple string: https://core.telegram.org/bots/api#sendpoll
    #     return json.dumps(self.text)


class InputPollOption(JsonSerializable):
    """
    This object contains information about one answer option in a poll to send.

    Telegram Documentation: https://core.telegram.org/bots/api#inputpolloption

    :param text: Option text, 1-100 characters
    :type text: :obj:`str`

    :param text_parse_mode: Optional. Mode for parsing entities in the text. See formatting options for more details. Currently, only custom emoji entities are allowed
    :type text_parse_mode: :obj:`str`

    :param text_entities: Optional. A JSON-serialized list of special entities that appear in the poll option text. It can be specified instead of text_parse_mode
    :type text_entities: :obj:`list` of :class:`telebot.types.MessageEntity`

    :return: Instance of the class
    :rtype: :class:`telebot.types.PollOption`
    """
    def __init__(self, text: str, text_parse_mode: Optional[str] = None, text_entities: Optional[List[MessageEntity]] = None,
                    **kwargs):
        self.text: str = text
        self.text_parse_mode: Optional[str] = text_parse_mode
        self.text_entities: Optional[List[MessageEntity]] = text_entities

    def to_json(self):
        return json.dumps(self.to_dict())

    def to_dict(self):
        json_dict = {
            "text": self.text,
        }
        if self.text_parse_mode:
            json_dict["text_parse_mode"] = self.text_parse_mode
        if self.text_entities:
            json_dict['text_entities'] = [entity.to_dict() for entity in self.text_entities]
        return json_dict


# noinspection PyShadowingBuiltins
class Poll(JsonDeserializable):
    """
    This object contains information about a poll.

    Telegram Documentation: https://core.telegram.org/bots/api#poll

    :param id: Unique poll identifier
    :type id: :obj:`str`

    :param question: Poll question, 1-300 characters
    :type question: :obj:`str`

    :param options: List of poll options
    :type options: :obj:`list` of :class:`telebot.types.PollOption`

    :param total_voter_count: Total number of users that voted in the poll
    :type total_voter_count: :obj:`int`

    :param is_closed: True, if the poll is closed
    :type is_closed: :obj:`bool`

    :param is_anonymous: True, if the poll is anonymous
    :type is_anonymous: :obj:`bool`

    :param type: Poll type, currently can be “regular” or “quiz”
    :type type: :obj:`str`

    :param allows_multiple_answers: True, if the poll allows multiple answers
    :type allows_multiple_answers: :obj:`bool`

    :param correct_option_id: Optional. 0-based identifier of the correct answer option. Available only for polls in the quiz mode, which are closed, or was sent (not forwarded) by the bot or to the private chat with the bot.
    :type correct_option_id: :obj:`int`

    :param explanation: Optional. Text that is shown when a user chooses an incorrect answer or taps on the lamp icon in a quiz-style poll, 0-200 characters
    :type explanation: :obj:`str`

    :param explanation_entities: Optional. Special entities like usernames, URLs, bot commands, etc. that appear in the explanation
    :type explanation_entities: :obj:`list` of :class:`telebot.types.MessageEntity`

    :param open_period: Optional. Amount of time in seconds the poll will be active after creation
    :type open_period: :obj:`int`

    :param close_date: Optional. Point in time (Unix timestamp) when the poll will be automatically closed
    :type close_date: :obj:`int`

    :param question_entities: Optional. Special entities that appear in the question. Currently, only custom emoji entities are allowed in poll questions
    :type question_entities: :obj:`list` of :class:`telebot.types.MessageEntity`

    :return: Instance of the class
    :rtype: :class:`telebot.types.Poll`
    """
    @classmethod
    def de_json(cls, json_string):
        if json_string is None: return None
        obj = cls.check_json(json_string)
        obj['poll_id'] = obj.pop('id')
        options = []
        for opt in obj['options']:
            options.append(PollOption.de_json(opt))
        obj['options'] = options or None
        if 'explanation_entities' in obj:
            obj['explanation_entities'] = Message.parse_entities(obj['explanation_entities'])
        if 'question_entities' in obj:
            obj['question_entities'] = Message.parse_entities(obj['question_entities'])
        return cls(**obj)

    def __init__(
            self,
            question: str, options: List[PollOption],
            poll_id: str = None, total_voter_count: int = None, is_closed: bool = None, is_anonymous: bool = None,
            type: str = None, allows_multiple_answers: bool = None, correct_option_id: int = None,
            explanation: str = None, explanation_entities: List[MessageEntity] = None, open_period: int = None,
            close_date: int = None, poll_type: str = None, question_entities: List[MessageEntity] = None,
            **kwargs):
        self.id: str = poll_id
        self.question: str = question
        self.options: List[PollOption] = options
        self.total_voter_count: int = total_voter_count
        self.is_closed: bool = is_closed
        self.is_anonymous: bool = is_anonymous
        self.type: str = type
        if poll_type is not None:
            log_deprecation_warning("Poll: poll_type parameter is deprecated. Use type instead.")
            if type is None:
                self.type: str = poll_type
        self.allows_multiple_answers: bool = allows_multiple_answers
        self.correct_option_id: int = correct_option_id
        self.explanation: str = explanation
        self.explanation_entities: List[MessageEntity] = explanation_entities
        self.question_entities: List[MessageEntity] = question_entities
        self.open_period: int = open_period
        self.close_date: int = close_date

    def add(self, option):
        """
        Add an option to the poll.

        :param option: Option to add
        :type option: :class:`telebot.types.PollOption` or :obj:`str`
        """
        if type(option) is PollOption:
            self.options.append(option)
        else:
            self.options.append(PollOption(option))


class PollAnswer(JsonSerializable, JsonDeserializable, Dictionaryable):
    """
    This object represents an answer of a user in a non-anonymous poll.

    Telegram Documentation: https://core.telegram.org/bots/api#pollanswer

    :param poll_id: Unique poll identifier
    :type poll_id: :obj:`str`

    :param voter_chat: Optional. The chat that changed the answer to the poll, if the voter is anonymous
    :type voter_chat: :class:`telebot.types.Chat`

    :param user: Optional. The user, who changed the answer to the poll
    :type user: :class:`telebot.types.User`

    :param option_ids: 0-based identifiers of answer options, chosen by the user. May be empty if the user retracted 
        their vote.
    :type option_ids: :obj:`list` of :obj:`int`

    :return: Instance of the class
    :rtype: :class:`telebot.types.PollAnswer`
    """
    @classmethod
    def de_json(cls, json_string):
        if json_string is None: return None
        obj = cls.check_json(json_string)
        if 'user' in obj:
            obj['user'] = User.de_json(obj['user'])
        if 'voter_chat' in obj:
            obj['voter_chat'] = Chat.de_json(obj['voter_chat'])
        return cls(**obj)

    def __init__(self, poll_id: str, option_ids: List[int], user: Optional[User] = None, voter_chat: Optional[Chat] = None, **kwargs):
        self.poll_id: str = poll_id
        self.user: Optional[User] = user
        self.option_ids: Optional[List[int]] = option_ids
        self.voter_chat: Optional[Chat] = voter_chat


    def to_json(self):
        return json.dumps(self.to_dict())

    def to_dict(self):
        # Left for backward compatibility, but with no support for voter_chat
        json_dict = {
            "poll_id": self.poll_id,
            "option_ids": self.option_ids
        }
        if self.user:
            json_dict["user"] = self.user.to_dict()
        if self.voter_chat:
            json_dict["voter_chat"] = self.voter_chat
        return json_dict
    


class ChatLocation(JsonSerializable, JsonDeserializable, Dictionaryable):
    """
    Represents a location to which a chat is connected.

    Telegram Documentation: https://core.telegram.org/bots/api#chatlocation

    :param location: The location to which the supergroup is connected. Can't be a live location.
    :type location: :class:`telebot.types.Location`

    :param address: Location address; 1-64 characters, as defined by the chat owner
    :type address: :obj:`str`

    :return: Instance of the class
    :rtype: :class:`telebot.types.ChatLocation`
    """
    @classmethod
    def de_json(cls, json_string):
        if json_string is None: return None
        obj = cls.check_json(json_string)
        obj['location'] = Location.de_json(obj['location'])
        return cls(**obj)
    
    def __init__(self, location: Location, address: str, **kwargs):
        self.location: Location = location
        self.address: str = address

    def to_json(self):
        return json.dumps(self.to_dict())
    
    def to_dict(self):
        return {
            "location": self.location.to_dict(),
            "address": self.address
        }


class ChatInviteLink(JsonSerializable, JsonDeserializable, Dictionaryable):
    """
    Represents an invite link for a chat.

    Telegram Documentation: https://core.telegram.org/bots/api#chatinvitelink

    :param invite_link: The invite link. If the link was created by another chat administrator, then the second part of 
        the link will be replaced with “…”.
    :type invite_link: :obj:`str`

    :param creator: Creator of the link
    :type creator: :class:`telebot.types.User`

    :param creates_join_request: True, if users joining the chat via the link need to be approved by chat administrators
    :type creates_join_request: :obj:`bool`

    :param is_primary: True, if the link is primary
    :type is_primary: :obj:`bool`

    :param is_revoked: True, if the link is revoked
    :type is_revoked: :obj:`bool`

    :param name: Optional. Invite link name
    :type name: :obj:`str`

    :param expire_date: Optional. Point in time (Unix timestamp) when the link will expire or has been expired
    :type expire_date: :obj:`int`

    :param member_limit: Optional. The maximum number of users that can be members of the chat simultaneously after 
        joining the chat via this invite link; 1-99999
    :type member_limit: :obj:`int`

    :param pending_join_request_count: Optional. Number of pending join requests created using this link
    :type pending_join_request_count: :obj:`int`

    :return: Instance of the class
    :rtype: :class:`telebot.types.ChatInviteLink`
    """
    @classmethod
    def de_json(cls, json_string):
        if json_string is None: return None
        obj = cls.check_json(json_string)
        obj['creator'] = User.de_json(obj['creator'])
        return cls(**obj)
    
    def __init__(self, invite_link: str, creator: User, creates_join_request: bool, is_primary: bool, is_revoked: bool,
                name: Optional[str] = None, expire_date: Optional[int] = None, member_limit: Optional[int] = None,
                pending_join_request_count: Optional[int] = None, **kwargs):
        self.invite_link: str = invite_link
        self.creator: User = creator
        self.creates_join_request: bool = creates_join_request
        self.is_primary: bool = is_primary
        self.is_revoked: bool = is_revoked
        self.name: Optional[str] = name
        self.expire_date: Optional[int] = expire_date
        self.member_limit: Optional[int] = member_limit
        self.pending_join_request_count: Optional[int] = pending_join_request_count
    
    def to_json(self):
        return json.dumps(self.to_dict())
    
    def to_dict(self):
        json_dict = {
            "invite_link": self.invite_link,
            "creator": self.creator.to_dict(),
            "is_primary": self.is_primary,
            "is_revoked": self.is_revoked,
            "creates_join_request": self.creates_join_request
        }
        if self.expire_date:
            json_dict["expire_date"] = self.expire_date
        if self.member_limit:
            json_dict["member_limit"] = self.member_limit
        if self.pending_join_request_count:
            json_dict["pending_join_request_count"] = self.pending_join_request_count
        if self.name:
            json_dict["name"] = self.name
        return json_dict


class ProximityAlertTriggered(JsonDeserializable):
    """
    This object represents the content of a service message, sent whenever a user in the chat triggers a proximity alert set by another user.

    Telegram Documentation: https://core.telegram.org/bots/api#proximityalerttriggered

    :param traveler: User that triggered the alert
    :type traveler: :class:`telebot.types.User`

    :param watcher: User that set the alert
    :type watcher: :class:`telebot.types.User`

    :param distance: The distance between the users
    :type distance: :obj:`int`

    :return: Instance of the class
    :rtype: :class:`telebot.types.ProximityAlertTriggered`
    """
    @classmethod
    def de_json(cls, json_string):
        if json_string is None: return None
        obj = cls.check_json(json_string, dict_copy=False)
        return cls(**obj)
    
    def __init__(self, traveler, watcher, distance, **kwargs):
        self.traveler: User = traveler
        self.watcher: User = watcher
        self.distance: int = distance


class VideoChatStarted(JsonDeserializable):
    """
    This object represents a service message about a video chat started in the chat. Currently holds no information.
    """
    @classmethod
    def de_json(cls, json_string):
        return cls()
    
    def __init__(self):
        pass

class VoiceChatStarted(VideoChatStarted):
    """
    Deprecated, use :class:`VideoChatStarted` instead.
    """

    def __init__(self):
        log_deprecation_warning('VoiceChatStarted is deprecated. Use VideoChatStarted instead.')
        super().__init__()


class VideoChatScheduled(JsonDeserializable):
    """
    This object represents a service message about a video chat scheduled in the chat.

    Telegram Documentation: https://core.telegram.org/bots/api#videochatscheduled

    :param start_date: Point in time (Unix timestamp) when the video chat is supposed to be started by a chat 
        administrator
    :type start_date: :obj:`int`

    :return: Instance of the class
    :rtype: :class:`telebot.types.VideoChatScheduled`
    """
    @classmethod
    def de_json(cls, json_string):
        if json_string is None: return None
        obj = cls.check_json(json_string, dict_copy=False)
        return cls(**obj)
    
    def __init__(self, start_date, **kwargs):
        self.start_date: int = start_date


class VoiceChatScheduled(VideoChatScheduled):
    """
    Deprecated, use :class:`VideoChatScheduled` instead.
    """
    def __init__(self, *args, **kwargs):
        log_deprecation_warning('VoiceChatScheduled is deprecated. Use VideoChatScheduled instead.')
        super().__init__(*args, **kwargs)


class VideoChatEnded(JsonDeserializable):
    """
    This object represents a service message about a video chat ended in the chat.

    Telegram Documentation: https://core.telegram.org/bots/api#videochatended

    :param duration: Video chat duration in seconds
    :type duration: :obj:`int`

    :return: Instance of the class
    :rtype: :class:`telebot.types.VideoChatEnded`
    """
    @classmethod
    def de_json(cls, json_string):
        if json_string is None: return None
        obj = cls.check_json(json_string, dict_copy=False)
        return cls(**obj)
    
    def __init__(self, duration, **kwargs):
        self.duration: int = duration


class VoiceChatEnded(VideoChatEnded):
    """
    Deprecated, use :class:`VideoChatEnded` instead.
    """
    def __init__(self, *args, **kwargs):
        log_deprecation_warning('VoiceChatEnded is deprecated. Use VideoChatEnded instead.')
        super().__init__(*args, **kwargs)



class VideoChatParticipantsInvited(JsonDeserializable):
    """
    This object represents a service message about new members invited to a video chat.

    Telegram Documentation: https://core.telegram.org/bots/api#videochatparticipantsinvited

    :param users: New members that were invited to the video chat
    :type users: :obj:`list` of :class:`telebot.types.User`

    :return: Instance of the class
    :rtype: :class:`telebot.types.VideoChatParticipantsInvited`
    """
    @classmethod
    def de_json(cls, json_string):
        if json_string is None: return None
        obj = cls.check_json(json_string)
        obj['users'] = [User.de_json(u) for u in obj['users']]
        return cls(**obj)
    
    def __init__(self, users=None, **kwargs):
        self.users: List[User] = users


class VoiceChatParticipantsInvited(VideoChatParticipantsInvited):
    """
    Deprecated, use :class:`VideoChatParticipantsInvited` instead.
    """
    def __init__(self, *args, **kwargs):
        log_deprecation_warning('VoiceChatParticipantsInvited is deprecated. Use VideoChatParticipantsInvited instead.')
        super().__init__(*args, **kwargs)


class MessageAutoDeleteTimerChanged(JsonDeserializable):
    """
    This object represents a service message about a change in auto-delete timer settings.

    Telegram Documentation: https://core.telegram.org/bots/api#messageautodeletetimerchanged

    :param message_auto_delete_time: New auto-delete time for messages in the chat; in seconds
    :type message_auto_delete_time: :obj:`int`

    :return: Instance of the class
    :rtype: :class:`telebot.types.MessageAutoDeleteTimerChanged`
    """   
    @classmethod
    def de_json(cls, json_string):
        if json_string is None: return None
        obj = cls.check_json(json_string, dict_copy=False)
        return cls(**obj)

    def __init__(self, message_auto_delete_time, **kwargs):
        self.message_auto_delete_time: int = message_auto_delete_time


class MenuButton(JsonDeserializable, JsonSerializable, Dictionaryable):
    """
    This object describes the bot's menu button in a private chat. It should be one of

    * :class:`MenuButtonCommands`
    * :class:`MenuButtonWebApp`
    * :class:`MenuButtonDefault`
    
    If a menu button other than MenuButtonDefault is set for a private chat, then it is applied
    in the chat. Otherwise the default menu button is applied. By default, the menu button opens the list of bot commands.
    """
    @classmethod
    def de_json(cls, json_string):
        if json_string is None: return None
        obj = cls.check_json(json_string)
        types = {
            'commands': MenuButtonCommands,
            'web_app': MenuButtonWebApp,
            'default': MenuButtonDefault
        }
        return types[obj['type']](**obj)
    
    def to_json(self):
        """
        :meta private:
        """
        raise NotImplementedError

    def to_dict(self):
        """
        :meta private:
        """
        raise NotImplementedError


# noinspection PyUnusedLocal,PyShadowingBuiltins
class MenuButtonCommands(MenuButton):
    """
    Represents a menu button, which opens the bot's list of commands.

    Telegram Documentation: https://core.telegram.org/bots/api#menubuttoncommands

    :param type: Type of the button, must be commands
    :type type: :obj:`str`

    :return: Instance of the class
    :rtype: :class:`telebot.types.MenuButtonCommands`
    """

    def __init__(self, type: str = None, **kwargs):
        self.type: str = "commands"

    def to_dict(self):
        return {'type': self.type}
    
    def to_json(self):
        return json.dumps(self.to_dict())


# noinspection PyUnusedLocal,PyShadowingBuiltins
class MenuButtonWebApp(MenuButton):
    """
    Represents a menu button, which launches a Web App.

    Telegram Documentation: https://core.telegram.org/bots/api#menubuttonwebapp

    :param type: Type of the button, must be web_app
    :type type: :obj:`str`

    :param text: Text on the button
    :type text: :obj:`str`

    :param web_app: Description of the Web App that will be launched when the user presses the button. The Web App will be 
        able to send an arbitrary message on behalf of the user using the method answerWebAppQuery. Alternatively, a t.me link
        to a Web App of the bot can be specified in the object instead of the Web App's URL, in which case the Web App will be
        opened as if the user pressed the link.
    :type web_app: :class:`telebot.types.WebAppInfo`

    :return: Instance of the class
    :rtype: :class:`telebot.types.MenuButtonWebApp`
    """

    def __init__(self, type: str, text: str, web_app: WebAppInfo, **kwargs):
        self.type: str = "web_app"
        self.text: str = text
        self.web_app: WebAppInfo = web_app

    def to_dict(self):
        return {'type': self.type, 'text': self.text, 'web_app': self.web_app.to_dict()}

    def to_json(self):
        return json.dumps(self.to_dict())


# noinspection PyUnusedLocal,PyShadowingBuiltins
class MenuButtonDefault(MenuButton):
    """
    Describes that no specific value for the menu button was set.

    Telegram Documentation: https://core.telegram.org/bots/api#menubuttondefault

    :param type: Type of the button, must be default
    :type type: :obj:`str`

    :return: Instance of the class
    :rtype: :class:`telebot.types.MenuButtonDefault`
    """
    def __init__(self, type: str = None, **kwargs):
        self.type: str = "default"

    def to_dict(self):
        return {'type': self.type}

    def to_json(self):
        return json.dumps(self.to_dict())

    
class ChatAdministratorRights(JsonDeserializable, JsonSerializable, Dictionaryable):
    """
    Represents the rights of an administrator in a chat.

    Telegram Documentation: https://core.telegram.org/bots/api#chatadministratorrights

    :param is_anonymous: True, if the user's presence in the chat is hidden
    :type is_anonymous: :obj:`bool`

    :param can_manage_chat: True, if the administrator can access the chat event log, chat statistics, message 
        statistics in channels, see channel members, see anonymous administrators in supergroups and ignore slow mode. 
        Implied by any other administrator privilege
    :type can_manage_chat: :obj:`bool`

    :param can_delete_messages: True, if the administrator can delete messages of other users
    :type can_delete_messages: :obj:`bool`

    :param can_manage_video_chats: True, if the administrator can manage video chats
    :type can_manage_video_chats: :obj:`bool`

    :param can_restrict_members: True, if the administrator can restrict, ban or unban chat members
    :type can_restrict_members: :obj:`bool`

    :param can_promote_members: True, if the administrator can add new administrators with a subset of their own 
        privileges or demote administrators that he has promoted, directly or indirectly (promoted by administrators that 
        were appointed by the user)
    :type can_promote_members: :obj:`bool`

    :param can_change_info: True, if the user is allowed to change the chat title, photo and other settings
    :type can_change_info: :obj:`bool`

    :param can_invite_users: True, if the user is allowed to invite new users to the chat
    :type can_invite_users: :obj:`bool`

    :param can_post_messages: Optional. True, if the administrator can post in the channel; channels only
    :type can_post_messages: :obj:`bool`

    :param can_edit_messages: Optional. True, if the administrator can edit messages of other users and can pin 
        messages; channels only
    :type can_edit_messages: :obj:`bool`

    :param can_pin_messages: Optional. True, if the user is allowed to pin messages; groups and supergroups only
    :type can_pin_messages: :obj:`bool`

    :param can_manage_topics: Optional. True, if the user is allowed to create, rename, close, and reopen forum topics; supergroups only
    :type can_manage_topics: :obj:`bool`

    :param can_post_stories: Optional. True, if the administrator can post channel stories
    :type can_post_stories: :obj:`bool`

    :param can_edit_stories: Optional. True, if the administrator can edit stories
    :type can_edit_stories: :obj:`bool`

    :param can_delete_stories: Optional. True, if the administrator can delete stories of other users
    :type can_delete_stories: :obj:`bool`

    :return: Instance of the class
    :rtype: :class:`telebot.types.ChatAdministratorRights`
    """

    @classmethod
    def de_json(cls, json_string):
        if json_string is None: return None
        obj = cls.check_json(json_string)
        return cls(**obj)

    def __init__(self, is_anonymous: bool, can_manage_chat: bool, 
        can_delete_messages: bool, can_manage_video_chats: bool, can_restrict_members: bool,
        can_promote_members: bool, can_change_info: bool, can_invite_users: bool,
        can_post_messages: Optional[bool]=None, can_edit_messages: Optional[bool]=None,
        can_pin_messages: Optional[bool]=None, can_manage_topics: Optional[bool]=None,
        can_post_stories: Optional[bool]=None, can_edit_stories: Optional[bool]=None,
        can_delete_stories: Optional[bool]=None, **kwargs
        ) -> None:
        
        self.is_anonymous: bool = is_anonymous
        self.can_manage_chat: bool = can_manage_chat
        self.can_delete_messages: bool = can_delete_messages
        self.can_manage_video_chats: bool = can_manage_video_chats
        self.can_restrict_members: bool = can_restrict_members
        self.can_promote_members: bool = can_promote_members
        self.can_change_info: bool = can_change_info
        self.can_invite_users: bool = can_invite_users
        self.can_post_messages: Optional[bool] = can_post_messages
        self.can_edit_messages: Optional[bool] = can_edit_messages
        self.can_pin_messages: Optional[bool] = can_pin_messages
        self.can_manage_topics: Optional[bool] = can_manage_topics
        self.can_post_stories: Optional[bool] = can_post_stories
        self.can_edit_stories: Optional[bool] = can_edit_stories
        self.can_delete_stories: Optional[bool] = can_delete_stories

    def to_dict(self):
        json_dict = {
            'is_anonymous': self.is_anonymous,
            'can_manage_chat': self.can_manage_chat,
            'can_delete_messages': self.can_delete_messages,
            'can_manage_video_chats': self.can_manage_video_chats,
            'can_restrict_members': self.can_restrict_members,
            'can_promote_members': self.can_promote_members,
            'can_change_info': self.can_change_info,
            'can_invite_users': self.can_invite_users,
        }
        if self.can_post_messages is not None:
            json_dict['can_post_messages'] = self.can_post_messages
        if self.can_edit_messages is not None:
            json_dict['can_edit_messages'] = self.can_edit_messages
        if self.can_pin_messages is not None:
            json_dict['can_pin_messages'] = self.can_pin_messages
        if self.can_manage_topics is not None:
            json_dict['can_manage_topics'] = self.can_manage_topics
        if self.can_post_stories is not None:
            json_dict['can_post_stories'] = self.can_post_stories
        if self.can_edit_stories is not None:
            json_dict['can_edit_stories'] = self.can_edit_stories
        if self.can_delete_stories is not None:
            json_dict['can_delete_stories'] = self.can_delete_stories

        return json_dict
    
    def to_json(self):
        return json.dumps(self.to_dict())
    


class InputFile:
    """
    A class to send files through Telegram Bot API.

    You need to pass a file, which should be an instance of :class:`io.IOBase` or 
    :class:`pathlib.Path`, or :obj:`str`.

    If you pass an :obj:`str` as a file, it will be opened and closed by the class.

    :param file: A file to send.
    :type file: :class:`io.IOBase` or :class:`pathlib.Path` or :obj:`str`

    .. code-block:: python3
        :caption: Example on sending a file using this class

        from telebot.types import InputFile

        # Sending a file from disk
        bot.send_document(
            chat_id,
            InputFile('/path/to/file/file.txt')
        )


        # Sending a file from an io.IOBase object
        with open('/path/to/file/file.txt', 'rb') as f:
            bot.send_document(
                chat_id,
                InputFile(f)
            )

        # Sending a file using pathlib.Path:
        bot.send_document(
            chat_id,
            InputFile(pathlib.Path('/path/to/file/file.txt'))
        )
    """
    def __init__(self, file: Union[str, IOBase, Path], file_name: Optional[str] = None):
        self._file, self._file_name = self._resolve_file(file)
        if file_name:
            self._file_name = file_name
        

    @staticmethod
    def _resolve_file(file):
        if isinstance(file, str):
            _file = open(file, 'rb')
            return _file, os.path.basename(_file.name)
        elif isinstance(file, IOBase):
            return file, service_utils.generate_random_token()
        elif isinstance(file, Path):
            _file = open(file, 'rb')
            return _file, os.path.basename(_file.name)
        else:
            raise TypeError("File must be a string or a file-like object(pathlib.Path, io.IOBase).")

    @property
    def file(self) -> Union[IOBase, str]:
        """
        File object.
        """
        return self._file
    
    @property
    def file_name(self) -> str:
        """
        File name.
        """
        return self._file_name


class ForumTopicCreated(JsonDeserializable):
    """
    This object represents a service message about a new forum topic created in the chat.
    
    Telegram documentation: https://core.telegram.org/bots/api#forumtopiccreated

    :param name: Name of the topic
    :type name: :obj:`str`

    :param icon_color: Color of the topic icon in RGB format
    :type icon_color: :obj:`int`

    :param icon_custom_emoji_id: Optional. Unique identifier of the custom emoji shown as the topic icon
    :type icon_custom_emoji_id: :obj:`str`

    :return: Instance of the class
    :rtype: :class:`telebot.types.ForumTopicCreated`
    """
    @classmethod
    def de_json(cls, json_string):
        if json_string is None: return None
        obj = cls.check_json(json_string)
        return cls(**obj)

    def __init__(self, name: str, icon_color: int, icon_custom_emoji_id: Optional[str]=None, **kwargs) -> None:
        self.name: str = name
        self.icon_color: int = icon_color
        self.icon_custom_emoji_id: Optional[str] = icon_custom_emoji_id


class ForumTopicClosed(JsonDeserializable):
    """
    This object represents a service message about a forum topic closed in the chat. Currently holds no information.
    
    Telegram documentation: https://core.telegram.org/bots/api#forumtopicclosed
    """
    # for future use
    @classmethod
    def de_json(cls, json_string):
        return cls()

    def __init__(self) -> None:
        pass


class ForumTopicReopened(JsonDeserializable):
    """
    This object represents a service message about a forum topic reopened in the chat. Currently holds no information.

    Telegram documentation: https://core.telegram.org/bots/api#forumtopicreopened
    """
    # for future use
    @classmethod
    def de_json(cls, json_string):
        return cls()

    def __init__(self) -> None:
        pass

class ForumTopicEdited(JsonDeserializable):
    """
    This object represents a service message about an edited forum topic.

    Telegram documentation: https://core.telegram.org/bots/api#forumtopicedited

    :param name: Optional, Name of the topic(if updated)
    :type name: :obj:`str`

    :param icon_custom_emoji_id: Optional. New identifier of the custom emoji shown as the topic icon, if it was edited;
        an empty string if the icon was removed
    :type icon_custom_emoji_id: :obj:`str`
    """
    @classmethod
    def de_json(cls, json_string):
        if json_string is None: return None
        obj = cls.check_json(json_string)
        return cls(**obj)

    def __init__(self, name: Optional[str]=None, icon_custom_emoji_id: Optional[str]=None, **kwargs) -> None:
        self.name: Optional[str] = name
        self.icon_custom_emoji_id: Optional[str] = icon_custom_emoji_id


class GeneralForumTopicHidden(JsonDeserializable):
    """
    This object represents a service message about General forum topic hidden in the chat.
    Currently holds no information.

    Telegram documentation: https://core.telegram.org/bots/api#generalforumtopichidden
    """
    @classmethod
    def de_json(cls, json_string):
        return cls()

    def __init__(self) -> None:
        pass


class GeneralForumTopicUnhidden(JsonDeserializable):
    """
    This object represents a service message about General forum topic unhidden in the chat.
    Currently holds no information.

    Telegram documentation: https://core.telegram.org/bots/api#generalforumtopicunhidden
    """
    
    @classmethod
    def de_json(cls, json_string):
        return cls()

    def __init__(self) -> None:
        pass



class ForumTopic(JsonDeserializable):
    """
    This object represents a forum topic.

    Telegram documentation: https://core.telegram.org/bots/api#forumtopic

    :param message_thread_id: Unique identifier of the forum topic
    :type message_thread_id: :obj:`int`

    :param name: Name of the topic
    :type name: :obj:`str`

    :param icon_color: Color of the topic icon in RGB format
    :type icon_color: :obj:`int`

    :param icon_custom_emoji_id: Optional. Unique identifier of the custom emoji shown as the topic icon
    :type icon_custom_emoji_id: :obj:`str`

    :return: Instance of the class
    :rtype: :class:`telebot.types.ForumTopic`
    """

    @classmethod
    def de_json(cls, json_string):
        if json_string is None: return None
        obj = cls.check_json(json_string)
        return cls(**obj)

    def __init__(self, message_thread_id: int, name: str, icon_color: int, icon_custom_emoji_id: Optional[str]=None,
                 **kwargs) -> None:
        self.message_thread_id: int = message_thread_id
        self.name: str = name
        self.icon_color: int = icon_color
        self.icon_custom_emoji_id: Optional[str] = icon_custom_emoji_id


class WriteAccessAllowed(JsonDeserializable):
    """
    This object represents a service message about a user allowing a bot to write
    messages after adding it to the attachment menu, launching a Web App from a link,
    or accepting an explicit request from a Web App sent by the method requestWriteAccess.

    Telegram documentation: https://core.telegram.org/bots/api#writeaccessallowed

    :param from_request: Optional. True, if the access was granted after the user accepted an
        explicit request from a Web App sent by the method requestWriteAccess
    :type from_request: :obj:`bool`

    :param web_app_name: Optional. Name of the Web App which was launched from a link
    :type web_app_name: :obj:`str`

    :param from_attachment_menu: Optional. True, if the access was granted when the bot was added to the attachment or side menu
    :type from_attachment_menu: :obj:`bool`
    """
    @classmethod
    def de_json(cls, json_string):
        if json_string is None: return None
        obj = cls.check_json(json_string)
        return cls(**obj)
        

    def __init__(self, from_request: Optional[bool]=None, web_app_name: Optional[str]=None, from_attachment_menu: Optional[bool]=None,
                 **kwargs) -> None:
        self.web_app_name: Optional[str] = web_app_name
        self.from_request: Optional[bool] = from_request
        self.from_attachment_menu: Optional[bool] = from_attachment_menu


class ChatShared(JsonDeserializable):
    """
    This object contains information about the chat whose identifier was shared with the bot using a
    `telebot.types.KeyboardButtonRequestChat` button.

    Telegram documentation: https://core.telegram.org/bots/api#Chatshared

    :param request_id: identifier of the request
    :type request_id: :obj:`int`

    :param chat_id: Identifier of the shared chat. This number may have more than 32 significant bits and some programming
        languages may have difficulty/silent defects in interpreting it. But it has at most 52 significant bits, so a 64-bit
        integer or double-precision float type are safe for storing this identifier. The bot may not have access to the chat
        and could be unable to use this identifier, unless the chat is already known to the bot by some other means.
    :type chat_id: :obj:`int`

    :param title: Optional. Title of the shared chat
    :type title: :obj:`str`

    :param photo: Optional. Array of Photosize
    :type photo: :obj:`list` of :class:`telebot.types.PhotoSize`

    :param username: Optional. Username of the shared chat
    :type username: :obj:`str`

    :return: Instance of the class
    :rtype: :class:`telebot.types.ChatShared`
    """

    @classmethod
    def de_json(cls, json_string):
        if json_string is None: return None
        obj = cls.check_json(json_string)
        return cls(**obj)

    def __init__(self, request_id: int, chat_id: int, title: Optional[str]=None, photo: Optional[List[PhotoSize]]=None,
                    username: Optional[str]=None, **kwargs) -> None:
        self.request_id: int = request_id
        self.chat_id: int = chat_id
        self.title: Optional[str] = title
        self.photo: Optional[List[PhotoSize]] = photo
        self.username: Optional[str] = username


class BotDescription(JsonDeserializable):
    """
    This object represents a bot description.

    Telegram documentation: https://core.telegram.org/bots/api#botdescription

    :param description: Bot description
    :type description: :obj:`str`

    :return: Instance of the class
    :rtype: :class:`telebot.types.BotDescription`
    """

    @classmethod
    def de_json(cls, json_string):
        if json_string is None: return None
        obj = cls.check_json(json_string)
        return cls(**obj)

    def __init__(self, description: str, **kwargs) -> None:
        self.description: str = description


class BotShortDescription(JsonDeserializable):
    """
    This object represents a bot short description.

    Telegram documentation: https://core.telegram.org/bots/api#botshortdescription

    :param short_description: Bot short description
    :type short_description: :obj:`str`

    :return: Instance of the class
    :rtype: :class:`telebot.types.BotShortDescription`
    """

    @classmethod
    def de_json(cls, json_string):
        if json_string is None: return None
        obj = cls.check_json(json_string)
        return cls(**obj)

    def __init__(self, short_description: str, **kwargs) -> None:
        self.short_description: str = short_description


# noinspection PyShadowingBuiltins
class InputSticker(Dictionaryable, JsonSerializable):
    """
    This object describes a sticker to be added to a sticker set.

    :param sticker: The added sticker. Pass a file_id as a String to send a file that already exists on the Telegram servers,
        pass an HTTP URL as a String for Telegram to get a file from the Internet, or upload a new one using multipart/form-data.
        Animated and video stickers can't be uploaded via HTTP URL. 
    :type sticker: :obj:`str` or :obj:`telebot.types.InputFile`

    :param emoji_list: One or more(up to 20) emoji(s) corresponding to the sticker
    :type emoji_list: :obj:`list` of :obj:`str`

    :param mask_position: Optional. Position where the mask should be placed on faces. For “mask” stickers only.
    :type mask_position: :class:`telebot.types.MaskPosition`
    
    :param keywords: Optional. List of 0-20 search keywords for the sticker with total length of up to 64 characters.
        For “regular” and “custom_emoji” stickers only.
    :type keywords: :obj:`list` of :obj:`str`

    :param format: 	Format of the added sticker, must be one of “static” for a .WEBP or .PNG image, “animated” for a .TGS animation, “video” for a WEBM video
    :type format: :obj:`str`

    :return: Instance of the class
    :rtype: :class:`telebot.types.InputSticker`
    """

    def __init__(self, sticker: Union[str, InputFile], emoji_list: List[str],  format: Optional[str]=None,
                 mask_position: Optional[MaskPosition]=None, keywords: Optional[List[str]]=None) -> None:
        self.sticker: Union[str, InputFile] = sticker
        self.emoji_list: List[str] = emoji_list
        self.mask_position: Optional[MaskPosition] = mask_position
        self.keywords: Optional[List[str]] = keywords
        self.format: str = format

        if not self.format:
            log_deprecation_warning("Deprecation warning. 'format' parameter is required in InputSticker. Setting format to 'static'.")
            self.format = "static"

        if service_utils.is_string(self.sticker):
            self._sticker_name = ''
            self._sticker_dic = self.sticker
        else:
            # work like in inputmedia: convert_input_media
            self._sticker_name = service_utils.generate_random_token()
            # uses attach://_sticker_name for sticker param. then,
            # actual file is sent using files param of the request
            self._sticker_dic = 'attach://{0}'.format(self._sticker_name)

    def to_dict(self) -> dict:
        json_dict = {
            'sticker': self._sticker_dic,
            'emoji_list': self.emoji_list,
            'format': self.format
        }

        if self.mask_position is not None:
            json_dict['mask_position'] = self.mask_position.to_dict()
        if self.keywords is not None:
            json_dict['keywords'] = self.keywords

        return json_dict
    
    def to_json(self) -> str:
        return json.dumps(self.to_dict())
    
    def convert_input_sticker(self) -> Tuple[str, Optional[dict]]:
        if service_utils.is_string(self.sticker):
            return self.to_json(), None

        return self.to_json(), {self._sticker_name: self.sticker}
        
        
        
class SwitchInlineQueryChosenChat(JsonDeserializable, Dictionaryable, JsonSerializable):
    """
    Represents an inline button that switches the current user to inline mode in a chosen chat,
    with an optional default inline query.

    Telegram Documentation: https://core.telegram.org/bots/api#inlinekeyboardbutton

    :param query: Optional. The default inline query to be inserted in the input field.
                  If left empty, only the bot's username will be inserted
    :type query: :obj:`str`

    :param allow_user_chats: Optional. True, if private chats with users can be chosen
    :type allow_user_chats: :obj:`bool`

    :param allow_bot_chats: Optional. True, if private chats with bots can be chosen
    :type allow_bot_chats: :obj:`bool`

    :param allow_group_chats: Optional. True, if group and supergroup chats can be chosen
    :type allow_group_chats: :obj:`bool`

    :param allow_channel_chats: Optional. True, if channel chats can be chosen
    :type allow_channel_chats: :obj:`bool`

    :return: Instance of the class
    :rtype: :class:`SwitchInlineQueryChosenChat`
    """

    @classmethod
    def de_json(cls, json_string):
        if json_string is None: return None
        obj = cls.check_json(json_string)
        return cls(**obj)

    def __init__(self, query: Optional[str]=None, allow_user_chats: Optional[bool]=None, allow_bot_chats: Optional[bool]=None,
                    allow_group_chats: Optional[bool]=None, allow_channel_chats: Optional[bool]=None) -> None:
        self.query: Optional[str] = query
        self.allow_user_chats: Optional[bool] = allow_user_chats
        self.allow_bot_chats: Optional[bool] = allow_bot_chats
        self.allow_group_chats: Optional[bool] = allow_group_chats
        self.allow_channel_chats: Optional[bool] = allow_channel_chats


    def to_dict(self):
        json_dict = {}

        if self.query is not None:
            json_dict['query'] = self.query
        if self.allow_user_chats is not None:
            json_dict['allow_user_chats'] = self.allow_user_chats
        if self.allow_bot_chats is not None:
            json_dict['allow_bot_chats'] = self.allow_bot_chats
        if self.allow_group_chats is not None:
            json_dict['allow_group_chats'] = self.allow_group_chats
        if self.allow_channel_chats is not None:
            json_dict['allow_channel_chats'] = self.allow_channel_chats

        return json_dict

    def to_json(self):
        return json.dumps(self.to_dict())


class BotName(JsonDeserializable):
    """
    This object represents a bot name.

    Telegram Documentation: https://core.telegram.org/bots/api#botname

    :param name: The bot name
    :type name: :obj:`str`

    :return: Instance of the class
    :rtype: :class:`BotName`
    """

    @classmethod
    def de_json(cls, json_string):
        if json_string is None: return None
        obj = cls.check_json(json_string)
        return cls(**obj)

    def __init__(self, name: str, **kwargs):
        self.name: str = name


class InlineQueryResultsButton(JsonSerializable, Dictionaryable):
    """
    This object represents a button to be shown above inline query results.
    You must use exactly one of the optional fields.

    Telegram documentation: https://core.telegram.org/bots/api#inlinequeryresultsbutton

    :param text: Label text on the button
    :type text: :obj:`str`

    :param web_app: Optional. Description of the Web App that will be launched when the user presses the button.
        The Web App will be able to switch back to the inline mode using the method web_app_switch_inline_query inside the Web App.
    :type web_app: :class:`telebot.types.WebAppInfo`
    
    :param start_parameter: Optional. Deep-linking parameter for the /start message sent to the bot when a user presses the button.
        1-64 characters, only A-Z, a-z, 0-9, _ and - are allowed.
        Example: An inline bot that sends YouTube videos can ask the user to connect the bot to their YouTube account to adapt search
        results accordingly. To do this, it displays a 'Connect your YouTube account' button above the results, or even before showing
        any. The user presses the button, switches to a private chat with the bot and, in doing so, passes a start parameter that instructs
        the bot to return an OAuth link. Once done, the bot can offer a switch_inline button so that the user can easily return to the chat
        where they wanted to use the bot's inline capabilities.
    :type start_parameter: :obj:`str`

    :return: Instance of the class
    :rtype: :class:`InlineQueryResultsButton`
    """

    def __init__(self, text: str, web_app: Optional[WebAppInfo]=None, start_parameter: Optional[str]=None) -> None:
        self.text: str = text
        self.web_app: Optional[WebAppInfo] = web_app
        self.start_parameter: Optional[str] = start_parameter

    def to_dict(self) -> dict:
        json_dict = {
            'text': self.text
        }

        if self.web_app is not None:
            json_dict['web_app'] = self.web_app.to_dict()
        if self.start_parameter is not None:
            json_dict['start_parameter'] = self.start_parameter

        return json_dict
    
    def to_json(self) -> str:
        return json.dumps(self.to_dict())


# noinspection PyShadowingBuiltins
class Story(JsonDeserializable):
    """
    This object represents a story.

    Telegram documentation: https://core.telegram.org/bots/api#story

    :param chat: Chat that posted the story
    :type chat: :class:`telebot.types.Chat`

    :param id: Unique identifier for the story in the chat
    :type id: :obj:`int`

    :return: Instance of the class
    :rtype: :class:`Story`
    """

    @classmethod
    def de_json(cls, json_string):
        if json_string is None: return None
        obj = cls.check_json(json_string)
        obj['chat'] = Chat.de_json(obj['chat'])
        return cls(**obj)
    
    def __init__(self, chat: Chat, id: int, **kwargs) -> None:
        self.chat: Chat = chat
        self.id: int = id


# base class
# noinspection PyShadowingBuiltins
class ReactionType(JsonDeserializable, Dictionaryable, JsonSerializable):
    """
    This object represents a reaction type.

    Telegram documentation: https://core.telegram.org/bots/api#reactiontype

    :param type: Type of the reaction
    :type type: :obj:`str`

    :return: Instance of the class
    :rtype: :class:`ReactionType`
    """

    @classmethod
    def de_json(cls, json_string):
        if json_string is None: return None
        obj = cls.check_json(json_string)
        # remove type 
        if obj['type'] == 'emoji':
            del obj['type']
            return ReactionTypeEmoji(**obj)
        elif obj['type'] == 'custom_emoji':
            del obj['type']
            return ReactionTypeCustomEmoji(**obj)

    def __init__(self, type: str) -> None:
        self.type: str = type

    def to_dict(self) -> dict:
        json_dict = {
            'type': self.type
        }
        return json_dict
    
    def to_json(self) -> str:
        return json.dumps(self.to_dict())


# noinspection PyUnresolvedReferences
class ReactionTypeEmoji(ReactionType):
    """
    This object represents an emoji reaction type.

    Telegram documentation: https://core.telegram.org/bots/api#reactiontypeemoji

    :param type: Type of the reaction, must be emoji
    :type type: :obj:`str`

    :param emoji: Reaction emoji. List is available on the API doc.
    :type emoji: :obj:`str`

    :return: Instance of the class
    :rtype: :class:`ReactionTypeEmoji`
    """

    def __init__(self, emoji: str, **kwargs) -> None:
        super().__init__('emoji')
        self.emoji: str = emoji

    def to_dict(self) -> dict:
        json_dict = super().to_dict()
        json_dict['emoji'] = self.emoji
        return json_dict


# noinspection PyUnresolvedReferences,PyUnusedLocal
class ReactionTypeCustomEmoji(ReactionType):
    """
    This object represents a custom emoji reaction type.

    Telegram documentation: https://core.telegram.org/bots/api#reactiontypecustomemoji

    :param type: Type of the reaction, must be custom_emoji
    :type type: :obj:`str`

    :param custom_emoji_id: Identifier of the custom emoji
    :type custom_emoji_id: :obj:`str`

    :return: Instance of the class
    :rtype: :class:`ReactionTypeCustomEmoji`
    """

    def __init__(self, custom_emoji_id: str, **kwargs) -> None:
        super().__init__('custom_emoji')
        self.custom_emoji_id: str = custom_emoji_id

    def to_dict(self) -> dict:
        json_dict = super().to_dict()
        json_dict['custom_emoji_id'] = self.custom_emoji_id
        return json_dict


class ReactionTypePaid(ReactionType):
    """
    This object represents a paid reaction type.

    Telegram documentation: https://core.telegram.org/bots/api#reactiontypepaid

    :param type: Type of the reaction, must be paid
    :type type: :obj:`str`

    :return: Instance of the class
    :rtype: :class:`ReactionTypePaid`
    """

    def __init__(self, **kwargs) -> None:
        super().__init__('paid')

    def to_dict(self) -> dict:
        return super().to_dict()
    


class MessageReactionUpdated(JsonDeserializable):
    """
    This object represents a service message about a change in the list of the current user's reactions to a message.

    Telegram documentation: https://core.telegram.org/bots/api#messagereactionupdated

    :param chat: The chat containing the message the user reacted to
    :type chat: :class:`telebot.types.Chat`

    :param message_id: Unique identifier of the message inside the chat
    :type message_id: :obj:`int`

    :param user: Optional. The user that changed the reaction, if the user isn't anonymous
    :type user: :class:`telebot.types.User`

    :param actor_chat: Optional. The chat on behalf of which the reaction was changed, if the user is anonymous
    :type actor_chat: :class:`telebot.types.Chat`

    :param date: Date of the change in Unix time
    :type date: :obj:`int`

    :param old_reaction: Previous list of reaction types that were set by the user
    :type old_reaction: :obj:`list` of :class:`ReactionType`

    :param new_reaction: New list of reaction types that have been set by the user
    :type new_reaction: :obj:`list` of :class:`ReactionType`

    :return: Instance of the class
    :rtype: :class:`MessageReactionUpdated`
    """

    @classmethod
    def de_json(cls, json_string):
        if json_string is None: return None
        obj = cls.check_json(json_string)

        obj['chat'] = Chat.de_json(obj['chat'])
        if 'user' in obj:
            obj['user'] = User.de_json(obj['user'])
        if 'actor_chat' in obj:
            obj['actor_chat'] = Chat.de_json(obj['actor_chat'])
        obj['old_reaction'] = [ReactionType.de_json(reaction) for reaction in obj['old_reaction']]
        obj['new_reaction'] = [ReactionType.de_json(reaction) for reaction in obj['new_reaction']]
        return cls(**obj)

    def __init__(self, chat: Chat, message_id: int, date: int, old_reaction: List[ReactionType], new_reaction: List[ReactionType],
                 user: Optional[User]=None, actor_chat: Optional[Chat]=None, **kwargs) -> None:
        self.chat: Chat = chat
        self.message_id: int = message_id
        self.user: Optional[User] = user
        self.actor_chat: Optional[Chat] = actor_chat
        self.date: int = date
        self.old_reaction: List[ReactionType] = old_reaction
        self.new_reaction: List[ReactionType] = new_reaction



class MessageReactionCountUpdated(JsonDeserializable):
    """
    This object represents a service message about a change in the list of the current user's reactions to a message.

    Telegram documentation: https://core.telegram.org/bots/api#messagereactioncountupdated

    :param chat: The chat containing the message
    :type chat: :class:`telebot.types.Chat`

    :param message_id: Unique message identifier inside the chat
    :type message_id: :obj:`int`

    :param date: Date of the change in Unix time
    :type date: :obj:`int`

    :param reactions: List of reactions that are present on the message
    :type reactions: :obj:`list` of :class:`ReactionCount`

    :return: Instance of the class
    :rtype: :class:`MessageReactionCountUpdated`
    """

    @classmethod
    def de_json(cls, json_string):
        if json_string is None: return None
        obj = cls.check_json(json_string)
        obj['chat'] = Chat.de_json(obj['chat'])
        obj['reactions'] = [ReactionCount.de_json(reaction) for reaction in obj['reactions']]
        return cls(**obj)

    def __init__(self, chat: Chat, message_id: int, date: int, reactions: List[ReactionCount], **kwargs) -> None:
        self.chat: Chat = chat
        self.message_id: int = message_id
        self.date: int = date
        self.reactions: List[ReactionCount] = reactions


# noinspection PyShadowingBuiltins
class ReactionCount(JsonDeserializable):
    """
    This object represents a reaction added to a message along with the number of times it was added.

    Telegram documentation: https://core.telegram.org/bots/api#reactioncount

    :param type: Type of the reaction
    :type type: :class:`ReactionType`

    :param total_count: Number of times the reaction was added
    :type total_count: :obj:`int`

    :return: Instance of the class
    :rtype: :class:`ReactionCount`
    """

    @classmethod
    def de_json(cls, json_string):
        if json_string is None: return None
        obj = cls.check_json(json_string)
        obj['type'] = ReactionType.de_json(obj['type'])
        return cls(**obj)
    
    def __init__(self, type: ReactionType, total_count: int, **kwargs) -> None:
        self.type: ReactionType = type
        self.total_count: int = total_count


class ExternalReplyInfo(JsonDeserializable):
    """
    This object contains information about a message that is being replied to,
    which may come from another chat or forum topic.

    Telegram documentation: https://core.telegram.org/bots/api#externalreplyinfo

    :param origin: Origin of the message replied to by the given message
    :type origin: :class:`MessageOrigin`

    :param chat: Optional. Chat the original message belongs to. Available only if the chat is a supergroup or a channel.
    :type chat: :class:`Chat`

    :param message_id: Optional. Unique message identifier inside the original chat. Available only if the original chat is a supergroup or a channel.
    :type message_id: :obj:`int`

    :param link_preview_options: Optional. Options used for link preview generation for the original message, if it is a text message
    :type link_preview_options: :class:`LinkPreviewOptions`

    :param animation: Optional. Message is an animation, information about the animation
    :type animation: :class:`Animation`

    :param audio: Optional. Message is an audio file, information about the file
    :type audio: :class:`Audio`

    :param document: Optional. Message is a general file, information about the file
    :type document: :class:`Document`

    :param paid_media: Optional. Message is a paid media content
    :type paid_media: :class:`PaidMedia`

    :param photo: Optional. Message is a photo, available sizes of the photo
    :type photo: :obj:`list` of :class:`PhotoSize`

    :param sticker: Optional. Message is a sticker, information about the sticker
    :type sticker: :class:`Sticker`

    :param story: Optional. Message is a forwarded story
    :type story: :class:`Story`

    :param video: Optional. Message is a video, information about the video
    :type video: :class:`Video`

    :param video_note: Optional. Message is a video note, information about the video message
    :type video_note: :class:`VideoNote`

    :param voice: Optional. Message is a voice message, information about the file
    :type voice: :class:`Voice`

    :param has_media_spoiler: Optional. True, if the message media is covered by a spoiler animation
    :type has_media_spoiler: :obj:`bool`

    :param checklist: Optional. Message is a checklist
    :type checklist: :class:`telebot.types.Checklist`

    :param contact: Optional. Message is a shared contact, information about the contact
    :type contact: :class:`Contact`

    :param dice: Optional. Message is a dice with random value
    :type dice: :class:`Dice`

    :param game: Optional. Message is a game, information about the game. More about games »
    :type game: :class:`Game`

    :param giveaway: Optional. Message is a scheduled giveaway, information about the giveaway
    :type giveaway: :class:`Giveaway`

    :param giveaway_winners: Optional. A giveaway with public winners was completed
    :type giveaway_winners: :class:`GiveawayWinners`

    :param invoice: Optional. Message is an invoice for a payment, information about the invoice. More about payments »
    :type invoice: :class:`Invoice`

    :param location: Optional. Message is a shared location, information about the location
    :type location: :class:`Location`

    :param poll: Optional. Message is a native poll, information about the poll
    :type poll: :class:`Poll`

    :param venue: Optional. Message is a venue, information about the venue
    :type venue: :class:`Venue`

    :return: Instance of the class
    :rtype: :class:`ExternalReplyInfo`
    """
    @classmethod
    def de_json(cls, json_string):
        if json_string is None: return None
        obj = cls.check_json(json_string)
        obj['origin'] = MessageOrigin.de_json(obj['origin'])
        if 'chat' in obj:
            obj['chat'] = Chat.de_json(obj['chat'])
        if 'link_preview_options' in obj:
            obj['link_preview_options'] = LinkPreviewOptions.de_json(obj['link_preview_options'])
        if 'animation' in obj:
            obj['animation'] = Animation.de_json(obj['animation'])
        if 'audio' in obj:
            obj['audio'] = Audio.de_json(obj['audio'])
        if 'document' in obj:
            obj['document'] = Document.de_json(obj['document'])
        if 'photo' in obj:
            obj['photo'] = Message.parse_photo(obj['photo'])
        if 'sticker' in obj:
            obj['sticker'] = Sticker.de_json(obj['sticker'])
        if 'story' in obj:
            obj['story'] = Story.de_json(obj['story'])
        if 'video' in obj:
            obj['video'] = Video.de_json(obj['video'])
        if 'video_note' in obj:
            obj['video_note'] = VideoNote.de_json(obj['video_note'])
        if 'voice' in obj:
            obj['voice'] = Voice.de_json(obj['voice'])
        if 'contact' in obj:
            obj['contact'] = Contact.de_json(obj['contact'])
        if 'dice' in obj:
            obj['dice'] = Dice.de_json(obj['dice'])
        if 'game' in obj:
            obj['game'] = Game.de_json(obj['game'])
        if 'giveaway' in obj:
            obj['giveaway'] = Giveaway.de_json(obj['giveaway'])
        if 'giveaway_winners' in obj:
            obj['giveaway_winners'] = GiveawayWinners.de_json(obj['giveaway_winners'])
        if 'invoice' in obj:
            obj['invoice'] = Invoice.de_json(obj['invoice'])
        if 'location' in obj:
            obj['location'] = Location.de_json(obj['location'])
        if 'poll' in obj:
            obj['poll'] = Poll.de_json(obj['poll'])
        if 'venue' in obj:
            obj['venue'] = Venue.de_json(obj['venue'])
        if 'paid_media' in obj:
            obj['paid_media'] = PaidMediaInfo.de_json(obj['paid_media'])
        if 'checklist' in obj:
            obj['checklist'] = Checklist.de_json(obj['checklist'])
        return cls(**obj)

    def __init__(
            self, origin: MessageOrigin, chat: Optional[Chat]=None, message_id: Optional[int]=None,
            link_preview_options: Optional[LinkPreviewOptions]=None, animation: Optional[Animation]=None,
            audio: Optional[Audio]=None, document: Optional[Document]=None, photo: Optional[List[PhotoSize]]=None,
            sticker: Optional[Sticker]=None, story: Optional[Story]=None, video: Optional[Video]=None,
            video_note: Optional[VideoNote]=None, voice: Optional[Voice]=None,
            has_media_spoiler: Optional[bool]=None, contact: Optional[Contact]=None,
            dice: Optional[Dice]=None, game: Optional[Game]=None, giveaway: Optional[Giveaway]=None,
            giveaway_winners: Optional[GiveawayWinners]=None, invoice: Optional[Invoice]=None,
            location: Optional[Location]=None, poll: Optional[Poll]=None,
            venue: Optional[Venue]=None, paid_media: Optional[PaidMediaInfo]=None,
            checklist: Optional[Checklist]=None, **kwargs) -> None:
        self.origin: MessageOrigin = origin
        self.chat: Optional[Chat] = chat
        self.message_id: Optional[int] = message_id
        self.link_preview_options: Optional[LinkPreviewOptions] = link_preview_options
        self.animation: Optional[Animation] = animation
        self.audio: Optional[Audio] = audio
        self.document: Optional[Document] = document
        self.photo: Optional[List[PhotoSize]] = photo
        self.sticker: Optional[Sticker] = sticker
        self.story: Optional[Story] = story
        self.video: Optional[Video] = video
        self.video_note: Optional[VideoNote] = video_note
        self.voice: Optional[Voice] = voice
        self.has_media_spoiler: Optional[bool] = has_media_spoiler
        self.contact: Optional[Contact] = contact
        self.dice: Optional[Dice] = dice
        self.game: Optional[Game] = game
        self.giveaway: Optional[Giveaway] = giveaway
        self.giveaway_winners: Optional[GiveawayWinners] = giveaway_winners
        self.invoice: Optional[Invoice] = invoice
        self.location: Optional[Location] = location
        self.poll: Optional[Poll] = poll
        self.venue: Optional[Venue] = venue
        self.paid_media: Optional[PaidMediaInfo] = paid_media
        self.checklist: Optional[Checklist] = checklist


# noinspection PyUnresolvedReferences,PyShadowingBuiltins
class MessageOrigin(JsonDeserializable):
    """
    This object describes the origin of a message.

    Telegram documentation: https://core.telegram.org/bots/api#messageorigin

    :param type: Type of the message origin
    :type type: :obj:`str`

    :param date: Date the message was sent originally in Unix time
    :type date: :obj:`int`

    :param sender_user: User that sent the message originally (for MessageOriginUser)
    :type sender_user: :class:`User`

    :param sender_user_name: Name of the user that sent the message originally (for MessageOriginHiddenUser)
    :type sender_user_name: :obj:`str`

    :param sender_chat: Chat that sent the message originally (for MessageOriginChat)
    :type sender_chat: :class:`Chat`

    :param author_signature: Optional. Author signature for certain cases
    :type author_signature: :obj:`str`

    :return: Instance of the class
    :rtype: :class:`MessageOrigin`
    """

    @classmethod
    def de_json(cls, json_string):
        if json_string is None: return None
        obj = cls.check_json(json_string)
        message_type = obj['type']
        if message_type == 'user':
            sender_user = User.de_json(obj['sender_user'])
            return MessageOriginUser(date=obj['date'], sender_user=sender_user)
        elif message_type == 'hidden_user':
            return MessageOriginHiddenUser(date=obj['date'], sender_user_name=obj['sender_user_name'])
        elif message_type == 'chat':
            sender_chat = Chat.de_json(obj['sender_chat'])
            return MessageOriginChat(date=obj['date'], sender_chat=sender_chat, author_signature=obj.get('author_signature'))
        elif message_type == 'channel':
            chat = Chat.de_json(obj['chat'])
            return MessageOriginChannel(date=obj['date'], chat=chat, message_id=obj['message_id'], author_signature=obj.get('author_signature'))

    def __init__(self, type: str, date: int) -> None:
        self.type: str = type
        self.date: int = date


class MessageOriginUser(MessageOrigin):
    """
    The message was originally sent by a known user.

    :param sender_user: User that sent the message originally
    :type sender_user: :class:`User`
    """

    def __init__(self, date: int, sender_user: User) -> None:
        super().__init__('user', date)
        self.sender_user: User = sender_user


class MessageOriginHiddenUser(MessageOrigin):
    """
    The message was originally sent by an unknown user.

    :param sender_user_name: Name of the user that sent the message originally
    :type sender_user_name: :obj:`str`
    """

    def __init__(self, date: int, sender_user_name: str) -> None:
        super().__init__('hidden_user', date)
        self.sender_user_name: str = sender_user_name


class MessageOriginChat(MessageOrigin):
    """
    The message was originally sent on behalf of a chat to a group chat.

    :param sender_chat: Chat that sent the message originally
    :type sender_chat: :class:`Chat`

    :param author_signature: Optional. For messages originally sent by an anonymous chat administrator, original message author signature
    :type author_signature: :obj:`str`
    """

    def __init__(self, date: int, sender_chat: Chat, author_signature: Optional[str] = None) -> None:
        super().__init__('chat', date)
        self.sender_chat: Chat = sender_chat
        self.author_signature: Optional[str] = author_signature


class MessageOriginChannel(MessageOrigin):
    """
    The message was originally sent to a channel chat.

    :param chat: Channel chat to which the message was originally sent
    :type chat: :class:`Chat`

    :param message_id: Unique message identifier inside the chat
    :type message_id: :obj:`int`

    :param author_signature: Optional. Signature of the original post author
    :type author_signature: :obj:`str`
    """

    def __init__(self, date: int, chat: Chat, message_id: int, author_signature: Optional[str] = None) -> None:
        super().__init__('channel', date)
        self.chat: Chat = chat
        self.message_id: int = message_id
        self.author_signature: Optional[str] = author_signature


class LinkPreviewOptions(JsonDeserializable, Dictionaryable, JsonSerializable):
    """
    Describes the options used for link preview generation.

    Telegram documentation: https://core.telegram.org/bots/api#linkpreviewoptions

    :param is_disabled: Optional. True, if the link preview is disabled
    :type is_disabled: :obj:`bool`

    :param url: Optional. URL to use for the link preview. If empty, then the first URL found in the message text will be used
    :type url: :obj:`str`

    :param prefer_small_media: Optional. True, if the media in the link preview is supposed to be shrunk; ignored if the URL isn't explicitly specified or media size change isn't supported for the preview
    :type prefer_small_media: :obj:`bool`

    :param prefer_large_media: Optional. True, if the media in the link preview is supposed to be enlarged; ignored if the URL isn't explicitly specified or media size change isn't supported for the preview
    :type prefer_large_media: :obj:`bool`

    :param show_above_text: Optional. True, if the link preview must be shown above the message text; otherwise, the link preview will be shown below the message text
    :type show_above_text: :obj:`bool`

    :return: Instance of the class
    :rtype: :class:`LinkPreviewOptions`
    """

    @classmethod
    def de_json(cls, json_string):
        if json_string is None: return None
        obj = cls.check_json(json_string)
        return cls(**obj)

    def __init__(self, is_disabled: Optional[bool] = None, url: Optional[str] = None,
                 prefer_small_media: Optional[bool] = None, prefer_large_media: Optional[bool] = None,
                 show_above_text: Optional[bool] = None, **kwargs) -> None:
        self.is_disabled: Optional[bool] = is_disabled
        self.url: Optional[str] = url
        self.prefer_small_media: Optional[bool] = prefer_small_media
        self.prefer_large_media: Optional[bool] = prefer_large_media
        self.show_above_text: Optional[bool] = show_above_text

    def to_dict(self) -> dict:
        json_dict = {}

        if self.is_disabled is not None:
            json_dict['is_disabled'] = self.is_disabled
        if self.url is not None:
            json_dict['url'] = self.url
        if self.prefer_small_media is not None:
            json_dict['prefer_small_media'] = self.prefer_small_media
        if self.prefer_large_media is not None:
            json_dict['prefer_large_media'] = self.prefer_large_media
        if self.show_above_text is not None:
            json_dict['show_above_text'] = self.show_above_text
        return json_dict

    def to_json(self) -> str:
        return json.dumps(self.to_dict())


class Giveaway(JsonDeserializable):
    """
    This object represents a message about a scheduled giveaway.

    Telegram documentation: https://core.telegram.org/bots/api#giveaway

    :param chats: The list of chats which the user must join to participate in the giveaway
    :type chats: :obj:`list` of :class:`Chat`

    :param winners_selection_date: Point in time (Unix timestamp) when winners of the giveaway will be selected
    :type winners_selection_date: :obj:`int`

    :param winner_count: The number of users which are supposed to be selected as winners of the giveaway
    :type winner_count: :obj:`int`

    :param only_new_members: Optional. True, if only users who join the chats after the giveaway started should be eligible to win
    :type only_new_members: :obj:`bool`

    :param has_public_winners: Optional. True, if the list of giveaway winners will be visible to everyone
    :type has_public_winners: :obj:`bool`

    :param prize_description: Optional. Description of additional giveaway prize
    :type prize_description: :obj:`str`

    :param country_codes: Optional. A list of two-letter ISO 3166-1 alpha-2 country codes indicating the countries from which eligible users for the giveaway must come. If empty, then all users can participate in the giveaway.
    :type country_codes: :obj:`list` of :obj:`str`

    :param prize_star_count: Optional. The number of Telegram Stars to be split between giveaway winners; for Telegram Star giveaways only
    :type prize_star_count: :obj:`int`

    :param premium_subscription_month_count: Optional. The number of months the Telegram Premium subscription won from the giveaway will be active for
    :type premium_subscription_month_count: :obj:`int`

    :return: Instance of the class
    :rtype: :class:`Giveaway`
    """

    @classmethod
    def de_json(cls, json_string):
        if json_string is None: return None
        obj = cls.check_json(json_string)
        obj['chats'] = [Chat.de_json(chat) for chat in obj['chats']]
        return cls(**obj)

    def __init__(self, chats: List[Chat], winners_selection_date: int, winner_count: int,
                 only_new_members: Optional[bool] = None, has_public_winners: Optional[bool] = None,
                 prize_description: Optional[str] = None, country_codes: Optional[List[str]] = None,
                 premium_subscription_month_count: Optional[int] = None, prize_star_count: Optional[int] = None, **kwargs) -> None:
        self.chats: List[Chat] = chats
        self.winners_selection_date: int = winners_selection_date
        self.winner_count: int = winner_count
        self.only_new_members: Optional[bool] = only_new_members
        self.has_public_winners: Optional[bool] = has_public_winners
        self.prize_description: Optional[str] = prize_description
        self.country_codes: Optional[List[str]] = country_codes
        self.premium_subscription_month_count: Optional[int] = premium_subscription_month_count
        self.prize_star_count: Optional[int] = prize_star_count
                     

class GiveawayWinners(JsonDeserializable):
    """
    This object represents a message about the completion of a giveaway with public winners.

    Telegram documentation: https://core.telegram.org/bots/api#giveawaywinners

    :param chat: The chat that created the giveaway
    :type chat: :class:`Chat`

    :param giveaway_message_id: Identifier of the messsage with the giveaway in the chat
    :type giveaway_message_id: :obj:`int`

    :param winners_selection_date: Point in time (Unix timestamp) when winners of the giveaway were selected
    :type winners_selection_date: :obj:`int`

    :param winner_count: Total number of winners in the giveaway
    :type winner_count: :obj:`int`

    :param winners: List of up to 100 winners of the giveaway
    :type winners: :obj:`list` of :class:`User`

    :param additional_chat_count: Optional. The number of other chats the user had to join in order to be eligible for the giveaway
    :type additional_chat_count: :obj:`int`

    :param premium_subscription_month_count: Optional. The number of months the Telegram Premium subscription won from the giveaway will be active for
    :type premium_subscription_month_count: :obj:`int`

    :param unclaimed_prize_count: Optional. Number of undistributed prizes
    :type unclaimed_prize_count: :obj:`int`

    :param only_new_members: Optional. True, if only users who had joined the chats after the giveaway started were eligible to win
    :type only_new_members: :obj:`bool`

    :param was_refunded: Optional. True, if the giveaway was canceled because the payment for it was refunded
    :type was_refunded: :obj:`bool`

    :param prize_description: Optional. Description of additional giveaway prize
    :type prize_description: :obj:`str`

    :param prize_star_count: Optional. The number of Telegram Stars to be split between giveaway winners; for Telegram Star giveaways only
    :type prize_star_count: :obj:`int`

    :return: Instance of the class
    :rtype: :class:`GiveawayWinners`
    """

    @classmethod
    def de_json(cls, json_string):
        if json_string is None: return None
        obj = cls.check_json(json_string)
        obj['chat'] = Chat.de_json(obj['chat'])
        obj['winners'] = [User.de_json(user) for user in obj['winners']]
        return cls(**obj)
    
    def __init__(self, chat: Chat, giveaway_message_id: int, winners_selection_date: int, winner_count: int,
                 winners: List[User], additional_chat_count: Optional[int] = None,
                 premium_subscription_month_count: Optional[int] = None, unclaimed_prize_count: Optional[int] = None,
                 only_new_members: Optional[bool] = None, was_refunded: Optional[bool] = None,
                 prize_description: Optional[str] = None, prize_star_count: Optional[int] = None, **kwargs) -> None:
        self.chat: Chat = chat
        self.giveaway_message_id: int = giveaway_message_id
        self.winners_selection_date: int = winners_selection_date
        self.winner_count: int = winner_count
        self.winners: List[User] = winners
        self.additional_chat_count: Optional[int] = additional_chat_count
        self.premium_subscription_month_count: Optional[int] = premium_subscription_month_count
        self.unclaimed_prize_count: Optional[int] = unclaimed_prize_count
        self.only_new_members: Optional[bool] = only_new_members
        self.was_refunded: Optional[bool] = was_refunded
        self.prize_description: Optional[str] = prize_description
        self.prize_star_count: Optional[int] = prize_star_count
                     
        
class GiveawayCompleted(JsonDeserializable):
    """
    This object represents a service message about the completion of a giveaway without public winners.

    Telegram documentation: https://core.telegram.org/bots/api#giveawaycompleted

    :param winner_count: Number of winners in the giveaway
    :type winner_count: :obj:`int`

    :param unclaimed_prize_count: Optional. Number of undistributed prizes
    :type unclaimed_prize_count: :obj:`int`

    :param giveaway_message: Optional. Message with the giveaway that was completed, if it wasn't deleted
    :type giveaway_message: :class:`Message`

    :param is_star_giveaway: Optional. True, if the giveaway was a Telegram Star giveaway
    :type is_star_giveaway: :obj:`bool`

    :return: Instance of the class
    :rtype: :class:`GiveawayCompleted`
    """

    @classmethod
    def de_json(cls, json_string):
        if json_string is None: return None
        obj = cls.check_json(json_string)
        if 'giveaway_message' in obj:
            obj['giveaway_message'] = Message.de_json(obj['giveaway_message'])
        return cls(**obj)
    
    def __init__(self, winner_count: int, unclaimed_prize_count: Optional[int] = None,
                    giveaway_message: Optional[Message] = None, is_star_giveaway: Optional[bool] = None, **kwargs) -> None:
        self.winner_count: int = winner_count
        self.unclaimed_prize_count: Optional[int] = unclaimed_prize_count
        self.giveaway_message: Optional[Message] = giveaway_message
        self.is_star_giveaway: Optional[bool] = is_star_giveaway
                        

class GiveawayCreated(JsonDeserializable):
    """
    This object represents a service message about the creation of a scheduled giveaway.

    :prize_star_count: Optional. The number of Telegram Stars to be split between giveaway winners; for Telegram Star giveaways only
    :type prize_star_count: :obj:`int`

    :return: Instance of the class
    """

    @classmethod
    def de_json(cls, json_string):
        if json_string is None: return None
        obj = cls.check_json(json_string)
        return cls(**obj)

    def __init__(self, prize_star_count=None, **kwargs) -> None:
        self.prize_star_count: Optional[str] = prize_star_count


class TextQuote(JsonDeserializable):
    """
    This object contains information about the quoted part of a message that is replied to by the given message.

    Telegram documentation: https://core.telegram.org/bots/api#textquote

    :param text: Text of the quoted part of a message that is replied to by the given message
    :type text: :obj:`str`

    :param entities: Optional. Special entities that appear in the quote. Currently, only bold, italic, underline, strikethrough, spoiler, and custom_emoji entities are kept in quotes.
    :type entities: :obj:`list` of :class:`MessageEntity`

    :param position: Approximate quote position in the original message in UTF-16 code units as specified by the sender
    :type position: :obj:`int`

    :param is_manual: Optional. True, if the quote was chosen manually by the message sender. Otherwise, the quote was added automatically by the server.
    :type is_manual: :obj:`bool`

    :return: Instance of the class
    :rtype: :class:`TextQuote`
    """

    @classmethod
    def de_json(cls, json_string):
        if json_string is None: return None
        obj = cls.check_json(json_string)
        if 'entities' in obj:
            obj['entities'] = [MessageEntity.de_json(entity) for entity in obj['entities']]
        return cls(**obj)

    def __init__(self, text: str, position: int,
                 entities: Optional[List[MessageEntity]] = None,
                 is_manual: Optional[bool] = None, **kwargs) -> None:
        self.text: str = text
        self.entities: Optional[List[MessageEntity]] = entities
        self.position: Optional[int] = position
        self.is_manual: Optional[bool] = is_manual

    @property
    def html_text(self):
        """
        Returns html-rendered text.
        """
        if self.text is None:
            return None
        return apply_html_entities(self.text, self.entities, getattr(self, "custom_subs", None))


class ReplyParameters(JsonDeserializable, Dictionaryable, JsonSerializable):
    """
    Describes reply parameters for the message that is being sent.

    Telegram documentation: https://core.telegram.org/bots/api#replyparameters

    :param message_id: Identifier of the message that will be replied to in the current chat, or in the chat chat_id if it is specified
    :type message_id: :obj:`int`

    :param chat_id: Optional. If the message to be replied to is from a different chat, unique identifier for the chat or username of the channel (in the format @channelusername)
    :type chat_id: :obj:`int` or :obj:`str`

    :param allow_sending_without_reply: Optional. Pass True if the message should be sent even if the specified message to be replied to is not found; can be used only for replies in the same chat and forum topic.
    :type allow_sending_without_reply: :obj:`bool`

    :param quote: Optional. Quoted part of the message to be replied to; 0-1024 characters after entities parsing. The quote must be an exact substring of the message to be replied to, including bold, italic, underline, strikethrough, spoiler, and custom_emoji entities. The message will fail to send if the quote isn't found in the original message.
    :type quote: :obj:`str`

    :param quote_parse_mode: Optional. Mode for parsing entities in the quote. See formatting options for more details.
    :type quote_parse_mode: :obj:`str`

    :param quote_entities: Optional. A JSON-serialized list of special entities that appear in the quote. It can be specified instead of quote_parse_mode.
    :type quote_entities: :obj:`list` of :class:`MessageEntity`

    :param quote_position: Optional. Position of the quote in the original message in UTF-16 code units
    :type quote_position: :obj:`int`

    :return: Instance of the class
    :rtype: :class:`ReplyParameters`
    """

    @classmethod
    def de_json(cls, json_string):
        if json_string is None: return None
        obj = cls.check_json(json_string)
        if 'quote_entities' in obj:
            obj['quote_entities'] = [MessageEntity.de_json(entity) for entity in obj['quote_entities']]
        return cls(**obj)    

    def __init__(self, message_id: int, chat_id: Optional[Union[int, str]] = None,
                 allow_sending_without_reply: Optional[bool] = None, quote: Optional[str] = None,
                 quote_parse_mode: Optional[str] = None, quote_entities: Optional[List[MessageEntity]] = None,
                 quote_position: Optional[int] = None, **kwargs) -> None:
        self.message_id: int = message_id
        self.chat_id: Optional[Union[int, str]] = chat_id
        self.allow_sending_without_reply: Optional[bool] = allow_sending_without_reply
        self.quote: Optional[str] = quote
        self.quote_parse_mode: Optional[str] = quote_parse_mode
        self.quote_entities: Optional[List[MessageEntity]] = quote_entities
        self.quote_position: Optional[int] = quote_position

    def to_dict(self) -> dict:
        json_dict = {
            'message_id': self.message_id
        }
        if self.chat_id is not None:
            json_dict['chat_id'] = self.chat_id
        if self.allow_sending_without_reply is not None:
            json_dict['allow_sending_without_reply'] = self.allow_sending_without_reply
        if self.quote is not None:
            json_dict['quote'] = self.quote
        if self.quote_parse_mode is not None:
            json_dict['quote_parse_mode'] = self.quote_parse_mode
        if self.quote_entities is not None:
            json_dict['quote_entities'] = [entity.to_dict() for entity in self.quote_entities]
        if self.quote_position is not None:
            json_dict['quote_position'] = self.quote_position
        return json_dict
    
    def to_json(self) -> str:
        return json.dumps(self.to_dict())
        
    
class UsersShared(JsonDeserializable):
    """
    This object contains information about the users whose identifiers were shared with the bot
    using a KeyboardButtonRequestUsers button.

    Telegram documentation: https://core.telegram.org/bots/api#usersshared

    :param request_id: Identifier of the request
    :type request_id: :obj:`int`

    :param users: Information about users shared with the bot
    :type users: :obj:`list` of :obj:`types.SharedUser`

    :return: Instance of the class
    :rtype: :class:`UsersShared`
    """
    @classmethod
    def de_json(cls, json_string):
        if json_string is None: return None
        obj = cls.check_json(json_string)
        obj['users'] = [SharedUser.de_json(user) for user in obj['users']]
        return cls(**obj)

    def __init__(self, request_id: int, users: List[SharedUser], **kwargs):
        self.request_id: int = request_id
        self.users: List[SharedUser] = users

    @property
    def user_id(self) -> None:
        log_deprecation_warning('The parameter "user_id" is deprecated, use "user_ids" instead')
        return None

    @property
    def user_ids(self) -> List[SharedUser]:
        log_deprecation_warning('The parameter "user_ids" is deprecated, use "users" instead')
        return self.users


class ChatBoostUpdated(JsonDeserializable):
    """
    This object represents a boost added to a chat or changed.

    Telegram documentation: https://core.telegram.org/bots/api#chatboostupdated

    :param chat: Chat which was boosted
    :type chat: :class:`Chat`

    :param boost: Infomation about the chat boost
    :type boost: :class:`ChatBoost`

    :return: Instance of the class
    :rtype: :class:`ChatBoostUpdated`
    """

    @classmethod
    def de_json(cls, json_string):
        if json_string is None: return None
        obj = cls.check_json(json_string)        
        obj['chat'] = Chat.de_json(obj['chat'])
        obj['boost'] = ChatBoost.de_json(obj['boost'])
        return cls(**obj)

    def __init__(self, chat, boost, **kwargs):
        self.chat: Chat = chat
        self.boost: ChatBoost = boost
        
    
class ChatBoostRemoved(JsonDeserializable):
    """
    This object represents a boost removed from a chat.

    Telegram documentation: https://core.telegram.org/bots/api#chatboostremoved

    :param chat: Chat which was boosted
    :type chat: :class:`Chat`

    :param boost_id: Unique identifier of the boost
    :type boost_id: :obj:`str`

    :param remove_date: Point in time (Unix timestamp) when the boost was removed
    :type remove_date: :obj:`int`

    :param source: Source of the removed boost
    :type source: :class:`ChatBoostSource`

    :return: Instance of the class
    :rtype: :class:`ChatBoostRemoved`
    """

    @classmethod
    def de_json(cls, json_string):
        if json_string is None: return None
        obj = cls.check_json(json_string)
        obj['chat'] = Chat.de_json(obj['chat'])
        obj['source'] = ChatBoostSource.de_json(obj['source'])        
        return cls(**obj)

    def __init__(self, chat, boost_id, remove_date, source, **kwargs):
        self.chat: Chat = chat
        self.boost_id: str = boost_id
        self.remove_date: int = remove_date
        self.source: ChatBoostSource = source
        
    
class ChatBoostSource(ABC, JsonDeserializable):
    """
    This object describes the source of a chat boost. It can be one of
        ChatBoostSourcePremium
        ChatBoostSourceGiftCode
        ChatBoostSourceGiveaway

    Telegram documentation: https://core.telegram.org/bots/api#chatboostsource

    :return: Instance of the class
    :rtype: :class:`ChatBoostSourcePremium` or :class:`ChatBoostSourceGiftCode` or :class:`ChatBoostSourceGiveaway`
    """

    @classmethod
    def de_json(cls, json_string):
        if json_string is None: return None
        obj = cls.check_json(json_string)
        if obj["source"] == "premium":
            return ChatBoostSourcePremium.de_json(obj)
        elif obj["source"] == "gift_code":
            return ChatBoostSourceGiftCode.de_json(obj)
        elif obj["source"] == "giveaway":
            return ChatBoostSourceGiveaway.de_json(obj)
        return None


# noinspection PyUnresolvedReferences
class ChatBoostSourcePremium(ChatBoostSource):
    """
    The boost was obtained by subscribing to Telegram Premium or by gifting a Telegram Premium subscription to another user.

    Telegram documentation: https://core.telegram.org/bots/api#chatboostsourcepremium

    :param source: Source of the boost, always “premium”
    :type source: :obj:`str`

    :param user: User that boosted the chat
    :type user: :class:`User`

    :return: Instance of the class
    :rtype: :class:`ChatBoostSourcePremium`
    """

    @classmethod
    def de_json(cls, json_string):
        if json_string is None: return None
        obj = cls.check_json(json_string)
        obj['user'] = User.de_json(obj['user'])
        return cls(**obj)

    def __init__(self, source, user, **kwargs):
        self.source: str = source
        self.user: User = user


# noinspection PyUnresolvedReferences
class ChatBoostSourceGiftCode(ChatBoostSource):
    """
    The boost was obtained by the creation of Telegram Premium gift codes to boost a chat.

    Telegram documentation: https://core.telegram.org/bots/api#chatboostsourcegiftcode

    :param source: Source of the boost, always “gift_code”
    :type source: :obj:`str`

    :param user: User for which the gift code was created
    :type user: :class:`User`

    :return: Instance of the class
    :rtype: :class:`ChatBoostSourceGiftCode`
    """

    @classmethod
    def de_json(cls, json_string):
        if json_string is None: return None
        obj = cls.check_json(json_string)
        obj['user'] = User.de_json(obj['user'])
        return cls(**obj)

    def __init__(self, source, user, **kwargs):
        self.source: str = source
        self.user: User = user


# noinspection PyUnresolvedReferences
class ChatBoostSourceGiveaway(ChatBoostSource):
    """
    The boost was obtained by the creation of a Telegram Premium giveaway.

    Telegram documentation: https://core.telegram.org/bots/api#chatboostsourcegiveaway

    :param source: Source of the boost, always “giveaway”
    :type source: :obj:`str`

    :param giveaway_message_id: Identifier of a message in the chat with the giveaway; the message could have been deleted already. May be 0 if the message isn't sent yet.
    :type giveaway_message_id: :obj:`int`

    :param user: User that won the prize in the giveaway if any
    :type user: :class:`User`

    :param is_unclaimed: True, if the giveaway was completed, but there was no user to win the prize
    :type is_unclaimed: :obj:`bool`

    :param prize_star_count: Optional. The number of Telegram Stars to be split between giveaway winners; for Telegram Star giveaways only
    :type prize_star_count: :obj:`int`

    :return: Instance of the class
    :rtype: :class:`ChatBoostSourceGiveaway`
    """

    @classmethod
    def de_json(cls, json_string):
        if json_string is None: return None
        obj = cls.check_json(json_string)
        obj['user'] = User.de_json(obj.get('user'))
        return cls(**obj)

    def __init__(self, source, giveaway_message_id, user=None, is_unclaimed=None, prize_star_count=None, **kwargs):
        self.source: str = source
        self.giveaway_message_id: int = giveaway_message_id
        self.user: Optional[User] = user
        self.is_unclaimed: Optional[bool] = is_unclaimed
        self.prize_star_count: Optional[int] = prize_star_count


class ChatBoost(JsonDeserializable):
    """
    This object contains information about a chat boost.

    Telegram documentation: https://core.telegram.org/bots/api#chatboost

    :param boost_id: Unique identifier of the boost
    :type boost_id: :obj:`str`

    :param add_date: Point in time (Unix timestamp) when the chat was boosted
    :type add_date: :obj:`int`

    :param expiration_date: Point in time (Unix timestamp) when the boost will automatically expire, unless the booster's Telegram Premium subscription is prolonged
    :type expiration_date: :obj:`int`

    :param source: Optional. Source of the added boost (made Optional for now due to API error)
    :type source: :class:`ChatBoostSource`

    :return: Instance of the class
    :rtype: :class:`ChatBoost`
    """

    @classmethod
    def de_json(cls, json_string):
        if json_string is None: return None
        obj = cls.check_json(json_string)
        if not 'boost_id' in obj:
            # Suppose that the field "boost_id" is not always provided by Telegram
            logger.warning('The field "boost_id" is not found in received ChatBoost.')
            obj['boost_id'] = None
        if not 'add_date' in obj:
            # Suppose that the field "boost_id" is not always provided by Telegram
            logger.warning('The field "add_date" is not found in received ChatBoost.')
            obj['add_date'] = None
        if not 'expiration_date' in obj:
            # Suppose that the field "boost_id" is not always provided by Telegram
            logger.warning('The field "expiration_date" is not found in received ChatBoost.')
            obj['expiration_date'] = None
        source = obj.get('source', None)
        obj['source'] = ChatBoostSource.de_json(source) if source else None
        return cls(**obj)

    def __init__(self, boost_id, add_date, expiration_date, source, **kwargs):
        self.boost_id: str = boost_id
        self.add_date: int = add_date
        self.expiration_date: int = expiration_date
        self.source: ChatBoostSource = source
        

class UserChatBoosts(JsonDeserializable):
    """
    This object represents a list of boosts added to a chat by a user.

    Telegram documentation: https://core.telegram.org/bots/api#userchatboosts

    :param boosts: The list of boosts added to the chat by the user
    :type boosts: :obj:`list` of :class:`ChatBoost`

    :return: Instance of the class
    :rtype: :class:`UserChatBoosts`
    """

    @classmethod
    def de_json(cls, json_string):
        if json_string is None: return None
        obj = cls.check_json(json_string)
        obj['boosts'] = [ChatBoost.de_json(boost) for boost in obj['boosts']]
        return cls(**obj)

    def __init__(self, boosts, **kwargs):
        self.boosts: List[ChatBoost] = boosts
    

class InaccessibleMessage(JsonDeserializable):
    """
    This object describes a message that was deleted or is otherwise inaccessible to the bot.

    Telegram documentation: https://core.telegram.org/bots/api#inaccessiblemessage

    :param chat: Chat the message belonged to
    :type chat: :class:`Chat`

    :param message_id: Unique message identifier inside the chat
    :type message_id: :obj:`int`

    :param date: Always 0. The field can be used to differentiate regular and inaccessible messages.
    :type date: :obj:`int`

    :return: Instance of the class
    :rtype: :class:`InaccessibleMessage`
    """

    @classmethod
    def de_json(cls, json_string):
        if json_string is None: return None
        obj = cls.check_json(json_string)
        obj['chat'] = Chat.de_json(obj['chat'])
        return cls(**obj)

    def __init__(self, chat, message_id, date, **kwargs):
        self.chat: Chat = chat
        self.message_id: int = message_id
        self.date: int = date

    @staticmethod
    def __universal_deprecation(property_name):
        log_deprecation_warning(f'Deprecation warning: the field "{property_name}" is not accessible for InaccessibleMessage. You should check if your object is Message instance before access.')
        return None

    def __getattr__(self, item):
        if item in [
            'message_thread_id', 'from_user', 'sender_chat', 'forward_origin', 'is_topic_message',
            'is_automatic_forward', 'reply_to_message', 'external_reply', 'qoute', 'via_bot', 'edit_date',
            'has_protected_content', 'media_group_id', 'author_signature', 'text', 'entities', 'link_preview_options',
            'animation', 'audio', 'document', 'photo', 'sticker', 'story', 'video', 'video_note', 'voice', 'caption',
            'caption_entities', 'has_media_spoiler', 'contact', 'dice', 'game', 'poll', 'venue', 'location',
            'new_chat_members', 'left_chat_member', 'new_chat_title', 'new_chat_photo', 'delete_chat_photo',
            'group_chat_created', 'supergroup_chat_created', 'channel_chat_created', 'message_auto_delete_timer_changed',
            'migrate_to_chat_id', 'migrate_from_chat_id', 'pinned_message', 'invoice', 'successful_payment',
            'users_shared', 'chat_shared', 'connected_website', 'write_access_allowed', 'passport_data',
            'proximity_alert_triggered', 'chat_background_set', 'forum_topic_created', 'forum_topic_edited', 'forum_topic_closed',
            'forum_topic_reopened', 'general_forum_topic_hidden', 'general_forum_topic_unhidden', 'giveaway_created',
            'giveaway', 'giveaway_winners', 'giveaway_completed', 'video_chat_scheduled', 'video_chat_started',
            'video_chat_ended', 'video_chat_participants_invited', 'web_app_data', 'reply_markup'
        ]:
            return self.__universal_deprecation(item)
        else:
            raise AttributeError(f'"{self.__class__.__name__}" object has no attribute "{item}"')


class ChatBoostAdded(JsonDeserializable):
    """
    This object represents a service message about a user boosting a chat.

    Telegram documentation: https://core.telegram.org/bots/api#chatboostadded

    :param boost_count: Number of boosts added by the user
    :type boost_count: :obj:`int`

    :return: Instance of the class
    :rtype: :class:`ChatBoostAdded`
    """

    @classmethod
    def de_json(cls, json_string):
        if json_string is None: return None
        obj = cls.check_json(json_string)
        return cls(**obj)
    
    def __init__(self, boost_count, **kwargs):
        self.boost_count: int = boost_count


# noinspection PyShadowingBuiltins
class BusinessConnection(JsonDeserializable):
    """
    This object describes the connection of the bot with a business account.

    Telegram documentation: https://core.telegram.org/bots/api#businessconnection

    :param id: Unique identifier of the business connection
    :type id: :obj:`str`

    :param user: Business account user that created the business connection
    :type user: :class:`User`

    :param user_chat_id: Identifier of a private chat with the user who created the business connection
    :type user_chat_id: :obj:`int`

    :param date: Date the connection was established in Unix time
    :type date: :obj:`int`

    :param can_reply: Deprecated, use :attr:`rights` instead. True, if the bot can reply to messages from the business account
    :type can_reply: :obj:`bool`

    :param rights: Optional. Rights of the business bot
    :type rights: :class:`BusinessBotRights`

    :param is_enabled: True, if the connection is active
    :type is_enabled: :obj:`bool`

    :return: Instance of the class
    :rtype: :class:`BusinessConnection`
    """

    @classmethod
    def de_json(cls, json_string):
        if json_string is None: return None
        obj = cls.check_json(json_string)
        obj['user'] = User.de_json(obj['user'])
        obj['rights'] = BusinessBotRights.de_json(obj.get('rights'))
        return cls(**obj)
    
    def __init__(self, id, user, user_chat_id, date, can_reply, is_enabled,
                    rights=None, **kwargs):
        self.id: str = id
        self.user: User = user
        self.user_chat_id: int = user_chat_id
        self.date: int = date
        self.rights: Optional[BusinessBotRights] = rights
        self.is_enabled: bool = is_enabled

    @property
    def can_reply(self) -> bool:
        """
        Deprecated, use :attr:`rights` instead.
        """
        log_deprecation_warning('The field "can_reply" is deprecated, use "rights" instead')
        return self.rights is not None and self.rights.can_reply



class BusinessMessagesDeleted(JsonDeserializable):
    """
    This object is received when messages are deleted from a connected business account.

    Telegram documentation: https://core.telegram.org/bots/api#businessmessagesdeleted

    :param business_connection_id: Unique identifier of the business connection
    :type business_connection_id: :obj:`str`

    :param chat: Information about a chat in the business account. The bot may not have access to the chat or the corresponding user.
    :type chat: :class:`Chat`

    :param message_ids: A JSON-serialized list of identifiers of deleted messages in the chat of the business account
    :type message_ids: :obj:`list` of :obj:`int`

    :return: Instance of the class
    :rtype: :class:`BusinessMessagesDeleted`
    """

    @classmethod
    def de_json(cls, json_string):
        if json_string is None: return None
        obj = cls.check_json(json_string)
        obj['chat'] = Chat.de_json(obj['chat'])
        return cls(**obj)
    

    def __init__(self, business_connection_id, chat, message_ids, **kwargs):
        self.business_connection_id: str = business_connection_id
        self.chat: Chat = chat
        self.message_ids: List[int] = message_ids
        

class BusinessIntro(JsonDeserializable):
    """
    This object represents a business intro.

    Telegram documentation: https://core.telegram.org/bots/api#businessintro

    :param title: Optional. Title text of the business intro
    :type title: :obj:`str`

    :param message: Optional. Message text of the business intro
    :type message: :obj:`str`

    :param sticker: Optional. Sticker of the business intro
    :type sticker: :class:`Sticker`

    :return: Instance of the class
    :rtype: :class:`BusinessIntro`
    """

    @classmethod
    def de_json(cls, json_string):
        if json_string is None: return None
        obj = cls.check_json(json_string)
        if 'sticker' in obj:
            obj['sticker'] = Sticker.de_json(obj['sticker'])
        return cls(**obj)
    
    def __init__(self, title=None, message=None, sticker=None, **kwargs):
        self.title: Optional[str] = title
        self.message: Optional[str] = message
        self.sticker: Optional[Sticker] = sticker


class BusinessLocation(JsonDeserializable):
    """
    This object represents a business location.

    Telegram documentation: https://core.telegram.org/bots/api#businesslocation

    :param address: Address of the business
    :type address: :obj:`str`

    :param location: Optional. Location of the business
    :type location: :class:`Location`

    :return: Instance of the class
    :rtype: :class:`BusinessLocation`
    """

    @classmethod
    def de_json(cls, json_string):
        if json_string is None: return None
        obj = cls.check_json(json_string)
        if 'location' in obj:
            obj['location'] = Location.de_json(obj['location'])
        return cls(**obj)
    
    def __init__(self, address, location=None, **kwargs):
        self.address: str = address
        self.location: Optional[Location] = location


class BusinessOpeningHoursInterval(JsonDeserializable):
    """
    This object represents a business opening hours interval.

    Telegram documentation: https://core.telegram.org/bots/api#businessopeninghoursinterval

    :param opening_minute: The minute's sequence number in a week, starting on Monday, marking the start of the time interval during which the business is open; 0 - 7 24 60
    :type opening_minute: :obj:`int`

    :param closing_minute: The minute's sequence number in a week, starting on Monday, marking the end of the time interval during which the business is open; 0 - 8 24 60
    :type closing_minute: :obj:`int`

    :return: Instance of the class
    :rtype: :class:`BusinessOpeningHoursInterval`
    """

    @classmethod
    def de_json(cls, json_string):
        if json_string is None: return None
        obj = cls.check_json(json_string)
        return cls(**obj)
    
    def __init__(self, opening_minute, closing_minute, **kwargs):
        self.opening_minute: int = opening_minute
        self.closing_minute: int = closing_minute


class BusinessOpeningHours(JsonDeserializable):
    """

    This object represents business opening hours.

    Telegram documentation: https://core.telegram.org/bots/api#businessopeninghours

    :param time_zone_name: Unique name of the time zone for which the opening hours are defined
    :type time_zone_name: :obj:`str`

    :param opening_hours: List of time intervals describing business opening hours
    :type opening_hours: :obj:`list` of :class:`BusinessOpeningHoursInterval`

    :return: Instance of the class

    :rtype: :class:`BusinessOpeningHours`
    """

    @classmethod
    def de_json(cls, json_string):
        if json_string is None: return None
        obj = cls.check_json(json_string)
        obj['opening_hours'] = [BusinessOpeningHoursInterval.de_json(interval) for interval in obj['opening_hours']]
        return cls(**obj)
    
    def __init__(self, time_zone_name, opening_hours, **kwargs):
        self.time_zone_name: str = time_zone_name
        self.opening_hours: List[BusinessOpeningHoursInterval] = opening_hours


class SharedUser(JsonDeserializable):
    """
    This object contains information about a user that was shared with the bot using a KeyboardButtonRequestUser button.

    Telegram documentation: https://core.telegram.org/bots/api#shareduser

    :param user_id: Identifier of the shared user. This number may have more than 32 significant bits and some programming languages may have difficulty/silent defects in interpreting it. But it has at most 52 significant bits, so 64-bit integers or double-precision float types are safe for storing these identifiers. The bot may not have access to the user and could be unable to use this identifier, unless the user is already known to the bot by some other means.
    :type user_id: :obj:`int`

    :param first_name: Optional. First name of the user, if the name was requested by the bot
    :type first_name: :obj:`str`

    :param last_name: Optional. Last name of the user, if the name was requested by the bot
    :type last_name: :obj:`str`

    :param username: Optional. Username of the user, if the username was requested by the bot
    :type username: :obj:`str`

    :param photo: Optional. Available sizes of the chat photo, if the photo was requested by the bot
    :type photo: :obj:`list` of :class:`PhotoSize`

    :return: Instance of the class
    :rtype: :class:`SharedUser`
    """

    @classmethod
    def de_json(cls, json_string):
        if json_string is None: return None
        obj = cls.check_json(json_string)
        if 'photo' in obj:
            obj['photo'] = [PhotoSize.de_json(photo) for photo in obj['photo']]
        return cls(**obj)
    
    def __init__(self, user_id, first_name=None, last_name=None, username=None, photo=None, **kwargs):
        self.user_id: int = user_id
        self.first_name: Optional[str] = first_name
        self.last_name: Optional[str] = last_name
        self.username: Optional[str] = username
        self.photo: Optional[List[PhotoSize]] = photo


class Birthdate(JsonDeserializable):
    """
    This object represents a user's birthdate.

    Telegram documentation: https://core.telegram.org/bots/api#birthdate

    :param day: Day of the user's birth; 1-31
    :type day: :obj:`int`

    :param month: Month of the user's birth; 1-12
    :type month: :obj:`int`

    :param year: Optional. Year of the user's birth
    :type year: :obj:`int`

    :return: Instance of the class
    :rtype: :class:`Birthdate`
    """

    @classmethod
    def de_json(cls, json_string):
        if json_string is None: return None
        obj = cls.check_json(json_string)
        return cls(**obj)
    
    def __init__(self, day, month, year=None, **kwargs):
        self.day: int = day
        self.month: int = month
        self.year: Optional[int] = year


class BackgroundFill(ABC, JsonDeserializable):
    """
    This object describes the way a background is filled based on the selected colors. Currently, it can be one of
        BackgroundFillSolid
        BackgroundFillGradient
        BackgroundFillFreeformGradient

    Telegram documentation: https://core.telegram.org/bots/api#backgroundfill

    :return: Instance of the class
    :rtype: :class:`BackgroundFillSolid` or :class:`BackgroundFillGradient` or :class:`BackgroundFillFreeformGradient`
    """

    @classmethod
    def de_json(cls, json_string):
        if json_string is None: return None
        obj = cls.check_json(json_string)
        if obj["type"] == "solid":
            return BackgroundFillSolid.de_json(obj)
        elif obj["type"] == "gradient":
            return BackgroundFillGradient.de_json(obj)
        elif obj["type"] == "freeform_gradient":
            return BackgroundFillFreeformGradient.de_json(obj)
        return None


# noinspection PyShadowingBuiltins
class BackgroundFillSolid(BackgroundFill):
    """
    The background is filled using the selected color.

    Telegram documentation: https://core.telegram.org/bots/api#backgroundfillsolid

    :param type: Type of the background fill, always “solid”
    :type type: :obj:`str`

    :param color: The color of the background fill in the RGB24 format
    :type color: :class:`int`

    :return: Instance of the class
    :rtype: :class:`BackgroundFillSolid`
    """

    @classmethod
    def de_json(cls, json_string):
        if json_string is None: return None
        obj = cls.check_json(json_string)
        return cls(**obj)

    def __init__(self, type, color, **kwargs):
        self.type: str = type
        self.color: int = color


# noinspection PyShadowingBuiltins
class BackgroundFillGradient(BackgroundFill):
    """
    The background is a gradient fill.

    Telegram documentation: https://core.telegram.org/bots/api#backgroundfillgradient

    :param type: Type of the background fill, always “gradient”
    :type type: :obj:`str`

    :param top_color: Top color of the gradient in the RGB24 format
    :type top_color: :class:`int`

    :param bottom_color: Bottom color of the gradient in the RGB24 format
    :type bottom_color: :class:`int`

    :param rotation_angle: Clockwise rotation angle of the background fill in degrees; 0-359
    :type rotation_angle: :class:`int`

    :return: Instance of the class
    :rtype: :class:`BackgroundFillGradient`
    """

    @classmethod
    def de_json(cls, json_string):
        if json_string is None: return None
        obj = cls.check_json(json_string)
        return cls(**obj)

    def __init__(self, type, top_color, bottom_color, rotation_angle, **kwargs):
        self.type: str = type
        self.top_color: int = top_color
        self.bottom_color: int = bottom_color
        self.rotation_angle: int = rotation_angle


# noinspection PyShadowingBuiltins
class BackgroundFillFreeformGradient(BackgroundFill):
    """
    The background is a freeform gradient that rotates after every message in the chat.

    Telegram documentation: https://core.telegram.org/bots/api#backgroundfillfreeformgradient

    :param type: Type of the background fill, always “freeform_gradient”
    :type type: :obj:`str`

    :param colors: A list of the 3 or 4 base colors that are used to generate the freeform gradient in the RGB24 format
    :type colors: :obj:`list` of :class:`int`

    :return: Instance of the class
    :rtype: :class:`BackgroundFillFreeformGradient`
    """

    @classmethod
    def de_json(cls, json_string):
        if json_string is None: return None
        obj = cls.check_json(json_string)
        return cls(**obj)

    def __init__(self, type, colors, **kwargs):
        self.type: str = type
        self.colors: List[int] = colors


class BackgroundType(ABC, JsonDeserializable):
    """
    This object describes the type of a background. Currently, it can be one of
        BackgroundTypeFill
        BackgroundTypeWallpaper
        BackgroundTypePattern
        BackgroundTypeChatTheme

    Telegram documentation: https://core.telegram.org/bots/api#backgroundtype

    :return: Instance of the class
    :rtype: :class:`BackgroundTypeFill` or :class:`BackgroundTypeWallpaper` or :class:`BackgroundTypePattern` or :class:`BackgroundTypeChatTheme`
    """

    @classmethod
    def de_json(cls, json_string):
        if json_string is None: return None
        obj = cls.check_json(json_string)
        if obj["type"] == "fill":
            return BackgroundTypeFill.de_json(obj)
        elif obj["type"] == "wallpaper":
            return BackgroundTypeWallpaper.de_json(obj)
        elif obj["type"] == "pattern":
            return BackgroundTypePattern.de_json(obj)
        elif obj["type"] == "chat_theme":
            return BackgroundTypeChatTheme.de_json(obj)
        return None


# noinspection PyShadowingBuiltins
class BackgroundTypeFill(BackgroundFill):
    """
    The background is automatically filled based on the selected colors.

    Telegram documentation: https://core.telegram.org/bots/api#backgroundtypefill

    :param type: Type of the background, always “fill”
    :type type: :obj:`str`

    :param fill: The background fill
    :type fill: :class:`BackgroundFill`

    :param dark_theme_dimming: Dimming of the background in dark themes, as a percentage; 0-100
    :type dark_theme_dimming: :obj:`int`

    :return: Instance of the class
    :rtype: :class:`BackgroundTypeFill`
    """

    @classmethod
    def de_json(cls, json_string):
        if json_string is None: return None
        obj = cls.check_json(json_string)
        obj['fill'] = BackgroundFill.de_json(obj['fill'])
        return cls(**obj)

    def __init__(self, type, fill, dark_theme_dimming, **kwargs):
        self.type: str = type
        self.fill: BackgroundFill = fill
        self.dark_theme_dimming: int = dark_theme_dimming


# noinspection PyShadowingBuiltins
class BackgroundTypeWallpaper(BackgroundFill):
    """
    The background is a wallpaper in the JPEG format.

    Telegram documentation: https://core.telegram.org/bots/api#backgroundtypewallpaper

    :param type: Type of the background, always “wallpaper”
    :type type: :obj:`str`

    :param document: Document with the wallpaper
    :type document: :class:`Document`

    :param dark_theme_dimming: Dimming of the background in dark themes, as a percentage; 0-100
    :type dark_theme_dimming: :obj:`int`

    :param is_blurred: Optional. True, if the wallpaper is downscaled to fit in a 450x450 square and then box-blurred with radius 12
    :type is_blurred: :obj:`bool`

    :param is_moving: Optional. True, if the background moves slightly when the device is tilted
    :type is_moving: :obj:`bool`

    :return: Instance of the class
    :rtype: :class:`BackgroundTypeWallpaper`
    """

    @classmethod
    def de_json(cls, json_string):
        if json_string is None: return None
        obj = cls.check_json(json_string)
        obj['document'] = Document.de_json(obj['document'])
        return cls(**obj)

    def __init__(self, type, document, dark_theme_dimming, is_blurred=None, is_moving=None, **kwargs):
        self.type: str = type
        self.document: Document = document
        self.dark_theme_dimming: int = dark_theme_dimming
        self.is_blurred: Optional[bool] = is_blurred
        self.is_moving: Optional[bool] = is_moving


# noinspection PyShadowingBuiltins
class BackgroundTypePattern(BackgroundFill):
    """
    The background is a wallpaper in the JPEG format.

    Telegram documentation: https://core.telegram.org/bots/api#backgroundtypepattern

    :param type: Type of the background, always “pattern”
    :type type: :obj:`str`

    :param document: Document with the pattern
    :type document: :class:`Document`

    :param fill: The background fill that is combined with the pattern
    :type fill: :class:`BackgroundFill`

    :param intensity: Intensity of the pattern when it is shown above the filled background; 0-100
    :type intensity: :obj:`int`

    :param is_inverted: Optional. True, if the background fill must be applied only to the pattern itself. All other pixels are black in this case. For dark themes only
    :type is_inverted: :obj:`bool`

    :param is_moving: Optional. True, if the background moves slightly when the device is tilted
    :type is_moving: :obj:`bool`

    :return: Instance of the class
    :rtype: :class:`BackgroundTypePattern`
    """

    @classmethod
    def de_json(cls, json_string):
        if json_string is None: return None
        obj = cls.check_json(json_string)
        obj['document'] = Document.de_json(obj['document'])
        return cls(**obj)

    def __init__(self, type, document, fill, intensity, is_inverted=None, is_moving=None, **kwargs):
        self.type: str = type
        self.document: Document = document
        self.fill: BackgroundFill = fill
        self.intensity: int = intensity
        self.is_inverted: Optional[bool] = is_inverted
        self.is_moving: Optional[bool] = is_moving


# noinspection PyShadowingBuiltins
class BackgroundTypeChatTheme(BackgroundFill):
    """
    The background is taken directly from a built-in chat theme.

    Telegram documentation: https://core.telegram.org/bots/api#backgroundtypechattheme

    :param type: Type of the background, always “chat_theme”
    :type type: :obj:`str`

    :param theme_name: Intensity of the pattern when it is shown above the filled background; 0-100
    :type theme_name: :obj:`str`

    :return: Instance of the class
    :rtype: :class:`BackgroundTypeChatTheme`
    """

    @classmethod
    def de_json(cls, json_string):
        if json_string is None: return None
        obj = cls.check_json(json_string)
        return cls(**obj)

    def __init__(self, type, theme_name, **kwargs):
        self.type: str = type
        self.theme_name: str = theme_name


# noinspection PyShadowingBuiltins
class ChatBackground(JsonDeserializable):
    """
    This object represents a chat background.

    Telegram documentation: https://core.telegram.org/bots/api#chatbackground

    :param type: Type of the background
    :type type: :class:`BackgroundType`

    :return: Instance of the class
    :rtype: :class:`ChatBackground`
    """

    @classmethod
    def de_json(cls, json_string):
        if json_string is None: return None
        obj = cls.check_json(json_string)
        obj['type'] = BackgroundType.de_json(obj['type'])
        return cls(**obj)

    def __init__(self, type, **kwargs):
        self.type: BackgroundType = type


class RevenueWithdrawalState(JsonDeserializable):
    # noinspection PyUnresolvedReferences
    """
    This object describes the state of a revenue withdrawal operation. Currently, it can be one of
        RevenueWithdrawalStatePending
        RevenueWithdrawalStateSucceeded
        RevenueWithdrawalStateFailed

    Telegram documentation: https://core.telegram.org/bots/api#revenuewithdrawalstate

    :param type: Type of the state, always “pending” or “succeeded” or “failed”
    :type type: :obj:`str`

    :return: Instance of the class
    :rtype: :class:`RevenueWithdrawalStatePending` or :class:`RevenueWithdrawalStateSucceeded` or :class:`RevenueWithdrawalStateFailed`
    """

    @classmethod
    def de_json(cls, json_string):
        if json_string is None: return None
        obj = cls.check_json(json_string)
        if obj["type"] == "pending":
            return RevenueWithdrawalStatePending.de_json(obj)
        elif obj["type"] == "succeeded":
            return RevenueWithdrawalStateSucceeded.de_json(obj)
        elif obj["type"] == "failed":
            return RevenueWithdrawalStateFailed.de_json(obj)
        return None


# noinspection PyShadowingBuiltins
class RevenueWithdrawalStatePending(RevenueWithdrawalState):
    """
    The withdrawal is in progress.

    Telegram documentation: https://core.telegram.org/bots/api#revenuewithdrawalstatepending

    :param type: Type of the state, always “pending”
    :type type: :obj:`str`

    :return: Instance of the class
    :rtype: :class:`RevenueWithdrawalStatePending`
    """

    def __init__(self, type, **kwargs):
        self.type: str = type

    @classmethod
    def de_json(cls, json_string):
        if json_string is None: return None
        obj = cls.check_json(json_string)
        return cls(**obj)


# noinspection PyShadowingBuiltins
class RevenueWithdrawalStateSucceeded(RevenueWithdrawalState):
    """
    The withdrawal succeeded.

    Telegram documentation: https://core.telegram.org/bots/api#revenuewithdrawalstatesucceeded

    :param type: Type of the state, always “succeeded”
    :type type: :obj:`str`

    :param date: Date the withdrawal was completed in Unix time
    :type date: :obj:`int`

    :param url: An HTTPS URL that can be used to see transaction details
    :type url: :obj:`str`

    :return: Instance of the class
    :rtype: :class:`RevenueWithdrawalStateSucceeded`
    """

    def __init__(self, type, date, url, **kwargs):
        self.type: str = type
        self.date: int = date
        self.url: str = url

    @classmethod
    def de_json(cls, json_string):
        if json_string is None: return None
        obj = cls.check_json(json_string)
        return cls(**obj)


# noinspection PyShadowingBuiltins
class RevenueWithdrawalStateFailed(RevenueWithdrawalState):
    """
    The withdrawal failed and the transaction was refunded.

    Telegram documentation: https://core.telegram.org/bots/api#revenuewithdrawalstatefailed

    :param type: Type of the state, always “failed”
    :type type: :obj:`str`

    :return: Instance of the class
    :rtype: :class:`RevenueWithdrawalStateFailed`
    """

    def __init__(self, type, **kwargs):
        self.type: str = type

    @classmethod
    def de_json(cls, json_string):
        if json_string is None: return None
        obj = cls.check_json(json_string)
        return cls(**obj)


class TransactionPartner(JsonDeserializable):
    # noinspection PyUnresolvedReferences
    """
    This object describes the source of a transaction, or its recipient for outgoing transactions. Currently, it can be one of
        TransactionPartnerFragment
        TransactionPartnerUser
        TransactionPartnerOther

    Telegram documentation: https://core.telegram.org/bots/api#transactionpartner

    :param type: Type of the transaction partner
    :type type: :obj:`str`

    :return: Instance of the class
    :rtype: :class:`TransactionPartnerFragment` or :class:`TransactionPartnerUser` or :class:`TransactionPartnerOther`
    """

    @classmethod
    def de_json(cls, json_string):
        if json_string is None: return None
        obj = cls.check_json(json_string)
        if obj["type"] == "fragment":
            return TransactionPartnerFragment.de_json(obj)
        elif obj["type"] == "user":
            return TransactionPartnerUser.de_json(obj)
        elif obj["type"] == "telegram_ads":
            return TransactionPartnerTelegramAds.de_json(obj)
        elif obj["type"] == "telegram_api":
            return TransactionPartnerTelegramApi.de_json(obj)
        elif obj["type"] == "affiliate_program":
            return TransactionPartnerAffiliateProgram.de_json(obj)
        elif obj["type"] == "other":
            return TransactionPartnerOther.de_json(obj)
        elif obj["type"] == "chat":
            return TransactionPartnerChat.de_json(obj)


# noinspection PyShadowingBuiltins
class TransactionPartnerFragment(TransactionPartner):
    """
    Describes a withdrawal transaction with Fragment.

    Telegram documentation: https://core.telegram.org/bots/api#transactionpartnerfragment

    :param type: Type of the transaction partner, always “fragment”
    :type type: :obj:`str`

    :param withdrawal_state: Optional. State of the transaction if the transaction is outgoing
    :type withdrawal_state: :class:`RevenueWithdrawalState`

    :return: Instance of the class
    :rtype: :class:`TransactionPartnerFragment`

    """

    def __init__(self, type, withdrawal_state=None, **kwargs):
        self.type: str = type
        self.withdrawal_state: Optional[RevenueWithdrawalState] = withdrawal_state

    @classmethod
    def de_json(cls, json_string):
        if json_string is None: return None
        obj = cls.check_json(json_string)
        if 'withdrawal_state' in obj:
            obj['withdrawal_state'] = RevenueWithdrawalState.de_json(obj['withdrawal_state'])
        return cls(**obj)


class TransactionPartnerTelegramApi(TransactionPartner):
    """
    Describes a transaction with payment for paid broadcasting.

    Telegram documentation: https://core.telegram.org/bots/api#transactionpartnertelegramapi

    :param type: Type of the transaction partner, always “telegram_api”
    :type type: :obj:`str`

    :param request_count: The number of successful requests that exceeded regular limits and were therefore billed
    :type request_count: :obj:`int`

    :return: Instance of the class
    :rtype: :class:`TransactionPartnerTelegramApi`
    """

    def __init__(self, type, request_count, **kwargs):
        self.type: str = type
        self.request_count: int = request_count

    @classmethod
    def de_json(cls, json_string):
        if json_string is None: return None
        obj = cls.check_json(json_string)
        return cls(**obj)


# noinspection PyShadowingBuiltins
class TransactionPartnerUser(TransactionPartner):
    """
    Describes a transaction with a user.

    Telegram documentation: https://core.telegram.org/bots/api#transactionpartneruser

    :param type: Type of the transaction partner, always “user”
    :type type: :obj:`str`

    :param transaction_type: Type of the transaction, currently one of “invoice_payment” for payments via invoices,
        “paid_media_payment” for payments for paid media, “gift_purchase” for gifts sent by the bot, “premium_purchase” for Telegram Premium subscriptions
        gifted by the bot, “business_account_transfer” for direct transfers from managed business accounts
    :type transaction_type: :obj:`str`

    :param user: Information about the user
    :type user: :class:`User`

    :param affiliate: Optional. Information about the affiliate that received a commission via this transaction
    :type affiliate: :class:`AffiliateInfo`

    :param invoice_payload: Optional, Bot-specified invoice payload
    :type invoice_payload: :obj:`str`

    :param subscription_period: Optional. The duration of the paid subscription
    :type subscription_period: :obj:`int`

    :param paid_media: Optional. Information about the paid media bought by the user
    :type paid_media: :obj:`list` of :class:`PaidMedia`

    :param gift: Optional. The gift sent to the user by the bot
    :type gift: :class:`Gift`

    :param premium_subscription_duration: Optional. Number of months the gifted Telegram Premium subscription will be active for; for “premium_purchase” transactions only
    :type premium_subscription_duration: :obj:`int`

    :return: Instance of the class
    :rtype: :class:`TransactionPartnerUser`
    """

    def __init__(self, type, user, affiliate=None, invoice_payload=None, paid_media: Optional[List[PaidMedia]] = None, 
                    subscription_period=None, gift: Optional[Gift] = None, premium_subscription_duration: Optional[int] = None, 
                    transaction_type: Optional[str] = None, **kwargs):
        self.type: str = type
        self.user: User = user
        self.affiliate: Optional[AffiliateInfo] = affiliate
        self.invoice_payload: Optional[str] = invoice_payload
        self.paid_media: Optional[List[PaidMedia]] = paid_media
        self.subscription_period: Optional[int] = subscription_period
        self.gift: Optional[Gift] = gift
        self.premium_subscription_duration: Optional[int] = premium_subscription_duration
        self.transaction_type: Optional[str] = transaction_type

    @classmethod
    def de_json(cls, json_string):
        if json_string is None: return None
        obj = cls.check_json(json_string)
        obj['user'] = User.de_json(obj['user'])
        if 'paid_media' in obj:
            obj['paid_media'] = [PaidMedia.de_json(media) for media in obj['paid_media']]
        if 'gift' in obj:
            obj['gift'] = Gift.de_json(obj['gift'])
        if 'affiliate' in obj:
            obj['affiliate'] = AffiliateInfo.de_json(obj['affiliate'])
        return cls(**obj)


# noinspection PyShadowingBuiltins
class TransactionPartnerTelegramAds(TransactionPartner):
    """
    Describes a transaction with Telegram Ads.

    Telegram documentation: https://core.telegram.org/bots/api#transactionpartnertelegramads
    
    :param type: Type of the transaction partner, always “telegram_ads”
    :type type: :obj:`str`

    :return: Instance of the class
    :rtype: :class:`TransactionPartnerTelegramAds`
    """

    def __init__(self, type, **kwargs):
        self.type: str = type

    @classmethod
    def de_json(cls, json_string):
        if json_string is None: return None
        obj = cls.check_json(json_string)
        return obj


# noinspection PyShadowingBuiltins
class TransactionPartnerOther(TransactionPartner):
    """
    Describes a transaction with an unknown source or recipient.

    Telegram documentation: https://core.telegram.org/bots/api#transactionpartnerother

    :param type: Type of the transaction partner, always “other”
    :type type: :obj:`str`

    :return: Instance of the class
    :rtype: :class:`TransactionPartnerOther`
    """

    def __init__(self, type, **kwargs):
        self.type: str = type

    @classmethod
    def de_json(cls, json_string):
        if json_string is None: return None
        obj = cls.check_json(json_string)
        return cls(**obj)


# noinspection PyShadowingBuiltins
class StarTransaction(JsonDeserializable):
    """
    Describes a Telegram Star transaction.

    Telegram documentation: https://core.telegram.org/bots/api#startransaction

    :param id: Unique identifier of the transaction. Coincides with the identifer of the original transaction for refund transactions. Coincides with SuccessfulPayment.telegram_payment_charge_id for successful incoming payments from users.
    :type id: :obj:`str`

    :param amount: Number of Telegram Stars transferred by the transaction
    :type amount: :obj:`int`

    :param nanostar_amount: Optional. The number of 1/1000000000 shares of Telegram Stars transferred by the transaction; from 0 to 999999999
    :type nanostar_amount: :obj:`int`

    :param date: Date the transaction was created in Unix time
    :type date: :obj:`int`

    :param source: Optional. Source of an incoming transaction (e.g., a user purchasing goods or services, Fragment refunding a failed withdrawal). Only for incoming transactions
    :type source: :class:`TransactionPartner`

    :param receiver: Optional. Receiver of an outgoing transaction (e.g., a user for a purchase refund, Fragment for a withdrawal). Only for outgoing transactions
    :type receiver: :class:`TransactionPartner`

    :return: Instance of the class
    :rtype: :class:`StarTransaction`
    """

    @classmethod
    def de_json(cls, json_string):
        if json_string is None: return None
        obj = cls.check_json(json_string)
        if 'source' in obj:
            obj['source'] = TransactionPartner.de_json(obj['source'])
        if 'receiver' in obj:
            obj['receiver'] = TransactionPartner.de_json(obj['receiver'])
        return cls(**obj)
    
    def __init__(self, id, amount, date, source=None, receiver=None, nanostar_amount=None, **kwargs):
        self.id: str = id
        self.amount: int = amount
        self.date: int = date
        self.source: Optional[TransactionPartner] = source
        self.receiver: Optional[TransactionPartner] = receiver
        self.nanostar_amount: Optional[int] = nanostar_amount


class StarTransactions(JsonDeserializable):
    """
    Contains a list of Telegram Star transactions.

    Telegram documentation: https://core.telegram.org/bots/api#startransactions

    :param transactions: The list of transactions
    :type transactions: :obj:`list` of :class:`StarTransaction`

    :return: Instance of the class
    :rtype: :class:`StarTransactions`

    """

    @classmethod
    def de_json(cls, json_string):
        if json_string is None: return None
        obj = cls.check_json(json_string)
        obj['transactions'] = [StarTransaction.de_json(transaction) for transaction in obj['transactions']]
        return cls(**obj)
    
    def __init__(self, transactions, **kwargs):
        self.transactions: List[StarTransaction] = transactions


class PaidMedia(JsonDeserializable):
    """
    This object describes paid media. Currently, it can be one of

        PaidMediaPreview
        PaidMediaPhoto
        PaidMediaVideo

    Telegram documentation: https://core.telegram.org/bots/api#paidmedia

    :return: Instance of the class
    :rtype: :class:`PaidMediaPreview` or :class:`PaidMediaPhoto` or :class:`PaidMediaVideo`
    """

    @classmethod
    def de_json(cls, json_string):
        if json_string is None: return None
        obj = cls.check_json(json_string)
        if obj["type"] == "preview":
            return PaidMediaPreview.de_json(obj)
        elif obj["type"] == "photo":
            return PaidMediaPhoto.de_json(obj)
        elif obj["type"] == "video":
            return PaidMediaVideo.de_json(obj)


# noinspection PyShadowingBuiltins
class PaidMediaPreview(PaidMedia):
    """
    The paid media isn't available before the payment.

    Telegram documentation: https://core.telegram.org/bots/api#paidmediapreview

    :param type: Type of the paid media, always “preview”
    :type type: :obj:`str`

    :param width: Optional. Media width as defined by the sender
    :type width: :obj:`int`

    :param height: Optional. Media height as defined by the sender
    :type height: :obj:`int`

    :param duration: Optional. Duration of the media in seconds as defined by the sender
    :type duration: :obj:`int`

    :return: Instance of the class
    :rtype: :class:`PaidMediaPreview`
    """

    def __init__(self, type, width=None, height=None, duration=None, **kwargs):
        self.type: str = type
        self.width: Optional[int] = width
        self.height: Optional[int] = height
        self.duration: Optional[int] = duration

    @classmethod
    def de_json(cls, json_string):
        if json_string is None: return None
        obj = cls.check_json(json_string)
        return cls(**obj)


# noinspection PyShadowingBuiltins
class PaidMediaPhoto(PaidMedia):
    """
    The paid media is a photo.

    Telegram documentation: https://core.telegram.org/bots/api#paidmediaphoto

    :param type: Type of the paid media, always “photo”
    :type type: :obj:`str`

    :param photo: The photo
    :type photo: :obj:`list` of :class:`PhotoSize`

    :return: Instance of the class
    :rtype: :class:`PaidMediaPhoto`

    """

    def __init__(self, type, photo, **kwargs):
        self.type: str = type
        self.photo: List[PhotoSize] = photo

    @classmethod
    def de_json(cls, json_string):
        if json_string is None: return None
        obj = cls.check_json(json_string)

        obj['photo'] = [PhotoSize.de_json(photo) for photo in obj['photo']]
        return cls(**obj)


# noinspection PyShadowingBuiltins
class PaidMediaVideo(PaidMedia):
    """
    The paid media is a video.

    Telegram documentation: https://core.telegram.org/bots/api#paidmediavideo

    :param type: Type of the paid media, always “video”
    :type type: :obj:`str`

    :param video: The video
    :type video: :class:`Video`

    :return: Instance of the class
    :rtype: :class:`PaidMediaVideo`
    """

    def __init__(self, type, video, **kwargs):
        self.type: str = type
        self.video: Video = video

    @classmethod
    def de_json(cls, json_string):
        if json_string is None: return None
        obj = cls.check_json(json_string)
        obj['video'] = Video.de_json(obj['video'])
        return cls(**obj)


class PaidMediaInfo(JsonDeserializable):
    """
    Describes the paid media added to a message.

    Telegram documentation: https://core.telegram.org/bots/api#paidmediainfo

    :param star_count: The number of Telegram Stars that must be paid to buy access to the media
    :type star_count: :obj:`int`

    :param paid_media: Information about the paid media
    :type paid_media: :obj:`list` of :class:`PaidMedia`

    :return: Instance of the class
    :rtype: :class:`PaidMediaInfo`
    """

    @classmethod
    def de_json(cls, json_string):
        if json_string is None: return None
        obj = cls.check_json(json_string)
        obj['paid_media'] = [PaidMedia.de_json(media) for media in obj['paid_media']]
        return cls(**obj)
    
    def __init__(self, star_count, paid_media, **kwargs):
        self.star_count: int = star_count
        self.paid_media: List[PaidMedia] = paid_media


# noinspection PyShadowingBuiltins
class InputPaidMedia(JsonSerializable):
    """
    This object describes the paid media to be sent. Currently, it can be one of
        InputPaidMediaPhoto
        InputPaidMediaVideo

    Telegram documentation: https://core.telegram.org/bots/api#inputpaidmedia

    :return: Instance of the class
    :rtype: :class:`InputPaidMediaPhoto` or :class:`InputPaidMediaVideo`
    """

    def __init__(self, type: str, media: Union[str, InputFile], **kwargs):
        self.type: str = type
        self.media: Union[str, InputFile] = media

        if service_utils.is_string(self.media):
            self._media_name = ''
            self._media_dic = self.media
        else:
            self._media_name = service_utils.generate_random_token()
            self._media_dic = 'attach://{0}'.format(self._media_name)

    def to_json(self):
        return json.dumps(self.to_dict())
    
    def to_dict(self):
        data = {
            'type': self.type,
            'media': self._media_dic
        }
        return data
    
class InputPaidMediaPhoto(InputPaidMedia):
    """
    The paid media to send is a photo.

    Telegram documentation: https://core.telegram.org/bots/api#inputpaidmediaphoto

    :param type: Type of the media, must be photo
    :type type: :obj:`str`

    :param media: File to send. Pass a file_id to send a file that exists on the Telegram servers (recommended), pass an HTTP URL for
        Telegram to get a file from the Internet, or pass “attach://<file_attach_name>” to upload a new one using multipart/form-data
        under <file_attach_name> name. More information on Sending Files »
    :type media: :obj:`str`

    :return: Instance of the class
    :rtype: :class:`InputPaidMediaPhoto`
    """

    def __init__(self, media: Union[str, InputFile], **kwargs):
        super().__init__(type='photo', media=media)
    
class InputPaidMediaVideo(InputPaidMedia):
    """
    The paid media to send is a video.

    Telegram documentation: https://core.telegram.org/bots/api#inputpaidmediavideo

    :param type: Type of the media, must be video
    :type type: :obj:`str`

    :param media: File to send. Pass a file_id to send a file that exists on the Telegram servers (recommended), pass an HTTP URL for
        Telegram to get a file from the Internet, or pass “attach://<file_attach_name>” to upload a new one using multipart/form-data
        under <file_attach_name> name. More information on Sending Files »
    :type media: :obj:`str`

    :param thumbnail: Optional. Thumbnail of the file sent; can be ignored if thumbnail generation for the file is supported server-side.
        The thumbnail should be in JPEG format and less than 200 kB in size. A thumbnail's width and height should not exceed 320.
        Ignored if the file is not uploaded using multipart/form-data. Thumbnails can't be reused and can be only uploaded as a new file,
        so you can pass “attach://<file_attach_name>” if the thumbnail was uploaded using multipart/form-data under <file_attach_name>.
        More information on Sending Files »
    :type thumbnail: :class:`InputFile`

    :param cover: Cover for the video in the message. Pass a file_id to send a file that exists on the Telegram servers (recommended),
        pass an HTTP URL for Telegram to get a file from the Internet, or pass “attach://<file_attach_name>” to upload a new one using multipart/form-data under
        <file_attach_name> name. More information on Sending Files »
    :type cover: :obj:`str` or :class:`telebot.types.InputFile`

    :param start_timestamp: Start timestamp for the video in the message
    :type start_timestamp: :obj:`int`

    :param width: Optional. Video width
    :type width: :obj:`int`

    :param height: Optional. Video height
    :type height: :obj:`int`

    :param duration: Optional. Video duration in seconds
    :type duration: :obj:`int`

    :param supports_streaming: Optional. Pass True if the uploaded video is suitable for streaming
    :type supports_streaming: :obj:`bool`

    :return: Instance of the class
    :rtype: :class:`InputPaidMediaVideo`

    """
    def __init__(self, media: Union[str, InputFile], thumbnail: Optional[InputFile] = None, width: Optional[int] = None,
                 height: Optional[int] = None, duration: Optional[int] = None, supports_streaming: Optional[bool] = None,
                 cover: Optional[Union[str,InputFile]] = None, start_timestamp: Optional[int] = None, **kwargs):
        super().__init__(type='video', media=media)
        self.thumbnail: Optional[Union[str,InputFile]] = thumbnail
        self.width: Optional[int] = width
        self.height: Optional[int] = height
        self.duration: Optional[int] = duration
        self.supports_streaming: Optional[bool] = supports_streaming
        self.cover: Optional[Union[str,InputFile]] = cover
        self.start_timestamp: Optional[int] = start_timestamp



    def to_dict(self):
        data = super().to_dict()
        if self.thumbnail:
            data['thumbnail'] = self.thumbnail
        if self.width:
            data['width'] = self.width
        if self.height:
            data['height'] = self.height
        if self.duration:
            data['duration'] = self.duration
        if self.supports_streaming is not None:
            data['supports_streaming'] = self.supports_streaming
        if self.cover:
            data['cover'] = self.cover
        if self.start_timestamp:
            data['start_timestamp'] = self.start_timestamp
        return data

class RefundedPayment(JsonDeserializable):
    """
    This object contains basic information about a refunded payment.

    Telegram documentation: https://core.telegram.org/bots/api#refundedpayment

    :param currency: Three-letter ISO 4217 currency code, or “XTR” for payments in Telegram Stars. Currently, always “XTR”
    :type currency: :obj:`str`

    :param total_amount: Total refunded price in the smallest units of the currency (integer, not float/double). For example, for a price of US$ 1.45, total_amount = 145. See the exp parameter in currencies.json, it shows the number of digits past the decimal point for each currency (2 for the majority of currencies).
    :type total_amount: :obj:`int`

    :param invoice_payload: Bot-specified invoice payload
    :type invoice_payload: :obj:`str`

    :param telegram_payment_charge_id: Telegram payment identifier
    :type telegram_payment_charge_id: :obj:`str`

    :param provider_payment_charge_id: Optional. Provider payment identifier
    :type provider_payment_charge_id: :obj:`str`

    :return: Instance of the class
    :rtype: :class:`RefundedPayment`
    """

    def __init__(self, currency, total_amount, invoice_payload, telegram_payment_charge_id, provider_payment_charge_id=None, **kwargs):
        self.currency: str = currency
        self.total_amount: int = total_amount
        self.invoice_payload: str = invoice_payload
        self.telegram_payment_charge_id: str = telegram_payment_charge_id
        self.provider_payment_charge_id: Optional[str] = provider_payment_charge_id

    @classmethod
    def de_json(cls, json_string):
        if json_string is None: return None
        obj = cls.check_json(json_string)
        return cls(**obj)
    
    
class PaidMediaPurchased(JsonDeserializable):
    """
    This object contains information about a paid media purchase.

    Telegram documentation: https://core.telegram.org/bots/api#paidmediapurchased

    :param from_user: User who purchased the media
    :type from_user: :class:`User`

    :param paid_media_payload: Bot-specified paid media payload
    :type paid_media_payload: :obj:`str`

    :return: Instance of the class
    :rtype: :class:`PaidMediaPurchased`
    """

    def __init__(self, from_user, paid_media_payload, **kwargs):
        self.from_user: User = from_user
        self.paid_media_payload: str = paid_media_payload

    @classmethod
    def de_json(cls, json_string):
        if json_string is None: return None
        obj = cls.check_json(json_string)
        obj['from_user'] = User.de_json(obj['from_user'])
        return cls(**obj)
    

class CopyTextButton(JsonSerializable, JsonDeserializable):
    """
    This object represents an inline keyboard button that copies specified text to the clipboard.

    Telegram documentation: https://core.telegram.org/bots/api#copytextbutton

    :param text: The text to be copied to the clipboard; 1-256 characters
    :type text: :obj:`str`

    :return: Instance of the class
    :rtype: :class:`CopyTextButton`
    """
    def __init__(self, text: str, **kwargs):
        self.text: str = text

    def to_json(self):
        return json.dumps(self.to_dict())
    
    def to_dict(self):
        data = {
            'text': self.text
        }
        return data
    
    @classmethod
    def de_json(cls, json_string):
        if json_string is None: return None
        obj = cls.check_json(json_string)
        return cls(**obj)


class PreparedInlineMessage(JsonDeserializable):
    """
    Describes an inline message to be sent by a user of a Mini App.

    Telegram documentation: https://core.telegram.org/bots/api#preparedinlinemessage

    :param id: Unique identifier of the prepared message
    :type id: :obj:`str`

    :param expiration_date: Expiration date of the prepared message, in Unix time. Expired prepared messages can no longer be used
    :type expiration_date: :obj:`int`

    :return: Instance of the class
    :rtype: :class:`PreparedInlineMessage`
    """

    def __init__(self, id, expiration_date, **kwargs):
        self.id: str = id
        self.expiration_date: int = expiration_date

    @classmethod
    def de_json(cls, json_string):
        if json_string is None: return None
        obj = cls.check_json(json_string)
        return cls(**obj)
    

class Gift(JsonDeserializable):
    """
    This object represents a gift that can be sent by the bot.

    Telegram documentation: https://core.telegram.org/bots/api#gift

    :param id: Unique identifier of the gift
    :type id: :obj:`str`

    :param sticker: The sticker that represents the gift
    :type sticker: :class:`Sticker`

    :param star_count: The number of Telegram Stars that must be paid to send the sticker
    :type star_count: :obj:`int`

    :param upgrade_star_count: Optional. The number of Telegram Stars that must be paid to upgrade the gift to a unique one
    :type upgrade_star_count: :obj:`int`

    :param total_count: Optional. The total number of the gifts of this type that can be sent; for limited gifts only
    :type total_count: :obj:`int`

    :param remaining_count: Optional. The number of remaining gifts of this type that can be sent; for limited gifts only
    :type remaining_count: :obj:`int`

    :return: Instance of the class
    :rtype: :class:`Gift`
    """

    def __init__(self, id, sticker, star_count, total_count=None, remaining_count=None, upgrade_star_count=None, **kwargs):
        self.id: str = id
        self.sticker: Sticker = sticker
        self.star_count: int = star_count
        self.total_count: Optional[int] = total_count
        self.remaining_count: Optional[int] = remaining_count
        self.upgrade_star_count: Optional[int] = upgrade_star_count

    @classmethod
    def de_json(cls, json_string):
        if json_string is None: return None
        obj = cls.check_json(json_string)
        obj['sticker'] = Sticker.de_json(obj['sticker'])
        return cls(**obj)
    
class Gifts(JsonDeserializable):
    """
    This object represent a list of gifts.

    Telegram documentation: https://core.telegram.org/bots/api#gifts

    :param gifts: The list of gifts
    :type gifts: :obj:`list` of :class:`Gift`

    :return: Instance of the class
    :rtype: :class:`Gifts`
    """

    def __init__(self, gifts, **kwargs):
        self.gifts: List[Gift] = gifts

    @classmethod
    def de_json(cls, json_string):
        if json_string is None: return None
        obj = cls.check_json(json_string)
        obj['gifts'] = [Gift.de_json(gift) for gift in obj['gifts']]
        return cls(**obj)
    
    
class TransactionPartnerAffiliateProgram(TransactionPartner):
    """
    Describes the affiliate program that issued the affiliate commission received via this transaction.

    Telegram documentation: https://core.telegram.org/bots/api#transactionpartneraffiliateprogram

    :param type: Type of the transaction partner, always “affiliate_program”
    :type type: :obj:`str`

    :param sponsor_user: Optional. Information about the bot that sponsored the affiliate program
    :type sponsor_user: :class:`User`

    :param commission_per_mille: The number of Telegram Stars received by the bot for each 1000 Telegram Stars received by the affiliate program sponsor from referred users
    :type commission_per_mille: :obj:`int`

    :return: Instance of the class
    :rtype: :class:`TransactionPartnerAffiliateProgram`
    """

    def __init__(self, type, commission_per_mille, sponsor_user=None, **kwargs):
        self.type: str = type
        self.sponsor_user: Optional[User] = sponsor_user
        self.commission_per_mille: int = commission_per_mille

    @classmethod
    def de_json(cls, json_string):
        if json_string is None: return None
        obj = cls.check_json(json_string)
        if 'sponsor_user' in obj:
            obj['sponsor_user'] = User.de_json(obj['sponsor_user'])

        return cls(**obj)
    

class AffiliateInfo(JsonDeserializable):
    """
    Contains information about the affiliate that received a commission via this transaction.

    Telegram documentation: https://core.telegram.org/bots/api#affiliateinfo

    :param affiliate_user: Optional. The bot or the user that received an affiliate commission if it was received by a bot or a user
    :type affiliate_user: :class:`User`

    :param affiliate_chat: Optional. The chat that received an affiliate commission if it was received by a chat
    :type affiliate_chat: :class:`Chat`

    :param commission_per_mille: The number of Telegram Stars received by the affiliate for each 1000 Telegram Stars received by the bot from referred users
    :type commission_per_mille: :obj:`int`

    :param amount: Integer amount of Telegram Stars received by the affiliate from the transaction, rounded to 0; can be negative for refunds
    :type amount: :obj:`int`

    :param nanostar_amount: Optional. The number of 1/1000000000 shares of Telegram Stars received by the affiliate; from -999999999 to 999999999; can be negative for refunds
    :type nanostar_amount: :obj:`int`

    :return: Instance of the class
    :rtype: :class:`AffiliateInfo`
    """

    def __init__(self, commission_per_mille, amount, affiliate_user=None, affiliate_chat=None, nanostar_amount=None, **kwargs):
        self.affiliate_user: Optional[User] = affiliate_user
        self.affiliate_chat: Optional[Chat] = affiliate_chat
        self.commission_per_mille: int = commission_per_mille
        self.amount: int = amount
        self.nanostar_amount: Optional[int] = nanostar_amount

    @classmethod
    def de_json(cls, json_string):
        if json_string is None: return None
        obj = cls.check_json(json_string)
        if 'affiliate_user' in obj:
            obj['affiliate_user'] = User.de_json(obj['affiliate_user'])
        if 'affiliate_chat' in obj:
            obj['affiliate_chat'] = Chat.de_json(obj['affiliate_chat'])
        return cls(**obj)
    

class TransactionPartnerChat(TransactionPartner):
    """
    Describes a transaction with a chat.

    Telegram documentation: https://core.telegram.org/bots/api#transactionpartnerchat

    :param type: Type of the transaction partner, always “chat”
    :type type: :obj:`str`

    :param chat: Information about the chat
    :type chat: :class:`Chat`

    :param gift: Optional. The gift sent to the chat by the bot
    :type gift: :class:`Gift`

    :return: Instance of the class
    :rtype: :class:`TransactionPartnerChat`
    """

    def __init__(self, type, chat, gift=None, **kwargs):
        self.type: str = type
        self.chat: Chat = chat
        self.gift: Optional[Gift] = gift

    @classmethod
    def de_json(cls, json_string):
        if json_string is None: return None
        obj = cls.check_json(json_string)
        obj['chat'] = Chat.de_json(obj['chat'])
        if 'gift' in obj:
            obj['gift'] = Gift.de_json(obj['gift'])
        return cls(**obj)
    

class BusinessBotRights(JsonDeserializable):
    """
    Represents the rights of a business bot.

    Telegram documentation: https://core.telegram.org/bots/api#businessbotrights

    :param can_reply: Optional. True, if the bot can send and edit messages in the private chats that had incoming messages in the last 24 hours
    :type can_reply: :obj:`bool`

    :param can_read_messages: Optional. True, if the bot can mark incoming private messages as read
    :type can_read_messages: :obj:`bool`

    :param can_delete_outgoing_messages: Optional. True, if the bot can delete messages sent by the bot
    :type can_delete_outgoing_messages: :obj:`bool`

    :param can_delete_all_messages: Optional. True, if the bot can delete all private messages in managed chats
    :type can_delete_all_messages: :obj:`bool`

    :param can_edit_name: Optional. True, if the bot can edit the first and last name of the business account
    :type can_edit_name: :obj:`bool`

    :param can_edit_bio: Optional. True, if the bot can edit the bio of the business account
    :type can_edit_bio: :obj:`bool`

    :param can_edit_profile_photo: Optional. True, if the bot can edit the profile photo of the business account
    :type can_edit_profile_photo: :obj:`bool`

    :param can_edit_username: Optional. True, if the bot can edit the username of the business account
    :type can_edit_username: :obj:`bool`

    :param can_change_gift_settings: Optional. True, if the bot can change the privacy settings pertaining to gifts for the business account
    :type can_change_gift_settings: :obj:`bool`

    :param can_view_gifts_and_stars: Optional. True, if the bot can view gifts and the amount of Telegram Stars owned by the business account
    :type can_view_gifts_and_stars: :obj:`bool`

    :param can_convert_gifts_to_stars: Optional. True, if the bot can convert regular gifts owned by the business account to Telegram Stars
    :type can_convert_gifts_to_stars: :obj:`bool`

    :param can_transfer_and_upgrade_gifts: Optional. True, if the bot can transfer and upgrade gifts owned by the business account
    :type can_transfer_and_upgrade_gifts: :obj:`bool`

    :param can_transfer_stars: Optional. True, if the bot can transfer Telegram Stars received by the business account to its own account, or use them to upgrade and transfer gifts
    :type can_transfer_stars: :obj:`bool`

    :param can_manage_stories: Optional. True, if the bot can post, edit and delete stories on behalf of the business account
    :type can_manage_stories: :obj:`bool`

    :return: Instance of the class
    :rtype: :class:`BusinessBotRights` 
    """
    def __init__(self, can_reply=None, can_read_messages=None, can_delete_outgoing_messages=None, can_delete_all_messages=None,
                    can_edit_name=None, can_edit_bio=None, can_edit_profile_photo=None, can_edit_username=None, 
                    can_change_gift_settings=None, can_view_gifts_and_stars=None, can_convert_gifts_to_stars=None,
                    can_transfer_and_upgrade_gifts=None, can_transfer_stars=None, can_manage_stories=None, **kwargs):
        self.can_reply: Optional[bool] = can_reply
        self.can_read_messages: Optional[bool] = can_read_messages
        self.can_delete_outgoing_messages: Optional[bool] = can_delete_outgoing_messages
        self.can_delete_all_messages: Optional[bool] = can_delete_all_messages
        self.can_edit_name: Optional[bool] = can_edit_name
        self.can_edit_bio: Optional[bool] = can_edit_bio
        self.can_edit_profile_photo: Optional[bool] = can_edit_profile_photo
        self.can_edit_username: Optional[bool] = can_edit_username
        self.can_change_gift_settings: Optional[bool] = can_change_gift_settings
        self.can_view_gifts_and_stars: Optional[bool] = can_view_gifts_and_stars
        self.can_convert_gifts_to_stars: Optional[bool] = can_convert_gifts_to_stars
        self.can_transfer_and_upgrade_gifts: Optional[bool] = can_transfer_and_upgrade_gifts
        self.can_transfer_stars: Optional[bool] = can_transfer_stars
        self.can_manage_stories: Optional[bool] = can_manage_stories
    
    @classmethod
    def de_json(cls, json_string):
        if json_string is None: return None
        obj = cls.check_json(json_string)
        return cls(**obj)


class AcceptedGiftTypes(JsonDeserializable, JsonSerializable):
    """
    This object describes the types of gifts that can be gifted to a user or a chat.

    Telegram documentation: https://core.telegram.org/bots/api#acceptedgifttypes

    :param unlimited_gifts: True, if unlimited regular gifts are accepted
    :type unlimited_gifts: :obj:`bool`

    :param limited_gifts: True, if limited regular gifts are accepted
    :type limited_gifts: :obj:`bool`

    :param unique_gifts: True, if unique gifts or gifts that can be upgraded to unique for free are accepted
    :type unique_gifts: :obj:`bool`
    
    :param premium_subscription: True, if a Telegram Premium subscription is accepted
    :type premium_subscription: :obj:`bool`

    :return: Instance of the class
    :rtype: :class:`AcceptedGiftTypes`
    """
    def __init__(self, unlimited_gifts: bool, limited_gifts: bool,
                    unique_gifts: bool, premium_subscription: bool, **kwargs):
        self.unlimited_gifts: bool = unlimited_gifts
        self.limited_gifts: bool = limited_gifts
        self.unique_gifts: bool = unique_gifts
        self.premium_subscription: bool = premium_subscription
        
    def to_json(self):
        return json.dumps(self.to_dict())
    
    def to_dict(self):
        data = {
            'unlimited_gifts': self.unlimited_gifts,
            'limited_gifts': self.limited_gifts,
            'unique_gifts': self.unique_gifts,
            'premium_subscription': self.premium_subscription
        }
        return data
    @classmethod
    def de_json(cls, json_string):
        if json_string is None: return None
        obj = cls.check_json(json_string)
        return cls(**obj)


class StarAmount(JsonDeserializable):
    """
    Describes an amount of Telegram Stars.

    Telegram documentation: https://core.telegram.org/bots/api#staramount

    :param amount: Integer amount of Telegram Stars, rounded to 0; can be negative
    :type amount: :obj:`int`

    :param nanostar_amount: Optional. The number of 1/1000000000 shares of Telegram Stars; from -999999999 to 999999999; can be negative if and only if amount is non-positive
    :type nanostar_amount: :obj:`int`

    :return: Instance of the class
    :rtype: :class:`StarAmount`
    """
    def __init__(self, amount, nanostar_amount=None, **kwargs):
        self.amount: int = amount
        self.nanostar_amount: Optional[int] = nanostar_amount
    @classmethod
    def de_json(cls, json_string):
        if json_string is None: return None
        obj = cls.check_json(json_string)
        return cls(**obj)
    

class OwnedGift(JsonDeserializable, ABC):
    """
    This object describes a gift received and owned by a user or a chat. Currently, it can be one of
        OwnedGiftRegular
        OwnedGiftUnique

    Telegram documentation: https://core.telegram.org/bots/api#ownedgift
    """

    def __init__(self, type, **kwargs):
        self.type: str = type
        self.gift: Union[Gift, UniqueGift] = None
    
    
    @classmethod
    def de_json(cls, json_string):
        if json_string is None: return None
        obj = cls.check_json(json_string)
        if obj["type"] == "regular":
            return OwnedGiftRegular.de_json(obj)
        elif obj["type"] == "unique":
            return OwnedGiftUnique.de_json(obj)
        
class OwnedGiftRegular(OwnedGift):
    """
    This object describes a regular gift owned by a user or a chat.

    Telegram documentation: https://core.telegram.org/bots/api#ownedgiftregular

    :param type: Type of the gift, always “regular”
    :type type: :obj:`str`

    :param gift: Information about the regular gift
    :type gift: :class:`Gift`

    :param owned_gift_id: Optional. Unique identifier of the gift for the bot; for gifts received on behalf of business accounts only
    :type owned_gift_id: :obj:`str`

    :param sender_user: Optional. Sender of the gift if it is a known user
    :type sender_user: :class:`User`

    :param send_date: Date the gift was sent in Unix time
    :type send_date: :obj:`int`
    
    :param text: Optional. Text of the message that was added to the gift
    :type text: :obj:`str`

    :param entities: Optional. Special entities that appear in the text
    :type entities: :obj:`list` of :class:`MessageEntity`

    :param is_private: Optional. True, if the sender and gift text are shown only to the gift receiver; otherwise, everyone will be able to see them
    :type is_private: :obj:`bool`

    :param is_saved: Optional. True, if the gift is displayed on the account's profile page; for gifts received on behalf of business accounts only
    :type is_saved: :obj:`bool`

    :param can_be_upgraded: Optional. True, if the gift can be upgraded to a unique gift; for gifts received on behalf of business accounts only
    :type can_be_upgraded: :obj:`bool`

    :param was_refunded: Optional. True, if the gift was refunded and isn't available anymore
    :type was_refunded: :obj:`bool`

    :param convert_star_count: Optional. Number of Telegram Stars that can be claimed by the receiver instead of the gift; omitted if the gift cannot be converted to Telegram Stars
    :type convert_star_count: :obj:`int`

    :param prepaid_upgrade_star_count: Optional. Number of Telegram Stars that were paid by the sender for the ability to upgrade the gift
    :type prepaid_upgrade_star_count: :obj:`int`

    :return: Instance of the class
    :rtype: :class:`OwnedGiftRegular`
    """
    def __init__(self, type, gift, owned_gift_id=None, sender_user=None, send_date=None, text=None, entities=None,
                    is_private=None, is_saved=None, can_be_upgraded=None, was_refunded=None, convert_star_count=None,
                    prepaid_upgrade_star_count=None, **kwargs):
        super().__init__(type=type)
        self.gift: Gift = gift
        self.owned_gift_id: Optional[str] = owned_gift_id
        self.sender_user: Optional[User] = sender_user
        self.send_date: Optional[int] = send_date
        self.text: Optional[str] = text
        self.entities: Optional[List[MessageEntity]] = entities
        self.is_private: Optional[bool] = is_private
        self.is_saved: Optional[bool] = is_saved
        self.can_be_upgraded: Optional[bool] = can_be_upgraded
        self.was_refunded: Optional[bool] = was_refunded
        self.convert_star_count: Optional[int] = convert_star_count
        self.prepaid_upgrade_star_count: Optional[int] = prepaid_upgrade_star_count
    @classmethod
    def de_json(cls, json_string):
        if json_string is None: return None
        obj = cls.check_json(json_string)
        obj['gift'] = Gift.de_json(obj['gift'])
        if 'sender_user' in obj:
            obj['sender_user'] = User.de_json(obj['sender_user'])
        if 'entities' in obj:
            obj['entities'] = [MessageEntity.de_json(entity) for entity in obj['entities']]
        return cls(**obj)
    
class OwnedGiftUnique(OwnedGift):
    """
    This object describes a unique gift owned by a user or a chat.

    Telegram documentation: https://core.telegram.org/bots/api#ownedgiftunique

    :param type: Type of the gift, always “unique”
    :type type: :obj:`str`

    :param gift: Information about the unique gift
    :type gift: :class:`UniqueGift`

    :param owned_gift_id: Optional. Unique identifier of the received gift for the bot; for gifts received on behalf of business accounts only
    :type owned_gift_id: :obj:`str`

    :param sender_user: Optional. Sender of the gift if it is a known user
    :type sender_user: :class:`User`

    :param send_date: Date the gift was sent in Unix time
    :type send_date: :obj:`int`

    :param is_saved: Optional. True, if the gift is displayed on the account's profile page; for gifts received on behalf of business accounts only
    :type is_saved: :obj:`bool`

    :param can_be_transferred: Optional. True, if the gift can be transferred to another owner; for gifts received on behalf of business accounts only
    :type can_be_transferred: :obj:`bool`

    :param transfer_star_count: Optional. Number of Telegram Stars that must be paid to transfer the gift; omitted if the bot cannot transfer the gift
    :type transfer_star_count: :obj:`int`

    :param next_transfer_date: Optional. Point in time (Unix timestamp) when the gift can be transferred. If it is in the past, then the gift can be transferred now
    :type next_transfer_date: :obj:`int`

    :return: Instance of the class
    :rtype: :class:`OwnedGiftUnique`
    """
    def __init__(self, type, gift, owned_gift_id=None, sender_user=None, send_date=None, is_saved=None,
                    can_be_transferred=None, transfer_star_count=None, next_transfer_date=None, **kwargs):
        super().__init__(type=type)
        self.gift: UniqueGift = gift
        self.owned_gift_id: Optional[str] = owned_gift_id
        self.sender_user: Optional[User] = sender_user
        self.send_date: Optional[int] = send_date
        self.is_saved: Optional[bool] = is_saved
        self.can_be_transferred: Optional[bool] = can_be_transferred
        self.transfer_star_count: Optional[int] = transfer_star_count
        self.next_transfer_date: Optional[int] = next_transfer_date
    @classmethod
    def de_json(cls, json_string):
        if json_string is None: return None
        obj = cls.check_json(json_string)
        obj['gift'] = UniqueGift.de_json(obj['gift'])
        if 'sender_user' in obj:
            obj['sender_user'] = User.de_json(obj['sender_user'])
        return cls(**obj)
    

class OwnedGifts(JsonDeserializable):
    """
    Contains the list of gifts received and owned by a user or a chat.

    Telegram documentation: https://core.telegram.org/bots/api#ownedgifts

    :param total_count: The total number of gifts owned by the user or the chat
    :type total_count: :obj:`int`

    :param gifts: The list of gifts
    :type gifts: :obj:`list` of :class:`OwnedGift`

    :param next_offset: Optional. Offset for the next request. If empty, then there are no more results
    :type next_offset: :obj:`str`

    :return: Instance of the class
    :rtype: :class:`OwnedGifts`

    """
    def __init__(self, total_count, gifts, next_offset=None, **kwargs):
        self.total_count: int = total_count
        self.gifts: List[OwnedGift] = gifts
        self.next_offset: Optional[str] = next_offset
    @classmethod
    def de_json(cls, json_string):
        if json_string is None: return None
        obj = cls.check_json(json_string)
        obj['gifts'] = [OwnedGift.de_json(gift) for gift in obj['gifts']]
        return cls(**obj)



class UniqueGift(JsonDeserializable):
    """
    This object describes a unique gift that was upgraded from a regular gift.

    Telegram documentation: https://core.telegram.org/bots/api#uniquegift

    :param base_name: Human-readable name of the regular gift from which this unique gift was upgraded
    :type base_name: :obj:`str`

    :param name: Unique name of the gift. This name can be used in https://t.me/nft/... links and story areas
    :type name: :obj:`str`

    :param number: Unique number of the upgraded gift among gifts upgraded from the same regular gift
    :type number: :obj:`int`

    :param model: Model of the gift
    :type model: :class:`UniqueGiftModel`

    :param symbol: Symbol of the gift
    :type symbol: :class:`UniqueGiftSymbol`

    :param backdrop: Backdrop of the gift
    :type backdrop: :class:`UniqueGiftBackdrop`

    :return: Instance of the class
    :rtype: :class:`UniqueGift`
    """
    def __init__(self, base_name, name, number, model, symbol, backdrop, **kwargs):
        self.base_name: str = base_name
        self.name: str = name
        self.number: int = number
        self.model: UniqueGiftModel = model
        self.symbol: UniqueGiftSymbol = symbol
        self.backdrop: UniqueGiftBackdrop = backdrop
    @classmethod
    def de_json(cls, json_string):
        if json_string is None: return None
        obj = cls.check_json(json_string)
        obj['model'] = UniqueGiftModel.de_json(obj['model'])
        obj['symbol'] = UniqueGiftSymbol.de_json(obj['symbol'])
        obj['backdrop'] = UniqueGiftBackdrop.de_json(obj['backdrop'])
        return cls(**obj)
    
    
class UniqueGiftModel(JsonDeserializable):
    """
    This object describes the model of a unique gift.

    Telegram documentation: https://core.telegram.org/bots/api#uniquegiftmodel

    :param name: Name of the model
    :type name: :obj:`str`

    :param sticker: The sticker that represents the unique gift
    :type sticker: :class:`Sticker`

    :param rarity_per_mille: The number of unique gifts that receive this model for every 1000 gifts upgraded
    :type rarity_per_mille: :obj:`int`

    :return: Instance of the class
    :rtype: :class:`UniqueGiftModel`

    """
    def __init__(self, name, sticker, rarity_per_mille, **kwargs):
        self.name: str = name
        self.sticker: Sticker = sticker
        self.rarity_per_mille: int = rarity_per_mille
    @classmethod
    def de_json(cls, json_string):
        if json_string is None: return None
        obj = cls.check_json(json_string)
        obj['sticker'] = Sticker.de_json(obj['sticker'])
        return cls(**obj)
    
class UniqueGiftSymbol(JsonDeserializable):
    """
    This object describes the symbol shown on the pattern of a unique gift.

    Telegram documentation: https://core.telegram.org/bots/api#uniquegiftsymbol

    :param name: Name of the symbol
    :type name: :obj:`str`

    :param sticker: The sticker that represents the unique gift
    :type sticker: :class:`Sticker`

    :param rarity_per_mille: The number of unique gifts that receive this model for every 1000 gifts upgraded
    :type rarity_per_mille: :obj:`int`

    :return: Instance of the class
    :rtype: :class:`UniqueGiftSymbol`
    """

    def __init__(self, name, sticker, rarity_per_mille, **kwargs):
        self.name: str = name
        self.sticker: Sticker = sticker
        self.rarity_per_mille: int = rarity_per_mille
    @classmethod
    def de_json(cls, json_string):
        if json_string is None: return None
        obj = cls.check_json(json_string)
        obj['sticker'] = Sticker.de_json(obj['sticker'])
        return cls(**obj)
    
class UniqueGiftBackdropColors(JsonDeserializable):
    """
    This object describes the colors of the backdrop of a unique gift.

    Telegram documentation: https://core.telegram.org/bots/api#uniquegiftbackdropcolors

    :param center_color: The color in the center of the backdrop in RGB format
    :type center_color: :obj:`int`

    :param edge_color: The color on the edges of the backdrop in RGB format
    :type edge_color: :obj:`int`

    :param symbol_color: The color to be applied to the symbol in RGB format
    :type symbol_color: :obj:`int`

    :param text_color: The color for the text on the backdrop in RGB format
    :type text_color: :obj:`int`

    :return: Instance of the class
    :rtype: :class:`UniqueGiftBackdropColors`
    """
    def __init__(self, center_color, edge_color, symbol_color, text_color, **kwargs):
        self.center_color: int = center_color
        self.edge_color: int = edge_color
        self.symbol_color: int = symbol_color
        self.text_color: int = text_color
    @classmethod
    def de_json(cls, json_string):
        if json_string is None: return None
        obj = cls.check_json(json_string)
        return cls(**obj)
    
class UniqueGiftBackdrop(JsonDeserializable):
    """
    This object describes the backdrop of a unique gift.

    Telegram documentation: https://core.telegram.org/bots/api#uniquegiftbackdrop

    :param name: Name of the backdrop
    :type name: :obj:`str`

    :param colors: Colors of the backdrop
    :type colors: :class:`UniqueGiftBackdropColors`

    :param rarity_per_mille: The number of unique gifts that receive this backdrop for every 1000 gifts upgraded
    :type rarity_per_mille: :obj:`int`

    :return: Instance of the class
    :rtype: :class:`UniqueGiftBackdrop`
    """
    def __init__(self, name, colors, rarity_per_mille, **kwargs):
        self.name: str = name
        self.colors: UniqueGiftBackdropColors = colors
        self.rarity_per_mille: int = rarity_per_mille
    @classmethod
    def de_json(cls, json_string):
        if json_string is None: return None
        obj = cls.check_json(json_string)
        obj['colors'] = UniqueGiftBackdropColors.de_json(obj['colors'])
        return cls(**obj)

class InputStoryContent(JsonSerializable, ABC):
    """
    This object describes the content of a story to post. Currently, it can be one of
    InputStoryContentPhoto
    InputStoryContentVideo

    Telegram documentation: https://core.telegram.org/bots/api#inputstorycontent

    """
    def __init__(self, type: str, **kwargs):
        self.type: str = type


class InputStoryContentPhoto(InputStoryContent):
    """
    This object describes a photo to post as a story.

    Telegram documentation: https://core.telegram.org/bots/api#inputstorycontentphoto

    :param photo: The photo to post as a story. The photo must be of the size 1080x1920 and must not exceed 10 MB. The photo can't be reused and can only be uploaded as a new file, so you can pass “attach://<file_attach_name>” if the photo was uploaded using multipart/form-data under <file_attach_name>. More information on Sending Files
    :type photo: :class:`telebot.types.InputFile`

    :return: Instance of the class
    :rtype: :class:`InputStoryContentPhoto`
    """
    def __init__(self, photo: InputFile, **kwargs):
        super().__init__(type="photo")
        self.photo: InputFile = photo
        self._photo_name = service_utils.generate_random_token()
        self._photo_dic = "attach://{}".format(self._photo_name)
        
    def to_json(self):
        return json.dumps(self.to_dict())
    
    def to_dict(self):
        data = {
            'type': self.type,
            'photo': self._photo_dic
        }
        return data
    
    def convert_input_story(self):
        return self.to_json(), {self._photo_name: self.photo}
    

class InputStoryContentVideo(InputStoryContent):
    """
    This object describes a video to post as a story.

    Telegram documentation: https://core.telegram.org/bots/api#inputstorycontentvideo

    :param video: The video to post as a story. The video must be of the size 720x1280, streamable, encoded with H.265 codec, with key frames added each second in the MPEG4 format, and must not exceed 30 MB. The video can't be reused and can only be uploaded as a new file, so you can pass “attach://<file_attach_name>” if the video was uploaded using multipart/form-data under <file_attach_name>. More information on Sending Files
    :type video: :class:`telebot.types.InputFile`

    :param duration: Optional. Precise duration of the video in seconds; 0-60
    :type duration: :obj:`float`

    :param cover_frame_timestamp: Optional. Timestamp in seconds of the frame that will be used as the static cover for the story. Defaults to 0.0.
    :type cover_frame_timestamp: :obj:`float`

    :param is_animation: Optional. Pass True if the video has no sound
    :type is_animation: :obj:`bool`

    :return: Instance of the class
    :rtype: :class:`InputStoryContentVideo`
    """
    def __init__(self, video: InputFile, duration: Optional[float] = None, cover_frame_timestamp: Optional[float] = None,
                    is_animation: Optional[bool] = None, **kwargs):
        super().__init__(type="video")
        self.video: InputFile = video
        self._video_name = service_utils.generate_random_token()
        self._video_dic = "attach://{}".format(self._video_name)
        self.duration: Optional[float] = duration
        self.cover_frame_timestamp: Optional[float] = cover_frame_timestamp
        self.is_animation: Optional[bool] = is_animation
    def to_json(self):
        return json.dumps(self.to_dict())
    
    def to_dict(self):
        data = {
            'type': self.type,
            'video': self._video_dic
        }
        if self.duration is not None:
            data['duration'] = self.duration
        if self.cover_frame_timestamp is not None:
            data['cover_frame_timestamp'] = self.cover_frame_timestamp
        if self.is_animation is not None:
            data['is_animation'] = self.is_animation
        return data
    def convert_input_story(self):
        return self.to_json(), {self._video_name: self.video}
    

class StoryAreaPosition(JsonSerializable):
    """
    Describes the position of a clickable area within a story.

    Telegram documentation: https://core.telegram.org/bots/api#storyareaposition

    :param x_percentage: The abscissa of the area's center, as a percentage of the media width
    :type x_percentage: :obj:`float`

    :param y_percentage: The ordinate of the area's center, as a percentage of the media height
    :type y_percentage: :obj:`float`

    :param width_percentage: The width of the area's rectangle, as a percentage of the media width
    :type width_percentage: :obj:`float`

    :param height_percentage: The height of the area's rectangle, as a percentage of the media height
    :type height_percentage: :obj:`float`

    :param rotation_angle: The clockwise rotation angle of the rectangle, in degrees; 0-360
    :type rotation_angle: :obj:`float`

    :param corner_radius_percentage: The radius of the rectangle corner rounding, as a percentage of the media width
    :type corner_radius_percentage: :obj:`float`

    :return: Instance of the class
    :rtype: :class:`StoryAreaPosition`
    """
    def __init__(self, x_percentage: float, y_percentage: float, width_percentage: float,
                    height_percentage: float, rotation_angle: float, corner_radius_percentage: float, **kwargs):
        self.x_percentage: float = x_percentage
        self.y_percentage: float = y_percentage
        self.width_percentage: float = width_percentage
        self.height_percentage: float = height_percentage
        self.rotation_angle: float = rotation_angle
        self.corner_radius_percentage: float = corner_radius_percentage
    def to_json(self):
        return json.dumps(self.to_dict())
    def to_dict(self):
        data = {
            'x_percentage': self.x_percentage,
            'y_percentage': self.y_percentage,
            'width_percentage': self.width_percentage,
            'height_percentage': self.height_percentage,
            'rotation_angle': self.rotation_angle,
            'corner_radius_percentage': self.corner_radius_percentage
        }
        return data
    

class LocationAddress(JsonSerializable):
    """
    Describes the physical address of a location.

    Telegram documentation: https://core.telegram.org/bots/api#locationaddress

    :param country_code: The two-letter ISO 3166-1 alpha-2 country code of the country where the location is located
    :type country_code: :obj:`str`

    :param state: Optional. State of the location
    :type state: :obj:`str`

    :param city: Optional. City of the location
    :type city: :obj:`str`

    :param street: Optional. Street address of the location
    :type street: :obj:`str`

    :return: Instance of the class
    :rtype: :class:`LocationAddress`
    """
    def __init__(self, country_code: str, state: Optional[str] = None, city: Optional[str] = None,
                    street: Optional[str] = None, **kwargs):
        self.country_code: str = country_code
        self.state: Optional[str] = state
        self.city: Optional[str] = city
        self.street: Optional[str] = street
    def to_json(self):
        return json.dumps(self.to_dict())
    def to_dict(self):
        data = {
            'country_code': self.country_code
        }
        if self.state:
            data['state'] = self.state
        if self.city is not None:
            data['city'] = self.city
        if self.street is not None:
            data['street'] = self.street
        return data
    
class StoryAreaType(JsonSerializable, ABC):
    """
    Describes the type of a clickable area on a story. Currently, it can be one of
    StoryAreaTypeLocation
    StoryAreaTypeSuggestedReaction
    StoryAreaTypeLink
    StoryAreaTypeWeather
    StoryAreaTypeUniqueGift

    Telegram documentation: https://core.telegram.org/bots/api#storyarea

    :return: Instance of the class
    :rtype: :class:`StoryArea`
    """
    def __init__(self, type: str, **kwargs):
        self.type: str = type


class StoryAreaTypeLocation(StoryAreaType):
    """
    Describes a story area pointing to a location. Currently, a story can have up to 10 location areas.

    Telegram documentation: https://core.telegram.org/bots/api#storyareatypelocation

    :param type: Type of the area, always “location”
    :type type: :obj:`str`

    :param latitude: Location latitude in degrees
    :type latitude: :obj:`float`

    :param longitude: Location longitude in degrees
    :type longitude: :obj:`float`

    :param address: Optional, Location address
    :type address: :class:`LocationAddress`

    :return: Instance of the class
    :rtype: :class:`StoryAreaTypeLocation`
    """
    def __init__(self,latitude: float, longitude: float, address: LocationAddress = None, **kwargs):
        super().__init__(type="location")
        self.latitude: float = latitude
        self.longitude: float = longitude
        self.address: Optional[LocationAddress] = address
    def to_json(self):
        return json.dumps(self.to_dict())
    def to_dict(self):
        data = {
            'type': self.type,
            'latitude': self.latitude,
            'longitude': self.longitude,
        }
        if self.address is not None:
            data['address'] = self.address.to_dict()
        return data
    

class StoryAreaTypeSuggestedReaction(StoryAreaType):
    """
    Describes a story area pointing to a suggested reaction. Currently, a story can have up to 5 suggested reaction areas.

    Telegram documentation: https://core.telegram.org/bots/api#storyareatypesuggestedreaction

    :param type: Type of the area, always “suggested_reaction”
    :type type: :obj:`str`

    :param reaction_type: Type of the reaction
    :type reaction_type: :class:`ReactionType`

    :param is_dark: Optional. Pass True if the reaction area has a dark background
    :type is_dark: :obj:`bool`

    :param is_flipped: Optional. Pass True if reaction area corner is flipped
    :type is_flipped: :obj:`bool`

    :return: Instance of the class
    :rtype: :class:`StoryAreaTypeSuggestedReaction`
    """
    def __init__(self, reaction_type: ReactionType, is_dark: Optional[bool] = None, is_flipped: Optional[bool] = None, **kwargs):
        super().__init__(type="suggested_reaction")
        self.reaction_type: ReactionType = reaction_type
        self.is_dark: Optional[bool] = is_dark
        self.is_flipped: Optional[bool] = is_flipped
    def to_json(self):
        return json.dumps(self.to_dict())
    def to_dict(self):
        data = {
            'type': self.type,
            'reaction_type': self.reaction_type.to_dict()
        }
        if self.is_dark is not None:
            data['is_dark'] = self.is_dark
        if self.is_flipped is not None:
            data['is_flipped'] = self.is_flipped
        return data
    
class StoryAreaTypeLink(StoryAreaType):
    """
    Describes a story area pointing to an HTTP or tg:// link. Currently, a story can have up to 3 link areas.

    Telegram documentation: https://core.telegram.org/bots/api#storyareatypelink

    :param type: Type of the area, always “link”
    :type type: :obj:`str`

    :param url: HTTP or tg:// URL to be opened when the area is clicked
    :type url: :obj:`str`

    :return: Instance of the class
    :rtype: :class:`StoryAreaTypeLink`
    """
    def __init__(self, url: str, **kwargs):
        super().__init__(type="link")
        self.url: str = url
    def to_json(self):
        return json.dumps(self.to_dict())
    def to_dict(self):
        data = {
            'type': self.type,
            'url': self.url
        }
        return data
    
class StoryAreaTypeWeather(StoryAreaType):
    """
    Describes a story area containing weather information. Currently, a story can have up to 3 weather areas.

    Telegram documentation: https://core.telegram.org/bots/api#storyareatypeweather

    :param type: Type of the area, always “weather”
    :type type: :obj:`str`

    :param temperature: Temperature, in degree Celsius
    :type temperature: :obj:`float`

    :param emoji: Emoji representing the weather
    :type emoji: :obj:`str`

    :param background_color: A color of the area background in the ARGB format
    :type background_color: :obj:`int`

    :return: Instance of the class
    :rtype: :class:`StoryAreaTypeWeather`
    """
    def __init__(self, temperature: float, emoji: str, background_color: int, **kwargs):
        super().__init__(type="weather")
        self.temperature: float = temperature
        self.emoji: str = emoji
        self.background_color: int = background_color
    def to_json(self):
        return json.dumps(self.to_dict())
    def to_dict(self):
        data = {
            'type': self.type,
            'temperature': self.temperature,
            'emoji': self.emoji,
            'background_color': self.background_color
        }
        return data
    
class StoryAreaTypeUniqueGift(StoryAreaType):
    """
    Describes a story area pointing to a unique gift. Currently, a story can have at most 1 unique gift area.

    Telegram documentation: https://core.telegram.org/bots/api#storyareatypeuniquegift

    :param type: Type of the area, always “unique_gift”
    :type type: :obj:`str`

    :param name: Unique name of the gift
    :type name: :obj:`str`

    :return: Instance of the class
    :rtype: :class:`StoryAreaTypeUniqueGift`
    """
    def __init__(self, name: str, **kwargs):
        super().__init__(type="unique_gift")
        self.name: str = name
    def to_json(self):
        return json.dumps(self.to_dict())
    def to_dict(self):
        data = {
            'type': self.type,
            'name': self.name
        }

        return data
    

class StoryArea(JsonSerializable):
    """
    Describes a clickable area on a story media.

    Telegram documentation: https://core.telegram.org/bots/api#storyarea

    :param position: Position of the area
    :type position: :class:`StoryAreaPosition`

    :param type: Type of the area
    :type type: :class:`StoryAreaType`

    :return: Instance of the class
    :rtype: :class:`StoryArea`
    """
    def __init__(self, position: StoryAreaPosition, type: StoryAreaType, **kwargs):
        self.position: StoryAreaPosition = position
        self.type: StoryAreaType = type
    def to_json(self):
        return json.dumps(self.to_dict())
    def to_dict(self):
        data = {
            'position': self.position.to_dict(),
            'type': self.type.to_dict()
        }
        return data
    

class GiftInfo(JsonDeserializable):
    """
    This object describes a service message about a regular gift that was sent or received.

    Telegram documentation: https://core.telegram.org/bots/api#giftinfo

    :param gift: Information about the gift
    :type gift: :class:`Gift`

    :param owned_gift_id: Optional. Unique identifier of the received gift for the bot; only present for gifts received on behalf of business accounts
    :type owned_gift_id: :obj:`str`

    :param convert_star_count: Optional. Number of Telegram Stars that can be claimed by the receiver by converting the gift; omitted if conversion to Telegram Stars is impossible
    :type convert_star_count: :obj:`int`

    :param prepaid_upgrade_star_count: Optional. Number of Telegram Stars that were prepaid by the sender for the ability to upgrade the gift
    :type prepaid_upgrade_star_count: :obj:`int`

    :param can_be_upgraded: Optional. True, if the gift can be upgraded to a unique gift
    :type can_be_upgraded: :obj:`bool`

    :param text: Optional. Text of the message that was added to the gift
    :type text: :obj:`str`

    :param entities: Optional. Special entities that appear in the text
    :type entities: :obj:`list` of :class:`MessageEntity`

    :param is_private: Optional. True, if the sender and gift text are shown only to the gift receiver; otherwise, everyone will be able to see them
    :type is_private: :obj:`bool`

    :return: Instance of the class
    :rtype: :class:`GiftInfo`
    """
    def __init__(self, gift: Gift, owned_gift_id: Optional[str] = None, convert_star_count: Optional[int] = None,
                    prepaid_upgrade_star_count: Optional[int] = None, can_be_upgraded: Optional[bool] = None,
                    text: Optional[str] = None, entities: Optional[List[MessageEntity]] = None,
                    is_private: Optional[bool] = None, **kwargs):
        self.gift: Gift = gift
        self.owned_gift_id: Optional[str] = owned_gift_id
        self.convert_star_count: Optional[int] = convert_star_count
        self.prepaid_upgrade_star_count: Optional[int] = prepaid_upgrade_star_count
        self.can_be_upgraded: Optional[bool] = can_be_upgraded
        self.text: Optional[str] = text
        self.entities: Optional[List[MessageEntity]] = entities
        self.is_private: Optional[bool] = is_private
    @classmethod
    def de_json(cls, json_string):
        if json_string is None: return None
        obj = cls.check_json(json_string)
        obj['gift'] = Gift.de_json(obj['gift'])
        if 'entities' in obj:
            obj['entities'] = [MessageEntity.de_json(entity) for entity in obj['entities']]
        return cls(**obj)
    
class UniqueGiftInfo(JsonDeserializable):
    """
    This object describes a service message about a unique gift that was sent or received.

    Telegram documentation: https://core.telegram.org/bots/api#uniquegiftinfo

    :param gift: Information about the gift
    :type gift: :class:`UniqueGift`

    :param origin: Origin of the gift. Currently, either “upgrade” for gifts upgraded from regular gifts, “transfer” for gifts transferred from other users or channels,
        or “resale” for gifts bought from other users
    :type origin: :obj:`str`

    :param last_resale_star_count: Optional. For gifts bought from other users, the price paid for the gift
    :type last_resale_star_count: :obj:`int`

    :param owned_gift_id: Optional. Unique identifier of the received gift for the bot; only present for gifts received on behalf of business accounts
    :type owned_gift_id: :obj:`str`

    :param transfer_star_count: Optional. Number of Telegram Stars that must be paid to transfer the gift; omitted if the bot cannot transfer the gift
    :type transfer_star_count: :obj:`int`

    :param next_transfer_date: Optional. Point in time (Unix timestamp) when the gift can be transferred. If it is in the past, then the gift can be transferred now
    :type next_transfer_date: :obj:`int`

    :return: Instance of the class
    :rtype: :class:`UniqueGiftInfo`
    """
    def __init__(self, gift: UniqueGift, origin: str, owned_gift_id: Optional[str] = None,
                    transfer_star_count: Optional[int] = None, next_transfer_date: Optional[int] = None,
                    last_resale_star_count: Optional[int] = None, **kwargs):
        self.gift: UniqueGift = gift
        self.origin: str = origin
        self.last_resale_star_count: Optional[int] = last_resale_star_count
        self.owned_gift_id: Optional[str] = owned_gift_id
        self.transfer_star_count: Optional[int] = transfer_star_count
        self.next_transfer_date: Optional[int] = next_transfer_date

    @classmethod
    def de_json(cls, json_string):
        if json_string is None: return None
        obj = cls.check_json(json_string)
        obj['gift'] = UniqueGift.de_json(obj['gift'])
        return cls(**obj)
    

class PaidMessagePriceChanged(JsonDeserializable):
    """
    Describes a service message about a change in the price of paid messages within a chat.

    Telegram documentation: https://core.telegram.org/bots/api#paidmessagepricechanged

    :param paid_message_star_count: The new number of Telegram Stars that must be paid by non-administrator users of the supergroup chat for each sent message
    :type paid_message_star_count: :obj:`int`

    :return: Instance of the class
    :rtype: :class:`PaidMessagePriceChanged`
    """
    def __init__(self, paid_message_star_count: int, **kwargs):
        self.paid_message_star_count: int = paid_message_star_count
    @classmethod
    def de_json(cls, json_string):
        if json_string is None: return None
        obj = cls.check_json(json_string)
        return cls(**obj)
    

class InputProfilePhoto(JsonSerializable):
    """
    This object describes a profile photo to set. Currently, it can be one of
    InputProfilePhotoStatic
    InputProfilePhotoAnimated

    Telegram documentation: https://core.telegram.org/bots/api#inputprofilephoto

    :return: Instance of the class
    :rtype: :class:`InputProfilePhoto`
    """

class InputProfilePhotoStatic(InputProfilePhoto):
    """
    This object describes a static profile photo to set.
    
    Telegram documentation: https://core.telegram.org/bots/api#inputprofilephotostatic

    :param type: Type of the profile photo, must be static
    :type type: :obj:`str`

    :param photo: The static profile photo. Profile photos can't be reused and can only be uploaded as a new file, so you can pass “attach://<file_attach_name>” if the photo was uploaded using multipart/form-data under <file_attach_name>. More information on Sending Files
    :type photo: :obj:`str`

    :return: Instance of the class
    :rtype: :class:`InputProfilePhotoStatic`

    """
    def __init__(self, photo: InputFile, **kwargs):
        self.type: str = "static"
        self.photo: InputFile = photo

        self._photo_name = service_utils.generate_random_token()
        self._photo_dic = "attach://{}".format(self._photo_name)
    def to_json(self):
        return json.dumps(self.to_dict())
    
    def to_dict(self):
        data = {
            'type': self.type,
            'photo': self._photo_dic
        }
        return data
    def convert_input_profile_photo(self):
        return self.to_json(), {self._photo_name: self.photo}


class InputProfilePhotoAnimated(InputProfilePhoto):
    """
    This object describes an animated profile photo to set.

    Telegram documentation: https://core.telegram.org/bots/api#inputprofilephotoanimated

    :param type: Type of the profile photo, must be animated
    :type type: :obj:`str`

    :param animation: The animated profile photo. Profile photos can't be reused and can only be uploaded as a new file, so you can pass “attach://<file_attach_name>” if the photo was uploaded using multipart/form-data under <file_attach_name>. More information on Sending Files
    :type animation: :obj:`str`

    :param main_frame_timestamp: Optional. Timestamp in seconds of the frame that will be used as the static profile photo. Defaults to 0.0.
    :type main_frame_timestamp: :obj:`float`

    :return: Instance of the class
    :rtype: :class:`InputProfilePhotoAnimated`

    """
    def __init__(self, animation: InputFile, main_frame_timestamp: Optional[float] = None, **kwargs):
        self.type: str = "animated"
        self.animation: InputFile = animation
        self._animation_name = service_utils.generate_random_token()
        self._animation_dic = "attach://{}".format(self._animation_name)
        self.main_frame_timestamp: Optional[float] = main_frame_timestamp
    def to_json(self):
        return json.dumps(self.to_dict())
    def to_dict(self):
        data = {
            'type': self.type,
            'animation': self._animation_dic
        }
        if self.main_frame_timestamp is not None:
            data['main_frame_timestamp'] = self.main_frame_timestamp
        return data
    def convert_input_profile_photo(self):
        return self.to_json(), {self._animation_name: self.animation}


class ChecklistTask(JsonDeserializable):
    """
    Describes a task in a checklist.

    Telegram documentation: https://core.telegram.org/bots/api#checklisttask

    :param id: Unique identifier of the task
    :type id: :obj:`int`

    :param text: Text of the task
    :type text: :obj:`str`

    :param text_entities: Optional. Special entities that appear in the task text
    :type text_entities: :obj:`list` of :class:`MessageEntity`

    :param completed_by_user: Optional. User that completed the task; omitted if the task wasn't completed
    :type completed_by_user: :class:`User`

    :param completion_date: Optional. Point in time (Unix timestamp) when the task was completed; 0 if the task wasn't completed
    :type completion_date: :obj:`int`

    :return: Instance of the class
    :rtype: :class:`ChecklistTask`
    """
    def __init__(self, id: int, text: str, text_entities: Optional[List[MessageEntity]] = None,
                    completed_by_user: Optional[User] = None,
                    completion_date: Optional[int] = None, **kwargs):
        self.id: int = id
        self.text: str = text
        self.text_entities: Optional[List[MessageEntity]] = text_entities
        self.completed_by_user: Optional[User] = completed_by_user
        self.completion_date: Optional[int] = completion_date

    @classmethod
    def de_json(cls, json_string):
        if json_string is None: return None
        obj = cls.check_json(json_string)
        if 'text_entities' in obj:
            obj['text_entities'] = Message.parse_entities(obj['text_entities'])
        if 'completed_by_user' in obj:
            obj['completed_by_user'] = User.de_json(obj['completed_by_user'])
        return cls(**obj)
    
class Checklist(JsonDeserializable):
    """
    Describes a checklist.

    Telegram documentation: https://core.telegram.org/bots/api#checklist

    :param title: Title of the checklist
    :type title: :obj:`str`

    :param title_entities: Optional. Special entities that appear in the checklist title
    :type title_entities: :obj:`list` of :class:`MessageEntity`

    :param tasks: List of tasks in the checklist
    :type tasks: :obj:`list` of :class:`ChecklistTask`

    :param others_can_add_tasks: Optional. True, if users other than the creator of the list can add tasks to the list
    :type others_can_add_tasks: :obj:`bool`

    :param others_can_mark_tasks_as_done: Optional. True, if users other than the creator of the list can mark tasks as done or not done in the list
    :type others_can_mark_tasks_as_done: :obj:`bool`

    :return: Instance of the class
    :rtype: :class:`Checklist`
    """
    def __init__(self, title: str, tasks: List[ChecklistTask],
                    title_entities: Optional[List[MessageEntity]] = None,    
                    others_can_add_tasks: Optional[bool] = None,
                    others_can_mark_tasks_as_done: Optional[bool] = None, **kwargs):
        self.title: str = title
        self.tasks: List[ChecklistTask] = tasks
        self.title_entities: Optional[List[MessageEntity]] = title_entities
        self.others_can_add_tasks: Optional[bool] = others_can_add_tasks
        self.others_can_mark_tasks_as_done: Optional[bool] = others_can_mark_tasks_as_done

    @classmethod
    def de_json(cls, json_string):
        if json_string is None: return None
        obj = cls.check_json(json_string)
        if 'title_entities' in obj:
            obj['title_entities'] = Message.parse_entities(obj['title_entities'])
        obj['tasks'] = [ChecklistTask.de_json(task) for task in obj['tasks']]
        return cls(**obj)

class InputChecklistTask(JsonSerializable):
    """
    Describes a task to add to a checklist.

    Telegram documentation: https://core.telegram.org/bots/api#inputchecklisttask

    :param id: Unique identifier of the task; must be positive and unique among all task identifiers currently present in the checklist
    :type id: :obj:`int`

    :param text: Text of the task; 1-100 characters after entities parsing
    :type text: :obj:`str`

    :param parse_mode: Optional. Mode for parsing entities in the text. See formatting options for more details.
    :type parse_mode: :obj:`str`

    :param text_entities: Optional. List of special entities that appear in the text, which can be specified instead of parse_mode. Currently, only bold, italic, underline, strikethrough, spoiler, and custom_emoji entities are allowed.
    :type text_entities: :obj:`list` of :class:`MessageEntity`

    :return: Instance of the class
    :rtype: :class:`InputChecklistTask`
    """
    def __init__(self, id: int, text: str, parse_mode: Optional[str] = None,
                    text_entities: Optional[List[MessageEntity]] = None, **kwargs):
        self.id: int = id
        self.text: str = text
        self.parse_mode: Optional[str] = parse_mode
        self.text_entities: Optional[List[MessageEntity]] = text_entities
        
    def to_json(self):
        return json.dumps(self.to_dict())
    
    def to_dict(self):
        data = {
            'id': self.id,
            'text': self.text
        }
        if self.parse_mode:
            data['parse_mode'] = self.parse_mode
        if self.text_entities:
            data['text_entities'] = [entity.to_dict() for entity in self.text_entities]
        return data
    
class InputChecklist(JsonSerializable):
    """
    Describes a checklist to create.

    Telegram documentation: https://core.telegram.org/bots/api#inputchecklist

    :param title: Title of the checklist; 1-255 characters after entities parsing
    :type title: :obj:`str`

    :param parse_mode: Optional. Mode for parsing entities in the title. See formatting options for more details.
    :type parse_mode: :obj:`str`

    :param title_entities: Optional. List of special entities that appear in the title, which can be specified instead of parse_mode. Currently, only bold, italic, underline, strikethrough, spoiler, and custom_emoji entities are allowed.
    :type title_entities: :obj:`list` of :class:`MessageEntity`

    :param tasks: List of 1-30 tasks in the checklist
    :type tasks: :obj:`list` of :class:`InputChecklistTask`

    :param others_can_add_tasks: Optional. Pass True if other users can add tasks to the checklist
    :type others_can_add_tasks: :obj:`bool`

    :param others_can_mark_tasks_as_done: Optional. Pass True if other users can mark tasks as done or not done in the checklist
    :type others_can_mark_tasks_as_done: :obj:`bool`

    :return: Instance of the class
    :rtype: :class:`InputChecklist`
    """
    def __init__(self, title: str, tasks: List[InputChecklistTask], 
                    parse_mode: Optional[str] = None,
                    title_entities: Optional[List[MessageEntity]] = None,
                    others_can_add_tasks: Optional[bool] = None,
                    others_can_mark_tasks_as_done: Optional[bool] = None, **kwargs):
        self.title: str = title
        self.tasks: List[InputChecklistTask] = tasks
        self.parse_mode: Optional[str] = parse_mode
        self.title_entities: Optional[List[MessageEntity]] = title_entities
        self.others_can_add_tasks: Optional[bool] = others_can_add_tasks
        self.others_can_mark_tasks_as_done: Optional[bool] = others_can_mark_tasks_as_done

    def to_json(self):
        return json.dumps(self.to_dict())
    
    def to_dict(self):
        data = {
            'title': self.title,
            'tasks': [task.to_dict() for task in self.tasks]
        }
        if self.parse_mode:
            data['parse_mode'] = self.parse_mode
        if self.title_entities:
            data['title_entities'] = [entity.to_dict() for entity in self.title_entities]
        if self.others_can_add_tasks is not None:
            data['others_can_add_tasks'] = self.others_can_add_tasks
        if self.others_can_mark_tasks_as_done is not None:
            data['others_can_mark_tasks_as_done'] = self.others_can_mark_tasks_as_done


class ChecklistTasksDone(JsonDeserializable):
    """
    Describes a service message about checklist tasks marked as done or not done.

    Telegram documentation: https://core.telegram.org/bots/api#checklisttasksdone

    :param checklist_message: Optional. Message containing the checklist whose tasks were marked as done or not done. Note that the Message object in this field will not contain the reply_to_message field even if it itself is a reply.
    :type checklist_message: :class:`Message`

    :param marked_as_done_task_ids: Optional. Identifiers of the tasks that were marked as done
    :type marked_as_done_task_ids: :obj:`list` of :obj:`int

    :param marked_as_not_done_task_ids: Optional. Identifiers of the tasks that were marked as not done
    :type marked_as_not_done_task_ids: :obj:`list` of :obj:`int`

    :return: Instance of the class
    :rtype: :class:`ChecklistTasksDone`
    """
    def __init__(self, checklist_message: Optional[Message] = None,
                    marked_as_done_task_ids: Optional[List[int]] = None,
                    marked_as_not_done_task_ids: Optional[List[int]] = None, **kwargs):
        self.checklist_message: Optional[Message] = checklist_message
        self.marked_as_done_task_ids: Optional[List[int]] = marked_as_done_task_ids
        self.marked_as_not_done_task_ids: Optional[List[int]] = marked_as_not_done_task_ids

    @classmethod
    def de_json(cls, json_string):
        if json_string is None: return None
        obj = cls.check_json(json_string)
        if 'checklist_message' in obj:
            obj['checklist_message'] = Message.de_json(obj['checklist_message'])
        return cls(**obj)
    
    
class ChecklistTasksAdded(JsonDeserializable):
    """
    Describes a service message about tasks added to a checklist.

    Telegram documentation: https://core.telegram.org/bots/api#checklisttasksadded

    :param checklist_message: Optional. Message containing the checklist to which the tasks were added. Note that the Message object in this field will not contain the reply_to_message field even if it itself is a reply.
    :type checklist_message: :class:`Message`

    :param tasks: List of tasks added to the checklist
    :type tasks: :obj:`list` of :class:`ChecklistTask`

    :return: Instance of the class
    :rtype: :class:`ChecklistTasksAdded`
    """
    def __init__(self, tasks: List[ChecklistTask], checklist_message: Optional[Message] = None, **kwargs):
        self.checklist_message: Optional[Message] = checklist_message
        self.tasks: List[ChecklistTask] = tasks
    @classmethod
    def de_json(cls, json_string):
        if json_string is None: return None
        obj = cls.check_json(json_string)
        if 'checklist_message' in obj:
            obj['checklist_message'] = Message.de_json(obj['checklist_message'])
        obj['tasks'] = [ChecklistTask.de_json(task) for task in obj['tasks']]
        return cls(**obj)

class DirectMessagePriceChanged(JsonDeserializable):
    """
    Describes a service message about a change in the price of direct messages sent to a channel chat.

    Telegram documentation: https://core.telegram.org/bots/api#directmessagepricechanged

    :param are_direct_messages_enabled: True, if direct messages are enabled for the channel chat; false otherwise
    :type are_direct_messages_enabled: :obj:`bool`

    :param direct_message_star_count: Optional. The new number of Telegram Stars that must be paid by users for each direct message sent to the channel. Does not apply to users who have been exempted by administrators. Defaults to 0.
    :type direct_message_star_count: :obj:`int`

    :return: Instance of the class
    :rtype: :class:`DirectMessagePriceChanged`
    """
    def __init__(self, are_direct_messages_enabled: bool, direct_message_star_count: Optional[int] = None, **kwargs):
        self.are_direct_messages_enabled: bool = are_direct_messages_enabled
        self.direct_message_star_count: Optional[int] = direct_message_star_count

    @classmethod
    def de_json(cls, json_string):
        if json_string is None: return None
        obj = cls.check_json(json_string)
        return cls(**obj)
