import telebot
from telebot import types
import time

TOKEN = '<token_string>'

knownUsers = []
userStep = {}
commands={ #command description used in the "help" command
'start': 'Get used to the bot', 
'help': 'Gives you information about the available commands', 
'sendLongText': 'A test using the \'send_chat_action\' command',
'getImage': 'A test using multi-stage messages, custom keyboard, and media sending'
}

imageSelect = types.ReplyKeyboardMarkup(one_time_keyboard=True) #create the image selection keyboard
imageSelect.add('cock', 'pussy')

hideBoard = types.ReplyKeyboardHide()	#if sent as reply_markup, will hide the keyboard

def printUser(msg): #debug function (will print every message sent by any user to the console)
	print str(msg.chat.first_name) + " [" + str(msg.chat.id) + "]: " + msg.text

def listener(messages):
	"""
	When new messages arrive TeleBot will call this function.
	"""
	for m in messages:
		cid = m.chat.id
		if m.content_type == 'text':
			text = m.text
			printUser(m) #print the sent message to the console
			
			if text[0] != '/': #filter out commands
				try: #don't quit, when the user hasn't used the "/start" command yet
					if userStep[cid]==1: #when the user has issued the "/getImage" command
						bot.send_chat_action(cid, 'typing') #for some reason the 'upload_photo' status isn't quite working (doesn't show at all)
						if text == "cock":                                  #send the appropriate image based on the reply to the "/getImage" command
							bot.send_photo(cid, open('rooster.jpg', 'rb'), reply_markup=hideBoard) #send file and hide keyboard, after image is sent
							userStep[cid]=0   #reset the users step back to 0
						elif text == "pussy":
							bot.send_photo(cid, open('kitten.jpg', 'rb'), reply_markup=hideBoard)
							userStep[cid]=0
						else:
							bot.send_message(cid, "Don't type bullsh*t, if I give you a predefined keyboard!")
							bot.send_message(cid, "Please try again")
					else:
						bot.send_message(cid, "I don't understand \""+text+"\"\nMaybe try the help page at /help") #this is the standard reply to a normal message

				except KeyError:
					bot.send_message(cid, "I don't know you yet... Please use the \'/start\' command!")
			


bot = telebot.TeleBot(TOKEN)
bot.set_update_listener(listener) #register listener
try:
	bot.polling()
except Exception:
	pass

@bot.message_handler(commands=['start'])
def command_start(m):
	cid = m.chat.id
	if not cid in knownUsers: #if user hasn't used the "/start" command yet:
		knownUsers.append(cid)  #save user id, so you could brodcast messages to all users of this bot later
		userStep[cid] = 0       #save user id and his current "command level", so he can use the "/getImage" command
		bot.send_message(cid, "Hello, stranger, let me scan you...")
		bot.send_message(cid, "Scanning complete, I know you now")
		command_help(m)         #show the new user the help page
	else:
		bot.send_message(cid, "I already know you, no need for me to scan you again!")
		

@bot.message_handler(commands=['help']) #help page
def command_help(m):
	cid = m.chat.id
	helpText = "The following commands are available: \n"
	for key in commands:                  #generate help text out of the commands dictionary defined at the top
		helpText += "/" + key + ": "
		helpText += commands[key] + "\n"
	bot.send_message(cid, helpText)       #send the generated help page
	
@bot.message_handler(commands=['sendLongText'])  #chat_action example (not a good one... sleep is bad, if this bot is used by multiple users)
def command_longText(m):
	cid = m.chat.id
	bot.send_message(cid, "If you think so...")
	bot.send_chat_action(cid, 'typing')            #show the bot "typing" (max. 5 secs)
	time.sleep(3)
	bot.send_message(cid,".")

@bot.message_handler(commands=['getImage']) #user can chose an image
def command_image(m):
	cid = m.chat.id
	bot.send_message(cid, "Please choose your image now", reply_markup=imageSelect) #show the keyboard
	userStep[cid] = 1 #set the user to the next step (expecting a reply in the listener now)

while True: # Don't let the main Thread end.
	try:
		pass
	except KeyboardInterrupt:
		break