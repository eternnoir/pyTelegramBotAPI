# Just a little example of middleware handlers

from telebot.handler_backends import BaseMiddleware
from telebot import TeleBot
from telebot.handler_backends import CancelUpdate
bot = TeleBot('TOKEN',
            use_class_middlewares=True) # if you don't set it to true, middlewares won't work


class SimpleMiddleware(BaseMiddleware):
    def __init__(self, limit) -> None:
        self.last_time = {}
        self.limit = limit
        self.update_types = ['message']
        # Always specify update types, otherwise middlewares won't work


    def pre_process(self, message, data):
        if not message.from_user.id in self.last_time:
            # User is not in a dict, so lets add and cancel this function
            self.last_time[message.from_user.id] = message.date
            return
        if message.date - self.last_time[message.from_user.id] < self.limit:
            # User is flooding
            bot.send_message(message.chat.id, 'You are making request too often')
            return CancelUpdate()
        self.last_time[message.from_user.id] = message.date

        
    def post_process(self, message, data, exception):
        pass

bot.setup_middleware(SimpleMiddleware(2))

@bot.message_handler(commands=['start'])
def start(message): # you don't have to put data in handler.
    bot.send_message(message.chat.id, 'Hello!')

bot.infinity_polling()
