import asyncio

from telebot.async_telebot import AsyncTeleBot
from telebot.formatting import (
    hbold, hide_link, hcode,
    hstrikethrough, hunderline, hitalic,
    format_text, mbold, munderline,
    mitalic, mstrikethrough, mcode
)

bot = AsyncTeleBot("TOKEN")


@bot.message_handler(commands=["start"])
async def start_message(message):
    await bot.send_message(
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
    await bot.send_message(
        message.chat.id,
        mbold(message.from_user.first_name),
        parse_mode="MarkdownV2",
    )

    # html
    await bot.send_message(
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
    await bot.send_message(
        message.chat.id,
        hbold(message.from_user.first_name),
        parse_mode="HTML",
    )

asyncio.run(bot.polling())
