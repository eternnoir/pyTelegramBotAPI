# -*- coding: utf-8 -*-
import re
import requests
import json
import os
import glob
import urllib
import random
import time

# Variables for Youtube
DICT_IUYOUTUBE = {}

# Properties for instagram
URL_INSTAGRAM = "https://www.instagram.com/"
DIRECTORY = "./insta_images/"
TARGETID = "dlwlrma"

class Insta():
    def __init__(self,targetId):
        # super(Insta, self).__init__()
        self.dir = ""
        self.targetId = ""

        self.checkDirectory(DIRECTORY)
        self.setId(targetId)

        self.imgCache = self.getLocalImages()
        self.syncImages()

    def setId(self, targetId):
        self.targetId = targetId

    def checkDirectory(self, directory):
        self.dir = directory
        if not os.path.exists(directory):
            os.makedirs(directory)

    def crawlInsta(self):
        urls = []
        target = self.targetId
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

    def getImgbyUrl(self, url):
        try:
            fname = self.dir+url.split("/")[-1]
            urllib.urlretrieve(url, fname)
            print("Download new image!")
        except Exception as e:
            print "Error occured at getImgbyUrl", e
            return False
        return 

    def syncImages(self):
        newCache = self.crawlInsta()
        localImgs = self.getLocalImages()

        for imgurl in newCache:
            if imgurl.split("/")[-1] not in localImgs:
                if self.getImgbyUrl(imgurl) == False:
                    print("Failed to download the image")
                    return False
        self.imgCache = localImgs
        return True

    def getLocalImages(self):
        oldFiles = [os.path.basename(x) for x in glob.glob(self.dir+"*.*")]
        return oldFiles

    def getImage(self):
        """
            Get random images from Instagram

            Requirement
            * None

            Return Value
            * filename (String) : Random image filename.
        """
        random.seed = time.time()
        fname = random.choice(self.getLocalImages())
        return fname

def getIUYoutube(fname):
	"""
		Get random URL from playlists.
	"""
	result = {}
	random.seed = time.time()
	try:
		f = open(json_name, "rb")
		result = json.loads(f.read())['list']
		result = random.choice(result)
		f.close()
	except Exception as e:
		print e
		return False
	return result