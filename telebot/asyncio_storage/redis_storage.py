from telebot.asyncio_storage.base_storage import StateStorageBase, StateContext
import json


redis_installed = True
try:
    import aioredis
except ImportError:
    try:
        from redis import asyncio as aioredis
    except ImportError:
        redis_installed = False


class StateRedisStorage(StateStorageBase):
    """
    This class is for Redis storage.
    This will work only for states.
    To use it, just pass this class to:
    TeleBot(storage=StateRedisStorage())
    """
    def __init__(self, host='localhost', port=6379, db=0, password=None, prefix='telebot_'):
        if not redis_installed:
            raise ImportError('AioRedis is not installed. Install it via "pip install aioredis"')


        aioredis_version = tuple(map(int, aioredis.__version__.split(".")[0]))
        if aioredis_version < (2,):
            raise ImportError('Invalid aioredis version. Aioredis version should be >= 2.0.0')
        self.redis = aioredis.Redis(host=host, port=port, db=db, password=password)

        self.prefix = prefix
        #self.con = Redis(connection_pool=self.redis) -> use this when necessary
        #
        # {chat_id: {user_id: {'state': None, 'data': {}}, ...}, ...}
    
    async def get_record(self, key):
        """
        Function to get record from database.
        It has nothing to do with states.
        Made for backward compatibility
        """
        result = await self.redis.get(self.prefix+str(key))
        if result: return json.loads(result)
        return

    async def set_record(self, key, value):
        """
        Function to set record to database.
        It has nothing to do with states.
        Made for backward compatibility
        """
    
        await self.redis.set(self.prefix+str(key), json.dumps(value))
        return True

    async def delete_record(self, key):
        """
        Function to delete record from database.
        It has nothing to do with states.
        Made for backward compatibility
        """
        await self.redis.delete(self.prefix+str(key))
        return True

    async def set_state(self, chat_id, user_id, state):
        """
        Set state for a particular user in a chat.
        """
        response = await self.get_record(chat_id)
        user_id = str(user_id)
        if hasattr(state, 'name'):
            state = state.name
        if response:
            if user_id in response:
                response[user_id]['state'] = state
            else:
                response[user_id] = {'state': state, 'data': {}}
        else:
            response = {user_id: {'state': state, 'data': {}}}
        await self.set_record(chat_id, response)

        return True
    
    async def delete_state(self, chat_id, user_id):
        """
        Delete state for a particular user in a chat.
        """
        response = await self.get_record(chat_id)
        user_id = str(user_id)
        if response:
            if user_id in response:
                del response[user_id]
                if user_id == str(chat_id):
                    await self.delete_record(chat_id)
                    return True
                else: await self.set_record(chat_id, response)
                return True
        return False

    async def get_value(self, chat_id, user_id, key):
        """
        Get value for a data of a user in a chat.
        """
        response = await self.get_record(chat_id)
        user_id = str(user_id)
        if response:
            if user_id in response:
                if key in response[user_id]['data']:
                    return response[user_id]['data'][key]
        return None

    async def get_state(self, chat_id, user_id):
        """
        Get state of a user in a chat.
        """
        response = await self.get_record(chat_id)
        user_id = str(user_id)
        if response:
            if user_id in response:
                return response[user_id]['state']

        return None

    async def get_data(self, chat_id, user_id):
        """
        Get data of particular user in a particular chat.
        """
        response = await self.get_record(chat_id)
        user_id = str(user_id)
        if response:
            if user_id in response:
                return response[user_id]['data']
        return None

    async def reset_data(self, chat_id, user_id):
        """
        Reset data of a user in a chat.
        """
        response = await self.get_record(chat_id)
        user_id = str(user_id)
        if response:
            if user_id in response:
                response[user_id]['data'] = {}
                await self.set_record(chat_id, response)
                return True

    async def set_data(self, chat_id, user_id, key, value):
        """
        Set data without interactive data.
        """
        response = await self.get_record(chat_id)
        user_id = str(user_id)
        if response:
            if user_id in response:
                response[user_id]['data'][key] = value
                await self.set_record(chat_id, response)
                return True
        return False

    def get_interactive_data(self, chat_id, user_id):
        """
        Get Data in interactive way.
        You can use with() with this function.
        """
        return StateContext(self, chat_id, user_id)
    
    async def save(self, chat_id, user_id, data):
        response = await self.get_record(chat_id)
        user_id = str(user_id)
        if response:
            if user_id in response:
                response[user_id]['data'] = dict(data, **response[user_id]['data'])
                await self.set_record(chat_id, response)
                return True
