# -*- coding: utf-8 -*-
import random
import re
import string
import threading
import traceback
import warnings
from typing import Any, Callable, List, Dict, Optional, Union

# noinspection PyPep8Naming
import queue as Queue
import logging

from telebot import types

try:
    import ujson as json
except ImportError:
    import json

try:
    # noinspection PyPackageRequirements
    from PIL import Image
    from io import BytesIO
    pil_imported = True
except:
    pil_imported = False

MAX_MESSAGE_LENGTH = 4096

logger = logging.getLogger('TeleBot')

thread_local = threading.local()

content_type_media = [
    'text', 'audio', 'animation', 'document', 'photo', 'sticker', 'video', 'video_note', 'voice', 'contact', 'dice', 'poll',
    'venue', 'location'
]

content_type_service = [
    'new_chat_members', 'left_chat_member', 'new_chat_title', 'new_chat_photo', 'delete_chat_photo', 'group_chat_created',
    'supergroup_chat_created', 'channel_chat_created', 'migrate_to_chat_id', 'migrate_from_chat_id', 'pinned_message',
    'proximity_alert_triggered', 'voice_chat_scheduled', 'voice_chat_started', 'voice_chat_ended', 
    'voice_chat_participants_invited', 'message_auto_delete_timer_changed'
]

update_types = [
    "update_id", "message", "edited_message", "channel_post", "edited_channel_post", "inline_query", 
    "chosen_inline_result", "callback_query", "shipping_query", "pre_checkout_query", "poll", "poll_answer", 
    "my_chat_member", "chat_member", "chat_join_request"
]

class WorkerThread(threading.Thread):
    count = 0

    def __init__(self, exception_callback=None, queue=None, name=None):
        if not name:
            name = "WorkerThread{0}".format(self.__class__.count + 1)
            self.__class__.count += 1
        if not queue:
            queue = Queue.Queue()

        threading.Thread.__init__(self, name=name)
        self.queue = queue
        self.daemon = True

        self.received_task_event = threading.Event()
        self.done_event = threading.Event()
        self.exception_event = threading.Event()
        self.continue_event = threading.Event()

        self.exception_callback = exception_callback
        self.exception_info = None
        self._running = True
        self.start()

    def run(self):
        while self._running:
            try:
                task, args, kwargs = self.queue.get(block=True, timeout=.5)
                self.continue_event.clear()
                self.received_task_event.clear()
                self.done_event.clear()
                self.exception_event.clear()
                logger.debug("Received task")
                self.received_task_event.set()

                task(*args, **kwargs)
                logger.debug("Task complete")
                self.done_event.set()
            except Queue.Empty:
                pass
            except Exception as e:
                logger.debug(type(e).__name__ + " occurred, args=" + str(e.args) + "\n" + traceback.format_exc())
                self.exception_info = e
                self.exception_event.set()
                if self.exception_callback:
                    self.exception_callback(self, self.exception_info)
                self.continue_event.wait()

    def put(self, task, *args, **kwargs):
        self.queue.put((task, args, kwargs))

    def raise_exceptions(self):
        if self.exception_event.is_set():
            raise self.exception_info

    def clear_exceptions(self):
        self.exception_event.clear()
        self.continue_event.set()

    def stop(self):
        self._running = False


class ThreadPool:

    def __init__(self, num_threads=2):
        self.tasks = Queue.Queue()
        self.workers = [WorkerThread(self.on_exception, self.tasks) for _ in range(num_threads)]
        self.num_threads = num_threads

        self.exception_event = threading.Event()
        self.exception_info = None

    def put(self, func, *args, **kwargs):
        self.tasks.put((func, args, kwargs))

    def on_exception(self, worker_thread, exc_info):
        self.exception_info = exc_info
        self.exception_event.set()
        worker_thread.continue_event.set()

    def raise_exceptions(self):
        if self.exception_event.is_set():
            raise self.exception_info

    def clear_exceptions(self):
        self.exception_event.clear()

    def close(self):
        for worker in self.workers:
            worker.stop()
        for worker in self.workers:
            worker.join()


class AsyncTask:
    def __init__(self, target, *args, **kwargs):
        self.target = target
        self.args = args
        self.kwargs = kwargs

        self.done = False
        self.thread = threading.Thread(target=self._run)
        self.thread.start()

    def _run(self):
        try:
            self.result = self.target(*self.args, **self.kwargs)
        except Exception as e:
            self.result = e
        self.done = True

    def wait(self):
        if not self.done:
            self.thread.join()
        if isinstance(self.result, BaseException):
            raise self.result
        else:
            return self.result


