from telebot.storage.base_storage import StateStorageBase, StateContext

class StateMemoryStorage(StateStorageBase):
    def __init__(self) -> None:
        self.data = {}
        #
        # {chat_id: {user_id: {'state': None, 'data': {}}, ...}, ...}
    
    
    def set_state(self, chat_id, user_id, state):
        if chat_id in self.data:
            if user_id in self.data[chat_id]:
                self.data[chat_id][user_id]['state'] = state
                return True
            else:
                self.data[chat_id][user_id] = {'state': state, 'data': {}}
                return True
        self.data[chat_id] = {user_id: {'state': state, 'data': {}}}
        return True
    
    def delete_state(self, chat_id, user_id):
        if self.data.get(chat_id):
            if self.data[chat_id].get(user_id):
                del self.data[chat_id][user_id]
                if chat_id == user_id:
                    del self.data[chat_id]
                    
                return True

        return False

    
    def get_state(self, chat_id, user_id):
        if self.data.get(chat_id):
            if self.data[chat_id].get(user_id):
                return self.data[chat_id][user_id]['state']

        return None
    def get_data(self, chat_id, user_id):
        if self.data.get(chat_id):
            if self.data[chat_id].get(user_id):
                return self.data[chat_id][user_id]['data']
        
        return None

    def reset_data(self, chat_id, user_id):
        if self.data.get(chat_id):
            if self.data[chat_id].get(user_id):
                self.data[chat_id][user_id]['data'] = {}
                return True
        return False

    def set_data(self, chat_id, user_id, key, value):
        if self.data.get(chat_id):
            if self.data[chat_id].get(user_id):
                self.data[chat_id][user_id]['data'][key] = value
                return True
        raise RuntimeError('chat_id {} and user_id {} does not exist'.format(chat_id, user_id))

    def get_interactive_data(self, chat_id, user_id):
        return StateContext(self, chat_id, user_id)

    def save(self, chat_id, user_id, data):
        self.data[chat_id][user_id]['data'] = data