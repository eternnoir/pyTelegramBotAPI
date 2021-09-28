import telebot
from telebot import custom_filters

bot = telebot.TeleBot('TOKEN')


# Check if message starts with @admin tag
@bot.message_handler(text_startswith="@admin")
def start_filter(message):
    bot.send_message(message.chat.id, "Looks like you are calling admin, wait...")

# Check if text is hi or hello
@bot.message_handler(text=['hi','hello'])
def text_filter(message):
    bot.send_message(message.chat.id, "Hi, {name}!".format(name=message.from_user.first_name))

# Do not forget to register filters
bot.add_custom_filter(custom_filters.TextMatchFilter())
bot.add_custom_filter(custom_filters.TextStartsFilter())

bot.infinity_polling()
