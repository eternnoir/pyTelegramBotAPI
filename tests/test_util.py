from telebot import util


def test_smart_split_exact_multiple_has_no_trailing_empty_part():
    # A chunk boundary landing exactly on the limit used to append an empty part.
    for size in (1, 2, 3, 4, 10):
        for chunks in (1, 2, 3):
            text = "a" * (size * chunks)
            assert util.smart_split(text, size) == ["a" * size] * chunks


def test_smart_split_short_text():
    assert util.smart_split("abc", 3) == ["abc"]
    assert util.smart_split("abcde", 3) == ["abc", "de"]
    assert util.smart_split("", 3) == [""]


def test_smart_split_prefers_newline_then_space():
    assert util.smart_split("one two\nthree four", 10) == ["one two\n", "three four"]
    assert util.smart_split("one two three", 8) == ["one two ", "three"]


def test_smart_split_caps_at_max_message_length():
    parts = util.smart_split("a" * (util.MAX_MESSAGE_LENGTH * 2), util.MAX_MESSAGE_LENGTH * 5)
    assert [len(p) for p in parts] == [util.MAX_MESSAGE_LENGTH] * 2


def test_extract_arguments_accepts_none():
    # message.text is None for non-text messages
    assert util.extract_arguments(None) is None  # type: ignore[arg-type]
    assert util.extract_command(None) is None  # type: ignore[arg-type]


def test_extract_arguments_values():
    assert util.extract_arguments("/get name") == "name"
    assert util.extract_arguments("/get") == ""
    assert util.extract_arguments("/get@bot name") == "name"
    assert util.extract_arguments("hello") is None
