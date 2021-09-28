import telebot
from telebot import custom_filters
bot = telebot.TeleBot('TOKEN')

# Handler
@bot.message_handler(chat_types=['supergroup'], is_chat_admin=True)
def answer_for_admin(message):
    bot.send_message(message.chat.id,"hello my admin")

# Register filter
bot.add_custom_filter(custom_filters.IsAdminFilter(bot))
bot.infinity_polling()
