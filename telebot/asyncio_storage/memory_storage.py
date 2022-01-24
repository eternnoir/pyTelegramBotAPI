from telebot.asyncio_storage.base_storage import StateStorageBase, StateContext

class StateMemoryStorage(StateStorageBase):
    def __init__(self) -> None:
        self.data = {}
        #
        # {chat_id: {user_id: {'state': None, 'data': {}}, ...}, ...}
    
    
    async def set_state(self, chat_id, user_id, state):
        if chat_id in self.data:
            if user_id in self.data[chat_id]:
                self.data[chat_id][user_id]['state'] = state
                return True
            else:
                self.data[chat_id][user_id] = {'state': state, 'data': {}}
                return True
        self.data[chat_id] = {user_id: {'state': state, 'data': {}}}
        return True
    
    async def delete_state(self, chat_id, user_id):
        if self.data.get(chat_id):
            if self.data[chat_id].get(user_id):
                del self.data[chat_id][user_id]
                if chat_id == user_id:
                    del self.data[chat_id]
                    
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
                return True
        return False

    async def set_data(self, chat_id, user_id, key, value):
        if self.data.get(chat_id):
            if self.data[chat_id].get(user_id):
                self.data[chat_id][user_id]['data'][key] = value
                return True
        raise RuntimeError('chat_id {} and user_id {} does not exist'.format(chat_id, user_id))

    def get_interactive_data(self, chat_id, user_id):
        return StateContext(self, chat_id, user_id)

    async def save(self, chat_id, user_id, data):
        self.data[chat_id][user_id]['data'] = data 