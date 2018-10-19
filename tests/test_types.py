# -*- coding: utf-8 -*-
import sys

sys.path.append('../')
from telebot import types


def test_json_user():
    jsonstring = r'{"id":101176298,"first_name":"RDSSBOT","username":"rdss_bot","is_bot":true}'
    u = types.User.de_json(jsonstring)
    assert u.id == 101176298


def test_json_message():
    jsonstring = r'{"message_id":1,"from":{"id":108929734,"first_name":"Frank","last_name":"Wang","username":"eternnoir","is_bot":true},"chat":{"id":1734,"first_name":"F","type":"private","last_name":"Wa","username":"oir"},"date":1435296025,"text":"HIHI"}'
    msg = types.Message.de_json(jsonstring)
    assert msg.text == 'HIHI'


def test_json_message_group():
    json_string = r'{"message_id":10,"from":{"id":12345,"first_name":"g","last_name":"G","username":"GG","is_bot":true},"chat":{"id":-866,"type":"private","title":"\u4ea4"},"date":1435303157,"text":"HIHI"}'
    msg = types.Message.de_json(json_string)
    assert msg.text == 'HIHI'
    assert len(msg.chat.title) != 0
    assert msg.from_user.username == 'GG'


def test_json_GroupChat():
    json_string = r'{"id":8926,"title":"\u5c4e\u4f2f\u98ef\u98ef\u4e4b\u4ea4"}'
    gc = types.GroupChat.de_json(json_string)
    assert gc.id == 8926


def test_json_Document():
    json_string = r'{"file_name":"Text File","thumb":{},"file_id":"BQADBQADMwIAAsYifgZ_CEh0u682xwI","file_size":446}'
    doc = types.Document.de_json(json_string)
    assert doc.thumb is None
    assert doc.file_name == 'Text File'


def test_json_Message_Audio():
    json_string = r'{"message_id":131,"from":{"id":12775,"first_name":"dd","username":"dd","is_bot":true },"chat":{"id":10834,"first_name":"dd","type":"private","type":"private","last_name":"dd","username":"dd"},"date":1439978364,"audio":{"duration":1,"mime_type":"audio\/mpeg","title":"pyTelegram","performer":"eternnoir","file_id":"BQADBQADDH1JaB8-1KyWUss2-Ag","file_size":20096}}'
    msg = types.Message.de_json(json_string)
    assert msg.audio.duration == 1
    assert msg.content_type == 'audio'
    assert msg.audio.performer == 'eternnoir'
    assert msg.audio.title == 'pyTelegram'


def test_json_Message_Sticker():
    json_string = r'{"message_id":98,"from":{"id":10734,"first_name":"Fd","last_name":"Wd","username":"dd","is_bot":true },"chat":{"id":10734,"first_name":"Fd","type":"private","last_name":"Wd","username":"dd"},"date":1435479551,"sticker":{"width":550,"height":368,"thumb":{"file_id":"AAQFABPJLB0sAAQq17w-li3bzoIfAAIC","file_size":1822,"width":90,"height":60},"file_id":"BQADBQADNAIAAsYifgYdGJOa6bGAsQI","file_size":30320}}'
    msg = types.Message.de_json(json_string)
    assert msg.sticker.height == 368
    assert msg.sticker.thumb.height == 60
    assert msg.content_type == 'sticker'


def test_json_Message_Sticker_without_thumb():
    json_string = r'{"message_id":98,"from":{"id":10734,"first_name":"Fd","last_name":"Wd","username":"dd","is_bot":true },"chat":{"id":10734,"first_name":"Fd","type":"private","last_name":"Wd","username":"dd"},"date":1435479551,"sticker":{"width":550,"height":368,"file_id":"BQADBQADNAIAAsYifgYdGJOa6bGAsQI","file_size":30320}}'
    msg = types.Message.de_json(json_string)
    assert msg.sticker.height == 368
    assert msg.sticker.thumb is None
    assert msg.content_type == 'sticker'


def test_json_Message_Document():
    json_string = r'{"message_id":97,"from":{"id":10734,"first_name":"Fd","last_name":"Wd","username":"dd","is_bot":true },"chat":{"id":10,"first_name":"Fd","type":"private","last_name":"Wd","username":"dd"},"date":1435478744,"document":{"file_name":"Text File","thumb":{},"file_id":"BQADBQADMwIAAsYifgZ_CEh0u682xwI","file_size":446}}'
    msg = types.Message.de_json(json_string)
    assert msg.document.file_name == 'Text File'
    assert msg.content_type == 'document'


def test_json_Message_Photo():
    json_string = r'{"message_id":96,"from":{"id":109734,"first_name":"Fd","last_name":"Wd","username":"dd","is_bot":true },"chat":{"id":10734,"first_name":"Fd","type":"private","last_name":"dd","username":"dd"},"date":1435478191,"photo":[{"file_id":"AgADBQADIagxG8YifgYv8yLSj76i-dd","file_size":615,"width":90,"height":67},{"file_id":"AgADBQADIagxG8YifgYv8yLSj76i-dd","file_size":10174,"width":320,"height":240},{"file_id":"dd-A_LsTIABFNx-FUOaEa_3AABAQABAg","file_size":53013,"width":759,"height":570}]}'
    msg = types.Message.de_json(json_string)
    assert len(msg.photo) == 3
    assert msg.content_type == 'photo'


