# -*- coding: utf-8 -*-

import requests
import six
from telebot import types
from telebot import util
from telebot import logger

API_URL = "https://api.telegram.org/bot{0}/{1}"
FILE_URL = "https://api.telegram.org/file/bot{0}/{1}"


class RequestExecutorImpl:
    DEFAULT_CONNECT_TIMEOUT = 3.5
    DEFAULT_READ_TIMEOUT = 9999

    def __init__(self, connect_timeout=DEFAULT_CONNECT_TIMEOUT, read_timeout=DEFAULT_READ_TIMEOUT):
        self.timeouts = (connect_timeout, read_timeout)

    def make_request(self, url, method='get', params=None, files=None, response_type='text'):
        logger.debug("{} {} params={} files={}".format(method.upper(), url, params, files))
        response = requests.request(method, url, params=params, files=files, timeout=self.timeouts)
        logger.debug("Server: '{0}'".format(response.text.encode('utf8')))
        response.raise_for_status()  # Raise if response status != 200 OK
        if response_type == 'text':
            return response.text
        elif response_type == 'binary':
            return response.content
        raise ValueError('Invalid response_type "{}"'.format(response_type))


class ApiInterface:

    def __init__(self, token, request_executor, api_url=API_URL, file_url=FILE_URL):
        self.token = token
        self.request_executor = request_executor
        self.api_url = api_url
        self.file_url = file_url

    @staticmethod
    def convert_markup(markup):
        return markup.to_json() if isinstance(markup, types.JsonSerializable) else markup

    @staticmethod
    def convert_inline_results(results):
        """
        Converts a list of InlineQueryResult objects to a json string.
        :param results: list of InlineQueryResult objects
        :rtype: str
        """
        converted_results = [r.to_json() for r in results]
        return '[' + ','.join(converted_results) + ']'

    @staticmethod
    def __merge(*dicts):
        """
        Merges two or more dicts into one, and deletes any keys which' associated values are equal to None.
        :rtype: dict
        """
        d = util.merge_dicts(*dicts)
        copy = d.copy()
        for k, v in six.iteritems(d.copy()):
            if v is None:
                del copy[k]
        return copy

    def make_request(self, method_name, params=None, files=None, method='get', response_type='text'):
        if params is not None and 'reply_markup' in params:
            params['reply_markup'] = self.convert_markup(params['reply_markup'])
        request_url = self.api_url.format(self.token, method_name)
        try:
            response = self.request_executor.make_request(request_url, method, params, files, response_type)
            return response
        except Exception as e:
            raise ApiException(e.message, method_name)

    def get_me(self):
        return self.make_request('getMe')

    def get_file(self, file_id):
        return self.make_request('getFile', params={'file_id': file_id})

    def download_file(self, file_path):
        url = self.file_url.format(self.token, file_path)
        return self.make_request(url, response_type='binary')

    def send_message(self, chat_id, text, **kwargs):
        payload = {'chat_id': str(chat_id), 'text': text}
        return self.make_request('sendMessage', self.__merge(payload, kwargs), method='post')

    def set_webhook(self, url="", certificate=None):
        files = None
        if certificate is not None:
            files = {'certificate': certificate}
        return self.make_request('setWebhook', params={'url': url}, files=files)

    def get_updates(self, **kwargs):
        return self.make_request('getUpdates', params=kwargs)

    def get_user_profile_photos(self, user_id, **kwargs):
        params = self.__merge({'user_id': user_id}, kwargs)
        return self.make_request('getUserProfilePhotos', params=params)

    def forward_message(self, chat_id, from_chat_id, message_id, **kwargs):
        params = self.__merge({
            'chat_id': chat_id,
            'from_chat_id': from_chat_id,
            'message_id': message_id
        }, kwargs)
        return self.make_request('forwardMessage', params=params)

    def send_photo(self, chat_id, photo, **kwargs):
        params = {'chat_id': chat_id}
        files = None
        if util.is_string(photo):
            files = {'photo': photo}
        else:
            params['photo'] = photo
        params = self.__merge(params, kwargs)
        return self.make_request('sendPhoto', params=params, files=files)

    def send_location(self, chat_id, latitude, longitude, **kwargs):
        params = self.__merge({'chat_id': chat_id, 'latitude': latitude, 'longitude': longitude}, kwargs)
        return self.make_request('sendLocation', params=params)

    def send_venue(self, chat_id, latitude, longitude, title, address, **kwargs):
        params = {'chat_id': chat_id, 'latitude': latitude, 'longitude': longitude, 'title': title, 'address': address}
        params.update(kwargs)
        return self.make_request('sendVenue', params=params)

    def send_contact(self, chat_id, phone_number, first_name, **kwargs):
        params = self.__merge({'chat_id': chat_id, 'phone_number': phone_number, 'first_name': first_name}, kwargs)
        return self.make_request('sendContact', params=params)

    def send_chat_action(self, chat_id, action):
        return self.make_request('sendChatAction', params={'chat_id': chat_id, 'action': action})

    def send_video(self, chat_id, video, **kwargs):
        return self.send_data('video', chat_id, video, **kwargs)

    def send_voice(self, chat_id, voice, **kwargs):
        return self.send_data('voice', chat_id, voice, **kwargs)

    def send_audio(self, chat_id, audio, **kwargs):
        return self.send_data('audio', chat_id, audio, **kwargs)

    def send_sticker(self, chat_id, sticker, **kwargs):
        return self.send_data('sticker', chat_id, sticker, **kwargs)

    def send_document(self, chat_id, document, **kwargs):
        return self.send_data('document', chat_id, document, **kwargs)

    def send_data(self, data_type, chat_id, data, **kwargs):
        params = {'chat_id': chat_id}
        files = None
        if not util.is_string(data):
            files = {data_type: data}
        else:
            params[data_type] = data
        params = self.__merge(params, kwargs)
        return self.make_request(self.get_method_by_type(data_type), params=params, files=files, method='post')

    @staticmethod
    def get_method_by_type(data_type):
        return {
            'document': 'sendDocument',
            'sticker': 'sendSticker',
            'video': 'sendVideo',
            'voice': 'sendVoice',
            'audio': 'sendAudio'
        }[data_type]

    def kick_chat_member(self, chat_id, user_id):
        return self.make_request('kickChatMember', params={'chat_id': chat_id, 'user_id': user_id}, method='post')

    def unban_chat_member(self, chat_id, user_id):
        return self.make_request('unbanChatMember', params={'chat_id': chat_id, 'user_id': user_id}, method='post')

    def edit_message_text(self, text, **kwargs):
        params = self.__merge({'text': text}, kwargs)
        return self.make_request('editMessageText', params=params)

    def edit_message_caption(self, caption, **kwargs):
        params = self.__merge({'caption': caption}, kwargs)
        return self.make_request('editMessageCaption', params=params)

    def edit_message_reply_markup(self, **kwargs):
        return self.make_request('editMessageReplyMarkup', params=kwargs)

    def answer_callback_query(self, callback_query_id, **kwargs):
        params = self.__merge({'callback_query_id': callback_query_id}, kwargs)
        return self.make_request('answerCallbackQuery', params=params)

    def answer_inline_query(self, inline_query_id, results, **kwargs):
        params = self.__merge({
            'inline_query_id': inline_query_id,
            'results': self.convert_inline_results(results)
        }, kwargs)
        return self.make_request('answerInlineQuery', params=params, method='post')


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
