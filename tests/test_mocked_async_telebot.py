from telebot import AsyncTeleBot, types
from telebot.test_util import (
    MOCKED_METHOD_NAMES,
    UNMOCKABLE_METHOD_NAMES,
    MockedAsyncTeleBot,
)


def test_mocked_async_telebot_mocks_all_mockable_parent_methods():
    b = MockedAsyncTeleBot("token")
    mockable_telebot_method_names = [
        method_name
        for method_name in dir(AsyncTeleBot)
        if not (method_name.startswith("__") or method_name in UNMOCKABLE_METHOD_NAMES)
    ]
    missing_mockable_methods = sorted(set(mockable_telebot_method_names) - set(MOCKED_METHOD_NAMES))
    assert missing_mockable_methods == []


async def test_mocked_async_telebot_defaults():
    bot = MockedAsyncTeleBot("testing")
    message = await bot.send_message(chat_id=1312, text="hello world")
    reply_to_first = await bot.reply_to(message, "again")
    assert reply_to_first.from_user == message.from_user
    assert message.text_content == "hello world"
    assert message.id == 2
    assert message.chat.id == 1312
    assert reply_to_first.text_content == "again"
    assert reply_to_first.id == 4
    assert reply_to_first.chat.id == 1312


async def test_mocked_async_telebot_custom_values():
    bot = MockedAsyncTeleBot("testing")

    bot.add_return_values(
        "send_message",
        types.Message(
            message_id=11111,
            from_user=types.User(id=1, is_bot=True, first_name="HEYY"),
            date=0,
            chat=types.Chat(id=420, type="supergroup"),
            content_type="text",
            options={"text": "manually created value"},
            json_string="",
        ),
    )

    message_man = await bot.send_message(chat_id=1312, text="something")
    assert message_man.id == 11111
    assert message_man.from_user.id == 1
    assert message_man.from_user.first_name == "HEYY"
    assert message_man.chat.id == 420
    assert message_man.text_content == "manually created value"

    message_default = await bot.send_message(chat_id=18, text="default")
    assert message_default.id == 2
    assert message_default.chat.id == 18
    assert message_default.from_user.first_name == "MockedAsyncTeleBot"
    assert message_default.text_content == "default"

    assert len(bot.method_calls["send_message"]) == 2
