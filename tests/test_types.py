# -*- coding: utf-8 -*-
import sys

sys.path.append('../')
from telebot import types


def test_json_user():
    jsonstring = r'{"id":101176298,"first_name":"RDSSBOT","last_name":")))","username":"rdss_bot","is_bot":true, "is_premium":true, "added_to_attachment_menu": true}'
    u = types.User.de_json(jsonstring)
    assert u.id == 101176298
    assert u.full_name == 'RDSSBOT )))'
    assert u.is_premium is True
    assert u.added_to_attachment_menu is True



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
    json_string = r'{"message_id":10,"from":{"id":12345,"first_name":"g","last_name":"G","username":"GG","is_bot":true},"chat":{"id":-866,"type":"private","title":"\u4ea4"},"date":1435303157,"text":"HIHI","has_protected_content":true}'
    msg = types.Message.de_json(json_string)
    assert msg.text == 'HIHI'
    assert len(msg.chat.title) != 0
    assert msg.from_user.username == 'GG'


def test_json_GroupChat():
    json_string = r'{"id":8926,"title":"\u5c4e\u4f2f\u98ef\u98ef\u4e4b\u4ea4"}'
    gc = types.GroupChat.de_json(json_string)
    assert gc.id == 8926


def test_json_Document():
    json_string = r'{"file_name":"Text File","thumbnail":{},"file_id":"BQADBQADMwIAAsYifgZ_CEh0u682xwI","file_unique_id": "AgADJQEAAqfhOEY","file_size":446}'
    doc = types.Document.de_json(json_string)
    assert doc.thumbnail is None
    assert doc.file_name == 'Text File'


def test_json_Message_Audio():
    json_string = r'{"message_id":131,"from":{"id":12775,"first_name":"dd","username":"dd","is_bot":true },"chat":{"id":10834,"first_name":"dd","type":"private","type":"private","last_name":"dd","username":"dd"},"date":1439978364,"audio":{"duration":1,"mime_type":"audio\/mpeg","title":"pyTelegram","performer":"eternnoir","file_id":"BQADBQADDH1JaB8-1KyWUss2-Ag","file_unique_id": "AgADawEAAn8VSFY","file_size":20096}}'
    msg = types.Message.de_json(json_string)
    assert msg.audio.duration == 1
    assert msg.content_type == 'audio'
    assert msg.audio.performer == 'eternnoir'
    assert msg.audio.title == 'pyTelegram'


def test_json_Message_Sticker():
    json_string = r'{"message_id": 21552, "from": {"id": 590740002, "is_bot": false, "first_name": "⚜️ Ƥυrуα ⚜️", "username": "Purya", "language_code": "en"}, "chat": {"id": -1001309982000, "title": "123", "type": "supergroup"}, "date": 1594068909, "sticker": {"type": "regular", "width": 368, "height": 368, "emoji": "🤖", "set_name": "ipuryapack", "is_animated": false, "is_video": true, "thumbnail": {"file_id": "AAMCBAADHQJOFL7mAAJUMF8Dj62hpmDhpRAYvkc8CtIqipolAAJ8AAPA-8cF9yxjgjkLS97A0D4iXQARtQAHbQADHy4AAhoE", "file_unique_id": "AQADwNA-Il0AAx8uAAI", "file_size": 7776, "width": 60, "height": 60}, "file_id": "CAACAgQAAx0CThS-5gACVDBfA4-toaZg4aUQGL5HWerSKoqaJQACArADwPvHBfcsY4I5C3feGgQ", "file_unique_id": "AgADfAADsPvHWQ", "file_size": 14602}}'
    msg = types.Message.de_json(json_string)
    assert msg.sticker.height == 368
    assert msg.sticker.thumbnail.height == 60
    assert msg.content_type == 'sticker'


def test_json_Message_Sticker_without_thumbnail():
    json_string = r'{"message_id": 21552, "from": {"id": 590740002, "is_bot": false, "first_name": "⚜️ Ƥυrуα ⚜️", "username": "Purya", "language_code": "en"}, "chat": {"id": -1001309982000, "title": "123", "type": "supergroup"}, "date": 1594068909, "sticker": {"type": "regular", "width": 368, "height": 368, "emoji": "🤖", "set_name": "ipuryapack", "is_animated": false, "is_video": true, "file_id": "CAACAgQAAx0CThS-5gACVDBfA4-toaZg4aUQGL5HWerSKoqaJQACArADwPvHBfcsY4I5C3feGgQ", "file_unique_id": "AgADfAADsPvHWQ", "file_size": 14602}}'
    msg = types.Message.de_json(json_string)
    assert msg.sticker.height == 368
    assert msg.sticker.thumbnail is None
    assert msg.content_type == 'sticker'


