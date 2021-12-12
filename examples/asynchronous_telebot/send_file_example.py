
import telebot
from telebot.async_telebot import AsyncTeleBot



bot = AsyncTeleBot('TOKEN')


@bot.message_handler(commands=['photo'])
async def photo_send(message: telebot.types.Message):
    with open('test.png', 'rb') as new_file:
        await bot.send_photo(message.chat.id, new_file)

@bot.message_handler(commands=['document'])
async def document_send(message: telebot.types.Message):
    with open('test.docx', 'rb') as new_file:
        await bot.send_document(message.chat.id, new_file)

@bot.message_handler(commands=['photos'])
async def photos_send(message: telebot.types.Message):
    with open('test.png', 'rb') as new_file, open('test2.png', 'rb') as new_file2:
        await bot.send_media_group(message.chat.id, [telebot.types.InputMediaPhoto(new_file), telebot.types.InputMediaPhoto(new_file2)])
    



import asyncio
asyncio.run(bot.polling())
