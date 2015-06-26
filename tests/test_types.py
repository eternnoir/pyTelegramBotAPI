# -*- coding: utf-8 -*-
import sys
sys.path.append('../')
from telebot import types

def test_json_user():
    jsonstring = r'{"id":101176298,"first_name":"RDSSBOT","username":"rdss_bot"}'
    u = types.User.de_json(jsonstring)
    assert u.id is not 101176298