# -*- coding: utf-8 -*-
"""Unit tests for `telebot.asyncio_helper._process_request` retry behaviour.

These tests are self-contained (no TOKEN required) and stub out all
network I/O.
"""
import asyncio

import aiohttp
import pytest

from telebot import asyncio_helper


class _FakeResponse:
    def __init__(self, payload):
        self._payload = payload
        self.status = 200

    async def json(self, encoding=None):
        return self._payload


class _FakeRequestContext:
    def __init__(self, outcome):
        self._outcome = outcome

    async def __aenter__(self):
        if isinstance(self._outcome, Exception):
            raise self._outcome
        return self._outcome

    async def __aexit__(self, exc_type, exc, tb):
        return False


class _FakeSession:
    """Yields the given outcomes (exception or response) one per request."""

    def __init__(self, outcomes):
        self._outcomes = list(outcomes)
        self.calls = 0

    def request(self, **kwargs):
        outcome = self._outcomes[min(self.calls, len(self._outcomes) - 1)]
        self.calls += 1
        return _FakeRequestContext(outcome)


def _ok_response(result=42):
    return _FakeResponse({"ok": True, "result": result})


def _invoke(outcomes, retry_on_error):
    """Run _process_request against stubbed outcomes.

    Returns (result, raised_exception, fake_session).
    """
    session = _FakeSession(outcomes)

    async def fake_get_session():
        return session

    saved_get_session = asyncio_helper.session_manager.get_session
    saved_retry_on_error = asyncio_helper.RETRY_ON_ERROR
    saved_retry_timeout = asyncio_helper.RETRY_TIMEOUT
    asyncio_helper.session_manager.get_session = fake_get_session
    asyncio_helper.RETRY_ON_ERROR = retry_on_error
    asyncio_helper.RETRY_TIMEOUT = 0
    try:
        result = asyncio.run(
            asyncio_helper._process_request("1:fake", "sendMessage", method="post")
        )
        return result, None, session
    except Exception as exc:
        return None, exc, session
    finally:
        asyncio_helper.session_manager.get_session = saved_get_session
        asyncio_helper.RETRY_ON_ERROR = saved_retry_on_error
        asyncio_helper.RETRY_TIMEOUT = saved_retry_timeout


def test_success_returns_result_payload():
    result, exc, session = _invoke([_ok_response()], retry_on_error=False)
    assert exc is None
    assert result == 42
    assert session.calls == 1


def test_network_error_is_not_retried_by_default():
    """Default behaviour stays unchanged: fail fast on the first error."""
    result, exc, session = _invoke(
        [aiohttp.ClientConnectionError("boom"), _ok_response()],
        retry_on_error=False,
    )
    assert isinstance(exc, asyncio_helper.RequestTimeout)
    assert session.calls == 1


def test_retries_recover_when_enabled():
    result, exc, session = _invoke(
        [
            aiohttp.ClientConnectionError("boom"),
            asyncio.TimeoutError(),
            _ok_response(),
        ],
        retry_on_error=True,
    )
    assert exc is None
    assert result == 42
    assert session.calls == 3


def test_retries_exhausted_raise_request_timeout():
    result, exc, session = _invoke(
        [aiohttp.ClientConnectionError("boom")], retry_on_error=True
    )
    assert isinstance(exc, asyncio_helper.RequestTimeout)
    assert session.calls == asyncio_helper.MAX_RETRIES


def test_api_error_is_not_retried():
    """Errors reported by the Bot API itself must propagate immediately."""
    bad_request = _FakeResponse(
        {"ok": False, "error_code": 400, "description": "Bad Request: test"}
    )
    result, exc, session = _invoke([bad_request, _ok_response()], retry_on_error=True)
    assert isinstance(exc, asyncio_helper.ApiTelegramException)
    assert session.calls == 1
