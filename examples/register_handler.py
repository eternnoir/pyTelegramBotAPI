import telebot

api_token = 'token'

bot = telebot.TeleBot(api_token)

def start_executor(message):
    bot.send_message(message.chat.id, 'Hello!')

bot.register_message_handler(start_executor, commands=['start']) # Start command executor

# See also
# bot.register_callback_query_handler(*args, **kwargs)
# bot.register_channel_post_handler(*args, **kwargs)
# bot.register_chat_member_handler(*args, **kwargs)
# bot.register_inline_handler(*args, **kwargs)
# bot.register_my_chat_member_handler(*args, **kwargs)
# bot.register_edited_message_handler(*args, **kwargs)
# And other functions..

bot.infinity_polling()
