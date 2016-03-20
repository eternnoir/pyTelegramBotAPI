# -*- coding: utf-8 -*-

import requests
import time
import telebot
from telebot import types
from telebot import util

logger = telebot.logger

API_URL = "https://api.telegram.org/bot{0}/{1}"
FILE_URL = "https://api.telegram.org/file/bot{0}/{1}"

# in seconds
CONNECT_TIMEOUT = 3.5
READ_TIMEOUT = 9999


def _make_request(token, method_name, method='get', params=None, files=None, base_url=API_URL,
                  timeout=(CONNECT_TIMEOUT, READ_TIMEOUT), max_retry=10):
    """
    Makes a request to the Telegram API.
    :param token: The bot's API token. (Created with @BotFather)
    :param method_name: Name of the API method to be called. (E.g. 'getUpdates')
    :param method: HTTP method to be used. Defaults to 'get'.
    :param params: Optional parameters. Should be a dictionary with key-value pairs.
    :param files: Optional files.
    :param base_url:
    :param timeout: see `_request_with_timeout`.
    :param max_retry: see `_request_with_timeout`.
    :return: The result parsed to a JSON dictionary.
    """
    request_url = base_url.format(token, method_name)
    logger.debug("Request: method={0} url={1} params={2} files={3}".format(method, request_url, params, files))
    result = _request_with_timeout(method, request_url, params=params, files=files,
                                   timeout=timeout, max_retry=max_retry)
    logger.debug("The server returned: '{0}'".format(result.text.encode('utf8')))
    return _check_result(method_name, result)['result']


def _request_with_timeout(method, request_url, params=None, files=None,
                          timeout=(CONNECT_TIMEOUT, READ_TIMEOUT), max_retry=10):
    """
    When network connection unreliable, try at most `max_retry` times until success.

    :param method: see `_make_request`.
    :param request_url: url to be passed to `requests.request`.
    :param params: see `_make_request`.
    :param files: see `_make_request`.
    :param timeout: see `requests.request(timeout=...)`. Defaults to (3.5, 9999).
    :param max_retry: number of attempts will be made before giving up. Defaults to 10.
    :return: result of `requests.request` invocation.
    :raises Exception: pass through any `requests.request` exception when `max_retry` exhausts.
    """
    delay = .25
    while True:
        try:
            return requests.request(method, request_url, params=params,
                                    files=files, timeout=timeout)
        except Exception as e:
            logger.debug("Request: connection failed.", exc_info=1)
            if max_retry <= 0:
                raise
            else:
                max_retry -= 1
                logger.debug("Request: Retry in {} seconds".format(delay))
                time.sleep(delay)
                delay *= 2


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
    if timeout is not None:
        payload['timeout'] = timeout
        timeout += 10  # for data transfer threshold
    return _make_request(token, method_url, params=payload, timeout=(CONNECT_TIMEOUT, timeout))


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


def answer_inline_query(token, inline_query_id, results, cache_time=None, is_personal=None, next_offset=None):
    method_url = 'answerInlineQuery'
    payload = {'inline_query_id': inline_query_id, 'results': _convert_inline_results(results)}
    if cache_time:
        payload['cache_time'] = cache_time
    if is_personal:
        payload['is_personal'] = is_personal
    if next_offset:
        payload['next_offset'] = next_offset
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

    def __init__(self, msg, function_name, result):
        super(ApiException, self).__init__("A request to the Telegram API was unsuccessful. {0}".format(msg))
        self.function_name = function_name
        self.result = result
