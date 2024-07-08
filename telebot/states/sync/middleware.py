from telebot.handler_backends import BaseMiddleware
from telebot import TeleBot
from telebot.states.sync.context import StateContext


class StateMiddleware(BaseMiddleware):

    def __init__(self, bot: TeleBot) -> None:
        self.update_sensitive = False
        self.update_types = ['message', 'edited_message', 'callback_query'] #TODO: support other types
        self.bot: TeleBot = bot

    def pre_process(self, message, data):
        data['state_context'] = StateContext(message, self.bot)

    def post_process(self, message, data, exception):
        pass