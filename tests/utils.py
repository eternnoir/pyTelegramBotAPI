import socket
from collections import defaultdict
from dataclasses import dataclass
from typing import Any, Optional

from telebot import AsyncTeleBot, api, constants, filters, types


def mock_message(text: str) -> types.Message:
    params = {"text": text}
    chat = types.User(11, False, "test")
    return types.Message(1, None, None, chat, "text", params, "")


def mock_message_update(text: str) -> types.Update:
    params = {"text": text}
    chat = types.User(11, False, "test")
    message = types.Message(1, None, None, chat, "text", params, "")
    edited_message = None
    channel_post = None
    edited_channel_post = None
    inline_query = None
    chosen_inline_result = None
    callback_query = None
    shipping_query = None
    pre_checkout_query = None
    poll = None
    poll_answer = None
    my_chat_member = None
    chat_member = None
    chat_join_request = None
    return types.Update(
        -1001234038283,
        message,
        edited_message,
        channel_post,
        edited_channel_post,
        inline_query,
        chosen_inline_result,
        callback_query,
        shipping_query,
        pre_checkout_query,
        poll,
        poll_answer,
        my_chat_member,
        chat_member,
        chat_join_request,
        _json_dict={"json": "data", "here": 1},
    )


@dataclass
class MethodCall:
    args: tuple[Any, ...]
    kwargs: dict[str, Any]


def capturing(method):
    async def decorated(self: "MockTeleBot", *args, **kwargs):
        self.method_calls[method.__name__].append(MethodCall(args, kwargs))
        return await method(self, *args, **kwargs)

    return decorated


class MockTeleBot(AsyncTeleBot):
    """Please patch methods as needed when you add new tests"""

    def __init__(
        self,
        token: str,
        parse_mode: Optional[str] = None,
        offset: Optional[int] = None,
        custom_filters: Optional[list[filters.AnyCustomFilter]] = None,
        force_allowed_updates: Optional[list[constants.UpdateType]] = None,
    ):
        super().__init__(token, parse_mode, offset, custom_filters, force_allowed_updates)
        self.method_calls: dict[str, list[MethodCall]] = defaultdict(list)

    @capturing
    async def delete_webhook(self, drop_pending_updates: Optional[bool] = None, timeout: Optional[float] = None):
        pass

    @capturing
    async def set_webhook(
        self,
        url: str,
        certificate: Optional[api.FileObject] = None,
        max_connections: Optional[int] = None,
        ip_address: Optional[str] = None,
        drop_pending_updates: Optional[bool] = None,
        timeout: Optional[float] = None,
    ):
        return True


def find_free_port():
    """https://stackoverflow.com/a/36331860/14418929"""
    with socket.socket() as s:
        s.bind(("", 0))  # Bind to a free port provided by the host.
        return s.getsockname()[1]
