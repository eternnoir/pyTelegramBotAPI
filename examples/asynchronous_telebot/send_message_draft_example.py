import asyncio

from telebot.async_telebot import AsyncTeleBot

bot = AsyncTeleBot("TOKEN")


@bot.message_handler(commands=['draft'])
async def send_draft(message):
    if message.chat.type != 'private':
        await bot.reply_to(message, "This example works in private chats.")
        return

    draft_id = message.from_user.id
    await bot.send_message_draft(message.chat.id, draft_id, "Generating response...")
    await asyncio.sleep(1)
    await bot.send_message_draft(message.chat.id, draft_id, "Still working...")
    await asyncio.sleep(1)
    await bot.send_message(message.chat.id, "Done.")


asyncio.run(bot.polling())
