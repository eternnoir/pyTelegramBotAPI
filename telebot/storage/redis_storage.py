from telebot.storage.base_storage import StateStorageBase, StateContext
import json

redis_installed = True
try:
    from redis import Redis, ConnectionPool

except:
    redis_installed = False

class StateRedisStorage(StateStorageBase):
    """
    This class is for Redis storage.
    This will work only for states.
    To use it, just pass this class to:
    TeleBot(storage=StateRedisStorage())
    """
    def __init__(self, host='localhost', port=6379, db=0, password=None, prefix='telebot_'):
        self.redis = ConnectionPool(host=host, port=port, db=db, password=password)
        #self.con = Redis(connection_pool=self.redis) -> use this when necessary
        #
        # {chat_id: {user_id: {'state': None, 'data': {}}, ...}, ...}
        self.prefix = prefix
        if not redis_installed:
            raise Exception("Redis is not installed. Install it via 'pip install redis'")
    
    def get_record(self, key):
        """
        Function to get record from database.
        It has nothing to do with states.
        Made for backend compatibility
        """
        connection = Redis(connection_pool=self.redis)
        result = connection.get(self.prefix+str(key))
        connection.close()
        if result: return json.loads(result)
        return

    def set_record(self, key, value):
        """
        Function to set record to database.
        It has nothing to do with states.
        Made for backend compatibility
        """
        connection = Redis(connection_pool=self.redis)
        connection.set(self.prefix+str(key), json.dumps(value))
        connection.close()
        return True

    def delete_record(self, key):
        """
        Function to delete record from database.
        It has nothing to do with states.
        Made for backend compatibility
        """
        connection = Redis(connection_pool=self.redis)
        connection.delete(self.prefix+str(key))
        connection.close()
        return True

    def set_state(self, chat_id, user_id, state):
        """
        Set state for a particular user in a chat.
        """
        response = self.get_record(chat_id)
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
        self.set_record(chat_id, response)

        return True
    
    def delete_state(self, chat_id, user_id):
        """
        Delete state for a particular user in a chat.
        """
        response = self.get_record(chat_id)
        user_id = str(user_id)
        if response:
            if user_id in response:
                del response[user_id]
                if user_id == str(chat_id):
                    self.delete_record(chat_id)
                    return True
                else: self.set_record(chat_id, response)
                return True
        return False


    def get_value(self, chat_id, user_id, key):
        """
        Get value for a data of a user in a chat.
        """
        response = self.get_record(chat_id)
        user_id = str(user_id)
        if response:
            if user_id in response:
                if key in response[user_id]['data']:
                    return response[user_id]['data'][key]
        return None
    

    def get_state(self, chat_id, user_id):
        """
        Get state of a user in a chat.
        """
        response = self.get_record(chat_id)
        user_id = str(user_id)
        if response:
            if user_id in response:
                return response[user_id]['state']

        return None


    def get_data(self, chat_id, user_id):
        """
        Get data of particular user in a particular chat.
        """
        response = self.get_record(chat_id)
        user_id = str(user_id)
        if response:
            if user_id in response:
                return response[user_id]['data']
        return None


    def reset_data(self, chat_id, user_id):
        """
        Reset data of a user in a chat.
        """
        response = self.get_record(chat_id)
        user_id = str(user_id)
        if response:
            if user_id in response:
                response[user_id]['data'] = {}
                self.set_record(chat_id, response)
                return True

       


    def set_data(self, chat_id, user_id, key, value):
        """
        Set data without interactive data.
        """
        response = self.get_record(chat_id)
        user_id = str(user_id)
        if response:
            if user_id in response:
                response[user_id]['data'][key] = value
                self.set_record(chat_id, response)
                return True
        return False

    def get_interactive_data(self, chat_id, user_id):
        """
        Get Data in interactive way.
        You can use with() with this function.
        """
        return StateContext(self, chat_id, user_id)
    
    def save(self, chat_id, user_id, data):
        response = self.get_record(chat_id)
        user_id = str(user_id)
        if response:
            if user_id in response:
                response[user_id]['data'] = dict(data, **response[user_id]['data'])
                self.set_record(chat_id, response)
                return True
    
