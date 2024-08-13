# The source of the "https://pytelegrambotminiapp.vercel.app" can be found in https://github.com/eternnoir/pyTelegramBotAPI/tree/master/examples/mini_app_web

import asyncio
from telebot.async_telebot import AsyncTeleBot 
from telebot.types import (
    ReplyKeyboardMarkup, 
    KeyboardButton, 
    WebAppInfo,
    InlineKeyboardMarkup,
    InlineKeyboardButton
)

BOT_TOKEN = "" 
WEB_URL = "https://pytelegrambotminiapp.vercel.app"

bot = AsyncTeleBot(BOT_TOKEN)

@bot.message_handler(commands=["start"])
async def start(message):
    reply_keyboard_markup = ReplyKeyboardMarkup(resize_keyboard=True)
    reply_keyboard_markup.row(KeyboardButton("Start MiniApp", web_app=WebAppInfo(WEB_URL)))

    inline_keyboard_markup = InlineKeyboardMarkup()
    inline_keyboard_markup.row(InlineKeyboardButton('Start MiniApp', web_app=WebAppInfo(WEB_URL)))

    await bot.reply_to(message, "Click the bottom inline button to start MiniApp", reply_markup=inline_keyboard_markup)
    await bot.reply_to(message, "Click keyboard button to start MiniApp", reply_markup=reply_keyboard_markup)

@bot.message_handler(content_types=['web_app_data'])
async def web_app(message):
    await bot.reply_to(message, f'Your message is "{message.web_app_data.data}"')

asyncio.run(bot.polling())
