# -*- coding: utf-8 -*-

import json

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
        json_dic = {'latitude': self.latitude, 'longitude': self.longitude}
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
        json_dic = {'phone_number': self.phone_number, 'first_name': self.first_name}
        if self.last_name:
            json_dic['last_name'] = self.last_name
        return json_dic


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
        json_dict = {'type': self.type, 'id': self.id, 'voice_url': self.voice_url, 'title': self.title}
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
        json_dict = {'type': self.type, 'id': self.id, 'document_url': self.document_url, 'mime_type': self.title}
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
