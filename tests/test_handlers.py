from typing import Optional
from uuid import uuid4

import pytest

import telebot
from telebot import AsyncTeleBot, types
from tests.utils import mock_message, mock_message_update


async def test_message_listener_receives_updates():
    tb = telebot.AsyncTeleBot("")
    updated_received_by_listener = None

    @tb.update_listener
    async def listener(message: types.Update):
        nonlocal updated_received_by_listener
        updated_received_by_listener = message

    update = mock_message_update("hello world")
    await tb.process_new_updates([update])
    assert update is updated_received_by_listener


@pytest.fixture(params=[True, False])
def pass_bot_to_handler_func(request) -> bool:
    return request.param


@pytest.mark.parametrize(
    "message_text, handler_filter_kwargs, must_be_received",
    [
        pytest.param("/help", {"commands": ["help", "start"]}, True),
        pytest.param("/start", {"commands": ["help", "start"]}, True),
        pytest.param("/help@botname", {"commands": ["help", "start"]}, True),
        pytest.param("/help как дела привет", {"commands": ["help", "start"]}, True),
        pytest.param("/hlp", {"commands": ["help", "start"]}, False),
        pytest.param("привет!", {"commands": ["help", "start"]}, False),
        pytest.param(
            "https://web.telegram.org/",
            {"regexp": r"((https?):((//)|(\\\\))+([\w\d:#@%/;$()~_?\+-=\\\.&](#!)?)*)"},
            True,
        ),
        pytest.param(
            "web.telegram.org/",
            {"regexp": r"((https?):((//)|(\\\\))+([\w\d:#@%/;$()~_?\+-=\\\.&](#!)?)*)"},
            False,
        ),
        pytest.param("lambda_text", {"func": lambda message: r"lambda" in message.text}, True),
        pytest.param("other_text", {"func": lambda message: r"lambda" in message.text}, False),
    ],
)
async def test_message_handler_basic(
    message_text: str, handler_filter_kwargs: dict, must_be_received: bool, pass_bot_to_handler_func: bool
):
    tb = telebot.AsyncTeleBot("")
    update = mock_message_update(message_text)
    got_msg_confirmation = uuid4().hex

    async def handler_simple(message: types.Message):
        message.text = got_msg_confirmation

    if pass_bot_to_handler_func:

        async def handler_with_bot(message: types.Message, bot: AsyncTeleBot):
            assert bot is tb
            await handler_simple(message)

        tb.message_handler(**handler_filter_kwargs)(handler_with_bot)
    else:
        tb.message_handler(**handler_filter_kwargs)(handler_simple)

    await tb.process_new_updates([update])
    assert update.message is not None
    if must_be_received:
        assert update.message.text == got_msg_confirmation
    else:
        assert update.message.text == message_text


@pytest.mark.parametrize(
    "message_text, handler_filter_kwargs_list, message_received_by_expected",
    [
        pytest.param("/start", [{"commands": ["start"]}], 0, id="single handler"),
        pytest.param("/start", [{"commands": ["start"]}, {}], 0, id="no priority - first handler gets the message"),
        pytest.param("/start", [{}, {"commands": ["start"]}], 0, id="no priority - first handler gets the message"),
        pytest.param(
            "/start",
            [{"commands": ["start"]}, {"commands": ["start"], "priority": 2}],
            1,
            id="second handler has higher priority than the first",
        ),
        pytest.param(
            "/start",
            [{}, {"commands": ["start"], "priority": 2}],
            1,
            id="second handler has higher priority than the first, even when it's catch-all",
        ),
    ],
)
async def test_message_handler_priority(
    message_text: str,
    handler_filter_kwargs_list: list[dict],
    message_received_by_expected: int,
):
    tb = telebot.AsyncTeleBot("")
    update = mock_message_update(message_text)

    message_received_by: Optional[int] = None

    def create_handler(idx: int):
        async def handler(message: types.Message):
            nonlocal message_received_by
            message_received_by = idx

        return handler

    for idx, handler_kwargs in enumerate(handler_filter_kwargs_list):
        decorator = tb.message_handler(**handler_kwargs)
        decorator(create_handler(idx))

    await tb.process_new_updates([update])
    assert message_received_by == message_received_by_expected
