# -*- coding: utf-8 -*-
import re

from telebot import util


class MessageHandler:

    def __init__(self, handler, commands=None, regexp=None, func=None, content_types=None):
        self.handler = handler
        self.tests = []
        if content_types is not None:
            self.tests.append(lambda m: m.content_type in content_types)

        if commands is not None:
            self.tests.append(lambda m: m.content_type == 'text' and util.extract_command(m.text) in commands)

        if regexp is not None:
            self.tests.append(lambda m: m.content_type == 'text' and re.search(regexp, m.text))

        if func is not None:
            self.tests.append(func)

    def test_message(self, message):
        return all([test(message) for test in self.tests])

    def __call__(self, update):
        if update.message is None:
            return

        if self.test_message(update.message):
            r = self.handler(update.message)
            return r if r is not None else True
        return True


class NextStepHandler:

    def __init__(self, handler, message):
        self.chat_id = message.chat.id
        self.handler = handler

    def __call__(self, update):
        if update.message is None:
            return

        if update.message.chat.id == self.chat_id:
            r = self.handler(update.message)
            return r if r is not None else False
        return False


class InlineHandler:

    def __init__(self, handler, func):
        self.handler = handler
        self.func = func

    def __call__(self, update):
        if update.inline_query is None:
            return

        if self.func(update.inline_query):
            r = self.handler(update.inline_query)
            return r if r is not None else True
        return True


class ChosenInlineResultHandler:

    def __init__(self, handler, func):
        self.handler = handler
        self.func = func

    def __call__(self, update):
        if update.chosen_inline_result is None:
            return

        if self.func(update.chosen_inline_result):
            r= self.handler(update.chosen_inline_result)
            return r if r is not None else True
        return True


class CallbackQueryHandler:

    def __init__(self, handler, func):
        self.handler = handler
        self.func = func

    def __call__(self, update):
        if update.callback_query is None:
            return

        if self.func(update.callback_query):
            r = self.handler(update.callback_query)
            return r if r is not None else True
        return True
