import asyncio
import os
from datetime import datetime, timedelta
from pathlib import Path

import pytest
from dotenv import load_dotenv

from telebot import AsyncTeleBot, api, types

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
IMAGE_2 = DATA_DIR / "image2.jpg"
VIDEO = DATA_DIR / "test_video.mp4"
AUDIO_MP3 = DATA_DIR / "test_audio.mp3"
AUDIO_WAV = DATA_DIR / "test_audio.wav"
AUDIO_OGG = DATA_DIR / "test_audio.ogg"


@pytest.fixture(scope="class")
def bot_attr(request):
    bot = AsyncTeleBot(TOKEN)
    request.cls.bot = bot
    return


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
    async def decorated(self: "TestIntegration"):
        await asyncio.sleep(1)
        await method(self)
        await self.passed()

    return decorated


@pytest.mark.skipif(skip_reason_msg is not None, reason=skip_reason_msg or "")
@pytest.mark.usefixtures("bot_attr", "teardown")
@pytest.mark.integration
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

    @respect_rate_limit
    async def test_send_message_with_disable_notification(self):
        markdown = """
        *bold text*
        _italic text_
        [text](URL)
        """
        ret_msg = await self.bot.send_message(CHAT_ID, markdown, parse_mode="Markdown", disable_notification=True)
        assert ret_msg.message_id

    @respect_rate_limit
    async def test_send_file(self):
        with open(IMAGE, "rb") as image_file:
            ret_msg = await self.bot.send_document(CHAT_ID, image_file)
            assert ret_msg.message_id
        ret_msg = await self.bot.send_document(CHAT_ID, ret_msg.document.file_id)
        assert ret_msg.message_id

    @respect_rate_limit
    async def test_send_file_with_filename(self):
        with open(IMAGE, "rb") as image_file:
            ret_msg = await self.bot.send_document(CHAT_ID, image_file)
            assert ret_msg.message_id
        with open(IMAGE, "rb") as image_file:
            ret_msg = await self.bot.send_document(CHAT_ID, image_file, visible_file_name="test.jpg")
            assert ret_msg.message_id

    @respect_rate_limit
    async def test_send_file_dis_noti(self):
        with open(IMAGE, "rb") as image_file:
            ret_msg = await self.bot.send_document(CHAT_ID, image_file, disable_notification=True)
            assert ret_msg.message_id
            ret_msg = await self.bot.send_document(CHAT_ID, ret_msg.document.file_id)
            assert ret_msg.message_id

    @respect_rate_limit
    async def test_send_file_caption(self):
        with open(IMAGE, "rb") as image_file:
            ret_msg = await self.bot.send_document(CHAT_ID, image_file, caption="Test")
            assert ret_msg.message_id
            ret_msg = await self.bot.send_document(CHAT_ID, ret_msg.document.file_id)
            assert ret_msg.message_id

    @respect_rate_limit
    async def test_send_video(self):
        with open(VIDEO, "rb") as video_file:
            ret_msg = await self.bot.send_video(CHAT_ID, video_file)
            assert ret_msg.message_id

    @respect_rate_limit
    async def test_send_video_dis_noti(self):
        with open(VIDEO, "rb") as video_file:
            ret_msg = await self.bot.send_video(CHAT_ID, video_file, disable_notification=True)
            assert ret_msg.message_id

    @respect_rate_limit
    async def test_send_video_more_params(self):
        with open(VIDEO, "rb") as video_file:
            ret_msg = await self.bot.send_video(CHAT_ID, video_file, duration=0.5)
            assert ret_msg.message_id

    @respect_rate_limit
    async def test_send_video_more_params_dis_noti(self):
        with open(VIDEO, "rb") as video_file:
            ret_msg = await self.bot.send_video(CHAT_ID, video_file, 1, disable_notification=True)
            assert ret_msg.message_id

    @respect_rate_limit
    async def test_send_file_exception(self):
        with pytest.raises(Exception):
            await self.bot.send_document(CHAT_ID, None)

    @respect_rate_limit
    async def test_send_photo(self):
        with open(IMAGE, "rb") as image_file:
            ret_msg = await self.bot.send_photo(CHAT_ID, image_file)
            assert ret_msg.message_id
            ret_msg = await self.bot.send_photo(CHAT_ID, ret_msg.photo[0].file_id)
            assert ret_msg.message_id

    @respect_rate_limit
    async def test_send_photo_dis_noti(self):
        with open(IMAGE, "rb") as image_file:
            ret_msg = await self.bot.send_photo(CHAT_ID, image_file)
            assert ret_msg.message_id
            ret_msg = await self.bot.send_photo(CHAT_ID, ret_msg.photo[0].file_id, disable_notification=True)
            assert ret_msg.message_id

    @respect_rate_limit
    async def test_send_audio(self):
        with open(AUDIO_MP3, "rb") as audio_file:
            ret_msg = await self.bot.send_audio(
                CHAT_ID, audio_file, duration=1, performer="eternnoir", title="pyTelegram"
            )
            assert ret_msg.content_type == "audio"
            assert ret_msg.audio.performer == "eternnoir"
            assert ret_msg.audio.title == "pyTelegram"

    @respect_rate_limit
    async def test_send_audio_dis_noti(self):
        with open(AUDIO_MP3, "rb") as audio_file:
            ret_msg = await self.bot.send_audio(
                CHAT_ID,
                audio_file,
                duration=1,
                performer="eternnoir",
                title="pyTelegram",
                disable_notification=True,
            )
            assert ret_msg.content_type == "audio"
            assert ret_msg.audio.performer == "eternnoir"
            assert ret_msg.audio.title == "pyTelegram"

    @respect_rate_limit
    async def test_send_voice(self):
        with open(AUDIO_OGG, "rb") as audio_file:
            ret_msg = await self.bot.send_voice(CHAT_ID, audio_file)
            assert ret_msg.voice.mime_type == "audio/ogg"

    @respect_rate_limit
    async def test_send_voice_dis_noti(self):
        with open(AUDIO_OGG, "rb") as audio_file:
            ret_msg = await self.bot.send_voice(CHAT_ID, audio_file, disable_notification=True)
            assert ret_msg.voice.mime_type == "audio/ogg"

    @respect_rate_limit
    async def test_get_file(self):
        with open(AUDIO_OGG, "rb") as audio_file:
            ret_msg = await self.bot.send_voice(CHAT_ID, audio_file)
            file_id = ret_msg.voice.file_id
            file_info = await self.bot.get_file(file_id)
            assert file_info.file_id == file_id

    @respect_rate_limit
    async def test_get_file_dis_noti(self):
        with open(AUDIO_OGG, "rb") as audio_file:
            ret_msg = await self.bot.send_voice(CHAT_ID, audio_file, disable_notification=True)
            file_id = ret_msg.voice.file_id
            file_info = await self.bot.get_file(file_id)
            assert file_info.file_id == file_id
            assert file_info.file_size == AUDIO_OGG.stat().st_size

    @respect_rate_limit
    async def test_send_message(self):
        text = "CI Test Message"
        ret_msg = await self.bot.send_message(CHAT_ID, text)
        assert ret_msg.message_id
        assert ret_msg.text == text

    @respect_rate_limit
    async def test_send_dice(self):
        ret_msg = await self.bot.send_dice(CHAT_ID, emoji="🎯")
        assert ret_msg.message_id
        assert ret_msg.content_type == "dice"

    @respect_rate_limit
    async def test_send_message_dis_noti(self):
        text = "CI Test Message"
        ret_msg = await self.bot.send_message(CHAT_ID, text, disable_notification=True)
        assert ret_msg.message_id
        assert ret_msg.text == text

    @respect_rate_limit
    async def test_send_message_with_markup(self):
        text = "CI Test Message"
        markup = types.ReplyKeyboardMarkup()
        markup.add(types.KeyboardButton("1"))
        markup.add(types.KeyboardButton("2"))
        ret_msg = await self.bot.send_message(CHAT_ID, text, disable_notification=True, reply_markup=markup)
        assert ret_msg.message_id
        assert ret_msg.text == text
        # assert ret_msg.reply_markup == markup  # reply markup is not returned

    @respect_rate_limit
    async def test_send_message_with_markup_use_string(self):
        text = "CI Test Message"
        markup = types.ReplyKeyboardMarkup()
        markup.add("1")
        markup.add("2")
        markup.add("3")
        markup.add("4")
        ret_msg = await self.bot.send_message(CHAT_ID, text, disable_notification=True, reply_markup=markup)
        assert ret_msg.message_id
        assert ret_msg.text == text
        # assert ret_msg.reply_markup == markup  # reply markup is not returned

    @respect_rate_limit
    async def test_send_message_with_inlinemarkup(self):
        text = "CI Test Message"
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("Google", url="http://www.google.com/"))
        markup.add(types.InlineKeyboardButton("Yahoo", url="http://www.yahoo.com/"))
        ret_msg = await self.bot.send_message(CHAT_ID, text, disable_notification=True, reply_markup=markup)
        assert ret_msg.message_id
        assert ret_msg.text == text
        print(markup.to_dict())
        print(ret_msg.reply_markup.to_dict())
        assert ret_msg.reply_markup == markup

    @respect_rate_limit
    async def test_forward_message(self):
        text = "CI forward_message Test Message"
        msg = await self.bot.send_message(CHAT_ID, text)
        ret_msg = await self.bot.forward_message(CHAT_ID, CHAT_ID, msg.message_id)
        me_dict = (await self.bot.get_me()).to_dict()
        fwd_from_user_dict = ret_msg.forward_from.to_dict()
        for get_me_only_field in {"can_join_groups", "can_read_all_group_messages", "supports_inline_queries"}:
            me_dict.pop(get_me_only_field)
            fwd_from_user_dict.pop(get_me_only_field)
        assert fwd_from_user_dict == me_dict

    @respect_rate_limit
    async def test_copy_message(self):
        text = "CI copy_message Test Message"
        msg = await self.bot.send_message(CHAT_ID, text)
        ret_msg = await self.bot.copy_message(CHAT_ID, CHAT_ID, msg.message_id)
        assert ret_msg.message_id

    @respect_rate_limit
    async def test_forward_message_dis_noti(self):
        text = "CI forward_message Test Message"

        msg = await self.bot.send_message(CHAT_ID, text)
        ret_msg = await self.bot.forward_message(CHAT_ID, CHAT_ID, msg.message_id, disable_notification=True)
        assert ret_msg.forward_from

    @respect_rate_limit
    async def test_reply_to(self):
        text = "CI reply_to Test Message"

        msg = await self.bot.send_message(CHAT_ID, text)
        ret_msg = await self.bot.reply_to(msg, text + " REPLY")
        assert ret_msg.reply_to_message.message_id == msg.message_id

    @respect_rate_limit
    async def test_send_location(self):
        lat = 26.3875591
        lon = -161.2901042
        ret_msg = await self.bot.send_location(CHAT_ID, lat, lon)
        assert int(ret_msg.location.longitude) == int(lon)
        assert int(ret_msg.location.latitude) == int(lat)

    @respect_rate_limit
    async def test_send_location_dis_noti(self):
        lat = 26.3875591
        lon = -161.2901042
        ret_msg = await self.bot.send_location(CHAT_ID, lat, lon, disable_notification=True)
        assert int(ret_msg.location.longitude) == int(lon)
        assert int(ret_msg.location.latitude) == int(lat)

    @respect_rate_limit
    async def test_send_venue(self):
        lat = 26.3875591
        lon = -161.2901042
        ret_msg = await self.bot.send_venue(CHAT_ID, lat, lon, "Test Venue", "1123 Test Venue address")
        assert ret_msg.venue.title == "Test Venue"
        assert int(lat) == int(ret_msg.venue.location.latitude)

    @respect_rate_limit
    async def test_send_venue_dis_noti(self):
        lat = 26.3875591
        lon = -161.2901042
        ret_msg = await self.bot.send_venue(
            CHAT_ID,
            lat,
            lon,
            "Test Venue",
            "1123 Test Venue address",
            disable_notification=True,
        )
        assert ret_msg.venue.title == "Test Venue"

    @respect_rate_limit
    async def test_chat(self):
        me = await self.bot.get_me()
        msg = await self.bot.send_message(CHAT_ID, "Test")
        assert me.id == msg.from_user.id
        assert msg.chat.id == int(CHAT_ID)

    @respect_rate_limit
    async def test_edit_message_text(self):
        msg = await self.bot.send_message(CHAT_ID, "Test")
        new_msg = await self.bot.edit_message_text("Edit test", chat_id=CHAT_ID, message_id=msg.message_id)
        assert new_msg.text == "Edit test"

    @respect_rate_limit
    async def test_edit_message_caption(self):
        with open(IMAGE, "rb") as image_file:
            msg = await self.bot.send_document(CHAT_ID, image_file, caption="Test")
        new_msg = await self.bot.edit_message_caption(caption="Edit test", chat_id=CHAT_ID, message_id=msg.message_id)
        assert new_msg.caption == "Edit test"

    @respect_rate_limit
    async def test_edit_message_media(self):
        with open(IMAGE, "rb") as image_file_1, open(IMAGE_2, "rb") as image_file_2:
            msg_original = await self.bot.send_photo(CHAT_ID, image_file_1)
            msg_edited_1 = await self.bot.edit_message_media(
                chat_id=CHAT_ID,
                message_id=msg_original.message_id,
                media=types.InputMediaPhoto(image_file_2, caption="Test editMessageMedia uloading new"),
            )
            assert not isinstance(msg_edited_1, bool)
            assert msg_edited_1.caption == "Test editMessageMedia uloading new"

        with open(IMAGE, "rb") as image_file_1:
            msg_original = await self.bot.send_photo(CHAT_ID, image_file_1)
            msg_edited_2 = await self.bot.edit_message_media(
                chat_id=CHAT_ID,
                message_id=msg_original.message_id,
                media=types.InputMediaPhoto(msg_edited_1.photo[0].file_id, caption="Test editMessageMedia by file id"),
            )
            assert not isinstance(msg_edited_1, bool)
            assert msg_edited_2.caption == "Test editMessageMedia by file id"

    @respect_rate_limit
    async def test_get_chat(self):
        ch = await self.bot.get_chat(GROUP_ID)
        assert str(ch.id) == GROUP_ID

    @respect_rate_limit
    async def test_get_chat_administrators(self):
        cas = await self.bot.get_chat_administrators(GROUP_ID)
        assert len(cas) > 0

    @respect_rate_limit
    async def test_get_chat_members_count(self):
        cn = await self.bot.get_chat_member_count(GROUP_ID)
        assert cn > 1

    @respect_rate_limit
    async def test_export_chat_invite_link(self):
        il = await self.bot.export_chat_invite_link(GROUP_ID)
        assert isinstance(il, str)

    @respect_rate_limit
    async def test_create_revoke_detailed_chat_invite_link(self):
        cil = await self.bot.create_chat_invite_link(
            GROUP_ID, expire_date=datetime.now() + timedelta(minutes=1), member_limit=5
        )
        assert isinstance(cil.invite_link, str)
        assert cil.creator.id == (await self.bot.get_me()).id
        assert isinstance(cil.expire_date, (float, int))
        assert cil.member_limit == 5
        assert not cil.is_revoked
        rcil = await self.bot.revoke_chat_invite_link(GROUP_ID, cil.invite_link)
        assert rcil.is_revoked

    @respect_rate_limit
    async def test_edit_markup(self):
        text = "CI Test Message"
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("Google", url="http://www.google.com/"))
        markup.add(types.InlineKeyboardButton("Yahoo", url="http://www.yahoo.com/"))
        ret_msg = await self.bot.send_message(CHAT_ID, text, disable_notification=True, reply_markup=markup)
        assert ret_msg.reply_markup == markup

        markup.add(types.InlineKeyboardButton("DuckDuckGo", url="https://duckduckgo.com//"))
        new_msg = await self.bot.edit_message_reply_markup(
            chat_id=CHAT_ID, message_id=ret_msg.message_id, reply_markup=markup
        )
        assert new_msg.message_id
        assert new_msg.reply_markup == markup

    @respect_rate_limit
    async def test_send_video_note(self):
        with open(VIDEO, "rb") as video_file:
            ret_msg = await self.bot.send_video_note(CHAT_ID, video_file)
            assert ret_msg.message_id

    @respect_rate_limit
    async def test_send_media_group(self):
        img1 = "https://i.imgur.com/CjXjcnU.png"
        img2 = "https://i.imgur.com/CjXjcnU.png"
        medias = [
            types.InputMediaPhoto(img1, "View"),
            types.InputMediaPhoto(img2, "Dog"),
        ]
        result = await self.bot.send_media_group(CHAT_ID, medias)
        assert len(result) == 2
        assert result[0].media_group_id is not None
        assert result[0].media_group_id == result[1].media_group_id

    @respect_rate_limit
    async def test_send_media_group_local_files(self):
        with open(IMAGE, "rb") as image_file, open(VIDEO, "rb") as video_file:
            medias = [types.InputMediaPhoto(image_file, "View"), types.InputMediaVideo(video_file)]
            result = await self.bot.send_media_group(CHAT_ID, medias)
            assert len(result) == 2
            assert result[0].media_group_id is not None
            assert result[1].media_group_id is not None

    @respect_rate_limit
    async def test_send_photo_formating_caption(self):
        with open(IMAGE, "rb") as image_file:
            ret_msg = await self.bot.send_photo(CHAT_ID, image_file, caption="_italic_", parse_mode="Markdown")
            assert ret_msg.caption_entities[0].type == "italic"

    @respect_rate_limit
    async def test_send_video_formatting_caption(self):
        with open(VIDEO, "rb") as video_file:
            ret_msg = await self.bot.send_video(CHAT_ID, video_file, caption="_italic_", parse_mode="Markdown")
            assert ret_msg.caption_entities[0].type == "italic"

    @respect_rate_limit
    async def test_send_audio_formatting_caption(self):
        with open(AUDIO_MP3, "rb") as audio_file:
            ret_msg = await self.bot.send_audio(CHAT_ID, audio_file, caption="<b>bold</b>", parse_mode="HTML")
            assert ret_msg.caption_entities[0].type == "bold"

    @respect_rate_limit
    async def test_send_voice_formatting_caprion(self):
        with open(AUDIO_OGG, "rb") as audio_file:
            ret_msg = await self.bot.send_voice(CHAT_ID, audio_file, caption="<b>bold</b>", parse_mode="HTML")
            assert ret_msg.caption_entities[0].type == "bold"
            assert ret_msg.voice.mime_type == "audio/ogg"

    @respect_rate_limit
    async def test_send_media_group_formatting_caption(self):
        img1 = "https://i.imgur.com/CjXjcnU.png"
        img2 = "https://i.imgur.com/CjXjcnU.png"
        medias = [
            types.InputMediaPhoto(img1, "*View*", parse_mode="Markdown"),
            types.InputMediaPhoto(img2, "_Dog_", parse_mode="Markdown"),
        ]
        result = await self.bot.send_media_group(CHAT_ID, medias)
        assert len(result) == 2
        assert result[0].media_group_id is not None
        assert result[0].caption_entities[0].type == "bold"
        assert result[1].caption_entities[0].type == "italic"

    @respect_rate_limit
    async def test_send_document_formating_caption(self):
        with open(IMAGE, "rb") as image_file:
            ret_msg = await self.bot.send_document(CHAT_ID, image_file, caption="_italic_", parse_mode="Markdown")
            assert ret_msg.caption_entities[0].type == "italic"

    @respect_rate_limit
    async def test_chat_commands(self):
        command, description, lang = "command_1", "description of command 1", "en"
        scope = types.BotCommandScopeChat(CHAT_ID)
        ret_msg = await self.bot.set_my_commands([types.BotCommand(command, description)], scope, lang)
        assert ret_msg is True

        ret_msg = await self.bot.get_my_commands(scope=scope, language_code=lang)
        assert ret_msg[0].command == command
        assert ret_msg[0].description == description

        ret_msg = await self.bot.delete_my_commands(scope=scope, language_code=lang)
        assert ret_msg is True

        ret_msg = await self.bot.get_my_commands(scope=scope, language_code=lang)
        assert ret_msg == []
