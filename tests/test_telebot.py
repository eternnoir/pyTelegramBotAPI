# -*- coding: utf-8 -*-
import sys

sys.path.append('../')

import time
import pytest
import os

import telebot
from telebot import types
from telebot import util

should_skip = 'TOKEN' and 'CHAT_ID' not in os.environ

if not should_skip:
    TOKEN = os.environ['TOKEN']
    CHAT_ID = os.environ['CHAT_ID']
    GROUP_ID = os.environ['GROUP_ID']


@pytest.mark.skipif(should_skip, reason="No environment variables configured")
class TestTeleBot:
    def test_message_listener(self):
        msg_list = []
        for x in range(100):
            msg_list.append(self.create_text_message('Message ' + str(x)))

        def listener(messages):
            assert len(messages) == 100

        tb = telebot.TeleBot('')
        tb.set_update_listener(listener)

    def test_message_handler(self):
        tb = telebot.TeleBot('')
        msg = self.create_text_message('/help')

        @tb.message_handler(commands=['help', 'start'])
        def command_handler(message):
            message.text = 'got'

        tb.process_new_messages([msg])
        time.sleep(1)
        assert msg.text == 'got'

    def test_message_handler_reg(self):
        bot = telebot.TeleBot('')
        msg = self.create_text_message(r'https://web.telegram.org/')

        @bot.message_handler(regexp='((https?):((//)|(\\\\))+([\w\d:#@%/;$()~_?\+-=\\\.&](#!)?)*)')
        def command_url(message):
            msg.text = 'got'

        bot.process_new_messages([msg])
        time.sleep(1)
        assert msg.text == 'got'

    def test_message_handler_lambda(self):
        bot = telebot.TeleBot('')
        msg = self.create_text_message(r'lambda_text')

        @bot.message_handler(func=lambda message: r'lambda' in message.text)
        def command_url(message):
            msg.text = 'got'

        bot.process_new_messages([msg])
        time.sleep(1)
        assert msg.text == 'got'

    def test_message_handler_lambda_fail(self):
        bot = telebot.TeleBot('')
        msg = self.create_text_message(r'text')

        @bot.message_handler(func=lambda message: r'lambda' in message.text)
        def command_url(message):
            msg.text = 'got'

        bot.process_new_messages([msg])
        time.sleep(1)
        assert not msg.text == 'got'

    def test_message_handler_reg_fail(self):
        bot = telebot.TeleBot('')
        msg = self.create_text_message(r'web.telegram.org/')

        @bot.message_handler(regexp='((https?):((//)|(\\\\))+([\w\d:#@%/;$()~_?\+-=\\\.&](#!)?)*)')
        def command_url(message):
            msg.text = 'got'

        bot.process_new_messages([msg])
        time.sleep(1)
        assert not msg.text == 'got'

    def test_send_message_with_markdown(self):
        tb = telebot.TeleBot(TOKEN)
        markdown = """
        *bold text*
        _italic text_
        [text](URL)
        """
        ret_msg = tb.send_message(CHAT_ID, markdown, parse_mode="Markdown")
        assert ret_msg.message_id

    def test_send_message_with_disable_notification(self):
        tb = telebot.TeleBot(TOKEN)
        markdown = """
        *bold text*
        _italic text_
        [text](URL)
        """
        ret_msg = tb.send_message(CHAT_ID, markdown, parse_mode="Markdown", disable_notification=True)
        assert ret_msg.message_id

    def test_send_file(self):
        file_data = open('../examples/detailed_example/kitten.jpg', 'rb')
        tb = telebot.TeleBot(TOKEN)
        ret_msg = tb.send_document(CHAT_ID, file_data)
        assert ret_msg.message_id

        ret_msg = tb.send_document(CHAT_ID, ret_msg.document.file_id)
        assert ret_msg.message_id

    def test_send_file_dis_noti(self):
        file_data = open('../examples/detailed_example/kitten.jpg', 'rb')
        tb = telebot.TeleBot(TOKEN)
        ret_msg = tb.send_document(CHAT_ID, file_data, disable_notification=True)
        assert ret_msg.message_id

        ret_msg = tb.send_document(CHAT_ID, ret_msg.document.file_id)
        assert ret_msg.message_id

    def test_send_file_caption(self):
        file_data = open('../examples/detailed_example/kitten.jpg', 'rb')
        tb = telebot.TeleBot(TOKEN)
        ret_msg = tb.send_document(CHAT_ID, file_data, caption="Test")
        assert ret_msg.message_id

        ret_msg = tb.send_document(CHAT_ID, ret_msg.document.file_id)
        assert ret_msg.message_id

    def test_send_video(self):
        file_data = open('./test_data/test_video.mp4', 'rb')
        tb = telebot.TeleBot(TOKEN)
        ret_msg = tb.send_video(CHAT_ID, file_data)
        assert ret_msg.message_id

    def test_send_video_dis_noti(self):
        file_data = open('./test_data/test_video.mp4', 'rb')
        tb = telebot.TeleBot(TOKEN)
        ret_msg = tb.send_video(CHAT_ID, file_data, disable_notification=True)
        assert ret_msg.message_id

    def test_send_video_more_params(self):
        file_data = open('./test_data/test_video.mp4', 'rb')
        tb = telebot.TeleBot(TOKEN)
        ret_msg = tb.send_video(CHAT_ID, file_data, 1)
        assert ret_msg.message_id

    def test_send_video_more_params_dis_noti(self):
        file_data = open('./test_data/test_video.mp4', 'rb')
        tb = telebot.TeleBot(TOKEN)
        ret_msg = tb.send_video(CHAT_ID, file_data, 1, disable_notification=True)
        assert ret_msg.message_id

    def test_send_file_exception(self):
        tb = telebot.TeleBot(TOKEN)
        try:
            tb.send_document(CHAT_ID, None)
            assert False
        except Exception as e:
            print(e)
            assert True

    def test_send_photo(self):
        file_data = open('../examples/detailed_example/kitten.jpg', 'rb')
        tb = telebot.TeleBot(TOKEN)
        ret_msg = tb.send_photo(CHAT_ID, file_data)
        assert ret_msg.message_id

        ret_msg = tb.send_photo(CHAT_ID, ret_msg.photo[0].file_id)
        assert ret_msg.message_id

    def test_send_photo_dis_noti(self):
        file_data = open('../examples/detailed_example/kitten.jpg', 'rb')
        tb = telebot.TeleBot(TOKEN)
        ret_msg = tb.send_photo(CHAT_ID, file_data)
        assert ret_msg.message_id

        ret_msg = tb.send_photo(CHAT_ID, ret_msg.photo[0].file_id, disable_notification=True)
        assert ret_msg.message_id

    def test_send_audio(self):
        file_data = open('./test_data/record.mp3', 'rb')
        tb = telebot.TeleBot(TOKEN)
        ret_msg = tb.send_audio(CHAT_ID, file_data, 1, performer='eternnoir', title='pyTelegram')
        assert ret_msg.content_type == 'audio'
        assert ret_msg.audio.performer == 'eternnoir'
        assert ret_msg.audio.title == 'pyTelegram'

    def test_send_audio_dis_noti(self):
        file_data = open('./test_data/record.mp3', 'rb')
        tb = telebot.TeleBot(TOKEN)
        ret_msg = tb.send_audio(CHAT_ID, file_data, 1, performer='eternnoir', title='pyTelegram',
                                disable_notification=True)
        assert ret_msg.content_type == 'audio'
        assert ret_msg.audio.performer == 'eternnoir'
        assert ret_msg.audio.title == 'pyTelegram'

    def test_send_voice(self):
        file_data = open('./test_data/record.ogg', 'rb')
        tb = telebot.TeleBot(TOKEN)
        ret_msg = tb.send_voice(CHAT_ID, file_data)
        assert ret_msg.voice.mime_type == 'audio/ogg'

    def test_send_voice_dis_noti(self):
        file_data = open('./test_data/record.ogg', 'rb')
        tb = telebot.TeleBot(TOKEN)
        ret_msg = tb.send_voice(CHAT_ID, file_data, disable_notification=True)
        assert ret_msg.voice.mime_type == 'audio/ogg'

    def test_get_file(self):
        file_data = open('./test_data/record.ogg', 'rb')
        tb = telebot.TeleBot(TOKEN)
        ret_msg = tb.send_voice(CHAT_ID, file_data)
        file_id = ret_msg.voice.file_id
        file_info = tb.get_file(file_id)
        assert file_info.file_id == file_id

    def test_get_file_dis_noti(self):
        file_data = open('./test_data/record.ogg', 'rb')
        tb = telebot.TeleBot(TOKEN)
        ret_msg = tb.send_voice(CHAT_ID, file_data, disable_notification=True)
        file_id = ret_msg.voice.file_id
        file_info = tb.get_file(file_id)
        assert file_info.file_id == file_id

    def test_send_message(self):
        text = 'CI Test Message'
        tb = telebot.TeleBot(TOKEN)
        ret_msg = tb.send_message(CHAT_ID, text)
        assert ret_msg.message_id

    def test_send_message_dis_noti(self):
        text = 'CI Test Message'
        tb = telebot.TeleBot(TOKEN)
        ret_msg = tb.send_message(CHAT_ID, text, disable_notification=True)
        assert ret_msg.message_id

    def test_send_message_with_markup(self):
        text = 'CI Test Message'
        tb = telebot.TeleBot(TOKEN)
        markup = types.ReplyKeyboardMarkup()
        markup.add(types.KeyboardButton("1"))
        markup.add(types.KeyboardButton("2"))
        ret_msg = tb.send_message(CHAT_ID, text, disable_notification=True, reply_markup=markup)
        assert ret_msg.message_id

    def test_send_message_with_markup_use_string(self):
        text = 'CI Test Message'
        tb = telebot.TeleBot(TOKEN)
        markup = types.ReplyKeyboardMarkup()
        markup.add("1")
        markup.add("2")
        markup.add("3")
        markup.add("4")
        ret_msg = tb.send_message(CHAT_ID, text, disable_notification=True, reply_markup=markup)
        assert ret_msg.message_id

    def test_send_message_with_inlinemarkup(self):
        text = 'CI Test Message'
        tb = telebot.TeleBot(TOKEN)
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("Google", url="http://www.google.com"))
        markup.add(types.InlineKeyboardButton("Yahoo", url="http://www.yahoo.com"))
        ret_msg = tb.send_message(CHAT_ID, text, disable_notification=True, reply_markup=markup)
        assert ret_msg.message_id

    def test_forward_message(self):
        text = 'CI forward_message Test Message'
        tb = telebot.TeleBot(TOKEN)
        msg = tb.send_message(CHAT_ID, text)
        ret_msg = tb.forward_message(CHAT_ID, CHAT_ID, msg.message_id)
        assert ret_msg.forward_from

    def test_forward_message_dis_noti(self):
        text = 'CI forward_message Test Message'
        tb = telebot.TeleBot(TOKEN)
        msg = tb.send_message(CHAT_ID, text)
        ret_msg = tb.forward_message(CHAT_ID, CHAT_ID, msg.message_id, disable_notification=True)
        assert ret_msg.forward_from

    def test_reply_to(self):
        text = 'CI reply_to Test Message'
        tb = telebot.TeleBot(TOKEN)
        msg = tb.send_message(CHAT_ID, text)
        ret_msg = tb.reply_to(msg, text + ' REPLY')
        assert ret_msg.reply_to_message.message_id == msg.message_id

    def test_register_for_reply(self):
        text = 'CI reply_to Test Message'
        tb = telebot.TeleBot(TOKEN)
        msg = tb.send_message(CHAT_ID, text, reply_markup=types.ForceReply())
        reply_msg = tb.reply_to(msg, text + ' REPLY')

        def process_reply(message):
            assert msg.message_id == message.reply_to_message.message_id

        tb.register_for_reply(msg, process_reply)

        tb.process_new_messages([reply_msg])

    def test_send_location(self):
        tb = telebot.TeleBot(TOKEN)
        lat = 26.3875591
        lon = -161.2901042
        ret_msg = tb.send_location(CHAT_ID, lat, lon)
        assert int(ret_msg.location.longitude) == int(lon)
        assert int(ret_msg.location.latitude) == int(lat)

    def test_send_location_dis_noti(self):
        tb = telebot.TeleBot(TOKEN)
        lat = 26.3875591
        lon = -161.2901042
        ret_msg = tb.send_location(CHAT_ID, lat, lon, disable_notification=True)
        assert int(ret_msg.location.longitude) == int(lon)
        assert int(ret_msg.location.latitude) == int(lat)

    def test_send_venue(self):
        tb = telebot.TeleBot(TOKEN)
        lat = 26.3875591
        lon = -161.2901042
        ret_msg = tb.send_venue(CHAT_ID, lat, lon, "Test Venue", "1123 Test Venue address")
        assert ret_msg.venue.title == "Test Venue"
        assert int(lat) == int(ret_msg.venue.location.latitude)

    def test_send_venue_dis_noti(self):
        tb = telebot.TeleBot(TOKEN)
        lat = 26.3875591
        lon = -161.2901042
        ret_msg = tb.send_venue(CHAT_ID, lat, lon, "Test Venue", "1123 Test Venue address", disable_notification=True)
        assert ret_msg.venue.title == "Test Venue"

    def test_Chat(self):
        tb = telebot.TeleBot(TOKEN)
        me = tb.get_me()
        msg = tb.send_message(CHAT_ID, 'Test')
        assert me.id == msg.from_user.id
        assert msg.chat.id == int(CHAT_ID)

    def test_edit_message_text(self):
        tb = telebot.TeleBot(TOKEN)
        msg = tb.send_message(CHAT_ID, 'Test')
        new_msg = tb.edit_message_text('Edit test', chat_id=CHAT_ID, message_id=msg.message_id)
        assert new_msg.text == 'Edit test'

    def test_edit_message_caption(self):
        file_data = open('../examples/detailed_example/kitten.jpg', 'rb')
        tb = telebot.TeleBot(TOKEN)
        msg = tb.send_document(CHAT_ID, file_data, caption="Test")
        new_msg = tb.edit_message_caption(caption='Edit test', chat_id=CHAT_ID, message_id=msg.message_id)
        assert new_msg.caption == 'Edit test'

    def test_edit_message_media(self):
        file_data = open('../examples/detailed_example/kitten.jpg', 'rb')
        file_data_2 = open('../examples/detailed_example/rooster.jpg', 'rb')
        tb = telebot.TeleBot(TOKEN)
        msg = tb.send_photo(CHAT_ID, file_data)
        new_msg = tb.edit_message_media(chat_id=CHAT_ID, message_id=msg.message_id,
                                        media=types.InputMediaPhoto(file_data_2, caption='Test editMessageMedia 0'))
        assert type(new_msg) != bool

        new_msg = tb.edit_message_media(chat_id=CHAT_ID, message_id=msg.message_id,
                                        media=types.InputMediaPhoto(msg.photo[0].file_id, caption='Test editMessageMedia'))
        assert type(new_msg) != bool
        assert new_msg.caption == 'Test editMessageMedia'

    def test_get_chat(self):
        tb = telebot.TeleBot(TOKEN)
        ch = tb.get_chat(GROUP_ID)
        assert str(ch.id) == GROUP_ID

    def test_get_chat_administrators(self):
        tb = telebot.TeleBot(TOKEN)
        cas = tb.get_chat_administrators(GROUP_ID)
        assert len(cas) > 0

    def test_get_chat_members_count(self):
        tb = telebot.TeleBot(TOKEN)
        cn = tb.get_chat_members_count(GROUP_ID)
        assert cn > 1

    def test_edit_markup(self):
        text = 'CI Test Message'
        tb = telebot.TeleBot(TOKEN)
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("Google", url="http://www.google.com"))
        markup.add(types.InlineKeyboardButton("Yahoo", url="http://www.yahoo.com"))
        ret_msg = tb.send_message(CHAT_ID, text, disable_notification=True, reply_markup=markup)
        markup.add(types.InlineKeyboardButton("Google2", url="http://www.google.com"))
        markup.add(types.InlineKeyboardButton("Yahoo2", url="http://www.yahoo.com"))
        new_msg = tb.edit_message_reply_markup(chat_id=CHAT_ID, message_id=ret_msg.message_id, reply_markup=markup)
        assert new_msg.message_id

    @staticmethod
    def create_text_message(text):
        params = {'text': text}
        chat = types.User(11, False, 'test')
        return types.Message(1, None, None, chat, 'text', params, "")

    def test_is_string_unicode(self):
        s1 = u'string'
        assert util.is_string(s1)

    def test_is_string_string(self):
        s1 = 'string'
        assert util.is_string(s1)

    def test_not_string(self):
        i1 = 10
        assert not util.is_string(i1)

    def test_send_video_note(self):
        file_data = open('./test_data/test_video.mp4', 'rb')
        tb = telebot.TeleBot(TOKEN)
        ret_msg = tb.send_video_note(CHAT_ID, file_data)
        assert ret_msg.message_id

    def test_send_media_group(self):
        tb = telebot.TeleBot(TOKEN)
        img1 = 'https://i.imgur.com/CjXjcnU.png'
        img2 = 'https://i.imgur.com/CjXjcnU.png'
        medias = [types.InputMediaPhoto(img1, "View"), types.InputMediaPhoto(img2, "Dog")]
        result = tb.send_media_group(CHAT_ID, medias)
        assert len(result) == 2
        assert result[0].media_group_id is not None
        assert result[0].media_group_id == result[1].media_group_id

    def test_send_media_group_local_files(self):
        photo = open('../examples/detailed_example/kitten.jpg', 'rb')
        video = open('./test_data/test_video.mp4', 'rb')
        tb = telebot.TeleBot(TOKEN)
        medias = [types.InputMediaPhoto(photo, "View"),
                  types.InputMediaVideo(video)]
        result = tb.send_media_group(CHAT_ID, medias)
        assert len(result) == 2
        assert result[0].media_group_id is not None
        assert result[1].media_group_id is not None

    def test_send_photo_formating_caption(self):
        file_data = open('../examples/detailed_example/kitten.jpg', 'rb')
        tb = telebot.TeleBot(TOKEN)
        ret_msg = tb.send_photo(CHAT_ID, file_data, caption='_italic_', parse_mode='Markdown')
        assert ret_msg.caption_entities[0].type == 'italic'

    def test_send_video_formatting_caption(self):
        file_data = open('./test_data/test_video.mp4', 'rb')
        tb = telebot.TeleBot(TOKEN)
        ret_msg = tb.send_video(CHAT_ID, file_data, caption='_italic_', parse_mode='Markdown')
        assert ret_msg.caption_entities[0].type == 'italic'

    def test_send_audio_formatting_caption(self):
        file_data = open('./test_data/record.mp3', 'rb')
        tb = telebot.TeleBot(TOKEN)
        ret_msg = tb.send_audio(CHAT_ID, file_data, caption='<b>bold</b>', parse_mode='HTML')
        assert ret_msg.caption_entities[0].type == 'bold'

    def test_send_voice_formatting_caprion(self):
        file_data = open('./test_data/record.ogg', 'rb')
        tb = telebot.TeleBot(TOKEN)
        ret_msg = tb.send_voice(CHAT_ID, file_data, caption='<b>bold</b>', parse_mode='HTML')
        assert ret_msg.caption_entities[0].type == 'bold'
        assert ret_msg.voice.mime_type == 'audio/ogg'

    def test_send_media_group_formatting_caption(self):
        tb = telebot.TeleBot(TOKEN)
        img1 = 'https://i.imgur.com/CjXjcnU.png'
        img2 = 'https://i.imgur.com/CjXjcnU.png'
        medias = [types.InputMediaPhoto(img1, "*View*", parse_mode='Markdown'),
                  types.InputMediaPhoto(img2, "_Dog_", parse_mode='Markdown')]
        result = tb.send_media_group(CHAT_ID, medias)
        assert len(result) == 2
        assert result[0].media_group_id is not None
        assert result[0].caption_entities[0].type == 'bold'
        assert result[1].caption_entities[0].type == 'italic'

    def test_send_document_formating_caption(self):
        file_data = open('../examples/detailed_example/kitten.jpg', 'rb')
        tb = telebot.TeleBot(TOKEN)
        ret_msg = tb.send_document(CHAT_ID, file_data, caption='_italic_', parse_mode='Markdown')
        assert ret_msg.caption_entities[0].type == 'italic'
