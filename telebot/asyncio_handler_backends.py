import os
import pickle
import threading

from telebot import apihelper


class HandlerBackend(object):
    """
    Class for saving (next step|reply) handlers
    """
    def __init__(self, handlers=None):
        if handlers is None:
            handlers = {}
        self.handlers = handlers

    async def register_handler(self, handler_group_id, handler):
        raise NotImplementedError()

    async def clear_handlers(self, handler_group_id):
        raise NotImplementedError()

    async def get_handlers(self, handler_group_id):
        raise NotImplementedError()


class MemoryHandlerBackend(HandlerBackend):
    async def register_handler(self, handler_group_id, handler):
        if handler_group_id in self.handlers:
            self.handlers[handler_group_id].append(handler)
        else:
            self.handlers[handler_group_id] = [handler]

    async def clear_handlers(self, handler_group_id):
        self.handlers.pop(handler_group_id, None)

    async def get_handlers(self, handler_group_id):
        return self.handlers.pop(handler_group_id, None)

    async def load_handlers(self, filename, del_file_after_loading):
        raise NotImplementedError()


class FileHandlerBackend(HandlerBackend):
    def __init__(self, handlers=None, filename='./.handler-saves/handlers.save', delay=120):
        super(FileHandlerBackend, self).__init__(handlers)
        self.filename = filename
        self.delay = delay
        self.timer = threading.Timer(delay, self.save_handlers)

    async def register_handler(self, handler_group_id, handler):
        if handler_group_id in self.handlers:
            self.handlers[handler_group_id].append(handler)
        else:
            self.handlers[handler_group_id] = [handler]
        await self.start_save_timer()

    async def clear_handlers(self, handler_group_id):
        self.handlers.pop(handler_group_id, None)
        await self.start_save_timer()

    async def get_handlers(self, handler_group_id):
        handlers = self.handlers.pop(handler_group_id, None)
        await self.start_save_timer()
        return handlers

    async def start_save_timer(self):
        if not self.timer.is_alive():
            if self.delay <= 0:
                self.save_handlers()
            else:
                self.timer = threading.Timer(self.delay, self.save_handlers)
                self.timer.start()

    async def save_handlers(self):
        await self.dump_handlers(self.handlers, self.filename)

    async def load_handlers(self, filename=None, del_file_after_loading=True):
        if not filename:
            filename = self.filename
        tmp = await self.return_load_handlers(filename, del_file_after_loading=del_file_after_loading)
        if tmp is not None:
            self.handlers.update(tmp)

    @staticmethod
    async def dump_handlers(handlers, filename, file_mode="wb"):
        dirs = filename.rsplit('/', maxsplit=1)[0]
        os.makedirs(dirs, exist_ok=True)

        with open(filename + ".tmp", file_mode) as file:
            if (apihelper.CUSTOM_SERIALIZER is None):
                pickle.dump(handlers, file)
            else:
                apihelper.CUSTOM_SERIALIZER.dump(handlers, file)

        if os.path.isfile(filename):
            os.remove(filename)

        os.rename(filename + ".tmp", filename)

    @staticmethod
    async def return_load_handlers(filename, del_file_after_loading=True):
        if os.path.isfile(filename) and os.path.getsize(filename) > 0:
            with open(filename, "rb") as file:
                if (apihelper.CUSTOM_SERIALIZER is None):
                    handlers = pickle.load(file)
                else:
                    handlers = apihelper.CUSTOM_SERIALIZER.load(file)

            if del_file_after_loading:
                os.remove(filename)

            return handlers


class RedisHandlerBackend(HandlerBackend):
    def __init__(self, handlers=None, host='localhost', port=6379, db=0, prefix='telebot', password=None):
        super(RedisHandlerBackend, self).__init__(handlers)
        from redis import Redis
        self.prefix = prefix
        self.redis = Redis(host, port, db, password)

    async def _key(self, handle_group_id):
        return ':'.join((self.prefix, str(handle_group_id)))

    async def register_handler(self, handler_group_id, handler):
        handlers = []
        value = self.redis.get(self._key(handler_group_id))
        if value:
            handlers = pickle.loads(value)
        handlers.append(handler)
        self.redis.set(self._key(handler_group_id), pickle.dumps(handlers))

    async def clear_handlers(self, handler_group_id):
        self.redis.delete(self._key(handler_group_id))

    async def get_handlers(self, handler_group_id):
        handlers = None
        value = self.redis.get(self._key(handler_group_id))
        if value:
            handlers = pickle.loads(value)
            self.clear_handlers(handler_group_id)
        return handlers


