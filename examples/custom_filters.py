import telebot
from telebot import util

bot = telebot.TeleBot('TOKEN')


# AdvancedCustomFilter is for list, string filter values
class MainFilter(util.AdvancedCustomFilter):
    key='text'
    @staticmethod
    def check(message, text):
        return message.text in text

# SimpleCustomFilter is for boolean values, such as is_admin=True
class IsAdmin(util.SimpleCustomFilter):
    key='is_admin'
    @staticmethod
    def check(message: telebot.types.Message):
        if bot.get_chat_member(message.chat.id,message.from_user.id).status in ['administrator','creator']:
            return True
        else:
            return False


@bot.message_handler(is_admin=True, commands=['admin']) # Check if user is admin
def admin_rep(message):
    bot.send_message(message.chat.id, "Hi admin")

@bot.message_handler(is_admin=False, commands=['admin']) # If user is not admin
def not_admin(message):
    bot.send_message(message.chat.id, "You are not admin")

@bot.message_handler(text=['hi']) # Response to hi message
def welcome_hi(message):
    bot.send_message(message.chat.id, 'You said hi')

@bot.message_handler(text=['bye']) # Response to bye message
def bye_user(message):
    bot.send_message(message.chat.id, 'You said bye')


# Do not forget to register filters
bot.add_custom_filter(MainFilter)
bot.add_custom_filter(IsAdmin)

bot.polling(skip_pending=True,non_stop=True) # Skip old updates