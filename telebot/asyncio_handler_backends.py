"""
File with all middleware classes, states.
"""


class BaseMiddleware:
    """
    Base class for middleware.
    Your middlewares should be inherited from this class.

    Set update_sensitive=True if you want to get different updates on
    different functions. For example, if you want to handle pre_process for
    message update, then you will have to create pre_process_message function, and
    so on. Same applies to post_process.

    .. code-block:: python
        :caption: Example of class-based middlewares

        class MyMiddleware(BaseMiddleware):
            def __init__(self):
                self.update_sensitive = True
                self.update_types = ['message', 'edited_message']
            
            async def pre_process_message(self, message, data):
                # only message update here
                pass

            async def post_process_message(self, message, data, exception):
                pass # only message update here for post_process

            async def pre_process_edited_message(self, message, data):
                # only edited_message update here
                pass

            async def post_process_edited_message(self, message, data, exception):
                pass # only edited_message update here for post_process
    """

    update_sensitive: bool = False

    def __init__(self):
        pass

    async def pre_process(self, message, data):
        raise NotImplementedError

    async def post_process(self, message, data, exception):
        raise NotImplementedError


class State:
    """
    Class representing a state.

    .. code-block:: python3

        class MyStates(StatesGroup):
            my_state = State() # returns my_state:State string.
    """
    def __init__(self) -> None:
        self.name = None

    def __str__(self) -> str:
        return self.name


class StatesGroup:
    """
    Class representing common states.

    .. code-block:: python3

        class MyStates(StatesGroup):
            my_state = State() # returns my_state:State string.
    """
    def __init_subclass__(cls) -> None:
        state_list = []
        for name, value in cls.__dict__.items():
            if not name.startswith('__') and not callable(value) and isinstance(value, State):
                # change value of that variable
                value.name = ':'.join((cls.__name__, name))
                value.group = cls
                state_list.append(value)
        cls._state_list = state_list

    @classmethod
    def state_list(self):
        return self._state_list


class SkipHandler:
    """
    Class for skipping handlers.
    Just return instance of this class 
    in middleware to skip handler.
    Update will go to post_process,
    but will skip execution of handler.
    """

    def __init__(self) -> None:
        pass


class CancelUpdate:
    """
    Class for canceling updates.
    Just return instance of this class 
    in middleware to skip update.
    Update will skip handler and execution
    of post_process in middlewares.
    """

    def __init__(self) -> None:
        pass


class ContinueHandling:
    """
    Class for continue updates in handlers.
    Just return instance of this class 
    in handlers to continue process.
    
    .. code-block:: python3
        :caption: Example of using ContinueHandling

        @bot.message_handler(commands=['start'])
        async def start(message):
            await bot.send_message(message.chat.id, 'Hello World!')
            return ContinueHandling()
        
        @bot.message_handler(commands=['start'])
        async def start2(message):
            await bot.send_message(message.chat.id, 'Hello World2!')
   
    """
    def __init__(self) -> None:
        pass
