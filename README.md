# pyTelegramBotAPI
Python Telegram bot api.

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
mport telebot
import time

TOKEN = '<tonke_string>'


def listener(*messages):
    for m in messages:
        chatid = m.chat.id
        text = m.text
        tb.send_message(chatid, text)


tb = telebot.TeleBot(TOKEN)
tb.get_update()  # cache exist message
tb.set_update_listener(listener)
tb.polling(3)
while True:
    time.sleep(20)
```