class CustomRequestResponse():
    def __init__(self, json_text, status_code = 200, reason = ""):
        self.status_code = status_code
        self.text = json_text
        self.reason = reason

    def json(self):
        return json.loads(self.text)


def async_dec():
    def decorator(fn):
        def wrapper(*args, **kwargs):
            return AsyncTask(fn, *args, **kwargs)

        return wrapper

    return decorator


def is_string(var):
    return isinstance(var, str)


def is_dict(var):
    return isinstance(var, dict)


def is_bytes(var):
    return isinstance(var, bytes)


def is_pil_image(var):
    return pil_imported and isinstance(var, Image.Image)


def pil_image_to_file(image, extension='JPEG', quality='web_low'):
    if pil_imported:
        photoBuffer = BytesIO()
        image.convert('RGB').save(photoBuffer, extension, quality=quality)
        photoBuffer.seek(0)
        
        return photoBuffer
    else:
        raise RuntimeError('PIL module is not imported')


def is_command(text: str) -> bool:
    """
    Checks if `text` is a command. Telegram chat commands start with the '/' character.
    :param text: Text to check.
    :return: True if `text` is a command, else False.
    """
    if text is None: return False
    return text.startswith('/')


def extract_command(text: str) -> Union[str, None]:
    """
    Extracts the command from `text` (minus the '/') if `text` is a command (see is_command).
    If `text` is not a command, this function returns None.

    Examples:
    extract_command('/help'): 'help'
    extract_command('/help@BotName'): 'help'
    extract_command('/search black eyed peas'): 'search'
    extract_command('Good day to you'): None

    :param text: String to extract the command from
    :return: the command if `text` is a command (according to is_command), else None.
    """
    if text is None: return None
    return text.split()[0].split('@')[0][1:] if is_command(text) else None


def extract_arguments(text: str) -> str:
    """
    Returns the argument after the command.
    
    Examples:
    extract_arguments("/get name"): 'name'
    extract_arguments("/get"): ''
    extract_arguments("/get@botName name"): 'name'
    
    :param text: String to extract the arguments from a command
    :return: the arguments if `text` is a command (according to is_command), else None.
    """
    regexp = re.compile(r"/\w*(@\w*)*\s*([\s\S]*)", re.IGNORECASE)
    result = regexp.match(text)
    return result.group(2) if is_command(text) else None


def split_string(text: str, chars_per_string: int) -> List[str]:
    """
    Splits one string into multiple strings, with a maximum amount of `chars_per_string` characters per string.
    This is very useful for splitting one giant message into multiples.

    :param text: The text to split
    :param chars_per_string: The number of characters per line the text is split into.
    :return: The splitted text as a list of strings.
    """
    return [text[i:i + chars_per_string] for i in range(0, len(text), chars_per_string)]


def smart_split(text: str, chars_per_string: int=MAX_MESSAGE_LENGTH) -> List[str]:
    """
    Splits one string into multiple strings, with a maximum amount of `chars_per_string` characters per string.
    This is very useful for splitting one giant message into multiples.
    If `chars_per_string` > 4096: `chars_per_string` = 4096.
    Splits by '\n', '. ' or ' ' in exactly this priority.

    :param text: The text to split
    :param chars_per_string: The number of maximum characters per part the text is split to.
    :return: The splitted text as a list of strings.
    """

    def _text_before_last(substr: str) -> str:
        return substr.join(part.split(substr)[:-1]) + substr

    if chars_per_string > MAX_MESSAGE_LENGTH: chars_per_string = MAX_MESSAGE_LENGTH

    parts = []
    while True:
        if len(text) < chars_per_string:
            parts.append(text)
            return parts

        part = text[:chars_per_string]

        if "\n" in part: part = _text_before_last("\n")
        elif ". " in part: part = _text_before_last(". ")
        elif " " in part: part = _text_before_last(" ")

        parts.append(part)
        text = text[len(part):]


def escape(text: str) -> str:
    """
    Replaces the following chars in `text` ('&' with '&amp;', '<' with '&lt;' and '>' with '&gt;').

    :param text: the text to escape
    :return: the escaped text
    """
    chars = {"&": "&amp;", "<": "&lt;", ">": "&gt"}
    for old, new in chars.items(): text = text.replace(old, new)
    return text


def user_link(user: types.User, include_id: bool=False) -> str:
    """
    Returns an HTML user link. This is useful for reports.
    Attention: Don't forget to set parse_mode to 'HTML'!

    Example:
    bot.send_message(your_user_id, user_link(message.from_user) + ' started the bot!', parse_mode='HTML')

    :param user: the user (not the user_id)
    :param include_id: include the user_id
    :return: HTML user link
    """
    name = escape(user.first_name)
    return (f"<a href='tg://user?id={user.id}'>{name}</a>" 
        + (f" (<pre>{user.id}</pre>)" if include_id else ""))


