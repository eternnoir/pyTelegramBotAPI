import json
from telebot.storage.base_storage import StateStorageBase, StateDataContext
from typing import Optional, Union

redis_installed = True
try:
    import redis
except ImportError:
    redis_installed = False


class StateRedisStorage(StateStorageBase):
    """
    State storage based on Redis.

    .. code-block:: python3

        storage = StateRedisStorage(...)
        bot = TeleBot(token, storage=storage)

    :param host: Redis host, default is "localhost".
    :type host: str

    :param port: Redis port, default is 6379.
    :type port: int

    :param db: Redis database, default is 0.
    :type db: int

    :param password: Redis password, default is None.
    :type password: Optional[str]

    :param prefix: Prefix for keys, default is "telebot".
    :type prefix: Optional[str]

    :param redis_url: Redis URL, default is None.
    :type redis_url: Optional[str]

    :param connection_pool: Redis connection pool, default is None.
    :type connection_pool: Optional[ConnectionPool]

    :param separator: Separator for keys, default is ":".
    :type separator: Optional[str]

    """

    def __init__(
        self,
        host="localhost",
        port=6379,
        db=0,
        password=None,
        prefix="telebot",
        redis_url=None,
        connection_pool: "redis.ConnectionPool" = None,
        separator: Optional[str] = ":",
    ) -> None:

        if not redis_installed:
            raise ImportError(
                "Redis is not installed. Please install it via pip install redis"
            )

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

        def set_state_action(pipe):
            pipe.multi()

            data = pipe.hget(_key, "data")
            result = pipe.execute()
            data = result[0]
            if data is None:
                # If data is None, set it to an empty dictionary
                data = {}
                pipe.hset(_key, "data", json.dumps(data))

            pipe.hset(_key, "state", state)

        self.redis.transaction(set_state_action, _key)
        return True

    def get_state(
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
        state_bytes = self.redis.hget(_key, "state")
        return state_bytes.decode("utf-8") if state_bytes else None

    def delete_state(
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
        return self.redis.delete(_key) > 0

    def set_data(
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

        def set_data_action(pipe):
            pipe.multi()
            data = pipe.hget(_key, "data")
            data = data.execute()[0]
            if data is None:
                raise RuntimeError(f"RedisStorage: key {_key} does not exist.")
            else:
                data = json.loads(data)
                data[key] = value
                pipe.hset(_key, "data", json.dumps(data))

        self.redis.transaction(set_data_action, _key)
        return True

    def get_data(
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
        data = self.redis.hget(_key, "data")
        return json.loads(data) if data else {}

    def reset_data(
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

        def reset_data_action(pipe):
            pipe.multi()
            if pipe.exists(_key):
                pipe.hset(_key, "data", "{}")
            else:
                return False

        self.redis.transaction(reset_data_action, _key)
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

    def save(
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

        def save_action(pipe):
            pipe.multi()
            if pipe.exists(_key):
                pipe.hset(_key, "data", json.dumps(data))
            else:
                return False

        self.redis.transaction(save_action, _key)
        return True

    def migrate_format(self, bot_id: int, prefix: Optional[str] = "telebot_"):
        """
        Migrate from old to new format of keys.
        Run this function once to migrate all redis existing keys to new format.

        Starting from version 4.23.0, the format of keys has been changed:
        <key>:value
        - Old format: {prefix}chat_id: {user_id: {'state': None, 'data': {}}, ...}
        - New format:
        {prefix}{separator}{bot_id}{separator}{business_connection_id}{separator}{message_thread_id}{separator}{chat_id}{separator}{user_id}: {'state': ..., 'data': {}}

        This function will help you to migrate from the old format to the new one in order to avoid data loss.

        :param bot_id: Bot ID; To get it, call a getMe request and grab the id from the response.
        :type bot_id: int

        :param prefix: Prefix for keys, default is "telebot_"(old default value)
        :type prefix: Optional[str]
        """
        keys = self.redis.keys(f"{prefix}*")

        for key in keys:
            old_key = key.decode("utf-8")
            # old: {prefix}chat_id: {user_id: {'state': None, 'data': {}}, ...}
            value = self.redis.get(old_key)
            value = json.loads(value)

            chat_id = old_key[len(prefix) :]
            user_id = list(value.keys())[0]
            state = value[user_id]["state"]
            state_data = value[user_id]["data"]

            # set new format
            new_key = self._get_key(
                int(chat_id), int(user_id), self.prefix, self.separator, bot_id=bot_id
            )
            self.redis.hset(new_key, "state", state)
            self.redis.hset(new_key, "data", json.dumps(state_data))

            # delete old key
            self.redis.delete(old_key)

    def __str__(self) -> str:
        return f"StateRedisStorage({self.redis})"
