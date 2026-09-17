from types import SimpleNamespace

from telebot import apihelper


def test_get_multipart_header_formatter_prefers_current_urllib3_name():
    def current_formatter(key, value):
        return 'current={0}'.format(value)

    def legacy_formatter(key, value):
        return 'legacy={0}'.format(value)

    fields = SimpleNamespace(
        format_multipart_header_param=current_formatter,
        format_header_param=legacy_formatter,
    )

    formatter, name = apihelper._get_multipart_header_formatter(fields)

    assert formatter is current_formatter
    assert name == 'format_multipart_header_param'


def test_get_multipart_header_formatter_supports_legacy_urllib3_name():
    def legacy_formatter(key, value):
        return 'legacy={0}'.format(value)

    fields = SimpleNamespace(format_header_param=legacy_formatter)

    formatter, name = apihelper._get_multipart_header_formatter(fields)

    assert formatter is legacy_formatter
    assert name == 'format_header_param'


def test_make_request_patches_selected_multipart_header_formatter(monkeypatch):
    def formatter(key, value):
        return '{0}="{1}"'.format(key, value)

    fields = SimpleNamespace(format_multipart_header_param=formatter)
    monkeypatch.setattr(apihelper, 'fields', fields)
    monkeypatch.setattr(apihelper, 'format_header_param', formatter)
    monkeypatch.setattr(apihelper, 'format_header_param_name', 'format_multipart_header_param')
    response = SimpleNamespace(
        text='{"ok": true, "result": true}',
        status_code=200,
        json=lambda: {'ok': True, 'result': True},
    )
    monkeypatch.setattr(apihelper, 'CUSTOM_REQUEST_SENDER', lambda *args, **kwargs: response)

    assert apihelper._make_request('token', 'test', method='post', files={'document': ('test.txt', object())}) is True
    assert fields.format_multipart_header_param('filename', 'test file.txt') == 'filename=test file.txt'


def test_promote_chat_member_can_manage_tags(monkeypatch):
    captured = {}

    def fake_make_request(token, method_url, params=None, method=None, **kwargs):
        captured['token'] = token
        captured['method_url'] = method_url
        captured['params'] = params
        captured['method'] = method
        return True

    monkeypatch.setattr(apihelper, '_make_request', fake_make_request)

    result = apihelper.promote_chat_member(
        token='token',
        chat_id=1,
        user_id=2,
        can_manage_tags=True,
    )

    assert result is True
    assert captured['method_url'] == 'promoteChatMember'
    assert captured['method'] == 'post'
    assert captured['params']['can_manage_tags'] is True


def test_set_chat_member_tag(monkeypatch):
    captured = {}

    def fake_make_request(token, method_url, params=None, method=None, **kwargs):
        captured['method_url'] = method_url
        captured['params'] = params
        return True

    monkeypatch.setattr(apihelper, '_make_request', fake_make_request)

    result = apihelper.set_chat_member_tag('token', 1, 2, tag='member-tag')

    assert result is True
    assert captured['method_url'] == 'setChatMemberTag'
    assert captured['params']['chat_id'] == 1
    assert captured['params']['user_id'] == 2
    assert captured['params']['tag'] == 'member-tag'
