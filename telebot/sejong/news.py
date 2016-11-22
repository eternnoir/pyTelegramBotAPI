#-*- coding:utf-8 -*-
from bs4 import BeautifulSoup
import urllib

def getNews(command):
    
    # source for scraping the news
    issue = urllib.urlopen('http://www.dailysecu.com/rss/S1N1.xml').read()
    popular = urllib.urlopen('http://www.dailysecu.com/rss/clickTop.xml').read()

    if command == news_issue:
        r = issue
    elif command == news_popular:
        r = popular

    soup = BeautifulSoup(r, "html.parser")
    news = soup.find_all("item")

    i=1
    for element in news:
        title = element.find("title").get_text()
        description = element.find("description").get_text()
        link = element.find("link").get_text()
        print i
        print "[",title,"]"         # title
        print description+"..."     # news description
        print "링크:",link           # link to news
        i=i+1
    