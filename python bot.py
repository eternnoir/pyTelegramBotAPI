import telebot

# اپنا ٹوکن یہاں ڈالیں
TOKEN = '7499765310:AAHn3q-_5gEy5knjxwhSS4m9V2hCMB8YB64'
bot = telebot.TeleBot(TOKEN)

# /start 
@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "Welcome")


@bot.message_handler(func=lambda message: True)
def echo_all(message):
    bot.reply_to(message, message.text)


bot.polling()