def quick_markup(values: Dict[str, Dict[str, Any]], row_width: int=2) -> types.InlineKeyboardMarkup:
    """
    Returns a reply markup from a dict in this format: {'text': kwargs}
    This is useful to avoid always typing 'btn1 = InlineKeyboardButton(...)' 'btn2 = InlineKeyboardButton(...)' 
    
    Example:
    quick_markup({
        'Twitter': {'url': 'https://twitter.com'},
        'Facebook': {'url': 'https://facebook.com'},
        'Back': {'callback_data': 'whatever'}
    }, row_width=2): 
        returns an InlineKeyboardMarkup with two buttons in a row, one leading to Twitter, the other to facebook
        and a back button below

    kwargs can be: 
    {
        'url': None, 
        'callback_data': None, 
        'switch_inline_query': None,
        'switch_inline_query_current_chat': None,
        'callback_game': None,
        'pay': None,
        'login_url': None
    }
    
    :param values: a dict containing all buttons to create in this format: {text: kwargs} {str:}
    :param row_width: int row width
    :return: InlineKeyboardMarkup
    """
    markup = types.InlineKeyboardMarkup(row_width=row_width)
    buttons = [
        types.InlineKeyboardButton(text=text, **kwargs)
        for text, kwargs in values.items()
    ]
    markup.add(*buttons)
    return markup


# CREDITS TO http://stackoverflow.com/questions/12317940#answer-12320352
def or_set(self):
    self._set()
    self.changed()


def or_clear(self):
    self._clear()
    self.changed()


def orify(e, changed_callback):
    if not hasattr(e, "_set"):
        e._set = e.set
    if not hasattr(e, "_clear"):
        e._clear = e.clear
    e.changed = changed_callback
    e.set = lambda: or_set(e)
    e.clear = lambda: or_clear(e)


def OrEvent(*events):
    or_event = threading.Event()

    def changed():
        bools = [ev.is_set() for ev in events]
        if any(bools):
            or_event.set()
        else:
            or_event.clear()

    def busy_wait():
        while not or_event.is_set():
            or_event._wait(3)

    for e in events:
        orify(e, changed)
    or_event._wait = or_event.wait
    or_event.wait = busy_wait
    changed()
    return or_event


def per_thread(key, construct_value, reset=False):
    if reset or not hasattr(thread_local, key):
        value = construct_value()
        setattr(thread_local, key, value)

    return getattr(thread_local, key)


def chunks(lst, n):
    """Yield successive n-sized chunks from lst."""
    # https://stackoverflow.com/a/312464/9935473
    for i in range(0, len(lst), n):
        yield lst[i:i + n]


def generate_random_token():
    return ''.join(random.sample(string.ascii_letters, 16))


def deprecated(warn: bool=True, alternative: Optional[Callable]=None):
    """
    Use this decorator to mark functions as deprecated.
    When the function is used, an info (or warning if `warn` is True) is logged.
    :param warn: If True a warning is logged else an info
    :param alternative: The new function to use instead
    """
    def decorator(function):
        def wrapper(*args, **kwargs):
            info = f"`{function.__name__}` is deprecated." + (f" Use `{alternative.__name__}` instead" if alternative else "")
            if not warn:
                logger.info(info)
            else:
                logger.warning(info)
            return function(*args, **kwargs)
        return wrapper
    return decorator


# Cloud helpers
def webhook_google_functions(bot, request):
    """A webhook endpoint for Google Cloud Functions FaaS."""
    if request.is_json:
        try:
            request_json = request.get_json()
            update = types.Update.de_json(request_json)
            bot.process_new_updates([update])
            return ''
        except Exception as e:
            print(e)
            return 'Bot FAIL', 400
    else:
        return 'Bot ON'

def antiflood(function, *args, **kwargs):
    """
    Use this function inside loops in order to avoid getting TooManyRequests error.
    Example:

    from telebot.util import antiflood
    for chat_id in chat_id_list:
        msg = antiflood(bot.send_message, chat_id, text)
        
    You want get the
    """
    from telebot.apihelper import ApiTelegramException
    from time import sleep
    msg = None
    try:
        msg = function(*args, **kwargs)
    except ApiTelegramException as ex:
        if ex.error_code == 429:
            sleep(ex.result_json['parameters']['retry_after'])
            msg = function(*args, **kwargs)
    finally:
        return msg
