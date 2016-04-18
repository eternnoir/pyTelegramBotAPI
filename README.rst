#

.. raw:: html

   <p align="center">

pyTelegramBotAPI

.. raw:: html

   <p align="center">

A simple, but extensible Python implementation for the `Telegram Bot
API <https://core.telegram.org/bots/api>`__.

|Download Month| |Build Status| |Download Month|

-  `Getting started. <#getting-started>`__
-  `Writing your first bot <#writing-your-first-bot>`__

   -  `Prerequisites <#prerequisites>`__
   -  `A simple echo bot <#a-simple-echo-bot>`__

-  `General API Documentation <#general-api-documentation>`__

   -  `Types <#types>`__
   -  `Methods <#methods>`__
   -  `General use of the API <#general-use-of-the-api>`__
   -  `Message handlers <#message-handlers>`__
   -  `Callback Query handlers <#message-handlers>`__
   -  `TeleBot <#telebot>`__
   -  `Reply markup <#reply-markup>`__
   -  `Inline Mode <#inline-mode>`__

-  `Advanced use of the API <#advanced-use-of-the-api>`__

   -  `Asynchronous delivery of
      messages <#asynchronous-delivery-of-messages>`__
   -  `Sending large text messages <#sending-large-text-messages>`__
   -  `Controlling the amount of Threads used by
      TeleBot <#controlling-the-amount-of-threads-used-by-telebot>`__
   -  `The listener mechanism <#the-listener-mechanism>`__
   -  `Using web hooks <#using-web-hooks>`__
   -  `Logging <#logging>`__

-  `F.A.Q. <#faq>`__

   -  `Bot 2.0 <#bot-20>`__
   -  `How can I distinguish a User and a GroupChat in
      message.chat? <#how-can-i-distinguish-a-user-and-a-groupchat-in-messagechat>`__

-  `The Telegram Chat Group <#the-telegram-chat-group>`__
-  `More examples <#more-examples>`__
-  `Bots using this API <#bots-using-this-api>`__

Getting started.
----------------

This API is tested with Python 2.6, Python 2.7, Python 3.4, Pypy and
Pypy 3. There are two ways to install the library:

-  Installation using pip (a Python package manager)\*:

::

    $ pip install pyTelegramBotAPI

-  Installation from source (requires git):

::

    $ git clone https://github.com/eternnoir/pyTelegramBotAPI.git
    $ cd pyTelegramBotAPI
    $ python setup.py install

It is generally recommended to use the first option.

\*\*While the API is production-ready, it is still under development and
it has regular updates, do not forget to update it regularly by calling
``pip install pytelegrambotapi --upgrade``\ \*

Writing your first bot
----------------------

Prerequisites
~~~~~~~~~~~~~

