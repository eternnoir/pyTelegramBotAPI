#-*- coding: utf-8 -*-
import sys, os

try:
    import telebot
except ImportError:
    sys.path.append(os.getcwd())
    import telebot

    from telebot.sejong import easteregg
    from telebot.sejong import volunteer
    from telebot.sejong import studyroom

print easteregg.crawlInsta()
print volunteer.getVolunteerInternal()

rs = studyroom.RoomStatus.instance()
rs.cache_exp_sec = 120

rs.update(2016, 10)
print rs.search(2016,10,12,10)
print rs.search(2016,10,12,11)

rs.update(2016, 10)
print rs.search(2016,10,12,12)
print rs.search(2016,10,12,13)

print rs.search(2016,10,12,range(10, 10+4))

print rs.mappingResult(rs.search(2016,10,12,range(10, 10+4)))
