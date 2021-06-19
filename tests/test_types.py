# -*- coding: utf-8 -*-
import sys

sys.path.append('../')
from telebot import types


def test_json_user():
    jsonstring = r'{"id":101176298,"first_name":"RDSSBOT","last_name":")))","username":"rdss_bot","is_bot":true}'
    u = types.User.de_json(jsonstring)
    assert u.id == 101176298
    assert u.full_name == 'RDSSBOT )))'


def test_json_message():
    jsonstring = r'{"message_id":1,"from":{"id":108929734,"first_name":"Frank","last_name":"Wang","username":"eternnoir","is_bot":true},"chat":{"id":1734,"first_name":"F","type":"private","last_name":"Wa","username":"oir"},"date":1435296025,"text":"HIHI"}'
    msg = types.Message.de_json(jsonstring)
    assert msg.text == 'HIHI'


def test_json_message_with_reply_markup():
    jsonstring = r'{"message_id":48,"from":{"id":153587469,"is_bot":false,"first_name":"Neko","username":"Neko"},"chat":{"id":153587469,"first_name":"Neko","username":"Neko","type":"private"},"date":1598879570,"text":"test","reply_markup":{"inline_keyboard":[[{"text":"Google","url":"http://www.google.com"},{"text":"Yahoo","url":"http://www.yahoo.com"}]]}}'
    msg = types.Message.de_json(jsonstring)
    assert msg.content_type == 'text'
    assert msg.reply_markup.keyboard[0][0].text == 'Google'


def test_json_InlineKeyboardMarkup():
    jsonstring = r'{"inline_keyboard":[[{"text":"Google","url":"http://www.google.com"},{"text":"Yahoo","url":"http://www.yahoo.com"}]]}'
    markup = types.InlineKeyboardMarkup.de_json(jsonstring)
    assert markup.keyboard[0][0].text == 'Google'
    assert markup.keyboard[0][1].url == 'http://www.yahoo.com'


def test_json_InlineKeyboardButton():
    jsonstring = r'{"text":"Google","url":"http://www.google.com"}'
    button = types.InlineKeyboardButton.de_json(jsonstring)
    assert button.text == 'Google'
    assert button.url == 'http://www.google.com'



def test_json_message_with_dice():
    jsonstring = r'{"message_id":5560,"from":{"id":879343317,"is_bot":false,"first_name":"George","last_name":"Forse","username":"dr_fxrse","language_code":"ru"},"chat":{"id":879343317,"first_name":"George","last_name":"Forse","username":"dr_fxrse","type":"private"},"date":1586926330,"dice":{"value": 4, "emoji": "\ud83c\udfaf"}}'
    msg = types.Message.de_json(jsonstring)
    assert msg.content_type == 'dice'
    assert isinstance(msg.dice, types.Dice)
    assert msg.dice.value == 4
    assert msg.dice.emoji == '🎯'


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
    json_string = r'{"file_name":"Text File","thumb":{},"file_id":"BQADBQADMwIAAsYifgZ_CEh0u682xwI","file_unique_id": "AgADJQEAAqfhOEY","file_size":446}'
    doc = types.Document.de_json(json_string)
    assert doc.thumb is None
    assert doc.file_name == 'Text File'


def test_json_Message_Audio():
    json_string = r'{"message_id":131,"from":{"id":12775,"first_name":"dd","username":"dd","is_bot":true },"chat":{"id":10834,"first_name":"dd","type":"private","type":"private","last_name":"dd","username":"dd"},"date":1439978364,"audio":{"duration":1,"mime_type":"audio\/mpeg","title":"pyTelegram","performer":"eternnoir","file_id":"BQADBQADDH1JaB8-1KyWUss2-Ag","file_unique_id": "AgADawEAAn8VSFY","file_size":20096}}'
    msg = types.Message.de_json(json_string)
    assert msg.audio.duration == 1
    assert msg.content_type == 'audio'
    assert msg.audio.performer == 'eternnoir'
    assert msg.audio.title == 'pyTelegram'


def test_json_Message_Sticker():
    json_string = r'{"message_id": 21552, "from": {"id": 590740002, "is_bot": false, "first_name": "⚜️ Ƥυrуα ⚜️", "username": "Purya", "language_code": "en"}, "chat": {"id": -1001309982000, "title": "123", "type": "supergroup"}, "date": 1594068909, "sticker": {"width": 368, "height": 368, "emoji": "🤖", "set_name": "ipuryapack", "is_animated": false, "thumb": {"file_id": "AAMCBAADHQJOFL7mAAJUMF8Dj62hpmDhpRAYvkc8CtIqipolAAJ8AAPA-8cF9yxjgjkLS97A0D4iXQARtQAHbQADHy4AAhoE", "file_unique_id": "AQADwNA-Il0AAx8uAAI", "file_size": 7776, "width": 60, "height": 60}, "file_id": "CAACAgQAAx0CThS-5gACVDBfA4-toaZg4aUQGL5HWerSKoqaJQACArADwPvHBfcsY4I5C3feGgQ", "file_unique_id": "AgADfAADsPvHWQ", "file_size": 14602}}'
    msg = types.Message.de_json(json_string)
    assert msg.sticker.height == 368
    assert msg.sticker.thumb.height == 60
    assert msg.content_type == 'sticker'


