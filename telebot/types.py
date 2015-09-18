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


class JsonSerializable:
    """
    Subclasses of this class are guaranteed to be able to be converted to JSON format.
    All subclasses of this class must override to_json.
    """
    def to_json(self):
        """
        Returns a JSON string representation of this class.

        This function must be overridden by subclasses.
        :return: a JSON formatted string.
        """
        raise NotImplementedError


class JsonDeserializable:
    """
    Subclasses of this class are guaranteed to be able to be created from a json-style dict or json formatted string.
    All subclasses of this class must override de_json.
    """
    @classmethod
    def de_json(cls, json_type):
        """
        Returns an instance of this class from the given json dict or string.

        This function must be overridden by subclasses.
        :return: an instance of this class created from the given json dict or string.
        """
        raise NotImplementedError

    @staticmethod
    def check_json(json_type):
        """
        Checks whether json_type is a dict or a string. If it is already a dict, it is returned as-is.
        If it is not, it is converted to a dict by means of json.loads(json_type)
        :param json_type:
        :return:
        """
        if type(json_type) == dict:
            return json_type
        elif type(json_type) == str:
            return json.loads(json_type)
        else:
            raise ValueError("json_type should be a json dict or string.")

    def __str__(self):
        d = {}
        for x, y in self.__dict__.iteritems():
            if hasattr(y, '__dict__'):
                d[x] = y.__dict__
            else:
                d[x] = y

        return unicode(d)

class Update(JsonDeserializable):
    @classmethod
    def de_json(cls, json_type):
        obj = cls.check_json(json_type)
        update_id = obj['update_id']
        message = Message.de_json(obj['message'])
        return Update(update_id, message)

    def __init__(self, update_id, message):
        self.update_id = update_id
        self.message = message

class User(JsonDeserializable):
    @classmethod
    def de_json(cls, json_string):
        obj = cls.check_json(json_string)
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


class GroupChat(JsonDeserializable):
    @classmethod
    def de_json(cls, json_string):
        obj = cls.check_json(json_string)
        id = obj['id']
        title = obj['title']
        return GroupChat(id, title)

    def __init__(self, id, title):
        self.id = id
        self.title = title


class Message(JsonDeserializable):
    @classmethod
    def de_json(cls, json_string):
        obj = cls.check_json(json_string)
        message_id = obj['message_id']
        from_user = User.de_json(obj['from'])
        chat = Message.parse_chat(obj['chat'])
        date = obj['date']
        content_type = None
        opts = {}
        if 'forward_from' in obj:
            opts['forward_from'] = User.de_json(obj['forward_from'])
        if 'forward_date' in obj:
            opts['forward_date'] = obj['forward_date']
        if 'reply_to_message' in obj:
            opts['reply_to_message'] = Message.de_json(obj['reply_to_message'])
        if 'text' in obj:
            opts['text'] = obj['text']
            content_type = 'text'
        if 'audio' in obj:
            opts['audio'] = Audio.de_json(obj['audio'])
            content_type = 'audio'
        if 'voice' in obj:
            opts['voice'] = Audio.de_json(obj['voice'])
            content_type = 'voice'
        if 'document' in obj:
            opts['document'] = Document.de_json(obj['document'])
            content_type = 'document'
        if 'photo' in obj:
            opts['photo'] = Message.parse_photo(obj['photo'])
            content_type = 'photo'
        if 'sticker' in obj:
            opts['sticker'] = Sticker.de_json(obj['sticker'])
            content_type = 'sticker'
        if 'video' in obj:
            opts['video'] = Video.de_json(obj['video'])
            content_type = 'video'
        if 'location' in obj:
            opts['location'] = Location.de_json(obj['location'])
            content_type = 'location'
        if 'contact' in obj:
            opts['contact'] = Contact.de_json(json.dumps(obj['contact']))
            content_type = 'contact'
        if 'new_chat_participant' in obj:
            opts['new_chat_participant'] = User.de_json(obj['new_chat_participant'])
            content_type = 'new_chat_participant'
        if 'left_chat_participant' in obj:
            opts['left_chat_participant'] = User.de_json(obj['left_chat_participant'])
            content_type = 'left_chat_participant'
        if 'new_chat_title' in obj:
            opts['new_chat_title'] = obj['new_chat_title']
            content_type = 'new_chat_title'
        if 'new_chat_photo' in obj:
            opts['new_chat_photo'] = obj['new_chat_photo']
            content_type = 'new_chat_photo'
        if 'delete_chat_photo' in obj:
            opts['delete_chat_photo'] = obj['delete_chat_photo']
            content_type = 'delete_chat_photo'
        if 'group_chat_created' in obj:
            opts['group_chat_created'] = obj['group_chat_created']
            content_type = 'group_chat_created'
        if 'caption' in obj:
            opts['caption'] = obj['caption']
        return Message(message_id, from_user, date, chat, content_type, opts)

    @classmethod
    def parse_chat(cls, chat):
        if 'first_name' not in chat:
            return GroupChat.de_json(chat)
        else:
            return User.de_json(chat)

    @classmethod
    def parse_photo(cls, photo_size_array):
        ret = []
        for ps in photo_size_array:
            ret.append(PhotoSize.de_json(ps))
        return ret

    def __init__(self, message_id, from_user, date, chat, content_type, options):
        self.chat = chat
        self.date = date
        self.from_user = from_user
        self.message_id = message_id
        self.content_type = content_type
        for key in options:
            setattr(self, key, options[key])


class PhotoSize(JsonDeserializable):
    @classmethod
    def de_json(cls, json_string):
        obj = cls.check_json(json_string)
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


