# -*- coding: utf-8 -*-

import sys
import six
import requests
import json
import logging

logger = logging.getLogger('TeleBot')


def __init_logger():
    formatter = logging.Formatter(
        '%(asctime)s (%(filename)s:%(lineno)d %(threadName)s) %(levelname)s - %(name)s: "%(message)s"'
    )

    console_output_handler = logging.StreamHandler(sys.stderr)
    console_output_handler.setFormatter(formatter)
    logger.addHandler(console_output_handler)

    logger.setLevel(logging.ERROR)

__init_logger()


def is_string(var):
    return isinstance(var, six.string_types)


def is_command(text):
    """
    Checks if `text` is a command. Telegram chat commands start with the '/' character.
    :param text: Text to check.
    :return: True if `text` is a command, else False.
    """
    return text.startswith('/')


def extract_command(text):
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
    return text.split()[0].split('@')[0][1:] if is_command(text) else None


def extract_arguments(text):
    """
    Returns the arguments after the command.

    Examples:
    extract_arguments("/get name"): ['name']
    extract_arguments("/get"): []
    extract_arguments("/get@botName name"): ['name']
    extract_arguments("/get@botName some more arguments"): ['some', 'more', 'arguments']

    :param text: String to extract the arguments from a command
    :return: the arguments of `text`.
    :raises ValueError if `text` is not a command
    """
    if not is_command(text):
        raise ValueError('Not a command: "{0}"'.format(text))
    return text.split()[1:]


def split_string(text, chars_per_string):
    """
    Splits one string into multiple strings, with a maximum amount of `chars_per_string` characters per string.
    This is very useful for splitting one giant message into multiples.

    :param text: The text to split
    :param chars_per_string: The number of characters per line the text is split into.
    :return: The splitted text as a list of strings.
    """
    return [text[i:i + chars_per_string] for i in range(0, len(text), chars_per_string)]


def obj_to_dict(obj):
    d = obj.__dict__.copy()
    if hasattr(obj, 'json_exclude'):
        for key in obj.json_exclude:
            if key in d:
                del d[key]

    for key, value in six.iteritems(d):
        if hasattr(value, '__dict__'):
            d[key] = obj_to_dict(value)
    return xmerge(d)


def obj_to_json(obj):
    return json.dumps(obj, default=lambda o: o.__dict__)


def json_exclude(*fields):
    def decorator(cls):
        cls.json_exclude = [f for f in fields]
        return cls
    return decorator


def merge_dicts(*dicts):
    if len(dicts) == 1:
        return dicts[0]

    result = {}
    for dictionary in dicts:
        result.update(dictionary)
    return result


def xmerge(*dicts):
    """
    Merges two or more dicts into one, and deletes any keys which' associated values are equal to None.
    :rtype: dict
    """
    d = merge_dicts(*dicts)
    copy = d.copy()
    for k, v in six.iteritems(d):
        if v is None:
            del copy[k]
    return copy


def required(*required_kwargs):
    def decorator(fn):
        def wrapper(*args, **kwargs):
            has_all_required_kwargs = all(p in kwargs for p in required_kwargs)

            if len(args) < len(required_kwargs) and not has_all_required_kwargs:
                # Calculate the missing kwargs
                diff = [p for p in required_kwargs[len(args):] if p not in kwargs]

                raise ValueError("Missing required arguments: {0}".format(diff))
            return fn(*args, **kwargs)
        return wrapper
    return decorator


def translate(translate_dict):
    def decorator(fn):
        def wrapper(*args, **kwargs):
            for k, v in six.iteritems(translate_dict):
                if k in kwargs:
                    kwargs[v] = kwargs[k]
                    del kwargs[k]
            return fn(*args, **kwargs)
        return wrapper
    return decorator


def async(threadpool):
    """
    Annotate a function with this decorator to ensure that this function is executed asynchronously.
    `threadpool` is the concurrent.futures.ThreadPoolExecutor that this function is executed by.
    :param threadpool: ThreadPoolExecutor to execute this function in.
    :type threadpool: concurrent.futures.ThreadPoolExecutor
    :return: concurrent.futures.Future
    """
    def decorator(fn):
        def wrapper(*args, **kwargs):
            return threadpool.submit(fn, *args, **kwargs)
        return wrapper
    return decorator


class BotanTracker:
    TRACK_URL = 'https://api.botan.io/track'

    def __init__(self, token, uid):
        self.token = token
        self.uid = uid

    def track_handler(self, name='Message'):
        def decorator(handler):
            def wrapper(arg):
                self.track(arg, name)
                handler(arg)
            return wrapper
        return decorator

    def track(self, message, name='Message'):
        try:
            response = requests.post(
                self.TRACK_URL,
                params={'token': self.token, 'uid': self.uid, 'name': name},
                data=obj_to_json(message),
                headers={'Content-type': 'application/json'}
            )
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(e)
            return False
