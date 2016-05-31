# -*- coding: utf-8 -*-

import requests

import telebot.util as util
import telebot.telegram_types as types
from telebot.util import logger

API_URL = "https://api.telegram.org/bot{0}/{1}"
FILE_URL = "https://api.telegram.org/file/bot{0}/{1}"


class DefaultRequestExecutor:
    DEFAULT_CONNECT_TIMEOUT = 3.5
    DEFAULT_READ_TIMEOUT = 9999

    def __init__(self, connect_timeout=DEFAULT_CONNECT_TIMEOUT, read_timeout=DEFAULT_READ_TIMEOUT):
        self.timeouts = (connect_timeout, read_timeout)

    def make_request(self, url, method='get', params=None, files=None, response_type='text'):
        logger.debug("{0} {1} params={2} files={3}".format(method.upper(), url, params, files))
        response = requests.request(method, url, params=params, files=files, timeout=self.timeouts)
        logger.debug("Server: '{0}'".format(response.text.encode('utf8')))
        # response.raise_for_status()  # Raise if response status != 200 OK
        if response_type == 'text':
            return response.text
        elif response_type == 'binary':
            return response.content
        elif response_type == 'json':
            return response.json()
        raise ValueError('Invalid response_type "{0}"'.format(response_type))

    def __call__(self, *args, **kwargs):
        return self.make_request(*args, **kwargs)


