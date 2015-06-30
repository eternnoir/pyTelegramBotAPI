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
        from_user = User.de_json(json.dumps(obj['from']))
        chat = Message.parse_chat(obj['chat'])
        date = obj['date']
        content_type = None
        opts = {}
        if 'text' in obj:
            opts['text'] = obj['text']
            content_type = 'text'
        if 'audio' in obj:
            opts['audio'] = Audio.de_json(json.dumps(obj['audio']))
            content_type = 'audio'
        if 'document' in obj:
            opts['document'] = Document.de_json(json.dumps(obj['document']))
            content_type = 'document'
        if 'photo' in obj:
            opts['photo'] = Message.parse_photo(obj['photo'])
            content_type = 'photo'
        if 'sticker' in obj:
            opts['sticker'] = Sticker.de_json(json.dumps(obj['sticker']))
            content_type = 'sticker'
        if 'video' in obj:
            opts['video'] = Video.de_json(json.dumps(obj['video']))
            content_type = 'video'
        if 'location' in obj:
            opts['location'] = Location.de_json(json.dumps(obj['location']))
            content_type = 'location'
        return Message(message_id, from_user, date, chat, content_type, opts)

    @classmethod
    def parse_chat(cls, chat):
        if 'first_name' not in chat:
            return GroupChat.de_json(json.dumps(chat))
        else:
            return User.de_json(json.dumps(chat))

    @classmethod
    def parse_photo(cls, photo_size_array):
        ret = []
        for ps in photo_size_array:
            ret.append(PhotoSize.de_json(json.dumps(ps)))
        return ret

    def __init__(self, message_id, from_user, date, chat, content_type, options):
        self.chat = chat
        self.date = date
        self.fromUser = from_user
        self.message_id = message_id
        self.content_type = content_type
        for key in options:
            setattr(self, key, options[key])


class PhotoSize:
    @classmethod
    def de_json(cls, json_string):
        obj = json.loads(json_string)
        file_id = obj['file_id']
        width = obj['width']
        height = obj['height']
        file_size = None
        if 'file_size' in obj:
            file_size = obj['file_size']
        return PhotoSize(file_id, width, height, file_size)

    def __init__(self, file_id, width, height, file_size=None):
        self.file_size = file_size
        self.height = height
        self.width = width
        self.file_id = file_id


class Audio:
    @classmethod
    def de_json(cls, json_string):
        obj = json.loads(json_string)
        file_id = obj['file_id']
        duration = obj['duration']
        mime_type = None
        file_size = None
        if 'mime_type' in obj:
            mime_type = obj['mime_type']
        if 'file_size' in obj:
            file_size = obj['file_size']
        return Audio(file_id, duration, mime_type, file_size)

    def __init__(self, file_id, duration, mime_type=None, file_size=None):
        self.file_id = file_id
        self.duration = duration
        self.mime_type = mime_type
        self.file_size = file_size


class Document:
    @classmethod
    def de_json(cls, json_string):
        obj = json.loads(json_string)
        file_id = obj['file_id']
        thumb = None
        if 'file_id' in obj['thumb']:
            thumb = PhotoSize.de_json(json.dumps(obj['thumb']))
        file_name = None
        mime_type = None
        file_size = None
        if 'file_name' in obj:
            file_name = obj['file_name']
        if 'mine_type' in obj:
            mime_type = obj['mime_type']
        if 'file_size' in obj:
            file_size = obj['file_size']
        return Document(file_id, thumb, file_name, mime_type, file_size)

    def __init__(self, file_id, thumb, file_name=None, mime_type=None, file_size=None):
        self.file_id = file_id
        self.thumb = thumb
        self.file_name = file_name
        self.mime_type = mime_type
        self.file_size = file_size


class Sticker:
    @classmethod
    def de_json(cls, json_string):
        obj = json.loads(json_string)
        file_id = obj['file_id']
        width = obj['width']
        height = obj['height']
        thumb = PhotoSize.de_json(json.dumps(obj['thumb']))
        file_size = None
        if 'file_size' in obj:
            file_size = obj['file_size']
        return Sticker(file_id, width, height, thumb, file_size)

    def __init__(self, file_id, width, height, thumb, file_size=None):
        self.file_id = file_id
        self.width = width
        self.height = height
        self.thumb = thumb
        self.file_size = file_size


class Video:
    @classmethod
    def de_json(cls, json_string):
        obj = json.loads(json_string)
        file_id = obj['file_id']
        width = obj['width']
        height = obj['height']
        duration = obj['duration']
        if 'file_id' in obj['thumb']:
            thumb = PhotoSize.de_json(json.dumps(obj['thumb']))
        caption = None
        mime_type = None
        file_size = None
        if 'caption' in obj:
            caption = obj['caption']
        if 'mine_type' in obj:
            mime_type = obj['mime_type']
        if 'file_size' in obj:
            file_size = obj['file_size']
        return Video(file_id, width, height, duration, thumb, mime_type, file_size, caption)

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
    @classmethod
    def de_json(cls, json_string):
        obj = json.loads(json_string)
        longitude = obj['longitude']
        latitude = obj['latitude']
        return Location(longitude, latitude)

    def __init__(self, longitude, latitude):
        self.longitude = longitude
        self.latitude = latitude


class UserProfilePhotos:
    @classmethod
    def de_json(cls, json_string):
        obj = json.loads(json_string)
        total_count = obj['total_count']
        photos = [[PhotoSize.de_json(json.dumps(y)) for y in x] for x in obj['photos']]
        return UserProfilePhotos(total_count, photos)

    def __init__(self, total_count, photos):
        self.total_count = total_count
        self.photos = photos


class ReplyKeyboardMarkup:
    def __init__(self, resize_keyboard=None, one_time_keyboard=None, selective=None, row_width=3):
        self.resize_keyboard = resize_keyboard
        self.one_time_keyboard = one_time_keyboard
        self.selective = selective
        self.row_width = row_width

        self.keyboard = []

    def add(self, *args):
        """
        This function adds strings to the keyboard, while not exceeding row_width.
        E.g. ReplyKeyboardMarkup#add("A", "B", "C") yields the json result {keyboard: [["A"], ["B"], ["C"]]}
        when row_width is set to 1.
        When row_width is set to 2, the following is the result of this function: {keyboard: [["A", "B"], ["C"]]}
        See https://core.telegram.org/bots/api#replykeyboardmarkup
        :param args: strings to append to the keyboard
        """
        i = 1
        row = []
        for string in args:
            row.append(string)
            if i % self.row_width == 0:
                self.keyboard.append(row)
                row = []
            i += 1
        if len(row) > 0:
            self.keyboard.append(row)

    def row(self, *args):
        """
        Adds a list of strings to the keyboard. This function does not consider row_width.
        ReplyKeyboardMarkup#row("A")#row("B", "C")#to_json() outputs '{keyboard: [["A"], ["B", "C"]]}'
        See https://core.telegram.org/bots/api#replykeyboardmarkup
        :param args: strings
        :return: self, to allow function chaining.
        """
        self.keyboard.append(args)
        return self

    def to_json(self):
        """
        Converts this object to its json representation following the Telegram API guidelines described here:
        https://core.telegram.org/bots/api#replykeyboardmarkup
        :return:
        """
        json_dict = {'keyboard': self.keyboard}
        if self.one_time_keyboard:
            json_dict['one_time_keyboard'] = True

        if self.resize_keyboard:
            json_dict['resize_keyboard'] = True

        if self.selective:
            json_dict['selective'] = True

        return json.dumps(json_dict)
