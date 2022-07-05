import telebot
from time import sleep, time
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton #Only for creating Inline Buttons, not necessary for creating Invite Links

Token = "api_token" #Your Bot Access Token
Group_ID = -1234567890 #Group ID for which invite link is to be created

bot = telebot.TeleBot(Token, parse_mode="HTML")

#/start command message
@bot.message_handler(commands=['start'])
def startmsg(msg):
    bot.reply_to(msg, "Hey there, I'm a bot made by pyTelegramBotAPI!")

#Get notified of incoming members in group
@bot.message_handler(content_types=['new_chat_members'])
def newmember(msg):
    #Create an invite link class that contains info about the created invite link using create_chat_invite_link() with parameters
    invite = bot.create_chat_invite_link(Group_ID, member_limit=1, expire_date=int(time())+45) #Here, the link will auto-expire in 45 seconds
    InviteLink = invite.invite_link #Get the actual invite link from 'invite' class
    
    mrkplink = InlineKeyboardMarkup() #Created Inline Keyboard Markup
    mrkplink.add(InlineKeyboardButton("Join our group 🚀", url=InviteLink)) #Added Invite Link to Inline Keyboard
    
    bot.send_message(msg.chat.id, f"Hey there {msg.from_user.first_name}, Click the link below to join our Official Group.", reply_markup=mrkplink)
    
    #This will send a message with the newly-created invite link as markup button.
    #The member limit will be 1 and expiring time will be 45 sec.




bot.infinity_polling()