class TelegramApiInterface:
    def __init__(self, token, request_executor, api_url=API_URL, file_url=FILE_URL):
        self.token = token
        self.request_executor = request_executor
        self.api_url = api_url
        self.file_url = file_url

    @staticmethod
    def convert_markup(markup):
        return types.to_json(markup)

    @staticmethod
    def convert_inline_results(results):
        """
        Converts a list of InlineQueryResult objects to a json string.
        :param results: list of InlineQueryResult objects
        :rtype: str
        """
        converted_results = [types.to_json(r) for r in results]
        return '[' + ','.join(converted_results) + ']'

    def make_request(self, method_name, params=None, files=None, method='get', response_type='json'):
        request_url = self.api_url.format(self.token, method_name)
        try:
            response = self.request_executor(request_url,
                                             method=method, params=params, files=files, response_type=response_type)
            return response
        except Exception as e:
            raise ApiException(repr(e), method_name)

    def make_json_request(self, method_name, params=None, files=None, method='post', return_type=None):
        if params is not None and 'reply_markup' in params:
            params['reply_markup'] = self.convert_markup(params['reply_markup'])

        response = self.make_request(method_name, params, files, method, response_type='json')
        if not response['ok']:
            raise ApiException('Error code: {error_code}, description: "{description}"'.format(**response), method)

        if return_type is not None and issubclass(return_type, types.JsonDeserializable):
            return types.de_json(return_type, response['result'])
        return response['result']

    def get_updates(self, **kwargs):
        """
        Use this method to receive incoming updates using long polling (wiki). An Array of Update objects is returned.
        :param offset: Integer. Identifier of the first update to be returned.
        :param limit: Integer. Limits the number of updates to be retrieved.
        :param timeout: Integer. Timeout in seconds for long polling.
        :return: list of Updates
        """
        json_updates = self.make_json_request('getUpdates', params=util.xmerge(kwargs))
        return [types.de_json(types.Update, update) for update in json_updates]

    def get_me(self):
        return self.make_json_request('getMe', return_type=types.User)

    def get_file(self, file_id):
        return self.make_json_request('getFile', params={'file_id': file_id}, return_type=types.File)

    def download_file(self, file_path):
        url = self.file_url.format(self.token, file_path)
        return self.make_request(url, response_type='binary')

    def send_message(self, chat_id, text, **kwargs):
        """
        Use this method to send text messages.

        Warning: Do not send more than about 5000 characters each message, otherwise you'll risk an HTTP 414 error.
        If you must send more than 5000 characters, use the split_string function in apihelper.py.

        :param chat_id:
        :param text:
        :param disable_web_page_preview: (optional)
        :param reply_to_message_id: (optional)
        :param reply_markup: (optional)
        :param parse_mode: (optional)
        :param disable_notification:(optional) Boolean. Sends the message silently.
        :return: :class:`Message <Message>` object
        :rtype types.Message
        """
        payload = {'chat_id': str(chat_id), 'text': text}
        return self.make_json_request('sendMessage', params=util.xmerge(payload, kwargs), return_type=types.Message)

    def set_webhook(self, certificate=None, **kwargs):
        files = None
        if certificate is not None:
            files = {'certificate': certificate}
        return self.make_json_request('setWebhook', params=util.xmerge(kwargs), files=files)

    def get_user_profile_photos(self, user_id, **kwargs):
        """
        Retrieves the user profile photos of the person with 'user_id'
        See https://core.telegram.org/bots/api#getuserprofilephotos
        :param user_id:
        :param offset:
        :param limit:
        :return: API reply.
        """
        params = util.xmerge({'user_id': user_id}, kwargs)
        return self.make_json_request('getUserProfilePhotos', params=params, return_type=types.UserProfilePhotos)

    def forward_message(self, chat_id, from_chat_id, message_id, **kwargs):
        """
        Use this method to forward messages of any kind.
        :param disable_notification:
        :param chat_id: which chat to forward
        :param from_chat_id: which chat message from
        :param message_id: message id
        :return: API reply.
        """
        params = util.xmerge({
            'chat_id': chat_id,
            'from_chat_id': from_chat_id,
            'message_id': message_id
        }, kwargs)
        return self.make_json_request('forwardMessage', params=params, return_type=types.Message)

    def send_location(self, chat_id, latitude, longitude, **kwargs):
        """
        Use this method to send point on the map.
        :param disable_notification:
        :param chat_id:
        :param latitude:
        :param longitude:
        :param reply_to_message_id:
        :param reply_markup:
        :return: API reply.
        """
        params = util.xmerge({'chat_id': chat_id, 'latitude': latitude, 'longitude': longitude}, kwargs)
        return self.make_json_request('sendLocation', params=params, return_type=types.Message)

    def send_venue(self, chat_id, latitude, longitude, title, address, **kwargs):
        """
        Use this method to send information about a venue.
        :param chat_id: Integer or String : Unique identifier for the target chat or username of the target channel
        :param latitude: Float : Latitude of the venue
        :param longitude: Float : Longitude of the venue
        :param title: String : Name of the venue
        :param address: String : Address of the venue
        :param foursquare_id: String : Foursquare identifier of the venue
        :param disable_notification:
        :param reply_to_message_id:
        :param reply_markup:
        :return:
        """
        params = {'chat_id': chat_id, 'latitude': latitude, 'longitude': longitude, 'title': title, 'address': address}
        params = util.xmerge(params, kwargs)
        return self.make_json_request('sendVenue', params=params, return_type=types.Message)

    def send_contact(self, chat_id, phone_number, first_name, **kwargs):
        params = util.xmerge({'chat_id': chat_id, 'phone_number': phone_number, 'first_name': first_name}, kwargs)
        return self.make_json_request('sendContact', params=params, return_type=types.Message)

    def send_chat_action(self, chat_id, action):
        """
        Use this method when you need to tell the user that something is happening on the bot's side.
        The status is set for 5 seconds or less (when a message arrives from your bot, Telegram clients clear
        its typing status).
        :param chat_id:
        :param action:  One of the following strings: 'typing', 'upload_photo', 'record_video', 'upload_video',
                        'record_audio', 'upload_audio', 'upload_document', 'find_location'.
        :return: API reply. :type: boolean
        """
        return self.make_json_request('sendChatAction', params={'chat_id': chat_id, 'action': action})

    def send_photo(self, chat_id, photo, **kwargs):
        """
        Use this method to send photos.
        :param disable_notification:
        :param chat_id:
        :param photo:
        :param caption:
        :param reply_to_message_id:
        :param reply_markup:
        :return: API reply.
        """
        return self.send_data('photo', chat_id, photo, **kwargs)

    def send_video(self, chat_id, video, **kwargs):
        """
        Use this method to send video files, Telegram clients support mp4 videos.
        :param video: string or file
        :param disable_notification:
        :param chat_id: Integer : Unique identifier for the message recipient — User or GroupChat id
        :param data: InputFile or String : Video to send. You can either pass a file_id as String to resend a video that is already on the Telegram server
        :param duration: Integer : Duration of sent video in seconds
        :param caption: String : Video caption (may also be used when resending videos by file_id).
        :param reply_to_message_id:
        :param reply_markup:
        :return:
        """
        return self.send_data('video', chat_id, video, **kwargs)

    def send_voice(self, chat_id, voice, **kwargs):
        """
        Use this method to send audio files, if you want Telegram clients to display the file as a playable voice message.
        :param disable_notification:
        :param chat_id:Unique identifier for the message recipient.
        :param voice:
        :param duration:Duration of sent audio in seconds
        :param reply_to_message_id:
        :param reply_markup:
        :return: Message
        """
        return self.send_data('voice', chat_id, voice, **kwargs)

    def send_audio(self, chat_id, audio, **kwargs):
        """
        Use this method to send audio files, if you want Telegram clients to display them in the music player. Your audio must be in the .mp3 format.
        :param disable_notification:
        :param chat_id:Unique identifier for the message recipient
        :param audio:Audio file to send.
        :param duration:Duration of the audio in seconds
        :param performer:Performer
        :param title:Track name
        :param reply_to_message_id:If the message is a reply, ID of the original message
        :param reply_markup:
        :return: Message
        """
        return self.send_data('audio', chat_id, audio, **kwargs)

    def send_sticker(self, chat_id, sticker, **kwargs):
        """
        Use this method to send .webp stickers.
        :param disable_notification:
        :param chat_id:
        :param data:
        :param reply_to_message_id:
        :param reply_markup:
        :return: API reply.
        """
        return self.send_data('sticker', chat_id, sticker, **kwargs)

    def send_document(self, chat_id, document, **kwargs):
        """
        Use this method to send general files.
        :param chat_id:
        :param data:
        :param reply_to_message_id:
        :param reply_markup:
        :return: API reply.
        """
        return self.send_data('document', chat_id, document, **kwargs)

    def send_data(self, data_type, chat_id, data, **kwargs):
        params = {'chat_id': chat_id}
        files = None
        if not util.is_string(data):
            files = {data_type: data}
        else:
            params[data_type] = data
        params = util.xmerge(params, kwargs)
        method = self.get_method_by_type(data_type)
        return self.make_json_request(method, params=params, files=files, return_type=types.Message)

    @staticmethod
    def get_method_by_type(data_type):
        return {
            'document': 'sendDocument',
            'sticker': 'sendSticker',
            'video': 'sendVideo',
            'voice': 'sendVoice',
            'audio': 'sendAudio',
            'photo': 'sendPhoto'
        }[data_type]

    def kick_chat_member(self, chat_id, user_id):
        """
        Use this method to kick a user from a group or a supergroup.
        :param chat_id: Int or string : Unique identifier for the target group or username of the target supergroup
        :param user_id: Int : Unique identifier of the target user
        :return: types.Message
        """
        return self.make_json_request('kickChatMember', params={'chat_id': chat_id, 'user_id': user_id})

    def leave_chat(self, chat_id):
        """
        Use this method for your bot to leave a group, supergroup or channel
        :param chat_id: Unique identifier for the target chat or username of the target supergroup or channel
            (in the format @channelusername)
        :return: True on success.
        """
        return self.make_json_request('leaveChat', params={'chat_id': chat_id})

    def unban_chat_member(self, chat_id, user_id):
        return self.make_json_request('unbanChatMember', params={'chat_id': chat_id, 'user_id': user_id})

    def get_chat(self, chat_id):
        """
        Use this method to get up to date information about the chat (current name of the user for one-on-one
        conversations, current username of a user, group or channel, etc.).
        :param chat_id: Unique identifier for the target chat or username of the target supergroup or channel
            (in the format @channelusername)
        :return: a Chat object on success
        :rtype: types.Chat
        """
        return self.make_json_request('getChat', params={'chat_id': chat_id})

    def get_chat_administrators(self, chat_id):
        """
        Use this method to get a list of administrators in a chat. On success, returns an Array of ChatMember objects
        that contains information about all chat administrators except other bots. If the chat is a group or a
        supergroup and no administrators were appointed, only the creator will be returned.
        :param chat_id: Unique identifier for the target chat or username of the target supergroup or channel
            (in the format @channelusername)
        :return: Array of ChatMember objects
        """
        response = self.make_json_request('getChatAdministrators', params={'chat_id': chat_id})
        return types.de_json_array(types.ChatMember, response)

    def get_chat_members_count(self, chat_id):
        """
        Use this method to get the number of members in a chat
        :param chat_id: Unique identifier for the target chat or username of the target supergroup or channel
            (in the format @channelusername)
        :return: Number of chat members
        :rtype integer
        """
        return self.make_json_request('getChatMembersCount', params={'chat_id': chat_id})

    def get_chat_member(self, chat_id, user_id):
        """
        Use this method to get information about a member of a chat.
        :param chat_id: Unique identifier for the target chat or username of the target supergroup or channel
            (in the format @channelusername)
        :param user_id: Unique identifier of the target user
        :return: ChatMember on success
        :rtype: types.ChatMember
        """
        return self.make_json_request('getChatMember', params={'chat_id': chat_id, 'user_id': user_id},
                                      return_type=types.ChatMember)

    def edit_message_text(self, text, **kwargs):
        params = util.xmerge({'text': text}, kwargs)
        response = self.make_json_request('editMessageText', params=params)
        return response if type(response) == bool else types.de_json(types.Message, response)

    def edit_message_caption(self, caption, **kwargs):
        params = util.xmerge({'caption': caption}, kwargs)
        return self.make_json_request('editMessageCaption', params=params, return_type=types.Message)

    def edit_message_reply_markup(self, **kwargs):
        return self.make_json_request('editMessageReplyMarkup', params=util.xmerge(kwargs), return_type=types.Message)

    def answer_callback_query(self, callback_query_id, **kwargs):
        """
        Use this method to send answers to callback queries sent from inline keyboards. The answer will be displayed to
        the user as a notification at the top of the chat screen or as an alert.
        :param callback_query_id:
        :param text:
        :param show_alert:
        :return:
        """
        params = util.xmerge({'callback_query_id': callback_query_id}, kwargs)
        return self.make_json_request('answerCallbackQuery', params=params)

    def answer_inline_query(self, inline_query_id, results, **kwargs):
        """
        Use this method to send answers to an inline query. On success, True is returned.
        No more than 50 results per query are allowed.
        :param inline_query_id: Unique identifier for the answered query
        :param results: Array of results for the inline query
        :param cache_time: The maximum amount of time in seconds that the result of the inline query may be cached on the server.
        :param is_personal: Pass True, if results may be cached on the server side only for the user that sent the query.
        :param next_offset: Pass the offset that a client should send in the next query with the same text to receive more results.
        :param switch_pm_parameter: If passed, clients will display a button with specified text that switches the user
         to a private chat with the bot and sends the bot a start message with the parameter switch_pm_parameter
        :param switch_pm_text: 	Parameter for the start message sent to the bot when user presses the switch button
        :return: True means success.
        """
        params = util.xmerge({
            'inline_query_id': inline_query_id,
            'results': self.convert_inline_results(results)
        }, kwargs)
        return self.make_json_request('answerInlineQuery', params=params)


class ApiException(Exception):
    """
    This class represents an Exception thrown when a call to the Telegram API fails.
    In addition to an informative message, it has a `function_name` and a `result` attribute, which respectively
    contain the name of the failed function and the returned result that made the function to be considered  as
    failed.
    """

    def __init__(self, msg, function_name=None, result=None):
        super(ApiException, self).__init__("A request to the Telegram API was unsuccessful. {0}".format(msg))
        self.function_name = function_name
        self.result = result
