import os

import telebot
from telebot import types
from tests.utils import mock_message, mock_message_update

should_skip = "TOKEN" and "CHAT_ID" not in os.environ

if not should_skip:
    TOKEN = os.environ["TOKEN"]
    CHAT_ID = os.environ["CHAT_ID"]
    GROUP_ID = os.environ["GROUP_ID"]


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


async def test_message_handler_for_commands():
    tb = telebot.AsyncTeleBot("")
    update = mock_message_update("/help")

    @tb.message_handler(commands=["help", "start"])
    async def command_handler(message: types.Message):
        message.text = "got"

    await tb.process_new_updates([update])
    assert update.message.text == "got"
