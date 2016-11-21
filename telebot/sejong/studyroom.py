#-*- coding: utf-8 -*-
import datetime
import utils
import urllib2

DEFAULT_CACHE_EXP_SEC = 30

ROOM_MAP = {
    1 : u'07 스터디룸(7층)_당일예약',
    2 : u'08 스터디룸(7층)',
    3 : u'09 스터디룸(7층)',
    4 : u'11 스터디룸(7층)',
    5 : u'12 스터디룸(7층)',
    8 : u'교육실(2층)',
    9 : u'10 스터디룸(7층)',
    10 : u'02 스터디룸(7층)',
    11 : u'01 스터디룸(7층)',
    12 : u'03 스터디룸(7층)',
    13 : u'04 스터디룸(7층)',
    14 : u'05 스터디룸(7층)',
    15 : u'06 스터디룸(7층)',
    16 : u'13 스터디룸(7층)',
    17 : u'25 스터디룸(지상1층)',
    18 : u'26 스터디룸(지상1층)',
    19 : u'27 스터디룸(지상1층)',
    20 : u'28 스터디룸(지상1층)',
    21 : u'29 스터디룸(지상1층)',
    22 : u'30 스터디룸(지상1층)',
    23 : u'14 스터디룸(4층)',
    24 : u'15 스터디룸(4층)',
    25 : u'16 스터디룸(4층)',
    26 : u'17 스터디룸(4층)',
    27 : u'18 스터디룸(4층)',
    28 : u'19 스터디룸(4층)',
    29 : u'20 스터디룸(4층)',
    30 : u'21 스터디룸(4층)',
    31 : u'22 스터디룸(4층)',
    32 : u'23 스터디룸(4층)',
    33 : u'24 스터디룸(4층)_당일예약',
    34 : u'진관홀 스터디룸1',
    35 : u'진관홀 스터디룸2',
    36 : u'진관홀 스터디룸3',
    37 : u'화상 회의실(7층)',
    #38 : u'무한상상공간_오픈박스(7층)',
    #39 : u'무한상상공간_미팅룸1(7층)',
    #40 : u'무한상상공간_메이커룸(7층)',
    #41 : u'무한상상공간_미팅룸2(7층)',
    #42 : u'무한상상공간_미팅룸3(7층)',
    #43 : u'무한상상공간_미팅룸4(7층)',
    #44 : u'무한상상공간_미팅룸5(7층)',
    #45 : u'무한상상공간_미팅룸6(7층)',
    #46 : u'무한상상공간_미팅룸7(7층)',
    }

TODAY = u'당일예약'

ROOM_INFO_URL_FMT = 'http://library.sejong.ac.kr/studyroom/BookingTable.axa?year=%d&month=%d&roomId=%d&mode&_=Name'

class SingletonInstane:
  __instance = None

  @classmethod
  def __getInstance(cls):
    return cls.__instance

  @classmethod
  def instance(cls, *args, **kargs):
    cls.__instance = cls(*args, **kargs)
    cls.instance = cls.__getInstance
    return cls.__instance


class RoomStatus(SingletonInstane):

    def __init__(self):
        self.cache = dict()
        self.cache_exp_sec = DEFAULT_CACHE_EXP_SEC
    def GC(self):
        for k in self.cache:
            if utils.to_sec(
                utils.time_elap_now( 
                    self.cache[k]['time']
                    )
                ) >= self.cache_exp_sec: # miss!
                del self.cache[k]

    def __update(self, year, month):
        ret_dict = dict()
        # self.cache[(year, month)]
        for k in ROOM_MAP:
            try:
                req = urllib2.urlopen(ROOM_INFO_URL_FMT % (year, month-1, k))
            except urllib2.URLError:
                continue
            month_dict = dict()

            d = req.read().decode("utf-8").replace("\t", "").replace("  ","")

            avtime = []
            th = d.split("<th")[3:]
            for t in th:
                avtime.append(int( t.split(">")[1].split("<")[0]))
    
            month_dict['avtime'] = avtime

            for low in d.split("<tr>")[3:]:

                date = low.split("<td")[1].split("<")[0].split(">")[-1]
                date = int(date.split(" ")[0])

                month_dict[date] = list()

                for col in low.split("<td")[2:]:
                    try:
                        month_dict[date].append(int(col.split("<")[0].split(">")[-1]))
                    except:
                        pass
            ret_dict[k] = month_dict
        if len(ret_dict) > 0:
            ret_dict['time'] = utils.time_now()
        else:
            ret_dict = None
        return ret_dict

    def update(self, year, month):

        self.GC()

        if not (year, month) in self.cache:
            tmp = self.__update(year, month)
            if tmp is not None:
                self.cache[(year, month)] = tmp 
            

    def __search(self, year, month, date, time):
        
        rst = []

        for room in self.cache[(year, month)]:
            if room == 'time': continue
            if (time in self.cache[(year, month)][room][date] ) : rst.append(room)

        return rst
    
    def search(self, year, month, date, time_range):

        if type(time_range) is int : time_range = [time_range]

        self.update(year, month)

        preset = None
        for i in time_range:
            if preset is not None: 
                preset = preset.intersection( set(self.__search(year,month,date,i)) )
            else:
                preset = set(self.__search(year,month,date,i))
        return list(preset)

    def mappingResult(self, room_list):
        rst = []
        for room_no in room_list:
            rst.append(ROOM_MAP[room_no])

        return rst

if __name__ == "__main__":
    rs = RoomStatus.instance()

    rs.update(2016, 10)
    print rs.search(2016,10,12,10)
    print rs.search(2016,10,12,11)
    rs.update(2016, 10)
    print rs.search(2016,10,12,12)
    print rs.search(2016,10,12,13)