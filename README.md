# pyTelegramBotAPI

A Python implementation for the Telegram Bot API.

See [https://core.telegram.org/bots/api](https://core.telegram.org/bots/api)

[![Build Status](https://travis-ci.org/eternnoir/pyTelegramBotAPI.svg?branch=master)](https://travis-ci.org/eternnoir/pyTelegramBotAPI)

## How to install

Python 2 or Python 3 is required.

* Install from source

```
$ git clone https://github.com/eternnoir/pyTelegramBotAPI.git
$ cd pyTelegramBotAPI
$ python setup.py install
```

* or install with pip

```
$ pip install pyTelegramBotAPI
```

## Example

* Sending a message.

```python
import telebot

TOKEN = '<token string>'

tb = telebot.TeleBot(TOKEN)
# tb.send_message(chatid, message)
tb.send_message(281281, 'gogo power ranger')
```

* Echo Bot

```python
import telebot
import time

TOKEN = '<token_string>'


def listener(messages):
    """
    When new messages arrive TeleBot will call this function.
    """
    for m in messages:
        chatid = m.chat.id
        if m.content_type == 'text':
            text = m.text
            tb.send_message(chatid, text)


tb = telebot.TeleBot(TOKEN)
tb.set_update_listener(listener) #register listener
tb.polling()
#Use none_stop flag let polling will not stop when get new message occur error.
tb.polling(none_stop=True)
# Interval setup. Sleep 3 secs between request new message.
tb.polling(interval=3)

while True: # Don't let the main Thread end.
    pass
```

## TeleBot API usage

```python
import telebot
import time

TOKEN = '<token_string>'
tb = telebot.TeleBot(TOKEN)	#create a new Telegram Bot object

# TeleBot will not create thread for message listener. Default is True.
tb = telebot.TeleBot(TOKEN, False)

# 4 Thread worker for message listener.
tb = telebot.TeleBot(TOKEN, True, 4)

# Setup telebot handler to telebot logger. If you want to get some information from telebot.
# More information at Logging section
handler = logging.StreamHandler(sys.stdout)
telebot.logger.addHandler(handler)
telebot.logger.setLevel(logging.INFO)

# getMe
user = tb.get_me()

# sendMessage
tb.send_message(chatid, text)

# forwardMessage
# tb.forward_message(10894,926,3)
tb.forward_message(to_chat_id, from_chat_id, message_id)

# sendPhoto
photo = open('/tmp/photo.png', 'rb')
tb.send_photo(chat_id, photo)
file_id = 'AAAaaaZZZzzz'
tb.send_photo(chat_id, file_id)

# sendAudio
audio = open('/tmp/audio.ogg', 'rb')
tb.send_audio(chat_id, audio)
file_id = 'AAAaaaZZZzzz'
tb.send_audio(chat_id, file_id)

# sendDocument
doc = open('/tmp/file.txt', 'rb')
tb.send_document(chat_id, doc)
file_id = 'AAAaaaZZZzzz'
tb.send_document(chat_id, file_id)

# sendSticker
sti = open('/tmp/sti.webp', 'rb')
tb.send_sticker(chat_id, sti)
file_id = 'AAAaaaZZZzzz'
tb.send_sticker(chat_id, file_id)

# sendVideo
video = open('/tmp/video.mp4', 'rb')
tb.send_video(chat_id, video)
file_id = 'AAAaaaZZZzzz'
tb.send_video(chat_id, file_id)

# sendLocation
tb.send_location(chat_id, lat, lon)

# sendChatAction
# action_string can be one of the following strings: 'typing', 'upload_photo', 'record_video', 'upload_video',
# 'record_audio', 'upload_audio', 'upload_document' or 'find_location'.
tb.send_chat_action(chat_id, action_string)

# Use the ReplyKeyboardMarkup class.
# Thanks pevdh.
from telebot import types

markup = types.ReplyKeyboardMarkup()
markup.add('a', 'v', 'd')
tb.send_message(chat_id, message, reply_markup=markup)

# or add strings one row at a time:
markup = types.ReplyKeyboardMarkup()
markup.row('a', 'v')
markup.row('c', 'd', 'e')
tb.send_message(chat_id, message, reply_markup=markup)

```

## Creating a Telegram bot with the pyTelegramBotAPI
There are two ways to define a Telegram Bot with the pyTelegramBotAPI.
### The listener mechanism
* First, create a TeleBot instance.
```python
import telebot

TOKEN = '<token string>'

bot = telebot.TeleBot(TOKEN)
```
* Then, define a listener function.
```python
def echo_messages(*messages):
	"""
	Echoes all incoming messages of content_type 'text'.
	"""
    for m in messages:
        chatid = m.chat.id
        if m.content_type == 'text':
            text = m.text
            bot.send_message(chatid, text)
```
* Now, register your listener with the TeleBot instance and call TeleBot#polling()
```python
bot.set_update_listener(echo_messages)
bot.polling()

while True: # Don't let the main Thread end.
    pass
```
* use Message's content_type attribute to check the type of Message. Now Message supports content types:
  * text
  * audio
  * document
  * photo
  * sticker
  * video
  * location
  * contact
  * new_chat_participant
  * left_chat_participant
  * new_chat_title
  * new_chat_photo
  * delete_chat_photo
  * group_chat_created
* That's it!

### The decorator mechanism
* First, create a TeleBot instance.
```python
import telebot

TOKEN = '<token string>'

bot = telebot.TeleBot(TOKEN)
```
* Next, define all of your so-called message handlers and decorate them with @bot.message_handler
```python
# Handle /start and /help
@bot.message_handler(commands=['start', 'help'])
def command_help(message):
    bot.reply_to(message, "Hello, did someone call for help?")
    
# Handles all messages which text matches the regex regexp.
# See https://en.wikipedia.org/wiki/Regular_expression
# This regex matches all sent url's.
@bot.message_handler(regexp='((https?):((//)|(\\\\))+([\w\d:#@%/;$()~_?\+-=\\\.&](#!)?)*)')
def command_url(message):
    bot.reply_to(message, "I shouldn't open that url, should I?")

# Handle all sent documents of type 'text/plain'.
@bot.message_handler(func=lambda message: message.document.mime_type == 'text/plain', content_types=['document'])
def command_handle_document(message):
    bot.reply_to(message, "Document received, sir!")

# Default command handler. A lambda expression which always returns True is used for this purpose.
@bot.message_handler(func=lambda message: True, content_types=['audio', 'video', 'document', 'text', 'location', 'contact', 'sticker'])
def default_command(message):
    bot.reply_to(message, "This is the default command handler.")
```
* And finally, call bot.polling()
```python
bot.polling()

while True: # Don't end the main thread.
    pass
```
Use whichever mechanism fits your purpose! It is even possible to mix and match.

## Logging

Now you can use Telebot module logger to log some information in Telebot. Use `telebot.logger` to get
Telebot module logger.

```python
logger = telebot.logger
formatter = logging.Formatter('[%(asctime)s] %(thread)d {%(pathname)s:%(lineno)d} %(levelname)s - %(message)s',
                                  '%m-%d %H:%M:%S')
ch = logging.StreamHandler(sys.stdout)
logger.addHandler(ch)
logger.setLevel(logging.DEBUG)  # or use logging.INFO
ch.setFormatter(formatter)
```

## Telegram Chat Group

Get help. Discuss. Chat.

Join [pyTelegramBotAPI Chat Group](https://telegram.me/joinchat/067e22c60035523fda8f6025ee87e30b).

## Examples

* [Echo Bot](https://github.com/eternnoir/pyTelegramBotAPI/blob/master/examples/echo_bot.py)
* [Deep Linking](https://github.com/eternnoir/pyTelegramBotAPI/blob/master/examples/deep_linking.py)
* [next_step_handler Example](https://github.com/eternnoir/pyTelegramBotAPI/blob/master/examples/step_example.py)

