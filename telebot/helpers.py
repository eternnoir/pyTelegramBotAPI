from typing import Any

from telebot import types, util


def user_link(user: types.User, include_id: bool = False) -> str:
    """
    Returns an HTML user link. This is useful for reports.
    Attention: Don't forget to set parse_mode to 'HTML'!

    Example:
    bot.send_message(your_user_id, user_link(message.from_user) + ' started the bot!', parse_mode='HTML')

    :param user: the user (not the user_id)
    :param include_id: include the user_id
    :return: HTML user link
    """
    name = util.escape(user.first_name)
    return f"<a href='tg://user?id={user.id}'>{name}</a>" + (f" (<pre>{user.id}</pre>)" if include_id else "")


def quick_markup(values: dict[str, dict[str, Any]], row_width: int = 2) -> types.InlineKeyboardMarkup:
    """
    Returns a reply markup from a dict in this format: {'text': kwargs}
    This is useful to avoid always typing 'btn1 = InlineKeyboardButton(...)' 'btn2 = InlineKeyboardButton(...)'

    Example:

    .. code-block:: python

        quick_markup({
            'Twitter': {'url': 'https://twitter.com'},
            'Facebook': {'url': 'https://facebook.com'},
            'Back': {'callback_data': 'whatever'}
        }, row_width=2):
            # returns an InlineKeyboardMarkup with two buttons in a row, one leading to Twitter, the other to facebook
            # and a back button below

        # kwargs can be:
        {
            'url': None,
            'callback_data': None,
            'switch_inline_query': None,
            'switch_inline_query_current_chat': None,
            'callback_game': None,
            'pay': None,
            'login_url': None,
            'web_app': None
        }

    :param values: a dict containing all buttons to create in this format: {text: kwargs} {str:}
    :param row_width: int row width
    :return: InlineKeyboardMarkup
    """
    markup = types.InlineKeyboardMarkup(row_width=row_width)
    buttons = [types.InlineKeyboardButton(text=text, **kwargs) for text, kwargs in values.items()]
    markup.add(*buttons)
    return markup
