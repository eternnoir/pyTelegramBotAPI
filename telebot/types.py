# -*- coding: utf-8 -*-

import json
import six

from telebot import util


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


class Dictionaryable:
    """
    Subclasses of this class are guaranteed to be able to be converted to dictionary.
    All subclasses of this class must override to_dic.
    """

    def to_dic(self):
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
        for x, y in six.iteritems(self.__dict__):
            if hasattr(y, '__dict__'):
                d[x] = y.__dict__
            else:
                d[x] = y

        return six.text_type(d)


class Update(JsonDeserializable):
    @classmethod
    def de_json(cls, json_type):
        obj = cls.check_json(json_type)
        update_id = obj['update_id']
        message = None
        inline_query = None
        chosen_inline_result = None
        callback_query = None
        if 'message' in obj:
            message = Message.de_json(obj['message'])
        if 'inline_query' in obj:
            inline_query = InlineQuery.de_json(obj['inline_query'])
        if 'chosen_inline_result' in obj:
            chosen_inline_result = ChosenInlineResult.de_json(obj['chosen_inline_result'])
        if 'callback_query' in obj:
            callback_query = CallbackQuery.de_json(obj['callback_query'])
        return cls(update_id, message, inline_query, chosen_inline_result, callback_query)

    def __init__(self, update_id, message, inline_query, chosen_inline_result, callback_query):
        self.update_id = update_id
        self.message = message
        self.inline_query = inline_query
        self.chosen_inline_result = chosen_inline_result
        self.callback_query = callback_query


class User(JsonDeserializable):
    @classmethod
    def de_json(cls, json_string):
        obj = cls.check_json(json_string)
        id = obj['id']
        first_name = obj['first_name']
        last_name = obj.get('last_name')
        username = obj.get('username')
        return cls(id, first_name, last_name, username)

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
        return cls(id, title)

    def __init__(self, id, title):
        self.id = id
        self.title = title


class Chat(JsonDeserializable):
    @classmethod
    def de_json(cls, json_string):
        obj = cls.check_json(json_string)
        id = obj['id']
        type = obj['type']
        title = obj.get('title')
        username = obj.get('username')
        first_name = obj.get('first_name')
        last_name = obj.get('last_name')
        return cls(id, type, title, username, first_name, last_name)

    def __init__(self, id, type, title=None, username=None, first_name=None, last_name=None):
        self.type = type
        self.last_name = last_name
        self.first_name = first_name
        self.username = username
        self.id = id
        self.title = title


class Message(JsonDeserializable):
    @classmethod
    def de_json(cls, json_string):
        obj = cls.check_json(json_string)
        message_id = obj['message_id']
        from_user = None
        if 'from' in obj:
            from_user = User.de_json(obj['from'])
        date = obj['date']
        chat = Chat.de_json(obj['chat'])
        content_type = None
        opts = {}
        if 'forward_from' in obj:
            opts['forward_from'] = User.de_json(obj['forward_from'])
        if 'forward_from_chat' in obj:
            opts['forward_from_chat'] = Chat.de_json(obj['forward_from_chat'])
        if 'forward_date' in obj:
            opts['forward_date'] = obj['forward_date']
        if 'reply_to_message' in obj:
            opts['reply_to_message'] = Message.de_json(obj['reply_to_message'])
        if 'text' in obj:
            opts['text'] = obj['text']
            content_type = 'text'
        if 'entities' in obj:
            opts['entities'] = Message.parse_entities(obj['entities'])
        if 'audio' in obj:
            opts['audio'] = Audio.de_json(obj['audio'])
            content_type = 'audio'
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
        if 'voice' in obj:
            opts['voice'] = Audio.de_json(obj['voice'])
            content_type = 'voice'
        if 'caption' in obj:
            opts['caption'] = obj['caption']
        if 'contact' in obj:
            opts['contact'] = Contact.de_json(json.dumps(obj['contact']))
            content_type = 'contact'
        if 'location' in obj:
            opts['location'] = Location.de_json(obj['location'])
            content_type = 'location'
        if 'venue' in obj:
            opts['venue'] = Venue.de_json(obj['venue'])
            content_type = 'venue'
        if 'new_chat_member' in obj:
            opts['new_chat_member'] = User.de_json(obj['new_chat_member'])
            content_type = 'new_chat_member'
        if 'left_chat_member' in obj:
            opts['left_chat_member'] = User.de_json(obj['left_chat_member'])
            content_type = 'left_chat_member'
        if 'new_chat_title' in obj:
            opts['new_chat_title'] = obj['new_chat_title']
        if 'new_chat_photo' in obj:
            opts['new_chat_photo'] = Message.parse_photo(obj['new_chat_photo'])
        if 'delete_chat_photo' in obj:
            opts['delete_chat_photo'] = obj['delete_chat_photo']
        if 'group_chat_created' in obj:
            opts['group_chat_created'] = obj['group_chat_created']
        if 'supergroup_chat_created' in obj:
            opts['supergroup_chat_created'] = obj['supergroup_chat_created']
        if 'channel_chat_created' in obj:
            opts['channel_chat_created'] = obj['channel_chat_created']
        if 'migrate_to_chat_id' in obj:
            opts['migrate_to_chat_id'] = obj['migrate_to_chat_id']
        if 'migrate_from_chat_id' in obj:
            opts['migrate_from_chat_id'] = obj['migrate_from_chat_id']
        if 'pinned_message' in obj:
            opts['pinned_message'] = Message.de_json(obj['pinned_message'])
        return cls(message_id, from_user, date, chat, content_type, opts)

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

    @classmethod
    def parse_entities(cls, message_entity_array):
        ret = []
        for me in message_entity_array:
            ret.append(MessageEntity.de_json(me))
        return ret

    def __init__(self, message_id, from_user, date, chat, content_type, options):
        self.content_type = content_type
        self.message_id = message_id
        self.from_user = from_user
        self.date = date
        self.chat = chat
        self.forward_from_chat = None
        self.forward_from = None
        self.forward_date = None
        self.reply_to_message = None
        self.text = None
        self.entities = None
        self.audio = None
        self.document = None
        self.photo = None
        self.sticker = None
        self.video = None
        self.voice = None
        self.caption = None
        self.contact = None
        self.location = None
        self.venue = None
        self.new_chat_member = None
        self.left_chat_member = None
        self.new_chat_title = None
        self.new_chat_photo = None
        self.delete_chat_photo = None
        self.group_chat_created = None
        self.supergroup_chat_created = None
        self.channel_chat_created = None
        self.migrate_to_chat_id = None
        self.migrate_from_chat_id = None
        self.pinned_message = None
        for key in options:
            setattr(self, key, options[key])


