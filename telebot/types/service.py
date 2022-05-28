from typing import Callable, Coroutine, TypedDict, TypeVar, Union

from typing_extensions import NotRequired

from telebot import callback_data, types
from telebot.text_matcher import TextMatcher

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


_UCT = TypeVar("_UCT", bound=UpdateContent)

FilterFunc = Union[Callable[[_UCT], bool], Callable[[_UCT], Coroutine[None, None, bool]]]

FilterValue = Union[
    str,  # simple filters like text="hello"
    list[str],  # most common filters like chat_types=["private", "group"]
    list[int],  # chat id filtering
    callback_data.CallbackData,  # callback query handler for a particular CallbackData
    FilterFunc,
    bool,  # to turn on CustomFilters
    TextMatcher,
    None,  # no filter
]

NoneCoroutine = Coroutine[None, None, None]
HandlerFunction = Union[
    Callable[[_UCT], NoneCoroutine],
    Callable[[_UCT, "AsyncTeleBot"], NoneCoroutine],  # type: ignore
]


class Handler(TypedDict):
    function: HandlerFunction
    filters: dict[str, FilterValue]
    name: NotRequired[str]


ChatId = Union[str, int]
