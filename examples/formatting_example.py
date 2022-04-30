from telebot import TeleBot
from telebot import formatting

bot = TeleBot('TOKEN')


@bot.message_handler(commands=['start'])
def start_message(message):
    bot.send_message(
        message.chat.id,
        # function which connects all strings
        formatting.format_text(
            formatting.mbold(message.from_user.first_name, escape=True), # pass escape=True to escape special characters
            formatting.mitalic(message.from_user.first_name, escape=True),
            formatting.munderline(message.from_user.first_name, escape=True),
            formatting.mstrikethrough(message.from_user.first_name, escape=True),
            formatting.mcode(message.from_user.first_name, escape=True),
            separator=" " # separator separates all strings
        ),
        parse_mode='MarkdownV2'
    )

    # just a bold text using markdownv2
    bot.send_message(
        message.chat.id,
        formatting.mbold(message.from_user.first_name, escape=True),
        parse_mode='MarkdownV2'
    )

    # html
    bot.send_message(
        message.chat.id,
        formatting.format_text(
            formatting.hbold(message.from_user.first_name, escape=True),
            formatting.hitalic(message.from_user.first_name, escape=True),
            formatting.hunderline(message.from_user.first_name, escape=True),
            formatting.hstrikethrough(message.from_user.first_name, escape=True),
            formatting.hcode(message.from_user.first_name, escape=True),
            separator=" "
        ),
        parse_mode='HTML'
    )

    # just a bold text in html
    bot.send_message(
        message.chat.id,
        formatting.hbold(message.from_user.first_name, escape=True),
        parse_mode='HTML'
    )

bot.infinity_polling()