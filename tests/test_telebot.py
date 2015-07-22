# -*- coding: utf-8 -*-
import sys
import time

sys.path.append('../')
from telebot import types
from telebot import apihelper
import telebot
import os

TOKEN = os.environ['TOKEN']
CHAT_ID = os.environ['CHAT_ID']


def test_message_listener():
    msg_list = []
    for x in range(100):
        msg_list.append(create_text_message('Message ' + str(x)))

    def listener(messages):
        assert len(messages) == 100

    tb = telebot.TeleBot('')
    tb.set_update_listener(listener)


def test_message_handler():
    tb = telebot.TeleBot('')
    msg = create_text_message('/help')

    @tb.message_handler(commands=['help', 'start'])
    def command_handler(message):
        message.text = 'got'

    tb.process_new_messages([msg])
    time.sleep(1)
    assert msg.text == 'got'


def test_message_handler_reg():
    bot = telebot.TeleBot('')
    msg = create_text_message(r'https://web.telegram.org/')

    @bot.message_handler(regexp='((https?):((//)|(\\\\))+([\w\d:#@%/;$()~_?\+-=\\\.&](#!)?)*)')
    def command_url(message):
        msg.text = 'got'

    bot.process_new_messages([msg])
    time.sleep(1)
    assert msg.text == 'got'


def test_message_handler_reg_fail():
    bot = telebot.TeleBot('')
    msg = create_text_message(r'web.telegram.org/')

    @bot.message_handler(regexp='((https?):((//)|(\\\\))+([\w\d:#@%/;$()~_?\+-=\\\.&](#!)?)*)')
    def command_url(message):
        msg.text = 'got'

    bot.process_new_messages([msg])
    time.sleep(1)
    assert not msg.text == 'got'


def test_send_file_by_id():
    file_id = 'BQADBQADjAIAAsYifgbvqwq1he9REAI'
    tb = telebot.TeleBot(TOKEN)
    ret_msg = tb.send_document(CHAT_ID, file_id)
    assert ret_msg.message_id


def test_send_file():
    file_data = open('../examples/detailed_example/kitten.jpg', 'rb')
    tb = telebot.TeleBot(TOKEN)
    ret_msg = tb.send_document(CHAT_ID, file_data)
    assert ret_msg.message_id


def test_send_photo_by_id():
    photo_id = 'AgADBQADTKgxG8YifgbcWQAB7Da9yYIx1rEyAAT-HYJ3CrJEqdA2AQABAg'
    tb = telebot.TeleBot(TOKEN)
    ret_msg = tb.send_photo(CHAT_ID, photo_id)
    assert ret_msg.message_id


def test_send_photo():
    file_data = open('../examples/detailed_example/kitten.jpg', 'rb')
    tb = telebot.TeleBot(TOKEN)
    ret_msg = tb.send_photo(CHAT_ID, file_data)
    assert ret_msg.message_id


def test_send_message():
    text = 'CI Test Message'
    tb = telebot.TeleBot(TOKEN)
    ret_msg = tb.send_message(CHAT_ID, text)
    assert ret_msg.message_id


def test_forward_message():
    text = 'CI forward_message Test Message'
    tb = telebot.TeleBot(TOKEN)
    msg = tb.send_message(CHAT_ID, text)
    ret_msg = tb.forward_message(CHAT_ID, CHAT_ID, msg.message_id)
    assert ret_msg.forward_from


def test_reply_to():
    text = 'CI reply_to Test Message'
    tb = telebot.TeleBot(TOKEN)
    msg = tb.send_message(CHAT_ID, text)
    ret_msg = tb.reply_to(msg, text + ' REPLY')
    assert ret_msg.reply_to_message.message_id == msg.message_id


def test_send_location():
    tb = telebot.TeleBot(TOKEN)
    lat = 26.3875591
    lon = -161.2901042
    ret_msg = tb.send_location(CHAT_ID, lat, lon)
    assert int(ret_msg.location.longitude) == int(lon)
    assert int(ret_msg.location.latitude) == int(lat)


def create_text_message(text):
    params = {'text': text}
    return types.Message(1, None, None, 1, 'text', params)


def test_is_string_unicode():
    s1 = u'string'
    assert apihelper.is_string(s1)


def test_is_string_string():
    s1 = 'string'
    assert apihelper.is_string(s1)


def test_not_string():
    i1 = 10
    assert not apihelper.is_string(i1)
