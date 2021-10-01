import telebot

from telebot import custom_filters

bot = telebot.TeleBot("")



@bot.message_handler(commands=['start'])
def start_ex(message):
    bot.set_state(message.chat.id, 1)
    bot.send_message(message.chat.id, 'Hi, write me a name')
 

 
@bot.message_handler(state="*", commands='cancel')
def any_state(message):
    bot.send_message(message.chat.id, "Your state was cancelled.")
    bot.delete_state(message.chat.id)

@bot.message_handler(state=1)
def name_get(message):
    bot.send_message(message.chat.id, f'Now write me a surname')
    bot.set_state(message.chat.id, 2)
    with bot.retrieve_data(message.chat.id) as data:
        data['name'] = message.text
 
 
@bot.message_handler(state=2)
def ask_age(message):
    bot.send_message(message.chat.id, "What is your age?")
    bot.set_state(message.chat.id, 3)
    with bot.retrieve_data(message.chat.id) as data:
        data['surname'] = message.text
 
@bot.message_handler(state=3, is_digit=True)
def ready_for_answer(message):
    with bot.retrieve_data(message.chat.id) as data:
        bot.send_message(message.chat.id, "Ready, take a look:\n<b>Name: {name}\nSurname: {surname}\nAge: {age}</b>".format(name=data['name'], surname=data['surname'], age=message.text), parse_mode="html")
    bot.delete_state(message.chat.id)

@bot.message_handler(state=3, is_digit=False)
def age_incorrect(message):
    bot.send_message(message.chat.id, 'Looks like you are submitting a string in the field age. Please enter a number')

bot.add_custom_filter(custom_filters.StateFilter(bot))
bot.add_custom_filter(custom_filters.IsDigitFilter())
bot.infinity_polling(skip_pending=True)