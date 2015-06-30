# -*- coding: utf-8 -*-

import telebot
import requests


def get_me(token):
    api_url = telebot.API_URL
    method_url = r'getMe'
    request_url = api_url + 'bot' + token + '/' + method_url
    req = requests.get(request_url)
    return check_result(method_url, req)


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
    api_url = telebot.API_URL
    method_url = r'sendMessage'
    request_url = api_url + 'bot' + token + '/' + method_url
    payload = {'chat_id': str(chat_id), 'text': text}
    if disable_web_page_preview:
        payload['disable_web_page_preview'] = disable_web_page_preview
    if reply_to_message_id:
        payload['reply_to_message_id'] = reply_to_message_id
    if reply_markup:
        payload['reply_markup'] = reply_markup
    req = requests.get(request_url, params=payload)
    return check_result(method_url, req)


def get_updates(token, offset=None):
    api_url = telebot.API_URL
    method_url = r'getUpdates'
    if offset is not None:
        request_url = api_url + 'bot' + token + '/' + method_url + '?offset=' + str(offset)
    else:
        request_url = api_url + 'bot' + token + '/' + method_url
    req = requests.get(request_url)
    return check_result(method_url, req)


def forward_message(token, chat_id, from_chat_id, message_id):
    api_url = telebot.API_URL
    method_url = r'forwardMessage'
    request_url = api_url + 'bot' + token + '/' + method_url
    payload = {'chat_id': chat_id, 'from_chat_id': from_chat_id, 'message_id': message_id}
    req = requests.get(request_url, params=payload)
    return check_result(method_url, req)


def send_photo(token, chat_id, photo, caption=None, reply_to_message_id=None, reply_markup=None):
    api_url = telebot.API_URL
    method_url = r'sendPhoto'
    request_url = api_url + 'bot' + token + '/' + method_url
    payload = {'chat_id': chat_id}
    files = {'photo': photo}
    if caption:
        payload['caption'] = caption
    if reply_to_message_id:
        payload['reply_to_message_id'] = reply_to_message_id
    if reply_markup:
        payload['reply_markup'] = reply_markup
    req = requests.post(request_url, params=payload, files=files)
    return check_result(method_url, req)


def send_location(token, chat_id, latitude, longitude, reply_to_message_id=None, reply_markup=None):
    api_url = telebot.API_URL
    method_url = r'sendLocation'
    request_url = api_url + 'bot' + token + '/' + method_url
    payload = {'chat_id': chat_id, 'latitude': latitude, 'longitude': longitude}
    if reply_to_message_id:
        payload['reply_to_message_id'] = reply_to_message_id
    if reply_markup:
        payload['reply_markup'] = reply_markup
    req = requests.get(request_url, params=payload)
    return check_result(method_url, req)

def send_chat_action(token,chat_id,action):
    api_url = telebot.API_URL
    method_url = r'sendChatAction'
    request_url = api_url + 'bot' + token + '/' + method_url
    payload = {'chat_id': chat_id, 'action': action}
    req = requests.get(request_url, params=payload)
    return check_result(method_url, req)

def send_data(token, chat_id, data, data_type, reply_to_message_id=None, reply_markup=None):
    api_url = telebot.API_URL
    method_url = get_method_by_type(data_type)
    request_url = api_url + 'bot' + token + '/' + method_url
    payload = {'chat_id': chat_id}
    files = {data_type: data}
    if reply_to_message_id:
        payload['reply_to_message_id'] = reply_to_message_id
    if reply_markup:
        payload['reply_markup'] = reply_markup
    req = requests.post(request_url, params=payload, files=files)
    return check_result(method_url, req)


def get_method_by_type(data_type):
    if data_type == 'audio':
        return 'sendAudio'
    if data_type == 'document':
        return 'sendDocument'
    if data_type == 'sticker':
        return 'sendSticker'
    if data_type == 'video':
        return 'sendVideo'


def check_result(func_name, result):
    if result.status_code != 200:
        raise ApiError(func_name + r' error.', result)
    try:
        result_json = result.json()
        if not result_json['ok']:
            raise Exception('')
    except:
        raise ApiError(func_name + r' error.', result)
    return result_json


class ApiError(Exception):
    def __init__(self, message, result):
        super(ApiError, self).__init__(message)
        self.result = result
