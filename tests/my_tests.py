import os
from telebot import logger, logging, types, TeleBot

try:
    TOKEN = os.environ['TOKEN']
except:
    logger.error('Not variable \'TOKEN\' in environ')
    exit(1)

CHAT_ID = -1001405019571
logger.setLevel(logging.DEBUG)

bot = TeleBot(TOKEN)


@bot.message_handler(content_types=['poll'])
def po(m):
    logger.debug('Give poll')
    bot.send_message(m.chat.id, 'Я тоже так умею!')
    m = bot.send_poll(m.chat.id, m.poll)
    print(m.chat.id, m.message_id)


def test_send_poll():
    poll = types.Poll('Какой ты сегодня?')
    poll.add('Добрый')
    poll.add('Веселый')
    poll.add('Грустный')
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton('1', url='t.me/dr_forse'))
    result = bot.send_poll(CHAT_ID, poll, reply_to_message=60312, reply_markup=kb)
    assert result['poll']['question'] == 'Какой ты сегодня?'


def test_stop_poll():
    res = bot.stop_poll(-1001405019571, 60370)


test_stop_poll()
bot.polling(none_stop=True, timeout=600)
