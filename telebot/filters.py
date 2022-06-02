import logging
from abc import ABC, abstractmethod
from typing import Generic, TypeVar, Union

from telebot import types
from telebot.check_text import CheckText
from telebot.types import ChatMember
from telebot.types import service as service_types

logger = logging.getLogger(__name__)


_UCT = TypeVar("_UCT", bound=service_types.UpdateContent)


class SimpleCustomFilter(ABC, Generic[_UCT]):
    """
    Simple Custom Filter base class.
    Create child class with check() method.
    Accepts only message, returns bool value, that is compared with given in handler.

    Child classes should have .key property.
    """

    key: str

    @abstractmethod
    async def check(self, update_content: _UCT) -> bool:
        ...


class AdvancedCustomFilter(ABC, Generic[_UCT]):
    """
    Simple Custom Filter base class.
    Create child class with check() method.
    Accepts two parameters, returns bool: True - filter passed, False - filter failed.
    message: Message class
    text: Filter value given in handler

    Child classes should have .key property.
    """

    key: str

    @abstractmethod
    async def check(self, update_content: _UCT, filter_value: service_types.FilterValue) -> bool:
        ...


AnyCustomFilter = Union[SimpleCustomFilter, AdvancedCustomFilter]


class TextMatchFilter(AdvancedCustomFilter[types.Message]):
    """
    Filter to check Text message.
    key: text

    Example:
    @bot.message_handler(text=['account'])
    """

    key = "text"

    async def check(self, update_content: types.Message, filter_value: service_types.FilterValue) -> bool:
        if isinstance(filter_value, CheckText):
            return await filter_value.check(update_content)
        elif isinstance(filter_value, list):
            return update_content.text in filter_value
        elif isinstance(filter_value, str):
            return filter_value == update_content.text
        else:
            logger.warning(f"Unexpected filter value passed to {self.__class__.__name__}: {filter_value}")
            return False


class ChatFilter(AdvancedCustomFilter[types.TiedToChat]):
    """
    Check whether chat_id corresponds to given chat_id.

    Example:
    @bot.message_handler(chat_id=[99999])
    """

    key = "chat_id"

    async def check(self, update_content: types.TiedToChat, filter_value: service_types.FilterValue) -> bool:
        if isinstance(filter_value, list):
            return update_content.chat.id in filter_value
        else:
            return False


class IsForwardedFilter(SimpleCustomFilter[types.Message]):
    """
    Check whether message was forwarded from channel or group.

    Example:

    @bot.message_handler(is_forwarded=True)
    """

    key = "is_forwarded"

    async def check(self, update_content: types.Message) -> bool:
        return update_content.forward_from_chat is not None


class IsReplyFilter(SimpleCustomFilter[types.Message]):
    """
    Check whether message is a reply.

    Example:

    @bot.message_handler(is_reply=True)
    """

    key = "is_reply"

    async def check(self, update_content: types.Message) -> bool:
        return update_content.reply_to_message is not None


class LanguageFilter(AdvancedCustomFilter[types.Message]):
    """
    Check users language_code.

    Example:

    @bot.message_handler(language_code=['ru'])
    """

    key = "language_code"

    async def check(self, update_content: types.Message, filter_value: service_types.FilterValue) -> bool:
        if isinstance(filter_value, list):
            languages = filter_value
        elif isinstance(filter_value, str):
            languages = [filter_value]
        else:
            return False
        return update_content.from_user.language_code in languages


class IsBotAdminFilter(SimpleCustomFilter[types.Message]):
    """
    Check whether the user is administrator / owner of the chat.

    Example:
    @bot.message_handler(chat_types=['supergroup'], is_chat_admin=True)
    """

    key = "is_chat_admin"

    def __init__(self, bot: "AsyncTeleBot"):  # type: ignore
        self._bot = bot

    async def check(self, update_content: types.Message) -> bool:
        result: ChatMember = await self._bot.get_chat_member(update_content.chat.id, update_content.from_user.id)
        return result.status in ["creator", "administrator"]


class IsDigitFilter(SimpleCustomFilter[types.Message]):
    """
    Filter to check whether the string is made up of only digits.

    Example:
    @bot.message_handler(is_digit=True)
    """

    key = "is_digit"

    async def check(self, update_content: types.Message) -> bool:
        return update_content.text is not None and update_content.text.isdigit()
