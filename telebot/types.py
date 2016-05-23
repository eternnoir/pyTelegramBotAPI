# -*- coding: utf-8 -*-

import json
import six

import telebot.util as util


def de_json(cls, json_type):
    if not issubclass(cls, JsonDeserializable):
        raise ValueError("{0} is not a subclass of JsonDeserializable".format(cls))
    if not json_type:
        return None
    if util.is_string(json_type):
        json_type = json.loads(json_type)
    return cls(**json_type)


def de_json_array(cls, json_array):
    if not json_array:
        return None
    return [de_json(cls, e) for e in json_array]


def to_dict(obj):
    if not obj:
        return None
    if not isinstance(obj, Dictionaryable):
        return obj
    return util.obj_to_dict(obj)


def to_json(obj):
    return json.dumps(to_dict(obj))


class Dictionaryable:
    """
    Subclasses of this class are guaranteed to be able to be converted to dictionary.
    All subclasses of this class must override to_dict.
    """
    pass


class JsonDeserializable:
    """
    Subclasses of this class are guaranteed to be able to be created from a json-style dict or json formatted string
    using de_json().
    """
    pass


class Update(JsonDeserializable):

    @util.required('update_id')
    def __init__(self, update_id=None, message=None, edited_message=None, inline_query=None,
                 chosen_inline_result=None, callback_query=None):
        self.update_id = update_id
        self.message = de_json(Message, message)
        self.edited_message = de_json(Message, edited_message)
        self.inline_query = de_json(InlineQuery, inline_query)
        self.chosen_inline_result = de_json(ChosenInlineResult, chosen_inline_result)
        self.callback_query = de_json(CallbackQuery, callback_query)


class User(JsonDeserializable):

    @util.required('id', 'first_name')
    def __init__(self, id=None, first_name=None, last_name=None, username=None):
        self.id = id
        self.first_name = first_name
        self.username = username
        self.last_name = last_name


class Chat(JsonDeserializable):

    @util.required('id', 'type')
    def __init__(self, id=None, type=None, title=None, username=None, first_name=None, last_name=None):
        self.type = type
        self.last_name = last_name
        self.first_name = first_name
        self.username = username
        self.id = id
        self.title = title


class ChatMember(JsonDeserializable):

    @util.required('user', 'status')
    def __init__(self, user=None, status=None):
        self.user = user
        self.status = status


class Message(JsonDeserializable):
    CONTENT_TYPES = ['text', 'audio', 'document', 'photo', 'sticker', 'video', 'voice', 'contact',
                     'location', 'venue', 'new_chat_member', 'left_chat_member']

    @util.translate({'from': 'from_user'})
    @util.required('message_id', 'date', 'chat')
    def __init__(self, message_id=None, from_user=None, date=None, chat=None,
                 forward_from=None, forward_from_chat=None, forward_date=None, reply_to_message=None, edit_date=None,
                 text=None, entities=None, audio=None, document=None, photo=None, sticker=None, video=None,
                 voice=None, caption=None, contact=None, location=None, venue=None, new_chat_member=None,
                 left_chat_member=None, new_chat_title=None, new_chat_photo=None, delete_chat_photo=None,
                 group_chat_created=None, supergroup_chat_created=None, channel_chat_created=None,
                 migrate_to_chat_id=None, migrate_from_chat_id=None, pinned_message=None):
        self.message_id = message_id
        self.from_user = de_json(User, from_user)
        self.date = date
        self.chat = de_json(Chat, chat)
        self.forward_from = de_json(User, forward_from)
        self.forward_from_chat = de_json(Chat, forward_from_chat)
        self.forward_date = forward_date
        self.reply_to_message = de_json(Message, reply_to_message)
        self.edit_date = edit_date
        self.text = text
        self.entities = de_json_array(MessageEntity, entities)
        self.audio = de_json(Audio, audio)
        self.document = de_json(Document, document)
        self.photo = de_json_array(PhotoSize, photo)
        self.sticker = de_json(Sticker, sticker)
        self.video = de_json(Video, video)
        self.voice = de_json(Voice, voice)
        self.caption = caption
        self.contact = de_json(Contact, contact)
        self.location = de_json(Location, location)
        self.venue = de_json(Venue, venue)
        self.new_chat_member = de_json(User, new_chat_member)
        self.left_chat_member = de_json(User, left_chat_member)
        self.new_chat_title = new_chat_title
        self.new_chat_photo = de_json_array(PhotoSize, new_chat_photo)
        self.delete_chat_photo = delete_chat_photo
        self.group_chat_created = group_chat_created
        self.supergroup_chat_created = supergroup_chat_created
        self.channel_chat_created = channel_chat_created
        self.migrate_to_chat_id = migrate_to_chat_id
        self.migrate_from_chat_id = migrate_from_chat_id
        self.pinned_message = de_json(Message, pinned_message)

        self.content_type = self.determine_content_type()

    def determine_content_type(self):
        for content_type in self.CONTENT_TYPES:
            if getattr(self, content_type) is not None:
                return content_type


