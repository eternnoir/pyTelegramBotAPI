import copy


class StateStorageBase:
    def __init__(self) -> None:
        pass

    async def set_data(self, chat_id, user_id, key, value):
        """
        Set data for a user in a particular chat.
        """
        raise NotImplementedError

    async def get_data(self, chat_id, user_id):
        """
        Get data for a user in a particular chat.
        """
        raise NotImplementedError
    
    async def set_state(self, chat_id, user_id, state):
        """
        Set state for a particular user.

        ! Note that you should create a 
        record if it does not exist, and 
        if a record with state already exists,
        you need to update a record.
        """
        raise NotImplementedError
    
    async def delete_state(self, chat_id, user_id):
        """
        Delete state for a particular user.
        """
        raise NotImplementedError
    
    async def reset_data(self, chat_id, user_id):
        """
        Reset data for a particular user in a chat.
        """
        raise NotImplementedError
    
    async def get_state(self, chat_id, user_id):
        raise NotImplementedError
        
    async def save(self, chat_id, user_id, data):
        raise NotImplementedError


class StateContext:
    """
    Class for data.
    """

    def __init__(self, obj, chat_id, user_id):
        self.obj = obj
        self.data = None
        self.chat_id = chat_id
        self.user_id = user_id

    

    async def __aenter__(self):
        self.data = copy.deepcopy(await self.obj.get_data(self.chat_id, self.user_id))
        return self.data

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        return await self.obj.save(self.chat_id, self.user_id, self.data)