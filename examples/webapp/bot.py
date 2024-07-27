from telebot import TeleBot
from telebot.types import ReplyKeyboardMarkup, KeyboardButton, WebAppInfo

BOT_TOKEN = '<bot_token>' 
WEB_URL = 'https://pytelegrambotminiapp.vercel.app/' # https://github.com/eternnoir/pyTelegramBotAPI/blob/master/examples/webapp/webapp.html

bot = TeleBot(BOT_TOKEN)

@bot.message_handler(commands=["start"])
def start(message):
    reply_markup = ReplyKeyboardMarkup(resize_keyboard=True)
    reply_markup.row(KeyboardButton("Start MiniApp", web_app=WebAppInfo(WEB_URL)))
    bot.reply_to(message, "Click the button to start MiniApp", reply_markup=reply_markup)

@bot.message_handler(content_types=['web_app_data'])
def web_app(message):
    bot.reply_to(message, f'Your message is "{message.web_app_data.data}"')

bot.infinity_polling()
