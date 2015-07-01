# -*- coding: utf-8 -*-

import requests

import telebot
from telebot import types


def _make_request(token, method_name, method='get', params=None, files=None):
    request_url = telebot.API_URL + 'bot' + token + '/' + method_name
    result = requests.request(method, request_url, params=params, files=files)
    if result.status_code != 200:
        raise ApiException(method_name + r' error.', result)
    try:
        result_json = result.json()
        if not result_json['ok']:
            raise ApiException(method_name, ' failed, result=' + result_json)
    except:
        raise ApiException(method_name + r' error.', result)
    return result_json['result']


def get_me(token):
    method_url = 'getMe'
    return _make_request(token, method_url)


def send_message(token, chat_id, text, disable_web_page_preview=None, reply_to_message_id=None, reply_markup=None):
    """
    Use this method to send text messages. On success, the sent Message is returned.
    :param token:
    :param chat_id:
    :param text:
    :param disable_web_page_preview:
    :param reply_to_message_id:
    :param reply_markup:
    :return:
    """
    method_url = r'sendMessage'
    payload = {'chat_id': str(chat_id), 'text': text}
    if disable_web_page_preview:
        payload['disable_web_page_preview'] = disable_web_page_preview
    if reply_to_message_id:
        payload['reply_to_message_id'] = reply_to_message_id
    if reply_markup:
        payload['reply_markup'] = convert_markup(reply_markup)
    return _make_request(token, method_url, params=payload)


def get_updates(token, offset=None):
    method_url = r'getUpdates'
    if offset is not None:
        return _make_request(token, method_url, params={'offset': offset})
    else:
        return _make_request(token, method_url)


def get_user_profile_photos(token, user_id, offset=None, limit=None):
    method_url = r'getUserProfilePhotos'
    payload = {'user_id': user_id}
    if offset:
        payload['offset'] = offset
    if limit:
        payload['limit'] = limit
    return _make_request(token, method_url, params=payload)


def forward_message(token, chat_id, from_chat_id, message_id):
    method_url = r'forwardMessage'
    payload = {'chat_id': chat_id, 'from_chat_id': from_chat_id, 'message_id': message_id}
    return _make_request(token, method_url, params=payload)


def send_photo(token, chat_id, photo, caption=None, reply_to_message_id=None, reply_markup=None):
    method_url = r'sendPhoto'
    payload = {'chat_id': chat_id}
    files = {'photo': photo}
    if caption:
        payload['caption'] = caption
    if reply_to_message_id:
        payload['reply_to_message_id'] = reply_to_message_id
    if reply_markup:
        payload['reply_markup'] = convert_markup(reply_markup)
    return _make_request(token, method_url, params=payload, files=files, method='post')


def send_location(token, chat_id, latitude, longitude, reply_to_message_id=None, reply_markup=None):
    method_url = r'sendLocation'
    payload = {'chat_id': chat_id, 'latitude': latitude, 'longitude': longitude}
    if reply_to_message_id:
        payload['reply_to_message_id'] = reply_to_message_id
    if reply_markup:
        payload['reply_markup'] = convert_markup(reply_markup)
    return _make_request(token, method_url, params=payload)


def send_chat_action(token, chat_id, action):
    method_url = r'sendChatAction'
    payload = {'chat_id': chat_id, 'action': action}
    return _make_request(token, method_url, params=payload)


def send_data(token, chat_id, data, data_type, reply_to_message_id=None, reply_markup=None):
    method_url = get_method_by_type(data_type)
    payload = {'chat_id': chat_id}
    files = {data_type: data}
    if reply_to_message_id:
        payload['reply_to_message_id'] = reply_to_message_id
    if reply_markup:
        payload['reply_markup'] = convert_markup(reply_markup)
    return _make_request(token, method_url, params=payload, files=files, method='post')


def get_method_by_type(data_type):
    if data_type == 'audio':
        return 'sendAudio'
    if data_type == 'document':
        return 'sendDocument'
    if data_type == 'sticker':
        return 'sendSticker'
    if data_type == 'video':
        return 'sendVideo'


def convert_markup(markup):
    if isinstance(markup, types.JsonSerializable):
        return markup.to_json()
    return markup


class ApiException(Exception):
    def __init__(self, message, result):
        super(ApiException, self).__init__(message)
        self.result = result
