import asyncio
import os
import time
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
import aiohttp

import pytest
from dotenv import load_dotenv

import telebot
from telebot import AsyncTeleBot, types, util
from telebot import api

load_dotenv()

try:
    TOKEN = os.environ["TOKEN"]
    CHAT_ID = os.environ["CHAT_ID"]
    GROUP_ID = os.environ["GROUP_ID"]
    skip_reason_msg = None
except KeyError as e:
    skip_reason_msg = f"Required env variable not found: {e}"


CUR_DIR = Path(__file__).parent
DATA_DIR = CUR_DIR / "test_data"

IMAGE = DATA_DIR / "image.jpg"


@pytest.fixture(scope="class")
def bot(request) -> AsyncTeleBot:
    bot = AsyncTeleBot(TOKEN)
    request.cls.bot = bot


@pytest.fixture(scope="session")
def event_loop():
    """Running all tests in the same loop"""
    yield asyncio.get_event_loop()


@pytest.fixture(scope="session")
async def teardown():
    yield
    await api.session_manager.close_session()


class _HasBotAttr:
    bot: AsyncTeleBot


def respect_rate_limit(method):
    async def decorated(*args, **kwargs):
        await asyncio.sleep(1)
        return await method(*args, **kwargs)
    
    return decorated


@pytest.mark.skipif(skip_reason_msg is not None, reason=skip_reason_msg or "")
@pytest.mark.usefixtures("bot", "teardown")
class TestIntegration(_HasBotAttr):
    async def passed(self):
        await self.bot.send_message(CHAT_ID, "✅")

    @respect_rate_limit
    async def test_send_message_with_markdown(self):
        markdown = """
        *bold text*
        _italic text_
        [text](URL)
        """
        ret_msg = await self.bot.send_message(CHAT_ID, markdown, parse_mode="Markdown")
        assert ret_msg.message_id
        await self.passed()

    @respect_rate_limit
    async def test_send_message_with_disable_notification(self):
        markdown = """
        *bold text*
        _italic text_
        [text](URL)
        """
        ret_msg = await self.bot.send_message(CHAT_ID, markdown, parse_mode="Markdown", disable_notification=True)
        assert ret_msg.message_id
        await self.passed()

    # async def test_send_file(self):
    #     with open(IMAGE, "rb") as image_file:
    #         tb = telebot.AsyncTeleBot(TOKEN)
    #         await tb.send_message(CHAT_ID, "This should send the same image twice")
    #         ret_msg = await tb.send_document(CHAT_ID, image_file)
    #         assert ret_msg.message_id

    #     ret_msg = await tb.send_document(CHAT_ID, ret_msg.document.file_id)
    #     assert ret_msg.message_id
    #     await send_test_passed(tb)

    # async def test_send_file_with_filename(self):
    #     with open(IMAGE, "rb") as image_file:
    #         tb = telebot.AsyncTeleBot(TOKEN)
    #         ret_msg = await tb.send_document(CHAT_ID, image_file)
    #         assert ret_msg.message_id
    #         ret_msg = await tb.send_document(CHAT_ID, image_file, visible_file_name="test.jpg")
    #         assert ret_msg.message_id
    #     await send_test_passed(tb)

    # async def test_send_file_dis_noti(self):
    #     file_data = open("../examples/detailed_example/kitten.jpg", "rb")
    #     tb = telebot.AsyncTeleBot(TOKEN)
    #     ret_msg = await tb.send_document(CHAT_ID, file_data, disable_notification=True)
    #     assert ret_msg.message_id

    #     ret_msg = await tb.send_document(CHAT_ID, ret_msg.document.file_id)
    #     assert ret_msg.message_id

    # async def test_send_file_caption(self):
    #     file_data = open("../examples/detailed_example/kitten.jpg", "rb")
    #     tb = telebot.AsyncTeleBot(TOKEN)
    #     ret_msg = await tb.send_document(CHAT_ID, file_data, caption="Test")
    #     assert ret_msg.message_id

    #     ret_msg = await tb.send_document(CHAT_ID, ret_msg.document.file_id)
    #     assert ret_msg.message_id

    # async def test_send_video(self):
    #     file_data = open("./test_data/test_video.mp4", "rb")
    #     tb = telebot.AsyncTeleBot(TOKEN)
    #     ret_msg = await tb.send_video(CHAT_ID, file_data)
    #     assert ret_msg.message_id

    # async def test_send_video_dis_noti(self):
    #     file_data = open("./test_data/test_video.mp4", "rb")
    #     tb = telebot.AsyncTeleBot(TOKEN)
    #     ret_msg = await tb.send_video(CHAT_ID, file_data, disable_notification=True)
    #     assert ret_msg.message_id

    # async def test_send_video_more_params(self):
    #     file_data = open("./test_data/test_video.mp4", "rb")
    #     tb = telebot.AsyncTeleBot(TOKEN)
    #     ret_msg = await tb.send_video(CHAT_ID, file_data, 1)
    #     assert ret_msg.message_id

    # async def test_send_video_more_params_dis_noti(self):
    #     file_data = open("./test_data/test_video.mp4", "rb")
    #     tb = telebot.AsyncTeleBot(TOKEN)
    #     ret_msg = await tb.send_video(CHAT_ID, file_data, 1, disable_notification=True)
    #     assert ret_msg.message_id

    # async def test_send_file_exception(self):
    #     tb = telebot.AsyncTeleBot(TOKEN)
    #     try:
    #         await tb.send_document(CHAT_ID, None)
    #         assert False
    #     except Exception as e:
    #         print(e)
    #         assert True

    # async def test_send_photo(self):
    #     file_data = open("../examples/detailed_example/kitten.jpg", "rb")
    #     tb = telebot.AsyncTeleBot(TOKEN)
    #     ret_msg = await tb.send_photo(CHAT_ID, file_data)
    #     assert ret_msg.message_id

    #     ret_msg = await tb.send_photo(CHAT_ID, ret_msg.photo[0].file_id)
    #     assert ret_msg.message_id

    # async def test_send_photo_dis_noti(self):
    #     file_data = open("../examples/detailed_example/kitten.jpg", "rb")
    #     tb = telebot.AsyncTeleBot(TOKEN)
    #     ret_msg = await tb.send_photo(CHAT_ID, file_data)
    #     assert ret_msg.message_id

    #     ret_msg = await tb.send_photo(CHAT_ID, ret_msg.photo[0].file_id, disable_notification=True)
    #     assert ret_msg.message_id

    # async def test_send_audio(self):
    #     file_data = open("./test_data/record.mp3", "rb")
    #     tb = telebot.AsyncTeleBot(TOKEN)
    #     ret_msg = await tb.send_audio(CHAT_ID, file_data, duration=1, performer="eternnoir", title="pyTelegram")
    #     assert ret_msg.content_type == "audio"
    #     assert ret_msg.audio.performer == "eternnoir"
    #     assert ret_msg.audio.title == "pyTelegram"

    # async def test_send_audio_dis_noti(self):
    #     file_data = open("./test_data/record.mp3", "rb")
    #     tb = telebot.AsyncTeleBot(TOKEN)
    #     ret_msg = await tb.send_audio(
    #         CHAT_ID,
    #         file_data,
    #         duration=1,
    #         performer="eternnoir",
    #         title="pyTelegram",
    #         disable_notification=True,
    #     )
    #     assert ret_msg.content_type == "audio"
    #     assert ret_msg.audio.performer == "eternnoir"
    #     assert ret_msg.audio.title == "pyTelegram"

    # async def test_send_voice(self):
    #     file_data = open("./test_data/record.ogg", "rb")
    #     tb = telebot.AsyncTeleBot(TOKEN)
    #     ret_msg = await tb.send_voice(CHAT_ID, file_data)
    #     assert ret_msg.voice.mime_type == "audio/ogg"

    # async def test_send_voice_dis_noti(self):
    #     file_data = open("./test_data/record.ogg", "rb")
    #     tb = telebot.AsyncTeleBot(TOKEN)
    #     ret_msg = await tb.send_voice(CHAT_ID, file_data, disable_notification=True)
    #     assert ret_msg.voice.mime_type == "audio/ogg"

    # async def test_get_file(self):
    #     file_data = open("./test_data/record.ogg", "rb")
    #     tb = telebot.AsyncTeleBot(TOKEN)
    #     ret_msg = await tb.send_voice(CHAT_ID, file_data)
    #     file_id = ret_msg.voice.file_id
    #     file_info = await tb.get_file(file_id)
    #     assert file_info.file_id == file_id

    # async def test_get_file_dis_noti(self):
    #     file_data = open("./test_data/record.ogg", "rb")
    #     tb = telebot.AsyncTeleBot(TOKEN)
    #     ret_msg = await tb.send_voice(CHAT_ID, file_data, disable_notification=True)
    #     file_id = ret_msg.voice.file_id
    #     file_info = await tb.get_file(file_id)
    #     assert file_info.file_id == file_id

    # async def test_send_message(self):
    #     text = "CI Test Message"
    #     tb = telebot.AsyncTeleBot(TOKEN)
    #     ret_msg = await tb.send_message(CHAT_ID, text)
    #     assert ret_msg.message_id

    # async def test_send_dice(self):
    #     tb = telebot.AsyncTeleBot(TOKEN)
    #     ret_msg = await tb.send_dice(CHAT_ID, emoji="🎯")
    #     assert ret_msg.message_id
    #     assert ret_msg.content_type == "dice"

    # async def test_send_message_dis_noti(self):
    #     text = "CI Test Message"
    #     tb = telebot.AsyncTeleBot(TOKEN)
    #     ret_msg = await tb.send_message(CHAT_ID, text, disable_notification=True)
    #     assert ret_msg.message_id

    # async def test_send_message_with_markup(self):
    #     text = "CI Test Message"
    #     tb = telebot.AsyncTeleBot(TOKEN)
    #     markup = types.ReplyKeyboardMarkup()
    #     markup.add(types.KeyboardButton("1"))
    #     markup.add(types.KeyboardButton("2"))
    #     ret_msg = await tb.send_message(CHAT_ID, text, disable_notification=True, reply_markup=markup)
    #     assert ret_msg.message_id

    # async def test_send_message_with_markup_use_string(self):
    #     text = "CI Test Message"
    #     tb = telebot.AsyncTeleBot(TOKEN)
    #     markup = types.ReplyKeyboardMarkup()
    #     markup.add("1")
    #     markup.add("2")
    #     markup.add("3")
    #     markup.add("4")
    #     ret_msg = await tb.send_message(CHAT_ID, text, disable_notification=True, reply_markup=markup)
    #     assert ret_msg.message_id

    # async def test_send_message_with_inlinemarkup(self):
    #     text = "CI Test Message"
    #     tb = telebot.AsyncTeleBot(TOKEN)
    #     markup = types.InlineKeyboardMarkup()
    #     markup.add(types.InlineKeyboardButton("Google", url="http://www.google.com"))
    #     markup.add(types.InlineKeyboardButton("Yahoo", url="http://www.yahoo.com"))
    #     ret_msg = await tb.send_message(CHAT_ID, text, disable_notification=True, reply_markup=markup)
    #     assert ret_msg.message_id

    # async def test_forward_message(self):
    #     text = "CI forward_message Test Message"
    #     tb = telebot.AsyncTeleBot(TOKEN)
    #     msg = await tb.send_message(CHAT_ID, text)
    #     ret_msg = await tb.forward_message(CHAT_ID, CHAT_ID, msg.message_id)
    #     assert ret_msg.forward_from

    # async def test_copy_message(self):
    #     text = "CI copy_message Test Message"
    #     tb = telebot.AsyncTeleBot(TOKEN)
    #     msg = await tb.send_message(CHAT_ID, text)
    #     ret_msg = await tb.copy_message(CHAT_ID, CHAT_ID, msg.message_id)
    #     assert ret_msg

    # async def test_forward_message_dis_noti(self):
    #     text = "CI forward_message Test Message"
    #     tb = telebot.AsyncTeleBot(TOKEN)
    #     msg = await tb.send_message(CHAT_ID, text)
    #     ret_msg = await tb.forward_message(CHAT_ID, CHAT_ID, msg.message_id, disable_notification=True)
    #     assert ret_msg.forward_from

    # async def test_reply_to(self):
    #     text = "CI reply_to Test Message"
    #     tb = telebot.AsyncTeleBot(TOKEN)
    #     msg = await tb.send_message(CHAT_ID, text)
    #     ret_msg = await tb.reply_to(msg, text + " REPLY")
    #     assert ret_msg.reply_to_message.message_id == msg.message_id

    # async def test_register_for_reply(self):
    #     text = "CI reply_to Test Message"
    #     tb = telebot.AsyncTeleBot(TOKEN)
    #     msg = await tb.send_message(CHAT_ID, text, reply_markup=types.ForceReply())
    #     reply_msg = await tb.reply_to(msg, text + " REPLY")

    #     async def process_reply(message):
    #         assert msg.message_id == message.reply_to_message.message_id

    #     await tb.register_for_reply(msg, process_reply)

    #     await tb.process_new_messages([reply_msg])

    # async def test_send_location(self):
    #     tb = telebot.AsyncTeleBot(TOKEN)
    #     lat = 26.3875591
    #     lon = -161.2901042
    #     ret_msg = await tb.send_location(CHAT_ID, lat, lon)
    #     assert int(ret_msg.location.longitude) == int(lon)
    #     assert int(ret_msg.location.latitude) == int(lat)

    # async def test_send_location_dis_noti(self):
    #     tb = telebot.AsyncTeleBot(TOKEN)
    #     lat = 26.3875591
    #     lon = -161.2901042
    #     ret_msg = await tb.send_location(CHAT_ID, lat, lon, disable_notification=True)
    #     assert int(ret_msg.location.longitude) == int(lon)
    #     assert int(ret_msg.location.latitude) == int(lat)

    # async def test_send_venue(self):
    #     tb = telebot.AsyncTeleBot(TOKEN)
    #     lat = 26.3875591
    #     lon = -161.2901042
    #     ret_msg = await tb.send_venue(CHAT_ID, lat, lon, "Test Venue", "1123 Test Venue address")
    #     assert ret_msg.venue.title == "Test Venue"
    #     assert int(lat) == int(ret_msg.venue.location.latitude)

    # async def test_send_venue_dis_noti(self):
    #     tb = telebot.AsyncTeleBot(TOKEN)
    #     lat = 26.3875591
    #     lon = -161.2901042
    #     ret_msg = await tb.send_venue(
    #         CHAT_ID,
    #         lat,
    #         lon,
    #         "Test Venue",
    #         "1123 Test Venue address",
    #         disable_notification=True,
    #     )
    #     assert ret_msg.venue.title == "Test Venue"

    # async def test_Chat(self):
    #     tb = telebot.AsyncTeleBot(TOKEN)
    #     me = await tb.get_me()
    #     msg = await tb.send_message(CHAT_ID, "Test")
    #     assert me.id == msg.from_user.id
    #     assert msg.chat.id == int(CHAT_ID)

    # async def test_edit_message_text(self):
    #     tb = telebot.AsyncTeleBot(TOKEN)
    #     msg = await tb.send_message(CHAT_ID, "Test")
    #     new_msg = await tb.edit_message_text("Edit test", chat_id=CHAT_ID, message_id=msg.message_id)
    #     assert new_msg.text == "Edit test"

    # async def test_edit_message_caption(self):
    #     file_data = open("../examples/detailed_example/kitten.jpg", "rb")
    #     tb = telebot.AsyncTeleBot(TOKEN)
    #     msg = await tb.send_document(CHAT_ID, file_data, caption="Test")
    #     new_msg = await tb.edit_message_caption(caption="Edit test", chat_id=CHAT_ID, message_id=msg.message_id)
    #     assert new_msg.caption == "Edit test"

    # async def test_edit_message_media(self):
    #     file_data = open("../examples/detailed_example/kitten.jpg", "rb")
    #     file_data_2 = open("../examples/detailed_example/rooster.jpg", "rb")
    #     tb = telebot.AsyncTeleBot(TOKEN)
    #     msg = await tb.send_photo(CHAT_ID, file_data)
    #     new_msg = await tb.edit_message_media(
    #         chat_id=CHAT_ID,
    #         message_id=msg.message_id,
    #         media=types.InputMediaPhoto(file_data_2, caption="Test editMessageMedia 0"),
    #     )
    #     assert type(new_msg) != bool

    #     new_msg = await tb.edit_message_media(
    #         chat_id=CHAT_ID,
    #         message_id=msg.message_id,
    #         media=types.InputMediaPhoto(msg.photo[0].file_id, caption="Test editMessageMedia"),
    #     )
    #     assert type(new_msg) != bool
    #     assert new_msg.caption == "Test editMessageMedia"

    # async def test_get_chat(self):
    #     tb = telebot.AsyncTeleBot(TOKEN)
    #     ch = await tb.get_chat(GROUP_ID)
    #     assert str(ch.id) == GROUP_ID

    # async def test_get_chat_administrators(self):
    #     tb = telebot.AsyncTeleBot(TOKEN)
    #     cas = await tb.get_chat_administrators(GROUP_ID)
    #     assert len(cas) > 0

    # async def test_get_chat_members_count(self):
    #     tb = telebot.AsyncTeleBot(TOKEN)
    #     cn = await tb.get_chat_members_count(GROUP_ID)
    #     assert cn > 1

    # async def test_export_chat_invite_link(self):
    #     tb = telebot.AsyncTeleBot(TOKEN)
    #     il = await tb.export_chat_invite_link(GROUP_ID)
    #     assert isinstance(il, str)

    # async def test_create_revoke_detailed_chat_invite_link(self):
    #     tb = telebot.AsyncTeleBot(TOKEN)
    #     cil = await tb.create_chat_invite_link(GROUP_ID, expire_date=datetime.now() + timedelta(minutes=1), member_limit=5)
    #     assert isinstance(cil.invite_link, str)
    #     assert cil.creator.id == await tb.get_me().id
    #     assert isinstance(cil.expire_date, (float, int))
    #     assert cil.member_limit == 5
    #     assert not cil.is_revoked
    #     rcil = await tb.revoke_chat_invite_link(GROUP_ID, cil.invite_link)
    #     assert rcil.is_revoked

    # async def test_edit_markup(self):
    #     text = "CI Test Message"
    #     tb = telebot.AsyncTeleBot(TOKEN)
    #     markup = types.InlineKeyboardMarkup()
    #     markup.add(types.InlineKeyboardButton("Google", url="http://www.google.com"))
    #     markup.add(types.InlineKeyboardButton("Yahoo", url="http://www.yahoo.com"))
    #     ret_msg = await tb.send_message(CHAT_ID, text, disable_notification=True, reply_markup=markup)
    #     markup.add(types.InlineKeyboardButton("Google2", url="http://www.google.com"))
    #     markup.add(types.InlineKeyboardButton("Yahoo2", url="http://www.yahoo.com"))
    #     new_msg = await tb.edit_message_reply_markup(chat_id=CHAT_ID, message_id=ret_msg.message_id, reply_markup=markup)
    #     assert new_msg.message_id

    # async def test_antiflood(self):
    #     text = "Testing antiflood function"
    #     tb = telebot.AsyncTeleBot(TOKEN)
    #     i = -1
    #     for i in range(0, 200):
    #         util.antiflood(await tb.send_message, CHAT_ID, text)
    #     assert i == 199

    # async def test_send_video_note(self):
    #     file_data = open("./test_data/test_video.mp4", "rb")
    #     tb = telebot.AsyncTeleBot(TOKEN)
    #     ret_msg = await tb.send_video_note(CHAT_ID, file_data)
    #     assert ret_msg.message_id

    # async def test_send_media_group(self):
    #     tb = telebot.AsyncTeleBot(TOKEN)
    #     img1 = "https://i.imgur.com/CjXjcnU.png"
    #     img2 = "https://i.imgur.com/CjXjcnU.png"
    #     medias = [
    #         types.InputMediaPhoto(img1, "View"),
    #         types.InputMediaPhoto(img2, "Dog"),
    #     ]
    #     result = await tb.send_media_group(CHAT_ID, medias)
    #     assert len(result) == 2
    #     assert result[0].media_group_id is not None
    #     assert result[0].media_group_id == result[1].media_group_id

    # async def test_send_media_group_local_files(self):
    #     photo = open("../examples/detailed_example/kitten.jpg", "rb")
    #     video = open("./test_data/test_video.mp4", "rb")
    #     tb = telebot.AsyncTeleBot(TOKEN)
    #     medias = [types.InputMediaPhoto(photo, "View"), types.InputMediaVideo(video)]
    #     result = await tb.send_media_group(CHAT_ID, medias)
    #     assert len(result) == 2
    #     assert result[0].media_group_id is not None
    #     assert result[1].media_group_id is not None

    # async def test_send_photo_formating_caption(self):
    #     file_data = open("../examples/detailed_example/kitten.jpg", "rb")
    #     tb = telebot.AsyncTeleBot(TOKEN)
    #     ret_msg = await tb.send_photo(CHAT_ID, file_data, caption="_italic_", parse_mode="Markdown")
    #     assert ret_msg.caption_entities[0].type == "italic"

    # async def test_send_video_formatting_caption(self):
    #     file_data = open("./test_data/test_video.mp4", "rb")
    #     tb = telebot.AsyncTeleBot(TOKEN)
    #     ret_msg = await tb.send_video(CHAT_ID, file_data, caption="_italic_", parse_mode="Markdown")
    #     assert ret_msg.caption_entities[0].type == "italic"

    # async def test_send_audio_formatting_caption(self):
    #     file_data = open("./test_data/record.mp3", "rb")
    #     tb = telebot.AsyncTeleBot(TOKEN)
    #     ret_msg = await tb.send_audio(CHAT_ID, file_data, caption="<b>bold</b>", parse_mode="HTML")
    #     assert ret_msg.caption_entities[0].type == "bold"

    # async def test_send_voice_formatting_caprion(self):
    #     file_data = open("./test_data/record.ogg", "rb")
    #     tb = telebot.AsyncTeleBot(TOKEN)
    #     ret_msg = await tb.send_voice(CHAT_ID, file_data, caption="<b>bold</b>", parse_mode="HTML")
    #     assert ret_msg.caption_entities[0].type == "bold"
    #     assert ret_msg.voice.mime_type == "audio/ogg"

    # async def test_send_media_group_formatting_caption(self):
    #     tb = telebot.AsyncTeleBot(TOKEN)
    #     img1 = "https://i.imgur.com/CjXjcnU.png"
    #     img2 = "https://i.imgur.com/CjXjcnU.png"
    #     medias = [
    #         types.InputMediaPhoto(img1, "*View*", parse_mode="Markdown"),
    #         types.InputMediaPhoto(img2, "_Dog_", parse_mode="Markdown"),
    #     ]
    #     result = await tb.send_media_group(CHAT_ID, medias)
    #     assert len(result) == 2
    #     assert result[0].media_group_id is not None
    #     assert result[0].caption_entities[0].type == "bold"
    #     assert result[1].caption_entities[0].type == "italic"

    # async def test_send_document_formating_caption(self):
    #     file_data = open("../examples/detailed_example/kitten.jpg", "rb")
    #     tb = telebot.AsyncTeleBot(TOKEN)
    #     ret_msg = await tb.send_document(CHAT_ID, file_data, caption="_italic_", parse_mode="Markdown")
    #     assert ret_msg.caption_entities[0].type == "italic"

    # async def test_chat_commands(self):
    #     tb = telebot.AsyncTeleBot(TOKEN)
    #     command, description, lang = "command_1", "description of command 1", "en"
    #     scope = telebot.types.BotCommandScopeChat(CHAT_ID)
    #     ret_msg = await tb.set_my_commands([telebot.types.BotCommand(command, description)], scope, lang)
    #     assert ret_msg is True

    #     ret_msg = await tb.get_my_commands(scope=scope, language_code=lang)
    #     assert ret_msg[0].command == command
    #     assert ret_msg[0].description == description

    #     ret_msg = await tb.delete_my_commands(scope=scope, language_code=lang)
    #     assert ret_msg is True

    #     ret_msg = await tb.get_my_commands(scope=scope, language_code=lang)
    #     assert ret_msg == []
