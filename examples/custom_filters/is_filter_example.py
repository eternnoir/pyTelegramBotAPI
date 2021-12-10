import telebot
from telebot import custom_filters

bot = telebot.TeleBot('TOKEN')


# Check if message is a reply
@bot.message_handler(is_reply=True)
def start_filter(message):
    bot.send_message(message.chat.id, "Looks like you replied to my message.")

# Check if message was forwarded
@bot.message_handler(is_forwarded=True)
def text_filter(message):
    bot.send_message(message.chat.id, "I do not accept forwarded messages!")

# Do not forget to register filters
bot.add_custom_filter(custom_filters.IsReplyFilter())
bot.add_custom_filter(custom_filters.ForwardFilter())

bot.infinity_polling()
