import telebot
from Ilkhom.utils.util import content_type_media
from telebot import types
from data import config

bot = telebot.TeleBot(token=config.BOT_TOKEN)


@bot.message_handler(content_types=content_type_media)
def bot_echo(message):
    chat_id = message.chat.id
    bot.copy_message(chat_id, chat_id, message.id)


bot.infinity_polling()