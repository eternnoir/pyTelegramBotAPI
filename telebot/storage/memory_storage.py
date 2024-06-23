from telebot.storage.base_storage import StateStorageBase, StateContext
from typing import Optional, Union

class StateMemoryStorage(StateStorageBase):
    def __init__(self, 
                 separator: Optional[str]=":",
                 prefix: Optional[str]="telebot"
                 ) -> None:
        self.separator = separator
        self.prefix = prefix
        if not self.prefix:
            raise ValueError("Prefix cannot be empty")
        
        self.data = {} # key: telebot:bot_id:business_connection_id:message_thread_id:chat_id:user_id

    def set_state(
            self, chat_id: int, user_id: int, state: str,   business_connection_id: Optional[str]=None,
            message_thread_id: Optional[int]=None, bot_id: Optional[int]=None

    ) -> bool:
        if hasattr(state, "name"):
            state = state.name

        _key = self.convert_params_to_key(
            chat_id, user_id, self.prefix, self.separator, business_connection_id, message_thread_id, bot_id
        )

        if self.data.get(_key) is None:
            self.data[_key] = {"state": state, "data": {}}
        else:
            self.data[_key]["state"] = state
        
        return True
    
    def get_state(
            self, chat_id: int, user_id: int, business_connection_id: Optional[str]=None,
            message_thread_id: Optional[int]=None, bot_id: Optional[int]=None
    ) -> Union[str, None]:

        _key = self.convert_params_to_key(
            chat_id, user_id, self.prefix, self.separator, business_connection_id, message_thread_id, bot_id
        )

        if self.data.get(_key) is None:
            return None
        
        return self.data[_key]["state"]
    
    def delete_state(
            self, chat_id: int, user_id: int, business_connection_id: Optional[str]=None,
            message_thread_id: Optional[int]=None, bot_id: Optional[int]=None
    ) -> bool:
        _key = self.convert_params_to_key(
            chat_id, user_id, self.prefix, self.separator, business_connection_id, message_thread_id, bot_id
        )
        
        if self.data.get(_key) is None:
            return False
        
        del self.data[_key]
        return True
        
    
    def set_data(
            self, chat_id: int, user_id: int, key: str, value: Union[str, int, float, dict],
            business_connection_id: Optional[str]=None, message_thread_id: Optional[int]=None,
            bot_id: Optional[int]=None) -> bool:
        
        _key = self.convert_params_to_key(
            chat_id, user_id, self.prefix, self.separator, business_connection_id, message_thread_id, bot_id
        )

        if self.data.get(_key) is None:
            return False
        self.data[_key]["data"][key] = value
        return True

    
    def get_data(
            self, chat_id: int, user_id: int, business_connection_id: Optional[str]=None,
            message_thread_id: Optional[int]=None, bot_id: Optional[int]=None
    ) -> dict:
        
        _key = self.convert_params_to_key(
            chat_id, user_id, self.prefix, self.separator, business_connection_id, message_thread_id, bot_id
        )

        return self.data.get(_key, {}).get("data", None)
    
    def reset_data(
            self, chat_id: int, user_id: int, business_connection_id: Optional[str]=None,
            message_thread_id: Optional[int]=None, bot_id: Optional[int]=None
    ) -> bool:
        
        _key = self.convert_params_to_key(
            chat_id, user_id, self.prefix, self.separator, business_connection_id, message_thread_id, bot_id
        )

        if self.data.get(_key) is None:
            return False
        self.data[_key]["data"] = {}
        return True
    
    def get_interactive_data(
            self, chat_id: int, user_id: int, business_connection_id: Optional[str]=None,
            message_thread_id: Optional[int]=None, bot_id: Optional[int]=None
    ) -> Optional[dict]:
        return StateContext(
            self, chat_id=chat_id, user_id=user_id, business_connection_id=business_connection_id,
            message_thread_id=message_thread_id, bot_id=bot_id
        )
    
    def save(
            self, chat_id: int, user_id: int, data: dict, business_connection_id: Optional[str]=None,
            message_thread_id: Optional[int]=None, bot_id: Optional[int]=None
    ) -> bool:
        _key = self.convert_params_to_key(
            chat_id, user_id, self.prefix, self.separator, business_connection_id,
            message_thread_id, bot_id
        )

        if self.data.get(_key) is None:
            return False
        self.data[_key]["data"] = data
        return True
    
    def __str__(self) -> str:
        return f"<StateMemoryStorage: {self.data}>"
            
            

