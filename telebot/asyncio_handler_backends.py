import os
import pickle



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

    def get_data(self, chat_id):
        return self._states[chat_id]['data']

    async def set(self, chat_id, new_state):
        """
        Set a new state for a user.
        :param chat_id:
        :param new_state: new_state of a user
        """
        await self.add_state(chat_id,new_state)

    async def add_data(self, chat_id, key, value):
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
        states_data = self.read_data()
        if chat_id in states_data:
            states_data[chat_id]['state'] = state
            return await self.save_data(states_data)
        else:
            states_data[chat_id] = {'state': state,'data': {}}
            return await self.save_data(states_data)


    async def current_state(self, chat_id):
        """Current state."""
        states_data = self.read_data()
        if chat_id in states_data: return states_data[chat_id]['state']
        else: return False

    async def delete_state(self, chat_id):
        """Delete a state"""
        states_data = self.read_data()
        states_data.pop(chat_id)
        await self.save_data(states_data)

    def read_data(self):
        """
        Read the data from file.
        """
        file = open(self.file_path, 'rb')
        states_data = pickle.load(file)
        file.close()
        return states_data

    def create_dir(self):
        """
        Create directory .save-handlers.
        """
        dirs = self.file_path.rsplit('/', maxsplit=1)[0]
        os.makedirs(dirs, exist_ok=True)
        if not os.path.isfile(self.file_path):
            with open(self.file_path,'wb') as file:
                pickle.dump({}, file)
        
    async def save_data(self, new_data):
        """
        Save data after editing.
        :param new_data:
        """
        with open(self.file_path, 'wb+') as state_file:
            pickle.dump(new_data, state_file, protocol=pickle.HIGHEST_PROTOCOL)
        return True

    def get_data(self, chat_id):
        return self.read_data()[chat_id]['data']

    async def set(self, chat_id, new_state):
        """
        Set a new state for a user.
        :param chat_id:
        :param new_state: new_state of a user
        
        """
        await self.add_state(chat_id,new_state)

    async def add_data(self, chat_id, key, value):
        states_data = self.read_data()
        result = states_data[chat_id]['data'][key] = value
        await self.save_data(result)

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
        return StateFileContext(self, chat_id)


class StateContext:
    """
    Class for data.
    """
    def __init__(self , obj: StateMemory, chat_id) -> None:
        self.obj = obj
        self.chat_id = chat_id
        self.data = obj.get_data(chat_id)

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
        self.data = self.obj.get_data(self.chat_id)
        return self.data

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        old_data = self.obj.read_data()
        for i in self.data:
            old_data[self.chat_id]['data'][i] = self.data.get(i)
        await self.obj.save_data(old_data)

        return


class BaseMiddleware:
    """
    Base class for middleware.

    Your middlewares should be inherited from this class.
    """
    def __init__(self):
        pass

    async def pre_process(self, message, data):
        raise NotImplementedError
    async def post_process(self, message, data, exception):
        raise NotImplementedError

