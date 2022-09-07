import asyncio
import functools
import logging
import random
import re
import string
import threading
from typing import Any, Callable, Coroutine, List, Optional, Type, TypeVar, Union, cast

from telebot.types import constants

MAX_MESSAGE_LENGTH = 4096

logger = logging.getLogger(__name__)


def qualified_name(obj: Any) -> str:
    try:
        return f"{obj.__module__}.{obj.__qualname__}"
    except Exception:
        return "<cant-get-qualified-name>"


T = TypeVar("T")


def ensure_async(func: Callable[..., Union[T, Coroutine[None, None, T]]]) -> Callable[..., Coroutine[None, None, T]]:
    if asyncio.iscoroutinefunction(func):
        return cast(Callable[..., Coroutine[None, None, T]], func)
    else:

        @functools.wraps(func)
        async def wrapper(*args, **kwargs) -> T:
            return cast(Callable[..., T], func)(*args, **kwargs)

        return wrapper


def is_string(var: Any) -> bool:
    return isinstance(var, str)


def is_bytes(var: Any) -> bool:
    return isinstance(var, bytes)


def validated_list_str(v: Any, name: Optional[str] = None) -> list[str]:
    name = name or "<anonymous>"
    if not isinstance(v, list):
        raise TypeError(f"{name} is expected to be list[str], but it's not even a list")
    for item in v:
        if not isinstance(item, str):
            raise TypeError(f"{name} is expected to be list[str], but includes non-string item '{item}'")
    return v


def validated_str(v: Any, name: Optional[str] = None) -> str:
    name = name or "<anonymous>"
    if not isinstance(v, str):
        raise TypeError(f"{name} is expected to be str, but it's '{v}'")
    return v


def _validated_list(v: Any, item_types: list[Type], name: Optional[str] = None) -> list:
    name = name or "<anonymous>"
    item_types_str = ", ".join([it.__name__ for it in item_types])
    if not isinstance(v, list):
        raise TypeError(f"{name} is expected to be list of {item_types_str} but it's not even a list")
    for item in v:
        if not isinstance(item, tuple(item_types)):
            raise TypeError(f"{name} is expected to be list of {item_types_str} but includes invalid item '{item}'")
    return v


def validated_list_content_type(v: Any, name: Optional[str] = None) -> list[constants.ContentType]:
    return _validated_list(v, item_types=[constants.ServiceContentType, constants.MediaContentType], name=name)


def validated_list_chat_type(v: Any, name: Optional[str] = None) -> list[constants.ChatType]:
    return _validated_list(v, item_types=[constants.ChatType], name=name)


def is_command(text: str) -> bool:
    r"""
    Checks if `text` is a command. Telegram chat commands start with the '/' character.

    :param text: Text to check.
    :return: True if `text` is a command, else False.
    """
    if text is None:
        return False
    return text.startswith("/")


def extract_command(text: Optional[str]) -> Optional[str]:
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
    if text is None:
        return None
    return text.split()[0].split("@")[0][1:] if is_command(text) else None


def extract_arguments(text: str) -> Optional[str]:
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
    if result is None:
        return None
    else:
        return result.group(2) if is_command(text) else None


def split_string(text: str, chars_per_string: int) -> List[str]:
    """
    Splits one string into multiple strings, with a maximum amount of `chars_per_string` characters per string.
    This is very useful for splitting one giant message into multiples.

    :param text: The text to split
    :param chars_per_string: The number of characters per line the text is split into.
    :return: The splitted text as a list of strings.
    """
    return [text[i : i + chars_per_string] for i in range(0, len(text), chars_per_string)]


def smart_split(text: str, chars_per_string: int = MAX_MESSAGE_LENGTH) -> List[str]:
    r"""
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

    if chars_per_string > MAX_MESSAGE_LENGTH:
        chars_per_string = MAX_MESSAGE_LENGTH

    parts = []
    while True:
        if len(text) < chars_per_string:
            parts.append(text)
            return parts

        part = text[:chars_per_string]

        if "\n" in part:
            part = _text_before_last("\n")
        elif ". " in part:
            part = _text_before_last(". ")
        elif " " in part:
            part = _text_before_last(" ")

        parts.append(part)
        text = text[len(part) :]


def escape(text: str) -> str:
    """
    Replaces the following chars in `text` ('&' with '&amp;', '<' with '&lt;' and '>' with '&gt;').

    :param text: the text to escape
    :return: the escaped text
    """
    chars = {"&": "&amp;", "<": "&lt;", ">": "&gt;"}
    for old, new in chars.items():
        text = text.replace(old, new)
    return text


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
            # noinspection PyProtectedMember
            or_event._wait(3)

    for e in events:
        orify(e, changed)
    or_event._wait = or_event.wait
    or_event.wait = busy_wait
    changed()
    return or_event


def chunks(lst, n):
    """Yield successive n-sized chunks from lst."""
    # https://stackoverflow.com/a/312464/9935473
    for i in range(0, len(lst), n):
        yield lst[i : i + n]


def generate_random_token():
    return "".join(random.sample(string.ascii_letters, 16))


def deprecated(warn: bool = True, alternative: Optional[Callable] = None, deprecation_text=None):
    """
    Use this decorator to mark functions as deprecated.
    When the function is used, an info (or warning if `warn` is True) is logged.

    :param warn: If True a warning is logged else an info
    :param alternative: The new function to use instead
    :param deprecation_text: Custom deprecation text
    """

    def decorator(function):
        def wrapper(*args, **kwargs):
            info = f"`{function.__name__}` is deprecated."
            if alternative:
                info += f" Use `{alternative.__name__}` instead"
            if deprecation_text:
                info += " " + deprecation_text
            if not warn:
                logger.info(info)
            else:
                logger.warning(info)
            return function(*args, **kwargs)

        return wrapper

    return decorator