class MessageEntity(JsonDeserializable):
    @classmethod
    def de_json(cls, json_string):
        obj = cls.check_json(json_string)
        type = obj['type']
        offset = obj['offset']
        length = obj['length']
        url = obj.get('url')
        return cls(type, offset, length, url)

    def __init__(self, type, offset, length, url=None):
        self.type = type
        self.offset = offset
        self.length = length
        self.url = url


class PhotoSize(JsonDeserializable):
    @classmethod
    def de_json(cls, json_string):
        obj = cls.check_json(json_string)
        file_id = obj['file_id']
        width = obj['width']
        height = obj['height']
        file_size = obj.get('file_size')
        return cls(file_id, width, height, file_size)

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
        performer = obj.get('performer')
        title = obj.get('title')
        mime_type = obj.get('mime_type')
        file_size = obj.get('file_size')
        return cls(file_id, duration, performer, title, mime_type, file_size)

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
        mime_type = obj.get('mime_type')
        file_size = obj.get('file_size')
        return cls(file_id, duration, mime_type, file_size)

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
        if 'thumb' in obj and 'file_id' in obj['thumb']:
            thumb = PhotoSize.de_json(obj['thumb'])
        file_name = obj.get('file_name')
        mime_type = obj.get('mime_type')
        file_size = obj.get('file_size')
        return cls(file_id, thumb, file_name, mime_type, file_size)

    def __init__(self, file_id, thumb=None, file_name=None, mime_type=None, file_size=None):
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
        emoji = obj.get('emoji')
        file_size = obj.get('file_size')
        return cls(file_id, width, height, thumb, emoji, file_size)

    def __init__(self, file_id, width, height, thumb, emoji=None, file_size=None):
        self.file_id = file_id
        self.width = width
        self.height = height
        self.thumb = thumb
        self.emoji = emoji
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
        if 'thumb' in obj:
            thumb = PhotoSize.de_json(obj['thumb'])
        mime_type = obj.get('mime_type')
        file_size = obj.get('file_size')
        return cls(file_id, width, height, duration, thumb, mime_type, file_size)

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
        last_name = obj.get('last_name')
        user_id = obj.get('user_id')
        return cls(phone_number, first_name, last_name, user_id)

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
        return cls(longitude, latitude)

    def __init__(self, longitude, latitude):
        self.longitude = longitude
        self.latitude = latitude


class Venue(JsonDeserializable):
    @classmethod
    def de_json(cls, json_type):
        obj = cls.check_json(json_type)
        location = obj['location']
        title = obj['title']
        address = obj['address']
        foursquare_id = obj.get('foursquare_id')
        return cls(location, title, address, foursquare_id)

    def __init__(self, location, title, address, foursquare_id=None):
        self.location = location
        self.title = title
        self.address = address
        self.foursquare_id = foursquare_id


class UserProfilePhotos(JsonDeserializable):
    @classmethod
    def de_json(cls, json_string):
        obj = cls.check_json(json_string)
        total_count = obj['total_count']
        photos = [[PhotoSize.de_json(y) for y in x] for x in obj['photos']]
        return cls(total_count, photos)

    def __init__(self, total_count, photos):
        self.total_count = total_count
        self.photos = photos


