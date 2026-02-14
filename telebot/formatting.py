"""
Markdown & HTML formatting functions.
"""

import re
import html
from typing import Optional, List, Dict, Tuple


# Alternative message entities parsers. Can be:
# "deepseek" - deepseek version
# "gemini" - gemini version
# "chatgpt" - chatgpt version
# other values - original version
ENTITY_PASER_MODE = None


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
    if ENTITY_PASER_MODE == "deepseek":
        return apply_html_entities_ds(text, entities, custom_subs)
    elif ENTITY_PASER_MODE == "gemini":
        return apply_html_entities_gm(text, entities, custom_subs)
    elif ENTITY_PASER_MODE == "chatgpt":
        return apply_html_entities_cg(text, entities, custom_subs)

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
        "blockquote": "<blockquote>{text}</blockquote>",
        "expandable_blockquote": "<blockquote expandable>{text}</blockquote>",
    }

    if custom_subs:
        for key, value in custom_subs.items():
            _subs[key] = value
    utf16_text = text.encode("utf-16-le")
    html_text = ""

    def func(upd_text, subst_type=None, url=None, user=None, custom_emoji_id=None, language=None):
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
        elif (subst_type == "pre") and language:
            return "<pre><code class=\"language-{0}\">{1}</code></pre>".format(language, upd_text)
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
                              url=entity.url, user=entity.user, custom_emoji_id=entity.custom_emoji_id,
                              language=entity.language)
            start_index = len(html_text)
            html_text += new_string
            offset += entity.length
            end_index = len(html_text)
        elif entity.offset == offset:
            new_string = func(utf16_text[offset * 2: (offset + entity.length) * 2], subst_type=entity.type,
                              url=entity.url, user=entity.user, custom_emoji_id=entity.custom_emoji_id,
                              language=entity.language)
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
                                    custom_emoji_id=entity.custom_emoji_id,
                                    language=entity.language). \
                replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">")
            html_text = html_text[:start_index] + formatted_string + html_text[end_index:]
            end_index = len(html_text)

    if offset * 2 < len(utf16_text):
        html_text += func(utf16_text[offset * 2:])

    return html_text


