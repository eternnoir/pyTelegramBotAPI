import asyncio
import io
import json
from types import SimpleNamespace

from telebot import apihelper, asyncio_helper, types


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


def _capture(captured):
    def fake_request(token, method_url, params=None, files=None, method=None, **kwargs):
        captured.update(method_url=method_url, params=params, files=files, method=method)
        return {'ok': True}
    return fake_request


def _checklist():
    return types.InputChecklist(title='Groceries', tasks=[types.InputChecklistTask(id=1, text='Milk')])


def test_send_and_edit_checklist_send_checklist_as_json(monkeypatch):
    captured = {}
    monkeypatch.setattr(apihelper, '_make_request', _capture(captured))

    apihelper.send_checklist('token', 'bc', 1, _checklist())
    assert json.loads(captured['params']['checklist'])['title'] == 'Groceries'

    apihelper.edit_message_checklist('token', 'bc', 1, 2, _checklist())
    assert json.loads(captured['params']['checklist'])['tasks'][0]['text'] == 'Milk'


def test_widget_methods_send_empty_data(monkeypatch):
    captured = {}
    monkeypatch.setattr(apihelper, '_make_request', _capture(captured))

    apihelper.send_widget('token', 1, '<b>hi</b>', public_data='', allow_queries=True)
    assert captured['method_url'] == 'sendWidget'
    assert captured['params'] == {'chat_id': 1, 'html': '<b>hi</b>', 'public_data': '', 'allow_queries': True}

    apihelper.edit_message_widget_data('token', chat_id=1, message_id=2, chat_data='')
    assert captured['method_url'] == 'editMessageWidgetData'
    assert captured['params'] == {'chat_id': 1, 'message_id': 2, 'chat_data': ''}

    apihelper.edit_shared_widget_data('token', 'w1', '')
    assert captured['params'] == {'widget_id': 'w1', 'public_data': ''}


def test_replace_sticker_in_set_uploads_the_sticker_file(monkeypatch):
    captured = {}
    monkeypatch.setattr(apihelper, '_make_request', _capture(captured))
    sticker_file = types.InputFile(io.BytesIO(b'sticker'), file_name='sticker.webp')
    sticker = types.InputSticker(sticker=sticker_file, emoji_list=['\U0001f642'], format='static')

    apihelper.replace_sticker_in_set('token', 1, 'set_by_bot', 'old_id', sticker)

    attach = json.loads(captured['params']['sticker'])['sticker']
    assert attach.startswith('attach://')
    assert captured['files'] == {attach[len('attach://'):]: sticker_file}
    assert captured['method'] == 'post'


def test_async_checklist_and_replace_sticker(monkeypatch):
    captured = {}

    async def fake_process_request(token, url, method='get', params=None, files=None, **kwargs):
        captured.update(url=url, params=params, files=files, method=method)
        return True

    monkeypatch.setattr(asyncio_helper, '_process_request', fake_process_request)

    asyncio.run(asyncio_helper.send_checklist('token', 'bc', 1, _checklist()))
    assert json.loads(captured['params']['checklist'])['title'] == 'Groceries'

    asyncio.run(asyncio_helper.edit_message_checklist('token', 'bc', 1, 2, _checklist()))
    assert json.loads(captured['params']['checklist'])['title'] == 'Groceries'

    sticker_file = types.InputFile(io.BytesIO(b'sticker'), file_name='sticker.webp')
    sticker = types.InputSticker(sticker=sticker_file, emoji_list=['\U0001f642'], format='static')
    asyncio.run(asyncio_helper.replace_sticker_in_set('token', 1, 'set_by_bot', 'old_id', sticker))
    attach = json.loads(captured['params']['sticker'])['sticker']
    assert captured['files'] == {attach[len('attach://'):]: sticker_file}
    assert captured['method'] == 'post'


