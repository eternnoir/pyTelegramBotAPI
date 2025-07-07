from telebot import types
from telebot.callback_data import CallbackData
from telebot.test_util import MockedAsyncTeleBot
from telebot.types.service import HandlerResult


async def test_mocked_async_telebot_defaults():
    bot = MockedAsyncTeleBot("testing")
    message = await bot.send_message(1312, text="hello world")
    reply_to_first = await bot.reply_to(message, "again")
    assert reply_to_first.from_user == message.from_user
    assert message.text_content == "hello world"
    assert message.id == 2
    assert message.chat.id == 1312
    assert reply_to_first.text_content == "again"
    assert reply_to_first.id == 4
    assert reply_to_first.chat.id == 1312

    assert list(bot.method_calls) == ["send_message"]
    send_message_full_kwargs = [mc.full_kwargs for mc in bot.method_calls["send_message"]]
    assert send_message_full_kwargs == [
        {"chat_id": 1312, "text": "hello world"},
        {
            "chat_id": 1312,
            "text": "again",
            "reply_to_message_id": 2,
            "parse_mode": None,
            "disable_web_page_preview": None,
            "disable_notification": None,
            "protect_content": None,
            "allow_sending_without_reply": None,
            "reply_markup": None,
            "timeout": None,
        },
    ]


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


async def test_callback_query_handler_auto_answer():
    bot = MockedAsyncTeleBot("testing")

    cbd1 = CallbackData("foo", prefix="one")
    cbd2 = CallbackData("bar", prefix="two")

    cbd1_handler_run_count = 0
    cbd2_handler_run_count = 0

    @bot.callback_query_handler(callback_data=cbd1)
    async def cbd1_regular_handler(cq: types.CallbackQuery):
        nonlocal cbd1_handler_run_count
        cbd1_handler_run_count += 1

    @bot.callback_query_handler(callback_data=cbd2, auto_answer=True)
    async def transparent_auto_answer_handler(cq: types.CallbackQuery) -> HandlerResult:
        return HandlerResult(continue_to_other_handlers=True)

    @bot.callback_query_handler(callback_data=cbd2, auto_answer=True)
    async def cbd2_auto_answering_handler(cq: types.CallbackQuery):
        nonlocal cbd2_handler_run_count
        cbd2_handler_run_count += 1

    def inline_button_press_update(cbk_data: str, cbk_id: int):
        return types.Update.de_json(
            {
                "update_id": 13,
                "callback_query": {
                    "id": cbk_id,
                    "data": cbk_data,
                    "chat_instance": "whatever",
                    "from": {
                        "id": 100,
                        "is_bot": False,
                        "first_name": "John",
                    },
                    "message": {
                        "message_id": 4444,
                        "from": {
                            "id": 101,
                            "is_bot": True,
                            "first_name": "Myself",
                        },
                        "date": 15555555,
                        "chat": {
                            "id": "dummy",
                            "type": "private",
                        },
                    },
                },
            }
        )

    await bot.process_new_updates(
        [
            inline_button_press_update("one:hello", 1),
            inline_button_press_update("two:world", 2),
        ]
    )

    assert cbd1_handler_run_count == 1
    assert cbd2_handler_run_count == 1

    assert len(bot.method_calls) == 1
    answering_calls = bot.method_calls.get("answer_callback_query")
    assert answering_calls is not None and len(answering_calls) == 1
    assert answering_calls[0].full_kwargs == {"callback_query_id": 2}
