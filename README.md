# pyTelegramBotAPI
Python Telegram bot api.

## How to install

* Install from source

```
$ git clone https://github.com/eternnoir/pyTelegramBotAPI.git
$ cd pyTelegramBotAPI
$ python setup.py install
```

* Install by pip

```
$ pip install pyTelegramBotAPI
```

## Example

* Send Message

```python
import telebot

TOKEN = '<token string>'

tb = telebot.TeleBot(TOKEN)
# tb.send_message(chatid,message)
print tb.send_message(281281, 'gogo power ranger')
```

* Echo Bot

```python
import telebot
import time

TOKEN = '<token_string>'


def listener(*messages):
    """
    When new message get will call this function.
    :param messages:
    :return:
    """
    for m in messages:
        chatid = m.chat.id
        text = m.text
        tb.send_message(chatid, text)


tb = telebot.TeleBot(TOKEN)
tb.get_update()  # cache exist message
tb.set_update_listener(listener) #register listener
tb.polling(3)
while True:
    time.sleep(20)
```

## TODO

- [x] getMe
- [x] sendMessage
- [x] forwardMessage
- [x] sendPhoto
- [x] sendAudio
- [x] sendDocument
- [x] sendSticker
- [x] sendVideo
- [ ] sendLocation
- [ ] sendChatAction
- [ ] getUserProfilePhotos
- [x] getUpdates