#region DeepSeek vibecoding here
class EntityProcessor:
    """
    Handles parsing of text with message entities to HTML.
    """

    # Entity type to HTML template mapping
    ENTITY_TEMPLATES = {
        "bold": "<b>{text}</b>",
        "italic": "<i>{text}</i>",
        "pre": "<pre>{text}</pre>",
        "code": "<code>{text}</code>",
        "text_link": "<a href=\"{url}\">{text}</a>",
        "strikethrough": "<s>{text}</s>",
        "underline": "<u>{text}</u>",
        "spoiler": "<span class=\"tg-spoiler\">{text}</span>",
        "custom_emoji": "<tg-emoji emoji-id=\"{custom_emoji_id}\">{text}</tg-emoji>",
        "blockquote": "<blockquote>{text}</blockquote>",
        "expandable_blockquote": "<blockquote expandable>{text}</blockquote>",
    }

    def __init__(self, text: str, custom_subs: Optional[Dict[str, str]] = None):
        self.text = text
        self.utf16_mapping, self.char_to_units = self.utf16_code_units_to_indices(text)
        self.total_utf16_units = len(self.utf16_mapping)
        self.custom_subs = custom_subs

    def check_entity_exists(self, entity_type: str) -> bool:
        """
        Check if an entity type has a defined HTML template, considering custom substitutions.
        """
        return (entity_type in self.ENTITY_TEMPLATES) or (self.custom_subs and (entity_type in self.custom_subs))

    def get_entity_template(self, entity_type: str, default: Optional[str] = None) -> Optional[str]:
        """
        Get the HTML template for a given entity type, considering custom substitutions.
        """
        if entity_type in self.ENTITY_TEMPLATES:
            return self.ENTITY_TEMPLATES[entity_type]
        elif self.custom_subs and (entity_type in self.custom_subs):
            return self.custom_subs[entity_type]
        else:
            return default

    @staticmethod
    def utf16_code_units_to_indices(text: str) -> Tuple[List[int], List[int]]:
        """
        Convert UTF-16 code unit positions to Python string indices.

        Returns:
            - code_unit_to_char_idx: Mapping from UTF-16 code unit position to character index
            - char_idx_to_code_units: Number of UTF-16 code units per character
        """
        code_unit_to_char_idx = []
        char_idx_to_code_units = []

        code_unit_pos = 0
        for char_idx, char in enumerate(text):
            code_point = ord(char)
            # Characters outside BMP (U+10000 to U+10FFFF) use 2 UTF-16 code units
            if code_point >= 0x10000:
                code_units = 2
            else:
                code_units = 1

            # Map this code unit position to character index
            for _ in range(code_units):
                code_unit_to_char_idx.append(char_idx)

            char_idx_to_code_units.append(code_units)
            code_unit_pos += code_units

        return code_unit_to_char_idx, char_idx_to_code_units

    def utf16_to_char_index(self, utf16_pos: int) -> int:
        """
        Convert UTF-16 code unit position to character index.
        """
        if utf16_pos >= len(self.utf16_mapping):
            return len(self.text)
        return self.utf16_mapping[utf16_pos]

    def get_entity_text(self, entity) -> str:  # entity: MessageEntity
        """
        Extract the text for an entity using UTF-16 code unit offsets.
        """
        start_char = self.utf16_to_char_index(entity.offset)
        end_char = self.utf16_to_char_index(entity.offset + entity.length)
        return self.text[start_char:end_char]

    def create_html_tag(self, entity, content: str) -> str:  # entity: MessageEntity
        """
        Create HTML tag for an entity with the given content.
        """
        entity_type = entity.type

        # if entity_type in self.ENTITY_TEMPLATES:
        #     template = self.ENTITY_TEMPLATES[entity_type]
        # elif self.custom_subs and (entity_type in self.custom_subs):
        #     template = self.custom_subs[entity_type]
        # else:
        #     # If no template is defined for this entity type, return the content as is
        #     return content
        template = self.get_entity_template(entity_type)
        if not template:
            return content

        # Prepare format arguments
        format_args = {"text": content}
        if entity_type == "text_link":
            format_args["url"] = escape_html(entity.url or "")
        elif entity_type == "custom_emoji":
            format_args["custom_emoji_id"] = entity.custom_emoji_id or ""

        return template.format(**format_args)

