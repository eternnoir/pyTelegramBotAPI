import typing


class CallbackDataFilter:

    def __init__(self, factory, config: typing.Dict[str, str]):
        self.config = config
        self.factory = factory

    def check(self, query):
        """
        Checks if query.data appropriates to specified config

        :param query: telebot.types.CallbackQuery
        :return: bool
        """

        try:
            data = self.factory.parse(query.data)
        except ValueError:
            return False

        for key, value in self.config.items():
            if isinstance(value, (list, tuple, set, frozenset)):
                if data.get(key) not in value:
                    return False
            elif data.get(key) != value:
                return False
        return True


class CallbackData:
    """
    Callback data factory
    This class will help you to work with CallbackQuery
    """

    def __init__(self, *parts, prefix: str, sep=':'):
        if not isinstance(prefix, str):
            raise TypeError(f'Prefix must be instance of str not {type(prefix).__name__}')
        if not prefix:
            raise ValueError("Prefix can't be empty")
        if sep in prefix:
            raise ValueError(f"Separator {sep!r} can't be used in prefix")

        self.prefix = prefix
        self.sep = sep

        self._part_names = parts

    def new(self, *args, **kwargs) -> str:
        """
        Generate callback data

        :param args: positional parameters of CallbackData instance parts
        :param kwargs: named parameters
        :return: str
        """
        args = list(args)

        data = [self.prefix]

        for part in self._part_names:
            value = kwargs.pop(part, None)
            if value is None:
                if args:
                    value = args.pop(0)
                else:
                    raise ValueError(f'Value for {part!r} was not passed!')

            if value is not None and not isinstance(value, str):
                value = str(value)

            if self.sep in value:
                raise ValueError(f"Symbol {self.sep!r} is defined as the separator and can't be used in parts' values")

            data.append(value)

        if args or kwargs:
            raise TypeError('Too many arguments were passed!')

        callback_data = self.sep.join(data)

        if len(callback_data.encode()) > 64:
            raise ValueError('Resulted callback data is too long!')

        return callback_data

    def parse(self, callback_data: str) -> typing.Dict[str, str]:
        """
        Parse data from the callback data
        
        :param callback_data: string, use to telebot.types.CallbackQuery to parse it from string to a dict
        :return: dict parsed from callback data
        """

        prefix, *parts = callback_data.split(self.sep)
        if prefix != self.prefix:
            raise ValueError("Passed callback data can't be parsed with that prefix.")
        elif len(parts) != len(self._part_names):
            raise ValueError('Invalid parts count!')

        result = {'@': prefix}
        result.update(zip(self._part_names, parts))
        return result

    def filter(self, **config) -> CallbackDataFilter:
        """
        Generate filter

        :param config: specified named parameters will be checked with CallbackQury.data
        :return: CallbackDataFilter class
        """

        for key in config.keys():
            if key not in self._part_names:
                raise ValueError(f'Invalid field name {key!r}')
        return CallbackDataFilter(self, config)
