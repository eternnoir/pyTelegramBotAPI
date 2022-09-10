import socket

from telebot import types


def mock_message_update(text: str) -> types.Update:
    params = {"text": text}
    chat = types.Chat(1312, "private")
    user = types.User(11, False, "John Doe")
    message = types.Message(1, user, 25, chat, "text", params, "")
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


def find_free_port():
    """https://stackoverflow.com/a/36331860/14418929"""
    with socket.socket() as s:
        s.bind(("", 0))  # Bind to a free port provided by the host.
        return s.getsockname()[1]