def apply_html_entities_ds(text: str, entities: Optional[List],           # entities: Optional[List[MessageEntity]]
                        custom_subs: Optional[Dict[str, str]] = None) -> str:
    """
    Parse text message to HTML code according to message entities.
    Properly handles UTF-16 code units for offsets and nested entities.

    Args:
        text: Plain text message
        entities: List of MessageEntity objects
        custom_subs: Optional custom substitutions (not used in this implementation)

    Returns:
        HTML formatted string
    """
    if not text:
        return text
    elif not entities:
        return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

    processor = EntityProcessor(text)

    # Sort entities by their position in the text
    # For proper nesting handling, we need to process from the end
    sorted_entities = sorted(entities, key=lambda e: e.offset, reverse=True)

    # Build a tree structure of entities
    # First, convert UTF-16 offsets to character indices for easier processing
    entity_ranges = []
    for entity in sorted_entities:
        # if entity.type in processor.ENTITY_TEMPLATES:
        #     pass
        # elif processor.custom_subs and (entity.type in processor.custom_subs):
        #     pass
        # else:
        #     continue
        if not processor.check_entity_exists(entity.type):
            continue

        start_char = processor.utf16_to_char_index(entity.offset)
        end_char = processor.utf16_to_char_index(entity.offset + entity.length)

        entity_ranges.append({
            'entity': entity,
            'start': start_char,
            'end': end_char,
            'type': entity.type,
            'processed': False
        })

    # Sort by start position (ascending) and then by length (descending)
    # This ensures parent entities come before children
    entity_ranges.sort(key=lambda x: (x['start'], -x['end']))

    # Build the HTML recursively
    def process_range(start_idx: int, end_idx: int, entities_in_range: List[dict]) -> str:
        """
        Recursively process a text range with its entities.
        """
        if not entities_in_range:
            return text[start_idx:end_idx]

        # Group entities by their start position
        result_parts = []
        current_pos = start_idx

        # Sort entities by their start position
        entities_in_range.sort(key=lambda x: x['start'])

        i = 0
        while i < len(entities_in_range):
            entity = entities_in_range[i]

            # Add text before this entity
            if entity['start'] > current_pos:
                result_parts.append(text[current_pos:entity['start']])

            # Find all entities that start at the same position or are nested within
            nested_entities = []
            j = i
            while j < len(entities_in_range) and entities_in_range[j]['start'] < entity['end']:
                if entities_in_range[j]['start'] >= entity['start']:
                    nested_entities.append(entities_in_range[j])
                j += 1

            # Filter entities that are actually within this entity's range
            nested_entities = [e for e in nested_entities if
                               e['start'] >= entity['start'] and e['end'] <= entity['end']]

            # Process the content of this entity (including nested entities)
            content = process_range(entity['start'], entity['end'],
                                    [e for e in nested_entities if e != entity])

            # Apply this entity's HTML tag
            html_content = processor.create_html_tag(entity['entity'], content)
            result_parts.append(html_content)

            # Move current position to the end of this entity
            current_pos = entity['end']
            i = j

        # Add remaining text
        if current_pos < end_idx:
            result_parts.append(text[current_pos:end_idx])

        return ''.join(result_parts)

    # Process the entire text
    return process_range(0, len(text), entity_ranges)
#endregion

#region Gemini vibecoding here
# import sys
# import html
# from typing import List, Optional, Dict

