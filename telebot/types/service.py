import abc
from dataclasses import dataclass
from typing import (
    Any,
    Coroutine,
    Optional,
    Protocol,
    TypedDict,
    TypeVar,
    Union,
)

from typing_extensions import NotRequired

from telebot import callback_data, types
from telebot.check_text import CheckText
from telebot.types.constants import ChatType, ContentType

UpdateContent = Union[
    types.Message,
    types.InlineQuery,
    types.ChosenInlineResult,
    types.ChosenInlineResult,
    types.CallbackQuery,
    types.ShippingQuery,
    types.PreCheckoutQuery,
    types.Poll,
    types.PollAnswer,
    types.ChatMemberUpdated,
    types.ChatJoinRequest,
]


UpdateContentT = TypeVar("UpdateContentT", bound=UpdateContent, contravariant=True)


class FilterFunc(Protocol[UpdateContentT]):
    def __call__(self, update_content: UpdateContentT) -> Union[bool, Coroutine[None, None, bool]]: ...


FilterValue = Union[
    str,  # simple filters like text="hello"
    int,  # numeric id filtering
    list[str],  # most common filters like chat_types=["private", "group"]
    list[ContentType],
    list[ChatType],
    list[int],  # chat id filtering
    callback_data.CallbackData,  # callback query handler for a particular CallbackData
    FilterFunc,
    bool,  # to turn on CustomFilters
    CheckText,
    None,  # no filter
]

NoneCoro = Coroutine[None, None, None]


@dataclass
class HandlerResult:
    metrics: dict[str, Any] | None = None
    continue_to_other_handlers: bool = False
    callback_query_answered: bool = False


class SimpleHandlerFunction(Protocol[UpdateContentT]):
    async def __call__(self, update_content: UpdateContentT, /) -> HandlerResult | None: ...


class AbstractAsyncTeleBot(abc.ABC):
    pass


class HandlerFunctionWithBot(Protocol[UpdateContentT]):
    async def __call__(self, update_content: UpdateContentT, bot: AbstractAsyncTeleBot, /) -> HandlerResult | None: ...


HandlerFunction = SimpleHandlerFunction | HandlerFunctionWithBot


class Handler(TypedDict):
    function: HandlerFunction
    filters: dict[str, FilterValue]
    name: NotRequired[str]
    priority: NotRequired[Optional[int]]


ChatId = Union[str, int]
