import time

import telebot

bot = telebot.TeleBot("TOKEN")


@bot.message_handler(commands=['draft'])
def send_draft(message):
    if message.chat.type != 'private':
        bot.reply_to(message, "This example works in private chats.")
        return

    draft_id = message.from_user.id
    bot.send_message_draft(message.chat.id, draft_id, "Generating response...")
    time.sleep(1)
    bot.send_message_draft(message.chat.id, draft_id, "Still working...")
    time.sleep(1)
    bot.send_message(message.chat.id, "Done.")


bot.infinity_polling()