def test_json_Message_Document():
    json_string = r'{"message_id":97,"from":{"id":10734,"first_name":"Fd","last_name":"Wd","username":"dd","is_bot":true },"chat":{"id":10,"first_name":"Fd","type":"private","last_name":"Wd","username":"dd"},"date":1435478744,"document":{"file_name":"Text File","thumbnail":{},"file_id":"BQADBQADMwIAAsYifgZ_CEh0u682xwI","file_unique_id": "AQAD_QIfa3QAAyA4BgAB","file_size":446}}'
    msg = types.Message.de_json(json_string)
    assert msg.document.file_name == 'Text File'
    assert msg.content_type == 'document'


def test_json_Message_Photo():
    json_string = r'{"message_id":96,"from":{"id":109734,"first_name":"Fd","last_name":"Wd","username":"dd","is_bot":true },"chat":{"id":10734,"first_name":"Fd","type":"private","last_name":"dd","username":"dd"},"date":1435478191,"photo":[{"file_id":"AgADBQADIagxG8YifgYv8yLSj76i-dd","file_unique_id": "AQAD_QIfa3QAAyA4BgAB","file_size":615,"width":90,"height":67},{"file_id":"AgADBQADIagxG8YifgYv8yLSj76i-dd","file_unique_id": "AQAD_QIfa3QAAyA4BgAB","file_size":10174,"width":320,"height":240},{"file_id":"dd-A_LsTIABFNx-FUOaEa_3AABAQABAg","file_unique_id": "AQAD_QIfa3QAAyA4BgAB","file_size":53013,"width":759,"height":570}]}'
    msg = types.Message.de_json(json_string)
    assert len(msg.photo) == 3
    assert msg.content_type == 'photo'


def test_json_Message_Video():
    json_string = r'{"message_id":101,"from":{"id":109734,"first_name":"dd","last_name":"dd","username":"dd","is_bot":true },"chat":{"id":109734,"first_name":"dd","type":"private","last_name":"dd","username":"dd"},"date":1435481960,"video":{"duration":3,"caption":"","width":360,"height":640,"thumbnail":{"file_id":"AAQFABPiYnBjkDwMAAIC","file_unique_id": "AQADTeisa3QAAz1nAAI","file_size":1597,"width":50,"height":90},"file_id":"BAADBQADNifgb_TOPEKErGoQI","file_unique_id": "AgADbgEAAn8VSFY","file_size":260699}}'
    msg = types.Message.de_json(json_string)
    assert msg.video
    assert msg.video.duration == 3
    assert msg.video.thumbnail.width == 50
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
    json_string = r'{"id": -111111,"title": "Test Title","type": "group", "join_to_send_messages": true, "join_by_request": true}'
    chat = types.Chat.de_json(json_string)
    assert chat.id == -111111
    assert chat.type == 'group'
    assert chat.title == 'Test Title'
    assert chat.join_to_send_messages is True
    assert chat.join_by_request is True
    

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
    jsonstring = r'{"message_id":2649246,"from":{"id":927266710,"is_bot":false,"first_name":"a","username":"b","language_code":"en"},"chat":{"id":1234,"first_name":"a","username":"b","type":"private"},"date":1775379138,"poll":{"id":"5373272187744556440","question":"Test","options":[{"persistent_id":"0","text":"1","voter_count":0},{"persistent_id":"1","text":"2","voter_count":0}],"total_voter_count":0,"is_closed":false,"is_anonymous":true,"allows_multiple_answers":false,"allows_revoting":false,"type":"quiz","correct_option_id":0,"correct_option_ids":[0]}}'
    msg = types.Message.de_json(jsonstring)
    assert msg.poll is not None
    assert isinstance(msg.poll, types.Poll)
    assert msg.poll.id == '5373272187744556440'
    assert msg.poll.question == 'Test'
    assert len(msg.poll.options) == 2
    assert msg.poll.options[0].text == '1'
    assert msg.poll.options[1].text == '2'
    assert msg.poll.options[0].voter_count == 0
    assert msg.poll.options[1].voter_count == 0
    assert msg.poll.options[0].persistent_id == '0'
    assert msg.poll.options[1].persistent_id == '1'
    assert msg.poll.total_voter_count == 0
    assert msg.poll.is_closed is False
    assert msg.poll.is_anonymous is True
    assert msg.poll.allows_multiple_answers is False
    assert msg.poll.allows_revoting is False
    assert msg.poll.type == 'quiz'
    assert msg.poll.correct_option_id == 0
    assert msg.poll.correct_option_ids == [0]


