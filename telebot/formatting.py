"""
Markdown & HTML formatting functions.

.. versionadded:: 4.5.1
"""

import re
import html
from typing import Optional, List, Dict


def format_text(*args, separator="\n"):
    """
    Formats a list of strings into a single string.

    .. code:: python3

        format_text( # just an example
            mbold('Hello'),
            mitalic('World')
        )

    :param args: Strings to format.
    :type args: :obj:`str`

    :param separator: The separator to use between each string.
    :type separator: :obj:`str`

    :return: The formatted string.
    :rtype: :obj:`str`
    """
    return separator.join(args)


def escape_html(content: str) -> str:
    """
    Escapes HTML characters in a string of HTML.

    :param content: The string of HTML to escape.
    :type content: :obj:`str`

    :return: The escaped string.
    :rtype: :obj:`str`
    """
    return html.escape(content)


def escape_markdown(content: str) -> str:
    """
    Escapes Markdown characters in a string of Markdown.

    Credits to: simonsmh

    :param content: The string of Markdown to escape.
    :type content: :obj:`str`

    :return: The escaped string.
    :rtype: :obj:`str`
    """
    
    parse = re.sub(r"([_*\[\]()~`>\#\+\-=|\.!\{\}\\])", r"\\\1", content)
    reparse = re.sub(r"\\\\([_*\[\]()~`>\#\+\-=|\.!\{\}\\])", r"\1", parse)
    return reparse


def mbold(content: str, escape: Optional[bool]=True) -> str:
    """
    Returns a Markdown-formatted bold string.

    :param content: The string to bold.
    :type content: :obj:`str`

    :param escape: True if you need to escape special characters. Defaults to True.
    :type escape: :obj:`bool`

    :return: The formatted string.
    :rtype: :obj:`str`
    """
    return '*{}*'.format(escape_markdown(content) if escape else content)


def hbold(content: str, escape: Optional[bool]=True) -> str:
    """
    Returns an HTML-formatted bold string.

    :param content: The string to bold.
    :type content: :obj:`str`

    :param escape: True if you need to escape special characters. Defaults to True.
    :type escape: :obj:`bool`

    :return: The formatted string.
    :rtype: :obj:`str`
    """
    return '<b>{}</b>'.format(escape_html(content) if escape else content)


def mitalic(content: str, escape: Optional[bool]=True) -> str:
    """
    Returns a Markdown-formatted italic string.

    :param content: The string to italicize.
    :type content: :obj:`str`

    :param escape: True if you need to escape special characters. Defaults to True.
    :type escape: :obj:`bool`

    :return: The formatted string.
    :rtype: :obj:`str`
    """
    return '_{}_\r'.format(escape_markdown(content) if escape else content)


def hitalic(content: str, escape: Optional[bool]=True) -> str:
    """
    Returns an HTML-formatted italic string.

    :param content: The string to italicize.
    :type content: :obj:`str`

    :param escape: True if you need to escape special characters. Defaults to True.
    :type escape: :obj:`bool`

    :return: The formatted string.
    :rtype: :obj:`str`
    """
    return '<i>{}</i>'.format(escape_html(content) if escape else content)


def munderline(content: str, escape: Optional[bool]=True) -> str:
    """
    Returns a Markdown-formatted underline string.

    :param content: The string to underline.
    :type content: :obj:`str`

    :param escape: True if you need to escape special characters. Defaults to True.
    :type escape: :obj:`bool`

    :return: The formatted string.
    :rtype: :obj:`str`
    """
    return '__{}__'.format(escape_markdown(content) if escape else content)


def hunderline(content: str, escape: Optional[bool]=True) -> str:
    """
    Returns an HTML-formatted underline string.

    :param content: The string to underline.
    :type content: :obj:`str`

    :param escape: True if you need to escape special characters. Defaults to True.
    :type escape: :obj:`bool`

    :return: The formatted string.
    :rtype: :obj:`str`

    """
    return '<u>{}</u>'.format(escape_html(content) if escape else content)


def mstrikethrough(content: str, escape: Optional[bool]=True) -> str:
    """
    Returns a Markdown-formatted strikethrough string.

    :param content: The string to strikethrough.
    :type content: :obj:`str`

    :param escape: True if you need to escape special characters. Defaults to True.
    :type escape: :obj:`bool`

    :return: The formatted string.
    :rtype: :obj:`str`
    """
    return '~{}~'.format(escape_markdown(content) if escape else content)


def hstrikethrough(content: str, escape: Optional[bool]=True) -> str:
    """
    Returns an HTML-formatted strikethrough string.

    :param content: The string to strikethrough.
    :type content: :obj:`str`

    :param escape: True if you need to escape special characters. Defaults to True.
    :type escape: :obj:`bool`

    :return: The formatted string.
    :rtype: :obj:`str`
    """
    return '<s>{}</s>'.format(escape_html(content) if escape else content)


