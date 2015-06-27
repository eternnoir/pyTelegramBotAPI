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

## TeleBot API usage

***NOTICE*** : getUpdates Message type only support text now.

```python
import telebot
import time

TOKEN = '<token_string>'
tb = telebot.TeleBot(TOKEN)	#create new Telegram Bot object

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

# sendAudio
audio = open('/tmp/audio.ogg', 'rb')
tb.send_audio(chat_id, audio)

# sendDocument
doc = open('/tmp/file.txt', 'rb')
tb.send_document(chat_id, doc)

# sendSticker
sti = open('/tmp/sti.webp', 'rb')
tb.send_sticker(chat_id, sti)

# sendVideo
video = open('/tmp/video.mp4', 'rb')
tb.send_video(chat_id, video)

```

## TODO

- [ ] Let message not only support text.
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
- [ ] getUpdates      (Only text message support now.)
