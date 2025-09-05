import telebot

# Sizning bot tokeningiz (BotFather bergan)
TOKEN = "8374542380:AAEkoBDJR-HATPYvrOUmgDTTzo_a2-bYjJM"

# Sizning Telegram ID raqamingiz (admin)
ADMIN_ID = 1114871353  

bot = telebot.TeleBot(TOKEN)

# Odam yozsa -> sizga yuboradi
@bot.message_handler(func=lambda message: True)
def forward_to_admin(message):
    if message.chat.id != ADMIN_ID:  # Agar bu siz bo'lmasangiz
        bot.forward_message(ADMIN_ID, message.chat.id, message.message_id)
        bot.send_message(message.chat.id, "✅ Xabaringiz yuborildi.")

# Siz (admin) javob yozsangiz -> odamga yuboradi
@bot.message_handler(func=lambda message: message.chat.id == ADMIN_ID, content_types=['text'])
def reply_to_user(message):
    if message.reply_to_message:  # Reply qilgan bo'lsangiz
        forwarded_msg = message.reply_to_message
        if forwarded_msg.forward_from:
            bot.send_message(forwarded_msg.forward_from.id, message.text)

# Botni doimiy ishlatish
print("🤖 Bot ishga tushdi...")
bot.polling(none_stop=True)
