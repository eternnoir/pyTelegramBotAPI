class BaseMiddleware:
    """
    Base class for middleware.
    Your middlewares should be inherited from this class.

    Set update_sensitive=True if you want to get different updates on
    different functions. For example, if you want to handle pre_process for
    message update, then you will have to create pre_process_message function, and
    so on. Same applies to post_process.

    .. code-block:: python
        class MyMiddleware(BaseMiddleware):
            def __init__(self):
                self.update_sensitive = True
                self.update_types = ['message', 'edited_message']
            
            def pre_process_message(self, message, data):
                # only message update here
                pass

            def post_process_message(self, message, data, exception):
                pass # only message update here for post_process

            def pre_process_edited_message(self, message, data):
                # only edited_message update here
                pass

            def post_process_edited_message(self, message, data, exception):
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
    def __init__(self) -> None:
        self.name = None

    def __str__(self) -> str:
        return self.name


class StatesGroup:
    def __init_subclass__(cls) -> None:

        for name, value in cls.__dict__.items():
            if not name.startswith('__') and not callable(value) and isinstance(value, State):
                # change value of that variable
                value.name = ':'.join((cls.__name__, name))
                value.group = cls


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