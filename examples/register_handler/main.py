import telebot
from telebot import custom_filters
import config
bot = telebot.TeleBot(config.api_token)

import handlers

bot.register_message_handler(handlers.start_executor, commands=['start']) # Start command executor

# See also
# bot.register_callback_query_handler(*args, **kwargs)
# bot.register_channel_post_handler(*args, **kwargs)
# bot.register_chat_member_handler(*args, **kwargs)
# bot.register_inline_handler(*args, **kwargs)
# bot.register_my_chat_member_handler(*args, **kwargs)
# bot.register_edited_message_handler(*args, **kwargs)
# And other functions..

bot.polling()