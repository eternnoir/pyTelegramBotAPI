# -*- coding: utf-8 -*-
import sys
import os

try:
    import telebot
except ImportError:
    sys.path.append(os.getcwd())
    sys.path.append("../../")
    import telebot

    from telebot.sejong import easteregg
    from telebot.sejong import volunteer
    from telebot.sejong import cvesearch
    from telebot.sejong import studyroom
    from telebot.sejong import news

# Easter EGG
#iu_insta = easteregg.Insta("dlwlrma")
#print iu_insta.getImage()


# Volunteer
print volunteer.getVolunteerInternal()
print volunteer.getVolunteerExternal()

# cve search
cs = CVESearch()
result = cs.search_by_number('2016-1111')
print result

#SecuNews
data = news.getNews('news_issue')
newsIndex = data[0]
newsList = data[1]

for index in newsIndex:
    title = newsIndex[index]
    print '<',index,'>'
    print '[',newsList[title,'title'],']'
    print newsList[title,'description'],'...'
    print '링크:',newsList[title,'link']
    print ""


# Study room search
rs = studyroom.RoomStatus.instance()
rs.cache_exp_sec = 120

# usage 1
rs.update(2016, 10)
print rs.search(2016,10,12,10)
print rs.search(2016,10,12,11)

# cache test
rs.update(2016, 10)
print rs.search(2016,10,12,12)
print rs.search(2016,10,12,13)

# usage 2
print rs.search(2016,10,12,range(10, 10+4))

# usage 3
print rs.mappingResult(rs.search(2016,10,12,range(10, 10+4)))
