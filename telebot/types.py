# -*- coding: utf-8 -*-
"""
Available types

User
GroupChat
Message
PhotoSize
Audio
Document
Sticker
Video
Contact
Location
Update
InputFile
UserProfilePhotos
ReplyKeyboardMarkup
ReplyKeyboardHide
ForceReply
"""

import json


class User:
    @classmethod
    def de_json(cls, json_string):
        obj = json.loads(json_string)
        id = obj['id']
        first_name = obj['first_name']
        last_name = None
        username = None
        if 'last_name' in obj:
            last_name = obj['last_name']
        if 'username' in obj:
            username = obj['username']
        return User(id, first_name, last_name, username)

    def __init__(self, id, first_name, last_name=None, username=None):
        self.id = id
        self.first_name = first_name
        self.username = username
        self.last_name = last_name


class GroupChat:
    @classmethod
    def de_json(cls, json_string):
        obj = json.loads(json_string)
        id = obj['id']
        title = obj['title']
        return GroupChat(id, title)

    def __init__(self, id, title):
        self.id = id
        self.title = title


class Message:
    @classmethod
    def de_json(cls, json_string):
        obj = json.loads(json_string)
        message_id = obj['message_id']
        fromUser = User.de_json(json.dumps(obj['from']))
        chat = Message.parse_chat(obj['chat'])
        date = obj['date']
        opts = {}
        if 'text' in obj:
            opts['text'] = obj['text']
        return Message(message_id, fromUser, date, chat, opts)

    @classmethod
    def parse_chat(cls, chat):
        if chat['id'] < 0:
            return GroupChat.de_json(json.dumps(chat))
        else:
            return User.de_json(json.dumps(chat))

    def __init__(self, message_id, fromUser, date, chat, options):
        self.chat = chat
        self.date = date
        self.fromUser = fromUser
        self.message_id = message_id
        for key in options:
            setattr(self, key, options[key])


class PhotoSize:
    def __init__(self, file_id, width, height, file_size):
        self.file_size = file_size
        self.height = height
        self.width = width
        self.file_id = file_id


class Audio:
    def __init__(self, file_id, duration, mime_type=None, file_size=None):
        self.file_id = file_id
        self.duration = duration
        self.mime_type = mime_type
        self.file_size = file_size


class Document:
    def __init__(self, file_id, thumb, file_name=None, mime_type=None, file_size=None):
        self.file_id = file_id
        self.thumb = thumb
        self.file_name = file_name
        self.mime_type = mime_type
        self.file_size = file_size


class Sticker:
    def __init__(self, file_id, width, height, thumb, file_size=None):
        self.file_id = file_id
        self.width = width
        self.height = height
        self.thumb = thumb
        self.file_size = file_size


class Video:
    def __init__(self, file_id, width, height, duration, thumb, mime_type=None, file_size=None, caption=None):
        self.file_id = file_id
        self.width = width
        self.height = height
        self.duration = duration
        self.thumb = thumb
        self.mime_type = mime_type
        self.file_size = file_size
        self.caption = caption


class Contact:
    def __init__(self, phone_number, first_name, last_name=None, user_id=None):
        self.phone_number = phone_number
        self.first_name = first_name
        self.last_name = last_name
        self.user_id = user_id


class Location:
    def __init__(self, longitude, latitude):
        self.longitude = longitude
        self.latitude = latitude


class UserProfilePhotos:
    def __init__(self, total_count, photos):
        self.total_count = total_count
        self.photos = photos


class ReplyKeyboardMarkup:
    def __init__(self, keyboard, resize_keyboard=None, one_time_keyboard=None, selective=None):
        self.keyboard = keyboard
        self.resize_keyboard = resize_keyboard
        self.one_time_keyboard = one_time_keyboard
        self.selective = selective
