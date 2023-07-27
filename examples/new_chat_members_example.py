from telebot.async_telebot import AsyncTeleBot
from asyncio import run

bot = AsyncTeleBot('YOUR TOKEN')
YOUR_CHAT_ID = 'your chat id' # capture the CHAT_ID of your private chat and put it here

@bot.message_handler(content_types=['new_chat_members']) # manages all new member events for all groups
async def Welcome(message):
    try:
        new_member = message.json['new_chat_member']['first_name'] # 'new_member' takes the first name from the dictionary in
        name_group = message.json['chat']['title'] # 'name_group' take the name of the group and send it along with the welcome message
        await bot.send_message(
            message.chat.id, f'Welcome to Hubber, @{new_member}🤖 you have been added to the group: *{name_group}*', parse_mode='Markdown') # welcome message
    except Exception as err:
        await bot.send_message(YOUR_CHAT_ID, text=err) # if it falls into an exception, the bot sends the error to your private without breaking the code
        
run(bot.polling(non_stop=True))