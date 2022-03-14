from telebot import TeleBot
from telebot.handler_backends import BaseMiddleware

bot = TeleBot('TOKEN', use_class_middlewares=True) # set use_class_middlewares to True!
# otherwise, class-based middlewares won't execute.

# You can use this classes for cancelling update or skipping handler:
# from telebot.handler_backends import CancelUpdate, SkipHandler

class Middleware(BaseMiddleware):
    def __init__(self):
        self.update_types = ['message']
    def pre_process(self, message, data):
        data['foo'] = 'Hello' # just for example
        # we edited the data. now, this data is passed to handler.
        # return SkipHandler() -> this will skip handler
        # return CancelUpdate() -> this will cancel update
    def post_process(self, message, data, exception=None):
        print(data['foo'])
        if exception: # check for exception
            print(exception)

@bot.message_handler(commands=['start'])
def start(message, data: dict): # you don't have to put data parameter in handler if you don't need it.
    bot.send_message(message.chat.id, data['foo'])
    data['foo'] = 'Processed' # we changed value of data.. this data is now passed to post_process.


# Setup middleware
bot.setup_middleware(Middleware())

bot.infinity_polling()
