# -*- coding: utf-8 -*-
import time
from datetime import datetime

try:
    import ujson as json
except ImportError:
    import json

import requests
from requests.exceptions import HTTPError, ConnectionError, Timeout
from requests.adapters import HTTPAdapter

try:
    # noinspection PyUnresolvedReferences
    from requests.packages.urllib3 import fields
    format_header_param = fields.format_header_param
except ImportError:
    format_header_param = None
import telebot
from telebot import types
from telebot import util

logger = telebot.logger

proxy = None
session = None

API_URL = None
FILE_URL = None

CONNECT_TIMEOUT = 15
READ_TIMEOUT = 30

LONG_POLLING_TIMEOUT = 10 # Should be positive, short polling should be used for testing purposes only (https://core.telegram.org/bots/api#getupdates)

SESSION_TIME_TO_LIVE = 600  # In seconds. None - live forever, 0 - one-time

RETRY_ON_ERROR = False
RETRY_TIMEOUT = 2
MAX_RETRIES = 15
RETRY_ENGINE = 1

CUSTOM_SERIALIZER = None
CUSTOM_REQUEST_SENDER = None

ENABLE_MIDDLEWARE = False


def _get_req_session(reset=False):
    if SESSION_TIME_TO_LIVE:
        # If session TTL is set - check time passed
        creation_date = util.per_thread('req_session_time', lambda: datetime.now(), reset)
        # noinspection PyTypeChecker
        if (datetime.now() - creation_date).total_seconds() > SESSION_TIME_TO_LIVE:
            # Force session reset
            reset = True
            # Save reset time
            util.per_thread('req_session_time', lambda: datetime.now(), True)

    if SESSION_TIME_TO_LIVE == 0:
        # Session is one-time use
        return requests.sessions.Session()
    else:
        # Session lives some time or forever once created. Default
        return util.per_thread('req_session', lambda: session if session else requests.sessions.Session(), reset)


