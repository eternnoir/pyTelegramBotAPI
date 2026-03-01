from telebot import apihelper


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
