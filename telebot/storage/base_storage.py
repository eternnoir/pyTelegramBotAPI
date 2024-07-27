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

    def get_interactive_data(self, chat_id, user_id):
        raise NotImplementedError

    def save(self, chat_id, user_id, data):
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
        res = obj.get_data(
            chat_id=chat_id,
            user_id=user_id,
            business_connection_id=business_connection_id,
            message_thread_id=message_thread_id,
            bot_id=bot_id,
        )
        self.data = copy.deepcopy(res)
        self.chat_id = chat_id
        self.user_id = user_id
        self.bot_id = bot_id
        self.business_connection_id = business_connection_id
        self.message_thread_id = message_thread_id

    def __enter__(self):
        return self.data

    def __exit__(self, exc_type, exc_val, exc_tb):
        return self.obj.save(
            self.chat_id,
            self.user_id,
            self.data,
            self.business_connection_id,
            self.message_thread_id,
            self.bot_id,
        )
