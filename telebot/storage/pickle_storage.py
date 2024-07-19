import os
import pickle
import threading
from typing import Optional, Union
from telebot.storage.base_storage import StateStorageBase, StateDataContext

class StatePickleStorage(StateStorageBase):
    def __init__(self, file_path: str="./.state-save/states.pkl",
                 prefix='telebot', separator: Optional[str]=":") -> None:
        self.file_path = file_path
        self.prefix = prefix
        self.separator = separator
        self.lock = threading.Lock()

        self.create_dir()

    def _read_from_file(self) -> dict:
        with open(self.file_path, 'rb') as f:
            return pickle.load(f)

    def _write_to_file(self, data: dict) -> None:
        with open(self.file_path, 'wb') as f:
            pickle.dump(data, f)

    def create_dir(self):
        """
        Create directory .save-handlers.
        """
        dirs, filename = os.path.split(self.file_path)
        os.makedirs(dirs, exist_ok=True)
        if not os.path.isfile(self.file_path):
            with open(self.file_path,'wb') as file:
                pickle.dump({}, file)

    def set_state(self, chat_id: int, user_id: int, state: str,
                  business_connection_id: Optional[str]=None, message_thread_id: Optional[int]=None,
                  bot_id: Optional[int]=None) -> bool:
        _key = self._get_key(
            chat_id, user_id, self.prefix, self.separator, business_connection_id, message_thread_id, bot_id
        )
        with self.lock:
            data = self._read_from_file()
            if _key not in data:
                data[_key] = {"state": state, "data": {}}
            else:
                data[_key]["state"] = state
            self._write_to_file(data)
        return True

    def get_state(self, chat_id: int, user_id: int, business_connection_id: Optional[str]=None,
                  message_thread_id: Optional[int]=None, bot_id: Optional[int]=None) -> Union[str, None]:
        _key = self._get_key(
            chat_id, user_id, self.prefix, self.separator, business_connection_id, message_thread_id, bot_id
        )
        with self.lock:
            data = self._read_from_file()
            return data.get(_key, {}).get("state")
        
    def delete_state(self, chat_id: int, user_id: int, business_connection_id: Optional[str]=None,
                        message_thread_id: Optional[int]=None, bot_id: Optional[int]=None) -> bool:
        _key = self._get_key(
            chat_id, user_id, self.prefix, self.separator, business_connection_id, message_thread_id, bot_id
        )
        with self.lock:
            data = self._read_from_file()
            if _key in data:
                del data[_key]
                self._write_to_file(data)
                return True
            return False

    def set_data(self, chat_id: int, user_id: int, key: str, value: Union[str, int, float, dict],
                 business_connection_id: Optional[str]=None, message_thread_id: Optional[int]=None,
                 bot_id: Optional[int]=None) -> bool:
        _key = self._get_key(
            chat_id, user_id, self.prefix, self.separator, business_connection_id, message_thread_id, bot_id
        )
        with self.lock:
            data = self._read_from_file()
            state_data = data.get(_key, {})
            state_data["data"][key] = value
            if _key not in data:
                data[_key] = {"state": None, "data": state_data}
            else:
                data[_key]["data"][key] = value
            self._write_to_file(data)
        return True

    def get_data(self, chat_id: int, user_id: int, business_connection_id: Optional[str]=None,
                 message_thread_id: Optional[int]=None, bot_id: Optional[int]=None) -> dict:
        _key = self._get_key(
            chat_id, user_id, self.prefix, self.separator, business_connection_id, message_thread_id, bot_id
        )
        with self.lock:
            data = self._read_from_file()
            return data.get(_key, {}).get("data", {})

    def reset_data(self, chat_id: int, user_id: int, business_connection_id: Optional[str]=None,
                   message_thread_id: Optional[int]=None, bot_id: Optional[int]=None) -> bool:
        _key = self._get_key(
            chat_id, user_id, self.prefix, self.separator, business_connection_id, message_thread_id, bot_id
        )
        with self.lock:
            data = self._read_from_file()
            if _key in data:
                data[_key]["data"] = {}
                self._write_to_file(data)
                return True
            return False

    def get_interactive_data(self, chat_id: int, user_id: int, business_connection_id: Optional[str]=None,
                             message_thread_id: Optional[int]=None, bot_id: Optional[int]=None) -> Optional[dict]:
        return StateDataContext(
            self, chat_id=chat_id, user_id=user_id, business_connection_id=business_connection_id,
            message_thread_id=message_thread_id, bot_id=bot_id
        )

    def save(self, chat_id: int, user_id: int, data: dict, business_connection_id: Optional[str]=None,
             message_thread_id: Optional[int]=None, bot_id: Optional[int]=None) -> bool:
        _key = self._get_key(
            chat_id, user_id, self.prefix, self.separator, business_connection_id, message_thread_id, bot_id
        )
        with self.lock:
            data = self._read_from_file()
            data[_key]["data"] = data
            self._write_to_file(data)
        return True
    
    def __str__(self) -> str:
        return f"StatePickleStorage({self.file_path}, {self.prefix})"