def test_json_poll_answer():
    jsonstring = r'{"poll_id": "5895675970559410186", "option_persistent_ids": ["0"], "user": {"id": 329343347, "is_bot": false, "first_name": "Test", "username": "test_user", "last_name": "User", "language_code": "en"}, "option_ids": [1]}'
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
    json_string = r'{"invite_link":"https://t.me/joinchat/MeASP-Wi...","creator":{"id":927266710,"is_bot":false,"first_name":">_run","username":"coder2020","language_code":"ru"},"pending_join_request_count":1,"creates_join_request":true,"is_primary":false,"is_revoked":false}'
    invite_link = types.ChatInviteLink.de_json(json_string)
    assert invite_link.invite_link == 'https://t.me/joinchat/MeASP-Wi...'
    assert isinstance(invite_link.creator, types.User)
    assert not invite_link.is_primary
    assert not invite_link.is_revoked
    assert invite_link.expire_date is None
    assert invite_link.member_limit is None
    assert invite_link.name is None
    assert invite_link.creator.id == 927266710
    assert invite_link.pending_join_request_count == 1
    assert invite_link.creates_join_request


def test_chat_member_updated():
    json_string = r'{"chat": {"id": -1234567890123, "type": "supergroup", "title": "No Real Group", "username": "NoRealGroup"}, "from": {"id": 133869498, "is_bot": false, "first_name": "Vincent"}, "date": 1624119999, "old_chat_member": {"user": {"id": 77777777, "is_bot": false, "first_name": "Pepe"}, "status": "member"}, "new_chat_member": {"user": {"id": 77777777, "is_bot": false, "first_name": "Pepe"}, "status": "left"}}'
    cm_updated = types.ChatMemberUpdated.de_json(json_string)
    assert cm_updated.chat.id == -1234567890123
    assert cm_updated.from_user.id == 133869498
    assert cm_updated.date == 1624119999
    assert cm_updated.old_chat_member.status == "member"
    assert cm_updated.new_chat_member.status == "left"


def test_webhook_info():
    json_string = r'{"url": "https://example.com/webhook", "has_custom_certificate": true, "pending_update_count": 1, "last_error_date": 0, "last_error_message": "", "last_synchronization_error_date": 489309, "max_connections": 40, "allowed_updates": ["message"]}'
    webhook_info = types.WebhookInfo.de_json(json_string)
    print(webhook_info)
    assert webhook_info.url == 'https://example.com/webhook'
    assert webhook_info.has_custom_certificate is True
    assert webhook_info.pending_update_count == 1
    assert webhook_info.last_error_date == 0
    assert webhook_info.last_error_message == ''
    assert webhook_info.max_connections == 40
    assert webhook_info.last_synchronization_error_date == 489309
    assert webhook_info.allowed_updates == ['message']
    

def test_sent_web_app_message():
    json_string = r'{"inline_message_id": "29430"}'
    sent_web_app_message = types.SentWebAppMessage.de_json(json_string)
    assert sent_web_app_message.inline_message_id == '29430'
    

