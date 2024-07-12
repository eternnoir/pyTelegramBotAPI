import json
from telebot.storage.base_storage import StateStorageBase, StateContext
from typing import Optional, Union

redis_installed = True
try:
    import redis
except ImportError:
    redis_installed = False

class StateRedisStorage(StateStorageBase):
    def __init__(self, host='localhost', port=6379, db=0, password=None,
                 prefix='telebot',
                 redis_url=None,
                 connection_pool: 'redis.ConnectionPool'=None,
                 separator: Optional[str]=":",
                 ) -> None:
        
        if not redis_installed:
            raise ImportError("Redis is not installed. Please install it via pip install redis")

        self.separator = separator
        self.prefix = prefix
        if not self.prefix:
            raise ValueError("Prefix cannot be empty")
        
        if redis_url:
            self.redis = redis.Redis.from_url(redis_url)
        elif connection_pool:
            self.redis = redis.Redis(connection_pool=connection_pool)
        else:
            self.redis = redis.Redis(host=host, port=port, db=db, password=password)
    

    def set_state(
            self, chat_id: int, user_id: int, state: str, 
            business_connection_id: Optional[str] = None,
            message_thread_id: Optional[int] = None, bot_id: Optional[int] = None
    ) -> bool:
        if hasattr(state, "name"):
            state = state.name

        _key = self.convert_params_to_key(
            chat_id, user_id, self.prefix, self.separator, business_connection_id, message_thread_id, bot_id
        )

        def set_state_action(pipe):
            pipe.multi()
            #pipe.hset(_key, mapping={"state": state, "data": "{}"})
            pipe.hset(_key, "state", state)
        
        self.redis.transaction(set_state_action, _key)
        return True

    def get_state(
            self, chat_id: int, user_id: int, business_connection_id: Optional[str] = None,
            message_thread_id: Optional[int] = None, bot_id: Optional[int] = None
    ) -> Union[str, None]:
        _key = self.convert_params_to_key(
            chat_id, user_id, self.prefix, self.separator, business_connection_id, message_thread_id, bot_id
        )
        state_bytes = self.redis.hget(_key, "state")
        return state_bytes.decode('utf-8') if state_bytes else None

    def delete_state(
            self, chat_id: int, user_id: int, business_connection_id: Optional[str] = None,
            message_thread_id: Optional[int] = None, bot_id: Optional[int] = None
    ) -> bool:
        _key = self.convert_params_to_key(
            chat_id, user_id, self.prefix, self.separator, business_connection_id, message_thread_id, bot_id
        )
        return self.redis.delete(_key) > 0

    def set_data(
            self, chat_id: int, user_id: int, key: str, value: Union[str, int, float, dict],
            business_connection_id: Optional[str] = None, message_thread_id: Optional[int] = None,
            bot_id: Optional[int] = None
    ) -> bool:
        _key = self.convert_params_to_key(
            chat_id, user_id, self.prefix, self.separator, business_connection_id, message_thread_id, bot_id
        )

        def set_data_action(pipe):
            pipe.multi()
            data = pipe.hget(_key, "data")
            data = data.execute()[0]
            if data is None:
                pipe.hset(_key, "data", json.dumps({key: value}))
            else:
                data = json.loads(data)
                data[key] = value
                pipe.hset(_key, "data", json.dumps(data))

        self.redis.transaction(set_data_action, _key)
        return True

    def get_data(
            self, chat_id: int, user_id: int, business_connection_id: Optional[str] = None,
            message_thread_id: Optional[int] = None, bot_id: Optional[int] = None
    ) -> dict:
        _key = self.convert_params_to_key(
            chat_id, user_id, self.prefix, self.separator, business_connection_id, message_thread_id, bot_id
        )
        data = self.redis.hget(_key, "data")
        return json.loads(data) if data else {}

    def reset_data(
            self, chat_id: int, user_id: int, business_connection_id: Optional[str] = None,
            message_thread_id: Optional[int] = None, bot_id: Optional[int] = None
    ) -> bool:
        _key = self.convert_params_to_key(
            chat_id, user_id, self.prefix, self.separator, business_connection_id, message_thread_id, bot_id
        )

        def reset_data_action(pipe):
            pipe.multi()
            if pipe.exists(_key):
                pipe.hset(_key, "data", "{}")
            else:
                return False

        self.redis.transaction(reset_data_action, _key)
        return True

    def get_interactive_data(
            self, chat_id: int, user_id: int, business_connection_id: Optional[str] = None,
            message_thread_id: Optional[int] = None, bot_id: Optional[int] = None
    ) -> Optional[dict]:
        return StateContext(
            self, chat_id=chat_id, user_id=user_id, business_connection_id=business_connection_id,
            message_thread_id=message_thread_id, bot_id=bot_id
        )

    def save(
            self, chat_id: int, user_id: int, data: dict, business_connection_id: Optional[str] = None,
            message_thread_id: Optional[int] = None, bot_id: Optional[int] = None
    ) -> bool:
        _key = self.convert_params_to_key(
            chat_id, user_id, self.prefix, self.separator, business_connection_id,
            message_thread_id, bot_id
        )

        def save_action(pipe):
            pipe.multi()
            if pipe.exists(_key):
                pipe.hset(_key, "data", json.dumps(data))
            else:
                return False

        self.redis.transaction(save_action, _key)
        return True

    def __str__(self) -> str:
        keys = self.redis.keys(f"{self.prefix}{self.separator}*")
        data = {key.decode(): self.redis.hgetall(key) for key in keys}
        return f"<StateRedisStorage: {data}>"
