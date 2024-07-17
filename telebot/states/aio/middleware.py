from telebot.asyncio_handler_backends import BaseMiddleware
from telebot.async_telebot import AsyncTeleBot
from telebot.states.sync.context import StateContext
from telebot.util import update_types
from telebot import types


class StateMiddleware(BaseMiddleware):

    def __init__(self, bot: AsyncTeleBot) -> None:
        self.update_sensitive = False
        self.update_types = update_types
        self.bot: AsyncTeleBot = bot

    async def pre_process(self, message, data):
        data['state_context'] = StateContext(message, self.bot)

    async def post_process(self, message, data, exception):
        pass
