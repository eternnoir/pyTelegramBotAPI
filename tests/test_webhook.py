import asyncio
import gc
import signal
from uuid import uuid4

import aiohttp
import pytest

from telebot import AsyncTeleBot, types
from telebot.graceful_shutdown import GracefulShutdownCondition, PreventShutdown
from telebot.runner import BotRunner
from telebot.test_util import MockedAsyncTeleBot
from telebot.webhook import WebhookApp
from tests.utils import find_free_port

MOCK_BOT_NAME = "testing-bot"
MOCK_TOKEN = uuid4().hex


COUNTED_MILLISECONDS = 0
RECEIVED_COMMANDS: list[types.Message] = []
RECEIVED_MESSAGES: list[types.Message] = []


@pytest.fixture
def bot() -> MockedAsyncTeleBot:
    bot = MockedAsyncTeleBot(MOCK_TOKEN)

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


async def test_bot_runner(bot_runner: BotRunner, bot: MockedAsyncTeleBot, aiohttp_client):
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


async def test_webhook_app_graceful_shutdown():
    # constructing bot object
    bot = MockedAsyncTeleBot("")
    message_processing_started = False
    message_processing_ended = False

    @bot.message_handler()
    async def time_consuming_message_processing(message: types.Message):
        nonlocal message_processing_started
        nonlocal message_processing_ended
        message_processing_started = True
        await asyncio.sleep(2)
        message_processing_ended = True

    # adding background task that prevents shutdown
    background_job_1_completed = False
    background_job_2_completed = False

    async def background_job_1():
        async with PreventShutdown("performing background task 1"):
            await asyncio.sleep(3)
            nonlocal background_job_1_completed
            background_job_1_completed = True

    prevent_shutdown = PreventShutdown("performing background task 2")

    @prevent_shutdown
    async def background_job_2():
        await asyncio.sleep(4)
        nonlocal background_job_2_completed
        background_job_2_completed = True
        async with prevent_shutdown.allow_shutdown():
            await asyncio.sleep(10)

    # constructing bot runner
    bot_runner = BotRunner("testing", bot, background_jobs=[background_job_1(), background_job_2()])
    subroute = bot_runner.webhook_subroute()
    base_url = "http://localhost"
    route = "/webhook/" + subroute + "/"
    webhook_app = WebhookApp(base_url)
    await webhook_app.add_bot_runner(bot_runner)

    # creating and running webhook app with system exit catching wrapper
    port = find_free_port()
    server_listening = asyncio.Future()
    server_exited_with_sys_exit = asyncio.Future()

    async def on_server_listening():
        server_listening.set_result(None)

    async def safe_run_webhook_app():
        try:
            await webhook_app.run(port, graceful_shutdown=True, on_server_listening=on_server_listening)
        except SystemExit:
            server_exited_with_sys_exit.set_result(None)

    server_task = asyncio.create_task(safe_run_webhook_app())
    await server_listening

    # validating setup sequence in bot
    assert len(bot.method_calls["delete_webhook"]) == 1
    assert len(bot.method_calls["set_webhook"]) == 1
    assert bot.method_calls["set_webhook"][0].kwargs == {"url": base_url + route}

    MESSAGE_UPDATE_JSON = {
        "update_id": 10001110101,
        "message": {
            "message_id": 53,
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
            "date": 1653769757,
            "text": "hello world",
        },
    }

    async def kill_bot_after(delay: float) -> None:
        await asyncio.sleep(delay)
        signal.raise_signal(signal.SIGTERM)

    async def send_message_update_after(delay: float) -> aiohttp.ClientResponse:
        await asyncio.sleep(delay)
        async with aiohttp.ClientSession(base_url=f"http://localhost:{port}") as session:
            return await session.post(route, json=MESSAGE_UPDATE_JSON)

    resp_completed, _, resp_rejected = await asyncio.gather(
        send_message_update_after(0),
        kill_bot_after(0.5),
        send_message_update_after(0.7),
    )

    await asyncio.wait_for(server_exited_with_sys_exit, timeout=30)

    assert resp_completed.status == 200
    assert resp_rejected.status == 500
    assert message_processing_started
    assert message_processing_ended
    assert background_job_1_completed
    assert background_job_2_completed


async def test_graceful_shutdown_conditions():
    GracefulShutdownCondition.instances.clear()

    for _ in range(1000):
        async with PreventShutdown("dummy"):
            i = 1 + 2

    actual_conditions = GracefulShutdownCondition.instances
    gc.collect()
    assert len(actual_conditions) == 0
