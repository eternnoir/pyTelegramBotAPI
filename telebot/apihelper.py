# -*- coding: utf-8 -*-

import telebot
import requests

def get_me(token):
    api_url=telebot.API_URL
    method_url = r'getMe'
    request_url = api_url+'bot'+token+'/'+method_url
    req = requests.get(request_url)
    return req.json()

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
    return req.json()

def get_updates(token):
    api_url = telebot.API_URL
    method_url = r'getUpdates'
    request_url = api_url+'bot'+token+'/'+method_url
    req = requests.get(request_url)
    return req.json()