def test_json_Message_Sticker_without_thumb():
    json_string = r'{"message_id": 21552, "from": {"id": 590740002, "is_bot": false, "first_name": "⚜️ Ƥυrуα ⚜️", "username": "Purya", "language_code": "en"}, "chat": {"id": -1001309982000, "title": "123", "type": "supergroup"}, "date": 1594068909, "sticker": {"width": 368, "height": 368, "emoji": "🤖", "set_name": "ipuryapack", "is_animated": false, "file_id": "CAACAgQAAx0CThS-5gACVDBfA4-toaZg4aUQGL5HWerSKoqaJQACArADwPvHBfcsY4I5C3feGgQ", "file_unique_id": "AgADfAADsPvHWQ", "file_size": 14602}}'
    msg = types.Message.de_json(json_string)
    assert msg.sticker.height == 368
    assert msg.sticker.thumb is None
    assert msg.content_type == 'sticker'


def test_json_Message_Document():
    json_string = r'{"message_id":97,"from":{"id":10734,"first_name":"Fd","last_name":"Wd","username":"dd","is_bot":true },"chat":{"id":10,"first_name":"Fd","type":"private","last_name":"Wd","username":"dd"},"date":1435478744,"document":{"file_name":"Text File","thumb":{},"file_id":"BQADBQADMwIAAsYifgZ_CEh0u682xwI","file_unique_id": "AQAD_QIfa3QAAyA4BgAB","file_size":446}}'
    msg = types.Message.de_json(json_string)
    assert msg.document.file_name == 'Text File'
    assert msg.content_type == 'document'


def test_json_Message_Photo():
    json_string = r'{"message_id":96,"from":{"id":109734,"first_name":"Fd","last_name":"Wd","username":"dd","is_bot":true },"chat":{"id":10734,"first_name":"Fd","type":"private","last_name":"dd","username":"dd"},"date":1435478191,"photo":[{"file_id":"AgADBQADIagxG8YifgYv8yLSj76i-dd","file_unique_id": "AQAD_QIfa3QAAyA4BgAB","file_size":615,"width":90,"height":67},{"file_id":"AgADBQADIagxG8YifgYv8yLSj76i-dd","file_unique_id": "AQAD_QIfa3QAAyA4BgAB","file_size":10174,"width":320,"height":240},{"file_id":"dd-A_LsTIABFNx-FUOaEa_3AABAQABAg","file_unique_id": "AQAD_QIfa3QAAyA4BgAB","file_size":53013,"width":759,"height":570}]}'
    msg = types.Message.de_json(json_string)
    assert len(msg.photo) == 3
    assert msg.content_type == 'photo'


def test_json_Message_Video():
    json_string = r'{"message_id":101,"from":{"id":109734,"first_name":"dd","last_name":"dd","username":"dd","is_bot":true },"chat":{"id":109734,"first_name":"dd","type":"private","last_name":"dd","username":"dd"},"date":1435481960,"video":{"duration":3,"caption":"","width":360,"height":640,"thumb":{"file_id":"AAQFABPiYnBjkDwMAAIC","file_unique_id": "AQADTeisa3QAAz1nAAI","file_size":1597,"width":50,"height":90},"file_id":"BAADBQADNifgb_TOPEKErGoQI","file_unique_id": "AgADbgEAAn8VSFY","file_size":260699}}'
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
    json_string = r'{"total_count":1,"photos":[[{"file_id":"AgADAgADqacxG6wpRwABvEB6fpeIcKS4HAIkAATZH_SpyZjzIwdVAAIC","file_unique_id": "AQAD_QIfa3QAAyA4BgAB","file_size":6150,"width":160,"height":160},{"file_id":"AgADAgADqacxG6wpRwABvEB6fpeIcKS4HAIkAATOiTNi_YoJMghVAAIC","file_unique_id": "AQAD_QIfa3QAAyA4BgAB","file_size":13363,"width":320,"height":320},{"file_id":"AgADAgADqacxG6wpRwABvEB6fpeIcKS4HAIkAAQW4DyFv0-lhglVAAIC","file_unique_id": "AQAD_QIfa3QAAyA4BgAB","file_size":28347,"width":640,"height":640},{"file_id":"AgADAgADqacxG6wpRwABvEB6fpeIcKS4HAIkAAT50RvJCg0GQApVAAIC","file_unique_id": "AQAD_QIfa3QAAyA4BgAB","file_size":33953,"width":800,"height":800}]]}'
    upp = types.UserProfilePhotos.de_json(json_string)
    assert upp.photos[0][0].width == 160
    assert upp.photos[0][-1].height == 800