It is presumed that you [have obtained an API token with
@BotFather](https://core.telegram.org/bots#botfather). We will call this
token ``TOKEN``. Furthermore, you have basic knowledge of the Python
programming language and more importantly `the Telegram Bot
API <https://core.telegram.org/bots/api>`__.

A simple echo bot
~~~~~~~~~~~~~~~~~

The TeleBot class (defined in \_\_init\_\_.py) encapsulates all API
calls in a single class. It provides functions such as ``send_xyz``
(``send_message``, ``send_document`` etc.) and several ways to listen
for incoming messages.

Create a file called ``echo_bot.py``. Then, open the file and create an
instance of the TeleBot class.

.. code:: python

    import telebot

    bot = telebot.TeleBot("TOKEN")

*Note: Make sure to actually replace TOKEN with your own API token.*

After that declaration, we need to register some so-called message
handlers. Message handlers define filters which a message must pass. If
a message passes the filter, the decorated function is called and the
incoming message is passed as an argument.

Let's define a message handler which handles incoming ``/start`` and
``/help`` commands.

.. code:: python

    @bot.message_handler(commands=['start', 'help'])
    def send_welcome(message):
        bot.reply_to(message, "Howdy, how are you doing?")

A function which is decorated by a message handler **can have an
arbitrary name, however, it must have only one parameter (the
message)**.

Let's add another handler:

.. code:: python

    @bot.message_handler(func=lambda m: True)
    def echo_all(message):
        bot.reply_to(message, message.text)

This one echoes all incoming text messages back to the sender. It uses a
lambda function to test a message. If the lambda returns True, the
message is handled by the decorated function. Since we want all messages
to be handled by this function, we simply always return True.

*Note: all handlers are tested in the order in which they were declared*

We now have a basic bot which replies a static message to "/start" and
"/help" commands and which echoes the rest of the sent messages. To
start the bot, add the following to our source file:

.. code:: python

    bot.polling()

Alright, that's it! Our source file now looks like this:

.. code:: python

    import telebot

    bot = telebot.TeleBot("TOKEN")

    @bot.message_handler(commands=['start', 'help'])
    def send_welcome(message):
        bot.reply_to(message, "Howdy, how are you doing?")

    @bot.message_handler(func=lambda message: True)
    def echo_all(message):
        bot.reply_to(message, message.text)

    bot.polling()

To start the bot, simply open up a terminal and enter
``python echo_bot.py`` to run the bot! Test it by sending commands
('/start' and '/help') and arbitrary text messages.

General API Documentation
-------------------------

Types
~~~~~

All types are defined in types.py. They are all completely in line with
the `Telegram API's definition of the
types <https://core.telegram.org/bots/api#available-types>`__, except
for the Message's ``from`` field, which is renamed to ``from_user``
(because ``from`` is a Python reserved token). Thus, attributes such as
``message_id`` can be accessed directly with ``message.message_id``.
Note that ``message.chat`` can be either an instance of ``User`` or
``GroupChat`` (see `How can I distinguish a User and a GroupChat in
message.chat? <#how-can-i-distinguish-a-user-and-a-groupchat-in-messagechat>`__).

The Message object also has a ``content_types``\ attribute, which
defines the type of the Message. ``content_types`` can be one of the
following strings: 'text', 'audio', 'document', 'photo', 'sticker',
'video', 'voice', 'location', 'contact', 'new\_chat\_participant',
'left\_chat\_participant', 'new\_chat\_title', 'new\_chat\_photo',
'delete\_chat\_photo', 'group\_chat\_created'.

Methods
~~~~~~~

All `API
methods <https://core.telegram.org/bots/api#available-methods>`__ are
located in the TeleBot class. They are renamed to follow common Python
naming conventions. E.g. ``getMe`` is renamed to ``get_me`` and
``sendMessage`` to ``send_message``.

General use of the API
~~~~~~~~~~~~~~~~~~~~~~

Outlined below are some general use cases of the API.

Message handlers
^^^^^^^^^^^^^^^^

A message handler is a function that is decorated with the
``message_handler`` decorator of a TeleBot instance. Message handlers
consist of one or multiple filters. Each filter much return True for a
certain message in order for a message handler to become eligible to
handle that message. A message handler is declared in the following way
(provided ``bot`` is an instance of TeleBot):

.. code:: python

    @bot.message_handler(filters)
    def function_name(message):
        bot.reply_to(message, "This is a message handler")

``function_name`` is not bound to any restrictions. Any function name is
permitted with message handlers. The function must accept at most one
argument, which will be the message that the function must handle.
``filters`` is a list of keyword arguments. A filter is declared in the
following manner: ``name=argument``. One handler may have multiple
filters. TeleBot supports the following filters:

+--------+------+------+
| name   | argu | Cond |
|        | ment | itio |
|        | (s)  | n    |
+========+======+======+
| conten | list | ``Tr |
| t\_typ | of   | ue`` |
| es     | stri | if   |
|        | ngs  | mess |
|        | (def | age. |
|        | ault | cont |
|        | ``[' | ent\ |
|        | text | _typ |
|        | ']`` | e    |
|        | )    | is   |
|        |      | in   |
|        |      | the  |
|        |      | list |
|        |      | of   |
|        |      | stri |
|        |      | ngs. |
+--------+------+------+
| regexp | a    | ``Tr |
|        | regu | ue`` |
|        | lar  | if   |
|        | expr | ``re |
|        | essi | .sea |
|        | on   | rch( |
|        | as a | rege |
|        | stri | xp_a |
|        | ng   | rg)` |
|        |      | `    |
|        |      | retu |
|        |      | rns  |
|        |      | ``Tr |
|        |      | ue`` |
|        |      | and  |
|        |      | ``me |
|        |      | ssag |
|        |      | e.co |
|        |      | nten |
|        |      | t_ty |
|        |      | pe = |
|        |      | = 't |
|        |      | ext' |
|        |      | ``   |
|        |      | (See |
|        |      | `Pyt |
|        |      | hon  |
|        |      | Regu |
|        |      | lar  |
|        |      | Expr |
|        |      | essi |
|        |      | ons  |
|        |      | <htt |
|        |      | ps:/ |
|        |      | /doc |
|        |      | s.py |
|        |      | thon |
|        |      | .org |
|        |      | /2/l |
|        |      | ibra |
|        |      | ry/r |
|        |      | e.ht |
|        |      | ml>` |
|        |      | __   |
+--------+------+------+
| comman | list | ``Tr |
| ds     | of   | ue`` |
|        | stri | if   |
|        | ngs  | ``me |
|        |      | ssag |
|        |      | e.co |
|        |      | nten |
|        |      | t_ty |
|        |      | pe = |
|        |      | = 't |
|        |      | ext' |
|        |      | ``   |
|        |      | and  |
|        |      | ``me |
|        |      | ssag |
|        |      | e.te |
|        |      | xt`` |
|        |      | star |
|        |      | ts   |
|        |      | with |
|        |      | a    |
|        |      | comm |
|        |      | and  |
|        |      | that |
|        |      | is   |
|        |      | in   |
|        |      | the  |
|        |      | list |
|        |      | of   |
|        |      | stri |
|        |      | ngs. |
+--------+------+------+
| func   | a    | ``Tr |
|        | func | ue`` |
|        | tion | if   |
|        | (lam | the  |
|        | bda  | lamb |
|        | or   | da   |
|        | func | or   |
|        | tion | func |
|        | refe | tion |
|        | renc | refe |
|        | e)   | renc |
|        |      | e    |
|        |      | retu |
|        |      | rns  |
|        |      | ``Tr |
|        |      | ue`` |
+--------+------+------+

Here are some examples of using the filters and message handlers:

.. code:: python

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

    # Handlers can be stacked to create a function which will be called if either message_handler is eligible
    # This handler will be called if the message starts with '/hello' OR is some emoji
    @bot.message_handler(commands=['hello'])
    @bot.message_handler(func=lambda msg: msg.text.encode("utf-8") == SOME_FANCY_EMOJI)
    def send_something(message):
        pass

**Important: all handlers are tested in the order in which they were
declared**

Callback Query Handler
^^^^^^^^^^^^^^^^^^^^^^

In bot2.0 update. You can get ``callback_query`` in update object. In
telebot use ``callback_query_handler`` to process callback\_querys.

.. code:: python

    @bot.callback_query_handler(func=lambda call: True)
    def  test_callback(call):
        logger.info(call)

TeleBot
^^^^^^^

.. code:: python

    import telebot

    TOKEN = '<token_string>'
    tb = telebot.TeleBot(TOKEN) #create a new Telegram Bot object

    # Upon calling this function, TeleBot starts polling the Telegram servers for new messages.
    # - none_stop: True/False (default False) - Don't stop polling when receiving an error from the Telegram servers
    # - interval: True/False (default False) - The interval between polling requests
    #           Note: Editing this parameter harms the bot's response time
    # - block: True/False (default True) - Blocks upon calling this function
    tb.polling(none_stop=False, interval=0, block=True)

    # getMe
    user = tb.get_me()

    # setWebhook
    tb.set_webhook(url="http://example.com", certificate=open('mycert.pem'))
    # unset webhook
    tb.remove_webhook()

    # getUpdates
    updates = tb.get_updates()
    updates = tb.get_updates(1234,100,20) #get_Updates(offset, limit, timeout):

    # sendMessage
    tb.send_message(chatid, text)

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

Reply markup
^^^^^^^^^^^^

All ``send_xyz`` functions of TeleBot take an optional ``reply_markup``
argument. This argument must be an instance of ``ReplyKeyboardMarkup``,
``ReplyKeyboardHide`` or ``ForceReply``, which are defined in types.py.

.. code:: python

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

    # or add strings one row at a time:
    markup = types.ReplyKeyboardMarkup()
    itembtna = types.KeyboardButton('a')
    itembtnv = types.KeyboardButton('v')
    itembtnc = types.KeyboardButton('c')
    itembtnd = types.KeyboardButton('d')
    itembtne = types.KeyboardButton('e')
    markup.row(itembtna, itembtnv)
    markup.row(itembtnc, itembtnd, itembtne)
    tb.send_message(chat_id, "Choose one letter:", reply_markup=markup)

The last example yields this result:

.. figure:: https://pp.vk.me/c624430/v624430512/473e5/_mxxW7FPe4U.jpg
   :alt: ReplyKeyboardMarkup

   ReplyKeyboardMarkup

.. code:: python

    # ReplyKeyboardHide: hides a previously sent ReplyKeyboardMarkup
    # Takes an optional selective argument (True/False, default False)
    markup = types.ReplyKeyboardHide(selective=False)
    tb.send_message(chat_id, message, reply_markup=markup)

.. code:: python

    # ForceReply: forces a user to reply to a message
    # Takes an optional selective argument (True/False, default False)
    markup = types.ForceReply(selective=False)
    tb.send_message(chat_id, "Send me another word:", reply_markup=markup)

ForceReply:

.. figure:: https://pp.vk.me/c624430/v624430512/473ec/602byyWUHcs.jpg
   :alt: ForceReply

   ForceReply

Inline Mode
~~~~~~~~~~~

More information about `Inline
mode <https://core.telegram.org/bots/inline>`__.

inline\_handler
^^^^^^^^^^^^^^^

Now, you can use inline\_handler to get inline\_query in telebot.

.. code:: python


    @bot.inline_handler(lambda query: query.query == 'text')
    def query_text(inline_query):
        # Query message is text

chosen\_inline\_handler
^^^^^^^^^^^^^^^^^^^^^^^

Use chosen\_inline\_handler to get chosen\_inline\_result in telebot.
Don't forgot add the /setinlinefeedback command for @Botfather.

More information :
`collecting-feedback <https://core.telegram.org/bots/inline#collecting-feedback>`__

.. code:: python

    @bot.chosen_inline_handler(func=lambda chosen_inline_result: True)
    def test_chosen(chosen_inline_result):
        # Process all chosen_inline_result.

answer\_inline\_query
^^^^^^^^^^^^^^^^^^^^^

.. code:: python

    @bot.inline_handler(lambda query: query.query == 'text')
    def query_text(inline_query):
        try:
            r = types.InlineQueryResultArticle('1', 'Result', 'Result message.')
            r2 = types.InlineQueryResultArticle('2', 'Result2', 'Result message2.')
            bot.answer_inline_query(inline_query.id, [r, r2])
        except Exception as e:
            print(e)

Advanced use of the API
-----------------------

Asynchronous delivery of messages
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

There exists an implementation of TeleBot which executes all
``send_xyz`` and the ``get_me`` functions asynchronously. This can speed
up you bot **significantly**, but it has unwanted side effects if used
without caution. To enable this behaviour, create an instance of
AsyncTeleBot instead of TeleBot.

.. code:: python

    tb = telebot.AsyncTeleBot("TOKEN")

Now, every function that calls the Telegram API is executed in a
separate Thread. The functions are modified to return an AsyncTask
instance (defined in util.py). Using AsyncTeleBot allows you to do the
following:

.. code:: python

    import telebot

    tb = telebot.AsyncTeleBot("TOKEN")
    task = tb.get_me() # Execute an API call
    # Do some other operations...
    a = 0
    for a in range(100):
        a += 10

    result = task.wait() # Get the result of the execution

*Note: if you execute send\_xyz functions after eachother without
calling wait(), the order in which messages are delivered might be
wrong.*

Sending large text messages
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Sometimes you must send messages that exceed 5000 characters. The
Telegram API can not handle that many characters in one request, so we
need to split the message in multiples. Here is how to do that using the
API:

.. code:: python

    from telebot import util
    large_text = open("large_text.txt", "rb").read()

    # Split the text each 3000 characters.
    # split_string returns a list with the splitted text.
    splitted_text = util.split_string(large_text, 3000)
    for text in splitted_text:
        tb.send_message(chat_id, text)

Controlling the amount of Threads used by TeleBot
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The TeleBot constructor takes the following optional arguments:

-  create\_threads: True/False (default True). A flag to indicate
   whether TeleBot should execute message handlers on it's polling
   Thread.
-  num\_threads: integer (default 4). Controls the amount of
   WorkerThreads created for the internal thread pool that TeleBot uses
   to execute message handlers. Is not used when create\_threads is
   False.

The listener mechanism
~~~~~~~~~~~~~~~~~~~~~~

As an alternative to the message handlers, one can also register a
function as a listener to TeleBot. Example:

.. code:: python

    def handle_messages(messages):
        for message in messsages:
            # Do something with the message
            bot.reply_to(message, 'Hi')

    bot.set_update_listener(handle_messages)
    bot.polling()

Using webhooks
~~~~~~~~~~~~~~

When using webhooks telegram sends one Update per call, for processing
it you should call process\_new\_messages([update.message]) when you
recieve it.

There are some examples using webhooks in the
*examples/webhook\_examples* directory.

Logging
~~~~~~~

You can use the Telebot module logger to log debug info about Telebot.
Use ``telebot.logger`` to get the logger of the TeleBot module. It is
possible to add custom logging Handlers to the logger. Refer to the
`Python logging module
page <https://docs.python.org/2/library/logging.html>`__ for more info.

.. code:: python

    import logging

    logger = telebot.logger
    telebot.logger.setLevel(logging.DEBUG) # Outputs debug messages to console.

F.A.Q.
------

Bot 2.0
~~~~~~~

April 9,2016 Telegram release new bot 2.0 API, which has a drastic
revision especially for the change of method's interface.If you want to
update to the latest version, please make sure you've switched bot's
code to bot 2.0 method interface.

`More information about pyTelegramBotAPI support
bot2.0 <https://github.com/eternnoir/pyTelegramBotAPI/issues/130>`__

How can I distinguish a User and a GroupChat in message.chat?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Telegram Bot API support new type Chat for message.chat.

-  Check the ``type`` attribute in ``Chat`` object:
-  \`\`\`python if message.chat.type == “private”: # private chat
   message

if message.chat.type == “group”: # group chat message

if message.chat.type == “supergroup”: # supergroup chat message

if message.chat.type == “channel”: # channel message

\`\`\`

The Telegram Chat Group
-----------------------

Get help. Discuss. Chat.

-  Join the pyTelegramBotAPI Telegram Chat Group
-  Messge to @eternnoir by telegram for Invitation.
-  We now have a Telegram Channel as well! Keep yourself up to date with
   API changes, and `join it <https://telegram.me/pytelegrambotapi>`__.

More examples
-------------

-  `Echo
   Bot <https://github.com/eternnoir/pyTelegramBotAPI/blob/master/examples/echo_bot.py>`__
-  `Deep
   Linking <https://github.com/eternnoir/pyTelegramBotAPI/blob/master/examples/deep_linking.py>`__
-  `next\_step\_handler
   Example <https://github.com/eternnoir/pyTelegramBotAPI/blob/master/examples/step_example.py>`__

Bots using this API
-------------------

-  `SiteAlert bot <https://telegram.me/SiteAlert_bot>`__
   (`source <https://github.com/ilteoood/SiteAlert-Python>`__) by
   *ilteoood* - Monitors websites and sends a notification on changes
-  `TelegramLoggingBot <https://github.com/aRandomStranger/TelegramLoggingBot>`__
   by *aRandomStranger*
-  `Telegram
   LMGTFY\_bot <https://github.com/GabrielRF/telegram-lmgtfy_bot>`__ by
   *GabrielRF*
-  `Telegram
   UrlProBot <https://github.com/GabrielRF/telegram-urlprobot>`__ by
   *GabrielRF*
-  `Telegram Proxy
   Bot <https://bitbucket.org/master_groosha/telegram-proxy-bot>`__ by
   *Groosha* - A simple BITM (bot-in-the-middle) for Telegram acting as
   some kind of "proxy".
-  `Telegram Proxy Bot <https://github.com/mrgigabyte/proxybot>`__ by
   *mrgigabyte* -
   ``Credits for the original version of this bot goes to`` **Groosha**
   ``, simply added certain features which I thought were needed``.
-  `RadRetroRobot <https://github.com/Tronikart/RadRetroRobot>`__ by
   *Tronikart* - Multifunctional Telegram Bot RadRetroRobot.
-  `League of Legends bot <https://telegram.me/League_of_Legends_bot>`__
   (`source <https://github.com/i32ropie/lol>`__) by *i32ropie*
-  `NeoBot <https://github.com/neoranger/NeoBot>`__ by *neoranger*
-  `TagAlertBot <https://github.com/pitasi/TagAlertBot>`__ by *pitasi*

Want to have your bot listed here? Send a Telegram message to @eternnoir
or @pevdh.

.. |Download Month| image:: https://img.shields.io/pypi/v/pyTelegramBotAPI.svg
   :target: https://pypi.python.org/pypi/pyTelegramBotAPI
.. |Build Status| image:: https://travis-ci.org/eternnoir/pyTelegramBotAPI.svg?branch=master
   :target: https://travis-ci.org/eternnoir/pyTelegramBotAPI
.. |Download Month| image:: https://img.shields.io/pypi/dm/pyTelegramBotAPI.svg
   :target: https://pypi.python.org/pypi/pyTelegramBotAPI