def mspoiler(content: str, escape: Optional[bool]=True) -> str:
    """
    Returns a Markdown-formatted spoiler string.

    :param content: The string to spoiler.
    :type content: :obj:`str`

    :param escape: True if you need to escape special characters. Defaults to True.
    :type escape: :obj:`bool`

    :return: The formatted string.
    :rtype: :obj:`str`
    """
    return '||{}||'.format(escape_markdown(content) if escape else content)


def hspoiler(content: str, escape: Optional[bool]=True) -> str:
    """
    Returns an HTML-formatted spoiler string.

    :param content: The string to spoiler.
    :type content: :obj:`str`

    :param escape: True if you need to escape special characters. Defaults to True.
    :type escape: :obj:`bool`

    :return: The formatted string.
    :rtype: :obj:`str`
    """
    return '<tg-spoiler>{}</tg-spoiler>'.format(escape_html(content) if escape else content)


def mlink(content: str, url: str, escape: Optional[bool]=True) -> str:
    """
    Returns a Markdown-formatted link string.

    :param content: The string to link.
    :type content: :obj:`str`

    :param url: The URL to link to.
    :type url: str

    :param escape: True if you need to escape special characters. Defaults to True.
    :type escape: :obj:`bool`

    :return: The formatted string.
    :rtype: :obj:`str`
    """
    return '[{}]({})'.format(escape_markdown(content), escape_markdown(url) if escape else content)


def hlink(content: str, url: str, escape: Optional[bool]=True) -> str:
    """
    Returns an HTML-formatted link string.

    :param content: The string to link.
    :type content: :obj:`str`

    :param url: The URL to link to.
    :type url: :obj:`str`

    :param escape: True if you need to escape special characters. Defaults to True.
    :type escape: :obj:`bool`

    :return: The formatted string.
    :rtype: :obj:`str`
    """
    return '<a href="{}">{}</a>'.format(escape_html(url), escape_html(content) if escape else content)


def mcode(content: str, language: str="", escape: Optional[bool]=True) -> str:
    """
    Returns a Markdown-formatted code string.

    :param content: The string to code.
    :type content: :obj:`str`

    :param escape: True if you need to escape special characters. Defaults to True.
    :type escape: :obj:`bool`

    :return: The formatted string.
    :rtype: :obj:`str`
    """
    return '```{}\n{}```'.format(language, escape_markdown(content) if escape else content)


def hcode(content: str, escape: Optional[bool]=True) -> str:
    """
    Returns an HTML-formatted code string.

    :param content: The string to code.
    :type content: :obj:`str`

    :param escape: True if you need to escape special characters. Defaults to True.
    :type escape: :obj:`bool`

    :return: The formatted string.
    :rtype: :obj:`str`
    """
    return '<code>{}</code>'.format(escape_html(content) if escape else content)


def hpre(content: str, escape: Optional[bool]=True, language: str="") -> str:
    """
    Returns an HTML-formatted preformatted string.

    :param content: The string to preformatted.
    :type content: :obj:`str`

    :param escape: True if you need to escape special characters. Defaults to True.
    :type escape: :obj:`bool`

    :return: The formatted string.
    :rtype: :obj:`str`
    """
    return '<pre><code class="{}">{}</code></pre>'.format(language, escape_html(content) if escape else content)


def hide_link(url: str) -> str:
    """
    Hide url of an image.

    :param url: The url of the image.
    :type url: :obj:`str`
    
    :return: The hidden url.
    :rtype: :obj:`str`
    """
    return f'<a href="{url}">&#8288;</a>'


def mcite(content: str, escape: Optional[bool]=True) -> str:
    """
    Returns a Markdown-formatted block-quotation string.

    :param content: The string to bold.
    :type content: :obj:`str`

    :param escape: True if you need to escape special characters. Defaults to True.
    :type escape: :obj:`bool`

    :return: The formatted string.
    :rtype: :obj:`str`
    """
    content = escape_markdown(content) if escape else content
    content = '\n'.join(['>' + line for line in content.split('\n')])
    return content


def hcite(content: str, escape: Optional[bool]=True) -> str:
    """
    Returns a html-formatted block-quotation string.

    :param content: The string to bold.
    :type content: :obj:`str`

    :param escape: True if you need to escape special characters. Defaults to True.
    :type escape: :obj:`bool`
    
    :return: The formatted string.
    :rtype: :obj:`str`
    """
    return '<blockquote>{}</blockquote>'.format(escape_html(content) if escape else content)


