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
        # print all variables of a subclass
        for name, value in cls.__dict__.items():
            if not name.startswith('__') and not callable(value) and isinstance(value, State):
                # change value of that variable
                value.name = ':'.join((cls.__name__, name))
