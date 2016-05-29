# -*- coding: utf-8 -*-
import pytest
from telebot import util


def test_is_string():
    assert util.is_string('abc')
    assert util.is_string(u'abc')
    assert not util.is_string(1)
    assert not util.is_string([])


def test_is_command():
    assert util.is_command('/help')
    assert not util.is_command('hello')


def test_extract_command():
    assert util.extract_command('/help') == 'help'
    assert util.extract_command('/help@BotName') == 'help'
    assert util.extract_command('/search for this') == 'search'
    assert util.extract_command('hello') is None


def test_extract_arguments():
    assert util.extract_arguments('/get name') == ['name']
    assert util.extract_arguments('/get something else') == ['something', 'else']
    assert util.extract_arguments('/get     something \n many\t  whitespace') == ['something', 'many', 'whitespace']
    with pytest.raises(ValueError):
        util.extract_arguments('Good day to you')


def test_split_string():
    assert util.split_string('a' * 30, 10) == ['a' * 10, 'a' * 10, 'a' * 10]
    assert util.split_string('a' * 30, 40) == ['a' * 30]
    assert util.split_string('', 10) == []


def test_to_deep_dict():
    class TestClass:

        def __init__(self, level, nest=True):
            setattr(self, 'prop_{0}'.format(level), level)
            if nest:
                setattr(self, 'nested_{0}'.format(level), TestClass(level + 1, nest=False))

    obj = TestClass(0)
    assert util.obj_to_dict(obj) == {'prop_0': 0, 'nested_0': {'prop_1': 1}}


def test_merge_dicts():
    assert util.merge_dicts({'a': 1}, {'b': 2}, {'c': 3}) == {'a': 1, 'b': 2, 'c': 3}
    assert util.merge_dicts({'a': 1}, {'a': 2}) == {'a': 2}
    assert util.merge_dicts({'a': 1}) == {'a': 1}


def test_xmerge():
    assert util.xmerge({'a': 1}, {'b': None}) == {'a': 1}
    assert util.xmerge({'a': None}, {'b': None}) == {}
    assert util.xmerge({'a': None}, {'a': None}) == {}


def test_required():

    @util.required('required1', 'required2')
    def func(required1=None, required2=None, not_required=None):
        return True

    assert func(required1=1, required2=2)
    assert func(required1=1, required2=2, not_required=3)
    assert func(1, 2)

    with pytest.raises(ValueError):
        assert func()
        assert func(not_required=3)
        assert func(required2=2)


def test_translate():

    @util.translate({'translated_from': 'translated_to'})
    def translated_function(translated_to='to', expect=None):
        return translated_to == expect

    assert translated_function(translated_from='from', expect='from')
    assert translated_function(translated_to='to', expect='to')
