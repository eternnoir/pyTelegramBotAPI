from typing import Callable, Coroutine, ForwardRef, Optional, TypedDict, TypeVar, Union

from telebot import callback_data, types

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


T = TypeVar("T", bound=UpdateContent)

FilterFunc = Union[Callable[[T], bool], Callable[[T], Coroutine[None, None, bool]]]
FilterValue = Union[str, list[str], callback_data.CallbackData, FilterFunc, None, bool]

NoneCoroutine = Coroutine[None, None, None]
HandlerFunction = Union[
    Callable[[T], NoneCoroutine],
    Callable[[T, ForwardRef("AsyncTeleBot")], NoneCoroutine],
]


class Handler(TypedDict):
    function: HandlerFunction
    filters: dict[str, FilterValue]
    name: Optional[str]
