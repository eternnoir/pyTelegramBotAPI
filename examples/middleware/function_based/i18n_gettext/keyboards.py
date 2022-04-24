from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton


def languages_keyboard():
    return InlineKeyboardMarkup(
        keyboard=[
            [
                InlineKeyboardButton(text="English", callback_data='en'),
                InlineKeyboardButton(text="Русский", callback_data='ru'),
                InlineKeyboardButton(text="O'zbekcha", callback_data='uz_Latn')
            ]
        ]
    )


def clicker_keyboard(_):
    return InlineKeyboardMarkup(
        keyboard=[
            [
                InlineKeyboardButton(text=_("click"), callback_data='click'),
            ]
        ]
    )
