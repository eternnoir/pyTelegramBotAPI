# -*- coding: utf-8 -*-

import requests
import telebot
from telebot import types
from telebot import util

merge = util.merge_dicts
logger = telebot.logger

API_URL = "https://api.telegram.org/bot{0}/{1}"
FILE_URL = "https://api.telegram.org/file/bot{0}/{1}"

# CONNECT_TIMEOUT = 3.5
# READ_TIMEOUT = 9999


class RequestExecutorImpl:
    DEFAULT_CONNECT_TIMEOUT = 3.5
    DEFAULT_READ_TIMEOUT = 9999

    def __init__(self, connect_timeout=DEFAULT_CONNECT_TIMEOUT, read_timeout=DEFAULT_READ_TIMEOUT):
        self.timeouts = (connect_timeout, read_timeout)

    def make_request(self, url, method='get', params=None, files=None):
        logger.debug("{} {} params={} files={}".format(method.upper(), url, params, files))
        response = requests.request(method, url, params=params, files=files, timeout=self.timeouts)
        logger.debug("Server: '{0}'".format(response.text.encode('utf8')))
        if response.status_code != 200:
            msg = 'The server returned HTTP {0} {1}. Response body:\n[{2}]' \
                .format(response.status_code, response.reason, response.text.encode('utf8'))
            raise ApiException(msg)
        return response


