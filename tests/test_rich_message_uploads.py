import asyncio
import io
import json

from telebot import apihelper, asyncio_helper, types


def _rich_message():
    photo_file = types.InputFile(io.BytesIO(b'photo'), file_name='photo.jpg')
    video_file = types.InputFile(io.BytesIO(b'video'), file_name='video.mp4')
    # A photo block nested in a list item, and a media entry for tg:// links
    nested_photo = types.InputRichBlockList(items=[
        types.InputRichBlockListItem(blocks=[types.InputRichBlockPhoto(photo=types.InputMediaPhoto(photo_file))]),
    ])
    media = types.InputRichMessageMedia(id='clip', media=types.InputMediaVideo(video_file))
    return types.InputRichMessage(blocks=[nested_photo], media=[media]), photo_file, video_file


def _check_uploads(params, files, photo_file, video_file):
    sent = json.loads(params['rich_message'])
    photo_ref = sent['blocks'][0]['items'][0]['blocks'][0]['photo']['media']
    video_ref = sent['media'][0]['media']['media']
    assert files == {
        photo_ref[len('attach://'):]: photo_file,
        video_ref[len('attach://'):]: video_file,
    }


def _capture(captured):
    def fake_request(token, method_url, params=None, files=None, method=None, **kwargs):
        captured.update(method_url=method_url, params=params, files=files, method=method)
        return {}
    return fake_request


def test_rich_message_without_uploads_has_no_files():
    rich_message = types.InputRichMessage(html='<b>Hello</b>')
    assert rich_message.convert_input_rich_message() == (rich_message.to_json(), {})


def test_rich_message_methods_upload_media_files(monkeypatch):
    captured = {}
    monkeypatch.setattr(apihelper, '_make_request', _capture(captured))

    rich_message, photo_file, video_file = _rich_message()
    apihelper.send_rich_message('token', 1, rich_message)
    assert captured['method'] == 'post'
    _check_uploads(captured['params'], captured['files'], photo_file, video_file)

    rich_message, photo_file, video_file = _rich_message()
    apihelper.send_rich_message_draft('token', 1, 2, rich_message)
    _check_uploads(captured['params'], captured['files'], photo_file, video_file)

    rich_message, photo_file, video_file = _rich_message()
    apihelper.edit_message_text('token', chat_id=1, message_id=2, rich_message=rich_message)
    _check_uploads(captured['params'], captured['files'], photo_file, video_file)


def test_async_rich_message_methods_upload_media_files(monkeypatch):
    captured = {}

    async def fake_process_request(token, url, method='get', params=None, files=None, **kwargs):
        captured.update(url=url, params=params, files=files, method=method)
        return {}

    monkeypatch.setattr(asyncio_helper, '_process_request', fake_process_request)

    rich_message, photo_file, video_file = _rich_message()
    asyncio.run(asyncio_helper.send_rich_message('token', 1, rich_message))
    assert captured['method'] == 'post'
    _check_uploads(captured['params'], captured['files'], photo_file, video_file)

    rich_message, photo_file, video_file = _rich_message()
    asyncio.run(asyncio_helper.send_rich_message_draft('token', 1, 2, rich_message))
    _check_uploads(captured['params'], captured['files'], photo_file, video_file)

    rich_message, photo_file, video_file = _rich_message()
    asyncio.run(asyncio_helper.edit_message_text('token', chat_id=1, message_id=2, rich_message=rich_message))
    _check_uploads(captured['params'], captured['files'], photo_file, video_file)
