import datetime

def time_now():
    return datetime.datetime.now()

def time_elap_now(time):
    return time-time_now()

def to_sec(time):
    return time.total_seconds()