class Audio(JsonDeserializable):
    @classmethod
    def de_json(cls, json_string):
        obj = cls.check_json(json_string)
        file_id = obj['file_id']
        duration = obj['duration']
        performer = None
        title = None
        mime_type = None
        file_size = None
        if 'mime_type' in obj:
            mime_type = obj['mime_type']
        if 'file_size' in obj:
            file_size = obj['file_size']
        if 'performer' in obj:
            performer = obj['performer']
        if 'title' in obj:
            title = obj['title']
        return Audio(file_id, duration, performer, title, mime_type, file_size)

    def __init__(self, file_id, duration, performer=None, title=None, mime_type=None, file_size=None):
        self.file_id = file_id
        self.duration = duration
        self.performer = performer
        self.title = title
        self.mime_type = mime_type
        self.file_size = file_size


class Voice(JsonDeserializable):
    @classmethod
    def de_json(cls, json_string):
        obj = cls.check_json(json_string)
        file_id = obj['file_id']
        duration = obj['duration']
        mime_type = None
        file_size = None
        if 'mime_type' in obj:
            mime_type = obj['mime_type']
        if 'file_size' in obj:
            file_size = obj['file_size']
        return Voice(file_id, duration, mime_type, file_size)

    def __init__(self, file_id, duration, mime_type=None, file_size=None):
        self.file_id = file_id
        self.duration = duration
        self.mime_type = mime_type
        self.file_size = file_size


class Document(JsonDeserializable):
    @classmethod
    def de_json(cls, json_string):
        obj = cls.check_json(json_string)
        file_id = obj['file_id']
        thumb = None
        if 'thumb' in obj:
            if 'file_id' in obj['thumb']:
                thumb = PhotoSize.de_json(obj['thumb'])
        file_name = None
        mime_type = None
        file_size = None
        if 'file_name' in obj:
            file_name = obj['file_name']
        if 'mime_type' in obj:
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


class Sticker(JsonDeserializable):
    @classmethod
    def de_json(cls, json_string):
        obj = cls.check_json(json_string)
        file_id = obj['file_id']
        width = obj['width']
        height = obj['height']
        thumb = None
        if 'thumb' in obj:
            thumb = PhotoSize.de_json(obj['thumb'])
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


class Video(JsonDeserializable):
    @classmethod
    def de_json(cls, json_string):
        obj = cls.check_json(json_string)
        file_id = obj['file_id']
        width = obj['width']
        height = obj['height']
        duration = obj['duration']
        thumb = None
        mime_type = None
        file_size = None
        if 'thumb' in obj:
            thumb = PhotoSize.de_json(obj['thumb'])
        if 'mime_type' in obj:
            mime_type = obj['mime_type']
        if 'file_size' in obj:
            file_size = obj['file_size']
        return Video(file_id, width, height, duration, thumb, mime_type, file_size)

    def __init__(self, file_id, width, height, duration, thumb=None, mime_type=None, file_size=None):
        self.file_id = file_id
        self.width = width
        self.height = height
        self.duration = duration
        self.thumb = thumb
        self.mime_type = mime_type
        self.file_size = file_size


class Contact(JsonDeserializable):
    @classmethod
    def de_json(cls, json_string):
        obj = cls.check_json(json_string)
        phone_number = obj['phone_number']
        first_name = obj['first_name']
        last_name = None
        user_id = None
        if 'last_name' in obj:
            last_name = obj['last_name']
        if 'user_id' in obj:
            user_id = obj['user_id']
        return Contact(phone_number, first_name, last_name, user_id)

    def __init__(self, phone_number, first_name, last_name=None, user_id=None):
        self.phone_number = phone_number
        self.first_name = first_name
        self.last_name = last_name
        self.user_id = user_id


class Location(JsonDeserializable):
    @classmethod
    def de_json(cls, json_string):
        obj = cls.check_json(json_string)
        longitude = obj['longitude']
        latitude = obj['latitude']
        return Location(longitude, latitude)

    def __init__(self, longitude, latitude):
        self.longitude = longitude
        self.latitude = latitude


class UserProfilePhotos(JsonDeserializable):
    @classmethod
    def de_json(cls, json_string):
        obj = cls.check_json(json_string)
        total_count = obj['total_count']
        photos = [[PhotoSize.de_json(y) for y in x] for x in obj['photos']]
        return UserProfilePhotos(total_count, photos)

    def __init__(self, total_count, photos):
        self.total_count = total_count
        self.photos = photos

class File(JsonDeserializable):

    @classmethod
    def de_json(cls, json_type):
        obj = cls.check_json(json_type)
        file_id = obj['file_id']

        file_size = None
        file_path = None
        if 'file_size' in obj:
            file_size = obj['file_size']
        if 'file_path' in obj:
            file_path = obj['file_path']
        return File(file_id, file_size, file_path)

    def __init__(self, file_id, file_size, file_path):
        self.file_id = file_id
        self.file_size = file_size
        self.file_path = file_path


class ForceReply(JsonSerializable):
    def __init__(self, selective=None):
        self.selective = selective

    def to_json(self):
        json_dict = {'force_reply': True}
        if self.selective:
            json_dict['selective'] = True
        return json.dumps(json_dict)


class ReplyKeyboardHide(JsonSerializable):
    def __init__(self, selective=None):
        self.selective = selective

    def to_json(self):
        json_dict = {'hide_keyboard': True}
        if self.selective:
            json_dict['selective'] = True
        return json.dumps(json_dict)


class ReplyKeyboardMarkup(JsonSerializable):
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
