import telebot

from telebot.handler_backends import State

bot = telebot.TeleBot("")

@bot.message_handler(commands=['start'])
def start_ex(message):
    bot.set_state(message.chat.id, 1)
    bot.send_message(message.chat.id, 'Hi, write me a name')
 
 
@bot.state_handler(state=1)
def name_get(message, state:State):
    bot.send_message(message.chat.id, f'Now write me a surname')
    state.set(message.chat.id, 2)
    with state.retrieve_data(message.chat.id) as data:
        data['name'] = message.text
 
 
@bot.state_handler(state=2)
def ask_age(message, state:State):
    bot.send_message(message.chat.id, "What is your age?")
    state.set(message.chat.id, 3)
    with state.retrieve_data(message.chat.id) as data:
        data['surname'] = message.text
 
@bot.state_handler(state=3)
def ready_for_answer(message, state: State):
    with state.retrieve_data(message.chat.id) as data:
        bot.send_message(message.chat.id, "Ready, take a look:\n<b>Name: {name}\nSurname: {surname}\nAge: {age}</b>".format(name=data['name'], surname=data['surname'], age=message.text), parse_mode="html")
    state.finish(message.chat.id)

bot.polling()