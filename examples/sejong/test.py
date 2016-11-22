# -*- coding: utf-8 -*-
import sys
import os

try:
    import telebot
except ImportError:
    sys.path.append(os.getcwd())
    import telebot

    from telebot.sejong import easteregg
    from telebot.sejong import volunteer
    from telebot.sejong import cvesearch


print easteregg.crawlInsta()
print volunteer.getVolunteerInternal()

cs = CVESearch()
result = cs.search_by_number('2016-1111')
print result
