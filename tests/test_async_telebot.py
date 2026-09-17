# -*- coding: utf-8 -*-
"""Unit tests for `telebot.async_telebot.AsyncTeleBot`.

These tests are self-contained (no TOKEN/CHAT_ID required) and stub out all
network I/O.
"""
import asyncio
import logging

import pytest

from telebot import types
import telebot.async_telebot as async_telebot
from telebot.async_telebot import AsyncTeleBot


def _make_fake_me() -> types.User:
    return types.User.de_json({
        "id": 1,
        "is_bot": True,
        "first_name": "Test",
        "username": "test_bot",
    })


@pytest.mark.parametrize(
    'logger_level, expected_count, includes_traceback',
    [
        (logging.DEBUG, 3, True),
        (logging.INFO, 2, False),
        (logging.ERROR, 1, False),
        (None, 0, False),
    ],
)
def test_infinity_polling_honors_logger_level(
        monkeypatch, logger_level, expected_count, includes_traceback):
    class RecordingLogger:
        def __init__(self):
            self.messages = []

        def error(self, message, *args):
            self.messages.append(message % args if args else message)

    bot = AsyncTeleBot('1:fake', validate_token=False)
    logger = RecordingLogger()

    async def fail_polling(*args, **kwargs):
        bot._polling = False
        raise RuntimeError('polling failed')

    async def no_sleep(_seconds):
        return None

    monkeypatch.setattr(async_telebot, 'logger', logger)
    monkeypatch.setattr(async_telebot.asyncio, 'sleep', no_sleep)
    monkeypatch.setattr(bot, '_process_polling', fail_polling)

    asyncio.run(bot.infinity_polling(logger_level=logger_level))

    assert len(logger.messages) == expected_count
    if logger_level:
        assert logger.messages[0] == 'Infinity polling exception: polling failed'
    assert any('Exception traceback:' in message for message in logger.messages) is includes_traceback


def test_process_polling_retains_update_processing_tasks():
    """Regression test for issue #2572.

    Tasks fired by `_process_polling` for `process_new_updates` must be held
    in `self._pending_tasks` while running and discarded on completion, so
    they cannot be garbage-collected mid-execution.
    """
    bot = AsyncTeleBot("1:fake", validate_token=False)

    task_was_tracked_during_run: list[bool] = []
    process_completed = asyncio.Event()

    async def fake_process_new_updates(updates):
        current = asyncio.current_task()
        task_was_tracked_during_run.append(current in bot._pending_tasks)
        process_completed.set()

    async def fake_get_me():
        return _make_fake_me()

    # Deliver a single update batch, then stop polling on the next tick.
    fake_update = types.Update.de_json({"update_id": 1})
    call_count = {"n": 0}

    async def fake_get_updates(*args, **kwargs):
        call_count["n"] += 1
        if call_count["n"] == 1:
            return [fake_update]
        bot._polling = False
        return []

    async def noop():
        return None

    bot.get_me = fake_get_me
    bot.get_updates = fake_get_updates
    bot.process_new_updates = fake_process_new_updates
    bot.close_session = noop  # stub: no real aiohttp session in tests

    async def driver():
        await bot._process_polling(non_stop=True, interval=0, timeout=0)
        # Allow the fire-and-forget task to finish plus one yield for the
        # add_done_callback discard to run. A timeout guards against the
        # stub ever being rewired such that the processing task never runs.
        await asyncio.wait_for(process_completed.wait(), timeout=1)
        await asyncio.sleep(0)

    asyncio.run(driver())

    assert task_was_tracked_during_run == [True], (
        "In-flight processing task must be held by _pending_tasks"
    )
    assert bot._pending_tasks == set(), (
        "Completed processing tasks must be discarded from _pending_tasks"
    )


def _fake_429(retry_after: int):
    from telebot.asyncio_helper import ApiTelegramException

    class _FakeResponse:
        status = 429
        reason = "Too Many Requests"

    result_json = {
        "ok": False,
        "error_code": 429,
        "description": "Too Many Requests",
        "parameters": {"retry_after": retry_after},
    }
    return ApiTelegramException("sendMessage", _FakeResponse(), result_json)


def test_async_antiflood_returns_result_without_retrying_when_ok():
    from telebot.util import async_antiflood

    calls = {"n": 0}

    async def ok(value):
        calls["n"] += 1
        return value

    result = asyncio.run(async_antiflood(ok, "hello"))

    assert result == "hello"
    assert calls["n"] == 1


def test_async_antiflood_sleeps_retry_after_then_succeeds():
    from telebot.util import async_antiflood

    calls = {"n": 0}

    async def flaky():
        calls["n"] += 1
        if calls["n"] == 1:
            raise _fake_429(retry_after=7)
        return "ok"

    sleeps: list[float] = []

    async def fake_sleep(seconds):
        sleeps.append(seconds)

    original_sleep = asyncio.sleep
    asyncio.sleep = fake_sleep  # type: ignore[assignment]
    try:
        result = asyncio.run(async_antiflood(flaky))
    finally:
        asyncio.sleep = original_sleep  # type: ignore[assignment]

    assert result == "ok"
    assert calls["n"] == 2
    assert sleeps == [7], "Must sleep exactly retry_after seconds between attempts"


def test_async_antiflood_propagates_non_429_immediately():
    from telebot.asyncio_helper import ApiTelegramException
    from telebot.util import async_antiflood

    class _FakeResponse:
        status = 400
        reason = "Bad Request"

    err = ApiTelegramException(
        "sendMessage",
        _FakeResponse(),
        {"ok": False, "error_code": 400, "description": "Bad Request"},
    )

    calls = {"n": 0}

    async def boom():
        calls["n"] += 1
        raise err

    try:
        asyncio.run(async_antiflood(boom))
    except ApiTelegramException as raised:
        assert raised is err
    else:
        raise AssertionError("Non-429 error should propagate")

    assert calls["n"] == 1, "Non-429 errors must not trigger a retry"


def test_async_antiflood_final_attempt_propagates_after_budget_exhausted():
    from telebot.asyncio_helper import ApiTelegramException
    from telebot.util import async_antiflood

    calls = {"n": 0}
    budget = 3

    async def always_429():
        calls["n"] += 1
        raise _fake_429(retry_after=1)

    async def fake_sleep(_seconds):
        return None

    original_sleep = asyncio.sleep
    asyncio.sleep = fake_sleep  # type: ignore[assignment]
    try:
        try:
            asyncio.run(async_antiflood(always_429, number_retries=budget))
        except ApiTelegramException:
            pass
        else:
            raise AssertionError("Final 429 must surface once retries are exhausted")
    finally:
        asyncio.sleep = original_sleep  # type: ignore[assignment]

    assert calls["n"] == budget, (
        f"Expected {budget} total attempts, got {calls['n']}"
    )
