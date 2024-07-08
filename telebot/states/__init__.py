"""
Contains classes for states and state groups.
"""


class State:
    """
    Class representing a state.

    .. code-block:: python3

        class MyStates(StatesGroup):
            my_state = State() # returns my_state:State string.
    """
    def __init__(self) -> None:
        self.name: str = None
        self.group: StatesGroup = None
    def __str__(self) -> str:
        return f"<{self.group.__name__}:{self.name}>"


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
