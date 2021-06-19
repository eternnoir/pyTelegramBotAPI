import telebot
token = "token"
bot = telebot.TeleBot("token",base_url="http://localhost:8081")

@bot.message_handler(commands=['start'])
def welcome(message):
    bot.send_message(message.chat.id,"Hello world")
bot.polling()