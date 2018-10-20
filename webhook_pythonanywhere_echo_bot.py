import flask
import telebot
import time

API_TOKEN = 'TELEGRAM_API_TOKEN'
secret = "USE A KEY GEN TO GET A NEW SECRET KEY"

WEBHOOK_URL = "https://yourname.pythonanywhere.com/" + secret

app = flask.Flask(__name__)

bot = telebot.TeleBot(API_TOKEN, threaded=False)

# Empty webserver index, return nothing, just http 200
@app.route('/', methods=['GET', 'HEAD'])
def index():
    return ''


# Process webhook calls
@app.route('/{}'.format(secret), methods=['POST'])
def webhook():
    if flask.request.headers.get('content-type') == 'application/json':
        json_string = flask.request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return ''
    else:
        flask.abort(403)


# Handle '/start'
@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "Hi there, {}! I am here to echo your kind words back to you.".format(message.from_user.first_name))


# Handle all other messages
@bot.message_handler(func=lambda message: True, content_types=['text'])
def echo_message(message):
    bot.reply_to(message, message.text)


# Remove webhook, it fails sometimes the set if there is a previous webhook
bot.remove_webhook()

time.sleep(0.1)


# Set webhook
bot.set_webhook(url=WEBHOOK_URL)