# 2. Main Function
def apply_html_entities_gm(
        text: str,
        entities: Optional[List],   # entities: Optional[List[MessageEntity]]
        custom_subs: Optional[Dict[str, str]] = None
) -> str:
    # if not entities:
    #     return html.escape(text)
    if not text:
        return text
    elif not entities:
        return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

    # --- Step 1: Map UTF-16 offsets to Python String Indices ---
    # Telegram API uses UTF-16 code units for offsets/length.
    # Python strings are indexed by Unicode code points.
    # We need to map: utf16_offset -> python_string_index

    # Identify all 'significant' UTF-16 boundaries we care about (start and end of every entity)
    boundaries = set()
    for e in entities:
        boundaries.add(e.offset)
        boundaries.add(e.offset + e.length)

    # Sort them to iterate through the text linearly
    sorted_boundaries = sorted(list(boundaries))
    boundary_map = {}  # Maps utf16_offset -> python_index

    current_utf16_len = 0
    boundary_idx = 0

    # Iterate over the string code point by code point
    for py_index, char in enumerate(text):
        # If we reached a boundary, record the mapping
        while boundary_idx < len(sorted_boundaries) and current_utf16_len == sorted_boundaries[boundary_idx]:
            boundary_map[sorted_boundaries[boundary_idx]] = py_index
            boundary_idx += 1

        if boundary_idx >= len(sorted_boundaries):
            break

        # Advance UTF-16 counter
        # BMP characters (<= 0xFFFF) take 1 unit. Non-BMP (surrogates) take 2 units.
        if ord(char) > 0xFFFF:
            current_utf16_len += 2
        else:
            current_utf16_len += 1

    # Handle boundaries that fall exactly at the end of the string
    while boundary_idx < len(sorted_boundaries) and current_utf16_len == sorted_boundaries[boundary_idx]:
        boundary_map[sorted_boundaries[boundary_idx]] = len(text)
        boundary_idx += 1

    # --- Step 2: Create Markers ---
    # We transform entities into "Insert Start Tag" and "Insert End Tag" markers.
    markers = []

    for e in entities:
        if e.offset not in boundary_map or (e.offset + e.length) not in boundary_map:
            continue  # Skip invalid entities

        start_py = boundary_map[e.offset]
        end_py = boundary_map[e.offset + e.length]

        # Structure: (Index, Type, Priority, Entity)
        # Type: 1 = Start Tag, 0 = End Tag.
        # Priority: Used to ensure correct nesting (Outer tags wrap Inner tags).
        #   - For Start Tags (1): Larger length = Higher priority (Process earlier).
        #     We use negative length so 'smaller' number comes first in ASC sort.
        #   - For End Tags (0): Smaller length = Higher priority (Process earlier).

        # Start Marker
        markers.append((start_py, 1, -e.length, e))

        # End Marker
        markers.append((end_py, 0, e.length, e))

    # --- Step 3: Sort Markers ---
    # Primary Key: Index (asc)
    # Secondary Key: Type (End tags (0) before Start tags (1) at same index) -> This fixes </b><i> vs <i></b>
    # Tertiary Key: Priority (Length based nesting)

    # FIX: We use a lambda key to avoid comparing the 'e' (MessageEntity) object directly
    markers.sort(key=lambda x: (x[0], x[1], x[2]))

    # --- Step 4: Build HTML ---
    result = []
    text_ptr = 0
    stack = []  # To track currently open entities

    for index, tag_type, _, entity in markers:
        # 1. Append text leading up to this marker
        if index > text_ptr:
            result.append(html.escape(text[text_ptr:index]))
            text_ptr = index

        # 2. Get the HTML tag representation
        tag = get_html_tag(entity, custom_subs)
        if not tag:
            continue

        if tag_type == 1:  # START TAG
            result.append(tag['open'])
            stack.append(entity)

        else:  # END TAG
            # If stack is empty (shouldn't happen in valid data), ignore
            if not stack:
                continue

            # If the entity to close is at the top of the stack, close it normally
            if stack[-1] == entity:
                result.append(tag['close'])
                stack.pop()
            else:
                # INTERSECTING ENTITIES DETECTED
                # We need to close everything down to our entity, then reopen them
                if entity in stack:
                    temp_stack = []

                    # Pop and close until we find the target
                    while stack[-1] != entity:
                        top_entity = stack.pop()
                        top_tag = get_html_tag(top_entity, custom_subs)
                        if top_tag:
                            result.append(top_tag['close'])
                        temp_stack.append(top_entity)

                    # Close the target entity
                    result.append(tag['close'])
                    stack.pop()

                    # Re-open the temporarily closed entities (in reverse order to preserve nesting)
                    for popped_entity in reversed(temp_stack):
                        p_tag = get_html_tag(popped_entity, custom_subs)
                        if p_tag:
                            result.append(p_tag['open'])
                        stack.append(popped_entity)

    # Append remaining text
    if text_ptr < len(text):
        result.append(html.escape(text[text_ptr:]))

    return "".join(result)


def get_html_tag(entity, custom_subs: Optional[Dict[str, str]]) -> Optional[Dict[str, str]]:  # entity: MessageEntity
    """Helper to get open/close tags based on entity type."""

    # Check custom subs first (basic implementation: if type in dict, return it as open tag)
    # Note: The prompt implies full substitutions, but simple key-value usually implies 'open' tag or full format.
    # Given the complexity of closing tags, we stick to the Prompt's Rules for known types.

    t = entity.type
    text_placeholder = "{text}"  # Not used here directly, we just return tags

    if t == "bold":
        return {'open': "<b>", 'close': "</b>"}
    elif t == "italic":
        return {'open': "<i>", 'close': "</i>"}
    elif t == "underline":
        return {'open': "<u>", 'close': "</u>"}
    elif t == "strikethrough":
        return {'open': "<s>", 'close': "</s>"}
    elif t == "spoiler":
        return {'open': '<span class="tg-spoiler">', 'close': "</span>"}
    elif t == "code":
        return {'open': "<code>", 'close': "</code>"}
    elif t == "pre":
        return {'open': "<pre>", 'close': "</pre>"}
    elif t == "blockquote":
        return {'open': "<blockquote>", 'close': "</blockquote>"}
    elif t == "expandable_blockquote":
        return {'open': "<blockquote expandable>", 'close': "</blockquote>"}
    elif t == "text_link":
        return {'open': f'<a href="{entity.url}">', 'close': "</a>"}
    elif t == "custom_emoji":
        return {'open': f'<tg-emoji emoji-id="{entity.custom_emoji_id}">', 'close': "</tg-emoji>"}
    elif t in custom_subs:
        return None # Custom subs are not handled in this tag-based approach

    return None
