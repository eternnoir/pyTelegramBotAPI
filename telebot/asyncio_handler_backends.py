from telebot.asyncio_middlewares import BaseMiddleware


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
