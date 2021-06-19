import sys

sys.path.append('../')

REDIS_TESTS = False

import os
import time

import pytest

import telebot
from telebot import types
from telebot.handler_backends import MemoryHandlerBackend, FileHandlerBackend

if REDIS_TESTS:
    from telebot.handler_backends import RedisHandlerBackend


@pytest.fixture()
def telegram_bot():
    return telebot.TeleBot('', threaded=False)


@pytest.fixture
def private_chat():
    return types.Chat(id=11, type='private')


@pytest.fixture
def user():
    return types.User(id=10, is_bot=False, first_name='Some User')


@pytest.fixture()
def message(user, private_chat):
    params = {'text': '/start'}
    return types.Message(
        message_id=1, from_user=user, date=None, chat=private_chat, content_type='text', options=params, json_string=""
    )


@pytest.fixture()
def reply_to_message(user, private_chat, message):
    params = {'text': '/start'}
    reply_message = types.Message(
        message_id=2, from_user=user, date=None, chat=private_chat, content_type='text', options=params, json_string=""
    )
    reply_message.reply_to_message = message
    return reply_message


@pytest.fixture()
def update_type(message):
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
    return types.Update(1001234038283, message, edited_message, channel_post, edited_channel_post, inline_query,
                        chosen_inline_result, callback_query, shipping_query, pre_checkout_query, poll, poll_answer,
                        my_chat_member, chat_member)


@pytest.fixture()
def reply_to_message_update_type(reply_to_message):
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
    return types.Update(1001234038284, reply_to_message, edited_message, channel_post, edited_channel_post,
                        inline_query, chosen_inline_result, callback_query, shipping_query, pre_checkout_query, 
                        poll, poll_answer, my_chat_member, chat_member)


def next_handler(message):
    message.text = 'entered next_handler'


def test_memory_handler_backend_default_backend(telegram_bot):
    assert telegram_bot.reply_backend.__class__ == MemoryHandlerBackend
    assert telegram_bot.next_step_backend.__class__ == MemoryHandlerBackend


def test_memory_handler_backend_register_next_step_handler(telegram_bot, private_chat, update_type):
    @telegram_bot.message_handler(commands=['start'])
    def start(message):
        message.text = 'entered start'
        telegram_bot.register_next_step_handler_by_chat_id(message.chat.id, next_handler)

    telegram_bot.process_new_updates([update_type])
    assert update_type.message.text == 'entered start'

    assert len(telegram_bot.next_step_backend.handlers[private_chat.id]) == 1

    telegram_bot.process_new_updates([update_type])
    assert update_type.message.text == 'entered next_handler'

    assert private_chat.id not in telegram_bot.next_step_backend.handlers


def test_memory_handler_backend_clear_next_step_handler(telegram_bot, private_chat, update_type):
    @telegram_bot.message_handler(commands=['start'])
    def start(message):
        message.text = 'entered start'
        telegram_bot.register_next_step_handler_by_chat_id(message.chat.id, next_handler)

    telegram_bot.process_new_updates([update_type])
    assert update_type.message.text == 'entered start'

    assert len(telegram_bot.next_step_backend.handlers[private_chat.id]) == 1

    telegram_bot.clear_step_handler_by_chat_id(private_chat.id)

    assert private_chat.id not in telegram_bot.next_step_backend.handlers

    telegram_bot.process_new_updates([update_type])
    assert update_type.message.text == 'entered start'


def test_memory_handler_backend_register_reply_handler(telegram_bot, private_chat, update_type,
                                                       reply_to_message_update_type):
    @telegram_bot.message_handler(commands=['start'])
    def start(message):
        message.text = 'entered start'
        telegram_bot.register_for_reply_by_message_id(message.message_id, next_handler)

    telegram_bot.process_new_updates([update_type])
    assert update_type.message.text == 'entered start'

    assert len(telegram_bot.reply_backend.handlers[update_type.message.message_id]) == 1

    telegram_bot.process_new_updates([reply_to_message_update_type])
    assert reply_to_message_update_type.message.text == 'entered next_handler'

    assert private_chat.id not in telegram_bot.reply_backend.handlers