class File(JsonDeserializable):
    @classmethod
    def de_json(cls, json_type):
        obj = cls.check_json(json_type)
        file_id = obj['file_id']
        file_size = obj.get('file_size')
        file_path = obj.get('file_path')
        return cls(file_id, file_size, file_path)

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
        :param args: KeyboardButton to append to the keyboard
        """
        i = 1
        row = []
        for button in args:
            if util.is_string(button):
                row.append({'text': button})
            else:
                row.append(button.to_dic())
            if i % self.row_width == 0:
                self.keyboard.append(row)
                row = []
            i += 1
        if len(row) > 0:
            self.keyboard.append(row)

    def row(self, *args):
        """
        Adds a list of KeyboardButton to the keyboard. This function does not consider row_width.
        ReplyKeyboardMarkup#row("A")#row("B", "C")#to_json() outputs '{keyboard: [["A"], ["B", "C"]]}'
        See https://core.telegram.org/bots/api#replykeyboardmarkup
        :param args: strings
        :return: self, to allow function chaining.
        """
        btn_array = []
        for button in args:
            if util.is_string(button):
                btn_array.append({'text': button})
            else:
                btn_array.append(button.to_dic())
        self.keyboard.append(btn_array)
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


class KeyboardButton(Dictionaryable, JsonSerializable):
    def __init__(self, text, request_contact=None, request_location=None):
        self.text = text
        self.request_contact = request_contact
        self.request_location = request_location

    def to_json(self):
        return json.dumps(self.to_dic())

    def to_dic(self):
        json_dic = {'text': self.text}
        if self.request_contact:
            json_dic['request_contact'] = self.request_contact
        if self.request_location:
            json_dic['request_location'] = self.request_location
        return json_dic


class InlineKeyboardMarkup(Dictionaryable, JsonSerializable):
    def __init__(self, row_width=3):
        self.row_width = row_width

        self.keyboard = []

    def add(self, *args):
        """
        This function adds strings to the keyboard, while not exceeding row_width.
        E.g. ReplyKeyboardMarkup#add("A", "B", "C") yields the json result {keyboard: [["A"], ["B"], ["C"]]}
        when row_width is set to 1.
        When row_width is set to 2, the following is the result of this function: {keyboard: [["A", "B"], ["C"]]}
        See https://core.telegram.org/bots/api#replykeyboardmarkup
        :param args: KeyboardButton to append to the keyboard
        """
        i = 1
        row = []
        for button in args:
            row.append(button.to_dic())
            if i % self.row_width == 0:
                self.keyboard.append(row)
                row = []
            i += 1
        if len(row) > 0:
            self.keyboard.append(row)

    def row(self, *args):
        """
        Adds a list of KeyboardButton to the keyboard. This function does not consider row_width.
        ReplyKeyboardMarkup#row("A")#row("B", "C")#to_json() outputs '{keyboard: [["A"], ["B", "C"]]}'
        See https://core.telegram.org/bots/api#inlinekeyboardmarkup
        :param args: strings
        :return: self, to allow function chaining.
        """
        btn_array = []
        for button in args:
            btn_array.append(button.to_dic())
        self.keyboard.append(btn_array)
        return self

    def to_json(self):
        """
        Converts this object to its json representation following the Telegram API guidelines described here:
        https://core.telegram.org/bots/api#inlinekeyboardmarkup
        :return:
        """
        json_dict = {'inline_keyboard': self.keyboard}
        return json.dumps(json_dict)

    def to_dic(self):
        json_dict = {'inline_keyboard': self.keyboard}
        return json_dict


class InlineKeyboardButton(JsonSerializable):
    def __init__(self, text, url=None, callback_data=None, switch_inline_query=None):
        self.text = text
        self.url = url
        self.callback_data = callback_data
        self.switch_inline_query = switch_inline_query

    def to_json(self):
        return json.dumps(self.to_dic())

    def to_dic(self):
        json_dic = {'text': self.text}
        if self.url:
            json_dic['url'] = self.url
        if self.callback_data:
            json_dic['callback_data'] = self.callback_data
        if self.switch_inline_query is not None:
            json_dic['switch_inline_query'] = self.switch_inline_query
        return json_dic


class CallbackQuery(JsonDeserializable):
    @classmethod
    def de_json(cls, json_type):
        obj = cls.check_json(json_type)
        id = obj['id']
        from_user = User.de_json(obj['from'])
        message = None
        if 'message' in obj:
            message = Message.de_json(obj['message'])
        inline_message_id = obj.get('inline_message_id')
        data = obj['data']
        return cls(id, from_user, data, message, inline_message_id)

    def __init__(self, id, from_user, data, message=None, inline_message_id=None):
        self.id = id
        self.from_user = from_user
        self.message = message
        self.data = data
        self.inline_message_id = inline_message_id


# InlineQuery

class InlineQuery(JsonDeserializable):
    @classmethod
    def de_json(cls, json_type):
        obj = cls.check_json(json_type)
        id = obj['id']
        from_user = User.de_json(obj['from'])
        query = obj['query']
        offset = obj['offset']
        return cls(id, from_user, query, offset)

    def __init__(self, id, from_user, query, offset):
        """
        This object represents an incoming inline query.
        When the user sends an empty query, your bot could
        return some default or trending results.
        :param id: string Unique identifier for this query
        :param from_user: User Sender
        :param query: String Text of the query
        :param offset: String Offset of the results to be returned, can be controlled by the bot
        :return: InlineQuery Object
        """
        self.id = id
        self.from_user = from_user
        self.query = query
        self.offset = offset


class InputTextMessageContent(Dictionaryable):
    def __init__(self, message_text, parse_mode=None, disable_web_page_preview=None):
        self.message_text = message_text
        self.parse_mode = parse_mode
        self.disable_web_page_preview = disable_web_page_preview

    def to_dic(self):
        json_dic = {'message_text': self.message_text}
        if self.parse_mode:
            json_dic['parse_mode'] = self.parse_mode
        if self.disable_web_page_preview:
            json_dic['disable_web_page_preview'] = self.disable_web_page_preview
        return json_dic


class InputLocationMessageContent(Dictionaryable):
    def __init__(self, latitude, longitude):
        self.latitude = latitude
        self.longitude = longitude

    def to_dic(self):
        json_dic = {'latitude': self.latitudet, 'longitude': self.longitude}
        return json_dic


class InputVenueMessageContent(Dictionaryable):
    def __init__(self, latitude, longitude, title, address, foursquare_id=None):
        self.latitude = latitude
        self.longitude = longitude
        self.title = title
        self.address = address
        self.foursquare_id = foursquare_id

    def to_dic(self):
        json_dic = {'latitude': self.latitude, 'longitude': self.longitude, 'title': self.title,
                    'address': self.address}
        if self.foursquare_id:
            json_dic['foursquare_id'] = self.foursquare_id
        return json_dic


class InputContactMessageContent(Dictionaryable):
    def __init__(self, phone_number, first_name, last_name=None):
        self.phone_number = phone_number
        self.first_name = first_name
        self.last_name = last_name

    def to_dic(self):
        json_dic = {'phone_numbe': self.phone_number, 'first_name': self.first_name}
        if self.last_name:
            json_dic['last_name'] = self.last_name
        return json_dic


class ChosenInlineResult(JsonDeserializable):
    @classmethod
    def de_json(cls, json_type):
        obj = cls.check_json(json_type)
        result_id = obj['result_id']
        from_user = User.de_json(obj['from'])
        query = obj['query']
        location = None
        if 'location' in obj:
            location = Location.de_json(obj['location'])
        inline_message_id = obj.get('inline_message_id')
        return cls(result_id, from_user, query, location, inline_message_id)

    def __init__(self, result_id, from_user, query, location=None, inline_message_id=None):
        """
        This object represents a result of an inline query
        that was chosen by the user and sent to their chat partner.
        :param result_id: string The unique identifier for the result that was chosen.
        :param from_user: User The user that chose the result.
        :param query: String The query that was used to obtain the result.
        :return: ChosenInlineResult Object.
        """
        self.result_id = result_id
        self.from_user = from_user
        self.query = query
        self.location = location
        self.inline_message_id = inline_message_id


class InlineQueryResultArticle(JsonSerializable):
    def __init__(self, id, title, input_message_content, reply_markup=None, url=None,
                 hide_url=None, description=None, thumb_url=None, thumb_width=None, thumb_height=None):
        """
        Represents a link to an article or web page.
        :param id: Unique identifier for this result, 1-64 Bytes.
        :param title: Title of the result.
        :param input_message_content: InputMessageContent : Content of the message to be sent
        :param reply_markup: InlineKeyboardMarkup : Inline keyboard attached to the message
        :param url: URL of the result.
        :param hide_url: Pass True, if you don't want the URL to be shown in the message.
        :param description: Short description of the result.
        :param thumb_url: Url of the thumbnail for the result.
        :param thumb_width: Thumbnail width.
        :param thumb_height: Thumbnail height
        :return:
        """
        self.type = 'article'
        self.id = id
        self.title = title
        self.input_message_content = input_message_content
        self.reply_markup = reply_markup
        self.url = url
        self.hide_url = hide_url
        self.description = description
        self.thumb_url = thumb_url
        self.thumb_width = thumb_width
        self.thumb_height = thumb_height

    def to_json(self):
        json_dict = {'type': self.type, 'id': self.id, 'title': self.title,
                     'input_message_content': self.input_message_content.to_dic()}
        if self.reply_markup:
            json_dict['reply_markup'] = self.reply_markup.to_dic()
        if self.url:
            json_dict['url'] = self.url
        if self.hide_url:
            json_dict['hide_url'] = self.hide_url
        if self.description:
            json_dict['description'] = self.description
        if self.thumb_url:
            json_dict['thumb_url'] = self.thumb_url
        if self.thumb_width:
            json_dict['thumb_width'] = self.thumb_width
        if self.thumb_height:
            json_dict['thumb_height'] = self.thumb_height
        return json.dumps(json_dict)


class InlineQueryResultPhoto(JsonSerializable):
    def __init__(self, id, photo_url, thumb_url, photo_width=None, photo_height=None, title=None,
                 description=None, caption=None, reply_markup=None, input_message_content=None):
        """
        Represents a link to a photo.
        :param id: Unique identifier for this result, 1-64 bytes
        :param photo_url: A valid URL of the photo. Photo must be in jpeg format. Photo size must not exceed 5MB
        :param thumb_url: URL of the thumbnail for the photo
        :param photo_width: Width of the photo.
        :param photo_height: Height of the photo.
        :param title: Title for the result.
        :param description: Short description of the result.
        :param caption: Caption of the photo to be sent, 0-200 characters.
        :param reply_markup: InlineKeyboardMarkup : Inline keyboard attached to the message
        :param input_message_content: InputMessageContent : Content of the message to be sent instead of the photo
        :return:
        """
        self.type = 'photo'
        self.id = id
        self.photo_url = photo_url
        self.photo_width = photo_width
        self.photo_height = photo_height
        self.thumb_url = thumb_url
        self.title = title
        self.description = description
        self.caption = caption
        self.reply_markup = reply_markup
        self.input_message_content = input_message_content

    def to_json(self):
        json_dict = {'type': self.type, 'id': self.id, 'photo_url': self.photo_url, 'thumb_url': self.thumb_url}
        if self.photo_width:
            json_dict['photo_width'] = self.photo_width
        if self.photo_height:
            json_dict['photo_height'] = self.photo_height
        if self.title:
            json_dict['title'] = self.title
        if self.description:
            json_dict['description'] = self.description
        if self.caption:
            json_dict['caption'] = self.caption
        if self.reply_markup:
            json_dict['reply_markup'] = self.reply_markup.to_dic()
        if self.input_message_content:
            json_dict['input_message_content'] = self.input_message_content.to_dic()
        return json.dumps(json_dict)


class InlineQueryResultGif(JsonSerializable):
    def __init__(self, id, gif_url, thumb_url, gif_width=None, gif_height=None, title=None, caption=None,
                 reply_markup=None, input_message_content=None):
        """
        Represents a link to an animated GIF file.
        :param id: Unique identifier for this result, 1-64 bytes.
        :param gif_url: A valid URL for the GIF file. File size must not exceed 1MB
        :param thumb_url: URL of the static thumbnail (jpeg or gif) for the result.
        :param gif_width: Width of the GIF.
        :param gif_height: Height of the GIF.
        :param title: Title for the result.
        :param caption:  Caption of the GIF file to be sent, 0-200 characters
        :param reply_markup: InlineKeyboardMarkup : Inline keyboard attached to the message
        :param input_message_content: InputMessageContent : Content of the message to be sent instead of the photo
        :return:
        """
        self.type = 'gif'
        self.id = id
        self.gif_url = gif_url
        self.gif_width = gif_width
        self.gif_height = gif_height
        self.thumb_url = thumb_url
        self.title = title
        self.caption = caption
        self.reply_markup = reply_markup
        self.input_message_content = input_message_content

    def to_json(self):
        json_dict = {'type': self.type, 'id': self.id, 'gif_url': self.gif_url, 'thumb_url': self.thumb_url}
        if self.gif_height:
            json_dict['gif_height'] = self.gif_height
        if self.gif_width:
            json_dict['gif_width'] = self.gif_width
        if self.title:
            json_dict['title'] = self.title
        if self.caption:
            json_dict['caption'] = self.caption
        if self.reply_markup:
            json_dict['reply_markup'] = self.reply_markup.to_dic()
        if self.input_message_content:
            json_dict['input_message_content'] = self.input_message_content.to_dic()
        return json.dumps(json_dict)


class InlineQueryResultMpeg4Gif(JsonSerializable):
    def __init__(self, id, mpeg4_url, thumb_url, mpeg4_width=None, mpeg4_height=None, title=None, caption=None,
                 reply_markup=None, input_message_content=None):
        """
        Represents a link to a video animation (H.264/MPEG-4 AVC video without sound).
        :param id: Unique identifier for this result, 1-64 bytes
        :param mpeg4_url: A valid URL for the MP4 file. File size must not exceed 1MB
        :param thumb_url: URL of the static thumbnail (jpeg or gif) for the result
        :param mpeg4_width: Video width
        :param mpeg4_height: Video height
        :param title: Title for the result
        :param caption: Caption of the MPEG-4 file to be sent, 0-200 characters
        :param reply_markup: InlineKeyboardMarkup : Inline keyboard attached to the message
        :param input_message_content: InputMessageContent : Content of the message to be sent instead of the photo
        :return:
        """
        self.type = 'mpeg4_gif'
        self.id = id
        self.mpeg4_url = mpeg4_url
        self.mpeg4_width = mpeg4_width
        self.mpeg4_height = mpeg4_height
        self.thumb_url = thumb_url
        self.title = title
        self.caption = caption
        self.reply_markup = reply_markup
        self.input_message_content = input_message_content

    def to_json(self):
        json_dict = {'type': self.type, 'id': self.id, 'mpeg4_url': self.mpeg4_url, 'thumb_url': self.thumb_url}
        if self.mpeg4_width:
            json_dict['mpeg4_width'] = self.mpeg4_width
        if self.mpeg4_height:
            json_dict['mpeg4_height'] = self.mpeg4_height
        if self.title:
            json_dict['title'] = self.title
        if self.caption:
            json_dict['caption'] = self.caption
        if self.reply_markup:
            json_dict['reply_markup'] = self.reply_markup.to_dic()
        if self.input_message_content:
            json_dict['input_message_content'] = self.input_message_content.to_dic()
        return json.dumps(json_dict)


class InlineQueryResultVideo(JsonSerializable):
    def __init__(self, id, video_url, mime_type, thumb_url, title,
                 caption=None, video_width=None, video_height=None, video_duration=None, description=None,
                 reply_markup=None, input_message_content=None):
        """
        Represents link to a page containing an embedded video player or a video file.
        :param id: Unique identifier for this result, 1-64 bytes
        :param video_url: A valid URL for the embedded video player or video file
        :param mime_type: Mime type of the content of video url, “text/html” or “video/mp4”
        :param thumb_url: URL of the thumbnail (jpeg only) for the video
        :param title: Title for the result
        :param video_width: Video width
        :param video_height: Video height
        :param video_duration: Video duration in seconds
        :param description: Short description of the result
        :return:
        """
        self.type = 'video'
        self.id = id
        self.video_url = video_url
        self.mime_type = mime_type
        self.video_width = video_width
        self.video_height = video_height
        self.video_duration = video_duration
        self.thumb_url = thumb_url
        self.title = title
        self.caption = caption
        self.description = description
        self.input_message_content = input_message_content
        self.reply_markup = reply_markup

    def to_json(self):
        json_dict = {'type': self.type, 'id': self.id, 'video_url': self.video_url, 'mime_type': self.mime_type,
                     'thumb_url': self.thumb_url, 'title': self.title}
        if self.video_width:
            json_dict['video_width'] = self.video_width
        if self.video_height:
            json_dict['video_height'] = self.video_height
        if self.video_duration:
            json_dict['video_duration'] = self.video_duration
        if self.description:
            json_dict['description'] = self.description
        if self.caption:
            json_dict['caption'] = self.caption
        if self.reply_markup:
            json_dict['reply_markup'] = self.reply_markup.to_dic()
        if self.input_message_content:
            json_dict['input_message_content'] = self.input_message_content.to_dic()
        return json.dumps(json_dict)


class InlineQueryResultAudio(JsonSerializable):
    def __init__(self, id, audio_url, title, performer=None, audio_duration=None, reply_markup=None,
                 input_message_content=None):
        self.type = 'audio'
        self.id = id
        self.audio_url = audio_url
        self.title = title
        self.performer = performer
        self.audio_duration = audio_duration
        self.reply_markup = reply_markup
        self.input_message_content = input_message_content

    def to_json(self):
        json_dict = {'type': self.type, 'id': self.id, 'audio_url': self.audio_url, 'title': self.title}
        if self.performer:
            json_dict['performer'] = self.performer
        if self.audio_duration:
            json_dict['audio_duration'] = self.audio_duration
        if self.reply_markup:
            json_dict['reply_markup'] = self.reply_markup.to_dic()
        if self.input_message_content:
            json_dict['input_message_content'] = self.input_message_content.to_dic()
        return json.dumps(json_dict)


class InlineQueryResultVoice(JsonSerializable):
    def __init__(self, id, voice_url, title, performer=None, voice_duration=None, reply_markup=None,
                 input_message_content=None):
        self.type = 'voice'
        self.id = id
        self.voice_url = voice_url
        self.title = title
        self.performer = performer
        self.voice_duration = voice_duration
        self.reply_markup = reply_markup
        self.input_message_content = input_message_content

    def to_json(self):
        json_dict = {'type': self.type, 'id': self.id, 'voice_url': self.voice_url, 'title': self.titlee}
        if self.performer:
            json_dict['performer'] = self.performer
        if self.voice_duration:
            json_dict['voice_duration'] = self.voice_duration
        if self.reply_markup:
            json_dict['reply_markup'] = self.reply_markup.to_dic()
        if self.input_message_content:
            json_dict['input_message_content'] = self.input_message_content.to_dic()
        return json.dumps(json_dict)


class InlineQueryResultDocument(JsonSerializable):
    def __init__(self, id, title, document_url, mime_type, caption=None, description=None, reply_markup=None,
                 input_message_content=None, thumb_url=None, thumb_width=None, thumb_height=None):
        self.type = 'document'
        self.id = id
        self.title = title
        self.document_url = document_url
        self.mime_type = mime_type
        self.caption = caption
        self.description = description
        self.reply_markup = reply_markup
        self.input_message_content = input_message_content
        self.thumb_url = thumb_url
        self.thumb_width = thumb_width
        self.thumb_height = thumb_height

    def to_json(self):
        json_dict = {'type': self.type, 'id': self.id, 'document_url': self.document_url, 'mime_type': self.titlee}
        if self.caption:
            json_dict['caption'] = self.caption
        if self.description:
            json_dict['description'] = self.description
        if self.thumb_url:
            json_dict['thumb_url'] = self.thumb_url
        if self.thumb_width:
            json_dict['thumb_width'] = self.thumb_width
        if self.thumb_height:
            json_dict['thumb_height'] = self.thumb_height
        if self.reply_markup:
            json_dict['reply_markup'] = self.reply_markup.to_dic()
        if self.input_message_content:
            json_dict['input_message_content'] = self.input_message_content.to_dic()
        return json.dumps(json_dict)


class InlineQueryResultLocation(JsonSerializable):
    def __init__(self, id, title, latitude, longitude, reply_markup=None,
                 input_message_content=None, thumb_url=None, thumb_width=None, thumb_height=None):
        self.type = 'location'
        self.id = id
        self.title = title
        self.latitude = latitude
        self.longitude = longitude
        self.reply_markup = reply_markup
        self.input_message_content = input_message_content
        self.thumb_url = thumb_url
        self.thumb_width = thumb_width
        self.thumb_height = thumb_height

    def to_json(self):
        json_dict = {'type': self.type, 'id': self.id, 'latitude': self.latitude, 'longitude': self.longitude,
                     'title': self.title}
        if self.thumb_url:
            json_dict['thumb_url'] = self.thumb_url
        if self.thumb_width:
            json_dict['thumb_width'] = self.thumb_width
        if self.thumb_height:
            json_dict['thumb_height'] = self.thumb_height
        if self.reply_markup:
            json_dict['reply_markup'] = self.reply_markup.to_dic()
        if self.input_message_content:
            json_dict['input_message_content'] = self.input_message_content.to_dic()
        return json.dumps(json_dict)


class InlineQueryResultVenue(JsonSerializable):
    def __init__(self, id, title, latitude, longitude, address, foursquare_id=None, reply_markup=None,
                 input_message_content=None, thumb_url=None, thumb_width=None, thumb_height=None):
        self.type = 'venue'
        self.id = id
        self.title = title
        self.latitude = latitude
        self.longitude = longitude
        self.address = address
        self.foursquare_id = foursquare_id
        self.reply_markup = reply_markup
        self.input_message_content = input_message_content
        self.thumb_url = thumb_url
        self.thumb_width = thumb_width
        self.thumb_height = thumb_height

    def to_json(self):
        json_dict = {'type': self.type, 'id': self.id, 'title': self.title, 'latitude': self.latitude,
                     'longitude': self.longitude, 'address': self.address}
        if self.foursquare_id:
            json_dict['foursquare_id'] = self.foursquare_id
        if self.thumb_url:
            json_dict['thumb_url'] = self.thumb_url
        if self.thumb_width:
            json_dict['thumb_width'] = self.thumb_width
        if self.thumb_height:
            json_dict['thumb_height'] = self.thumb_height
        if self.reply_markup:
            json_dict['reply_markup'] = self.reply_markup.to_dic()
        if self.input_message_content:
            json_dict['input_message_content'] = self.input_message_content.to_dic()
        return json.dumps(json_dict)


class InlineQueryResultContact(JsonSerializable):
    def __init__(self, id, phone_number, first_name, last_name=None, reply_markup=None,
                 input_message_content=None, thumb_url=None, thumb_width=None, thumb_height=None):
        self.type = 'contact'
        self.id = id
        self.phone_number = phone_number
        self.first_name = first_name
        self.last_name = last_name
        self.reply_markup = reply_markup
        self.input_message_content = input_message_content
        self.thumb_url = thumb_url
        self.thumb_width = thumb_width
        self.thumb_height = thumb_height

    def to_json(self):
        json_dict = {'type': self.type, 'id': self.id, 'phone_number': self.phone_number, 'first_name': self.first_name}
        if self.last_name:
            json_dict['last_name'] = self.last_name
        if self.thumb_url:
            json_dict['thumb_url'] = self.thumb_url
        if self.thumb_width:
            json_dict['thumb_width'] = self.thumb_width
        if self.thumb_height:
            json_dict['thumb_height'] = self.thumb_height
        if self.reply_markup:
            json_dict['reply_markup'] = self.reply_markup.to_dic()
        if self.input_message_content:
            json_dict['input_message_content'] = self.input_message_content.to_dic()
        return json.dumps(json_dict)


class BaseInlineQueryResultCached(JsonSerializable):
    def __init__(self):
        self.type = None
        self.id = None
        self.title = None
        self.description = None
        self.caption = None
        self.reply_markup = None
        self.input_message_content = None
        self.payload_dic = {}

    def to_json(self):
        json_dict = self.payload_dic
        json_dict['type'] = self.type
        json_dict['id'] = self.id
        if self.title:
            json_dict['title'] = self.title
        if self.description:
            json_dict['description'] = self.description
        if self.caption:
            json_dict['caption'] = self.caption
        if self.reply_markup:
            json_dict['reply_markup'] = self.reply_markup.to_dic()
        if self.input_message_content:
            json_dict['input_message_content'] = self.input_message_content.to_dic()
        return json.dumps(json_dict)


class InlineQueryResultCachedPhoto(BaseInlineQueryResultCached):
    def __init__(self, id, photo_file_id, title=None, description=None, caption=None, reply_markup=None,
                 input_message_content=None):
        BaseInlineQueryResultCached.__init__(self)
        self.type = 'photo'
        self.id = id
        self.photo_file_id = photo_file_id
        self.title = title
        self.description = description
        self.caption = caption
        self.reply_markup = reply_markup
        self.input_message_content = input_message_content
        self.payload_dic['photo_file_id'] = photo_file_id


class InlineQueryResultCachedGif(BaseInlineQueryResultCached):
    def __init__(self, id, gif_file_id, title=None, description=None, caption=None, reply_markup=None,
                 input_message_content=None):
        BaseInlineQueryResultCached.__init__(self)
        self.type = 'gif'
        self.id = id
        self.gif_file_id = gif_file_id
        self.title = title
        self.description = description
        self.caption = caption
        self.reply_markup = reply_markup
        self.input_message_content = input_message_content
        self.payload_dic['gif_file_id'] = gif_file_id


class InlineQueryResultCachedMpeg4Gif(BaseInlineQueryResultCached):
    def __init__(self, id, mpeg4_file_id, title=None, description=None, caption=None, reply_markup=None,
                 input_message_content=None):
        BaseInlineQueryResultCached.__init__(self)
        self.type = 'mpeg4_gif'
        self.id = id
        self.mpeg4_file_id = mpeg4_file_id
        self.title = title
        self.description = description
        self.caption = caption
        self.reply_markup = reply_markup
        self.input_message_content = input_message_content
        self.payload_dic['mpeg4_file_id'] = mpeg4_file_id


class InlineQueryResultCachedSticker(BaseInlineQueryResultCached):
    def __init__(self, id, sticker_file_id, reply_markup=None, input_message_content=None):
        BaseInlineQueryResultCached.__init__(self)
        self.type = 'sticker'
        self.id = id
        self.sticker_file_id = sticker_file_id
        self.reply_markup = reply_markup
        self.input_message_content = input_message_content
        self.payload_dic['sticker_file_id'] = sticker_file_id


class InlineQueryResultCachedDocument(BaseInlineQueryResultCached):
    def __init__(self, id, document_file_id, title, description=None, caption=None, reply_markup=None,
                 input_message_content=None):
        BaseInlineQueryResultCached.__init__(self)
        self.type = 'document'
        self.id = id
        self.document_file_id = document_file_id
        self.title = title
        self.description = description
        self.caption = caption
        self.reply_markup = reply_markup
        self.input_message_content = input_message_content
        self.payload_dic['document_file_id'] = document_file_id


class InlineQueryResultCachedVideo(BaseInlineQueryResultCached):
    def __init__(self, id, video_file_id, title, description=None, caption=None, reply_markup=None,
                 input_message_content=None):
        BaseInlineQueryResultCached.__init__(self)
        self.type = 'video'
        self.id = id
        self.video_file_id = video_file_id
        self.title = title
        self.description = description
        self.caption = caption
        self.reply_markup = reply_markup
        self.input_message_content = input_message_content
        self.payload_dic['video_file_id'] = video_file_id


class InlineQueryResultCachedVoice(BaseInlineQueryResultCached):
    def __init__(self, id, voice_file_id, title, reply_markup=None, input_message_content=None):
        BaseInlineQueryResultCached.__init__(self)
        self.type = 'voice'
        self.id = id
        self.voice_file_id = voice_file_id
        self.title = title
        self.reply_markup = reply_markup
        self.input_message_content = input_message_content
        self.payload_dic['voice_file_id'] = voice_file_id


class InlineQueryResultCachedAudio(BaseInlineQueryResultCached):
    def __init__(self, id, audio_file_id, reply_markup=None, input_message_content=None):
        BaseInlineQueryResultCached.__init__(self)
        self.type = 'audio'
        self.id = id
        self.audio_file_id = audio_file_id
        self.reply_markup = reply_markup
        self.input_message_content = input_message_content
        self.payload_dic['audio_file_id'] = audio_file_id
