import copy


class StateStorageBase:
    def __init__(self) -> None:
        pass

    async def set_data(self, chat_id, user_id, key, value,
        business_connection_id=None,
        message_thread_id=None,
        bot_id=None,
    ):
        """
        Set data for a user in a particular chat.
        """
        raise NotImplementedError

    async def get_data(self, chat_id, user_id):
        """
        Get data for a user in a particular chat.
        """
        raise NotImplementedError

    async def set_state(self, chat_id, user_id, state,
        business_connection_id=None,
        message_thread_id=None,
        bot_id=None,
    ):
        """
        Set state for a particular user.

        ! Note that you should create a
        record if it does not exist, and
        if a record with state already exists,
        you need to update a record.
        """
        raise NotImplementedError

    async def delete_state(self, chat_id, user_id,
        business_connection_id=None,
        message_thread_id=None,
        bot_id=None,
    ):
        """
        Delete state for a particular user.
        """
        raise NotImplementedError

    async def reset_data(self, chat_id, user_id,
        business_connection_id=None,
        message_thread_id=None,
        bot_id=None,
    ):
        """
        Reset data for a particular user in a chat.
        """
        raise NotImplementedError

    async def get_state(self, chat_id, user_id,
        business_connection_id=None,
        message_thread_id=None,
        bot_id=None,
    ):
        raise NotImplementedError

    def get_interactive_data(self, chat_id, user_id,
        business_connection_id=None,
        message_thread_id=None,
        bot_id=None,
    ):
        """
        Should be sync, but should provide a context manager
        with __aenter__ and __aexit__ methods.
        """
        raise NotImplementedError

    async def save(self, chat_id, user_id, data):
        raise NotImplementedError

    def _get_key(
        self,
        chat_id: int,
        user_id: int,
        prefix: str,
        separator: str,
        business_connection_id: str = None,
        message_thread_id: int = None,
        bot_id: int = None,
    ) -> str:
        """
        Convert parameters to a key.
        """
        params = [prefix]
        if bot_id:
            params.append(str(bot_id))
        if business_connection_id:
            params.append(business_connection_id)
        if message_thread_id:
            params.append(str(message_thread_id))
        params.append(str(chat_id))
        params.append(str(user_id))

        return separator.join(params)


class StateDataContext:
    """
    Class for data.
    """

    def __init__(
        self,
        obj,
        chat_id,
        user_id,
        business_connection_id=None,
        message_thread_id=None,
        bot_id=None,
    ):
        self.obj = obj
        self.data = None
        self.chat_id = chat_id
        self.user_id = user_id
        self.bot_id = bot_id
        self.business_connection_id = business_connection_id
        self.message_thread_id = message_thread_id

    async def __aenter__(self):
        data = await self.obj.get_data(
            chat_id=self.chat_id,
            user_id=self.user_id,
            business_connection_id=self.business_connection_id,
            message_thread_id=self.message_thread_id,
            bot_id=self.bot_id,
        )
        self.data = copy.deepcopy(data)
        return self.data

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        return await self.obj.save(
            self.chat_id,
            self.user_id,
            self.data,
            self.business_connection_id,
            self.message_thread_id,
            self.bot_id,
        )