class StateMemory:
    def __init__(self):
        self._states = {}

    async def add_state(self, chat_id, state):
        """
        Add a state.
        :param chat_id:
        :param state: new state
        """
        if chat_id in self._states:
            
            self._states[chat_id]['state'] = state
        else:
            self._states[chat_id] = {'state': state,'data': {}}

    async def current_state(self, chat_id):
        """Current state"""
        if chat_id in self._states: return self._states[chat_id]['state']
        else: return False

    async def delete_state(self, chat_id):
        """Delete a state"""
        self._states.pop(chat_id)

    def _get_data(self, chat_id):
        return self._states[chat_id]['data']

    async def set(self, chat_id, new_state):
        """
        Set a new state for a user.
        :param chat_id:
        :param new_state: new_state of a user
        """
        await self.add_state(chat_id,new_state)

    async def _add_data(self, chat_id, key, value):
        result = self._states[chat_id]['data'][key] = value
        return result

    async def finish(self, chat_id):
        """
        Finish(delete) state of a user.
        :param chat_id:
        """
        await self.delete_state(chat_id)

    def retrieve_data(self, chat_id):
        """
        Save input text.

        Usage:
        with bot.retrieve_data(message.chat.id) as data:
            data['name'] = message.text

        Also, at the end of your 'Form' you can get the name:
        data['name']
        """
        return StateContext(self, chat_id)


class StateFile:
    """
    Class to save states in a file.
    """
    def __init__(self, filename):
        self.file_path = filename

    async def add_state(self, chat_id, state):
        """
        Add a state.
        :param chat_id:
        :param state: new state
        """
        states_data = self._read_data()
        if chat_id in states_data:
            states_data[chat_id]['state'] = state
            return await self._save_data(states_data)
        else:
            new_data = states_data[chat_id] = {'state': state,'data': {}}
            return await self._save_data(states_data)


    async def current_state(self, chat_id):
        """Current state."""
        states_data = self._read_data()
        if chat_id in states_data: return states_data[chat_id]['state']
        else: return False

    async def delete_state(self, chat_id):
        """Delete a state"""
        states_data = await self._read_data()
        states_data.pop(chat_id)
        await self._save_data(states_data)

    async def _read_data(self):
        """
        Read the data from file.
        """
        file = open(self.file_path, 'rb')
        states_data = pickle.load(file)
        file.close()
        return states_data

    async def _create_dir(self):
        """
        Create directory .save-handlers.
        """
        dirs = self.file_path.rsplit('/', maxsplit=1)[0]
        os.makedirs(dirs, exist_ok=True)
        if not os.path.isfile(self.file_path):
            with open(self.file_path,'wb') as file:
                pickle.dump({}, file)
        
    async def _save_data(self, new_data):
        """
        Save data after editing.
        :param new_data:
        """
        with open(self.file_path, 'wb+') as state_file:
            pickle.dump(new_data, state_file, protocol=pickle.HIGHEST_PROTOCOL)
        return True

    def _get_data(self, chat_id):
        return self._read_data()[chat_id]['data']

    async def set(self, chat_id, new_state):
        """
        Set a new state for a user.
        :param chat_id:
        :param new_state: new_state of a user
        
        """
        await self.add_state(chat_id,new_state)

    async def _add_data(self, chat_id, key, value):
        states_data = self._read_data()
        result = states_data[chat_id]['data'][key] = value
        await self._save_data(result)

        return result

    async def finish(self, chat_id):
        """
        Finish(delete) state of a user.
        :param chat_id:
        """
        await self.delete_state(chat_id)

    async def retrieve_data(self, chat_id):
        """
        Save input text.

        Usage:
        with bot.retrieve_data(message.chat.id) as data:
            data['name'] = message.text

        Also, at the end of your 'Form' you can get the name:
        data['name']
        """
        return StateFileContext(self, chat_id)


class StateContext:
    """
    Class for data.
    """
    def __init__(self , obj: StateMemory, chat_id) -> None:
        self.obj = obj
        self.chat_id = chat_id
        self.data = obj._get_data(chat_id)

    async def __aenter__(self):
        return self.data

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        return

class StateFileContext:
    """
    Class for data.
    """
    def __init__(self , obj: StateFile, chat_id) -> None:
        self.obj = obj
        self.chat_id = chat_id
        self.data = None

    async def __aenter__(self):
        self.data = self.obj._get_data(self.chat_id)
        return self.data

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        old_data = await self.obj._read_data()
        for i in self.data:
            old_data[self.chat_id]['data'][i] = self.data.get(i)
        await self.obj._save_data(old_data)

        return
