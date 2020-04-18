import telebot
bot = telebot.TeleBot("TOKEN")

@bot.message_handler(commands = ['test'])
def poll_test(message):
    poll = telebot.types.Poll('test')
    poll.add('1')
    poll.add('2')
    poll.add('3')
    # correct_option_id must use 0-based identifier, so the right answer is '2'.
    bot.send_poll(message.chat.id, poll, is_anonymous = False, allows_multiple_answers = True, poll_type = 'quiz', correct_option_id = 1)

bot.polling()