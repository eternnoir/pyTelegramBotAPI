import asyncio
import os
import uuid

import pytest

# These tests need a running Redis server. To run them, point REDIS_URL at it:
#   REDIS_URL=redis://localhost:6379/0 py.test test_redis_storage.py
REDIS_URL = os.environ.get("REDIS_URL")

pytestmark = pytest.mark.skipif(not REDIS_URL, reason="set REDIS_URL to run the Redis storage tests")

CHAT_ID = 11
USER_ID = 22


@pytest.fixture
def prefix():
    return "telebot_test_" + uuid.uuid4().hex


@pytest.fixture
def storage(prefix):
    pytest.importorskip("redis")
    from telebot.storage import StateRedisStorage

    storage = StateRedisStorage(redis_url=REDIS_URL, prefix=prefix)
    yield storage
    for key in storage.redis.scan_iter(prefix + "*"):
        storage.redis.delete(key)


def test_save_and_reset_data_keep_working_for_an_existing_state(storage):
    storage.set_state(CHAT_ID, USER_ID, "order")

    assert storage.save(CHAT_ID, USER_ID, {"address": "street"}) is True
    assert storage.get_data(CHAT_ID, USER_ID) == {"address": "street"}

    assert storage.reset_data(CHAT_ID, USER_ID) is True
    assert storage.get_data(CHAT_ID, USER_ID) == {}
    assert storage.get_state(CHAT_ID, USER_ID) == "order"


def test_save_and_reset_data_do_not_create_a_missing_state(storage, prefix):
    assert storage.save(CHAT_ID, USER_ID, {"address": "street"}) is False
    assert storage.reset_data(CHAT_ID, USER_ID) is False

    assert list(storage.redis.scan_iter(prefix + "*")) == []


def test_data_of_a_state_deleted_inside_the_context_is_not_restored(storage):
    storage.set_state(CHAT_ID, USER_ID, "order")
    storage.set_data(CHAT_ID, USER_ID, "address", "street")

    with storage.get_interactive_data(CHAT_ID, USER_ID) as data:
        data["paid"] = True
        storage.delete_state(CHAT_ID, USER_ID)

    storage.set_state(CHAT_ID, USER_ID, "order")
    assert storage.get_data(CHAT_ID, USER_ID) == {}


def test_async_save_and_reset_data_keep_working_for_an_existing_state(prefix):
    pytest.importorskip("redis")
    from telebot.asyncio_storage import StateRedisStorage

    async def scenario():
        storage = StateRedisStorage(redis_url=REDIS_URL, prefix=prefix)
        try:
            await storage.set_state(CHAT_ID, USER_ID, "order")

            assert await storage.save(CHAT_ID, USER_ID, {"address": "street"}) is True
            assert await storage.get_data(CHAT_ID, USER_ID) == {"address": "street"}

            assert await storage.reset_data(CHAT_ID, USER_ID) is True
            assert await storage.get_data(CHAT_ID, USER_ID) == {}
            assert await storage.get_state(CHAT_ID, USER_ID) == "order"
        finally:
            await storage.delete_state(CHAT_ID, USER_ID)
            await storage.redis.aclose()

    asyncio.run(scenario())


def test_async_save_and_reset_data_do_not_create_a_missing_state(prefix):
    pytest.importorskip("redis")
    from telebot.asyncio_storage import StateRedisStorage

    async def scenario():
        storage = StateRedisStorage(redis_url=REDIS_URL, prefix=prefix)
        try:
            assert await storage.save(CHAT_ID, USER_ID, {"address": "street"}) is False
            assert await storage.reset_data(CHAT_ID, USER_ID) is False

            assert [key async for key in storage.redis.scan_iter(prefix + "*")] == []
        finally:
            await storage.delete_state(CHAT_ID, USER_ID)
            await storage.redis.aclose()

    asyncio.run(scenario())


def test_async_data_of_a_state_deleted_inside_the_context_is_not_restored(prefix):
    pytest.importorskip("redis")
    from telebot.asyncio_storage import StateRedisStorage

    async def scenario():
        storage = StateRedisStorage(redis_url=REDIS_URL, prefix=prefix)
        try:
            await storage.set_state(CHAT_ID, USER_ID, "order")
            await storage.set_data(CHAT_ID, USER_ID, "address", "street")

            async with storage.get_interactive_data(CHAT_ID, USER_ID) as data:
                data["paid"] = True
                await storage.delete_state(CHAT_ID, USER_ID)

            await storage.set_state(CHAT_ID, USER_ID, "order")
            assert await storage.get_data(CHAT_ID, USER_ID) == {}
        finally:
            await storage.delete_state(CHAT_ID, USER_ID)
            await storage.redis.aclose()

    asyncio.run(scenario())
