"""
In this example you will learn how to adapt your bot to different languages
Using built-in class I18N.
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

from telebot import TeleBot, types, custom_filters
from telebot import apihelper
from telebot.storage.memory_storage import StateMemoryStorage

import keyboards
from i18n_class import I18N

apihelper.ENABLE_MIDDLEWARE = True
storage = StateMemoryStorage()
# IMPORTANT! This example works only if polling is non-threaded.
bot = TeleBot("", state_storage=storage, threaded=False)

i18n = I18N(translations_path='locales', domain_name='messages')
_ = i18n.gettext  # for singular translations
__ = i18n.ngettext  # for plural translations

# These are example storages, do not use it in a production development
users_lang = {}
users_clicks = {}


@bot.middleware_handler(update_types=['message', 'callback_query'])
def set_contex_language(bot_instance, message):
    i18n.context_lang.language = users_lang.get(message.from_user.id, 'en')


@bot.message_handler(commands=['start'])
def start_handler(message: types.Message):
    text = _("Hello, {user_fist_name}!\n"
             "This is the example of multilanguage bot.\n"
             "Available commands:\n\n"
             "/lang - change your language\n"
             "/plural - pluralization example")

    # remember don't use f string for interpolation, use .format method instead
    text = text.format(user_fist_name=message.from_user.first_name)
    bot.send_message(message.from_user.id, text)


@bot.message_handler(commands=['lang'])
def change_language_handler(message: types.Message):
    bot.send_message(message.chat.id, "Choose language\nВыберите язык\nTilni tanlang",
                     reply_markup=keyboards.languages_keyboard())


@bot.callback_query_handler(func=None, text=custom_filters.TextFilter(contains=['en', 'ru', 'uz_Latn']))
def language_handler(call: types.CallbackQuery):
    lang = call.data
    users_lang[call.from_user.id] = lang

    # When you change user's language, pass language explicitly coz it's not changed in context
    bot.edit_message_text(_("Language has been changed", lang=lang), call.from_user.id, call.message.id)
    bot.delete_state(call.from_user.id)


@bot.message_handler(commands=['plural'])
def pluralization_handler(message: types.Message):
    if not users_clicks.get(message.from_user.id):
        users_clicks[message.from_user.id] = 0
    clicks = users_clicks[message.from_user.id]

    text = __(
        singular="You have {number} click",
        plural="You have {number} clicks",
        n=clicks,
    )
    text = _("This is clicker.\n\n") + text.format(number=clicks)
    bot.send_message(message.chat.id, text, reply_markup=keyboards.clicker_keyboard(_))


@bot.callback_query_handler(func=None, text=custom_filters.TextFilter(equals='click'))
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


if __name__ == '__main__':
    bot.add_custom_filter(custom_filters.TextMatchFilter())
    bot.infinity_polling()