def _make_request(token, method_name, method='get', params=None, files=None):
    """
    Makes a request to the Telegram API.
    :param token: The bot's API token. (Created with @BotFather)
    :param method_name: Name of the API method to be called. (E.g. 'getUpdates')
    :param method: HTTP method to be used. Defaults to 'get'.
    :param params: Optional parameters. Should be a dictionary with key-value pairs.
    :param files: Optional files.
    :return: The result parsed to a JSON dictionary.
    """
    if not token:
        raise Exception('Bot token is not defined')
    if API_URL:
        # noinspection PyUnresolvedReferences
        request_url = API_URL.format(token, method_name)
    else:
        request_url = "https://api.telegram.org/bot{0}/{1}".format(token, method_name)

    logger.debug("Request: method={0} url={1} params={2} files={3}".format(method, request_url, params, files).replace(token, token.split(':')[0] + ":{TOKEN}"))
    read_timeout = READ_TIMEOUT
    connect_timeout = CONNECT_TIMEOUT

    if files:
        files_copy = dict(files)
        # process types.InputFile
        for key, value in files_copy.items():
            if isinstance(value, types.InputFile):
                files[key] = value.file
                
    
    if files and format_header_param:
        fields.format_header_param = _no_encode(format_header_param)
    if params:
        if 'timeout' in params:
            read_timeout = params.pop('timeout')
            connect_timeout = read_timeout
        if 'long_polling_timeout' in params:
            # For getUpdates. It's the only function with timeout parameter on the BOT API side
            long_polling_timeout = params.pop('long_polling_timeout')
            params['timeout'] = long_polling_timeout
            # Long polling hangs for a given time. Read timeout should be greater that long_polling_timeout
            read_timeout = max(long_polling_timeout + 5, read_timeout)

    params = params or None # Set params to None if empty
    result = None

    if CUSTOM_REQUEST_SENDER:
        # noinspection PyCallingNonCallable
        result = CUSTOM_REQUEST_SENDER(
            method, request_url, params=params, files=files,
            timeout=(connect_timeout, read_timeout), proxies=proxy)
    elif RETRY_ON_ERROR and RETRY_ENGINE == 1:
        got_result = False
        current_try = 0
        while not got_result and current_try<MAX_RETRIES-1:
            current_try+=1
            try:
                result = _get_req_session().request(
                    method, request_url, params=params, files=files,
                    timeout=(connect_timeout, read_timeout), proxies=proxy)
                got_result = True
            except HTTPError:
                logger.debug("HTTP Error on {0} method (Try #{1})".format(method_name, current_try))
                time.sleep(RETRY_TIMEOUT)
            except ConnectionError:
                logger.debug("Connection Error on {0} method (Try #{1})".format(method_name, current_try))
                time.sleep(RETRY_TIMEOUT)
            except Timeout:
                logger.debug("Timeout Error on {0} method (Try #{1})".format(method_name, current_try))
                time.sleep(RETRY_TIMEOUT)
        if not got_result:
            result = _get_req_session().request(
                    method, request_url, params=params, files=files,
                    timeout=(connect_timeout, read_timeout), proxies=proxy)
    elif RETRY_ON_ERROR and RETRY_ENGINE == 2:
        http = _get_req_session()
        # noinspection PyUnresolvedReferences
        retry_strategy = requests.packages.urllib3.util.retry.Retry(
            total=MAX_RETRIES,
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        for prefix in ('http://', 'https://'):
            http.mount(prefix, adapter)
        result = http.request(
            method, request_url, params=params, files=files,
            timeout=(connect_timeout, read_timeout), proxies=proxy)
    else:
        result = _get_req_session().request(
            method, request_url, params=params, files=files,
            timeout=(connect_timeout, read_timeout), proxies=proxy)
    
    logger.debug("The server returned: '{0}'".format(result.text.encode('utf8')))
    
    json_result = _check_result(method_name, result)
    if json_result:
        return json_result['result']


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
    try:
        result_json = result.json()
    except:
        if result.status_code != 200:
            raise ApiHTTPException(method_name, result)
        else:
            raise ApiInvalidJSONException(method_name, result)
    else:    
        if not result_json['ok']:
            raise ApiTelegramException(method_name, result, result_json)
            
        return result_json


def get_me(token):
    method_url = r'getMe'
    return _make_request(token, method_url)


def log_out(token):
    method_url = r'logOut'
    return _make_request(token, method_url)


def close(token):
    method_url = r'close'
    return _make_request(token, method_url)


def get_file(token, file_id):
    method_url = r'getFile'
    return _make_request(token, method_url, params={'file_id': file_id})


def get_file_url(token, file_id):
    if FILE_URL is None:
        return "https://api.telegram.org/file/bot{0}/{1}".format(token, get_file(token, file_id)['file_path'])
    else:
        # noinspection PyUnresolvedReferences
        return FILE_URL.format(token, get_file(token, file_id)['file_path'])


def download_file(token, file_path):
    if FILE_URL is None:
        url =  "https://api.telegram.org/file/bot{0}/{1}".format(token, file_path)
    else:
        # noinspection PyUnresolvedReferences
        url =  FILE_URL.format(token, file_path)
        
    result = _get_req_session().get(url, proxies=proxy)
    if result.status_code != 200:
        raise ApiHTTPException('Download file', result)
        
    return result.content


def send_message(
        token, chat_id, text,
        disable_web_page_preview=None, reply_to_message_id=None, reply_markup=None,
        parse_mode=None, disable_notification=None, timeout=None,
        entities=None, allow_sending_without_reply=None, protect_content=None,
        message_thread_id=None):
    method_url = r'sendMessage'
    payload = {'chat_id': str(chat_id), 'text': text}
    if disable_web_page_preview is not None:
        payload['disable_web_page_preview'] = disable_web_page_preview
    if reply_to_message_id:
        payload['reply_to_message_id'] = reply_to_message_id
    if reply_markup:
        payload['reply_markup'] = _convert_markup(reply_markup)
    if parse_mode:
        payload['parse_mode'] = parse_mode
    if disable_notification is not None:
        payload['disable_notification'] = disable_notification
    if timeout:
        payload['timeout'] = timeout
    if entities:
        payload['entities'] = json.dumps(types.MessageEntity.to_list_of_dicts(entities))
    if allow_sending_without_reply is not None:
        payload['allow_sending_without_reply'] = allow_sending_without_reply
    if protect_content is not None:
        payload['protect_content'] = protect_content
    if message_thread_id:
        payload['message_thread_id'] = message_thread_id
    return _make_request(token, method_url, params=payload, method='post')


def set_webhook(token, url=None, certificate=None, max_connections=None, allowed_updates=None, ip_address=None,
                drop_pending_updates = None, timeout=None, secret_token=None):
    method_url = r'setWebhook'
    payload = {
        'url': url if url else "",
    }
    files = None
    if certificate:
        files = {'certificate': certificate}
    if max_connections:
        payload['max_connections'] = max_connections
    if allowed_updates is not None:       # Empty lists should pass
        payload['allowed_updates'] = json.dumps(allowed_updates)
    if ip_address is not None:            # Empty string should pass
        payload['ip_address'] = ip_address
    if drop_pending_updates is not None:  # Any bool value should pass
        payload['drop_pending_updates'] = drop_pending_updates
    if timeout:
        payload['timeout'] = timeout
    if secret_token:
        payload['secret_token'] = secret_token
    return _make_request(token, method_url, params=payload, files=files)


def delete_webhook(token, drop_pending_updates=None, timeout=None):
    method_url = r'deleteWebhook'
    payload = {}
    if drop_pending_updates is not None:  # Any bool value should pass
        payload['drop_pending_updates'] = drop_pending_updates
    if timeout:
        payload['timeout'] = timeout
    return _make_request(token, method_url, params=payload)


def get_webhook_info(token, timeout=None):
    method_url = r'getWebhookInfo'
    payload = {}
    if timeout:
        payload['timeout'] = timeout
    return _make_request(token, method_url, params=payload)


def get_updates(token, offset=None, limit=None, timeout=None, allowed_updates=None, long_polling_timeout = None):
    method_url = r'getUpdates'
    payload = {}
    if offset:
        payload['offset'] = offset
    if limit:
        payload['limit'] = limit
    if timeout:
        payload['timeout'] = timeout
    payload['long_polling_timeout'] = long_polling_timeout if long_polling_timeout else LONG_POLLING_TIMEOUT
    if allowed_updates is not None:  # Empty lists should pass
        payload['allowed_updates'] = json.dumps(allowed_updates)
    return _make_request(token, method_url, params=payload)


def get_user_profile_photos(token, user_id, offset=None, limit=None):
    method_url = r'getUserProfilePhotos'
    payload = {'user_id': user_id}
    if offset:
        payload['offset'] = offset
    if limit:
        payload['limit'] = limit
    return _make_request(token, method_url, params=payload)


def get_chat(token, chat_id):
    method_url = r'getChat'
    payload = {'chat_id': chat_id}
    return _make_request(token, method_url, params=payload)


def leave_chat(token, chat_id):
    method_url = r'leaveChat'
    payload = {'chat_id': chat_id}
    return _make_request(token, method_url, params=payload)


def get_chat_administrators(token, chat_id):
    method_url = r'getChatAdministrators'
    payload = {'chat_id': chat_id}
    return _make_request(token, method_url, params=payload)


def get_chat_member_count(token, chat_id):
    method_url = r'getChatMemberCount'
    payload = {'chat_id': chat_id}
    return _make_request(token, method_url, params=payload)


def set_sticker_set_thumb(token, name, user_id, thumb):
    method_url = r'setStickerSetThumb'
    payload = {'name': name, 'user_id': user_id}
    files = {}
    if thumb:
        if not isinstance(thumb, str):
            files['thumb'] = thumb
        else:
            payload['thumb'] = thumb
    return _make_request(token, method_url, params=payload, files=files or None)


def set_chat_sticker_set(token, chat_id, sticker_set_name):
    method_url = r'setChatStickerSet'
    payload = {'chat_id': chat_id, 'sticker_set_name': sticker_set_name}
    return _make_request(token, method_url, params=payload)


def delete_chat_sticker_set(token, chat_id):
    method_url = r'deleteChatStickerSet'
    payload = {'chat_id': chat_id}
    return _make_request(token, method_url, params=payload)


def get_chat_member(token, chat_id, user_id):
    method_url = r'getChatMember'
    payload = {'chat_id': chat_id, 'user_id': user_id}
    return _make_request(token, method_url, params=payload)


def forward_message(
        token, chat_id, from_chat_id, message_id,
        disable_notification=None, timeout=None, protect_content=None, message_thread_id=None):
    method_url = r'forwardMessage'
    payload = {'chat_id': chat_id, 'from_chat_id': from_chat_id, 'message_id': message_id}
    if disable_notification is not None:
        payload['disable_notification'] = disable_notification
    if timeout:
        payload['timeout'] = timeout
    if protect_content is not None:
        payload['protect_content'] = protect_content
    if message_thread_id:
        payload['message_thread_id'] = message_thread_id
    return _make_request(token, method_url, params=payload)


def copy_message(token, chat_id, from_chat_id, message_id, caption=None, parse_mode=None, caption_entities=None,
                 disable_notification=None, reply_to_message_id=None, allow_sending_without_reply=None,
                 reply_markup=None, timeout=None, protect_content=None, message_thread_id=None):
    method_url = r'copyMessage'
    payload = {'chat_id': chat_id, 'from_chat_id': from_chat_id, 'message_id': message_id}
    if caption is not None:
        payload['caption'] = caption
    if parse_mode:
        payload['parse_mode'] = parse_mode
    if caption_entities is not None:
        payload['caption_entities'] = _convert_entites(caption_entities)
    if disable_notification is not None:
        payload['disable_notification'] = disable_notification
    if reply_to_message_id:
        payload['reply_to_message_id'] = reply_to_message_id
    if reply_markup is not None:
        payload['reply_markup'] = _convert_markup(reply_markup)
    if allow_sending_without_reply is not None:
        payload['allow_sending_without_reply'] = allow_sending_without_reply
    if timeout:
        payload['timeout'] = timeout
    if protect_content is not None:
        payload['protect_content'] = protect_content
    if message_thread_id is not None:
        payload['message_thread_id'] = message_thread_id
    return _make_request(token, method_url, params=payload)


def send_dice(
        token, chat_id,
        emoji=None, disable_notification=None, reply_to_message_id=None,
        reply_markup=None, timeout=None, allow_sending_without_reply=None, protect_content=None, message_thread_id=None):
    method_url = r'sendDice'
    payload = {'chat_id': chat_id}
    if emoji:
        payload['emoji'] = emoji
    if disable_notification is not None:
        payload['disable_notification'] = disable_notification
    if reply_to_message_id:
        payload['reply_to_message_id'] = reply_to_message_id
    if reply_markup:
        payload['reply_markup'] = _convert_markup(reply_markup)
    if timeout:
        payload['timeout'] = timeout
    if allow_sending_without_reply is not None:
        payload['allow_sending_without_reply'] = allow_sending_without_reply
    if protect_content is not None:
        payload['protect_content'] = protect_content
    if message_thread_id:
        payload['message_thread_id'] = message_thread_id
    return _make_request(token, method_url, params=payload)


def send_photo(
        token, chat_id, photo,
        caption=None, reply_to_message_id=None, reply_markup=None,
        parse_mode=None, disable_notification=None, timeout=None,
        caption_entities=None, allow_sending_without_reply=None, protect_content=None,
        message_thread_id=None):
    method_url = r'sendPhoto'
    payload = {'chat_id': chat_id}
    files = None
    if util.is_string(photo):
        payload['photo'] = photo
    elif util.is_pil_image(photo):
        files = {'photo': util.pil_image_to_file(photo)}
    else:
        files = {'photo': photo}
    if caption:
        payload['caption'] = caption
    if reply_to_message_id:
        payload['reply_to_message_id'] = reply_to_message_id
    if reply_markup:
        payload['reply_markup'] = _convert_markup(reply_markup)
    if parse_mode:
        payload['parse_mode'] = parse_mode
    if disable_notification is not None:
        payload['disable_notification'] = disable_notification
    if timeout:
        payload['timeout'] = timeout
    if caption_entities:
        payload['caption_entities'] = json.dumps(types.MessageEntity.to_list_of_dicts(caption_entities))
    if allow_sending_without_reply is not None:
        payload['allow_sending_without_reply'] = allow_sending_without_reply
    if protect_content is not None:
        payload['protect_content'] = protect_content
    if message_thread_id is not None:
        payload['message_thread_id'] = message_thread_id
    return _make_request(token, method_url, params=payload, files=files, method='post')


def send_media_group(
        token, chat_id, media,
        disable_notification=None, reply_to_message_id=None,
        timeout=None, allow_sending_without_reply=None, protect_content=None, message_thread_id=None):
    method_url = r'sendMediaGroup'
    media_json, files = convert_input_media_array(media)
    payload = {'chat_id': chat_id, 'media': media_json}
    if disable_notification is not None:
        payload['disable_notification'] = disable_notification
    if reply_to_message_id:
        payload['reply_to_message_id'] = reply_to_message_id
    if timeout:
        payload['timeout'] = timeout
    if allow_sending_without_reply is not None:
        payload['allow_sending_without_reply'] = allow_sending_without_reply
    if protect_content is not None:
        payload['protect_content'] = protect_content
    if message_thread_id is not None:
        payload['message_thread_id'] = message_thread_id
    return _make_request(
        token, method_url, params=payload,
        method='post' if files else 'get',
        files=files if files else None)


def send_location(
        token, chat_id, latitude, longitude,
        live_period=None, reply_to_message_id=None, 
        reply_markup=None, disable_notification=None, 
        timeout=None, horizontal_accuracy=None, heading=None,
        proximity_alert_radius=None, allow_sending_without_reply=None, protect_content=None,
        message_thread_id=None):
    method_url = r'sendLocation'
    payload = {'chat_id': chat_id, 'latitude': latitude, 'longitude': longitude}
    if live_period:
        payload['live_period'] = live_period
    if horizontal_accuracy:
        payload['horizontal_accuracy'] = horizontal_accuracy
    if heading:
        payload['heading'] = heading
    if proximity_alert_radius:
        payload['proximity_alert_radius'] = proximity_alert_radius
    if reply_to_message_id:
        payload['reply_to_message_id'] = reply_to_message_id
    if allow_sending_without_reply is not None:
        payload['allow_sending_without_reply'] = allow_sending_without_reply
    if reply_markup:
        payload['reply_markup'] = _convert_markup(reply_markup)
    if disable_notification is not None:
        payload['disable_notification'] = disable_notification
    if timeout:
        payload['timeout'] = timeout
    if protect_content is not None:
        payload['protect_content'] = protect_content
    if message_thread_id is not None:
        payload['message_thread_id'] = message_thread_id
    return _make_request(token, method_url, params=payload)


def edit_message_live_location(
        token, latitude, longitude, chat_id=None, message_id=None,
        inline_message_id=None, reply_markup=None, timeout=None,
        horizontal_accuracy=None, heading=None, proximity_alert_radius=None):
    method_url = r'editMessageLiveLocation'
    payload = {'latitude': latitude, 'longitude': longitude}
    if chat_id:
        payload['chat_id'] = chat_id
    if message_id:
        payload['message_id'] = message_id
    if horizontal_accuracy:
        payload['horizontal_accuracy'] = horizontal_accuracy
    if heading:
        payload['heading'] = heading
    if proximity_alert_radius:
        payload['proximity_alert_radius'] = proximity_alert_radius
    if inline_message_id:
        payload['inline_message_id'] = inline_message_id
    if reply_markup:
        payload['reply_markup'] = _convert_markup(reply_markup)
    if timeout:
        payload['timeout'] = timeout
    return _make_request(token, method_url, params=payload)


def stop_message_live_location(
        token, chat_id=None, message_id=None,
        inline_message_id=None, reply_markup=None, timeout=None):
    method_url = r'stopMessageLiveLocation'
    payload = {}
    if chat_id:
        payload['chat_id'] = chat_id
    if message_id:
        payload['message_id'] = message_id
    if inline_message_id:
        payload['inline_message_id'] = inline_message_id
    if reply_markup:
        payload['reply_markup'] = _convert_markup(reply_markup)
    if timeout:
        payload['timeout'] = timeout
    return _make_request(token, method_url, params=payload)


def send_venue(
        token, chat_id, latitude, longitude, title, address,
        foursquare_id=None, foursquare_type=None, disable_notification=None,
        reply_to_message_id=None, reply_markup=None, timeout=None,
        allow_sending_without_reply=None, google_place_id=None,
        google_place_type=None, protect_content=None, message_thread_id=None):
    method_url = r'sendVenue'
    payload = {'chat_id': chat_id, 'latitude': latitude, 'longitude': longitude, 'title': title, 'address': address}
    if foursquare_id:
        payload['foursquare_id'] = foursquare_id
    if foursquare_type:
        payload['foursquare_type'] = foursquare_type
    if disable_notification is not None:
        payload['disable_notification'] = disable_notification
    if reply_to_message_id:
        payload['reply_to_message_id'] = reply_to_message_id
    if reply_markup:
        payload['reply_markup'] = _convert_markup(reply_markup)
    if timeout:
        payload['timeout'] = timeout
    if allow_sending_without_reply is not None:
        payload['allow_sending_without_reply'] = allow_sending_without_reply
    if google_place_id:
        payload['google_place_id'] = google_place_id
    if google_place_type:
        payload['google_place_type'] = google_place_type
    if protect_content is not None:
        payload['protect_content'] = protect_content
    if message_thread_id is not None:
        payload['message_thread_id'] = message_thread_id
    return _make_request(token, method_url, params=payload)


def send_contact(
        token, chat_id, phone_number, first_name, last_name=None, vcard=None,
        disable_notification=None, reply_to_message_id=None, reply_markup=None, timeout=None,
        allow_sending_without_reply=None, protect_content=None, message_thread_id=None):
    method_url = r'sendContact'
    payload = {'chat_id': chat_id, 'phone_number': phone_number, 'first_name': first_name}
    if last_name:
        payload['last_name'] = last_name
    if vcard:
        payload['vcard'] = vcard
    if disable_notification is not None:
        payload['disable_notification'] = disable_notification
    if reply_to_message_id:
        payload['reply_to_message_id'] = reply_to_message_id
    if reply_markup:
        payload['reply_markup'] = _convert_markup(reply_markup)
    if timeout:
        payload['timeout'] = timeout
    if allow_sending_without_reply is not None:
        payload['allow_sending_without_reply'] = allow_sending_without_reply
    if protect_content is not None:
        payload['protect_content'] = protect_content
    if message_thread_id is not None:
        payload['message_thread_id'] = message_thread_id

    return _make_request(token, method_url, params=payload)


def send_chat_action(token, chat_id, action, timeout=None):
    method_url = r'sendChatAction'
    payload = {'chat_id': chat_id, 'action': action}
    if timeout:
        payload['timeout'] = timeout
    return _make_request(token, method_url, params=payload)


def send_video(token, chat_id, data, duration=None, caption=None, reply_to_message_id=None, reply_markup=None,
               parse_mode=None, supports_streaming=None, disable_notification=None, timeout=None, 
               thumb=None, width=None, height=None, caption_entities=None, allow_sending_without_reply=None, protect_content=None,
               message_thread_id=None):
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
    if parse_mode:
        payload['parse_mode'] = parse_mode
    if supports_streaming is not None:
        payload['supports_streaming'] = supports_streaming
    if disable_notification is not None:
        payload['disable_notification'] = disable_notification
    if timeout:
        payload['timeout'] = timeout
    if thumb:
        if not util.is_string(thumb):
            if files:
                files['thumb'] = thumb
            else:
                files = {'thumb': thumb}
        else:
            payload['thumb'] = thumb
    if width:
        payload['width'] = width
    if height:
        payload['height'] = height
    if caption_entities:
        payload['caption_entities'] = json.dumps(types.MessageEntity.to_list_of_dicts(caption_entities))
    if allow_sending_without_reply is not None:
        payload['allow_sending_without_reply'] = allow_sending_without_reply
    if protect_content is not None:
        payload['protect_content'] = protect_content
    if message_thread_id:
        payload['message_thread_id'] = message_thread_id
    return _make_request(token, method_url, params=payload, files=files, method='post')


def send_animation(
        token, chat_id, data, duration=None, caption=None, reply_to_message_id=None, reply_markup=None,
        parse_mode=None, disable_notification=None, timeout=None, thumb=None, caption_entities=None,
        allow_sending_without_reply=None, protect_content=None, width=None, height=None, message_thread_id=None):
    method_url = r'sendAnimation'
    payload = {'chat_id': chat_id}
    files = None
    if not util.is_string(data):
        files = {'animation': data}
    else:
        payload['animation'] = data
    if duration:
        payload['duration'] = duration
    if caption:
        payload['caption'] = caption
    if reply_to_message_id:
        payload['reply_to_message_id'] = reply_to_message_id
    if reply_markup:
        payload['reply_markup'] = _convert_markup(reply_markup)
    if parse_mode:
        payload['parse_mode'] = parse_mode
    if disable_notification is not None:
        payload['disable_notification'] = disable_notification
    if timeout:
        payload['timeout'] = timeout
    if thumb:
        if not util.is_string(thumb):
            if files:
                files['thumb'] = thumb
            else:
                files = {'thumb': thumb}
        else:
            payload['thumb'] = thumb
    if caption_entities:
        payload['caption_entities'] = json.dumps(types.MessageEntity.to_list_of_dicts(caption_entities))
    if allow_sending_without_reply is not None:
        payload['allow_sending_without_reply'] = allow_sending_without_reply
    if protect_content is not None:
        payload['protect_content'] = protect_content
    if width:
        payload['width'] = width
    if height:
        payload['height'] = height
    if message_thread_id:
        payload['message_thread_id'] = message_thread_id
    return _make_request(token, method_url, params=payload, files=files, method='post')


def send_voice(token, chat_id, voice, caption=None, duration=None, reply_to_message_id=None, reply_markup=None,
               parse_mode=None, disable_notification=None, timeout=None, caption_entities=None,
               allow_sending_without_reply=None, protect_content=None, message_thread_id=None):
    method_url = r'sendVoice'
    payload = {'chat_id': chat_id}
    files = None
    if not util.is_string(voice):
        files = {'voice': voice}
    else:
        payload['voice'] = voice
    if caption:
        payload['caption'] = caption
    if duration:
        payload['duration'] = duration
    if reply_to_message_id:
        payload['reply_to_message_id'] = reply_to_message_id
    if reply_markup:
        payload['reply_markup'] = _convert_markup(reply_markup)
    if parse_mode:
        payload['parse_mode'] = parse_mode
    if disable_notification is not None:
        payload['disable_notification'] = disable_notification
    if timeout:
        payload['timeout'] = timeout
    if caption_entities:
        payload['caption_entities'] = json.dumps(types.MessageEntity.to_list_of_dicts(caption_entities))
    if allow_sending_without_reply is not None:
        payload['allow_sending_without_reply'] = allow_sending_without_reply
    if protect_content is not None:
        payload['protect_content'] = protect_content
    if message_thread_id:
        payload['message_thread_id'] = message_thread_id
    return _make_request(token, method_url, params=payload, files=files, method='post')


def send_video_note(token, chat_id, data, duration=None, length=None, reply_to_message_id=None, reply_markup=None,
                    disable_notification=None, timeout=None, thumb=None, allow_sending_without_reply=None, protect_content=None,
                    message_thread_id=None):
    method_url = r'sendVideoNote'
    payload = {'chat_id': chat_id}
    files = None
    if not util.is_string(data):
        files = {'video_note': data}
    else:
        payload['video_note'] = data
    if duration:
        payload['duration'] = duration
    if length and (str(length).isdigit() and int(length) <= 639):
        payload['length'] = length
    else:
        payload['length'] = 639  # seems like it is MAX length size
    if reply_to_message_id:
        payload['reply_to_message_id'] = reply_to_message_id
    if reply_markup:
        payload['reply_markup'] = _convert_markup(reply_markup)
    if disable_notification is not None:
        payload['disable_notification'] = disable_notification
    if timeout:
        payload['timeout'] = timeout
    if thumb:
        if not util.is_string(thumb):
            if files:
                files['thumb'] = thumb
            else:
                files = {'thumb': thumb}
        else:
            payload['thumb'] = thumb
    if allow_sending_without_reply is not None:
        payload['allow_sending_without_reply'] = allow_sending_without_reply
    if protect_content is not None:
        payload['protect_content'] = protect_content
    if message_thread_id:
        payload['message_thread_id'] = message_thread_id
    return _make_request(token, method_url, params=payload, files=files, method='post')


def send_audio(token, chat_id, audio, caption=None, duration=None, performer=None, title=None, reply_to_message_id=None,
               reply_markup=None, parse_mode=None, disable_notification=None, timeout=None, thumb=None,
               caption_entities=None, allow_sending_without_reply=None, protect_content=None, message_thread_id=None):
    method_url = r'sendAudio'
    payload = {'chat_id': chat_id}
    files = None
    if not util.is_string(audio):
        files = {'audio': audio}
    else:
        payload['audio'] = audio
    if caption:
        payload['caption'] = caption
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
    if parse_mode:
        payload['parse_mode'] = parse_mode
    if disable_notification is not None:
        payload['disable_notification'] = disable_notification
    if timeout:
        payload['timeout'] = timeout
    if thumb:
        if not util.is_string(thumb):
            if files:
                files['thumb'] = thumb
            else:
                files = {'thumb': thumb}
        else:
            payload['thumb'] = thumb
    if caption_entities:
        payload['caption_entities'] = json.dumps(types.MessageEntity.to_list_of_dicts(caption_entities))
    if allow_sending_without_reply is not None:
        payload['allow_sending_without_reply'] = allow_sending_without_reply
    if protect_content is not None:
        payload['protect_content'] = protect_content
    if message_thread_id:
        payload['message_thread_id'] = message_thread_id
    return _make_request(token, method_url, params=payload, files=files, method='post')


def send_data(token, chat_id, data, data_type, reply_to_message_id=None, reply_markup=None, parse_mode=None,
              disable_notification=None, timeout=None, caption=None, thumb=None, caption_entities=None,
              allow_sending_without_reply=None, disable_content_type_detection=None, visible_file_name=None,
              protect_content = None, message_thread_id=None):
    method_url = get_method_by_type(data_type)
    payload = {'chat_id': chat_id}
    files = None
    if not util.is_string(data):
        file_data = data
        if visible_file_name:
            file_data = (visible_file_name, data)
        files = {data_type: file_data}
    else:
        payload[data_type] = data
    if reply_to_message_id:
        payload['reply_to_message_id'] = reply_to_message_id
    if reply_markup:
        payload['reply_markup'] = _convert_markup(reply_markup)
    if parse_mode and data_type == 'document':
        payload['parse_mode'] = parse_mode
    if disable_notification is not None:
        payload['disable_notification'] = disable_notification
    if timeout:
        payload['timeout'] = timeout
    if caption:
        payload['caption'] = caption
    if thumb:
        if not util.is_string(thumb):
            if files:
                files['thumb'] = thumb
            else:
                files = {'thumb': thumb}
        else:
            payload['thumb'] = thumb
    if caption_entities:
        payload['caption_entities'] = json.dumps(types.MessageEntity.to_list_of_dicts(caption_entities))
    if allow_sending_without_reply is not None:
        payload['allow_sending_without_reply'] = allow_sending_without_reply
    if protect_content is not None:
        payload['protect_content'] = protect_content
    if method_url == 'sendDocument' and disable_content_type_detection is not None:
        payload['disable_content_type_detection'] = disable_content_type_detection
    if message_thread_id:
        payload['message_thread_id'] = message_thread_id
    return _make_request(token, method_url, params=payload, files=files, method='post')


def get_method_by_type(data_type):
    if data_type == 'document':
        return r'sendDocument'
    if data_type == 'sticker':
        return r'sendSticker'


def ban_chat_member(token, chat_id, user_id, until_date=None, revoke_messages=None):
    method_url = 'banChatMember'
    payload = {'chat_id': chat_id, 'user_id': user_id}
    if isinstance(until_date, datetime):
        payload['until_date'] = until_date.timestamp()
    else:
        payload['until_date'] = until_date
    if revoke_messages is not None:
        payload['revoke_messages'] = revoke_messages
    return _make_request(token, method_url, params=payload, method='post')


def unban_chat_member(token, chat_id, user_id, only_if_banned):
    method_url = 'unbanChatMember'
    payload = {'chat_id': chat_id, 'user_id': user_id}
    if only_if_banned is not None:  # None / True / False
        payload['only_if_banned'] = only_if_banned
    return _make_request(token, method_url, params=payload, method='post')


def restrict_chat_member(
        token, chat_id, user_id, until_date=None,
        can_send_messages=None, can_send_media_messages=None,
        can_send_polls=None, can_send_other_messages=None,
        can_add_web_page_previews=None, can_change_info=None,
        can_invite_users=None, can_pin_messages=None):
    method_url = 'restrictChatMember'
    permissions = {}
    if can_send_messages is not None:
        permissions['can_send_messages'] = can_send_messages
    if can_send_media_messages is not None:
        permissions['can_send_media_messages'] = can_send_media_messages
    if can_send_polls is not None:
        permissions['can_send_polls'] = can_send_polls
    if can_send_other_messages is not None:
        permissions['can_send_other_messages'] = can_send_other_messages
    if can_add_web_page_previews is not None:
        permissions['can_add_web_page_previews'] = can_add_web_page_previews
    if can_change_info is not None:
        permissions['can_change_info'] = can_change_info
    if can_invite_users is not None:
        permissions['can_invite_users'] = can_invite_users
    if can_pin_messages is not None:
        permissions['can_pin_messages'] = can_pin_messages
    permissions_json = json.dumps(permissions)
    payload = {'chat_id': chat_id, 'user_id': user_id, 'permissions': permissions_json}
    if until_date is not None:
        if isinstance(until_date, datetime):
            payload['until_date'] = until_date.timestamp()
        else:
            payload['until_date'] = until_date
    return _make_request(token, method_url, params=payload, method='post')


def promote_chat_member(
        token, chat_id, user_id, can_change_info=None, can_post_messages=None,
        can_edit_messages=None, can_delete_messages=None, can_invite_users=None,
        can_restrict_members=None, can_pin_messages=None, can_promote_members=None,
        is_anonymous=None, can_manage_chat=None, can_manage_video_chats=None,
        can_manage_topics=None):
    method_url = 'promoteChatMember'
    payload = {'chat_id': chat_id, 'user_id': user_id}
    if can_change_info is not None:
        payload['can_change_info'] = can_change_info
    if can_post_messages is not None:
        payload['can_post_messages'] = can_post_messages
    if can_edit_messages is not None:
        payload['can_edit_messages'] = can_edit_messages
    if can_delete_messages is not None:
        payload['can_delete_messages'] = can_delete_messages
    if can_invite_users is not None:
        payload['can_invite_users'] = can_invite_users
    if can_restrict_members is not None:
        payload['can_restrict_members'] = can_restrict_members
    if can_pin_messages is not None:
        payload['can_pin_messages'] = can_pin_messages
    if can_promote_members is not None:
        payload['can_promote_members'] = can_promote_members
    if is_anonymous is not None:
        payload['is_anonymous'] = is_anonymous
    if can_manage_chat is not None:
        payload['can_manage_chat'] = can_manage_chat
    if can_manage_video_chats is not None:
        payload['can_manage_video_chats'] = can_manage_video_chats
    if can_manage_topics is not None:
        payload['can_manage_topics'] = can_manage_topics
    return _make_request(token, method_url, params=payload, method='post')


def set_chat_administrator_custom_title(token, chat_id, user_id, custom_title):
    method_url = 'setChatAdministratorCustomTitle'
    payload = {
        'chat_id': chat_id, 'user_id': user_id, 'custom_title': custom_title
    }
    return _make_request(token, method_url, params=payload, method='post')


def ban_chat_sender_chat(token, chat_id, sender_chat_id):
    method_url = 'banChatSenderChat'
    payload = {'chat_id': chat_id, 'sender_chat_id': sender_chat_id}
    return _make_request(token, method_url, params=payload, method='post')


def unban_chat_sender_chat(token, chat_id, sender_chat_id):
    method_url = 'unbanChatSenderChat'
    payload = {'chat_id': chat_id, 'sender_chat_id': sender_chat_id}
    return _make_request(token, method_url, params=payload, method='post')


def set_chat_permissions(token, chat_id, permissions):
    method_url = 'setChatPermissions'
    payload = {
        'chat_id': chat_id,
        'permissions': permissions.to_json()
    }
    return _make_request(token, method_url, params=payload, method='post')


def create_chat_invite_link(token, chat_id, name, expire_date, member_limit, creates_join_request):
    method_url = 'createChatInviteLink'
    payload = {
        'chat_id': chat_id
    }

    if expire_date is not None:
        if isinstance(expire_date, datetime):
            payload['expire_date'] = expire_date.timestamp()
        else:
            payload['expire_date'] = expire_date
    if member_limit:
        payload['member_limit'] = member_limit
    if creates_join_request is not None:
        payload['creates_join_request'] = creates_join_request
    if name:
        payload['name'] = name

    return _make_request(token, method_url, params=payload, method='post')


def edit_chat_invite_link(token, chat_id, invite_link, name, expire_date, member_limit, creates_join_request):
    method_url = 'editChatInviteLink'
    payload = {
        'chat_id': chat_id,
        'invite_link': invite_link
    }

    if expire_date is not None:
        if isinstance(expire_date, datetime):
            payload['expire_date'] = expire_date.timestamp()
        else:
            payload['expire_date'] = expire_date

    if member_limit is not None:
        payload['member_limit'] = member_limit
    if name:
        payload['name'] = name
    if creates_join_request is not None:
        payload['creates_join_request'] = creates_join_request

    return _make_request(token, method_url, params=payload, method='post')


def revoke_chat_invite_link(token, chat_id, invite_link):
    method_url = 'revokeChatInviteLink'
    payload = {
        'chat_id': chat_id,
        'invite_link': invite_link
    }
    return _make_request(token, method_url, params=payload, method='post')


def export_chat_invite_link(token, chat_id):
    method_url = 'exportChatInviteLink'
    payload = {'chat_id': chat_id}
    return _make_request(token, method_url, params=payload, method='post')


def approve_chat_join_request(token, chat_id, user_id):
    method_url = 'approveChatJoinRequest'
    payload = {
        'chat_id': chat_id,
        'user_id': user_id
    }
    return _make_request(token, method_url, params=payload, method='post')


def decline_chat_join_request(token, chat_id, user_id):
    method_url = 'declineChatJoinRequest'
    payload = {
        'chat_id': chat_id,
        'user_id': user_id
    }
    return _make_request(token, method_url, params=payload, method='post')


def set_chat_photo(token, chat_id, photo):
    method_url = 'setChatPhoto'
    payload = {'chat_id': chat_id}
    files = None
    if util.is_string(photo):
        payload['photo'] = photo
    elif util.is_pil_image(photo):
        files = {'photo': util.pil_image_to_file(photo)}
    else:
        files = {'photo': photo}
    return _make_request(token, method_url, params=payload, files=files, method='post')


def delete_chat_photo(token, chat_id):
    method_url = 'deleteChatPhoto'
    payload = {'chat_id': chat_id}
    return _make_request(token, method_url, params=payload, method='post')


def set_chat_title(token, chat_id, title):
    method_url = 'setChatTitle'
    payload = {'chat_id': chat_id, 'title': title}
    return _make_request(token, method_url, params=payload, method='post')


def get_my_commands(token, scope=None, language_code=None):
    method_url = r'getMyCommands'
    payload = {}
    if scope:
        payload['scope'] = scope.to_json()
    if language_code:
        payload['language_code'] = language_code
    return _make_request(token, method_url, params=payload)

def set_chat_menu_button(token, chat_id=None, menu_button=None):
    method_url = r'setChatMenuButton'
    payload = {}
    if chat_id:
        payload['chat_id'] = chat_id
    if menu_button:
        payload['menu_button'] = menu_button.to_json()
    return _make_request(token, method_url, params=payload, method='post')

def get_chat_menu_button(token, chat_id=None):
    method_url = r'getChatMenuButton'
    payload = {}
    if chat_id:
        payload['chat_id'] = chat_id
    return _make_request(token, method_url, params=payload, method='post')


def set_my_default_administrator_rights(token, rights=None, for_channels=None):
    method_url = r'setMyDefaultAdministratorRights'
    payload = {}
    if rights:
        payload['rights'] = rights.to_json()
    if for_channels is not None:
        payload['for_channels'] = for_channels
    return _make_request(token, method_url, params=payload, method='post')


def get_my_default_administrator_rights(token, for_channels=None):
    method_url = r'getMyDefaultAdministratorRights'
    payload = {}
    if for_channels:
        payload['for_channels'] = for_channels
    return _make_request(token, method_url, params=payload, method='post')


def set_my_commands(token, commands, scope=None, language_code=None):
    method_url = r'setMyCommands'
    payload = {'commands': _convert_list_json_serializable(commands)}
    if scope:
        payload['scope'] = scope.to_json()
    if language_code:
        payload['language_code'] = language_code
    return _make_request(token, method_url, params=payload, method='post')


def delete_my_commands(token, scope=None, language_code=None):
    method_url = r'deleteMyCommands'
    payload = {}
    if scope: 
        payload['scope'] = scope.to_json()
    if language_code: 
        payload['language_code'] = language_code
    return _make_request(token, method_url, params=payload, method='post')


def set_chat_description(token, chat_id, description):
    method_url = 'setChatDescription'
    payload = {'chat_id': chat_id}
    if description is not None:  # Allow empty strings
        payload['description'] = description
    return _make_request(token, method_url, params=payload, method='post')


def pin_chat_message(token, chat_id, message_id, disable_notification=None):
    method_url = 'pinChatMessage'
    payload = {'chat_id': chat_id, 'message_id': message_id}
    if disable_notification is not None:
        payload['disable_notification'] = disable_notification
    return _make_request(token, method_url, params=payload, method='post')


def unpin_chat_message(token, chat_id, message_id):
    method_url = 'unpinChatMessage'
    payload = {'chat_id': chat_id}
    if message_id:
        payload['message_id'] = message_id
    return _make_request(token, method_url, params=payload, method='post')


def unpin_all_chat_messages(token, chat_id):
    method_url = 'unpinAllChatMessages'
    payload = {'chat_id': chat_id}
    return _make_request(token, method_url, params=payload, method='post')


# Updating messages

def edit_message_text(token, text, chat_id=None, message_id=None, inline_message_id=None, parse_mode=None,
                      entities = None, disable_web_page_preview=None, reply_markup=None):
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
    if entities:
        payload['entities'] = json.dumps(types.MessageEntity.to_list_of_dicts(entities))
    if disable_web_page_preview is not None:
        payload['disable_web_page_preview'] = disable_web_page_preview
    if reply_markup:
        payload['reply_markup'] = _convert_markup(reply_markup)
    return _make_request(token, method_url, params=payload, method='post')


def edit_message_caption(token, caption, chat_id=None, message_id=None, inline_message_id=None,
                         parse_mode=None, caption_entities=None,reply_markup=None):
    method_url = r'editMessageCaption'
    payload = {'caption': caption}
    if chat_id:
        payload['chat_id'] = chat_id
    if message_id:
        payload['message_id'] = message_id
    if inline_message_id:
        payload['inline_message_id'] = inline_message_id
    if parse_mode:
        payload['parse_mode'] = parse_mode
    if caption_entities:
        payload['caption_entities'] = json.dumps(types.MessageEntity.to_list_of_dicts(caption_entities))
    if reply_markup:
        payload['reply_markup'] = _convert_markup(reply_markup)
    return _make_request(token, method_url, params=payload, method='post')


def edit_message_media(token, media, chat_id=None, message_id=None, inline_message_id=None, reply_markup=None):
    method_url = r'editMessageMedia'
    media_json, file = convert_input_media(media)
    payload = {'media': media_json}
    if chat_id:
        payload['chat_id'] = chat_id
    if message_id:
        payload['message_id'] = message_id
    if inline_message_id:
        payload['inline_message_id'] = inline_message_id
    if reply_markup:
        payload['reply_markup'] = _convert_markup(reply_markup)
    return _make_request(token, method_url, params=payload, files=file, method='post' if file else 'get')


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
    return _make_request(token, method_url, params=payload, method='post')


def delete_message(token, chat_id, message_id, timeout=None):
    method_url = r'deleteMessage'
    payload = {'chat_id': chat_id, 'message_id': message_id}
    if timeout:
        payload['timeout'] = timeout
    return _make_request(token, method_url, params=payload, method='post')


# Game

def send_game(
        token, chat_id, game_short_name,
        disable_notification=None, reply_to_message_id=None, reply_markup=None, timeout=None,
        allow_sending_without_reply=None, protect_content=None, message_thread_id=None):
    method_url = r'sendGame'
    payload = {'chat_id': chat_id, 'game_short_name': game_short_name}
    if disable_notification is not None:
        payload['disable_notification'] = disable_notification
    if reply_to_message_id:
        payload['reply_to_message_id'] = reply_to_message_id
    if reply_markup:
        payload['reply_markup'] = _convert_markup(reply_markup)
    if timeout:
        payload['timeout'] = timeout
    if allow_sending_without_reply is not None:
        payload['allow_sending_without_reply'] = allow_sending_without_reply
    if protect_content is not None:
        payload['protect_content'] = protect_content
    if message_thread_id:
        payload['message_thread_id'] = message_thread_id
    return _make_request(token, method_url, params=payload)


# https://core.telegram.org/bots/api#setgamescore
def set_game_score(token, user_id, score, force=None, disable_edit_message=None, chat_id=None, message_id=None,
                   inline_message_id=None):
    """
    Use this method to set the score of the specified user in a game. On success, if the message was sent by the bot, returns the edited Message, otherwise returns True. Returns an error, if the new score is not greater than the user's current score in the chat.
    :param token: Bot's token (you don't need to fill this)
    :param user_id: User identifier
    :param score: New score, must be non-negative
    :param force: (Optional) Pass True, if the high score is allowed to decrease. This can be useful when fixing mistakes or banning cheaters
    :param disable_edit_message: (Optional) Pass True, if the game message should not be automatically edited to include the current scoreboard
    :param chat_id: (Optional, required if inline_message_id is not specified) Unique identifier for the target chat (or username of the target channel in the format @channelusername)
    :param message_id: (Optional, required if inline_message_id is not specified) Unique identifier of the sent message
    :param inline_message_id: (Optional, required if chat_id and message_id are not specified) Identifier of the inline message
    :return:
    """
    method_url = r'setGameScore'
    payload = {'user_id': user_id, 'score': score}
    if force is not None:
        payload['force'] = force
    if chat_id:
        payload['chat_id'] = chat_id
    if message_id:
        payload['message_id'] = message_id
    if inline_message_id:
        payload['inline_message_id'] = inline_message_id
    if disable_edit_message is not None:
        payload['disable_edit_message'] = disable_edit_message
    return _make_request(token, method_url, params=payload)


# https://core.telegram.org/bots/api#getgamehighscores
def get_game_high_scores(token, user_id, chat_id=None, message_id=None, inline_message_id=None):
    """
    Use this method to get data for high score tables. Will return the score of the specified user and several of his neighbors in a game. On success, returns an Array of GameHighScore objects.
    This method will currently return scores for the target user, plus two of his closest neighbors on each side. Will also return the top three users if the user and his neighbors are not among them. Please note that this behavior is subject to change.
    :param token: Bot's token (you don't need to fill this)
    :param user_id: Target user id
    :param chat_id: (Optional, required if inline_message_id is not specified) Unique identifier for the target chat (or username of the target channel in the format @channelusername)
    :param message_id: (Optional, required if inline_message_id is not specified) Unique identifier of the sent message
    :param inline_message_id: (Optional, required if chat_id and message_id are not specified) Identifier of the inline message
    :return:
    """
    method_url = r'getGameHighScores'
    payload = {'user_id': user_id}
    if chat_id:
        payload['chat_id'] = chat_id
    if message_id:
        payload['message_id'] = message_id
    if inline_message_id:
        payload['inline_message_id'] = inline_message_id
    return _make_request(token, method_url, params=payload)


# Payments (https://core.telegram.org/bots/api#payments)

def send_invoice(
        token, chat_id, title, description, invoice_payload, provider_token, currency, prices,
        start_parameter = None, photo_url=None, photo_size=None, photo_width=None, photo_height=None,
        need_name=None, need_phone_number=None, need_email=None, need_shipping_address=None,
        send_phone_number_to_provider = None, send_email_to_provider = None, is_flexible=None,
        disable_notification=None, reply_to_message_id=None, reply_markup=None, provider_data=None,
        timeout=None, allow_sending_without_reply=None, max_tip_amount=None, suggested_tip_amounts=None,
        protect_content=None, message_thread_id=None):
    """
    Use this method to send invoices. On success, the sent Message is returned.
    :param token: Bot's token (you don't need to fill this)
    :param chat_id: Unique identifier for the target private chat
    :param title: Product name
    :param description: Product description
    :param invoice_payload: Bot-defined invoice payload, 1-128 bytes. This will not be displayed to the user, use for your internal processes.
    :param provider_token: Payments provider token, obtained via @Botfather
    :param currency: Three-letter ISO 4217 currency code, see https://core.telegram.org/bots/payments#supported-currencies
    :param prices: Price breakdown, a list of components (e.g. product price, tax, discount, delivery cost, delivery tax, bonus, etc.)
    :param start_parameter: Unique deep-linking parameter that can be used to generate this invoice when used as a start parameter
    :param photo_url: URL of the product photo for the invoice. Can be a photo of the goods or a marketing image for a service. People like it better when they see what they are paying for.
    :param photo_size: Photo size
    :param photo_width: Photo width
    :param photo_height: Photo height
    :param need_name: Pass True, if you require the user's full name to complete the order
    :param need_phone_number: Pass True, if you require the user's phone number to complete the order
    :param need_email: Pass True, if you require the user's email to complete the order
    :param need_shipping_address: Pass True, if you require the user's shipping address to complete the order
    :param is_flexible: Pass True, if the final price depends on the shipping method
    :param send_phone_number_to_provider: Pass True, if user's phone number should be sent to provider
    :param send_email_to_provider: Pass True, if user's email address should be sent to provider
    :param disable_notification: Sends the message silently. Users will receive a notification with no sound.
    :param reply_to_message_id: If the message is a reply, ID of the original message
    :param reply_markup: A JSON-serialized object for an inline keyboard. If empty, one 'Pay total price' button will be shown. If not empty, the first button must be a Pay button
    :param provider_data: A JSON-serialized data about the invoice, which will be shared with the payment provider. A detailed description of required fields should be provided by the payment provider.
    :param timeout:
    :param allow_sending_without_reply:
    :param max_tip_amount: The maximum accepted amount for tips in the smallest units of the currency
    :param suggested_tip_amounts: A JSON-serialized array of suggested amounts of tips in the smallest units of the currency.
        At most 4 suggested tip amounts can be specified. The suggested tip amounts must be positive, passed in a strictly increased order and must not exceed max_tip_amount.
    :param protect_content:
    :return:
    """
    method_url = r'sendInvoice'
    payload = {'chat_id': chat_id, 'title': title, 'description': description, 'payload': invoice_payload,
               'provider_token': provider_token, 'currency': currency,
               'prices': _convert_list_json_serializable(prices)}
    if start_parameter:
        payload['start_parameter'] = start_parameter
    if photo_url:
        payload['photo_url'] = photo_url
    if photo_size:
        payload['photo_size'] = photo_size
    if photo_width:
        payload['photo_width'] = photo_width
    if photo_height:
        payload['photo_height'] = photo_height
    if need_name is not None:
        payload['need_name'] = need_name
    if need_phone_number is not None:
        payload['need_phone_number'] = need_phone_number
    if need_email is not None:
        payload['need_email'] = need_email
    if need_shipping_address is not None:
        payload['need_shipping_address'] = need_shipping_address
    if send_phone_number_to_provider is not None:
        payload['send_phone_number_to_provider'] = send_phone_number_to_provider
    if send_email_to_provider is not None:
        payload['send_email_to_provider'] = send_email_to_provider
    if is_flexible is not None:
        payload['is_flexible'] = is_flexible
    if disable_notification is not None:
        payload['disable_notification'] = disable_notification
    if reply_to_message_id:
        payload['reply_to_message_id'] = reply_to_message_id
    if reply_markup:
        payload['reply_markup'] = _convert_markup(reply_markup)
    if provider_data:
        payload['provider_data'] = provider_data
    if timeout:
        payload['timeout'] = timeout
    if allow_sending_without_reply is not None:
        payload['allow_sending_without_reply'] = allow_sending_without_reply
    if max_tip_amount is not None:
        payload['max_tip_amount'] = max_tip_amount
    if suggested_tip_amounts is not None:
        payload['suggested_tip_amounts'] = json.dumps(suggested_tip_amounts)
    if protect_content is not None:
        payload['protect_content'] = protect_content
    if message_thread_id:
        payload['message_thread_id'] = message_thread_id
    return _make_request(token, method_url, params=payload)


def answer_shipping_query(token, shipping_query_id, ok, shipping_options=None, error_message=None):
    """
    If you sent an invoice requesting a shipping address and the parameter is_flexible was specified, the Bot API will send an Update with a shipping_query field to the bot. Use this method to reply to shipping queries. On success, True is returned.
    :param token: Bot's token (you don't need to fill this)
    :param shipping_query_id: Unique identifier for the query to be answered
    :param ok: Specify True if delivery to the specified address is possible and False if there are any problems (for example, if delivery to the specified address is not possible)
    :param shipping_options: Required if ok is True. A JSON-serialized array of available shipping options.
    :param error_message: Required if ok is False. Error message in human readable form that explains why it is impossible to complete the order (e.g. "Sorry, delivery to your desired address is unavailable'). Telegram will display this message to the user.
    :return:
    """
    method_url = 'answerShippingQuery'
    payload = {'shipping_query_id': shipping_query_id, 'ok': ok}
    if shipping_options:
        payload['shipping_options'] = _convert_list_json_serializable(shipping_options)
    if error_message:
        payload['error_message'] = error_message
    return _make_request(token, method_url, params=payload)


def answer_pre_checkout_query(token, pre_checkout_query_id, ok, error_message=None):
    """
    Once the user has confirmed their payment and shipping details, the Bot API sends the final confirmation in the form of an Update with the field pre_checkout_query. Use this method to respond to such pre-checkout queries. On success, True is returned. Note: The Bot API must receive an answer within 10 seconds after the pre-checkout query was sent.
    :param token: Bot's token (you don't need to fill this)
    :param pre_checkout_query_id: Unique identifier for the query to be answered
    :param ok: Specify True if everything is alright (goods are available, etc.) and the bot is ready to proceed with the order. Use False if there are any problems.
    :param error_message: Required if ok is False. Error message in human readable form that explains the reason for failure to proceed with the checkout (e.g. "Sorry, somebody just bought the last of our amazing black T-shirts while you were busy filling out your payment details. Please choose a different color or garment!"). Telegram will display this message to the user.
    :return:
    """
    method_url = 'answerPreCheckoutQuery'
    payload = {'pre_checkout_query_id': pre_checkout_query_id, 'ok': ok}
    if error_message:
        payload['error_message'] = error_message
    return _make_request(token, method_url, params=payload)


# InlineQuery

def answer_callback_query(token, callback_query_id, text=None, show_alert=None, url=None, cache_time=None):
    """
    Use this method to send answers to callback queries sent from inline keyboards. The answer will be displayed to the user as a notification at the top of the chat screen or as an alert. On success, True is returned.
    Alternatively, the user can be redirected to the specified Game URL. For this option to work, you must first create a game for your bot via BotFather and accept the terms. Otherwise, you may use links like telegram.me/your_bot?start=XXXX that open your bot with a parameter.
    :param token: Bot's token (you don't need to fill this)
    :param callback_query_id: Unique identifier for the query to be answered
    :param text: (Optional) Text of the notification. If not specified, nothing will be shown to the user, 0-200 characters
    :param show_alert: (Optional) If true, an alert will be shown by the client instead of a notification at the top of the chat screen. Defaults to false.
    :param url: (Optional) URL that will be opened by the user's client. If you have created a Game and accepted the conditions via @Botfather, specify the URL that opens your game – note that this will only work if the query comes from a callback_game button.
    Otherwise, you may use links like telegram.me/your_bot?start=XXXX that open your bot with a parameter.
    :param cache_time: (Optional) The maximum amount of time in seconds that the result of the callback query may be cached client-side. Telegram apps will support caching starting in version 3.14. Defaults to 0.
    :return:
    """
    method_url = 'answerCallbackQuery'
    payload = {'callback_query_id': callback_query_id}
    if text:
        payload['text'] = text
    if show_alert is not None:
        payload['show_alert'] = show_alert
    if url:
        payload['url'] = url
    if cache_time is not None:
        payload['cache_time'] = cache_time
    return _make_request(token, method_url, params=payload, method='post')


def answer_inline_query(token, inline_query_id, results, cache_time=None, is_personal=None, next_offset=None,
                        switch_pm_text=None, switch_pm_parameter=None):
    method_url = 'answerInlineQuery'
    payload = {'inline_query_id': inline_query_id, 'results': _convert_list_json_serializable(results)}
    if cache_time is not None:
        payload['cache_time'] = cache_time
    if is_personal is not None:
        payload['is_personal'] = is_personal
    if next_offset is not None:
        payload['next_offset'] = next_offset
    if switch_pm_text:
        payload['switch_pm_text'] = switch_pm_text
    if switch_pm_parameter:
        payload['switch_pm_parameter'] = switch_pm_parameter
    return _make_request(token, method_url, params=payload, method='post')


def get_sticker_set(token, name):
    method_url = 'getStickerSet'
    return _make_request(token, method_url, params={'name': name})

def get_custom_emoji_stickers(token, custom_emoji_ids):
    method_url = r'getCustomEmojiStickers'
    return _make_request(token, method_url, params={'custom_emoji_ids': custom_emoji_ids})
    
def upload_sticker_file(token, user_id, png_sticker):
    method_url = 'uploadStickerFile'
    payload = {'user_id': user_id}
    files = {'png_sticker': png_sticker}
    return _make_request(token, method_url, params=payload, files=files, method='post')


def create_new_sticker_set(
        token, user_id, name, title, emojis, png_sticker, tgs_sticker,
        mask_position=None, webm_sticker=None, sticker_type=None):
    method_url = 'createNewStickerSet'
    payload = {'user_id': user_id, 'name': name, 'title': title, 'emojis': emojis}
    if png_sticker:
        stype = 'png_sticker'
    elif webm_sticker:
        stype = 'webm_sticker'
    else:
        stype = 'tgs_sticker'
    sticker = png_sticker or tgs_sticker or webm_sticker
    files = None
    if not util.is_string(sticker):
        files = {stype: sticker}
    else:
        payload[stype] = sticker
    if mask_position:
        payload['mask_position'] = mask_position.to_json()
    if webm_sticker:
        payload['webm_sticker'] = webm_sticker
    if sticker_type:
        payload['sticker_type'] = sticker_type
    return _make_request(token, method_url, params=payload, files=files, method='post')


def add_sticker_to_set(token, user_id, name, emojis, png_sticker, tgs_sticker, mask_position, webm_sticker):
    method_url = 'addStickerToSet'
    payload = {'user_id': user_id, 'name': name, 'emojis': emojis}
    if png_sticker:
        stype = 'png_sticker'
    elif webm_sticker:
        stype = 'webm_sticker'
    else:
        stype = 'tgs_sticker'
    sticker = png_sticker or tgs_sticker or webm_sticker
    files = None
    if not util.is_string(sticker):
        files = {stype: sticker}
    else:
        payload[stype] = sticker
    if mask_position:
        payload['mask_position'] = mask_position.to_json()
    return _make_request(token, method_url, params=payload, files=files, method='post')


def set_sticker_position_in_set(token, sticker, position):
    method_url = 'setStickerPositionInSet'
    payload = {'sticker': sticker, 'position': position}
    return _make_request(token, method_url, params=payload, method='post')


def delete_sticker_from_set(token, sticker):
    method_url = 'deleteStickerFromSet'
    payload = {'sticker': sticker}
    return _make_request(token, method_url, params=payload, method='post')


def answer_web_app_query(token, web_app_query_id, result: types.InlineQueryResultBase):
    method_url = 'answerWebAppQuery'
    payload = {'web_app_query_id': web_app_query_id, 'result': result.to_json()}
    return _make_request(token, method_url, params=payload, method='post')


def create_invoice_link(token, title, description, payload, provider_token,
            currency, prices, max_tip_amount=None, suggested_tip_amounts=None, provider_data=None,
            photo_url=None, photo_size=None, photo_width=None, photo_height=None, need_name=None, need_phone_number=None,
            need_email=None, need_shipping_address=None, send_phone_number_to_provider=None,
            send_email_to_provider=None, is_flexible=None):
    method_url = r'createInvoiceLink'
    payload = {'title': title, 'description': description, 'payload': payload, 'provider_token': provider_token,
                'currency': currency, 'prices': _convert_list_json_serializable(prices)}
    if max_tip_amount:
        payload['max_tip_amount'] = max_tip_amount
    if suggested_tip_amounts:
        payload['suggested_tip_amounts'] = json.dumps(suggested_tip_amounts)
    if provider_data:
        payload['provider_data'] = provider_data
    if photo_url:
        payload['photo_url'] = photo_url
    if photo_size:
        payload['photo_size'] = photo_size
    if photo_width:
        payload['photo_width'] = photo_width
    if photo_height:
        payload['photo_height'] = photo_height
    if need_name is not None:
        payload['need_name'] = need_name
    if need_phone_number is not None:
        payload['need_phone_number'] = need_phone_number
    if need_email is not None:
        payload['need_email'] = need_email
    if need_shipping_address is not None:
        payload['need_shipping_address'] = need_shipping_address
    if send_phone_number_to_provider is not None:
        payload['send_phone_number_to_provider'] = send_phone_number_to_provider
    if send_email_to_provider is not None:
        payload['send_email_to_provider'] = send_email_to_provider
    if is_flexible is not None:
        payload['is_flexible'] = is_flexible
    return _make_request(token, method_url, params=payload, method='post')


# noinspection PyShadowingBuiltins
def send_poll(
        token, chat_id,
        question, options,
        is_anonymous = None, type = None, allows_multiple_answers = None, correct_option_id = None,
        explanation = None, explanation_parse_mode=None, open_period = None, close_date = None, is_closed = None,
        disable_notification=False, reply_to_message_id=None, allow_sending_without_reply=None,
        reply_markup=None, timeout=None, explanation_entities=None, protect_content=None, message_thread_id=None):
    method_url = r'sendPoll'
    payload = {
        'chat_id': str(chat_id),
        'question': question,
        'options': json.dumps(_convert_poll_options(options))}

    if is_anonymous is not None:
        payload['is_anonymous'] = is_anonymous
    if type is not None:
        payload['type'] = type
    if allows_multiple_answers is not None:
        payload['allows_multiple_answers'] = allows_multiple_answers
    if correct_option_id is not None:
        payload['correct_option_id'] = correct_option_id
    if explanation is not None:
        payload['explanation'] = explanation
    if explanation_parse_mode is not None:
        payload['explanation_parse_mode'] = explanation_parse_mode
    if open_period is not None:
        payload['open_period'] = open_period
    if close_date is not None:
        if isinstance(close_date, datetime):
            payload['close_date'] = close_date.timestamp()
        else:
            payload['close_date'] = close_date
    if is_closed is not None:
        payload['is_closed'] = is_closed

    if disable_notification:
        payload['disable_notification'] = disable_notification
    if reply_to_message_id is not None:
        payload['reply_to_message_id'] = reply_to_message_id
    if allow_sending_without_reply is not None:
        payload['allow_sending_without_reply'] = allow_sending_without_reply
    if reply_markup is not None:
        payload['reply_markup'] = _convert_markup(reply_markup)
    if timeout:
        payload['timeout'] = timeout
    if explanation_entities:
        payload['explanation_entities'] = json.dumps(
            types.MessageEntity.to_list_of_dicts(explanation_entities))
    if protect_content:
        payload['protect_content'] = protect_content
    if message_thread_id:
        payload['message_thread_id'] = message_thread_id
    return _make_request(token, method_url, params=payload)

def create_forum_topic(token, chat_id, name, icon_color=None, icon_custom_emoji_id=None):
    method_url = r'createForumTopic'
    payload = {'chat_id': chat_id, 'name': name}
    if icon_color:
        payload['icon_color'] = icon_color
    if icon_custom_emoji_id:
        payload['icon_custom_emoji_id'] = icon_custom_emoji_id
    return _make_request(token, method_url, params=payload)

def edit_forum_topic(token, chat_id, message_thread_id, name, icon_custom_emoji_id):
    method_url = r'editForumTopic'
    payload = {'chat_id': chat_id, 'message_thread_id': message_thread_id, 'name': name, 'icon_custom_emoji_id': icon_custom_emoji_id}
    return _make_request(token, method_url, params=payload)

def close_forum_topic(token, chat_id, message_thread_id):
    method_url = r'closeForumTopic'
    payload = {'chat_id': chat_id, 'message_thread_id': message_thread_id}
    return _make_request(token, method_url, params=payload)

def reopen_forum_topic(token, chat_id, message_thread_id):
    method_url = r'reopenForumTopic'
    payload = {'chat_id': chat_id, 'message_thread_id': message_thread_id}
    return _make_request(token, method_url, params=payload)

def delete_forum_topic(token, chat_id, message_thread_id):
    method_url = r'deleteForumTopic'
    payload = {'chat_id': chat_id, 'message_thread_id': message_thread_id}
    return _make_request(token, method_url, params=payload)

def unpin_all_forum_topic_messages(token, chat_id, message_thread_id):
    method_url = r'unpinAllForumTopicMessages'
    payload = {'chat_id': chat_id, 'message_thread_id': message_thread_id}
    return _make_request(token, method_url, params=payload)

def get_forum_topic_icon_stickers(token):
    method_url = r'getForumTopicIconStickers'
    return _make_request(token, method_url)

def stop_poll(token, chat_id, message_id, reply_markup=None):
    method_url = r'stopPoll'
    payload = {'chat_id': str(chat_id), 'message_id': message_id}
    if reply_markup:
        payload['reply_markup'] = _convert_markup(reply_markup)
    return _make_request(token, method_url, params=payload)


def _convert_list_json_serializable(results):
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


def _convert_entites(entites):
    if entites is None:
        return None
    elif len(entites) == 0:
        return []
    elif isinstance(entites[0], types.JsonSerializable):
        return [entity.to_json() for entity in entites]
    else:
        return entites


def _convert_poll_options(poll_options):
    if poll_options is None:
        return None
    elif len(poll_options) == 0:
        return []
    elif isinstance(poll_options[0], str):
        # Compatibility mode with previous bug when only list of string was accepted as poll_options
        return poll_options
    elif isinstance(poll_options[0], types.PollOption):
        return [option.text for option in poll_options]
    else:
        return poll_options


def convert_input_media(media):
    if isinstance(media, types.InputMedia):
        return media.convert_input_media()
    return None, None


def convert_input_media_array(array):
    media = []
    files = {}
    for input_media in array:
        if isinstance(input_media, types.InputMedia):
            media_dict = input_media.to_dict()
            if media_dict['media'].startswith('attach://'):
                key = media_dict['media'].replace('attach://', '')
                files[key] = input_media.media
            media.append(media_dict)
    return json.dumps(media), files


def _no_encode(func):
    def wrapper(key, val):
        if key == 'filename':
            return u'{0}={1}'.format(key, val)
        else:
            return func(key, val)

    return wrapper


class ApiException(Exception):
    """
    This class represents a base Exception thrown when a call to the Telegram API fails.
    In addition to an informative message, it has a `function_name` and a `result` attribute, which respectively
    contain the name of the failed function and the returned result that made the function to be considered  as
    failed.
    """

    def __init__(self, msg, function_name, result):
        super(ApiException, self).__init__("A request to the Telegram API was unsuccessful. {0}".format(msg))
        self.function_name = function_name
        self.result = result


class ApiHTTPException(ApiException):
    """
    This class represents an Exception thrown when a call to the 
    Telegram API server returns HTTP code that is not 200.
    """
    def __init__(self, function_name, result):
        super(ApiHTTPException, self).__init__(
            "The server returned HTTP {0} {1}. Response body:\n[{2}]" \
            .format(result.status_code, result.reason, result.text.encode('utf8')),
            function_name,
            result)


class ApiInvalidJSONException(ApiException):
    """
    This class represents an Exception thrown when a call to the 
    Telegram API server returns invalid json.
    """
    def __init__(self, function_name, result):
        super(ApiInvalidJSONException, self).__init__(
            "The server returned an invalid JSON response. Response body:\n[{0}]" \
            .format(result.text.encode('utf8')),
            function_name,
            result)


class ApiTelegramException(ApiException):
    """
    This class represents an Exception thrown when a Telegram API returns error code.
    """
    def __init__(self, function_name, result, result_json):
        super(ApiTelegramException, self).__init__(
            "Error code: {0}. Description: {1}" \
            .format(result_json['error_code'], result_json['description']),
            function_name,
            result)
        self.result_json = result_json
        self.error_code = result_json['error_code']
        self.description = result_json['description']
