# pyTelegramBotAPI
Python Telegram bot api.

## Example

```python
import telebot

TOKEN = '<token string>'

tb = telebot.TeleBot(TOKEN)
# tb.send_message(chatid,message)
print tb.send_message(281281, 'gogo power ranger')
```