def test_async_widget_methods(monkeypatch):
    captured = {}

    async def fake_process_request(token, url, method='get', params=None, files=None, **kwargs):
        captured.update(url=url, params=params, method=method)
        return True

    monkeypatch.setattr(asyncio_helper, '_process_request', fake_process_request)

    asyncio.run(asyncio_helper.send_shared_widget('token', 1, 'w1', chat_data=''))
    assert captured['url'] == 'sendSharedWidget'
    assert captured['params'] == {'chat_id': 1, 'widget_id': 'w1', 'chat_data': ''}

    asyncio.run(asyncio_helper.answer_widget_query('token', 'q1', data='ok'))
    assert captured['url'] == 'answerWidgetQuery'
    assert captured['params'] == {'widget_query_id': 'q1', 'data': 'ok'}
    assert captured['method'] == 'post'


def test_ephemeral_reply_without_chat_id(monkeypatch):
    captured = {}
    monkeypatch.setattr(apihelper, '_make_request', _capture(captured))
    parameters = types.EphemeralMessageParameters(callback_query_id='q1')

    apihelper.send_message('token', None, 'hi', ephemeral_message_parameters=parameters)
    assert captured['params'] == {'text': 'hi', 'ephemeral_message_parameters': '{"callback_query_id": "q1"}'}

    apihelper.send_data('token', None, 'file-id', 'document', ephemeral_message_parameters=parameters)
    assert 'chat_id' not in captured['params']

    apihelper.send_message('token', 1, 'hi')
    assert captured['params']['chat_id'] == '1'


def test_api_104_methods(monkeypatch):
    captured = {}
    monkeypatch.setattr(apihelper, '_make_request', _capture(captured))

    apihelper.get_unique_gift('token', 'Cake-1')
    assert captured['method_url'] == 'getUniqueGift'
    assert captured['params'] == {'name': 'Cake-1'}

    apihelper.get_chat_share_theme_backdrops('token')
    assert captured['method_url'] == 'getChatShareThemeBackdrops'

    apihelper.delete_business_account_gift('token', 'bc', 'g1')
    assert captured['method_url'] == 'deleteBusinessAccountGift'
    assert captured['params'] == {'business_connection_id': 'bc', 'owned_gift_id': 'g1'}

    entity = types.MessageEntity('text_link', 0, 4, url='https://example.com')
    apihelper.verify_user('token', 1, 'Team', custom_description_entities=[entity])
    assert json.loads(captured['params']['custom_description_entities'])[0]['url'] == 'https://example.com'

    apihelper.verify_chat('token', 1, 'Team', custom_description_parse_mode='HTML')
    assert captured['params']['custom_description_parse_mode'] == 'HTML'


def test_async_api_104_methods(monkeypatch):
    captured = {}

    async def fake_process_request(token, url, method='get', params=None, files=None, **kwargs):
        captured.update(url=url, params=params, method=method)
        return True

    monkeypatch.setattr(asyncio_helper, '_process_request', fake_process_request)
    parameters = types.EphemeralMessageParameters(callback_query_id='q1')

    asyncio.run(asyncio_helper.send_message('token', None, 'hi', ephemeral_message_parameters=parameters))
    assert 'chat_id' not in captured['params']

    asyncio.run(asyncio_helper.send_photo('token', None, 'file-id', ephemeral_message_parameters=parameters))
    assert 'chat_id' not in captured['params']

    asyncio.run(asyncio_helper.get_unique_gift('token', 'Cake-1'))
    assert captured['url'] == 'getUniqueGift'
    assert captured['params'] == {'name': 'Cake-1'}

    asyncio.run(asyncio_helper.delete_business_account_gift('token', 'bc', 'g1'))
    assert captured['url'] == 'deleteBusinessAccountGift'
    assert captured['method'] == 'post'

    asyncio.run(asyncio_helper.verify_chat('token', 1, custom_description_parse_mode='HTML'))
    assert captured['params'] == {'chat_id': 1, 'custom_description_parse_mode': 'HTML'}
