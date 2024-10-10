aiofiles_installed = True
try:
    import aiofiles
except ImportError:
    aiofiles_installed = False

import os
import pickle
import asyncio
from typing import Optional, Union, Callable, Any

from telebot.asyncio_storage.base_storage import StateStorageBase, StateDataContext


def with_lock(func: Callable) -> Callable:
    async def wrapper(self, *args, **kwargs):
        async with self.lock:
            return await func(self, *args, **kwargs)

    return wrapper


class StatePickleStorage(StateStorageBase):
    """
    State storage based on pickle file.

    .. warning::

        This storage is not recommended for production use.
        Data may be corrupted. If you face a case where states do not work as expected,
        try to use another storage.

    .. code-block:: python3

        storage = StatePickleStorage()
        bot = AsyncTeleBot(token, storage=storage)

    :param file_path: Path to file where states will be stored.
    :type file_path: str

    :param prefix: Prefix for keys, default is "telebot".
    :type prefix: Optional[str]

    :param separator: Separator for keys, default is ":".
    :type separator: Optional[str]
    """

    def __init__(
        self,
        file_path: str = "./.state-save/states.pkl",
        prefix="telebot",
        separator: Optional[str] = ":",
    ) -> None:

        if not aiofiles_installed:
            raise ImportError("Please install aiofiles using `pip install aiofiles`")

        self.file_path = file_path
        self.prefix = prefix
        self.separator = separator
        self.lock = asyncio.Lock()
        self.create_dir()

    async def _read_from_file(self) -> dict:
        async with aiofiles.open(self.file_path, "rb") as f:
            data = await f.read()
            return pickle.loads(data)

    async def _write_to_file(self, data: dict) -> None:
        async with aiofiles.open(self.file_path, "wb") as f:
            await f.write(pickle.dumps(data))

    def create_dir(self):
        """
        Create directory .save-handlers.
        """
        dirs, filename = os.path.split(self.file_path)
        os.makedirs(dirs, exist_ok=True)
        if not os.path.isfile(self.file_path):
            with open(self.file_path, "wb") as file:
                pickle.dump({}, file)

    @with_lock
    async def set_state(
        self,
        chat_id: int,
        user_id: int,
        state: str,
        business_connection_id: Optional[str] = None,
        message_thread_id: Optional[int] = None,
        bot_id: Optional[int] = None,
    ) -> bool:
        _key = self._get_key(
            chat_id,
            user_id,
            self.prefix,
            self.separator,
            business_connection_id,
            message_thread_id,
            bot_id,
        )
        data = await self._read_from_file()
        if _key not in data:
            data[_key] = {"state": state, "data": {}}
        else:
            data[_key]["state"] = state
        await self._write_to_file(data)
        return True

    @with_lock
    async def get_state(
        self,
        chat_id: int,
        user_id: int,
        business_connection_id: Optional[str] = None,
        message_thread_id: Optional[int] = None,
        bot_id: Optional[int] = None,
    ) -> Union[str, None]:
        _key = self._get_key(
            chat_id,
            user_id,
            self.prefix,
            self.separator,
            business_connection_id,
            message_thread_id,
            bot_id,
        )
        data = await self._read_from_file()
        return data.get(_key, {}).get("state")

    @with_lock
    async def delete_state(
        self,
        chat_id: int,
        user_id: int,
        business_connection_id: Optional[str] = None,
        message_thread_id: Optional[int] = None,
        bot_id: Optional[int] = None,
    ) -> bool:
        _key = self._get_key(
            chat_id,
            user_id,
            self.prefix,
            self.separator,
            business_connection_id,
            message_thread_id,
            bot_id,
        )
        data = await self._read_from_file()
        if _key in data:
            del data[_key]
            await self._write_to_file(data)
            return True
        return False

    @with_lock
    async def set_data(
        self,
        chat_id: int,
        user_id: int,
        key: str,
        value: Union[str, int, float, dict],
        business_connection_id: Optional[str] = None,
        message_thread_id: Optional[int] = None,
        bot_id: Optional[int] = None,
    ) -> bool:
        _key = self._get_key(
            chat_id,
            user_id,
            self.prefix,
            self.separator,
            business_connection_id,
            message_thread_id,
            bot_id,
        )
        data = await self._read_from_file()
        state_data = data.get(_key, {})
        state_data["data"][key] = value
        if _key not in data:
            raise RuntimeError(f"StatePickleStorage: key {_key} does not exist.")
        else:
            data[_key]["data"][key] = value
        await self._write_to_file(data)
        return True

    @with_lock
    async def get_data(
        self,
        chat_id: int,
        user_id: int,
        business_connection_id: Optional[str] = None,
        message_thread_id: Optional[int] = None,
        bot_id: Optional[int] = None,
    ) -> dict:
        _key = self._get_key(
            chat_id,
            user_id,
            self.prefix,
            self.separator,
            business_connection_id,
            message_thread_id,
            bot_id,
        )
        data = await self._read_from_file()
        return data.get(_key, {}).get("data", {})

    @with_lock
    async def reset_data(
        self,
        chat_id: int,
        user_id: int,
        business_connection_id: Optional[str] = None,
        message_thread_id: Optional[int] = None,
        bot_id: Optional[int] = None,
    ) -> bool:
        _key = self._get_key(
            chat_id,
            user_id,
            self.prefix,
            self.separator,
            business_connection_id,
            message_thread_id,
            bot_id,
        )
        data = await self._read_from_file()
        if _key in data:
            data[_key]["data"] = {}
            await self._write_to_file(data)
            return True
        return False

    def get_interactive_data(
        self,
        chat_id: int,
        user_id: int,
        business_connection_id: Optional[str] = None,
        message_thread_id: Optional[int] = None,
        bot_id: Optional[int] = None,
    ) -> Optional[dict]:
        return StateDataContext(
            self,
            chat_id=chat_id,
            user_id=user_id,
            business_connection_id=business_connection_id,
            message_thread_id=message_thread_id,
            bot_id=bot_id,
        )

    @with_lock
    async def save(
        self,
        chat_id: int,
        user_id: int,
        data: dict,
        business_connection_id: Optional[str] = None,
        message_thread_id: Optional[int] = None,
        bot_id: Optional[int] = None,
    ) -> bool:
        _key = self._get_key(
            chat_id,
            user_id,
            self.prefix,
            self.separator,
            business_connection_id,
            message_thread_id,
            bot_id,
        )
        file_data = await self._read_from_file()
        file_data[_key]["data"] = data
        await self._write_to_file(file_data)
        return True

    def __str__(self) -> str:
        return f"StatePickleStorage({self.file_path}, {self.prefix})"
