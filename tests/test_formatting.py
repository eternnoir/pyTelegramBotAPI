import sys

sys.path.append('../')

from html.parser import HTMLParser

from telebot import types
from telebot.formatting import apply_html_entities, hpre


class AttributeCollector(HTMLParser):
    def __init__(self):
        super().__init__()
        self.tags = []

    def handle_starttag(self, tag, attrs):
        self.tags.append((tag, attrs))


def test_hpre_keeps_plain_language():
    assert hpre("x", language="python") == '<pre><code class="python">x</code></pre>'


def test_hpre_escapes_quotes_in_language():
    assert hpre("x", language='a"b') == '<pre><code class="a&quot;b">x</code></pre>'


def test_hpre_language_cannot_add_attributes():
    parser = AttributeCollector()
    parser.feed(hpre("x", language='a" onmouseover="alert(1)'))
    assert parser.tags == [
        ("pre", []),
        ("code", [("class", 'a" onmouseover="alert(1)')]),
    ]


def test_hpre_still_escapes_content():
    assert hpre("<b>", language="python") == '<pre><code class="python">&lt;b&gt;</code></pre>'


def test_apply_html_entities_date_time():
    # used to raise KeyError: 'unix_time' because the template was formatted with
    # unix= while it declares {unix_time}
    entity = types.MessageEntity(
        type="date_time", offset=11, length=5,
        unix_time=1735689600, date_time_format="r"
    )
    assert apply_html_entities("Meeting at 10:00", [entity]) == (
        'Meeting at <tg-time unix="1735689600" format="r">10:00</tg-time>'
    )


def test_apply_html_entities_date_time_keeps_unix_placeholder():
    # custom submissions written against the old {unix} placeholder must keep
    # working now that the default template uses {unix_time}
    entity = types.MessageEntity(
        type="date_time", offset=0, length=5,
        unix_time=1735689600, date_time_format="r"
    )
    subs = {"date_time": '<tg-time unix="{unix}">{text}</tg-time>'}
    assert apply_html_entities("today", [entity], custom_subs=subs) == (
        '<tg-time unix="1735689600">today</tg-time>'
    )


def test_apply_html_entities_escapes_link_url():
    entity = types.MessageEntity(
        type="text_link", offset=0, length=4, url='https://x.test/?a="b'
    )
    parser = AttributeCollector()
    parser.feed(apply_html_entities("link rest", [entity]))
    assert parser.tags == [("a", [("href", 'https://x.test/?a="b')])]


def test_apply_html_entities_escapes_pre_language():
    entity = types.MessageEntity(
        type="pre", offset=0, length=4, language='py" onload="x'
    )
    parser = AttributeCollector()
    parser.feed(apply_html_entities("code rest", [entity]))
    assert parser.tags == [
        ("pre", []),
        ("code", [("class", 'language-py" onload="x')]),
    ]


def test_apply_html_entities_still_escapes_content():
    entity = types.MessageEntity(type="bold", offset=0, length=4)
    assert apply_html_entities("a<b> c", [entity]) == "<b>a&lt;b&gt;</b> c"
