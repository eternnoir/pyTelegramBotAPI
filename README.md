#<center>pyTelegramBotAPI</center>

<center>A simple, but extensible Python implementation for the [Telegram Bot API](https://core.telegram.org/bots/api).</center>


<center>[![Build Status](https://travis-ci.org/eternnoir/pyTelegramBotAPI.svg?branch=master)](https://travis-ci.org/eternnoir/pyTelegramBotAPI)</center>

  * [Getting started.](#getting-started)
  * [Writing your first bot](#writing-your-first-bot)
    * [Prerequisites](#prerequisites)
    * [A simple echo bot](#a-simple-echo-bot)
  * [General API Documentation](#general-api-documentation)
    * [Types](#types)
    * [Methods](#methods)
    * [General use of the API](#general-use-of-the-api)
      * [Message handlers](#message-handlers)
      * [TeleBot](#telebot)
      * [Reply markup](#reply-markup)
  * [Advanced use of the API](#advanced-use-of-the-api)
    * [Asynchronous delivery of messages](#asynchronous-delivery-of-messages)
    * [Sending large text messages](#sending-large-text-messages)
    * [Controlling the amount of Threads used by TeleBot](#controlling-the-amount-of-threads-used-by-telebot)
    * [Don't stop when receiving an error](#dont-stop-when-receiving-an-error)
    * [The listener mechanism](#the-listener-mechanism)
    * [Using web hooks](#using-web-hooks)
    * [Logging](#logging)
  * [The Telegram Chat Group](#the-telegram-chat-group)
  * [More examples](#more-examples)

## Getting started.

This API is tested with Python 2.6, Python 2.7, Python 3.4, Pypy and Pypy 3.
There are two ways to install the library:

* Installation using pip (a Python package manager):

```
$ pip install pyTelegramBotAPI
```
* Installation from source (requires git):

```
$ git clone https://github.com/eternnoir/pyTelegramBotAPI.git
$ cd pyTelegramBotAPI
$ python setup.py install
```

It is generally recommended to use the first option.

## Writing your first bot

### Prerequisites

It is presumed that you [have obtained an API token with @BotFather](https://core.telegram.org/bots#botfather). We will call this token `TOKEN`.
Furthermore, you have basic knowledge of the Python programming language and more importantly [the Telegram Bot API](https://core.telegram.org/bots/api).

### A simple echo bot

The TeleBot class (defined in \__init__.py) encapsulates all API calls in a single class. It provides functions such as `send_xyz` (`send_message`, `send_document` etc.) and several ways to listen for incoming messages.

Create a file called `echo_bot.py`.
Then, open the file and create an instance of the TeleBot class.
```python
import telebot

bot = TeleBot("TOKEN")
```
*Note: Make sure to actually replace TOKEN with our own API token.*

After that declaration, we need to register some so-called message handlers. Message handlers define filters which a message must pass. If a message passes the filter, the decorated function is called and the incoming message is passed as an argument.

Let's define a message handler which handles incoming `/start` and `/help` commands.
```python
@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
	bot.reply_to(message, "Howdy, how are you doing?")
```
A function which is decorated by a message handler __can have an arbitrary name, however, it must have only one parameter (the message)__.

Let's add another handler:
```python
@bot.message.handler(func=lambda m: True)
def echo_all(message):
	bot.reply_to(message, message.text)
```
This one echoes all incoming text messages back to the sender.

We now have a basic bot which replies a static message to "/start" and "/help" commands and echoes the rest of the sent messages back. To start the bot, add the following to our source file:
```python
bot.polling()

import time
while True:
	time.sleep(100)
```
The last three lines are necessary to keep the process alive. If they were to be omitted, the program would terminate as soon as bot.polling() is called. They have no impact on the bot's functioning.

Alright, that's it! Our source file now looks like this:
```python
import telebot

bot = TeleBot("TOKEN")

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
	bot.reply_to(message, "Howdy, how are you doing?")

@bot.message.handler(func=lambda m: True)
def echo_all(message):
	bot.reply_to(message, message.text)

bot.polling()

import time
while True:
	time.sleep(100)
```
To start the bot, simply open up a terminal and enter `python echo_bot.py` to run the bot! Test it by sending commands ('/start' and '/help') and arbitrary text messages.

## General API Documentation

### Types

All types are defined in types.py. They are all completely in line with the [Telegram API's definition of the types](https://core.telegram.org/bots/api#available-types), except for the Message's `from` field, which is renamed to `from_user` (because `from` is a Python reserved token). Thus, attributes such as `message_id` can be accessed directly with `message.message_id`. Note that `chat` can be either an instance of `User` or `GroupChat`.

### Methods

All [API methods](https://core.telegram.org/bots/api#available-methods) are located in the TeleBot class. They are renamed to follow common Python naming conventions. E.g. `getMe` is renamed to `get_me` and `sendMessage` to `send_message`.

### General use of the API

Outlined below are some general use cases of the API.

#### Message handlers
A message handler is a function which is decorated with the `message_handler` decorator of a TeleBot instance. The following examples illustrate the possibilities of message handlers:
```python
import telebot
bot = telebot.TeleBot("TOKEN")

# Handles all text messages that contains the commands '/start' or '/help'.
@bot.message_handler(commands=['start', 'help'])
def handle_start_help(message):
	pass

# Handles all sent documents and audio files
@bot.message_handler(content_types=['document', 'audio'])
def handle_docs_audio(message):
	pass

# Handles all text messages that match the regular expression
@bot.message_handler(regexp="SOME_REGEXP")
def handle_message(message):
	pass

#Handles all messages for which the lambda returns True
@bot.message_handler(func=lambda message: message.document.mime_type == 'text/plain', content_types=['document'])
def handle_text_doc(message):
	pass

#Which could also be defined as:
def test_message(message):
	return message.document.mime_type == 'text/plan'

@bot.message_handler(func=test_message, content_types=['document'])
def handle_text_doc(message)
	pass
```
*Note: all handlers are tested in the order in which they were declared*
#### TeleBot
```python
import telebot

TOKEN = '<token_string>'
tb = telebot.TeleBot(TOKEN)	#create a new Telegram Bot object

# getMe
user = tb.get_me()

# sendMessage
tb.send_message(chatid, text)

# forwardMessage
tb.forward_message(to_chat_id, from_chat_id, message_id)

# sendPhoto with a File
photo = open('/tmp/photo.png', 'rb')
tb.send_photo(chat_id, photo)

# sendAudio
audio = open('/tmp/audio.mp3', 'rb')
tb.send_audio(chat_id, audio)

## sendAudio with duration, performer and title.
tb.send_audio(CHAT_ID, file_data, 1, 'eternnoir', 'pyTelegram')

# sendVoice
voice = open('/tmp/voice.ogg', 'rb')
tb.send_voice(chat_id, voice)

# sendDocument
doc = open('/tmp/file.txt', 'rb')
tb.send_document(chat_id, doc)

# sendSticker
sti = open('/tmp/sti.webp', 'rb')
tb.send_sticker(chat_id, sti)

# sendVideo
video = open('/tmp/video.mp4', 'rb')
tb.send_video(chat_id, video)

# sendLocation
tb.send_location(chat_id, lat, lon)

# sendChatAction
# action_string can be one of the following strings: 'typing', 'upload_photo', 'record_video', 'upload_video',
# 'record_audio', 'upload_audio', 'upload_document' or 'find_location'.
tb.send_chat_action(chat_id, action_string)
```
#### Reply markup
All `send_xyz` functions of TeleBot take an optional `reply_markup` argument. This argument must be an instance of `ReplyKeyboardMarkup`, `ReplyKeyboardHide` or `ForceReply`, which are defined in types.py.

```python
from telebot import types

# Use the ReplyKeyboardMarkup class.
# It's constructor can take the following optional arguments:
# - resize_keyboard: True/False (default False)
# - one_time_keyboard: True/False (default False)
# - selective: True/False (default False)
# - row_width: integer (default 3)
# row_width is used in combination with the add() function.
# It defines how many buttons are fit on each row before continuing on the next row.
markup = types.ReplyKeyboardMarkup(row_width=2)
markup.add('a', 'v', 'd')
tb.send_message(chat_id, message, reply_markup=markup)

# or add strings one row at a time:
markup = types.ReplyKeyboardMarkup()
markup.row('a', 'v')
markup.row('c', 'd', 'e')
tb.send_message(chat_id, message, reply_markup=markup)

# Using ReplyKeyboardHide
# Takes an optional selective argument (True/False, default False)
markup = types.ReplyKeyboardHide(selective=False)
tb.send_message(chat_id, message, reply_markup=markup)

# Using ForceReply
# Takes an optional selective argument (True/False, default False)
markup = types.ForceReply(selective=False)
tb.send_message(chat_id, message, reply_markup=markup)
```

## Advanced use of the API

### Asynchronous delivery of messages
There exists an implementation of TeleBot which executes all `send_xyz` and the `get_me` functions asynchronously. This can speed up you bot __significantly__, but it has unwanted side effects if used without caution.
To enable this behaviour, create an instance of AsyncTeleBot instead of TeleBot.
```python
tb = telebot.AsyncTeleBot("TOKEN")
```
Now, every function that calls the Telegram API is executed in a separate Thread. The functions are modified to return an AsyncTask instance (defined in \__init__.py). Using AsyncTeleBot allows you to do the following:
```python
import telebot

tb = AsyncTeleBot("TOKEN")
task = tb.get_me() # Execute an API call
# Do some other operations...
a = 0
for a in range(100):
	a += 10

result = task.wait() # Get the result of the execution
```
*Note: if you execute send_xyz functions after eachother without calling wait(), the order in which messages are delivered might be wrong.*

### Sending large text messages
Sometimes you must send messages that exceeds 5000 characters. The Telegram API can not handle that many characters at a time, so we need to split the message in multiples. Here is how to do that using the API:
```python
from telebot import apihelper
large_text = open("large_text.txt", "rb").read()
splitted_text = apihelper.split_string(large_text, 3000)
for text in splitted_text:
	tb.send_message(chat_id, text)
```
### Controlling the amount of Threads used by TeleBot
The TeleBot constructor takes the following optional arguments:
 - create_threads: True/False (default True). A flag to indicate whether TeleBot should execute message handlers on it's polling Thread.
 - num_threads: integer (default 4). Controls the amount of WorkerThreads created for the internal thread pool that TeleBot uses to execute message handlers. Is not used when create_threads is False.

### Don't stop when receiving an error
TeleBot's `polling()` function takes an optional none_stop argument. When none_stop equals True, the bot will not exit when it receives an invalid response from the Telegram API servers. none_stop defaults to False.
Example: `tb.polling(none_stop=True)`

### The listener mechanism
As an alternative to the message handlers, one can also register a function as a listener to TeleBot. Example:
```python
def handle_messages(message):
	for message in messsages:
		# Do something with the message
		bot.reply_to(message, 'hi')

bot.set_update_listener(handle_messages)
bot.polling()
```

### Using web hooks
If you prefer using web hooks to the getUpdates method, you can use the `process_new_messages(messages)` function in TeleBot to make it process the messages that you supply. It takes a list of Message objects.

### Logging

Now you can use Telebot module logger to log some information in Telebot. Use `telebot.logger` to get the
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

## The Telegram Chat Group

Get help. Discuss. Chat.

Join [pyTelegramBotAPI Chat Group](https://telegram.me/joinchat/067e22c60035523fda8f6025ee87e30b).

## More examples

* [Echo Bot](https://github.com/eternnoir/pyTelegramBotAPI/blob/master/examples/echo_bot.py)
* [Deep Linking](https://github.com/eternnoir/pyTelegramBotAPI/blob/master/examples/deep_linking.py)
* [next_step_handler Example](https://github.com/eternnoir/pyTelegramBotAPI/blob/master/examples/step_example.py)