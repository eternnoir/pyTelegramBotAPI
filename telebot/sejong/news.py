#-*- coding:utf-8 -*-
from bs4 import BeautifulSoup
import urllib

def getNews(command):

    if command == 'news_issue':
        try:
            r = urllib.urlopen('http://www.dailysecu.com/rss/S1N1.xml').read()
        except urllib.error.HTTPError as e:
            error_message = "Error %s HTTP." % e.code
            return error_message
    elif command == 'news_popular':
        try:
            r = urllib.urlopen('http://www.dailysecu.com/rss/clickTop.xml').read()
        except Exception as e:
            error_message = "Error %s HTTP." % e.code
            return error_message

    soup = BeautifulSoup(r, "html.parser")
    news = soup.find_all("item")

    newsIndex = {}
    newsList = {}

    i=1
    for element in news:
        title = element.find("title").get_text()
        description = element.find("description").get_text()
        link = element.find("link").get_text()
        newsIndex[i] = title
        newsList[title,'title']  = title                # title
        newsList[title,'description'] = description     # news description
        newsList[title,'link'] = link                   # link to news
        i=i+1

    return (newsIndex, newsList)
