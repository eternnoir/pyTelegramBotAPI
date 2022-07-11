from telebot import TeleBot
from telebot import formatting

bot = TeleBot('TOKEN')


@bot.message_handler(commands=['start'])
def start_message(message):
    bot.send_message(
        message.chat.id,
        # function which connects all strings
        formatting.format_text(
            formatting.mbold(message.from_user.first_name),
            formatting.mitalic(message.from_user.first_name),
            formatting.munderline(message.from_user.first_name),
            formatting.mstrikethrough(message.from_user.first_name),
            formatting.mcode(message.from_user.first_name),
            separator=" " # separator separates all strings
        ),
        parse_mode='MarkdownV2'
    )

    # just a bold text using markdownv2
    bot.send_message(
        message.chat.id,
        formatting.mbold(message.from_user.first_name),
        parse_mode='MarkdownV2'
    )

    # html
    bot.send_message(
        message.chat.id,
        formatting.format_text(
            formatting.hbold(message.from_user.first_name),
            formatting.hitalic(message.from_user.first_name),
            formatting.hunderline(message.from_user.first_name),
            formatting.hstrikethrough(message.from_user.first_name),
            formatting.hcode(message.from_user.first_name),
            # hide_link is only for html
            formatting.hide_link('https://telegra.ph/file/c158e3a6e2a26a160b253.jpg'),
            separator=" "
        ),
        parse_mode='HTML'
    )

    # just a bold text in html
    bot.send_message(
        message.chat.id,
        formatting.hbold(message.from_user.first_name),
        parse_mode='HTML'
    )

bot.infinity_polling()