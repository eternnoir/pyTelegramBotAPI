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

preset = None
for i in range(10,14):
    if preset is not None: 
        preset = preset.intersection( set(rs.search(2016,10,12,i)) )
    else:
        preset = set(rs.search(2016,10,12,i))
print preset