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