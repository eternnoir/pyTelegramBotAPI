"""
Markdown & HTML formatting functions.

.. versionadded:: 4.5.1
"""

import html

import re

from typing import Optional


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
    
    parse = re.sub(r"([_*\[\]()~`>\#\+\-=|\.!])", r"\\\1", content)
    reparse = re.sub(r"\\\\([_*\[\]()~`>\#\+\-=|\.!])", r"\1", parse)
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