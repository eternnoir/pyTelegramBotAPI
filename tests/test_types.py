# -*- coding: utf-8 -*-
import sys

sys.path.append('../')
from telebot import types


def test_json_user():
    jsonstring = r'{"id":101176298,"first_name":"RDSSBOT","username":"rdss_bot"}'
    u = types.User.de_json(jsonstring)
    assert u.id == 101176298


def test_json_message():
    jsonstring = r'{"message_id":1,"from":{"id":108929734,"first_name":"Frank","last_name":"Wang","username":"eternnoir"},"chat":{"id":108929734,"first_name":"Frank","last_name":"Wang","username":"eternnoir"},"date":1435296025,"text":"HIHI"}'
    msg = types.Message.de_json(jsonstring)
    assert msg.text == 'HIHI'

def test_json_message_group():
    json_string = r'{"message_id":10,"from":{"id":12345,"first_name":"g","last_name":"G","username":"GG"},"chat":{"id":-866,"title":"\u4ea4"},"date":1435303157,"text":"HIHI"}'
    msg = types.Message.de_json(json_string)
    assert msg.text == 'HIHI'
    assert len(msg.chat.title) != 0
    assert msg.fromUser.username == 'GG'

def test_json_GroupChat():
    json_string = r'{"id":8926,"title":"\u5c4e\u4f2f\u98ef\u98ef\u4e4b\u4ea4"}'
    gc = types.GroupChat.de_json(json_string)
    assert gc.id == 8926