def test_json_contact():
    json_string = r'{"phone_number":"00011111111","first_name":"dd","last_name":"ddl","user_id":8633,"vcard":"SomeContactString"}'
    contact = types.Contact.de_json(json_string)
    assert contact.first_name == 'dd'
    assert contact.last_name == 'ddl'


def test_json_voice():
    json_string = r'{"duration": 0,"mime_type": "audio/ogg","file_id": "AwcccccccDH1JaB7w_gyFjYQxVAg","file_unique_id": "AgADbAEAAn8VSFY","file_size": 10481}'
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


def test_json_poll_1():
    jsonstring = r'{"message_id": 395020,"from": {"id": 111,"is_bot": false,"first_name": "FN","last_name": "LN","username": "Badiboy","language_code": "ru"},"chat": {"id": 111,"first_name": "FN","last_name": "LN","username": "Badiboy","type": "private"},"date": 1587841239,"poll": {"id": "5272018969396510722","question": "Test poll 1","options": [{"text": "Answer 1","voter_count": 0},{"text": "Answer 2","voter_count": 0}],"total_voter_count": 0,"is_closed": false,"is_anonymous": true,"type": "regular","allows_multiple_answers": true}}'
    msg = types.Message.de_json(jsonstring)
    assert msg.poll is not None
    assert isinstance(msg.poll, types.Poll)
    assert msg.poll.id == '5272018969396510722'
    assert msg.poll.question is not None
    assert msg.poll.options is not None
    assert len(msg.poll.options) == 2
    assert msg.poll.allows_multiple_answers is True


def test_json_poll_answer():
    jsonstring = r'{"poll_id": "5895675970559410186", "user": {"id": 329343347, "is_bot": false, "first_name": "Test", "username": "test_user", "last_name": "User", "language_code": "en"}, "option_ids": [1]}'
    __import__('pprint').pprint(__import__('json').loads(jsonstring))
    poll_answer = types.PollAnswer.de_json(jsonstring)
    assert poll_answer.poll_id == '5895675970559410186'
    assert isinstance(poll_answer.user, types.User)
    assert poll_answer.option_ids == [1]


def test_KeyboardButtonPollType():
    markup = types.ReplyKeyboardMarkup()
    markup.add(types.KeyboardButton('send me a poll', request_poll=types.KeyboardButtonPollType(type='quiz')))
    json_str = markup.to_json()
    assert 'request_poll' in json_str
    assert 'quiz' in json_str


def test_json_chat_invite_link():
    json_string = r'{"invite_link": "https://t.me/joinchat/z-abCdEFghijKlMn", "creator": {"id": 329343347, "is_bot": false, "first_name": "Test", "username": "test_user", "last_name": "User", "language_code": "en"}, "is_primary": false, "is_revoked": false, "expire_date": 1624119999, "member_limit": 10}'
    invite_link = types.ChatInviteLink.de_json(json_string)
    assert invite_link.invite_link == 'https://t.me/joinchat/z-abCdEFghijKlMn'
    assert isinstance(invite_link.creator, types.User)
    assert not invite_link.is_primary
    assert not invite_link.is_revoked
    assert invite_link.expire_date == 1624119999
    assert invite_link.member_limit == 10

def test_chat_member_updated():
    json_string = r'{"chat": {"id": -1234567890123, "type": "supergroup", "title": "No Real Group", "username": "NoRealGroup"}, "from": {"id": 133869498, "is_bot": false, "first_name": "Vincent"}, "date": 1624119999, "old_chat_member": {"user": {"id": 77777777, "is_bot": false, "first_name": "Pepe"}, "status": "member"}, "new_chat_member": {"user": {"id": 77777777, "is_bot": false, "first_name": "Pepe"}, "status": "administrator"}}'
    cm_updated = types.ChatMemberUpdated.de_json(json_string)
    assert cm_updated.chat.id == -1234567890123
    assert cm_updated.from_user.id == 133869498
    assert cm_updated.date == 1624119999
    assert cm_updated.old_chat_member.status == "member"
    assert cm_updated.new_chat_member.status == "administrator"

