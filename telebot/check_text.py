from typing import Optional, Union

from telebot import types


class CheckText:
    """
    Advanced text filter to check types.Message. For example, the handler

    >>> @bot.message_handler(text=CheckText(contains=["hello", "world"], equals="potato", ends_with=["foo", "bar"]))
    >>> async def handler(...):
    ...     ...

    will receive all of the following: "hello world", "hello", "potato", "the world is ending", "hello foo", "bar"
    """

    def __init__(
        self,
        equals: Optional[str] = None,
        contains: Optional[Union[list, tuple]] = None,
        starts_with: Optional[Union[str, list, tuple]] = None,
        ends_with: Optional[Union[str, list, tuple]] = None,
        ignore_case: bool = False,
    ):
        to_check = sum((pattern is not None for pattern in (equals, contains, starts_with, ends_with)))
        if to_check == 0:
            raise ValueError("None of the check modes was specified")

        self.equals = equals
        self.contains = self._to_list(contains, filter_name="contains")
        self.starts_with = self._to_list(starts_with, filter_name="starts_with")
        self.ends_with = self._to_list(ends_with, filter_name="ends_with")
        self.ignore_case = ignore_case

    def _to_list(self, iterable, filter_name) -> list[str]:
        if not iterable:
            pass
        elif not isinstance(iterable, str) and not isinstance(iterable, list) and not isinstance(iterable, tuple):
            raise ValueError(f"Incorrect value of {filter_name!r}")
        elif isinstance(iterable, str):
            iterable = [iterable]
        elif isinstance(iterable, list) or isinstance(iterable, tuple):
            iterable = [i for i in iterable if isinstance(i, str)]
        return iterable

    async def check(self, message: types.Message):
        text = message.text_content

        if self.ignore_case:
            text = text.lower()
            prepare_func = lambda string: str(string).lower()
        else:
            prepare_func = str

        if self.equals:
            result = prepare_func(self.equals) == text
            if result:
                return True
            elif not result and not any((self.contains, self.starts_with, self.ends_with)):
                return False

        if self.contains:
            result = any([prepare_func(i) in text for i in self.contains])
            if result:
                return True
            elif not result and not any((self.starts_with, self.ends_with)):
                return False

        if self.starts_with:
            result = any([text.startswith(prepare_func(i)) for i in self.starts_with])
            if result:
                return True
            elif not result and not self.ends_with:
                return False

        if self.ends_with:
            return any([text.endswith(prepare_func(i)) for i in self.ends_with])

        return False
