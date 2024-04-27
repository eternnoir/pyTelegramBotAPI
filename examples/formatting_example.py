from telebot import TeleBot
from telebot.formatting import (
    format_text, munderline, mstrikethrough,
    mitalic, mbold, mcode, hcode, hide_link,
    hunderline, hitalic, hstrikethrough, hbold,
)

bot = TeleBot("TOKEN")


@bot.message_handler(commands=["start"])
def start_message(message):
    bot.send_message(
        message.chat.id,
        # function which connects all strings
        format_text(
            mbold(message.from_user.first_name),
            mitalic(message.from_user.first_name),
            munderline(message.from_user.first_name),
            mstrikethrough(message.from_user.first_name),
            mcode(message.from_user.first_name),
            separator=" ",  # separator separates all strings
        ),
        parse_mode="MarkdownV2",
    )

    # just a bold text using markdownv2
    bot.send_message(
        message.chat.id,
        mbold(message.from_user.first_name),
        parse_mode="MarkdownV2",
    )

    # html
    bot.send_message(
        message.chat.id,
        format_text(
            hbold(message.from_user.first_name),
            hitalic(message.from_user.first_name),
            hunderline(message.from_user.first_name),
            hstrikethrough(message.from_user.first_name),
            hcode(message.from_user.first_name),
            # hide_link is only for html
            hide_link("https://telegra.ph/file/c158e3a6e2a26a160b253.jpg"),
            separator=" ",
        ),
        parse_mode="HTML",
    )

    # just a bold text in html
    bot.send_message(
        message.chat.id,
        hbold(message.from_user.first_name),
        parse_mode="HTML",
    )


bot.infinity_polling()
