# -*- coding: utf-8 -*-
import sys

sys.path.append('../')
from telebot import types


def test_json_user():
    jsonstring = r'{"id":101176298,"first_name":"RDSSBOT","username":"rdss_bot"}'
    u = types.User.de_json(jsonstring)
    assert u.id == 101176298


def test_json_message():
    jsonstring = r'{"message_id":1,"from":{"id":108929734,"first_name":"Frank","last_name":"Wang","username":"eternnoir"},"chat":{"id":108929734,"first_name":"Frank","last_name":"Wang","username":"eternnoir"},"date":1435296025,"text":"HIHI"}'
    msg = types.Message.de_json(jsonstring)
    assert msg.text == 'HIHI'


def test_json_message_group():
    json_string = r'{"message_id":10,"from":{"id":12345,"first_name":"g","last_name":"G","username":"GG"},"chat":{"id":-866,"title":"\u4ea4"},"date":1435303157,"text":"HIHI"}'
    msg = types.Message.de_json(json_string)
    assert msg.text == 'HIHI'
    assert len(msg.chat.title) != 0
    assert msg.fromUser.username == 'GG'


def test_json_GroupChat():
    json_string = r'{"id":8926,"title":"\u5c4e\u4f2f\u98ef\u98ef\u4e4b\u4ea4"}'
    gc = types.GroupChat.de_json(json_string)
    assert gc.id == 8926


def test_json_Document():
    json_string = r'{"file_name":"Text File","thumb":{},"file_id":"BQADBQADMwIAAsYifgZ_CEh0u682xwI","file_size":446}'
    doc = types.Document.de_json(json_string)
    assert doc.thumb == None
    assert doc.file_name == 'Text File'


def test_json_Message_Audio():
    json_string = r'{"message_id":100,"from":{"id":10734,"first_name":"dd","last_name":"dd","username":"dd"},"chat":{"id":10734,"first_name":"dd","last_name":"dd","username":"dd"},"date":1435481343,"audio":{"duration":3,"mime_type":"audio\/ogg","file_id":"ddg","file_size":8249}}'
    msg = types.Message.de_json(json_string)
    assert msg.audio.duration == 3
    assert msg.content_type == 'audio'


def test_json_Message_Sticker():
    json_string = r'{"message_id":98,"from":{"id":10734,"first_name":"Fd","last_name":"Wd","username":"dd"},"chat":{"id":10734,"first_name":"Fd","last_name":"Wd","username":"dd"},"date":1435479551,"sticker":{"width":550,"height":368,"thumb":{"file_id":"AAQFABPJLB0sAAQq17w-li3bzoIfAAIC","file_size":1822,"width":90,"height":60},"file_id":"BQADBQADNAIAAsYifgYdGJOa6bGAsQI","file_size":30320}}'
    msg = types.Message.de_json(json_string)
    assert msg.sticker.height == 368
    assert msg.sticker.thumb.height == 60
    assert msg.content_type == 'sticker'


def test_json_Message_Document():
    json_string = r'{"message_id":97,"from":{"id":10734,"first_name":"Fd","last_name":"Wd","username":"dd"},"chat":{"id":10,"first_name":"Fd","last_name":"Wd","username":"dd"},"date":1435478744,"document":{"file_name":"Text File","thumb":{},"file_id":"BQADBQADMwIAAsYifgZ_CEh0u682xwI","file_size":446}}'
    msg = types.Message.de_json(json_string)
    assert msg.document.file_name == 'Text File'
    assert msg.content_type == 'document'


def test_json_Message_Photo():
    json_string = r'{"message_id":96,"from":{"id":109734,"first_name":"Fd","last_name":"Wd","username":"dd"},"chat":{"id":10734,"first_name":"Fd","last_name":"dd","username":"dd"},"date":1435478191,"photo":[{"file_id":"AgADBQADIagxG8YifgYv8yLSj76i-dd","file_size":615,"width":90,"height":67},{"file_id":"AgADBQADIagxG8YifgYv8yLSj76i-dd","file_size":10174,"width":320,"height":240},{"file_id":"dd-A_LsTIABFNx-FUOaEa_3AABAQABAg","file_size":53013,"width":759,"height":570}]}'
    msg = types.Message.de_json(json_string)
    assert len(msg.photo) == 3
    assert msg.content_type == 'photo'


def test_json_Message_Video():
    json_string = r'{"message_id":101,"from":{"id":109734,"first_name":"dd","last_name":"dd","username":"dd"},"chat":{"id":109734,"first_name":"dd","last_name":"dd","username":"dd"},"date":1435481960,"video":{"duration":3,"caption":"","width":360,"height":640,"thumb":{"file_id":"AAQFABPiYnBjkDwMAAIC","file_size":1597,"width":50,"height":90},"file_id":"BAADBQADNifgb_TOPEKErGoQI","file_size":260699}}'
    msg = types.Message.de_json(json_string)
    assert msg.video
    assert msg.video.duration == 3
    assert msg.video.thumb.width == 50
    assert msg.content_type == 'video'


def test_json_Message_Location():
    json_string = r'{"message_id":102,"from":{"id":108734,"first_name":"dd","last_name":"dd","username":"dd"},"chat":{"id":1089734,"first_name":"dd","last_name":"dd","username":"dd"},"date":1535482469,"location":{"longitude":127.479471,"latitude":26.090577}}'
    msg = types.Message.de_json(json_string)
    assert msg.location.latitude == 26.090577
    assert msg.content_type == 'location'
