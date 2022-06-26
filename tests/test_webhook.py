import asyncio
import datetime
from typing import Generator
from uuid import uuid4

import aiohttp
import pytest

from telebot import AsyncTeleBot, types
from telebot.runner import BotRunner
from telebot.webhook import WebhookApp
from tests.utils import MockTeleBot

MOCK_BOT_NAME = "testing-bot"
MOCK_TOKEN = uuid4().hex


COUNTED_MILLISECONDS = 0
RECEIVED_COMMANDS: list[types.Message] = []
RECEIVED_MESSAGES: list[types.Message] = []


@pytest.fixture
def bot() -> MockTeleBot:
    bot = MockTeleBot(MOCK_TOKEN)

    @bot.message_handler(commands=["start", "help"])
    async def receive_cmd(m: types.Message):
        RECEIVED_COMMANDS.append(m)

    @bot.message_handler()
    def receive_message(m: types.Message):  # bot converts all funcs to coroutine funcs on its own
        RECEIVED_MESSAGES.append(m)

    return bot


@pytest.fixture
def bot_runner(bot: AsyncTeleBot) -> BotRunner:
    async def count_milliseconds():
        global COUNTED_MILLISECONDS
        while True:
            COUNTED_MILLISECONDS += 10
            await asyncio.sleep(0.01)

    return BotRunner(
        bot_prefix=MOCK_BOT_NAME,
        bot=bot,
        background_jobs=[count_milliseconds()],
    )


async def test_bot_runner(bot_runner: BotRunner, bot: MockTeleBot, aiohttp_client):
    subroute = bot_runner.webhook_subroute()
    route = "/webhook/" + subroute + "/"
    webhook_app = WebhookApp("http://127.0.0.1")
    await webhook_app.add_bot_runner(bot_runner)
    client: aiohttp.ClientSession = await aiohttp_client(webhook_app.aiohttp_app)

    assert MOCK_TOKEN not in subroute

    assert len(bot.method_calls["delete_webhook"]) == 1
    assert len(bot.method_calls["set_webhook"]) == 1
    assert bot.method_calls["set_webhook"][0].kwargs == {"url": "http://127.0.0.1" + route}

    for i, text in enumerate(["текст сообщения", "/start", "еще текст", "/help"]):
        resp = await client.post(
            route,
            json={
                "update_id": 10001110101 + i,
                "message": {
                    "message_id": 53 + i,
                    "from": {
                        "id": 1312,
                        "is_bot": False,
                        "first_name": "раз",
                        "last_name": "два",
                        "username": "testing",
                        "language_code": "en",
                    },
                    "chat": {
                        "id": 1312,
                        "first_name": "раз",
                        "last_name": "два",
                        "username": "testing",
                        "type": "private",
                    },
                    "date": 1653769757 + i,
                    "text": text,
                },
            },
        )
        assert resp.status == 200

    assert len(RECEIVED_MESSAGES) == 2
    assert [m.text for m in RECEIVED_MESSAGES] == ["текст сообщения", "еще текст"]

    assert len(RECEIVED_COMMANDS) == 2
    assert [m.text for m in RECEIVED_COMMANDS] == ["/start", "/help"]

    assert COUNTED_MILLISECONDS > 1, "Background job didn't count milliseconds!"


@pytest.mark.parametrize(
    "bot_name, token, expected_route_prefix",
    [
        pytest.param("hello-world", uuid4().hex, "hello-world"),
        pytest.param("hello world", uuid4().hex, "hello-world"),
        pytest.param(" Very Bad  Name For   a Bot!!!   ", uuid4().hex, "Very-Bad-Name-For-a-Bot%21%21%21"),
    ],
)
def test_webhook_route_generation(bot_name: str, token: str, expected_route_prefix: str):
    bot = AsyncTeleBot(token)
    bot_runner = BotRunner(bot_prefix=bot_name, bot=bot)
    assert bot_runner.webhook_subroute().startswith(expected_route_prefix)