class ApiInterface:

    def __init__(self, token, request_executor, api_url=API_URL, file_url=FILE_URL):
        self.token = token
        self.request_executor = request_executor
        self.api_url = api_url
        self.file_url = file_url

    def make_request(self, method_name, params=None, files=None, method='get'):
        request_url = self.api_url.format(self.token, method_name)
        response = self.request_executor.make_request(request_url, method, params, files)
        return response

    def get_me(self):
        return self.make_request('getMe')

    def get_file(self, file_id):
        return self.make_request('getFile', params={'file_id': file_id})

    def download_file(self, file_path):
        url = self.file_url.format(self.token, file_path)
        result = self.request_executor.make_request(url)
        return result.content

    def send_message(self, chat_id, text, **kwargs):
        payload = {'chat_id': str(chat_id), 'text': text}
        return self.make_request('sendMessage', merge(payload, kwargs), method='post')

    def set_webhook(self, url="", certificate=None):
        files = None
        if certificate is not None:
            files = {'certificate': certificate}
        return self.make_request('setWebhook', params={'url': url}, files=files)

    def get_updates(self, **kwargs):
        return self.make_request('getUpdates', params=kwargs)

    def get_user_profile_photos(self, user_id, **kwargs):
        params = merge({'user_id': user_id}, kwargs)
        return self.make_request('getUserProfilePhotos', params=params)

    def forward_message(self, chat_id, from_chat_id, message_id, **kwargs):
        params = merge({
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
        params = merge(params, kwargs)
        return self.make_request('sendPhoto', params=params, files=files)

    def send_location(self, chat_id, latitude, longitude, **kwargs):
        params = merge({'chat_id': chat_id, 'latitude': latitude, 'longitude': longitude}, kwargs)
        return self.make_request('sendLocation', params=params)

    def send_venue(self, chat_id, latitude, longitude, title, address, **kwargs):
        params = {'chat_id': chat_id, 'latitude': latitude, 'longitude': longitude, 'title': title, 'address': address}
        params.update(kwargs)
        return self.make_request('sendVenue', params=params)

    def send_contact(self, chat_id, phone_number, first_name, **kwargs):
        params = merge({'chat_id': chat_id, 'phone_number': phone_number, 'first_name': first_name}, kwargs)
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
        params = merge(params, kwargs)
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
        params = merge({'text': text}, kwargs)
        return self.make_request('editMessageText', params=params)

    def edit_message_caption(self, caption, **kwargs):
        params = merge({'caption': caption}, kwargs)
        return self.make_request('editMessageCaption', params=params)

    def edit_message_reply_markup(self, **kwargs):
        return self.make_request('editMessageReplyMarkup', params=kwargs)

    def answer_callback_query(self, callback_query_id, **kwargs):
        params = merge({'callback_query_id': callback_query_id}, kwargs)
        return self.make_request('answerCallbackQuery', params=params)

    def answer_inline_query(self, inline_query_id, results):
        params = merge({'inline_query_id': inline_query_id, 'results': results})
        return self.make_request('answerInlineQuery', params=params, method='post')

def _make_request(token, method_name, method='get', params=None, files=None, base_url=API_URL):
    """
    Makes a request to the Telegram API.
    :param token: The bot's API token. (Created with @BotFather)
    :param method_name: Name of the API method to be called. (E.g. 'getUpdates')
    :param method: HTTP method to be used. Defaults to 'get'.
    :param params: Optional parameters. Should be a dictionary with key-value pairs.
    :param files: Optional files.
    :return: The result parsed to a JSON dictionary.
    """
    request_url = base_url.format(token, method_name)
    logger.debug("Request: method={0} url={1} params={2} files={3}".format(method, request_url, params, files))
    read_timeout = READ_TIMEOUT
    if params:
        if 'timeout' in params: read_timeout = params['timeout'] + 10
    result = requests.request(method, request_url, params=params, files=files, timeout=(CONNECT_TIMEOUT, read_timeout))
    logger.debug("The server returned: '{0}'".format(result.text.encode('utf8')))
    return _check_result(method_name, result)['result']


def _check_result(method_name, result):
    """
    Checks whether `result` is a valid API response.
    A result is considered invalid if:
        - The server returned an HTTP response code other than 200
        - The content of the result is invalid JSON.
        - The method call was unsuccessful (The JSON 'ok' field equals False)

    :raises ApiException: if one of the above listed cases is applicable
    :param method_name: The name of the method called
    :param result: The returned result of the method request
    :return: The result parsed to a JSON dictionary.
    """
    if result.status_code != 200:
        msg = 'The server returned HTTP {0} {1}. Response body:\n[{2}]' \
            .format(result.status_code, result.reason, result.text.encode('utf8'))
        raise ApiException(msg, method_name, result)

    try:
        result_json = result.json()
    except:
        msg = 'The server returned an invalid JSON response. Response body:\n[{0}]' \
            .format(result.text.encode('utf8'))
        raise ApiException(msg, method_name, result)

    if not result_json['ok']:
        msg = 'Error code: {0} Description: {1}' \
            .format(result_json['error_code'], result_json['description'])
        raise ApiException(msg, method_name, result)
    return result_json


def get_me(token):
    method_url = r'getMe'
    return _make_request(token, method_url)


def get_file(token, file_id):
    method_url = r'getFile'
    return _make_request(token, method_url, params={'file_id': file_id})


def download_file(token, file_path):
    url = FILE_URL.format(token, file_path)
    result = requests.get(url)
    if result.status_code != 200:
        msg = 'The server returned HTTP {0} {1}. Response body:\n[{2}]' \
            .format(result.status_code, result.reason, result.text)
        raise ApiException(msg, 'Download file', result)
    return result.content


def send_message(token, chat_id, text, disable_web_page_preview=None, reply_to_message_id=None, reply_markup=None,
                 parse_mode=None, disable_notification=None):
    """
    Use this method to send text messages. On success, the sent Message is returned.
    :param token:
    :param chat_id:
    :param text:
    :param disable_web_page_preview:
    :param reply_to_message_id:
    :param reply_markup:
    :return:
    """
    method_url = r'sendMessage'
    payload = {'chat_id': str(chat_id), 'text': text}
    if disable_web_page_preview:
        payload['disable_web_page_preview'] = disable_web_page_preview
    if reply_to_message_id:
        payload['reply_to_message_id'] = reply_to_message_id
    if reply_markup:
        payload['reply_markup'] = _convert_markup(reply_markup)
    if parse_mode:
        payload['parse_mode'] = parse_mode
    if disable_notification:
        payload['disable_notification'] = disable_notification
    return _make_request(token, method_url, params=payload, method='post')


def set_webhook(token, url=None, certificate=None):
    method_url = r'setWebhook'
    payload = {
        'url': url if url else "",
    }
    files = None
    if certificate:
        files = {'certificate': certificate}

    return _make_request(token, method_url, params=payload, files=files)


def get_updates(token, offset=None, limit=None, timeout=None):
    method_url = r'getUpdates'
    payload = {}
    if offset:
        payload['offset'] = offset
    if limit:
        payload['limit'] = limit
    if timeout:
        payload['timeout'] = timeout
    return _make_request(token, method_url, params=payload)


def get_user_profile_photos(token, user_id, offset=None, limit=None):
    method_url = r'getUserProfilePhotos'
    payload = {'user_id': user_id}
    if offset:
        payload['offset'] = offset
    if limit:
        payload['limit'] = limit
    return _make_request(token, method_url, params=payload)


def forward_message(token, chat_id, from_chat_id, message_id, disable_notification=None):
    method_url = r'forwardMessage'
    payload = {'chat_id': chat_id, 'from_chat_id': from_chat_id, 'message_id': message_id}
    if disable_notification:
        payload['disable_notification'] = disable_notification
    return _make_request(token, method_url, params=payload)


def send_photo(token, chat_id, photo, caption=None, reply_to_message_id=None, reply_markup=None,
               disable_notification=None):
    method_url = r'sendPhoto'
    payload = {'chat_id': chat_id}
    files = None
    if not util.is_string(photo):
        files = {'photo': photo}
    else:
        payload['photo'] = photo
    if caption:
        payload['caption'] = caption
    if reply_to_message_id:
        payload['reply_to_message_id'] = reply_to_message_id
    if reply_markup:
        payload['reply_markup'] = _convert_markup(reply_markup)
    if disable_notification:
        payload['disable_notification'] = disable_notification
    return _make_request(token, method_url, params=payload, files=files, method='post')


def send_location(token, chat_id, latitude, longitude, reply_to_message_id=None, reply_markup=None,
                  disable_notification=None):
    method_url = r'sendLocation'
    payload = {'chat_id': chat_id, 'latitude': latitude, 'longitude': longitude}
    if reply_to_message_id:
        payload['reply_to_message_id'] = reply_to_message_id
    if reply_markup:
        payload['reply_markup'] = _convert_markup(reply_markup)
    if disable_notification:
        payload['disable_notification'] = disable_notification
    return _make_request(token, method_url, params=payload)


def send_venue(token, chat_id, latitude, longitude, title, address, foursquare_id=None, disable_notification=None,
               reply_to_message_id=None, reply_markup=None):
    method_url = r'sendVenue'
    payload = {'chat_id': chat_id, 'latitude': latitude, 'longitude': longitude, 'title': title, 'address': address}
    if foursquare_id:
        payload['foursquare_id'] = foursquare_id
    if disable_notification:
        payload['disable_notification'] = disable_notification
    if reply_to_message_id:
        payload['reply_to_message_id'] = reply_to_message_id
    if reply_markup:
        payload['reply_markup'] = _convert_markup(reply_markup)
    return _make_request(token, method_url, params=payload)


def send_contact(token, chat_id, phone_number, first_name, last_name=None, disable_notification=None,
                 reply_to_message_id=None, reply_markup=None):
    method_url = r'sendContact'
    payload = {'chat_id': chat_id, 'phone_number': phone_number, 'first_name': first_name}
    if last_name:
        payload['last_name'] = last_name
    if disable_notification:
        payload['disable_notification'] = disable_notification
    if reply_to_message_id:
        payload['reply_to_message_id'] = reply_to_message_id
    if reply_markup:
        payload['reply_markup'] = _convert_markup(reply_markup)
    return _make_request(token, method_url, params=payload)


def send_chat_action(token, chat_id, action):
    method_url = r'sendChatAction'
    payload = {'chat_id': chat_id, 'action': action}
    return _make_request(token, method_url, params=payload)


def send_video(token, chat_id, data, duration=None, caption=None, reply_to_message_id=None, reply_markup=None,
               disable_notification=None):
    method_url = r'sendVideo'
    payload = {'chat_id': chat_id}
    files = None
    if not util.is_string(data):
        files = {'video': data}
    else:
        payload['video'] = data
    if duration:
        payload['duration'] = duration
    if caption:
        payload['caption'] = caption
    if reply_to_message_id:
        payload['reply_to_message_id'] = reply_to_message_id
    if reply_markup:
        payload['reply_markup'] = _convert_markup(reply_markup)
    if disable_notification:
        payload['disable_notification'] = disable_notification
    return _make_request(token, method_url, params=payload, files=files, method='post')


def send_voice(token, chat_id, voice, duration=None, reply_to_message_id=None, reply_markup=None,
               disable_notification=None):
    method_url = r'sendVoice'
    payload = {'chat_id': chat_id}
    files = None
    if not util.is_string(voice):
        files = {'voice': voice}
    else:
        payload['voice'] = voice
    if duration:
        payload['duration'] = duration
    if reply_to_message_id:
        payload['reply_to_message_id'] = reply_to_message_id
    if reply_markup:
        payload['reply_markup'] = _convert_markup(reply_markup)
    if disable_notification:
        payload['disable_notification'] = disable_notification
    return _make_request(token, method_url, params=payload, files=files, method='post')


def send_audio(token, chat_id, audio, duration=None, performer=None, title=None, reply_to_message_id=None,
               reply_markup=None, disable_notification=None):
    method_url = r'sendAudio'
    payload = {'chat_id': chat_id}
    files = None
    if not util.is_string(audio):
        files = {'audio': audio}
    else:
        payload['audio'] = audio
    if duration:
        payload['duration'] = duration
    if performer:
        payload['performer'] = performer
    if title:
        payload['title'] = title
    if reply_to_message_id:
        payload['reply_to_message_id'] = reply_to_message_id
    if reply_markup:
        payload['reply_markup'] = _convert_markup(reply_markup)
    if disable_notification:
        payload['disable_notification'] = disable_notification
    return _make_request(token, method_url, params=payload, files=files, method='post')


def send_data(token, chat_id, data, data_type, reply_to_message_id=None, reply_markup=None, disable_notification=None):
    method_url = get_method_by_type(data_type)
    payload = {'chat_id': chat_id}
    files = None
    if not util.is_string(data):
        files = {data_type: data}
    else:
        payload[data_type] = data
    if reply_to_message_id:
        payload['reply_to_message_id'] = reply_to_message_id
    if reply_markup:
        payload['reply_markup'] = _convert_markup(reply_markup)
    if disable_notification:
        payload['disable_notification'] = disable_notification
    return _make_request(token, method_url, params=payload, files=files, method='post')


def get_method_by_type(data_type):
    if data_type == 'document':
        return r'sendDocument'
    if data_type == 'sticker':
        return r'sendSticker'


def kick_chat_member(token, chat_id, user_id):
    method_url = 'kickChatMember'
    payload = {'chat_id': chat_id, 'user_id': user_id}
    return _make_request(token, method_url, params=payload, method='post')


def unban_chat_member(token, chat_id, user_id):
    method_url = 'unbanChatMember'
    payload = {'chat_id': chat_id, 'user_id': user_id}
    return _make_request(token, method_url, params=payload, method='post')


# Updating messages

def edit_message_text(token, text, chat_id=None, message_id=None, inline_message_id=None, parse_mode=None,
                      disable_web_page_preview=None, reply_markup=None):
    method_url = r'editMessageText'
    payload = {'text': text}
    if chat_id:
        payload['chat_id'] = chat_id
    if message_id:
        payload['message_id'] = message_id
    if inline_message_id:
        payload['inline_message_id'] = inline_message_id
    if parse_mode:
        payload['parse_mode'] = parse_mode
    if disable_web_page_preview:
        payload['disable_web_page_preview'] = disable_web_page_preview
    if reply_markup:
        payload['reply_markup'] = _convert_markup(reply_markup)
    return _make_request(token, method_url, params=payload)


def edit_message_caption(token, caption, chat_id=None, message_id=None, inline_message_id=None, reply_markup=None):
    method_url = r'editMessageCaption'
    payload = {'caption': caption}
    if chat_id:
        payload['chat_id'] = chat_id
    if message_id:
        payload['message_id'] = message_id
    if inline_message_id:
        payload['inline_message_id'] = inline_message_id
    if reply_markup:
        payload['reply_markup'] = _convert_markup(reply_markup)
    return _make_request(token, method_url, params=payload)


def edit_message_reply_markup(token, chat_id=None, message_id=None, inline_message_id=None, reply_markup=None):
    method_url = r'editMessageReplyMarkup'
    payload = {}
    if chat_id:
        payload['chat_id'] = chat_id
    if message_id:
        payload['message_id'] = message_id
    if inline_message_id:
        payload['inline_message_id'] = inline_message_id
    if reply_markup:
        payload['reply_markup'] = _convert_markup(reply_markup)
    return _make_request(token, method_url, params=payload)


# InlineQuery

def answer_callback_query(token, callback_query_id, text=None, show_alert=None):
    method_url = 'answerCallbackQuery'
    payload = {'callback_query_id': callback_query_id}
    if text:
        payload['text'] = text
    if show_alert:
        payload['show_alert'] = show_alert
    return _make_request(token, method_url, params=payload, method='post')


def answer_inline_query(token, inline_query_id, results, cache_time=None, is_personal=None, next_offset=None,
                        switch_pm_text=None, switch_pm_parameter=None):
    method_url = 'answerInlineQuery'
    payload = {'inline_query_id': inline_query_id, 'results': _convert_inline_results(results)}
    if cache_time:
        payload['cache_time'] = cache_time
    if is_personal:
        payload['is_personal'] = is_personal
    if next_offset is not None:
        payload['next_offset'] = next_offset
    if switch_pm_text:
        payload['switch_pm_text'] = switch_pm_text
    if switch_pm_parameter:
        payload['switch_pm_parameter'] = switch_pm_parameter
    return _make_request(token, method_url, params=payload, method='post')


def _convert_inline_results(results):
    ret = ''
    for r in results:
        if isinstance(r, types.JsonSerializable):
            ret = ret + r.to_json() + ','
    if len(ret) > 0:
        ret = ret[:-1]
    return '[' + ret + ']'


def _convert_markup(markup):
    if isinstance(markup, types.JsonSerializable):
        return markup.to_json()
    return markup


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
