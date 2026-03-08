"""
Markdown & HTML formatting functions.
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


# noinspection RegExpRedundantEscape
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
    return '[{}]({})'.format(escape_markdown(content), escape_markdown(url) if escape else url)


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

    :param language: The programming language of the code. Defaults to an empty string.
    :type language: :obj:`str`

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

    :param language: The programming language of the code. Defaults to an empty string.
    :type language: :obj:`str`

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


def mcite(content: str, escape: Optional[bool] = True, expandable: Optional[bool] = False) -> str:
    """
    Returns a Markdown-formatted block-quotation string.

    :param content: The string to bold.
    :type content: :obj:`str`

    :param escape: True if you need to escape special characters. Defaults to True.
    :type escape: :obj:`bool`

    :param expandable: True if you need the quote to be expandable. Defaults to False.
    :type expandable: :obj:`bool`

    :return: The formatted string.
    :rtype: :obj:`str`
    """
    content = escape_markdown(content) if escape else content
    content = "\n".join([">" + line for line in content.split("\n")])
    if expandable:
        return f"**{content}||"
    return content


def hcite(content: str, escape: Optional[bool] = True, expandable: Optional[bool] = False) -> str:
    """
    Returns a html-formatted block-quotation string.

    :param content: The string to bold.
    :type content: :obj:`str`

    :param escape: True if you need to escape special characters. Defaults to True.
    :type escape: :obj:`bool`

    :param expandable: True if you need the quote to be expandable. Defaults to False.
    :type expandable: :obj:`bool`

    :return: The formatted string.
    :rtype: :obj:`str`
    """
    return "<blockquote{}>{}</blockquote>".format(
        " expandable" if expandable else "",
        escape_html(content) if escape else content,
    )


def apply_html_entities(text: str, entities: Optional[List]=None, custom_subs: Optional[Dict[str, str]]=None) -> str:
    """
    Apply HTML formatting to text based on provided entities.
    Handles nested and overlapping entities correctly.
    """
    if not entities:
        return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

    _subs = {
        "bold": "<b>{text}</b>",
        "italic": "<i>{text}</i>",
        "pre": "<pre>{text}</pre>",
        "code": "<code>{text}</code>",
        "text_link": "<a href=\"{url}\">{text}</a>",
        "strikethrough": "<s>{text}</s>",
        "underline": "<u>{text}</u>",
        "spoiler": "<span class=\"tg-spoiler\">{text}</span>",
        "custom_emoji": "<tg-emoji emoji-id=\"{custom_emoji_id}\">{text}</tg-emoji>",
        "date_time": "<tg-time unix=\"{unix_time}\" format=\"{date_time_format}\">{text}</tg-time>",
        "blockquote": "<blockquote>{text}</blockquote>",
        "expandable_blockquote": "<blockquote expandable>{text}</blockquote>",
    }

    if custom_subs:
        for key, value in custom_subs.items():
            _subs[key] = value

    # Sort entities by offset (starting position), with longer entities first for equal offsets
    sorted_entities = sorted(entities, key=lambda e: (e.offset, -e.length))

    # Convert text to utf-16 encoding for proper handling
    utf16_text = text.encode("utf-16-le")

    def escape_entity(text_part):
        """Escape HTML special characters in a text part"""
        if isinstance(text_part, bytes):
            text_part = text_part.decode("utf-16-le")
        return text_part.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

    def format_entity(entity, content):
        """Apply entity formatting to the content"""
        entity_type = entity.type

        # Handle different entity types
        if entity_type == "text_mention" and hasattr(entity, 'user'):
            return f"<a href=\"tg://user?id={entity.user.id}\">{content}</a>"
        # elif entity_type == "mention":   # No need to do this, @username works fine
        #     username = content[1:]  # Remove @ symbol
        #     return f"<a href=\"https://t.me/{username}\">{content}</a>"
        elif entity_type == "text_link" and hasattr(entity, 'url'):
            return _subs["text_link"].format(url=entity.url, text=content)
        elif entity_type == "custom_emoji" and hasattr(entity, 'custom_emoji_id'):
            return _subs["custom_emoji"].format(custom_emoji_id=entity.custom_emoji_id, text=content)
        elif entity_type == "date_time" and hasattr(entity, 'unix_time') and hasattr(entity, 'date_time_format'):
            return _subs["date_time"].format(unix=entity.unix_time, date_time_format=entity.date_time_format, text=content)
        elif entity_type == "pre" and hasattr(entity, 'language') and entity.language:
            return f"<pre><code class=\"language-{entity.language}\">{content}</code></pre>"
        elif entity_type in _subs:
            template = _subs[entity_type]
            return template.format(text=content)

        # If no matching entity type, return text as is
        return content

    def process_entities(byte_text, entity_list, start_pos=0, end_pos=None):
        if end_pos is None:
            end_pos = len(byte_text)

        if not entity_list or start_pos >= end_pos:
            return escape_entity(byte_text[start_pos:end_pos])

        current_entity = entity_list[0]
        current_start = current_entity.offset * 2
        current_end = current_start + current_entity.length * 2

        if current_end <= start_pos or current_start >= end_pos:
            return escape_entity(byte_text[start_pos:end_pos])

        result = []

        if current_start > start_pos:
            result.append(escape_entity(byte_text[start_pos:current_start]))

        nested_entities = []
        remaining_entities = []

        for entity in entity_list[1:]:
            entity_start = entity.offset * 2
            # entity_end = entity_start + entity.length * 2

            if current_start <= entity_start < current_end:
                nested_entities.append(entity)
            else:
                remaining_entities.append(entity)

        if nested_entities:
            inner_content = process_entities(
                byte_text,
                nested_entities,
                current_start,
                current_end
            )
        else:
            inner_content = escape_entity(byte_text[current_start:current_end])

        result.append(format_entity(current_entity, inner_content))

        if current_end < end_pos and remaining_entities:
            result.append(process_entities(
                byte_text,
                remaining_entities,
                current_end,
                end_pos
            ))
        elif current_end < end_pos:
            result.append(escape_entity(byte_text[current_end:end_pos]))

        return "".join(result)

    html_result = process_entities(utf16_text, sorted_entities)

    return html_result
