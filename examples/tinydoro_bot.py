import telebot
import time

# токен зарегистрированного у @BotFather нового бота
token = 'token'

# создаем бота
bot = telebot.TeleBot(token)

HELP = '''🍅Добро пожаловать в "TinyDoro_bot"!🍅
Техника «Помодоро» – это техника, предложенная Франческо Чирилло, которая использует таймер ⌚
для дробления задач на фиксированные временные интервалы, разделенные короткими перерывами.
Каждый интервал обычно длится 25 минут, и называется помидорка 🍅, а несколько интервалов – помидорками 🍅.

Команды бота:
/help, /start - показ справки бота.
/add 25 - установить таймер на 25 минут. Можно указать любое число.
/yes - после установки таймера, чтобы подтвердить что вы начали работу.
/yaw - после того, как рабочее время прошло, чтобы запустить 5 минутный таймер отдыха.

Автор: Alex Lestra 
https://github.com/lestrangeqq lestrangeqq@gmail.com
'''


# вывод справки бота
@bot.message_handler(commands=['help', 'start'])
def help(message):
    bot.send_message(message.chat.id, HELP)


# команда: установить таймер на 25 минут
@bot.message_handler(commands=['add'])
def setTimer(message):
    regime = 1
    command = message.text.split(maxsplit=1)
    workMin = command[1]
    bot.send_message(message.chat.id, '⌚ Таймер установлен на ' + workMin + ' минут.')
    workTimer(message, workMin, regime)


# процесс переключения режимов таймера с работы на отдых
def workTimer(message, workMin, regime):
    workSec = int(workMin)*60

    if regime == 0:
        bot.send_message(message.chat.id, '☕ Время отдохнуть! Введите /yaw чтобы начать.')

        @bot.message_handler(commands=['yaw'])
        def startRest(message):
            regime = 1
            bot.send_message(message.chat.id, 'Отдохните, у вас есть 5 минут!')
            timer(300, workMin, regime, message)
    elif regime == 1:
        bot.send_message(message.chat.id, '🔧 Время поработать! Введите /yes чтобы начать.')

        @bot.message_handler(commands=['yes'])
        def startWork(message):
            regime = 0
            bot.send_message(message.chat.id, 'Время пошло, приступите к работе! Полная концентрация!')
            timer(workSec, workMin, regime, message)


# функция работы таймера
def timer(workSec, workMin, regime, message):
    while workSec > 0:
        time.sleep(1)
        workSec -= 1
    workTimer(message, workMin, regime)


@bot.message_handler(commands=['stop'])
def stop(message):
    bot.send_message(message.chat.id, 'Таймер должен быть остановлен.')


# цикл запросов на сервер телеграм, чтобы бот
# проверял отправили ли ему сообщение
bot.polling(none_stop=True)
