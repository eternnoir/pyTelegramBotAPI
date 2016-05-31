# -*- coding: utf-8 -*-
import pytest
import os

import telebot
from telebot import types

should_run = 'TOKEN' and 'CHAT_ID' not in os.environ

if not should_run:
    TOKEN = os.environ['TOKEN']
    CHAT_ID = os.environ['CHAT_ID']


@pytest.mark.skipif(not should_run, reason="No environment variables configured")
class TestTeleBot:
    def test_message_listener(self):
        msg_list = []
        for x in range(100):
            msg_list.append(self.create_text_message('Message ' + str(x)))

        class C:
            def __init__(self):
                self.recv = 0

            def __call__(self, _):
                self.recv += 1

        tb = self.create_telebot()
        listener = C()
        tb.add_update_listener(listener)
        tb.process_new_updates(self.messages_to_updates(msg_list))

        assert listener.recv == 100

    def test_message_handler(self):
        tb = self.create_telebot()

        @tb.message_handler(commands=['help', 'start'])
        def command_handler(message):
            message.text = 'ok'

        msg = self.create_text_message('/help')
        tb.process_new_updates(self.messages_to_updates([msg]))
        assert msg.text == 'ok'

    def test_message_handler_reg(self):
        bot = self.create_telebot()

        @bot.message_handler(regexp='((https?):((//)|(\\\\))+([\w\d:#@%/;$()~_?\+-=\\\.&](#!)?)*)')
        def command_url(message):
            message.text = 'ok'

        msg = self.create_text_message(r'https://web.telegram.org/')
        bot.process_new_updates(self.messages_to_updates([msg]))
        assert msg.text == 'ok'

    def test_message_handler_lambda(self):
        bot = self.create_telebot()

        @bot.message_handler(func=lambda message: 'lambda' in message.text)
        def command_url(message):
            message.text = 'ok'

        msg = self.create_text_message('lambda_text')
        bot.process_new_updates(self.messages_to_updates([msg]))
        assert msg.text == 'ok'

    def test_message_handler_lambda_fail(self):
        bot = self.create_telebot()

        @bot.message_handler(func=lambda message: 'lambda' in message.text)
        def command_url(message):
            message.text = 'ok'

        msg = self.create_text_message('text')
        bot.process_new_updates(self.messages_to_updates([msg]))
        assert msg.text != 'ok'

    def test_message_handler_reg_fail(self):
        bot = self.create_telebot()

        @bot.message_handler(regexp='((https?):((//)|(\\\\))+([\w\d:#@%/;$()~_?\+-=\\\.&](#!)?)*)')
        def command_url(message):
            message.text = 'ok'

        msg = self.create_text_message(r'web.telegram.org/')
        bot.process_new_updates(self.messages_to_updates([msg]))
        assert not msg.text == 'ok'

    def test_send_message_with_markdown(self):
        tb = self.create_telebot()
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
        file_data = open('examples/detailed_example/kitten.jpg')
        tb = telebot.TeleBot(TOKEN)
        ret_msg = tb.send_document(CHAT_ID, file_data)
        assert ret_msg.message_id

        ret_msg = tb.send_document(CHAT_ID, ret_msg.document.file_id)
        assert ret_msg.message_id

    def test_send_file_dis_noti(self):
        file_data = open('examples/detailed_example/kitten.jpg')
        tb = telebot.TeleBot(TOKEN)
        ret_msg = tb.send_document(CHAT_ID, file_data, disable_notification=True)
        assert ret_msg.message_id

        ret_msg = tb.send_document(CHAT_ID, ret_msg.document.file_id)
        assert ret_msg.message_id

    def test_send_video(self):
        file_data = self.get_test_data('test_video.mp4')
        tb = telebot.TeleBot(TOKEN)
        ret_msg = tb.send_video(CHAT_ID, file_data)
        assert ret_msg.message_id

    def test_send_video_dis_noti(self):
        file_data = self.get_test_data('test_video.mp4')
        tb = telebot.TeleBot(TOKEN)
        ret_msg = tb.send_video(CHAT_ID, file_data, disable_notification=True)
        assert ret_msg.message_id

    def test_send_video_more_params(self):
        file_data = self.get_test_data('test_video.mp4')
        tb = telebot.TeleBot(TOKEN)
        ret_msg = tb.send_video(CHAT_ID, file_data)
        assert ret_msg.message_id

    def test_send_video_more_params_dis_noti(self):
        file_data = self.get_test_data('test_video.mp4')
        tb = telebot.TeleBot(TOKEN)
        ret_msg = tb.send_video(CHAT_ID, file_data, duration=1, disable_notification=True)
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
        file_data = open('examples/detailed_example/kitten.jpg')
        tb = telebot.TeleBot(TOKEN)
        ret_msg = tb.send_photo(CHAT_ID, file_data)
        assert ret_msg.message_id

        ret_msg = tb.send_photo(CHAT_ID, ret_msg.photo[0].file_id)
        assert ret_msg.message_id

    def test_send_photo_dis_noti(self):
        file_data = open('examples/detailed_example/kitten.jpg')
        tb = telebot.TeleBot(TOKEN)
        ret_msg = tb.send_photo(CHAT_ID, file_data)
        assert ret_msg.message_id

        ret_msg = tb.send_photo(CHAT_ID, ret_msg.photo[0].file_id, disable_notification=True)
        assert ret_msg.message_id

    def test_send_audio(self):
        file_data = self.get_test_data('record.mp3')
        tb = telebot.TeleBot(TOKEN)
        ret_msg = tb.send_audio(CHAT_ID, file_data, duration=1, performer='eternnoir', title='pyTelegram')
        assert ret_msg.content_type == 'audio'
        assert ret_msg.audio.performer == 'eternnoir'
        assert ret_msg.audio.title == 'pyTelegram'

    def test_send_audio_dis_noti(self):
        file_data = self.get_test_data('record.mp3')
        tb = telebot.TeleBot(TOKEN)
        opts = {'duration': 1, 'performer': 'eternnoir', 'title': 'pyTelegram', 'disable_notification': True}
        ret_msg = tb.send_audio(CHAT_ID, file_data, **opts)
        assert ret_msg.content_type == 'audio'
        assert ret_msg.audio.performer == 'eternnoir'
        assert ret_msg.audio.title == 'pyTelegram'

    def test_send_voice(self):
        file_data = self.get_test_data('record.ogg')
        tb = telebot.TeleBot(TOKEN)
        ret_msg = tb.send_voice(CHAT_ID, file_data)
        assert ret_msg.voice.mime_type == 'audio/ogg'

    def test_send_voice_dis_noti(self):
        file_data = self.get_test_data('record.ogg')
        tb = telebot.TeleBot(TOKEN)
        ret_msg = tb.send_voice(CHAT_ID, file_data, disable_notification=True)
        assert ret_msg.voice.mime_type == 'audio/ogg'

    def test_get_file(self):
        file_data = self.get_test_data('record.ogg')
        tb = telebot.TeleBot(TOKEN)
        ret_msg = tb.send_voice(CHAT_ID, file_data)
        file_id = ret_msg.voice.file_id
        file_info = tb.get_file(file_id)
        assert file_info.file_id == file_id

    def test_get_file_dis_noti(self):
        file_data = self.get_test_data('record.ogg')
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

    def test_send_venue_dis_noti(self):
        tb = telebot.TeleBot(TOKEN)
        lat = 26.3875591
        lon = -161.2901042
        ret_msg = tb.send_venue(CHAT_ID, lat, lon, "Test Venue", "1123 Test Venue address", disable_notification=True)
        assert ret_msg.venue.title == "Test Venue"

    def test_chat(self):
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

    @pytest.mark.xfail(reason="Broken", run=False)
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
        chat = types.Chat(11, 'private', first_name='test')
        return types.Message(1, None, None, chat, text=text)

    @staticmethod
    def create_telebot():
        return telebot.TeleBot(TOKEN, None)

    @staticmethod
    def messages_to_updates(messages):
        return [types.Update(1, message=message) for message in messages]

    @staticmethod
    def get_test_data(filename):
        return open('./tests/test_data/' + filename, 'rb')
