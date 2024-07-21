from abc import ABC
from typing import Optional, Union
from telebot.handler_backends import State

from telebot import types

from telebot.states import resolve_context

class SimpleCustomFilter(ABC):
    """
    Simple Custom Filter base class.
    Create child class with check() method.
    Accepts only message, returns bool value, that is compared with given in handler.

    Child classes should have .key property.

    .. code-block:: python3
        :caption: Example on creating a simple custom filter.

        class ForwardFilter(SimpleCustomFilter):
            # Check whether message was forwarded from channel or group.
            key = 'is_forwarded'

            def check(self, message):
                return message.forward_date is not None

    """

    key: str = None

    def check(self, message):
        """
        Perform a check.
        """
        pass


class AdvancedCustomFilter(ABC):
    """
    Advanced Custom Filter base class.
    Create child class with check() method.
    Accepts two parameters, returns bool: True - filter passed, False - filter failed.
    message: Message class
    text: Filter value given in handler

    Child classes should have .key property.

    .. code-block:: python3
        :caption: Example on creating an advanced custom filter.

        class TextStartsFilter(AdvancedCustomFilter):
            # Filter to check whether message starts with some text.
            key = 'text_startswith'

            def check(self, message, text):
                return message.text.startswith(text)
    """

    key: str = None

    def check(self, message, text):
        """
        Perform a check.
        """
        pass


class TextFilter:
    """
    Advanced text filter to check (types.Message, types.CallbackQuery, types.InlineQuery, types.Poll)

    example of usage is in examples/custom_filters/advanced_text_filter.py

    :param equals: string, True if object's text is equal to passed string
    :type equals: :obj:`str`

    :param contains: list[str] or tuple[str], True if any string element of iterable is in text
    :type contains: list[str] or tuple[str]

    :param starts_with: string, True if object's text starts with passed string
    :type starts_with: :obj:`str`

    :param ends_with: string, True if object's text starts with passed string
    :type ends_with: :obj:`str`

    :param ignore_case: bool (default False), case insensitive
    :type ignore_case: :obj:`bool`

    :raises ValueError: if incorrect value for a parameter was supplied

    :return: None
    """

    def __init__(self,
                 equals: Optional[str] = None,
                 contains: Optional[Union[list, tuple]] = None,
                 starts_with: Optional[Union[str, list, tuple]] = None,
                 ends_with: Optional[Union[str, list, tuple]] = None,
                 ignore_case: bool = False):
        """
        :param equals: string, True if object's text is equal to passed string
        :type equals: :obj:`str`

        :param contains: list[str] or tuple[str], True if any string element of iterable is in text
        :type contains: list[str] or tuple[str]

        :param starts_with: string, True if object's text starts with passed string
        :type starts_with: :obj:`str`

        :param ends_with: string, True if object's text starts with passed string
        :type ends_with: :obj:`str`

        :param ignore_case: bool (default False), case insensitive
        :type ignore_case: :obj:`bool`

        :raises ValueError: if incorrect value for a parameter was supplied

        :return: None
        """
        
        to_check = sum((pattern is not None for pattern in (equals, contains, starts_with, ends_with)))
        if to_check == 0:
            raise ValueError('None of the check modes was specified')

        self.equals = equals
        self.contains = self._check_iterable(contains, filter_name='contains')
        self.starts_with = self._check_iterable(starts_with, filter_name='starts_with')
        self.ends_with = self._check_iterable(ends_with, filter_name='ends_with')
        self.ignore_case = ignore_case

    def _check_iterable(self, iterable, filter_name: str):
        if not iterable:
            pass
        elif not isinstance(iterable, str) and not isinstance(iterable, list) and not isinstance(iterable, tuple):
            raise ValueError(f"Incorrect value of {filter_name!r}")
        elif isinstance(iterable, str):
            iterable = [iterable]
        elif isinstance(iterable, list) or isinstance(iterable, tuple):
            iterable = [i for i in iterable if isinstance(i, str)]
        return iterable

    def check(self, obj: Union[types.Message, types.CallbackQuery, types.InlineQuery, types.Poll]):
        """
        :meta private:
        """

        if isinstance(obj, types.Poll):
            text = obj.question
        elif isinstance(obj, types.Message):
            text = obj.text or obj.caption
            if text is None:
                return False
        elif isinstance(obj, types.CallbackQuery):
            text = obj.data
        elif isinstance(obj, types.InlineQuery):
            text = obj.query
        else:
            return False

        if self.ignore_case:
            text = text.lower()

            if self.equals:
                self.equals = self.equals.lower()
            elif self.contains:
                self.contains = tuple(map(str.lower, self.contains))
            elif self.starts_with:
                self.starts_with = tuple(map(str.lower, self.starts_with))
            elif self.ends_with:
                self.ends_with = tuple(map(str.lower, self.ends_with))

        if self.equals:
            result = self.equals == text
            if result:
                return True
            elif not result and not any((self.contains, self.starts_with, self.ends_with)):
                return False

        if self.contains:
            result = any([i in text for i in self.contains])
            if result:
                return True
            elif not result and not any((self.starts_with, self.ends_with)):
                return False

        if self.starts_with:
            result = any([text.startswith(i) for i in self.starts_with])
            if result:
                return True
            elif not result and not self.ends_with:
                return False

        if self.ends_with:
            return any([text.endswith(i) for i in self.ends_with])

        return False

