# -*- coding: utf-8 -*-
"""Unit tests for `telebot.async_telebot.AsyncTeleBot`.

These tests are self-contained (no TOKEN/CHAT_ID required) and stub out all
network I/O.
"""
import asyncio

from telebot import types
from telebot.async_telebot import AsyncTeleBot


def _make_fake_me() -> types.User:
    return types.User.de_json({
        "id": 1,
        "is_bot": True,
        "first_name": "Test",
        "username": "test_bot",
    })


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
        # add_done_callback discard to run.
        await process_completed.wait()
        await asyncio.sleep(0)

    asyncio.run(driver())

    assert task_was_tracked_during_run == [True], (
        "In-flight processing task must be held by _pending_tasks"
    )
    assert bot._pending_tasks == set(), (
        "Completed processing tasks must be discarded from _pending_tasks"
    )
