import telebot
from telebot import types,util

bot = telebot.TeleBot("token")

#chat_member_handler. When status changes, telegram gives update. check status from old_chat_member and new_chat_member.
@bot.chat_member_handler()
def chat_m(message: types.ChatMemberUpdated):
    old = message.old_chat_member
    new = message.new_chat_member
    if new.status == "member":
        bot.send_message(message.chat.id,"Hello {name}!".format(name=new.user.first_name)) # Welcome message

#if bot is added to group, this handler will work
@bot.my_chat_member_handler()
def my_chat_m(message: types.ChatMemberUpdated):
    old = message.old_chat_member
    new = message.new_chat_member
    if new.status == "member":
        bot.send_message(message.chat.id,"Somebody added me to group") # Welcome message, if bot was added to group
        bot.leave_chat(message.chat.id)

#content_Type_service is:
#'new_chat_members', 'left_chat_member', 'new_chat_title', 'new_chat_photo', 'delete_chat_photo', 'group_chat_created',
#'supergroup_chat_created', 'channel_chat_created', 'migrate_to_chat_id', 'migrate_from_chat_id', 'pinned_message',
#'proximity_alert_triggered', 'voice_chat_scheduled', 'voice_chat_started', 'voice_chat_ended', 
#'voice_chat_participants_invited', 'message_auto_delete_timer_changed'
# this handler deletes service messages

@bot.message_handler(content_types=util.content_type_service)
def delall(message: types.Message):
    bot.delete_message(message.chat.id,message.message_id)
bot.polling(allowed_updates=util.update_types)