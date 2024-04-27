import telebot
from telebot import util
from telebot.types import ChatJoinRequest

bot = telebot.TeleBot("TOKEN")


@bot.chat_join_request_handler()
def make_some(message: ChatJoinRequest):
    bot.send_message(message.chat.id, "I accepted a new user!")
    bot.approve_chat_join_request(message.chat.id, message.from_user.id)


bot.infinity_polling(allowed_updates=util.update_types)
