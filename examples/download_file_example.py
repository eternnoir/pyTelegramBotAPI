import telebot

TOKEN = 'YOUR BOT TOKEN'
CHAT_ID = 'YOUR CHAT ID'

bot = telebot.TeleBot(TOKEN)

ret_msg = bot.send_voice(CHAT_ID, open('tests/test_data/record.ogg', 'rb'))

file_info = bot.get_file(ret_msg.voice.file_id)

downloaded_file = bot.download_file(file_info.file_path)

with open('new_file.ogg', 'wb') as new_file:
    new_file.write(downloaded_file)
