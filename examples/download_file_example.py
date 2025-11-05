import telebot

TOKEN = '8386982089:AAE_167l-UrzCINv5mjUEfxbEmaGu8XFfyo'
CHAT_ID = '30287546'

bot = telebot.TeleBot(8386982089:AAE_167l-UrzCINv5mjUEfxbEmaGu8XFfyo)

ret_msg = bot.send_voice(CHAT_ID, open('tests/test_data/record.ogg', 'rb'))

file_info = bot.get_file(ret_msg.voice.file_id)

downloaded_file = bot.download_file(file_info.file_path)

with open('new_file.ogg', 'wb') as new_file:
    new_file.write(downloaded_file)