def apply_html_entities(text: str, entities: Optional[List], custom_subs: Optional[Dict[str, str]]) -> str:
    """
    Author: @sviat9440
    Updaters: @badiboy, @EgorKhabarov
    Message: "*Test* parse _formatting_, [url](https://example.com), [text_mention](tg://user?id=123456) and mention @username"

    .. code-block:: python3
        :caption: Example:

        apply_html_entities(text, entities)
        >> "<b>Test</b> parse <i>formatting</i>, <a href=\"https://example.com\">url</a>, <a href=\"tg://user?id=123456\">text_mention</a> and mention @username"

    Custom subs:
        You can customize the substitutes. By default, there is no substitute for the entities: hashtag, bot_command, email. You can add or modify substitute an existing entity.
    .. code-block:: python3
        :caption: Example:

        apply_html_entities(
            text,
            entities,
            {"bold": "<strong class=\"example\">{text}</strong>", "italic": "<i class=\"example\">{text}</i>", "mention": "<a href={url}>{text}</a>"},
        )
        >> "<strong class=\"example\">Test</strong> parse <i class=\"example\">formatting</i>, <a href=\"https://example.com\">url</a> and <a href=\"tg://user?id=123456\">text_mention</a> and mention <a href=\"https://t.me/username\">@username</a>"
    """

    if not entities:
        return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

    _subs = {
        "bold": "<b>{text}</b>",
        "italic": "<i>{text}</i>",
        "pre": "<pre>{text}</pre>",
        "code": "<code>{text}</code>",
        # "url": "<a href=\"{url}\">{text}</a>", # @badiboy plain URLs have no text and do not need tags
        "text_link": "<a href=\"{url}\">{text}</a>",
        "strikethrough": "<s>{text}</s>",
        "underline": "<u>{text}</u>",
        "spoiler": "<span class=\"tg-spoiler\">{text}</span>",
        "custom_emoji": "<tg-emoji emoji-id=\"{custom_emoji_id}\">{text}</tg-emoji>",
        "blockquote": "<blockquote>{text}</blockquote>",
        "expandable_blockquote": "<blockquote expandable>{text}</blockquote>",

    }

    if custom_subs:
        for key, value in custom_subs.items():
            _subs[key] = value
    utf16_text = text.encode("utf-16-le")
    html_text = ""

    def func(upd_text, subst_type=None, url=None, user=None, custom_emoji_id=None):
        upd_text = upd_text.decode("utf-16-le")
        if subst_type == "text_mention":
            subst_type = "text_link"
            url = "tg://user?id={0}".format(user.id)
        elif subst_type == "mention":
            url = "https://t.me/{0}".format(upd_text[1:])
        upd_text = upd_text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        if not subst_type or not _subs.get(subst_type):
            return upd_text
        subs = _subs.get(subst_type)
        if subst_type == "custom_emoji":
            return subs.format(text=upd_text, custom_emoji_id=custom_emoji_id)
        return subs.format(text=upd_text, url=url)

    offset = 0
    start_index = 0
    end_index = 0
    for entity in entities:
        if entity.offset > offset:
            # when the offset is not 0: for example, a __b__
            # we need to add the text before the entity to the html_text
            html_text += func(utf16_text[offset * 2: entity.offset * 2])
            offset = entity.offset

            new_string = func(utf16_text[offset * 2: (offset + entity.length) * 2], subst_type=entity.type,
                              url=entity.url, user=entity.user, custom_emoji_id=entity.custom_emoji_id)
            start_index = len(html_text)
            html_text += new_string
            offset += entity.length
            end_index = len(html_text)
        elif entity.offset == offset:
            new_string = func(utf16_text[offset * 2: (offset + entity.length) * 2], subst_type=entity.type,
                              url=entity.url, user=entity.user, custom_emoji_id=entity.custom_emoji_id)
            start_index = len(html_text)
            html_text += new_string
            end_index = len(html_text)
            offset += entity.length
        else:
            # Here we are processing nested entities.
            # We shouldn't update offset, because they are the same as entity before.
            # And, here we are replacing previous string with a new html-rendered text(previous string is already html-rendered,
            # And we don't change it).
            entity_string = html_text[start_index: end_index].encode("utf-16-le")
            formatted_string = func(entity_string, subst_type=entity.type, url=entity.url, user=entity.user,
                                    custom_emoji_id=entity.custom_emoji_id). \
                replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">")
            html_text = html_text[:start_index] + formatted_string + html_text[end_index:]
            end_index = len(html_text)

    if offset * 2 < len(utf16_text):
        html_text += func(utf16_text[offset * 2:])

    return html_text
