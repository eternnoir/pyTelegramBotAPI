import os

import pytest

from telebot.storage import StatePickleStorage


def test_state_pickle_storage_accepts_filename_without_directory(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    StatePickleStorage(file_path="states.pkl")

    assert os.path.isfile("states.pkl")


def test_async_state_pickle_storage_accepts_filename_without_directory(tmp_path, monkeypatch):
    pytest.importorskip("aiofiles")
    from telebot.asyncio_storage import StatePickleStorage as AsyncStatePickleStorage

    monkeypatch.chdir(tmp_path)
    AsyncStatePickleStorage(file_path="states.pkl")

    assert os.path.isfile("states.pkl")