def test_message_entity():
    # TODO: Add support for nesting entities


    sample_string_1 = r'{"update_id":934522126,"message":{"message_id":1374510,"from":{"id":927266710,"is_bot":false,"first_name":">_run","username":"coder2020","language_code":"en","is_premium":true},"chat":{"id":927266710,"first_name":">_run","username":"coder2020","type":"private"},"date":1682177590,"text":"b b b","entities":[{"offset":0,"length":2,"type":"bold"},{"offset":0,"length":1,"type":"italic"},{"offset":2,"length":2,"type":"bold"},{"offset":2,"length":1,"type":"italic"},{"offset":4,"length":1,"type":"bold"},{"offset":4,"length":1,"type":"italic"}]}}'
    update = types.Update.de_json(sample_string_1)
    message: types.Message = update.message
    assert message.html_text == "<b><i>b</i> </b><b><i>b</i> </b><b><i>b</i></b>"

    sample_string_2 = r'{"update_id":934522166,"message":{"message_id":1374526,"from":{"id":927266710,"is_bot":false,"first_name":">_run","username":"coder2020","language_code":"en","is_premium":true},"chat":{"id":927266710,"first_name":">_run","username":"coder2020","type":"private"},"date":1682179716,"text":"b b b","entities":[{"offset":0,"length":1,"type":"bold"},{"offset":2,"length":1,"type":"bold"},{"offset":4,"length":1,"type":"italic"}]}}'
    message_2 = types.Update.de_json(sample_string_2).message
    assert message_2.html_text == "<b>b</b> <b>b</b> <i>b</i>"

    

    sample_string_3 = r'{"update_id":934522172,"message":{"message_id":1374530,"from":{"id":927266710,"is_bot":false,"first_name":">_run","username":"coder2020","language_code":"en","is_premium":true},"chat":{"id":927266710,"first_name":">_run","username":"coder2020","type":"private"},"date":1682179968,"text":"This is a bold text with a nested italic and bold text.","entities":[{"offset":10,"length":4,"type":"bold"},{"offset":27,"length":7,"type":"italic"},{"offset":34,"length":15,"type":"bold"},{"offset":34,"length":15,"type":"italic"}]}}'
    message_3 = types.Update.de_json(sample_string_3).message
    assert \
        (message_3.html_text == "This is a <b>bold</b> text with a <i>nested </i><i><b>italic and bold</b></i> text.") or \
        (message_3.html_text == "This is a <b>bold</b> text with a <i>nested </i><b><i>italic and bold</i></b> text.")


    sample_string_4 = r'{"update_id":934522437,"message":{"message_id":1374619,"from":{"id":927266710,"is_bot":false,"first_name":">_run","username":"coder2020","language_code":"en","is_premium":true},"chat":{"id":927266710,"first_name":">_run","username":"coder2020","type":"private"},"date":1682189507,"forward_from":{"id":927266710,"is_bot":false,"first_name":">_run","username":"coder2020","language_code":"en","is_premium":true},"forward_date":1682189124,"text":"aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa😋😋","entities":[{"offset":0,"length":76,"type":"bold"},{"offset":0,"length":76,"type":"italic"},{"offset":0,"length":76,"type":"underline"},{"offset":0,"length":76,"type":"strikethrough"},{"offset":76,"length":2,"type":"custom_emoji","custom_emoji_id":"5456188142006575553"},{"offset":78,"length":2,"type":"custom_emoji","custom_emoji_id":"5456188142006575553"}]}}'
    message_4 = types.Update.de_json(sample_string_4).message
    assert \
        (message_4.html_text == '<s><u><i><b>aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa</b></i></u></s><tg-emoji emoji-id="5456188142006575553">😋</tg-emoji><tg-emoji emoji-id="5456188142006575553">😋</tg-emoji>') or \
        (message_4.html_text == '<b><i><u><s>aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa</s></u></i></b><tg-emoji emoji-id="5456188142006575553">😋</tg-emoji><tg-emoji emoji-id="5456188142006575553">😋</tg-emoji>')


    sample_string_5 = r'{"update_id":934522166,"message":{"message_id":1374526,"from":{"id":927266710,"is_bot":false,"first_name":">_run","username":"coder2020","language_code":"en","is_premium":true},"chat":{"id":927266710,"first_name":">_run","username":"coder2020","type":"private"},"date":1682179716,"text":"b <b>b</b> <i>i</i>","entities":[{"offset":0,"length":1,"type":"bold"}]}}'
    message_5 = types.Update.de_json(sample_string_5).message
    assert message_5.html_text == "<b>b</b> &lt;b&gt;b&lt;/b&gt; &lt;i&gt;i&lt;/i&gt;"


    sample_string_6 = r'{"update_id":934522166,"message":{"message_id":1374526,"from":{"id":927266710,"is_bot":false,"first_name":">_run","username":"coder2020","language_code":"en","is_premium":true},"chat":{"id":927266710,"first_name":">_run","username":"coder2020","type":"private"},"date":1682179716,"text":"<b>b</b> <i>i</i>"}}'
    message_6 = types.Update.de_json(sample_string_6).message
    assert message_6.html_text == "&lt;b&gt;b&lt;/b&gt; &lt;i&gt;i&lt;/i&gt;"


    sample_string_7 = r'{"update_id":934522167,"message":{"message_id":1374526,"from":{"id":927266710,"is_bot":false,"first_name":">_run","username":"coder2020","language_code":"en","is_premium":true},"chat":{"id":927266710,"first_name":">_run","username":"coder2020","type":"private"},"date":1682179716,"reply_to_message":{"message_id":1374510,"from":{"id":927266710,"is_bot":false,"first_name":">_run","username":"coder2020","language_code":"en"},"chat":{"id":927266710,"first_name":">_run","username":"coder2020","type":"private"},"date":1712765863,"text":"text @UserName b i s u c p #hashtag https://example.com","entities":[{"offset":5,"length":9,"type":"mention"},{"offset":15,"length":1,"type":"bold"},{"offset":17,"length":1,"type":"italic"},{"offset":19,"length":1,"type":"strikethrough"},{"offset":21,"length":1,"type":"underline"},{"offset":23,"length":1,"type":"code"},{"offset":25,"length":1,"type":"spoiler"},{"offset":27,"length":8,"type":"hashtag"},{"offset":36,"length":19,"type":"url"}],"link_preview_options":{"is_disabled":true}},"quote":{"text":"text @UserName b i s u c p #hashtag https://example.com","entities":[{"offset":15,"length":1,"type":"bold"},{"offset":17,"length":1,"type":"italic"},{"offset":19,"length":1,"type":"strikethrough"},{"offset":21,"length":1,"type":"underline"},{"offset":25,"length":1,"type":"spoiler"}],"position":0,"is_manual":true},"text":"quote reply"}}'
    message_7 = types.Update.de_json(sample_string_7).message
    assert message_7.quote.html_text == 'text @UserName <b>b</b> <i>i</i> <s>s</s> <u>u</u> c <span class="tg-spoiler">p</span> #hashtag https://example.com'


