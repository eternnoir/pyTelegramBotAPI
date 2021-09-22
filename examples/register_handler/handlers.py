# All handlers can be written in this file
from config import bot

def start_executor(message):
    bot.send_message(message.chat.id, 'Hello!')

# Write more handlers here if you wish. You don't need a decorator

# Just create function and register in main file.