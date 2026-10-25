import sys

sys.path.append('../')

from html.parser import HTMLParser

from telebot.formatting import hpre


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