class MessageEntity(JsonDeserializable):
    TYPES = ['mention', 'hashtag', 'bot_command', 'url', 'email', 'bold', 'italic',
             'code', 'pre', 'text_link', 'text_mention']

    @util.required('type', 'offset', 'length')
    def __init__(self, type=None, offset=None, length=None, url=None, user=None):
        self.type = type
        self.offset = offset
        self.length = length
        self.url = url
        self.user = de_json(User, user)


class PhotoSize(JsonDeserializable):

    @util.required('file_id', 'width', 'height')
    def __init__(self, file_id=None, width=None, height=None, file_size=None):
        self.file_size = file_size
        self.height = height
        self.width = width
        self.file_id = file_id


class Audio(JsonDeserializable):

    @util.required('file_id', 'duration')
    def __init__(self, file_id=None, duration=None, performer=None, title=None, mime_type=None, file_size=None):
        self.file_id = file_id
        self.duration = duration
        self.performer = performer
        self.title = title
        self.mime_type = mime_type
        self.file_size = file_size


class Document(JsonDeserializable):

    @util.required('file_id')
    def __init__(self, file_id=None, thumb=None, file_name=None, mime_type=None, file_size=None):
        self.file_id = file_id
        self.thumb = de_json(PhotoSize, thumb)
        self.file_name = file_name
        self.mime_type = mime_type
        self.file_size = file_size


class Sticker(JsonDeserializable):

    @util.required('file_id', 'width', 'height')
    def __init__(self, file_id=None, width=None, height=None, thumb=None, emoji=None, file_size=None):
        self.file_id = file_id
        self.width = width
        self.height = height
        self.thumb = de_json(PhotoSize, thumb)
        self.emoji = emoji
        self.file_size = file_size


class Video(JsonDeserializable):

    @util.required('file_id', 'width', 'height', 'duration')
    def __init__(self, file_id=None, width=None, height=None, duration=None, thumb=None,
                 mime_type=None, file_size=None):
        self.file_id = file_id
        self.width = width
        self.height = height
        self.duration = duration
        self.thumb = de_json(PhotoSize, thumb)
        self.mime_type = mime_type
        self.file_size = file_size


class Voice(JsonDeserializable):

    @util.required('file_id', 'duration')
    def __init__(self, file_id=None, duration=None, mime_type=None, file_size=None):
        self.file_id = file_id
        self.duration = duration
        self.mime_type = mime_type
        self.file_size = file_size


class Contact(JsonDeserializable):

    @util.required('phone_number', 'first_name')
    def __init__(self, phone_number=None, first_name=None, last_name=None, user_id=None):
        self.phone_number = phone_number
        self.first_name = first_name
        self.last_name = last_name
        self.user_id = user_id


class Location(JsonDeserializable):

    @util.required('longitude', 'latitude')
    def __init__(self, longitude=None, latitude=None):
        self.longitude = longitude
        self.latitude = latitude


class Venue(JsonDeserializable):

    @util.required('location', 'title', 'address')
    def __init__(self, location=None, title=None, address=None, foursquare_id=None):
        self.location = de_json(Location, location)
        self.title = title
        self.address = address
        self.foursquare_id = foursquare_id


class UserProfilePhotos(JsonDeserializable):
    @util.required('total_count', 'photos')
    def __init__(self, total_count=None, photos=None):
        self.total_count = total_count
        self.photos = [de_json_array(PhotoSize, p) for p in photos]


class File(JsonDeserializable):

    @util.required('file_id')
    def __init__(self, file_id=None, file_size=None, file_path=None):
        self.file_id = file_id
        self.file_size = file_size
        self.file_path = file_path


class ForceReply(Dictionaryable):
    def __init__(self, selective=None):
        self.selective = selective


class ReplyKeyboardHide(Dictionaryable):
    def __init__(self, selective=None):
        self.selective = selective


class ReplyKeyboardMarkup(Dictionaryable):
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


class KeyboardButton(Dictionaryable):
    def __init__(self, text, request_contact=None, request_location=None):
        self.text = text
        self.request_contact = request_contact
        self.request_location = request_location