class TextMatchFilter(AdvancedCustomFilter):
    """
    Filter to check Text message.

    .. code-block:: python3
        :caption: Example on using this filter:

        @bot.message_handler(text=['account'])
        # your function
    """

    key = 'text'

    def check(self, message, text):
        """
        :meta private:
        """
        if isinstance(text, TextFilter):
            return text.check(message)
        elif isinstance(text, list):
            return message.text in text
        else:
            return text == message.text


class TextContainsFilter(AdvancedCustomFilter):
    """
    Filter to check Text message.
    key: text


    .. code-block:: python3
        :caption: Example on using this filter:

        # Will respond if any message.text contains word 'account'
        @bot.message_handler(text_contains=['account'])
        # your function
    """

    key = 'text_contains'

    def check(self, message, text):
        """
        :meta private:
        """
        if not isinstance(text, str) and not isinstance(text, list) and not isinstance(text, tuple):
            raise ValueError("Incorrect text_contains value")
        elif isinstance(text, str):
            text = [text]
        elif isinstance(text, list) or isinstance(text, tuple):
            text = [i for i in text if isinstance(i, str)]

        return any([i in message.text for i in text])


class TextStartsFilter(AdvancedCustomFilter):
    """
    Filter to check whether message starts with some text.

    .. code-block:: python3
        :caption: Example on using this filter:

        # Will work if message.text starts with 'sir'.
        @bot.message_handler(text_startswith='sir')
        # your function
    """

    key = 'text_startswith'

    def check(self, message, text):
        """
        :meta private:
        """
        return message.text.startswith(text)


class ChatFilter(AdvancedCustomFilter):
    """
    Check whether chat_id corresponds to given chat_id.

    .. code-block:: python3
        :caption: Example on using this filter:

        @bot.message_handler(chat_id=[99999])
        # your function
    """

    key = 'chat_id'

    def check(self, message, text):
        """
        :meta private:
        """
        if isinstance(message, types.CallbackQuery):
            return message.message.chat.id in text
        return message.chat.id in text


class ForwardFilter(SimpleCustomFilter):
    """
    Check whether message was forwarded from channel or group.

    .. code-block:: python3 
        :caption: Example on using this filter:

        @bot.message_handler(is_forwarded=True)
        # your function
    """

    key = 'is_forwarded'

    def check(self, message):
        """
        :meta private:
        """
        return message.forward_origin is not None


class IsReplyFilter(SimpleCustomFilter):
    """
    Check whether message is a reply.

    .. code-block:: python3
        :caption: Example on using this filter:

        @bot.message_handler(is_reply=True)
        # your function
    """

    key = 'is_reply'

    def check(self, message):
        """
        :meta private:
        """
        if isinstance(message, types.CallbackQuery):
            return message.message.reply_to_message is not None
        return message.reply_to_message is not None


class LanguageFilter(AdvancedCustomFilter):
    """
    Check users language_code.

    .. code-block:: python3
        :caption: Example on using this filter:

        @bot.message_handler(language_code=['ru'])
        # your function
    """

    key = 'language_code'

    def check(self, message, text):
        """
        :meta private:
        """
        if isinstance(text, list):
            return message.from_user.language_code in text
        else:
            return message.from_user.language_code == text


class IsAdminFilter(SimpleCustomFilter):
    """
    Check whether the user is administrator / owner of the chat.

    .. code-block:: python3
        :caption: Example on using this filter:

        @bot.message_handler(chat_types=['supergroup'], is_chat_admin=True)
        # your function
    """

    key = 'is_chat_admin'

    def __init__(self, bot):
        self._bot = bot

    def check(self, message):
        """
        :meta private:
        """
        if isinstance(message, types.CallbackQuery):
            return self._bot.get_chat_member(message.message.chat.id, message.from_user.id).status in ['creator', 'administrator']
        return self._bot.get_chat_member(message.chat.id, message.from_user.id).status in ['creator', 'administrator']


class StateFilter(AdvancedCustomFilter):
    """
    Filter to check state.

    .. code-block:: python3
        :caption: Example on using this filter:
        
        @bot.message_handler(state=1)
        # your function
    """

    def __init__(self, bot):
        self.bot = bot

    key = 'state'

    def check(self, message, text):
        """
        :meta private:
        """
        
        chat_id, user_id, business_connection_id, bot_id, message_thread_id = resolve_context(message, self.bot._user.id)

        if chat_id is None:
            chat_id = user_id # May change in future

        if isinstance(text, list):
            new_text = []
            for i in text:
                if isinstance(i, State): i = i.name
                new_text.append(i)
            text = new_text
        elif isinstance(text, State):
            text = text.name
        
        user_state = self.bot.current_states.get_state(
            chat_id=chat_id,
            user_id=user_id,
            business_connection_id=business_connection_id,
            bot_id=bot_id,
            message_thread_id=message_thread_id
        )

        # CHANGED BEHAVIOUR
        if text == "*" and user_state is not None:
            return True

        if user_state == text:
            return True
        elif type(text) is list and user_state in text:
            return True
        return False

class IsDigitFilter(SimpleCustomFilter):
    """
    Filter to check whether the string is made up of only digits.

    .. code-block:: python3
        :caption: Example on using this filter:

        @bot.message_handler(is_digit=True)
        # your function
    """
    key = 'is_digit'

    def check(self, message):
        """
        :meta private:
        """
        return message.text.isdigit()
