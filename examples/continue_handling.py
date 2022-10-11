from telebot import TeleBot
from telebot.handler_backends import ContinueHandling


bot = TeleBot('TOKEN')

@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id, 'Hello World!')
    return ContinueHandling()

@bot.message_handler(commands=['start'])
def start2(message):
    """
    This handler comes after the first one, but it will never be called.
    But you can call it by returning ContinueHandling() in the first handler.

    If you return ContinueHandling() in the first handler, the next 
    registered handler with appropriate filters will be called.
    """
    bot.send_message(message.chat.id, 'Hello World2!')

bot.infinity_polling()
