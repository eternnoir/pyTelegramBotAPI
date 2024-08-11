from telebot.asyncio_storage.base_storage import StateStorageBase, StateDataContext
from typing import Optional, Union


class StateMemoryStorage(StateStorageBase):
    """
    Memory storage for states.

    Stores states in memory as a dictionary.

    .. code-block:: python3

        storage = StateMemoryStorage()
        bot = AsyncTeleBot(token, storage=storage)

    :param separator: Separator for keys, default is ":".
    :type separator: Optional[str]

    :param prefix: Prefix for keys, default is "telebot".
    :type prefix: Optional[str]
    """

    def __init__(
        self, separator: Optional[str] = ":", prefix: Optional[str] = "telebot"
    ) -> None:
        self.separator = separator
        self.prefix = prefix
        if not self.prefix:
            raise ValueError("Prefix cannot be empty")

        self.data = (
            {}
        )  # key: telebot:bot_id:business_connection_id:message_thread_id:chat_id:user_id

    async def set_state(
        self,
        chat_id: int,
        user_id: int,
        state: str,
        business_connection_id: Optional[str] = None,
        message_thread_id: Optional[int] = None,
        bot_id: Optional[int] = None,
    ) -> bool:
        if hasattr(state, "name"):
            state = state.name

        _key = self._get_key(
            chat_id,
            user_id,
            self.prefix,
            self.separator,
            business_connection_id,
            message_thread_id,
            bot_id,
        )

        if self.data.get(_key) is None:
            self.data[_key] = {"state": state, "data": {}}
        else:
            self.data[_key]["state"] = state

        return True

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

        if self.data.get(_key) is None:
            return None

        return self.data[_key]["state"]

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

        if self.data.get(_key) is None:
            return False

        del self.data[_key]
        return True

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

        if self.data.get(_key) is None:
            raise RuntimeError(f"MemoryStorage: key {_key} does not exist.")
        self.data[_key]["data"][key] = value
        return True

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

        return self.data.get(_key, {}).get("data", {})

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

        if self.data.get(_key) is None:
            return False
        self.data[_key]["data"] = {}
        return True

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

        if self.data.get(_key) is None:
            return False
        self.data[_key]["data"] = data
        return True

    def __str__(self) -> str:
        return f"<StateMemoryStorage: {self.data}>"
