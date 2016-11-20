# -*- coding:utf-8 -*-
import re
import requests
import json

URL_INSTAGRAM = "https://www.instagram.com/"

def crawlInsta(target_id="dlwlrma"):
	"""
		Crawl images from Instagram

		Requirement
		* target_id (String) : User's id of Instagram. (Default : dlwlrma)

		Return Value
		* urls (List) : list of urls.
	"""
	urls = []
	target = target_id
	max_id = ""
	while 1:
		try:
			url = URL_INSTAGRAM+target+"/media/?max_id="+max_id+""
			result = requests.get(url).text
			insta = json.loads(result)
			articles = insta['items']
			for article in articles:
				if article['type'] == "image":
					url = article['images']['standard_resolution']['url'].replace("s640x640","s1080x1080")
					url = url.split("?")[0]
					urls.append(url)
				max_id = article['id']
			if len(articles) == 0:
				break
		except Exception as e:
			print "An error occured, ", e
			break
	return urls

