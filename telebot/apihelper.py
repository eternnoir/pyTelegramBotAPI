# -*- coding: utf-8 -*-

import telebot
import requests


def send_message(token, chat_id, text, disable_web_page_preview=None, reply_to_message_id=None, reply_markup=None):
    api_url = telebot.API_URL
    method_url = r'sendMessage'
    request_url = api_url + 'bot' + token + '/' + method_url
    paras = 'chat_id=' + str(chat_id) + '&text=' + text
    if disable_web_page_preview:
        paras = paras + '&disable_web_page_preview=' + disable_web_page_preview
    if reply_to_message_id:
        paras = paras + '&reply_to_message_id=' + reply_to_message_id
    if reply_markup:
        paras = paras + '&reply_markup=' + reply_markup
    request_url = request_url +  '?' + paras
    req = requests.get(request_url)
    return req.json()
