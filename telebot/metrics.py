import contextlib
import time
from typing import Any, Generator, Optional, TypedDict

from typing_extensions import Required


class UserInfo(TypedDict):
    user_id_hash: str
    language_code: Optional[str]


class MessageInfo(TypedDict):
    is_forwarded: bool
    is_reply: bool
    content_type: str  # see Message class for a complete list


class ExceptionInfo(TypedDict):
    type_name: str  # e.g. ValueError, KeyError
    body: str  # str(exception_obj)


class TelegramUpdateMetrics(TypedDict, total=False):
    bot_prefix: Required[str]
    received_at: Required[float]  # UNIX timestamp
    update_id: int

    # update content type, e.g. "message" or "pre_checkout_query"
    # see https://core.telegram.org/bots/api#update
    update_type: str

    # qualified function name or explicitly specified one (e.g. @bot.message_handler(..., name="hello"))
    # None = no handler matched, update ignored
    handler_name: Optional[str]

    # if an update handler returns HandlerResult with non-empty metrics, they are copied here
    handler_metrics: dict[str, Any]

    # list of durations for each handler tested
    handler_test_durations: list[float]
    # duration for matched handler execution
    processing_duration: float
    # set when the matched handler raised the exception
    exception_info: ExceptionInfo

    # info about user who initiated the update (message author, button clicker, etc)
    user_info: UserInfo
    # info about message within the update
    message_info: MessageInfo


@contextlib.contextmanager
def save_handler_test_duration(metrics: TelegramUpdateMetrics) -> Generator[None, None, None]:
    start_time = time.time()
    try:
        yield
    finally:
        metrics.setdefault("handler_test_durations", []).append(time.time() - start_time)


@contextlib.contextmanager
def save_processing_duration(metrics: TelegramUpdateMetrics) -> Generator[None, None, None]:
    start_time = time.time()
    try:
        yield
    finally:
        metrics["processing_duration"] = time.time() - start_time
