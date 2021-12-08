
[![PyPi Package Version](https://img.shields.io/pypi/v/pyTelegramBotAPI.svg)](https://pypi.python.org/pypi/pyTelegramBotAPI)
[![Supported Python versions](https://img.shields.io/pypi/pyversions/pyTelegramBotAPI.svg)](https://pypi.python.org/pypi/pyTelegramBotAPI)
[![Build Status](https://travis-ci.org/eternnoir/pyTelegramBotAPI.svg?branch=master)](https://travis-ci.org/eternnoir/pyTelegramBotAPI)
[![PyPi downloads](https://img.shields.io/pypi/dm/pyTelegramBotAPI.svg)](https://pypi.org/project/pyTelegramBotAPI/)

# <p align="center">pyTelegramBotAPI

<p align="center">A simple, but extensible Python implementation for the <a href="https://core.telegram.org/bots/api">Telegram Bot API</a>.</p>
<p align="center">Supports both sync and async ways.</p>

## <p align="center">Supporting Bot API version: <a href="https://core.telegram.org/bots/api#december-7-2021">5.5</a>!

## Contents

  * [Getting started](#getting-started)
  * [Writing your first bot](#writing-your-first-bot)
    * [Prerequisites](#prerequisites)
    * [A simple echo bot](#a-simple-echo-bot)
  * [General API Documentation](#general-api-documentation)
    * [Types](#types)
    * [Methods](#methods)
    * [General use of the API](#general-use-of-the-api)
      * [Message handlers](#message-handlers)
      * [Edited Message handler](#edited-message-handler)
      * [Channel Post handler](#channel-post-handler)
      * [Edited Channel Post handler](#edited-channel-post-handler)
      * [Callback Query handlers](#callback-query-handler)
      * [Shipping Query Handler](#shipping-query-handler)
      * [Pre Checkout Query Handler](#pre-checkout-query-handler)
      * [Poll Handler](#poll-handler)
      * [Poll Answer Handler](#poll-answer-handler)
      * [My Chat Member Handler](#my-chat-member-handler)
      * [Chat Member Handler](#chat-member-handler)
      * [Chat Join request handler](#chat-join-request-handler)
    * [Inline Mode](#inline-mode)
      * [Inline handler](#inline-handler)
      * [Chosen Inline handler](#chosen-inline-handler)
      * [Answer Inline Query](#answer-inline-query)
    * [Additional API features](#additional-api-features)
      * [Middleware handlers](#middleware-handlers)
      * [Custom filters](#custom-filters)
      * [TeleBot](#telebot)
      * [Reply markup](#reply-markup)
  * [Advanced use of the API](#advanced-use-of-the-api)
    * [Using local Bot API Server](#using-local-bot-api-sever)
    * [Asynchronous TeleBot](#asynchronous-telebot)
    * [Sending large text messages](#sending-large-text-messages)
    * [Controlling the amount of Threads used by TeleBot](#controlling-the-amount-of-threads-used-by-telebot)
    * [The listener mechanism](#the-listener-mechanism)
    * [Using web hooks](#using-web-hooks)
    * [Logging](#logging)
    * [Proxy](#proxy)
    * [Testing](#testing)
  * [API conformance](#api-conformance)
  * [AsyncTeleBot](#asynctelebot)
  * [F.A.Q.](#faq)
    * [How can I distinguish a User and a GroupChat in message.chat?](#how-can-i-distinguish-a-user-and-a-groupchat-in-messagechat)
    * [How can I handle reocurring ConnectionResetErrors?](#how-can-i-handle-reocurring-connectionreseterrors)
  * [The Telegram Chat Group](#the-telegram-chat-group)
  * [More examples](#more-examples)
  * [Bots using this API](#bots-using-this-api)

## Getting started

This API is tested with Python 3.6-3.10 and Pypy 3.
There are two ways to install the library:

* Installation using pip (a Python package manager)*:

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

**While the API is production-ready, it is still under development and it has regular updates, do not forget to update it regularly by calling `pip install pytelegrambotapi --upgrade`*

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

bot = telebot.TeleBot("TOKEN", parse_mode=None) # You can set parse_mode by default. HTML or MARKDOWN
```
*Note: Make sure to actually replace TOKEN with your own API token.*

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
@bot.message_handler(func=lambda m: True)
def echo_all(message):
	bot.reply_to(message, message.text)
```
This one echoes all incoming text messages back to the sender. It uses a lambda function to test a message. If the lambda returns True, the message is handled by the decorated function. Since we want all messages to be handled by this function, we simply always return True.

*Note: all handlers are tested in the order in which they were declared*

We now have a basic bot which replies a static message to "/start" and "/help" commands and which echoes the rest of the sent messages. To start the bot, add the following to our source file:
```python
bot.infinity_polling()
```
Alright, that's it! Our source file now looks like this:
```python
import telebot

bot = telebot.TeleBot("YOUR_BOT_TOKEN")

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
	bot.reply_to(message, "Howdy, how are you doing?")

@bot.message_handler(func=lambda message: True)
def echo_all(message):
	bot.reply_to(message, message.text)

bot.infinity_polling()
```
To start the bot, simply open up a terminal and enter `python echo_bot.py` to run the bot! Test it by sending commands ('/start' and '/help') and arbitrary text messages.

## General API Documentation

### Types

All types are defined in types.py. They are all completely in line with the [Telegram API's definition of the types](https://core.telegram.org/bots/api#available-types), except for the Message's `from` field, which is renamed to `from_user` (because `from` is a Python reserved token). Thus, attributes such as `message_id` can be accessed directly with `message.message_id`. Note that `message.chat` can be either an instance of `User` or `GroupChat` (see [How can I distinguish a User and a GroupChat in message.chat?](#how-can-i-distinguish-a-user-and-a-groupchat-in-messagechat)).

The Message object also has a `content_type`attribute, which defines the type of the Message. `content_type` can be one of the following strings:
`text`, `audio`, `document`, `photo`, `sticker`, `video`, `video_note`, `voice`, `location`, `contact`, `new_chat_members`, `left_chat_member`, `new_chat_title`, `new_chat_photo`, `delete_chat_photo`, `group_chat_created`, `supergroup_chat_created`, `channel_chat_created`, `migrate_to_chat_id`, `migrate_from_chat_id`, `pinned_message`.

You can use some types in one function. Example:

```content_types=["text", "sticker", "pinned_message", "photo", "audio"]```

### Methods

All [API methods](https://core.telegram.org/bots/api#available-methods) are located in the TeleBot class. They are renamed to follow common Python naming conventions. E.g. `getMe` is renamed to `get_me` and `sendMessage` to `send_message`.

### General use of the API

Outlined below are some general use cases of the API.

#### Message handlers
A message handler is a function that is decorated with the `message_handler` decorator of a TeleBot instance. Message handlers consist of one or multiple filters.
Each filter must return True for a certain message in order for a message handler to become eligible to handle that message. A message handler is declared in the following way (provided `bot` is an instance of TeleBot):
```python
@bot.message_handler(filters)
def function_name(message):
	bot.reply_to(message, "This is a message handler")
```
`function_name` is not bound to any restrictions. Any function name is permitted with message handlers. The function must accept at most one argument, which will be the message that the function must handle.
`filters` is a list of keyword arguments.
A filter is declared in the following manner: `name=argument`. One handler may have multiple filters.
TeleBot supports the following filters:

|name|argument(s)|Condition|
|:---:|---| ---|
|content_types|list of strings (default `['text']`)|`True` if message.content_type is in the list of strings.|
|regexp|a regular expression as a string|`True` if `re.search(regexp_arg)` returns `True` and `message.content_type == 'text'` (See [Python Regular Expressions](https://docs.python.org/2/library/re.html))|
|commands|list of strings|`True` if `message.content_type == 'text'` and `message.text` starts with a command that is in the list of strings.|
|chat_types|list of chat types|`True` if `message.chat.type` in your filter|
|func|a function (lambda or function reference)|`True` if the lambda or function reference returns `True`|
	
Here are some examples of using the filters and message handlers:

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

# Handles all messages for which the lambda returns True
@bot.message_handler(func=lambda message: message.document.mime_type == 'text/plain', content_types=['document'])
def handle_text_doc(message):
	pass

# Which could also be defined as:
def test_message(message):
	return message.document.mime_type == 'text/plain'

@bot.message_handler(func=test_message, content_types=['document'])
def handle_text_doc(message):
	pass

# Handlers can be stacked to create a function which will be called if either message_handler is eligible
# This handler will be called if the message starts with '/hello' OR is some emoji
@bot.message_handler(commands=['hello'])
@bot.message_handler(func=lambda msg: msg.text.encode("utf-8") == SOME_FANCY_EMOJI)
def send_something(message):
    pass
```
**Important: all handlers are tested in the order in which they were declared**

#### Edited Message handler
Handle edited messages
`@bot.edited_message_handler(filters) # <- passes a Message type object to your function`

#### Channel Post handler
Handle channel post messages
`@bot.channel_post_handler(filters) # <- passes a Message type object to your function`

#### Edited Channel Post handler
Handle edited channel post messages
`@bot.edited_channel_post_handler(filters) # <- passes a Message type object to your function`

#### Callback Query Handler
Handle callback queries
```python
@bot.callback_query_handler(func=lambda call: True)
def test_callback(call): # <- passes a CallbackQuery type object to your function
    logger.info(call)
```

#### Shipping Query Handler
Handle shipping queries
`@bot.shipping_query_handeler() # <- passes a ShippingQuery type object to your function`

#### Pre Checkout Query Handler
Handle pre checkoupt queries
`@bot.pre_checkout_query_handler() # <- passes a PreCheckoutQuery type object to your function`

#### Poll Handler
Handle poll updates
`@bot.poll_handler() # <- passes a Poll type object to your function`

#### Poll Answer Handler
Handle poll answers
`@bot.poll_answer_handler() # <- passes a PollAnswer type object to your function`

#### My Chat Member Handler
Handle updates of a the bot's member status in a chat
`@bot.my_chat_member_handler() # <- passes a ChatMemberUpdated type object to your function`

#### Chat Member Handler
Handle updates of a chat member's status in a chat
`@bot.chat_member_handler() # <- passes a ChatMemberUpdated type object to your function`
*Note: "chat_member" updates are not requested by default. If you want to allow all update types, set `allowed_updates` in `bot.polling()` / `bot.infinity_polling()` to `util.update_types`*

#### Chat Join Request Handler	
Handle chat join requests using:
`@bot.chat_join_request_handler() # <- passes ChatInviteLink type object to your function`

### Inline Mode

More information about [Inline mode](https://core.telegram.org/bots/inline).

#### Inline handler

Now, you can use inline_handler to get inline queries in telebot.

```python

@bot.inline_handler(lambda query: query.query == 'text')
def query_text(inline_query):
    # Query message is text
```

#### Chosen Inline handler

Use chosen_inline_handler to get chosen_inline_result in telebot. Don't forgot add the /setinlinefeedback
command for @Botfather.

More information : [collecting-feedback](https://core.telegram.org/bots/inline#collecting-feedback)

```python
@bot.chosen_inline_handler(func=lambda chosen_inline_result: True)
def test_chosen(chosen_inline_result):
    # Process all chosen_inline_result.
```

#### Answer Inline Query

```python
@bot.inline_handler(lambda query: query.query == 'text')
def query_text(inline_query):
    try:
        r = types.InlineQueryResultArticle('1', 'Result', types.InputTextMessageContent('Result message.'))
        r2 = types.InlineQueryResultArticle('2', 'Result2', types.InputTextMessageContent('Result message2.'))
        bot.answer_inline_query(inline_query.id, [r, r2])
    except Exception as e:
        print(e)

```

### Additional API features

#### Middleware Handlers

A middleware handler is a function that allows you to modify requests or the bot context as they pass through the 
Telegram to the bot. You can imagine middleware as a chain of logic connection handled before any other handlers are
executed. Middleware processing is disabled by default, enable it by setting `apihelper.ENABLE_MIDDLEWARE = True`. 

```python
apihelper.ENABLE_MIDDLEWARE = True

@bot.middleware_handler(update_types=['message'])
def modify_message(bot_instance, message):
    # modifying the message before it reaches any other handler 
    message.another_text = message.text + ':changed'

@bot.message_handler(commands=['start'])
def start(message):
    # the message is already modified when it reaches message handler
    assert message.another_text == message.text + ':changed'
```
There are other examples using middleware handler in the [examples/middleware](examples/middleware) directory.
	
	
#### Custom filters
Also, you can use built-in custom filters. Or, you can create your own filter.	

[Example of custom filter](https://github.com/eternnoir/pyTelegramBotAPI/blob/master/examples/custom_filters/general_custom_filters.py)
	
Also, we have examples on them. Check this links:
	
You can check some built-in filters in source [code](https://github.com/eternnoir/pyTelegramBotAPI/blob/master/telebot/custom_filters.py)
	
Example of [filtering by id](https://github.com/eternnoir/pyTelegramBotAPI/blob/master/examples/custom_filters/id_filter_example.py)
	
Example of [filtering by text](https://github.com/eternnoir/pyTelegramBotAPI/blob/master/examples/custom_filters/text_filter_example.py)
	
If you want to add some built-in filter, you are welcome to add it in custom_filters.py file.
	
Here is example of creating filter-class:
	
```python
class IsAdmin(telebot.custom_filters.SimpleCustomFilter):
    # Class will check whether the user is admin or creator in group or not
    key='is_admin'
    @staticmethod
    def check(message: telebot.types.Message):
        return bot.get_chat_member(message.chat.id,message.from_user.id).status in ['administrator','creator']
	
# To register filter, you need to use method add_custom_filter.
bot.add_custom_filter(IsAdmin())
	
# Now, you can use it in handler.
@bot.message_handler(is_admin=True)
def admin_of_group(message):
	bot.send_message(message.chat.id, 'You are admin of this group!')

```
	

#### TeleBot
```python
import telebot

TOKEN = '<token_string>'
tb = telebot.TeleBot(TOKEN)	#create a new Telegram Bot object

# Upon calling this function, TeleBot starts polling the Telegram servers for new messages.
# - interval: int (default 0) - The interval between polling requests
# - timeout: integer (default 20) - Timeout in seconds for long polling.
# - allowed_updates: List of Strings (default None) - List of update types to request 
tb.infinity_polling(interval=0, timeout=20)

# getMe
user = tb.get_me()

# setWebhook
tb.set_webhook(url="http://example.com", certificate=open('mycert.pem'))
# unset webhook
tb.remove_webhook()

# getUpdates
updates = tb.get_updates()
# or
updates = tb.get_updates(1234,100,20) #get_Updates(offset, limit, timeout):

# sendMessage
tb.send_message(chat_id, text)

# editMessageText
tb.edit_message_text(new_text, chat_id, message_id)

# forwardMessage
tb.forward_message(to_chat_id, from_chat_id, message_id)

# All send_xyz functions which can take a file as an argument, can also take a file_id instead of a file.
# sendPhoto
photo = open('/tmp/photo.png', 'rb')
tb.send_photo(chat_id, photo)
tb.send_photo(chat_id, "FILEID")

# sendAudio
audio = open('/tmp/audio.mp3', 'rb')
tb.send_audio(chat_id, audio)
tb.send_audio(chat_id, "FILEID")

## sendAudio with duration, performer and title.
tb.send_audio(CHAT_ID, file_data, 1, 'eternnoir', 'pyTelegram')

# sendVoice
voice = open('/tmp/voice.ogg', 'rb')
tb.send_voice(chat_id, voice)
tb.send_voice(chat_id, "FILEID")

# sendDocument
doc = open('/tmp/file.txt', 'rb')
tb.send_document(chat_id, doc)
tb.send_document(chat_id, "FILEID")

# sendSticker
sti = open('/tmp/sti.webp', 'rb')
tb.send_sticker(chat_id, sti)
tb.send_sticker(chat_id, "FILEID")

# sendVideo
video = open('/tmp/video.mp4', 'rb')
tb.send_video(chat_id, video)
tb.send_video(chat_id, "FILEID")

# sendVideoNote
videonote = open('/tmp/videonote.mp4', 'rb')
tb.send_video_note(chat_id, videonote)
tb.send_video_note(chat_id, "FILEID")

# sendLocation
tb.send_location(chat_id, lat, lon)

# sendChatAction
# action_string can be one of the following strings: 'typing', 'upload_photo', 'record_video', 'upload_video',
# 'record_audio', 'upload_audio', 'upload_document' or 'find_location'.
tb.send_chat_action(chat_id, action_string)

# getFile
# Downloading a file is straightforward
# Returns a File object
import requests
file_info = tb.get_file(file_id)

file = requests.get('https://api.telegram.org/file/bot{0}/{1}'.format(API_TOKEN, file_info.file_path))


```
#### Reply markup
All `send_xyz` functions of TeleBot take an optional `reply_markup` argument. This argument must be an instance of `ReplyKeyboardMarkup`, `ReplyKeyboardRemove` or `ForceReply`, which are defined in types.py.

```python
from telebot import types

# Using the ReplyKeyboardMarkup class
# It's constructor can take the following optional arguments:
# - resize_keyboard: True/False (default False)
# - one_time_keyboard: True/False (default False)
# - selective: True/False (default False)
# - row_width: integer (default 3)
# row_width is used in combination with the add() function.
# It defines how many buttons are fit on each row before continuing on the next row.
markup = types.ReplyKeyboardMarkup(row_width=2)
itembtn1 = types.KeyboardButton('a')
itembtn2 = types.KeyboardButton('v')
itembtn3 = types.KeyboardButton('d')
markup.add(itembtn1, itembtn2, itembtn3)
tb.send_message(chat_id, "Choose one letter:", reply_markup=markup)

# or add KeyboardButton one row at a time:
markup = types.ReplyKeyboardMarkup()
itembtna = types.KeyboardButton('a')
itembtnv = types.KeyboardButton('v')
itembtnc = types.KeyboardButton('c')
itembtnd = types.KeyboardButton('d')
itembtne = types.KeyboardButton('e')
markup.row(itembtna, itembtnv)
markup.row(itembtnc, itembtnd, itembtne)
tb.send_message(chat_id, "Choose one letter:", reply_markup=markup)
```
The last example yields this result:

![ReplyKeyboardMarkup](https://farm3.staticflickr.com/2933/32418726704_9ef76093cf_o_d.jpg "ReplyKeyboardMarkup")

```python
# ReplyKeyboardRemove: hides a previously sent ReplyKeyboardMarkup
# Takes an optional selective argument (True/False, default False)
markup = types.ReplyKeyboardRemove(selective=False)
tb.send_message(chat_id, message, reply_markup=markup)
```

```python
# ForceReply: forces a user to reply to a message
# Takes an optional selective argument (True/False, default False)
markup = types.ForceReply(selective=False)
tb.send_message(chat_id, "Send me another word:", reply_markup=markup)
```
ForceReply:

![ForceReply](https://farm4.staticflickr.com/3809/32418726814_d1baec0fc2_o_d.jpg "ForceReply")


### Working with entities
This object represents one special entity in a text message. For example, hashtags, usernames, URLs, etc.
Attributes:
* `type`
* `url`
* `offset`
* `length`
* `user`


**Here's an Example:**`message.entities[num].<attribute>`<br>
Here `num` is the entity number or order of entity in a reply, for if incase there are multiple entities in the reply/message.<br>
`message.entities` returns a list of entities object. <br>
`message.entities[0].type` would give the type of the first entity<br>
Refer [Bot Api](https://core.telegram.org/bots/api#messageentity) for extra details

## Advanced use of the API

### Using local Bot API Sever
Since version 5.0 of the Bot API, you have the possibility to run your own [Local Bot API Server](https://core.telegram.org/bots/api#using-a-local-bot-api-server).
pyTelegramBotAPI also supports this feature.
```python
from telebot import apihelper

apihelper.API_URL = "http://localhost:4200/bot{0}/{1}"
```
**Important: Like described [here](https://core.telegram.org/bots/api#logout), you have to log out your bot from the Telegram server before switching to your local API server. in pyTelegramBotAPI use `bot.log_out()`**

*Note: 4200 is an example port*

### Asynchronous TeleBot
New: There is an asynchronous implementation of telebot.
To enable this behaviour, create an instance of AsyncTeleBot instead of TeleBot.
```python
tb = telebot.AsyncTeleBot("TOKEN")
```
Now, every function that calls the Telegram API is executed in a separate asynchronous task.
Using AsyncTeleBot allows you to do the following:
```python
import telebot

tb = telebot.AsyncTeleBot("TOKEN")

@tb.message_handler(commands=['start'])
async def start_message(message):
	await bot.send_message(message.chat.id, 'Hello!')

```

See more in [examples](https://github.com/eternnoir/pyTelegramBotAPI/tree/master/examples/asynchronous_telebot)

### Sending large text messages
Sometimes you must send messages that exceed 5000 characters. The Telegram API can not handle that many characters in one request, so we need to split the message in multiples. Here is how to do that using the API:
```python
from telebot import util
large_text = open("large_text.txt", "rb").read()

# Split the text each 3000 characters.
# split_string returns a list with the splitted text.
splitted_text = util.split_string(large_text, 3000)

for text in splitted_text:
	tb.send_message(chat_id, text)
```

Or you can use the new `smart_split` function to get more meaningful substrings:
```python
from telebot import util
large_text = open("large_text.txt", "rb").read()
# Splits one string into multiple strings, with a maximum amount of `chars_per_string` (max. 4096)
# Splits by last '\n', '. ' or ' ' in exactly this priority.
# smart_split returns a list with the splitted text.
splitted_text = util.smart_split(large_text, chars_per_string=3000)
for text in splitted_text:
	tb.send_message(chat_id, text)
```
### Controlling the amount of Threads used by TeleBot
The TeleBot constructor takes the following optional arguments:

 - threaded: True/False (default True). A flag to indicate whether
   TeleBot should execute message handlers on it's polling Thread.

### The listener mechanism
As an alternative to the message handlers, one can also register a function as a listener to TeleBot.

NOTICE: handlers won't disappear! Your message will be processed both by handlers and listeners. Also, it's impossible to predict which will work at first because of threading. If you use threaded=False, custom listeners will work earlier, after them handlers will be called. 
Example:
```python
def handle_messages(messages):
	for message in messages:
		# Do something with the message
		bot.reply_to(message, 'Hi')

bot.set_update_listener(handle_messages)
bot.infinity_polling()
```

### Using web hooks
When using webhooks telegram sends one Update per call, for processing it you should call process_new_messages([update.message]) when you recieve it.

There are some examples using webhooks in the [examples/webhook_examples](examples/webhook_examples) directory.

### Logging
You can use the Telebot module logger to log debug info about Telebot. Use `telebot.logger` to get the logger of the TeleBot module.
It is possible to add custom logging Handlers to the logger. Refer to the [Python logging module page](https://docs.python.org/2/library/logging.html) for more info.

```python
import logging

logger = telebot.logger
telebot.logger.setLevel(logging.DEBUG) # Outputs debug messages to console.
```

### Proxy
You can use proxy for request. `apihelper.proxy` object will use by call `requests` proxies argument.

```python
from telebot import apihelper

apihelper.proxy = {'http':'http://127.0.0.1:3128'}
```

If you want to use socket5 proxy you need install dependency `pip install requests[socks]` and make sure, that you have the latest version of `gunicorn`, `PySocks`, `pyTelegramBotAPI`, `requests` and `urllib3`.

```python
apihelper.proxy = {'https':'socks5://userproxy:password@proxy_address:port'}
```

### Testing
You can disable or change the interaction with real Telegram server by using
```python
apihelper.CUSTOM_REQUEST_SENDER = your_handler
```
parameter. You can pass there your own function that will be called instead of _requests.request_.

For example:
```python
def custom_sender(method, url, **kwargs):
    print("custom_sender. method: {}, url: {}, params: {}".format(method, url, kwargs.get("params")))
    result = util.CustomRequestResponse('{"ok":true,"result":{"message_id": 1, "date": 1, "chat": {"id": 1, "type": "private"}}}')
    return result
```

Then you can use API and proceed requests in your handler code.
```python
apihelper.CUSTOM_REQUEST_SENDER = custom_sender
tb = TeleBot("test")
res = tb.send_message(123, "Test")
```

Result will be:

`custom_sender. method: post, url: https://api.telegram.org/botololo/sendMessage, params: {'chat_id': '123', 'text': 'Test'}`



## API conformance

* ✔ [Bot API 5.5](https://core.telegram.org/bots/api#december-7-2021)
* ✔ [Bot API 5.4](https://core.telegram.org/bots/api#november-5-2021)
* ➕ [Bot API 5.3](https://core.telegram.org/bots/api#june-25-2021) - ChatMember* classes are full copies of ChatMember
* ✔ [Bot API 5.2](https://core.telegram.org/bots/api#april-26-2021)
* ✔ [Bot API 5.1](https://core.telegram.org/bots/api#march-9-2021)
* ✔ [Bot API 5.0](https://core.telegram.org/bots/api-changelog#november-4-2020)
* ✔ [Bot API 4.9](https://core.telegram.org/bots/api-changelog#june-4-2020)
* ✔ [Bot API 4.8](https://core.telegram.org/bots/api-changelog#april-24-2020)
* ✔ [Bot API 4.7](https://core.telegram.org/bots/api-changelog#march-30-2020)
* ✔ [Bot API 4.6](https://core.telegram.org/bots/api-changelog#january-23-2020)
* ➕ [Bot API 4.5](https://core.telegram.org/bots/api-changelog#december-31-2019) - No nested MessageEntities and Markdown2 support
* ✔ [Bot API 4.4](https://core.telegram.org/bots/api-changelog#july-29-2019)
* ✔ [Bot API 4.3](https://core.telegram.org/bots/api-changelog#may-31-2019)
* ✔ [Bot API 4.2](https://core.telegram.org/bots/api-changelog#april-14-2019)
* ➕ [Bot API 4.1](https://core.telegram.org/bots/api-changelog#august-27-2018) - No Passport support
* ➕ [Bot API 4.0](https://core.telegram.org/bots/api-changelog#july-26-2018)   - No Passport support


## AsyncTeleBot
### Asynchronous version of telebot
We have a fully asynchronous version of TeleBot.
This class is not controlled by threads. Asyncio tasks are created to execute all the stuff.

### EchoBot
Echo Bot example on AsyncTeleBot:
	
```python
# This is a simple echo bot using the decorator mechanism.
# It echoes any incoming text messages.

from telebot.async_telebot import AsyncTeleBot
bot = AsyncTeleBot('TOKEN')



# Handle '/start' and '/help'
@bot.message_handler(commands=['help', 'start'])
async def send_welcome(message):
    await bot.reply_to(message, """\
Hi there, I am EchoBot.
I am here to echo your kind words back to you. Just say anything nice and I'll say the exact same thing to you!\
""")


# Handle all other messages with content_type 'text' (content_types defaults to ['text'])
@bot.message_handler(func=lambda message: True)
async def echo_message(message):
    await bot.reply_to(message, message.text)


bot.polling()
```
As you can see here, keywords are await and async. 
	
### Why should I use async?
Asynchronous tasks depend on processor performance. Many asynchronous tasks can run parallelly, while thread tasks will block each other.

### Differences in AsyncTeleBot
AsyncTeleBot has different middlewares. See example on [middlewares](https://github.com/coder2020official/pyTelegramBotAPI/tree/master/examples/asynchronous_telebot/middleware)
	
### Examples
See more examples in our [examples](https://github.com/coder2020official/pyTelegramBotAPI/tree/master/examples/asynchronous_telebot) folder
	

## F.A.Q.

### How can I distinguish a User and a GroupChat in message.chat?
Telegram Bot API support new type Chat for message.chat.

- Check the ```type``` attribute in ```Chat``` object:
-
```python
if message.chat.type == "private":
    # private chat message

if message.chat.type == "group":
	# group chat message

if message.chat.type == "supergroup":
	# supergroup chat message

if message.chat.type == "channel":
	# channel message

```

### How can I handle reocurring ConnectionResetErrors?

Bot instances that were idle for a long time might be rejected by the server when sending a message due to a timeout of the last used session. Add `apihelper.SESSION_TIME_TO_LIVE = 5 * 60` to your initialisation to force recreation after 5 minutes without any activity. 

## The Telegram Chat Group

Get help. Discuss. Chat.

* Join the [pyTelegramBotAPI Telegram Chat Group](https://telegram.me/joinchat/Bn4ixj84FIZVkwhk2jag6A)

## More examples

* [Echo Bot](https://github.com/eternnoir/pyTelegramBotAPI/blob/master/examples/echo_bot.py)
* [Deep Linking](https://github.com/eternnoir/pyTelegramBotAPI/blob/master/examples/deep_linking.py)
* [next_step_handler Example](https://github.com/eternnoir/pyTelegramBotAPI/blob/master/examples/step_example.py)

## Bots using this API
* [SiteAlert bot](https://telegram.me/SiteAlert_bot) ([source](https://github.com/ilteoood/SiteAlert-Python)) by *ilteoood* - Monitors websites and sends a notification on changes
* [TelegramLoggingBot](https://github.com/aRandomStranger/TelegramLoggingBot) by *aRandomStranger*
* [Telegram LMGTFY_bot](https://github.com/GabrielRF/telegram-lmgtfy_bot) by *GabrielRF* - Let me Google that for you.
* [Telegram Proxy Bot](https://github.com/mrgigabyte/proxybot) by *mrgigabyte* 
* [RadRetroRobot](https://github.com/Tronikart/RadRetroRobot) by *Tronikart* - Multifunctional Telegram Bot RadRetroRobot.
* [League of Legends bot](https://telegram.me/League_of_Legends_bot) ([source](https://github.com/i32ropie/lol)) by *i32ropie*
* [NeoBot](https://github.com/neoranger/NeoBot) by [@NeoRanger](https://github.com/neoranger)
* [ColorCodeBot](https://t.me/colorcodebot) ([source](https://github.com/andydecleyre/colorcodebot)) - Share code snippets as beautifully syntax-highlighted HTML and/or images.
* [ComedoresUGRbot](http://telegram.me/ComedoresUGRbot) ([source](https://github.com/alejandrocq/ComedoresUGRbot)) by [*alejandrocq*](https://github.com/alejandrocq) - Telegram bot to check the menu of Universidad de Granada dining hall.
* [proxybot](https://github.com/p-hash/proxybot) - Simple Proxy Bot for Telegram. by p-hash
* [DonantesMalagaBot](https://github.com/vfranch/DonantesMalagaBot) - DonantesMalagaBot facilitates information to Malaga blood donors about the places where they can donate today or in the incoming days. It also records the date of the last donation so that it helps the donors to know when they can donate again. - by vfranch
* [DuttyBot](https://github.com/DmytryiStriletskyi/DuttyBot) by *Dmytryi Striletskyi* - Timetable for one university in Kiev.
* [wat-bridge](https://github.com/rmed/wat-bridge) by [*rmed*](https://github.com/rmed) - Send and receive messages to/from WhatsApp through Telegram
* [filmratingbot](http://t.me/filmratingbot)([source](https://github.com/jcolladosp/film-rating-bot)) by [*jcolladosp*](https://github.com/jcolladosp) - Telegram bot using the Python API that gets films rating from IMDb and metacritic
* [Send2Kindlebot](http://t.me/Send2KindleBot) ([source](https://github.com/GabrielRF/Send2KindleBot)) by *GabrielRF* - Send to Kindle service.
* [RastreioBot](http://t.me/RastreioBot) ([source](https://github.com/GabrielRF/RastreioBot)) by *GabrielRF* - Bot used to track packages on the Brazilian Mail Service.
* [Spbu4UBot](http://t.me/Spbu4UBot)([link](https://github.com/EeOneDown/spbu4u)) by *EeOneDown* - Bot with timetables for SPbU students.
* [SmartySBot](http://t.me/ZDU_bot)([link](https://github.com/0xVK/SmartySBot)) by *0xVK* - Telegram timetable bot, for Zhytomyr Ivan Franko State University students.
* [LearnIt](https://t.me/LearnItbot)([link](https://github.com/tiagonapoli/LearnIt)) - A Telegram Bot created to help people to memorize other languages’ vocabulary.
* [Bot-Telegram-Shodan ](https://github.com/rubenleon/Bot-Telegram-Shodan) by [rubenleon](https://github.com/rubenleon)
* [VigoBusTelegramBot](https://t.me/vigobusbot) ([GitHub](https://github.com/Pythoneiro/VigoBus-TelegramBot)) - Bot that provides buses coming to a certain stop and their remaining time for the city of Vigo (Galicia - Spain)
* [kaishnik-bot](https://t.me/kaishnik_bot) ([source](https://github.com/airatk/kaishnik-bot)) by *airatk* - bot which shows all the necessary information to KNTRU-KAI students.
* [Robbie](https://t.me/romdeliverybot) ([source](https://github.com/FacuM/romdeliverybot_support)) by @FacuM - Support Telegram bot for developers and maintainers.
* [AsadovBot](https://t.me/asadov_bot) ([source](https://github.com/desexcile/BotApi)) by @DesExcile - Сatalog of poems by Eduard Asadov.
* [thesaurus_com_bot](https://t.me/thesaurus_com_bot) ([source](https://github.com/LeoSvalov/words-i-learn-bot)) by @LeoSvalov - words and synonyms from [dictionary.com](https://www.dictionary.com) and [thesaurus.com](https://www.thesaurus.com) in the telegram.
* [InfoBot](https://t.me/info2019_bot) ([source](https://github.com/irevenko/info-bot)) by @irevenko - An all-round bot that displays some statistics (weather, time, crypto etc...)
* [FoodBot](https://t.me/ChensonUz_bot) ([source](https://github.com/Fliego/old_restaurant_telegram_chatbot)) by @Fliego - a simple bot for food ordering
* [Sporty](https://t.me/SportydBot) ([source](https://github.com/0xnu/sporty)) by @0xnu - Telegram bot for displaying the latest news, sports schedules and injury updates.
* [JoinGroup Silencer Bot](https://t.me/joingroup_silencer_bot) ([source](https://github.com/zeph1997/Telegram-Group-Silencer-Bot)) by [@zeph1997](https://github.com/zeph1997) - A Telegram Bot to remove "join group" and "removed from group" notifications.
* [TasksListsBot](https://t.me/TasksListsBot) ([source](https://github.com/Pablo-Davila/TasksListsBot)) by [@Pablo-Davila](https://github.com/Pablo-Davila) - A (tasks) lists manager bot for Telegram.
* [MyElizaPsychologistBot](https://t.me/TasksListsBot) ([source](https://github.com/Pablo-Davila/MyElizaPsychologistBot)) by [@Pablo-Davila](https://github.com/Pablo-Davila) - An implementation of the famous Eliza psychologist chatbot.
* [Frcstbot](https://t.me/frcstbot) ([source](https://github.com/Mrsqd/frcstbot_public)) by [Mrsqd](https://github.com/Mrsqd). A Telegram bot that will always be happy to show you the weather forecast.
* [MineGramBot](https://github.com/ModischFabrications/MineGramBot) by [ModischFabrications](https://github.com/ModischFabrications). This bot can start, stop and monitor a minecraft server.
* [Tabletop DiceBot](https://github.com/dexpiper/tabletopdicebot) by [dexpiper](https://github.com/dexpiper). This bot can roll multiple dices for RPG-like games, add positive and negative modifiers and show short descriptions to the rolls.
* [BarnameKon](https://t.me/BarnameKonBot) by [Anvaari](https://github.com/anvaari). This Bot make "Add to google calendar" link for your events. It give information about event and return link. It work for Jalali calendar and in Tehran Time. [Source code](https://github.com/anvaari/BarnameKon)
* [Translator bot](https://github.com/AREEG94FAHAD/translate_text_bot) by Areeg Fahad. This bot can be used to translate texts. 
* [Digital Cryptocurrency bot](https://github.com/AREEG94FAHAD/currencies_bot) by Areeg Fahad. With this bot, you can now monitor the prices of more than 12 digital Cryptocurrency. 
* [Anti-Tracking Bot](https://t.me/AntiTrackingBot) by Leon Heess [(source)](https://github.com/leonheess/AntiTrackingBot). Send any link, and the bot tries its best to remove all tracking from the link you sent.
* [Developer Bot](https://t.me/IndDeveloper_bot) by [Vishal Singh](https://github.com/vishal2376) [(source code)](https://github.com/vishal2376/telegram-bot) This telegram bot can do tasks like GitHub search & clone,provide c++ learning resources ,Stackoverflow search, Codeforces(profile visualizer,random problems)
* [oneIPO bot](https://github.com/aaditya2200/IPO-proj) by [Aadithya](https://github.com/aaditya2200) & [Amol Soans](https://github.com/AmolDerickSoans) This Telegram bot provides live updates , data and documents on current and upcoming IPOs(Initial Public Offerings) 
* [CoronaGraphsBot](https://t.me/CovidGraph_bot) ([source](https://github.com/TrevorWinstral/CoronaGraphsBot)) by *TrevorWinstral* - Gets live COVID Country data, plots it, and briefs the user
* [ETHLectureBot](https://t.me/ETHLectureBot) ([source](https://github.com/TrevorWinstral/ETHLectureBot)) by *TrevorWinstral* - Notifies ETH students when their lectures have been uploaded
* [Vlun Finder Bot](https://github.com/resinprotein2333/Vlun-Finder-bot) by [Resinprotein2333](https://github.com/resinprotein2333). This bot can help you to find The information of CVE vulnerabilities.
* [ETHGasFeeTrackerBot](https://t.me/ETHGasFeeTrackerBot) ([Source](https://github.com/DevAdvik/ETHGasFeeTrackerBot]) by *DevAdvik* - Get Live Ethereum Gas Fees in GWEI
* [Google Sheet Bot](https://github.com/JoachimStanislaus/Tele_Sheet_bot) by [JoachimStanislaus](https://github.com/JoachimStanislaus). This bot can help you to track your expenses by uploading your bot entries to your google sheet.
* [GrandQuiz Bot](https://github.com/Carlosma7/TFM-GrandQuiz) by [Carlosma7](https://github.com/Carlosma7). This bot is a trivia game that allows you to play with people from different ages. This project addresses the use of a system through chatbots to carry out a social and intergenerational game as an alternative to traditional game development.
	
**Want to have your bot listed here? Just make a pull request. Only bots with public source code are accepted.**
