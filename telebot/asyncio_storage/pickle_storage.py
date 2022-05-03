from telebot.asyncio_storage.base_storage import StateStorageBase, StateContext
import os

import pickle


class StatePickleStorage(StateStorageBase):
    def __init__(self, file_path="./.state-save/states.pkl") -> None:
        self.file_path = file_path
        self.create_dir()
        self.data = self.read()

    async def convert_old_to_new(self):
        # old looks like:
        # {1: {'state': 'start', 'data': {'name': 'John'}}
        # we should update old version pickle to new.
        # new looks like:
        # {1: {2: {'state': 'start', 'data': {'name': 'John'}}}}
        new_data = {}
        for key, value in self.data.items():
            # this returns us id and dict with data and state
            new_data[key] = {key: value} # convert this to new
        # pass it to global data
        self.data = new_data
        self.update_data() # update data in file

    def create_dir(self):
        """
        Create directory .save-handlers.
        """
        dirs = self.file_path.rsplit('/', maxsplit=1)[0]
        os.makedirs(dirs, exist_ok=True)
        if not os.path.isfile(self.file_path):
            with open(self.file_path,'wb') as file:
                pickle.dump({}, file)

    def read(self):
        file = open(self.file_path, 'rb')
        data = pickle.load(file)
        file.close()
        return data
    
    def update_data(self):
        file = open(self.file_path, 'wb+')
        pickle.dump(self.data, file, protocol=pickle.HIGHEST_PROTOCOL)
        file.close()

    async def set_state(self, chat_id, user_id, state):
        if hasattr(state, 'name'):
            state = state.name
        if chat_id in self.data:
            if user_id in self.data[chat_id]:
                self.data[chat_id][user_id]['state'] = state
                return True
            else:
                self.data[chat_id][user_id] = {'state': state, 'data': {}}
                return True
        self.data[chat_id] = {user_id: {'state': state, 'data': {}}}
        self.update_data()
        return True
    
    async def delete_state(self, chat_id, user_id):
        if self.data.get(chat_id):
            if self.data[chat_id].get(user_id):
                del self.data[chat_id][user_id]
                if chat_id == user_id:
                    del self.data[chat_id]
                self.update_data()
                return True

        return False

    
    async def get_state(self, chat_id, user_id):
        if self.data.get(chat_id):
            if self.data[chat_id].get(user_id):
                return self.data[chat_id][user_id]['state']

        return None
    async def get_data(self, chat_id, user_id):
        if self.data.get(chat_id):
            if self.data[chat_id].get(user_id):
                return self.data[chat_id][user_id]['data']
        
        return None

    async def reset_data(self, chat_id, user_id):
        if self.data.get(chat_id):
            if self.data[chat_id].get(user_id):
                self.data[chat_id][user_id]['data'] = {}
                self.update_data()
                return True
        return False

    async def set_data(self, chat_id, user_id, key, value):
        if self.data.get(chat_id):
            if self.data[chat_id].get(user_id):
                self.data[chat_id][user_id]['data'][key] = value
                self.update_data()
                return True
        raise RuntimeError('chat_id {} and user_id {} does not exist'.format(chat_id, user_id))

    def get_interactive_data(self, chat_id, user_id):
        return StateContext(self, chat_id, user_id)

    async def save(self, chat_id, user_id, data):
        self.data[chat_id][user_id]['data'] = data
        self.update_data()