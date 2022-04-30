"""
Markdown & HTML formatting functions.

.. versionadded:: 4.5.1
"""

import html
import re


def format_text(*args, separator="\n"):
    """
    Formats a list of strings into a single string.

    .. code:: python

        format_text( # just an example
            mbold('Hello'),
            mitalic('World')
        )

    :param args: Strings to format.
    :param separator: The separator to use between each string.
    """
    return separator.join(args)



def escape_html(content: str) -> str:
    """
    Escapes HTML characters in a string of HTML.

    :param content: The string of HTML to escape.
    """
    return html.escape(content)


def escape_markdown(content: str) -> str:
    """
    Escapes Markdown characters in a string of Markdown.

    Credits: simonsmh

    :param content: The string of Markdown to escape.
    """
    
    parse = re.sub(r"([_*\[\]()~`>\#\+\-=|\.!])", r"\\\1", content)
    reparse = re.sub(r"\\\\([_*\[\]()~`>\#\+\-=|\.!])", r"\1", parse)
    return reparse 


def mbold(content: str, escape: bool=False) -> str:
    """
    Returns a Markdown-formatted bold string.

    :param content: The string to bold.
    :param escape: True if you need to escape special characters.
    """
    return '*{}*'.format(escape_markdown(content) if escape else content)


def hbold(content: str, escape: bool=False) -> str:
    """
    Returns an HTML-formatted bold string.

    :param content: The string to bold.
    :param escape: True if you need to escape special characters.
    """
    return '<b>{}</b>'.format(escape_html(content) if escape else content)


def mitalic(content: str, escape: bool=False) -> str:
    """
    Returns a Markdown-formatted italic string.

    :param content: The string to italicize.
    :param escape: True if you need to escape special characters.
    """
    return '_{}_\r'.format(escape_markdown(content) if escape else content)


def hitalic(content: str, escape: bool=False) -> str:
    """
    Returns an HTML-formatted italic string.

    :param content: The string to italicize.
    :param escape: True if you need to escape special characters.
    """
    return '<i>{}</i>'.format(escape_html(content) if escape else content)


def munderline(content: str, escape: bool=False) -> str:
    """
    Returns a Markdown-formatted underline string.

    :param content: The string to underline.
    :param escape: True if you need to escape special characters.
    """
    return '__{}__'.format(escape_markdown(content) if escape else content)


def hunderline(content: str, escape: bool=False) -> str:
    """
    Returns an HTML-formatted underline string.

    :param content: The string to underline.
    :param escape: True if you need to escape special characters.
    """
    return '<u>{}</u>'.format(escape_html(content) if escape else content)


def mstrikethrough(content: str, escape: bool=False) -> str:
    """
    Returns a Markdown-formatted strikethrough string.

    :param content: The string to strikethrough.
    :param escape: True if you need to escape special characters.
    """
    return '~{}~'.format(escape_markdown(content) if escape else content)


def hstrikethrough(content: str, escape: bool=False) -> str:
    """
    Returns an HTML-formatted strikethrough string.

    :param content: The string to strikethrough.
    :param escape: True if you need to escape special characters.
    """
    return '<s>{}</s>'.format(escape_html(content) if escape else content)


def mspoiler(content: str, escape: bool=False) -> str:
    """
    Returns a Markdown-formatted spoiler string.

    :param content: The string to spoiler.
    :param escape: True if you need to escape special characters.
    """
    return '||{}||'.format(escape_markdown(content) if escape else content)


def hspoiler(content: str, escape: bool=False) -> str:
    """
    Returns an HTML-formatted spoiler string.

    :param content: The string to spoiler.
    :param escape: True if you need to escape special characters.
    """
    return '<tg-spoiler>{}</tg-spoiler>'.format(escape_html(content) if escape else content)


def mlink(content: str, url: str, escape: bool=False) -> str:
    """
    Returns a Markdown-formatted link string.

    :param content: The string to link.
    :param url: The URL to link to.
    :param escape: True if you need to escape special characters.
    """
    return '[{}]({})'.format(escape_markdown(content), escape_markdown(url) if escape else content)


def hlink(content: str, url: str, escape: bool=False) -> str:
    """
    Returns an HTML-formatted link string.

    :param content: The string to link.
    :param url: The URL to link to.
    :param escape: True if you need to escape special characters.
    """
    return '<a href="{}">{}</a>'.format(escape_html(url), escape_html(content) if escape else content)


def mcode(content: str, language: str="", escape: bool=False) -> str:
    """
    Returns a Markdown-formatted code string.

    :param content: The string to code.
    :param escape: True if you need to escape special characters.
    """
    return '```{}\n{}```'.format(language, escape_markdown(content) if escape else content)


def hcode(content: str, escape: bool=False) -> str:
    """
    Returns an HTML-formatted code string.

    :param content: The string to code.
    :param escape: True if you need to escape special characters.
    """
    return '<code>{}</code>'.format(escape_html(content) if escape else content)


def hpre(content: str, escape: bool=False, language: str="") -> str:
    """
    Returns an HTML-formatted preformatted string.

    :param content: The string to preformatted.
    :param escape: True if you need to escape special characters.
    """
    return '<pre><code class="{}">{}</code></pre>'.format(language, escape_html(content) if escape else content)