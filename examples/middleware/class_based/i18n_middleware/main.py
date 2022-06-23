"""
In this example you will learn how to adapt your bot to different languages
Using built-in middleware I18N.

You need to install babel package 'https://pypi.org/project/Babel/'
Babel provides a command-line interface for working with message catalogs
After installing babel package you have a script called 'pybabel'
Too see all the commands open terminal and type 'pybabel --help'
Full description for pybabel commands can be found here: 'https://babel.pocoo.org/en/latest/cmdline.html'

Create a directory 'locales' where our translations will be stored

First we need to extract texts:
    pybabel extract -o locales/{domain_name}.pot --input-dirs .
{domain_name}.pot - is the file where all translations are saved
The name of this file should be the same as domain which you pass to I18N class
In this example domain_name will be 'messages'

For gettext (singular texts) we use '_' alias and it works perfect
You may also you some alias for ngettext (plural texts) but you can face with a problem that
your plural texts are not being extracted
That is because by default 'pybabel extract' recognizes the following keywords:
 _, gettext, ngettext, ugettext, ungettext, dgettext, dngettext, N_
To add your own keyword you can use '-k' flag
In this example for 'ngettext' i will assign double underscore alias '__'

Full command with pluralization support will look so:
    pybabel extract -o locales/{domain_name}.pot -k __:1,2 --input-dirs .

Then create directories with translations (get list of all locales: 'pybabel --list-locales'):
    pybabel init -i locales/{domain_name}.pot -d locales -l en
    pybabel init -i locales/{domain_name}.pot -d locales -l ru
    pybabel init -i locales/{domain_name}.pot -d locales -l uz_Latn

Now you can translate the texts located in locales/{language}/LC_MESSAGES/{domain_name}.po
After you translated all the texts you need to compile .po files:
    pybabel compile -d locales

When you delete/update your texts you also need to update them in .po files:
    pybabel extract -o locales/{domain_name}.pot -k __:1,2 --input-dirs .
    pybabel update -i locales/{domain_name}.pot -d locales
    - translate
    pybabel compile -d locales

If you have any exceptions check:
    - you have installed babel
    - translations are ready, so you just compiled it
    - in the commands above you replaced {domain_name} to messages
    - you are writing commands from correct path in terminal
"""

import asyncio
from typing import Union

import keyboards
from i18n_base_middleware import I18N
from telebot import TeleBot
from telebot import types, StateMemoryStorage
from telebot.custom_filters import TextMatchFilter, TextFilter

class I18NMiddleware(I18N):

    def process_update_types(self) -> list:
        """
        Here you need to return a list of update types which you want to be processed
        """
        return ['message', 'callback_query']

    def get_user_language(self, obj: Union[types.Message, types.CallbackQuery]):
        """
        This method is called when new update comes (only updates which you return in 'process_update_types' method)
        Returned language will be used in 'pre_process' method of parent class
        Returned language will be set to context language variable.
        If you need to get translation with user's actual language you don't have to pass it manually
        It will be automatically passed from context language value.
        However if you need some other language you can always pass it.
        """

        user_id = obj.from_user.id

        if user_id not in users_lang:
            users_lang[user_id] = 'en'

        return users_lang[user_id]


storage = StateMemoryStorage()
bot = TeleBot("", state_storage=storage, use_class_middlewares=True)

i18n = I18NMiddleware(translations_path='locales', domain_name='messages')
_ = i18n.gettext  # for singular translations
__ = i18n.ngettext  # for plural translations

# These are example storages, do not use it in a production development
users_lang = {}
users_clicks = {}

@bot.message_handler(commands=['start'])
def start_handler(message: types.Message):
    text = _("Hello, {user_fist_name}!\n"
             "This is the example of multilanguage bot.\n"
             "Available commands:\n\n"
             "/lang - change your language\n"
             "/plural - pluralization example\n"
             "/menu - text menu example")

    # remember don't use f string for interpolation, use .format method instead
    text = text.format(user_fist_name=message.from_user.first_name)
    bot.send_message(message.from_user.id, text)


@bot.message_handler(commands=['lang'])
def change_language_handler(message: types.Message):
    bot.send_message(message.chat.id, "Choose language\nВыберите язык\nTilni tanlang",
                     reply_markup=keyboards.languages_keyboard())


@bot.callback_query_handler(func=None, text=TextFilter(contains=['en', 'ru', 'uz_Latn']))
def language_handler(call: types.CallbackQuery):
    lang = call.data
    users_lang[call.from_user.id] = lang

    # When you changed user language, you have to pass it manually beacause it is not changed in context
    bot.edit_message_text(_("Language has been changed", lang=lang), call.from_user.id, call.message.id)


@bot.message_handler(commands=['plural'])
def pluralization_handler(message: types.Message):
    if not users_clicks.get(message.from_user.id):
        users_clicks[message.from_user.id] = 0
    clicks = users_clicks[message.from_user.id]

    text = __(
        singular="You have {number} click",
        plural="You have {number} clicks",
        n=clicks
    )
    text = _("This is clicker.\n\n") + text.format(number=clicks)

    bot.send_message(message.chat.id, text, reply_markup=keyboards.clicker_keyboard(_))


@bot.callback_query_handler(func=None, text=TextFilter(equals='click'))
def click_handler(call: types.CallbackQuery):
    if not users_clicks.get(call.from_user.id):
        users_clicks[call.from_user.id] = 1
    else:
        users_clicks[call.from_user.id] += 1

    clicks = users_clicks[call.from_user.id]

    text = __(
        singular="You have {number} click",
        plural="You have {number} clicks",
        n=clicks
    )
    text = _("This is clicker.\n\n") + text.format(number=clicks)

    bot.edit_message_text(text, call.from_user.id, call.message.message_id,
                          reply_markup=keyboards.clicker_keyboard(_))


@bot.message_handler(commands=['menu'])
def menu_handler(message: types.Message):
    text = _("This is ReplyKeyboardMarkup menu example in multilanguage bot.")
    bot.send_message(message.chat.id, text, reply_markup=keyboards.menu_keyboard(_))


# For lazy tranlations
# lazy gettext is used when you don't know user's locale
# It can be used for example to handle text buttons in multilanguage bot
# The actual translation will be delayed until update comes and context language is set
l_ = i18n.lazy_gettext


# Handlers below will handle text according to user's language
@bot.message_handler(text=l_("My user id"))
def return_user_id(message: types.Message):
    bot.send_message(message.chat.id, str(message.from_user.id))


@bot.message_handler(text=l_("My user name"))
def return_user_id(message: types.Message):
    username = message.from_user.username
    if not username:
        username = '-'
    bot.send_message(message.chat.id, username)


# You can make it case-insensitive
@bot.message_handler(text=TextFilter(equals=l_("My first name"), ignore_case=True))
def return_user_id(message: types.Message):
    bot.send_message(message.chat.id, message.from_user.first_name)


all_menu_texts = []
for language in i18n.available_translations:
    for menu_text in ("My user id", "My user name", "My first name"):
        all_menu_texts.append(_(menu_text, language))


# When user confused language. (handles all menu buttons texts)
@bot.message_handler(text=TextFilter(contains=all_menu_texts, ignore_case=True))
def missed_message(message: types.Message):
    bot.send_message(message.chat.id, _("Seems you confused language"), reply_markup=keyboards.menu_keyboard(_))


if __name__ == '__main__':
    bot.setup_middleware(i18n)
    bot.add_custom_filter(TextMatchFilter())
    asyncio.run(bot.infinity_polling())