#endregion

#region ChatGPT vibecoding here
ENTITY_TEMPLATES_CG = {
    "bold": "<b>{text}</b>",
    "italic": "<i>{text}</i>",
    "pre": "<pre>{text}</pre>",
    "code": "<code>{text}</code>",
    "text_link": "<a href=\"{url}\">{text}</a>",
    "strikethrough": "<s>{text}</s>",
    "underline": "<u>{text}</u>",
    "spoiler": "<span class=\"tg-spoiler\">{text}</span>",
    "custom_emoji": "<tg-emoji emoji-id=\"{custom_emoji_id}\">{text}</tg-emoji>",
    "blockquote": "<blockquote>{text}</blockquote>",
    "expandable_blockquote": "<blockquote expandable>{text}</blockquote>",
}

def utf16_index_map(s: str) -> List[int]:
    """
    Map UTF-16 code unit index -> Python string index.
    Result length = utf16_len + 1
    """
    mapping = [0]
    u16 = 0
    for i, ch in enumerate(s):
        code = ord(ch)
        u16 += 2 if code > 0xFFFF else 1
        while len(mapping) <= u16:
            mapping.append(i + 1)
    return mapping

def apply_template(entity, inner: str, custom_subs: Optional[Dict[str, str]]) -> str:
    t = entity.type
    if t in ENTITY_TEMPLATES_CG:
        tpl = ENTITY_TEMPLATES_CG[t]
    elif custom_subs and t in custom_subs:
        tpl = custom_subs[t]
    else:
        return inner

    data = {"text": inner}

    if t == "text_link":
        data["url"] = getattr(entity, "url", "")
    if t == "custom_emoji":
        data["custom_emoji_id"] = getattr(entity, "custom_emoji_id", "")

    return tpl.format(**data)

def build_tree(text: str, entities: List, mapping: List[int]):
    nodes = []

    for e in entities:
        start16 = e.offset
        end16 = e.offset + e.length

        start = mapping[start16]
        end = mapping[end16]

        nodes.append({
            "entity": e,
            "start": start,
            "end": end,
            "children": []
        })

    nodes.sort(key=lambda n: (n["start"], -n["end"]))

    stack = []
    roots = []

    for n in nodes:
        while stack and n["start"] >= stack[-1]["end"]:
            stack.pop()

        if stack:
            stack[-1]["children"].append(n)
        else:
            roots.append(n)

        stack.append(n)

    return roots

def render(text: str, nodes, custom_subs):
    result = []
    pos = 0

    for n in nodes:
        result.append(text[pos:n["start"]])

        inner = render(
            text[n["start"]:n["end"]],
            shift_nodes(n["children"], n["start"]),
            custom_subs
        )

        wrapped = apply_template(n["entity"], inner, custom_subs)
        result.append(wrapped)

        pos = n["end"]

    result.append(text[pos:])
    return "".join(result)

def shift_nodes(nodes, shift):
    out = []
    for n in nodes:
        out.append({
            "entity": n["entity"],
            "start": n["start"] - shift,
            "end": n["end"] - shift,
            "children": shift_nodes(n["children"], shift),
        })
    return out

def apply_html_entities_cg(
    text: str,
    entities: Optional[List],
    custom_subs: Optional[Dict[str, str]]
) -> str:
    if not text:
        return text
    elif not entities:
        return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

    mapping = utf16_index_map(text)
    tree = build_tree(text, entities, mapping)
    return render(text, tree, custom_subs)
#endregion