def test_json_Message_Video():
    json_string = r'{"message_id":101,"from":{"id":109734,"first_name":"dd","last_name":"dd","username":"dd","is_bot":true },"chat":{"id":109734,"first_name":"dd","type":"private","last_name":"dd","username":"dd"},"date":1435481960,"video":{"duration":3,"caption":"","width":360,"height":640,"thumb":{"file_id":"AAQFABPiYnBjkDwMAAIC","file_size":1597,"width":50,"height":90},"file_id":"BAADBQADNifgb_TOPEKErGoQI","file_size":260699}}'
    msg = types.Message.de_json(json_string)
    assert msg.video
    assert msg.video.duration == 3
    assert msg.video.thumb.width == 50
    assert msg.content_type == 'video'


def test_json_Message_Location():
    json_string = r'{"message_id":102,"from":{"id":108734,"first_name":"dd","last_name":"dd","username":"dd","is_bot":true },"chat":{"id":1089734,"first_name":"dd","type":"private","last_name":"dd","username":"dd"},"date":1535482469,"location":{"longitude":127.479471,"latitude":26.090577}}'
    msg = types.Message.de_json(json_string)
    assert msg.location.latitude == 26.090577
    assert msg.content_type == 'location'


def test_json_UserProfilePhotos():
    json_string = r'{"total_count":1,"photos":[[{"file_id":"AgADAgADqacxG6wpRwABvEB6fpeIcKS4HAIkAATZH_SpyZjzIwdVAAIC","file_size":6150,"width":160,"height":160},{"file_id":"AgADAgADqacxG6wpRwABvEB6fpeIcKS4HAIkAATOiTNi_YoJMghVAAIC","file_size":13363,"width":320,"height":320},{"file_id":"AgADAgADqacxG6wpRwABvEB6fpeIcKS4HAIkAAQW4DyFv0-lhglVAAIC","file_size":28347,"width":640,"height":640},{"file_id":"AgADAgADqacxG6wpRwABvEB6fpeIcKS4HAIkAAT50RvJCg0GQApVAAIC","file_size":33953,"width":800,"height":800}]]}'
    upp = types.UserProfilePhotos.de_json(json_string)
    assert upp.photos[0][0].width == 160
    assert upp.photos[0][-1].height == 800


def test_json_contact():
    json_string = r'{"phone_number":"00011111111","first_name":"dd","last_name":"ddl","user_id":8633}'
    contact = types.Contact.de_json(json_string)
    assert contact.first_name == 'dd'
    assert contact.last_name == 'ddl'


def test_json_voice():
    json_string = r'{"duration": 0,"mime_type": "audio/ogg","file_id": "AwcccccccDH1JaB7w_gyFjYQxVAg","file_size": 10481}'
    voice = types.Voice.de_json(json_string)
    assert voice.duration == 0
    assert voice.file_size == 10481


def test_json_update():
    json_string = r'{"update_id":938203,"message":{"message_id":241,"from":{"is_bot":true,"id":9734,"first_name":"Fk","last_name":"Wg","username":"nir"},"chat":{"id":1111,"first_name":"Fk","type":"private","last_name":"Wg","username":"oir"},"date":1441447009,"text":"HIHI"}}'
    update = types.Update.de_json(json_string)
    assert update.update_id == 938203
    assert update.message.message_id == 241
    assert update.message.from_user.id == 9734


def test_json_chat():
    json_string = r'{"id": -111111,"title": "Test Title","type": "group"}'
    chat = types.Chat.de_json(json_string)
    assert chat.id == -111111
    assert chat.type == 'group'
    assert chat.title == 'Test Title'


def test_InlineQueryResultCachedPhoto():
    iq = types.InlineQueryResultCachedPhoto('aaa', 'Fileid')
    json_str = iq.to_json()
    assert 'aa' in json_str
    assert 'Fileid' in json_str
    assert 'caption' not in json_str


def test_InlineQueryResultCachedPhoto_with_title():
    iq = types.InlineQueryResultCachedPhoto('aaa', 'Fileid', title='Title')
    json_str = iq.to_json()
    assert 'aa' in json_str
    assert 'Fileid' in json_str
    assert 'Title' in json_str
    assert 'caption' not in json_str


def test_InlineQueryResultCachedPhoto_with_markup():
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("Google", url="http://www.google.com"))
    markup.add(types.InlineKeyboardButton("Yahoo", url="http://www.yahoo.com"))
    iq = types.InlineQueryResultCachedPhoto('aaa', 'Fileid', title='Title', reply_markup=markup)
    json_str = iq.to_json()
    assert 'aa' in json_str
    assert 'Fileid' in json_str
    assert 'Title' in json_str
    assert 'caption' not in json_str
    assert 'reply_markup' in json_str
