import sys

sys.path.append('../')

import asyncio
import json

import pytest

from telebot import asyncio_filters, types
from telebot.custom_filters import IsDigitFilter, TextContainsFilter, TextFilter, TextStartsFilter


def make_message(**fields):
    payload = {
        "message_id": 1,
        "date": 0,
        "chat": {"id": 1, "type": "private"},
        "from": {"id": 1, "is_bot": False, "first_name": "Test"},
    }
    payload.update(fields)
    return types.Message.de_json(json.dumps(payload))


@pytest.fixture
def photo_message():
    return make_message(
        photo=[{"file_id": "f", "file_unique_id": "u", "width": 1, "height": 1}]
    )


@pytest.fixture
def text_message():
    return make_message(text="12345")


def test_text_contains_filter_skips_message_without_text(photo_message):
    assert photo_message.text is None
    assert TextContainsFilter().check(photo_message, "23") is False


def test_text_startswith_filter_skips_message_without_text(photo_message):
    assert TextStartsFilter().check(photo_message, "12") is False


def test_is_digit_filter_skips_message_without_text(photo_message):
    assert IsDigitFilter().check(photo_message) is False


def test_text_filters_still_match_text_messages(text_message):
    assert TextContainsFilter().check(text_message, "23") is True
    assert TextStartsFilter().check(text_message, "12") is True
    assert IsDigitFilter().check(text_message) is True


def test_async_text_filters_skip_message_without_text(photo_message):
    assert asyncio.run(asyncio_filters.TextContainsFilter().check(photo_message, "23")) is False
    assert asyncio.run(asyncio_filters.TextStartsFilter().check(photo_message, "12")) is False
    assert asyncio.run(asyncio_filters.IsDigitFilter().check(photo_message)) is False
    assert asyncio.run(asyncio_filters.TextFilter(contains=["23"]).check(photo_message)) is False
    assert asyncio.run(asyncio_filters.TextFilter(equals="12345", ignore_case=True).check(photo_message)) is False


def test_async_text_filters_still_match_text_messages(text_message):
    assert asyncio.run(asyncio_filters.TextContainsFilter().check(text_message, "23")) is True
    assert asyncio.run(asyncio_filters.TextStartsFilter().check(text_message, "12")) is True
    assert asyncio.run(asyncio_filters.IsDigitFilter().check(text_message)) is True
    captioned = make_message(
        photo=[{"file_id": "f", "file_unique_id": "u", "width": 1, "height": 1}], caption="12345"
    )
    assert asyncio.run(asyncio_filters.TextFilter(contains=["23"]).check(captioned)) is True


@pytest.mark.parametrize(
    "conditions, text",
    [
        ({"equals": "Hi", "contains": ["Hello"]}, "oh, HELLO there"),
        ({"equals": "Hi", "starts_with": "Hello"}, "hello there"),
        ({"contains": ["Good"], "ends_with": "Bye"}, "see you, BYE"),
        ({"starts_with": "Hello", "ends_with": "World"}, "big WORLD"),
        ({"equals": "Hi", "contains": ["Hello"], "starts_with": "Hey", "ends_with": "Bye"}, "see you, bye"),
    ],
)
def test_text_filter_ignore_case_applies_to_every_condition(conditions, text):
    message = make_message(text=text)
    assert TextFilter(**conditions, ignore_case=True).check(message) is True
    assert asyncio.run(asyncio_filters.TextFilter(**conditions, ignore_case=True).check(message)) is True
    assert TextFilter(**conditions).check(message) is False


def test_text_filter_ignore_case_keeps_the_filter_unchanged():
    text_filter = TextFilter(equals="Hi", contains=["Hello"], ignore_case=True)
    assert text_filter.check(make_message(text="HI")) is True
    assert text_filter.equals == "Hi"
    assert text_filter.contains == ["Hello"]
