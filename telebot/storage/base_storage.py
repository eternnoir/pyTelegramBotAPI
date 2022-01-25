import copy

class StateStorageBase:
    def __init__(self) -> None:
        pass

    def set_data(self, chat_id, user_id, key, value):
        """
        Set data for a user in a particular chat.
        """
        raise NotImplementedError

    def get_data(self, chat_id, user_id):
        """
        Get data for a user in a particular chat.
        """
        raise NotImplementedError
    
    def set_state(self, chat_id, user_id, state):
        """
        Set state for a particular user.

        ! Note that you should create a 
        record if it does not exist, and 
        if a record with state already exists,
        you need to update a record.
        """
        raise NotImplementedError
    
    def delete_state(self, chat_id, user_id):
        """
        Delete state for a particular user.
        """
        raise NotImplementedError
    
    def reset_data(self, chat_id, user_id):
        """
        Reset data for a particular user in a chat.
        """
        raise NotImplementedError
    
    def get_state(self, chat_id, user_id):
        raise NotImplementedError
        
    def save(self, chat_id, user_id, data):
        raise NotImplementedError



class StateContext:
    """
    Class for data.
    """
    def __init__(self , obj, chat_id, user_id) -> None:
        self.obj = obj
        self.data = copy.deepcopy(obj.get_data(chat_id, user_id))
        self.chat_id = chat_id
        self.user_id = user_id


    def __enter__(self):
        return self.data

    def __exit__(self, exc_type, exc_val, exc_tb):
        return self.obj.save(self.chat_id, self.user_id, self.data)