def test_message_entity_date_time():
    entity = types.MessageEntity(
        type='date_time',
        offset=0,
        length=10,
        unix_time=1740787200,
        date_time_format='short',
    )
    assert entity.type == 'date_time'
    assert entity.to_dict()['type'] == 'date_time'
    assert entity.to_dict()['unix_time'] == 1740787200
    assert entity.to_dict()['date_time_format'] == 'short'


def test_message_sender_tag():
    jsonstring = r'{"message_id":1,"from":{"id":1,"first_name":"A","is_bot":false},"chat":{"id":1,"first_name":"A","type":"private"},"date":1435296025,"text":"hi","sender_tag":"blue"}'
    msg = types.Message.de_json(jsonstring)
    assert msg.sender_tag == 'blue'


def test_chat_member_member_tag():
    jsonstring = r'{"status":"member","user":{"id":1,"is_bot":false,"first_name":"A"},"tag":"alpha"}'
    cm = types.ChatMember.de_json(jsonstring)
    assert isinstance(cm, types.ChatMemberMember)
    assert cm.tag == 'alpha'


def test_chat_member_restricted_tag_and_can_edit_tag():
    jsonstring = r'{"status":"restricted","user":{"id":1,"is_bot":false,"first_name":"A"},"is_member":true,"can_send_messages":true,"can_send_audios":true,"can_send_documents":true,"can_send_photos":true,"can_send_videos":true,"can_send_video_notes":true,"can_send_voice_notes":true,"can_send_polls":true,"can_send_other_messages":true,"can_add_web_page_previews":true,"can_change_info":false,"can_invite_users":false,"can_pin_messages":false,"can_manage_topics":false,"until_date":0,"tag":"beta","can_edit_tag":true}'
    cm = types.ChatMember.de_json(jsonstring)
    assert isinstance(cm, types.ChatMemberRestricted)
    assert cm.tag == 'beta'
    assert cm.can_edit_tag is True


def test_chat_member_administrator_can_manage_tags():
    jsonstring = r'{"status":"administrator","user":{"id":1,"is_bot":false,"first_name":"A"},"can_be_edited":true,"is_anonymous":false,"can_manage_chat":true,"can_delete_messages":true,"can_manage_video_chats":true,"can_restrict_members":true,"can_promote_members":true,"can_change_info":true,"can_invite_users":true,"can_post_stories":true,"can_edit_stories":true,"can_delete_stories":true,"can_manage_tags":true}'
    cm = types.ChatMember.de_json(jsonstring)
    assert isinstance(cm, types.ChatMemberAdministrator)
    assert cm.can_manage_tags is True


def test_chat_permissions_can_edit_tag():
    permissions = types.ChatPermissions(can_send_messages=True, can_edit_tag=True)
    assert permissions.to_dict()['can_edit_tag'] is True


def test_chat_administrator_rights_can_manage_tags():
    rights = types.ChatAdministratorRights(
        is_anonymous=False,
        can_manage_chat=True,
        can_delete_messages=True,
        can_manage_video_chats=True,
        can_restrict_members=True,
        can_promote_members=True,
        can_change_info=True,
        can_invite_users=True,
        can_manage_tags=True,
    )
    assert rights.to_dict()['can_manage_tags'] is True
