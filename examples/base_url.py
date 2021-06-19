import telebot
bot = telebot.TeleBot("token",base_url="http://localhost:8081") #change your base_url. If you want to make request to api.telegram.org, leave it.

@bot.message_handler(commands=['start'])
def welcome(message):
    bot.send_message(message.chat.id,"Hello world")
bot.polling()