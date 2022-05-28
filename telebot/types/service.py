from typing import (
    Callable,
    Coroutine,
    ForwardRef,
    Protocol,
    TypedDict,
    TypeVar,
    Union,
    overload,
)

from typing_extensions import NotRequired

from telebot import callback_data, types
from telebot.text_matcher import TextMatcher
from telebot.types.constants import ContentType

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


_UCT = TypeVar("_UCT", bound=UpdateContent, contravariant=True)


class FilterFunc(Protocol[_UCT]):
    def __call__(self, update_content: _UCT) -> Union[bool, Coroutine[None, None, bool]]:
        pass


FilterValue = Union[
    str,  # simple filters like text="hello"
    list[str],  # most common filters like chat_types=["private", "group"]
    list[ContentType],
    list[int],  # chat id filtering
    callback_data.CallbackData,  # callback query handler for a particular CallbackData
    FilterFunc,
    bool,  # to turn on CustomFilters
    TextMatcher,
    None,  # no filter
]

NoneCoro = Coroutine[None, None, None]


class HandlerFunction(Protocol[_UCT]):
    @overload
    async def __call__(self, update_content: _UCT) -> None:
        ...

    @overload
    async def __call__(self, update_content: _UCT, bot: "AsyncTeleBot") -> None:  # type: ignore
        ...


class Handler(TypedDict):
    function: HandlerFunction
    filters: dict[str, FilterValue]
    name: NotRequired[str]


ChatId = Union[str, int]