def test_memory_handler_backend_clear_reply_handler(telegram_bot, private_chat, update_type,
                                                    reply_to_message_update_type):
    @telegram_bot.message_handler(commands=['start'])
    def start(message):
        message.text = 'entered start'
        telegram_bot.register_for_reply_by_message_id(message.message_id, next_handler)

    telegram_bot.process_new_updates([update_type])
    assert update_type.message.text == 'entered start'

    assert len(telegram_bot.reply_backend.handlers[update_type.message.message_id]) == 1

    telegram_bot.clear_reply_handlers_by_message_id(update_type.message.message_id)

    assert update_type.message.message_id not in telegram_bot.reply_backend.handlers

    telegram_bot.process_new_updates([reply_to_message_update_type])
    assert reply_to_message_update_type.message.text == 'entered start'


def test_file_handler_backend_register_next_step_handler(telegram_bot, private_chat, update_type):
    telegram_bot.next_step_backend=FileHandlerBackend(filename='./.handler-saves/step1.save', delay=0.1)

    @telegram_bot.message_handler(commands=['start'])
    def start(message):
        message.text = 'entered start'
        telegram_bot.register_next_step_handler_by_chat_id(message.chat.id, next_handler)

    telegram_bot.process_new_updates([update_type])
    assert update_type.message.text == 'entered start'

    time.sleep(0.2)

    assert os.path.exists(telegram_bot.next_step_backend.filename)

    assert len(telegram_bot.next_step_backend.handlers[private_chat.id]) == 1

    telegram_bot.next_step_backend.handlers = {}

    telegram_bot.next_step_backend.load_handlers()

    assert len(telegram_bot.next_step_backend.handlers[private_chat.id]) == 1

    telegram_bot.process_new_updates([update_type])
    assert update_type.message.text == 'entered next_handler'

    assert private_chat.id not in telegram_bot.next_step_backend.handlers

    time.sleep(0.2)
    if os.path.exists(telegram_bot.next_step_backend.filename):
        os.remove(telegram_bot.next_step_backend.filename)


def test_file_handler_backend_clear_next_step_handler(telegram_bot, private_chat, update_type):
    telegram_bot.next_step_backend=FileHandlerBackend(filename='./.handler-saves/step2.save', delay=0.1)

    @telegram_bot.message_handler(commands=['start'])
    def start(message):
        message.text = 'entered start'
        telegram_bot.register_next_step_handler_by_chat_id(message.chat.id, next_handler)

    telegram_bot.process_new_updates([update_type])
    assert update_type.message.text == 'entered start'

    assert len(telegram_bot.next_step_backend.handlers[private_chat.id]) == 1

    time.sleep(0.2)

    assert os.path.exists(telegram_bot.next_step_backend.filename)

    telegram_bot.clear_step_handler_by_chat_id(private_chat.id)

    time.sleep(0.2)

    telegram_bot.next_step_backend.load_handlers()

    assert private_chat.id not in telegram_bot.next_step_backend.handlers

    telegram_bot.process_new_updates([update_type])
    assert update_type.message.text == 'entered start'

    time.sleep(0.2)
    if os.path.exists(telegram_bot.next_step_backend.filename):
        os.remove(telegram_bot.next_step_backend.filename)


def test_redis_handler_backend_register_next_step_handler(telegram_bot, private_chat, update_type):
    if not REDIS_TESTS:
        pytest.skip('please install redis and configure redis server, then enable REDIS_TESTS')

    telegram_bot.next_step_backend = RedisHandlerBackend(prefix='pyTelegramBotApi:step_backend1')

    @telegram_bot.message_handler(commands=['start'])
    def start(message):
        message.text = 'entered start'
        telegram_bot.register_next_step_handler_by_chat_id(message.chat.id, next_handler)

    telegram_bot.process_new_updates([update_type])
    assert update_type.message.text == 'entered start'

    telegram_bot.process_new_updates([update_type])
    assert update_type.message.text == 'entered next_handler'


def test_redis_handler_backend_clear_next_step_handler(telegram_bot, private_chat, update_type):
    if not REDIS_TESTS:
        pytest.skip('please install redis and configure redis server, then enable REDIS_TESTS')

    telegram_bot.next_step_backend = RedisHandlerBackend(prefix='pyTelegramBotApi:step_backend2')

    @telegram_bot.message_handler(commands=['start'])
    def start(message):
        message.text = 'entered start'
        telegram_bot.register_next_step_handler_by_chat_id(message.chat.id, next_handler)

    telegram_bot.process_new_updates([update_type])
    assert update_type.message.text == 'entered start'

    telegram_bot.clear_step_handler_by_chat_id(private_chat.id)

    telegram_bot.process_new_updates([update_type])
    assert update_type.message.text == 'entered start'
