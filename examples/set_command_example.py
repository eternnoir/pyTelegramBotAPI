#!/usr/bin/python

# This is a set_my_commands example.
# Press on [/] button in telegram client.
# Important, to update the command menu, be sure to exit the chat with the bot and enter to chat again
# Important, command for chat_id and for group have a higher priority than for all

import telebot


API_TOKEN = '<api_token>'
bot = telebot.TeleBot(API_TOKEN)

# use in for delete with the necessary scope and language_code if necessary
bot.delete_my_commands(scope=None, language_code=None)

bot.set_my_commands(
    commands=[
        telebot.types.BotCommand("command1", "command1 description"),
        telebot.types.BotCommand("command2", "command2 description")
    ],
    # scope=telebot.types.BotCommandScopeChat(12345678)  # use for personal command for users
    # scope=telebot.types.BotCommandScopeAllPrivateChats()  # use for all private chats
)

# check command
cmd = bot.get_my_commands(scope=None, language_code=None)
print([c.to_json() for c in cmd])
