# -*- coding:utf-8 -*-
import re
import requests
import json

URL_VOLUNTEERINTERNAL = "http://volunteer.sejong.ac.kr/vmsUsrOfenListInfo.do?mzcode=K00M050101"
URL_VOLUNTEEREXTERNAL = "http://volunteer.sejong.ac.kr/boardList.do?bcode=B0011"

def getVolunteerInternal():
	"""
		Crawl internal volunteer works from volunteer.sejong.ac.kr

		Requirement
		* None

		Return Values
		* result (Dictionary) : Dictionaries of volunteer works.
		  - result['title'] : Title
		  - result['date'] : Date (Ex: 11.23 ~ 11.23)
		  - result['day'] : Day of the week. (Ex: 목)
		  - result['time'] : Time (Ex: 15:00~16:00)
	"""
	result = []
	try:
		volunteer_info = {}
		data = requests.get(getVolunteerInternal).text
		data = data.replace("\n", "").replace("\r", "").replace("\t", "")
		volunteers = re.findall("<tr>.*?</tr>", data)
		del volunteers[0] # remove first row
		for i in volunteers:
			if "recruit_close.gif" in i: # if not available anymore
				continue
			vol_data = re.findall("<td>(.*?)</td>", i)
			volunteer_info['title'] = re.findall("<a.*?>(.*?)</a>", vol_data[2])[0]
			volunteer_info['date'] = vol_data[3]
			volunteer_info['day'] = vol_data[5]
			volunteer_info['time'] = vol_data[4]
			result.append(volunteer_info)
	except Exception, e:
		print "An error occured.", e
	return result

def getVolunteerExternal():
	"""
		Crawl external volunteer works from volunteer.sejong.ac.kr

		Requirement
		* None

		Return Values
		* result (Dictionary) : Dictionaries of volunteer works.
		  - result['title'] : Title
	"""
	result = []
	try:
		volunteer_info = {}
		data = requests.get(URL_VOLUNTEEREXTERNAL).text
		data = data.replace("\n", "").replace("\r", "").replace("\t", "")
		volunteers = re.findall("<tr>.*?</tr>", data)
		del volunteers[0] # remove first row
		for i in volunteers:
			if "recruit_close.gif" in i: # if not available anymore
				continue
			volunteer_info['title'] = re.findall("<a.*?>(.*?)</a>", i)[0]
			result.append(volunteer_info)
	except Exception, e:
		print "An error occured.", e
	return result