class InlineKeyboardMarkup(Dictionaryable):
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
            row.append(to_dict(button))
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
            btn_array.append(to_dict(button))
        self.keyboard.append(btn_array)
        return self


class InlineKeyboardButton(Dictionaryable):
    def __init__(self, text, url=None, callback_data=None, switch_inline_query=None):
        self.text = text
        self.url = url
        self.callback_data = callback_data
        self.switch_inline_query = switch_inline_query


class CallbackQuery(JsonDeserializable):

    @util.required('id', 'from_user', 'data')
    def __init__(self, id=None, from_user=None, data=None, message=None, inline_message_id=None):
        self.id = id
        self.from_user = de_json(User, from_user)
        self.message = de_json(Message, message)
        self.data = data
        self.inline_message_id = inline_message_id


class InlineQuery(JsonDeserializable):

    @util.required('id', 'from_user', 'query', 'offset')
    def __init__(self, id=None, from_user=None, query=None, offset=None, location=None):
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
        self.from_user = de_json(User, from_user)
        self.query = query
        self.offset = offset
        self.location = de_json(Location, location)


class ChosenInlineResult(JsonDeserializable):

    @util.required('result_id', 'from_user', 'query')
    def __init__(self, result_id=None, from_user=None, query=None, location=None, inline_message_id=None):
        """
        This object represents a result of an inline query
        that was chosen by the user and sent to their chat partner.
        :param result_id: string The unique identifier for the result that was chosen.
        :param from_user: User The user that chose the result.
        :param query: String The query that was used to obtain the result.
        :return: ChosenInlineResult Object.
        """
        self.result_id = result_id
        self.from_user = de_json(User, from_user)
        self.query = query
        self.location = de_json(Location, location)
        self.inline_message_id = inline_message_id


class InputTextMessageContent(Dictionaryable):
    def __init__(self, message_text, parse_mode=None, disable_web_page_preview=None):
        self.message_text = message_text
        self.parse_mode = parse_mode
        self.disable_web_page_preview = disable_web_page_preview


class InputLocationMessageContent(Dictionaryable):
    def __init__(self, latitude, longitude):
        self.latitude = latitude
        self.longitude = longitude


class InputVenueMessageContent(Dictionaryable):
    def __init__(self, latitude, longitude, title, address, foursquare_id=None):
        self.latitude = latitude
        self.longitude = longitude
        self.title = title
        self.address = address
        self.foursquare_id = foursquare_id


class InputContactMessageContent(Dictionaryable):
    def __init__(self, phone_number, first_name, last_name=None):
        self.phone_number = phone_number
        self.first_name = first_name
        self.last_name = last_name


class InlineQueryResultFactory:
    TYPES = [
        'article', 'audio', 'contact', 'document', 'gif', 'location',
        'mpeg4_gif', 'photo', 'venue', 'video', 'voice'
    ]
    CACHED_TYPES = ['photo', 'gif', 'mpeg4_gif', 'sticker', 'document', 'video', 'voice', 'audio']
    __CACHED_FILE_ID_KEYS = {
        'photo': 'photo_file_id',
        'gif': 'gif_file_id',
        'mpeg4_gif': 'mpeg4_file_id',
        'sticker': 'sticker_file_id',
        'document': 'document_file_id',
        'video': 'video_file_id',
        'voice': 'voice_file_id',
        'audio': 'audio_file_id'
    }

    def __init__(self):
        raise NotImplementedError('Instantiation not allowed')

    @staticmethod
    def create_result(type, id, **kwargs):
        if type not in InlineQueryResultFactory.TYPES:
            raise ValueError('Unknown type: {0}. Known types: {1}'.format(type, InlineQueryResultFactory.TYPES))

        json_dict = kwargs
        json_dict['type'] = type
        json_dict['id'] = id

        for k, v in six.iteritems(json_dict):
            json_dict[k] = to_dict(v)

        return json_dict

    @staticmethod
    def create_cached_result(type, id, file_id, **kwargs):
        if type not in InlineQueryResultFactory.CACHED_TYPES:
            raise ValueError(
                'Unknown cached type: {0}. Known types: {1}'.format(type, InlineQueryResultFactory.CACHED_TYPES)
            )

        json_dict = kwargs
        json_dict['type'] = type
        json_dict['id'] = id
        json_dict[InlineQueryResultFactory.__CACHED_FILE_ID_KEYS[type]] = file_id

        for k, v in six.iteritems(json_dict):
            json_dict[k] = to_dict(v)

        return json_dict
