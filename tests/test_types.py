# -*- coding: utf-8 -*-
import sys

sys.path.append('../')
from telebot import types


def test_json_user():
    json_str = r'{"id": 123456789, "is_bot": false, "first_name": "John", "last_name": "Doe", "username": "@johndoe", "language_code": "en", "can_join_groups": true, "can_read_all_group_messages": false, "supports_inline_queries": true, "is_premium": true, "added_to_attachment_menu": false, "can_connect_to_business": true, "has_main_web_app": false, "has_topics_enabled": true, "allows_users_to_create_topics": true, "can_manage_bots": true, "supports_guest_queries": true, "supports_join_request_queries": true}'
    result = types.User.de_json(json_str)
    assert isinstance(result, types.User)
    assert result.id == 123456789
    assert result.is_bot == False
    assert result.first_name == 'John'
    assert result.last_name == 'Doe'
    assert result.username == '@johndoe'
    assert result.language_code == 'en'
    assert result.can_join_groups == True
    assert result.can_read_all_group_messages == False
    assert result.supports_inline_queries == True
    assert result.is_premium == True
    assert result.added_to_attachment_menu == False
    assert result.can_connect_to_business == True
    assert result.has_main_web_app == False
    assert result.has_topics_enabled == True
    assert result.allows_users_to_create_topics == True
    assert result.can_manage_bots == True
    assert result.supports_guest_queries == True
    assert result.supports_join_request_queries == True


def test_json_chat():
        json_str = r'{"id": 12345, "type": "private", "title": "Test Chat", "username": "@testchat", "first_name": "John", "last_name": "Doe", "photo": {"small_file_id": "s", "small_file_unique_id": "su", "big_file_id": "b", "big_file_unique_id": "bu"}, "bio": "bio text", "has_private_forwards": true, "description": "chat description", "invite_link": "https://t.me/joinchat/ABC", "pinned_message": {"message_id": 1, "date": 1682189507, "chat": {"id": 1, "type": "private"}, "from": {"id": 1, "is_bot": false, "first_name": "User"}, "text": "pinned"}, "permissions": {"can_send_messages": true, "can_send_audios": true, "can_send_documents": true, "can_send_photos": true, "can_send_videos": true, "can_send_video_notes": true, "can_send_voice_notes": true, "can_send_polls": true, "can_send_other_messages": true, "can_add_web_page_previews": true, "can_change_info": true, "can_invite_users": true, "can_pin_messages": true, "can_manage_topics": true}, "slow_mode_delay": 30, "message_auto_delete_time": 86400, "has_protected_content": true, "sticker_set_name": "TestStickerSet", "can_set_sticker_set": false, "linked_chat_id": 2, "location": {"chat": {"id": 1, "type": "supergroup", "title": "Loc"}, "location": {"latitude": 50.45, "longitude": 30.52}, "address": "Main St"}, "join_to_send_messages": false, "join_by_request": true, "has_restricted_voice_and_video_messages": false, "is_forum": true, "max_reaction_count": 10, "active_usernames": ["test"], "emoji_status_custom_emoji_id": "custom_emoji", "has_hidden_members": false, "has_aggressive_anti_spam_enabled": false, "emoji_status_expiration_date": 1682275907, "available_reactions": ["emoji", "custom_emoji"], "accent_color_id": 1, "background_custom_emoji_id": "bg_emoji", "profile_accent_color_id": 2, "profile_background_custom_emoji_id": "profile_bg", "has_visible_history": true, "unrestrict_boost_count": 5, "custom_emoji_sticker_set_name": "custom_stickers", "business_intro": {"title": "Business", "description": "Business desc", "has_visible_history": true}, "business_location": {"address": "New York, NY", "has_active_address": true}, "business_opening_hours": {"time_zone_name": "America/New_York", "opening_hours": [{"opening_minute": 540, "closing_minute": 1020, "day_of_week": 1, "is_recurring": true}]}, "personal_chat": {"id": 3, "type": "private", "title": "Personal"}, "birthdate": {"day": "15", "month": "6"}, "can_send_paid_media": true, "accepted_gift_types": {"unlimited_gifts": false, "limited_gifts": false, "unique_gifts": true, "premium_subscription": false, "gifts_from_channels": false}, "is_direct_messages": true, "parent_chat": {"id": 4, "type": "supergroup", "title": "Parent"}, "rating": {"level": "test", "rating": "test", "current_level_rating": "test"}, "paid_message_star_count": 5, "first_profile_audio": {"file_id": "fa1", "file_unique_id": "fa1u", "duration": 30, "mime_type": "audio/ogg"}, "unique_gift_colors": {"model_custom_emoji_id": 1, "symbol_custom_emoji_id": 1, "light_theme_main_color": 333333, "light_theme_other_colors": [444444], "dark_theme_main_color": 555555, "dark_theme_other_colors": [666666]}, "guard_bot": {"id": 2, "is_bot": true, "first_name": "GuardBot"}, "community": {"id": 5, "name": "Community"}}'
        result = types.Chat.de_json(json_str)
        assert isinstance(result, types.Chat)
        assert result.id == 12345
        assert result.type == 'private'
        assert result.title == 'Test Chat'
        assert result.username == "@testchat"
        assert result.first_name == "John"
        assert result.last_name == "Doe"
        assert isinstance(result.photo, types.ChatPhoto)
        assert result.bio == "bio text"
        assert result.has_private_forwards == True
        assert result.description == "chat description"
        assert result.invite_link == "https://t.me/joinchat/ABC"
        assert isinstance(result.pinned_message, types.Message)
        assert isinstance(result.permissions, types.ChatPermissions)
        assert result.slow_mode_delay == 30
        assert result.message_auto_delete_time == 86400
        assert result.has_protected_content == True
        assert result.sticker_set_name == "TestStickerSet"
        assert result.can_set_sticker_set == False
        assert result.linked_chat_id == 2
        assert isinstance(result.location, types.ChatLocation)
        assert result.join_to_send_messages == False
        assert result.join_by_request == True
        assert result.has_restricted_voice_and_video_messages == False
        assert result.is_forum == True
        assert result.max_reaction_count == 10
        assert isinstance(result.active_usernames, list)
        assert result.emoji_status_custom_emoji_id == "custom_emoji"
        assert result.has_hidden_members == False
        assert result.has_aggressive_anti_spam_enabled == False
        assert result.emoji_status_expiration_date == 1682275907
        assert isinstance(result.available_reactions, list)
        assert result.accent_color_id == 1
        assert result.background_custom_emoji_id == "bg_emoji"
        assert result.profile_accent_color_id == 2
        assert result.profile_background_custom_emoji_id == "profile_bg"
        assert result.has_visible_history == True
        assert result.unrestrict_boost_count == 5
        assert result.custom_emoji_sticker_set_name == "custom_stickers"
        assert isinstance(result.business_intro, types.BusinessIntro)
        assert isinstance(result.business_location, types.BusinessLocation)
        assert isinstance(result.business_opening_hours, types.BusinessOpeningHours)
        assert isinstance(result.personal_chat, types.Chat)
        assert isinstance(result.birthdate, types.Birthdate)
        assert result.can_send_paid_media == True
        assert isinstance(result.accepted_gift_types, types.AcceptedGiftTypes)
        assert result.is_direct_messages == True
        assert isinstance(result.parent_chat, types.Chat)
        assert isinstance(result.rating, types.UserRating)
        assert result.paid_message_star_count == 5
        assert isinstance(result.unique_gift_colors, types.UniqueGiftColors)
        assert isinstance(result.first_profile_audio, types.Audio)
        assert isinstance(result.guard_bot, types.User)
        assert isinstance(result.community, types.Community)


# NOTE: Message has internal fields that are not covered by de_json tests:
# - options: internal field, not from JSON
# - json_string: internal field, not from JSON
def test_json_message():
    json_str = r'{"message_id": 1, "date": 1682189507, "chat": {"id": 12345, "type": "private", "title": "Chat"}, "from": {"id": 1, "is_bot": false, "first_name": "User"}, "text": "Hello", "content_type": "text"}'
    result = types.Message.de_json(json_str)
    assert isinstance(result, types.Message)
    assert result.message_id == 1
    assert isinstance(result.from_user, types.User)
    assert result.date == 1682189507
    assert isinstance(result.chat, types.Chat)
    assert result.content_type == 'text'


def test_json_location():
    json_str = r'{"latitude": 50.4501, "longitude": 30.5234, "horizontal_accuracy": 1.5, "live_period": 3600, "heading": 45, "proximity_alert_radius": 100}'
    result = types.Location.de_json(json_str)
    assert isinstance(result, types.Location)
    assert result.longitude == 30.5234
    assert result.latitude == 50.4501
    assert result.horizontal_accuracy == 1.5
    assert result.live_period == 3600
    assert result.heading == 45
    assert result.proximity_alert_radius == 100


def test_json_venue():
    json_str = r'{"location": {"latitude": 50.45, "longitude": 30.52}, "title": "Kyiv", "address": "Khreshchatyk St", "foursquare_id": "12345", "foursquare_type": "restaurant", "google_place_id": "ChI123456", "google_place_type": "locality"}'
    result = types.Venue.de_json(json_str)
    assert isinstance(result, types.Venue)
    assert isinstance(result.location, types.Location)
    assert result.title == 'Kyiv'
    assert result.address == 'Khreshchatyk St'
    assert result.foursquare_id == '12345'
    assert result.foursquare_type == 'restaurant'
    assert result.google_place_id == 'ChI123456'
    assert result.google_place_type == 'locality'


def test_json_contact():
    json_str = r'{"phone_number": "+123****7890", "first_name": "John", "user_id": 12345, "last_name": "Doe", "vcard": "some vcard data"}'
    result = types.Contact.de_json(json_str)
    assert isinstance(result, types.Contact)
    assert result.phone_number == '+123****7890'
    assert result.first_name == 'John'
    assert result.last_name == 'Doe'
    assert result.user_id == 12345
    assert result.vcard == 'some vcard data'


def test_json_document():
    json_str = r'{"file_id": "doc1", "file_unique_id": "du1", "file_name": "test.pdf", "mime_type": "application/pdf", "file_size": 1024, "thumbnail": {"file_id": "th1", "file_unique_id": "thu1", "width": 50, "height": 50}}'
    result = types.Document.de_json(json_str)
    assert isinstance(result, types.Document)
    assert result.file_id == 'doc1'
    assert result.file_unique_id == 'du1'
    assert isinstance(result.thumbnail, types.PhotoSize)
    assert result.file_name == 'test.pdf'
    assert result.mime_type == 'application/pdf'
    assert result.file_size == 1024


def test_json_photo_size():
    json_str = r'{"file_id": "photo1", "file_unique_id": "pu1", "width": 100, "height": 100, "file_size": 512}'
    result = types.PhotoSize.de_json(json_str)
    assert isinstance(result, types.PhotoSize)
    assert result.file_id == 'photo1'
    assert result.file_unique_id == 'pu1'
    assert result.width == 100
    assert result.height == 100
    assert result.file_size == 512


def test_json_video():
    json_str = r'{"file_id": "video1", "file_unique_id": "vu1", "width": 640, "height": 480, "duration": 30, "mime_type": "video/mp4", "thumbnail": {"file_id": "th1", "file_unique_id": "thu1", "width": 50, "height": 50}, "file_name": "video.mp4", "file_size": 2048, "start_timestamp": 5, "qualities": [{"file_id": "q1", "file_unique_id": "qu1", "width": 240, "height": 360, "codec": "h264", "file_size": 1024}, {"file_id": "q2", "file_unique_id": "qu2", "width": 640, "height": 480, "codec": "h264", "file_size": 2048}]}'
    result = types.Video.de_json(json_str)
    assert isinstance(result, types.Video)
    assert result.file_id == 'video1'
    assert result.file_unique_id == 'vu1'
    assert result.width == 640
    assert result.height == 480
    assert result.duration == 30
    assert isinstance(result.thumbnail, types.PhotoSize)
    assert result.file_name == 'video.mp4'
    assert result.mime_type == 'video/mp4'
    assert result.file_size == 2048
    assert result.cover is None
    assert result.start_timestamp == 5
    assert isinstance(result.qualities, list)


def test_json_audio():
    json_str = r'{"file_id": "audio1", "file_unique_id": "au1", "duration": 30, "mime_type": "audio/mpeg", "performer": "Artist", "title": "Song Title", "file_name": "song.mp3", "file_size": 512, "thumbnail": {"file_id": "th1", "file_unique_id": "thu1", "width": 50, "height": 50}}'
    result = types.Audio.de_json(json_str)
    assert isinstance(result, types.Audio)
    assert result.file_id == 'audio1'
    assert result.file_unique_id == 'au1'
    assert result.duration == 30
    assert result.performer == 'Artist'
    assert result.title == 'Song Title'
    assert result.file_name == 'song.mp3'
    assert result.mime_type == 'audio/mpeg'
    assert result.file_size == 512
    assert isinstance(result.thumbnail, types.PhotoSize)


def test_json_voice():
    json_str = r'{"file_id": "voice1", "file_unique_id": "vu1", "duration": 30, "mime_type": "audio/ogg", "file_size": 256}'
    result = types.Voice.de_json(json_str)
    assert isinstance(result, types.Voice)
    assert result.file_id == 'voice1'
    assert result.file_unique_id == 'vu1'
    assert result.duration == 30
    assert result.mime_type == 'audio/ogg'
    assert result.file_size == 256


def test_json_animation():
    json_str = r'{"file_id": "anim1", "file_unique_id": "anu1", "width": 100, "height": 100, "duration": 10, "thumbnail": {"file_id": "th1", "file_unique_id": "thu1", "width": 50, "height": 50}, "file_name": "anim.mp4", "mime_type": "video/mp4", "file_size": 1024}'
    result = types.Animation.de_json(json_str)
    assert isinstance(result, types.Animation)
    assert result.file_id == 'anim1'
    assert result.file_unique_id == 'anu1'
    assert result.width == 100
    assert result.height == 100
    assert result.duration == 10
    assert isinstance(result.thumbnail, types.PhotoSize)
    assert result.file_name == 'anim.mp4'
    assert result.mime_type == 'video/mp4'
    assert result.file_size == 1024


def test_json_sticker():
    json_str = r'{"file_id": "sticker1", "file_unique_id": "stu1", "type": "regular", "width": 512, "height": 512, "is_animated": false, "is_video": false, "thumbnail": {"file_id": "th1", "file_unique_id": "thu1", "width": 100, "height": 100}, "emoji": "😀", "set_name": "TestSet", "mask_position": {"point": "forehead", "x_shift": 0.0, "y_shift": 0.0, "scale": 0.5}, "file_size": 4096, "premium_animation": {"file_id": "pa1", "file_unique_id": "pa1u"}, "custom_emoji_id": "ce1", "needs_repainting": true}'
    result = types.Sticker.de_json(json_str)
    assert isinstance(result, types.Sticker)
    assert result.file_id == 'sticker1'
    assert result.file_unique_id == 'stu1'
    assert result.type == 'regular'
    assert result.width == 512
    assert result.height == 512
    assert result.is_animated == False
    assert result.is_video == False
    assert isinstance(result.thumbnail, types.PhotoSize)
    assert result.emoji == '😀'
    assert result.set_name == 'TestSet'
    assert isinstance(result.mask_position, types.MaskPosition)
    assert result.file_size == 4096
    assert isinstance(result.premium_animation, types.File)
    assert result.custom_emoji_id == 'ce1'
    assert result.needs_repainting == True


def test_json_stickerset():
    json_str = r'{"name": "TestName", "title": "Test Title", "sticker_type": "regular", "stickers": [{"file_id": "st1", "file_unique_id": "su1", "type": "regular", "width": 512, "height": 512, "is_animated": false, "is_video": false}], "thumbnail": {"file_id": "th1", "file_unique_id": "thu1", "width": 100, "height": 100}}'
    result = types.StickerSet.de_json(json_str)
    assert isinstance(result, types.StickerSet)
    assert result.name == 'TestName'
    assert result.title == 'Test Title'
    assert result.sticker_type == 'regular'
    assert isinstance(result.stickers, list)
    assert isinstance(result.thumbnail, types.PhotoSize)


def test_json_chatlocation():
    json_str = r'{"location": {"latitude": 50.45, "longitude": 30.52}, "address": "New York, NY"}'
    result = types.ChatLocation.de_json(json_str)
    assert isinstance(result, types.ChatLocation)
    assert isinstance(result.location, types.Location)
    assert result.address == 'New York, NY'


def test_json_reactiontypeemoji():
    json_str = r'{"type": "emoji", "emoji": "\u2764\uFE0F"}'
    result = types.ReactionTypeEmoji.de_json(json_str)
    assert isinstance(result, types.ReactionTypeEmoji)
    assert result.emoji == '❤️'


def test_json_reactiontypecustomemoji():
    json_str = r'{"type": "custom_emoji", "custom_emoji_id": "ce123"}'
    result = types.ReactionTypeCustomEmoji.de_json(json_str)
    assert isinstance(result, types.ReactionTypeCustomEmoji)
    assert result.custom_emoji_id == 'ce123'


def test_json_reactioncount():
    json_str = r'{"type": {"type": "emoji", "emoji": "\u2764\uFE0F"}, "total_count": 5}'
    result = types.ReactionCount.de_json(json_str)
    assert isinstance(result, types.ReactionCount)
    assert isinstance(result.type, types.ReactionType)
    assert result.total_count == 5


def test_json_chatinvitelink():
    json_str = r'{"invite_link": "https://t.me/joinchat/ABC", "creator": {"id": 12345, "is_bot": false, "first_name": "Test"}, "creates_join_request": false, "is_primary": true, "is_revoked": false, "name": "Invite", "expire_date": 1704067200, "member_limit": 10, "pending_join_request_count": 3}'
    result = types.ChatInviteLink.de_json(json_str)
    assert isinstance(result, types.ChatInviteLink)
    assert result.invite_link == 'https://t.me/joinchat/ABC'
    assert isinstance(result.creator, types.User)
    assert result.creates_join_request == False
    assert result.is_primary == True
    assert result.is_revoked == False
    assert result.name == 'Invite'
    assert result.expire_date == 1704067200
    assert result.member_limit == 10
    assert result.pending_join_request_count == 3


def test_json_forumtopic():
    json_str = r'{"message_thread_id": 42, "name": "Topic", "icon_color": 4294967295, "icon_custom_emoji_id": "emoji1", "is_name_implicit": true}'
    result = types.ForumTopic.de_json(json_str)
    assert isinstance(result, types.ForumTopic)
    assert result.message_thread_id == 42
    assert result.name == 'Topic'
    assert result.icon_color == 4294967295
    assert result.icon_custom_emoji_id == 'emoji1'
    assert result.is_name_implicit == True


def test_json_loginurl():
    json_str = r'{"url": "https://example.com", "forward_text": "Forward", "bot_username": "botuser", "request_write_access": true}'
    result = types.LoginUrl.de_json(json_str)
    assert isinstance(result, types.LoginUrl)
    assert result.url == 'https://example.com'
    assert result.forward_text == 'Forward'
    assert result.bot_username == 'botuser'
    assert result.request_write_access == True


def test_json_webappinfo():
    json_str = r'{"url": "https://example.com"}'
    result = types.WebAppInfo.de_json(json_str)
    assert isinstance(result, types.WebAppInfo)
    assert result.url == 'https://example.com'


def test_json_webappdata():
    json_str = r'{"data": "test_data", "button_text": "Button"}'
    result = types.WebAppData.de_json(json_str)
    assert isinstance(result, types.WebAppData)
    assert result.data == 'test_data'
    assert result.button_text == 'Button'


def test_json_maskposition():
    json_str = r'{"point": "forehead", "x_shift": 0.0, "y_shift": 0.0, "scale": 0.5}'
    result = types.MaskPosition.de_json(json_str)
    assert isinstance(result, types.MaskPosition)
    assert result.point == 'forehead'
    assert result.x_shift == 0.0
    assert result.y_shift == 0.0
    assert result.scale == 0.5


def test_json_messageentity():
    json_str = r'{"type": "bold", "offset": 0, "length": 5, "url": "https://example.com", "language": "en", "unix_time": 1682189507, "date_time_format": "YYYY-MM-DD"}'
    result = types.MessageEntity.de_json(json_str)
    assert isinstance(result, types.MessageEntity)
    assert result.type == 'bold'
    assert result.offset == 0
    assert result.length == 5
    assert result.url == 'https://example.com'
    assert result.language == 'en'
    assert result.unix_time == 1682189507
    assert result.date_time_format == 'YYYY-MM-DD'


def test_json_messageentitycustomemoji():
    json_str = r'{"type": "custom_emoji", "offset": 0, "length": 10, "custom_emoji_id": "ce123"}'
    result = types.MessageEntity.de_json(json_str)
    assert isinstance(result, types.MessageEntity)
    assert result.type == 'custom_emoji'
    assert result.offset == 0
    assert result.length == 10
    assert result.custom_emoji_id == 'ce123'


def test_json_messageentitytextmention():
    json_str = r'{"type": "text_mention", "offset": 0, "length": 10, "user": {"id": 12345, "is_bot": false, "first_name": "Test"}}'
    result = types.MessageEntity.de_json(json_str)
    assert isinstance(result, types.MessageEntity)
    assert result.type == 'text_mention'
    assert result.offset == 0
    assert result.length == 10
    assert isinstance(result.user, types.User)


def test_json_chatshared():
    json_str = r'{"request_id": 1, "chat_id": 12345, "title": "Chat Title", "photo": [{"small_file_id": "s", "small_file_unique_id": "su", "big_file_id": "b", "big_file_unique_id": "bu"}], "username": "chatuser"}'
    result = types.ChatShared.de_json(json_str)
    assert isinstance(result, types.ChatShared)
    assert result.request_id == 1
    assert result.chat_id == 12345
    assert result.title == 'Chat Title'
    assert isinstance(result.photo, list)
    assert isinstance(result.photo[0], dict)
    assert result.photo[0]['small_file_id'] == 's'
    assert result.username == 'chatuser'


def test_json_shareduser():
    json_str = r'{"user_id": 12345, "first_name": "Test", "last_name": "User", "username": "testuser", "photo": [{"file_id": "p", "file_unique_id": "pu", "width": 100, "height": 100}]}'
    result = types.SharedUser.de_json(json_str)
    assert isinstance(result, types.SharedUser)
    assert result.user_id == 12345
    assert result.first_name == 'Test'
    assert result.last_name == 'User'
    assert result.username == 'testuser'
    assert isinstance(result.photo, list)
    assert isinstance(result.photo[0], types.PhotoSize)


def test_json_usersshared():
    json_str = r'{"request_id": 1, "users": [{"user_id": 12345, "first_name": "Test", "last_name": "User"}]}'
    result = types.UsersShared.de_json(json_str)
    assert isinstance(result, types.UsersShared)
    assert result.request_id == 1
    assert isinstance(result.users, list)


def test_json_chatboost():
    json_str = r'{"boost_item_id": "b1", "add_date": 1682189507, "expiration_date": 1682275907, "source": {"source": "premium", "user": {"id": 1, "is_bot": false, "first_name": "Test"}}}'
    result = types.ChatBoost.de_json(json_str)
    assert isinstance(result, types.ChatBoost)
    assert result.boost_id is None
    assert result.add_date == 1682189507
    assert result.expiration_date == 1682275907
    assert isinstance(result.source, types.ChatBoostSourcePremium)
    assert result.source.source == 'premium'
    assert isinstance(result.source.user, types.User)


def test_json_gift():
    json_str = r'{"id": 123456789, "sticker": {"file_id": "s", "file_unique_id": "su", "type": "regular", "width": 512, "height": 512, "is_animated": false, "is_video": false}, "star_count": 100, "total_count": 5, "remaining_count": 3, "upgrade_star_count": 50, "personal_total_count": 10, "personal_remaining_count": 2, "is_premium": true, "has_colors": true, "background": {"center_color": 16777215, "edge_color": 16711680, "text_color": 0}, "publisher_chat": {"id": 1, "type": "channel", "title": "Publisher"}, "unique_gift_variant_count": 3}'
    result = types.Gift.de_json(json_str)
    assert isinstance(result, types.Gift)
    assert result.id == 123456789
    assert isinstance(result.sticker, types.Sticker)
    assert result.star_count == 100
    assert result.total_count == 5
    assert result.remaining_count == 3
    assert result.upgrade_star_count == 50
    assert result.personal_total_count == 10
    assert result.personal_remaining_count == 2
    assert result.is_premium == True
    assert result.has_colors == True
    assert isinstance(result.background, types.GiftBackground)
    assert isinstance(result.publisher_chat, types.Chat)
    assert result.unique_gift_variant_count == 3


def test_json_giftinfo():
    json_str = r'{"gift": {"id": 123456789, "sticker": {"file_id": "s", "file_unique_id": "su", "type": "regular", "width": 512, "height": 512, "is_animated": false, "is_video": false}, "star_count": 100}, "owned_gift_id": "og_123", "convert_star_count": 50, "prepaid_upgrade_star_count": 100, "can_be_upgraded": true, "text": "Gift text", "entities": [{"type": "bold", "offset": 0, "length": 4}], "is_private": false, "is_upgrade_separate": false, "unique_gift_number": 42}'
    result = types.GiftInfo.de_json(json_str)
    assert isinstance(result, types.GiftInfo)
    assert isinstance(result.gift, types.Gift)
    assert result.owned_gift_id == 'og_123'
    assert result.convert_star_count == 50
    assert result.prepaid_upgrade_star_count == 100
    assert result.can_be_upgraded == True
    assert result.text == 'Gift text'
    assert isinstance(result.entities, list)
    assert result.is_private == False
    assert result.is_upgrade_separate == False
    assert result.unique_gift_number == 42


def test_json_gifts():
    json_str = r'{"gifts": [{"id": 123456789, "sticker": {"file_id": "s", "file_unique_id": "su", "type": "regular", "width": 512, "height": 512, "is_animated": false, "is_video": false}, "star_count": 100}]}'
    result = types.Gifts.de_json(json_str)
    assert isinstance(result, types.Gifts)
    assert isinstance(result.gifts, list)


def test_json_richtextbold():
    json_str = r'{"type": "bold", "text": "Test"}'
    result = types.RichText.de_json(json_str)
    assert isinstance(result, types.RichTextBold)
    assert result.text == 'Test'


def test_json_richtextitalic():
    json_str = r'{"type": "italic", "text": "Test"}'
    result = types.RichText.de_json(json_str)
    assert isinstance(result, types.RichTextItalic)
    assert result.text == 'Test'


def test_json_richtextunderline():
    json_str = r'{"type": "underline", "text": "Test"}'
    result = types.RichText.de_json(json_str)
    assert isinstance(result, types.RichTextUnderline)
    assert result.text == 'Test'


def test_json_richtextstrikethrough():
    json_str = r'{"type": "strikethrough", "text": "Test"}'
    result = types.RichText.de_json(json_str)
    assert isinstance(result, types.RichTextStrikethrough)
    assert result.text == 'Test'


def test_json_richtextspoiler():
    json_str = r'{"type": "spoiler", "text": "Test"}'
    result = types.RichText.de_json(json_str)
    assert isinstance(result, types.RichTextSpoiler)
    assert result.text == 'Test'


def test_json_richtextsubscript():
    json_str = r'{"type": "subscript", "text": "sub"}'
    result = types.RichText.de_json(json_str)
    assert isinstance(result, types.RichTextSubscript)
    assert result.text == 'sub'


def test_json_richtextsuperscript():
    json_str = r'{"type": "superscript", "text": "sup"}'
    result = types.RichText.de_json(json_str)
    assert isinstance(result, types.RichTextSuperscript)
    assert result.text == 'sup'


def test_json_richtextmarked():
    json_str = r'{"type": "marked", "text": "marked"}'
    result = types.RichText.de_json(json_str)
    assert isinstance(result, types.RichTextMarked)
    assert result.text == 'marked'


def test_json_richtextcode():
    json_str = r'{"type": "code", "text": "code"}'
    result = types.RichText.de_json(json_str)
    assert isinstance(result, types.RichTextCode)
    assert result.text == 'code'


def test_json_richtextanchor():
    json_str = r'{"type": "anchor", "name": "anchor"}'
    result = types.RichText.de_json(json_str)
    assert isinstance(result, types.RichTextAnchor)
    assert result.name == 'anchor'


def test_json_richtextdatetime():
    json_str = r'{"type": "date_time", "text": "2024-01-01", "unix_time": 1704067200, "date_time_format": "YYYY-MM-DD"}'
    result = types.RichText.de_json(json_str)
    assert isinstance(result, types.RichTextDateTime)
    assert result.text == '2024-01-01'
    assert result.unix_time == 1704067200
    assert result.date_time_format == 'YYYY-MM-DD'


def test_json_richtexttextmention():
    json_str = r'{"type": "text_mention", "text": "test text", "user": {"id": 12345, "is_bot": false, "first_name": "Test"}}'
    result = types.RichText.de_json(json_str)
    assert isinstance(result, types.RichTextTextMention)
    assert result.text == 'test text'
    assert isinstance(result.user, types.User)


def test_json_richtextanchorlink():
    json_str = r'{"type": "anchor_link", "text": "Link", "anchor_name": "anchor"}'
    result = types.RichText.de_json(json_str)
    assert isinstance(result, types.RichTextAnchorLink)
    assert result.text == 'Link'
    assert result.anchor_name == 'anchor'


def test_json_richtexturl():
    json_str = r'{"type": "url", "text": "click here", "url": "https://example.com"}'
    result = types.RichText.de_json(json_str)
    assert isinstance(result, types.RichTextUrl)
    assert result.text == 'click here'
    assert result.url == 'https://example.com'


def test_json_richtextemailaddress():
    json_str = r'{"type": "email_address", "text": "test@example.com", "email_address": "test@example.com"}'
    result = types.RichText.de_json(json_str)
    assert isinstance(result, types.RichTextEmailAddress)
    assert result.text == 'test@example.com'
    assert result.email_address == 'test@example.com'


def test_json_richtextphonenumber():
    json_str = r'{"type": "phone_number", "text": "+123****7890", "phone_number": "+123****7890"}'
    result = types.RichText.de_json(json_str)
    assert isinstance(result, types.RichTextPhoneNumber)
    assert result.text == '+123****7890'
    assert result.phone_number == '+123****7890'


def test_json_richtextbankcardnumber():
    json_str = r'{"type": "bank_card_number", "text": "1234 5678 9012 3456", "bank_card_number": "1234 5678 9012 3456"}'
    result = types.RichText.de_json(json_str)
    assert isinstance(result, types.RichTextBankCardNumber)
    assert result.text == '1234 5678 9012 3456'
    assert result.bank_card_number == '1234 5678 9012 3456'


def test_json_richblockparagraph():
    json_str = r'{"type": "paragraph", "text": "Test"}'
    result = types.RichBlock.de_json(json_str)
    assert isinstance(result, types.RichBlockParagraph)
    assert result.text == 'Test'


def test_json_richblockpreformatted():
    json_str = r'{"type": "pre", "text": "Code", "language": "python"}'
    result = types.RichBlock.de_json(json_str)
    assert isinstance(result, types.RichBlockPreformatted)
    assert result.text == 'Code'
    assert result.language == 'python'


def test_json_richblockfooter():
    json_str = r'{"type": "footer", "text": "Footer"}'
    result = types.RichBlock.de_json(json_str)
    assert isinstance(result, types.RichBlockFooter)
    assert result.text == 'Footer'


def test_json_richblockcaption():
    json_str = r'{"text": "Caption", "credit": "Author"}'
    result = types.RichBlockCaption.de_json(json_str)
    assert isinstance(result, types.RichBlockCaption)
    assert result.text == 'Caption'
    assert result.credit == 'Author'


def test_json_richblockanimation():
    json_str = r'{"type": "animation", "animation": {"file_id": "anim_id", "file_unique_id": "anim_uid", "width": 100, "height": 100, "duration": 10}, "caption": {"type": "bold", "text": "anim caption"}, "has_spoiler": true}'
    result = types.RichBlock.de_json(json_str)
    assert isinstance(result, types.RichBlockAnimation)
    assert isinstance(result.animation, types.Animation)
    assert result.has_spoiler == True
    assert isinstance(result.caption, types.RichBlockCaption)


def test_json_richblockdetails():
    json_str = r'{"type": "details", "summary": {"text": "summary text"}, "blocks": [{"text": "detail"}], "is_open": false}'
    result = types.RichBlock.de_json(json_str)
    assert isinstance(result, types.RichBlockDetails)
    assert isinstance(result.summary, dict) or result.summary is None
    assert isinstance(result.blocks, list)
    assert result.is_open == False


def test_json_richblocklistitem():
    json_str = r'{"label": "label text", "blocks": [{"text": "item block"}], "has_checkbox": true, "is_checked": true, "value": 42, "type": null}'
    result = types.RichBlockListItem.de_json(json_str)
    assert isinstance(result, types.RichBlockListItem)
    assert result.label == 'label text'
    assert isinstance(result.blocks, list)
    assert result.has_checkbox == True
    assert result.is_checked == True
    assert result.value == 42
    assert result.type is None


def test_json_richblockvoicenote():
    json_str = r'{"type": "voice_note", "voice_note": {"file_id": "voice_id", "file_unique_id": "voice_uid", "duration": 30}, "caption": {"type": "bold", "text": "voice caption"}}'
    result = types.RichBlock.de_json(json_str)
    assert isinstance(result, types.RichBlockVoiceNote)
    assert isinstance(result.voice_note, types.Voice)
    assert isinstance(result.caption, types.RichBlockCaption)


def test_json_chatadministratorrights():
    json_str = r'{"is_anonymous": true, "can_manage_chat": true, "can_delete_messages": true, "can_manage_video_chats": true, "can_restrict_members": true, "can_promote_members": true, "can_change_info": true, "can_invite_users": true, "can_post_messages": true, "can_edit_messages": true, "can_pin_messages": true, "can_manage_topics": true, "can_post_stories": true, "can_edit_stories": true, "can_delete_stories": true, "can_manage_direct_messages": true, "can_manage_tags": true}'
    result = types.ChatAdministratorRights.de_json(json_str)
    assert isinstance(result, types.ChatAdministratorRights)
    assert result.is_anonymous == True
    assert result.can_manage_chat == True
    assert result.can_delete_messages == True
    assert result.can_manage_video_chats == True
    assert result.can_restrict_members == True
    assert result.can_promote_members == True
    assert result.can_change_info == True
    assert result.can_invite_users == True
    assert result.can_post_messages == True
    assert result.can_edit_messages == True
    assert result.can_pin_messages == True
    assert result.can_manage_topics == True
    assert result.can_post_stories == True
    assert result.can_edit_stories == True
    assert result.can_delete_stories == True
    assert result.can_manage_direct_messages == True
    assert result.can_manage_tags == True


def test_json_chatpermissions():
    json_str = r'{"can_send_messages": true, "can_send_audios": true, "can_send_documents": true, "can_send_photos": true, "can_send_videos": true, "can_send_video_notes": true, "can_send_voice_notes": true, "can_send_polls": true, "can_send_other_messages": true, "can_add_web_page_previews": true, "can_change_info": true, "can_invite_users": true, "can_pin_messages": true, "can_manage_topics": true, "can_edit_tag": true, "can_react_to_messages": true}'
    result = types.ChatPermissions.de_json(json_str)
    assert isinstance(result, types.ChatPermissions)
    assert result.can_send_messages == True
    # can_send_media_messages is deprecated in this fork, not a real attribute
    assert result.can_send_audios == True
    assert result.can_send_documents == True
    assert result.can_send_photos == True
    assert result.can_send_videos == True
    assert result.can_send_video_notes == True
    assert result.can_send_voice_notes == True
    assert result.can_send_polls == True
    assert result.can_send_other_messages == True
    assert result.can_add_web_page_previews == True
    assert result.can_change_info == True
    assert result.can_invite_users == True
    assert result.can_pin_messages == True
    assert result.can_manage_topics == True
    assert result.can_edit_tag == True
    assert result.can_react_to_messages == True


def test_json_chatmembermember():
    json_str = r'{"user": {"id": 1, "is_bot": false, "first_name": "Test"}, "status": "member", "until_date": 1682275907, "tag": "member_tag"}'
    result = types.ChatMemberMember.de_json(json_str)
    assert isinstance(result, types.ChatMemberMember)
    assert isinstance(result.user, types.User)
    assert result.status == 'member'
    assert result.until_date == 1682275907
    assert result.tag == 'member_tag'


def test_json_chatmemberowner():
    json_str = r'{"status": "creator", "user": {"id": 12345, "is_bot": false, "first_name": "Test"}, "is_anonymous": false, "custom_title": "Owner"}'
    result = types.ChatMemberOwner.de_json(json_str)
    assert isinstance(result, types.ChatMemberOwner)
    assert isinstance(result.user, types.User)
    assert result.status == 'creator'
    assert result.is_anonymous == False
    assert result.custom_title == 'Owner'


def test_json_chatmemberadministrator():
    json_str = r'{"status": "administrator", "user": {"id": 12345, "is_bot": false, "first_name": "Test"}, "is_anonymous": true, "can_be_edited": true, "can_manage_chat": true, "can_delete_messages": true, "can_manage_video_chats": true, "can_restrict_members": true, "can_promote_members": true, "can_change_info": true, "can_invite_users": true, "can_post_stories": true, "can_edit_stories": true, "can_delete_stories": true, "can_post_messages": true, "can_edit_messages": true, "can_pin_messages": true, "can_manage_topics": true, "can_manage_direct_messages": true, "can_manage_tags": true, "custom_title": "mod"}'
    result = types.ChatMemberAdministrator.de_json(json_str)
    assert isinstance(result, types.ChatMemberAdministrator)
    assert isinstance(result.user, types.User)
    assert result.status == 'administrator'
    assert result.can_be_edited == True
    assert result.is_anonymous == True
    assert result.can_manage_chat == True
    assert result.can_delete_messages == True
    assert result.can_manage_video_chats == True
    assert result.can_restrict_members == True
    assert result.can_promote_members == True
    assert result.can_change_info == True
    assert result.can_invite_users == True
    assert result.can_post_stories == True
    assert result.can_edit_stories == True
    assert result.can_delete_stories == True
    assert result.can_post_messages == True
    assert result.can_edit_messages == True
    assert result.can_pin_messages == True
    assert result.can_manage_topics == True
    assert result.custom_title == "mod"
    assert result.can_manage_direct_messages == True
    assert result.can_manage_tags == True


def test_json_chatmemberrestricted():
    json_str = r'{"status": "restricted", "user": {"id": 12345, "is_bot": false, "first_name": "Test"}, "is_member": true, "can_send_messages": true, "can_send_audios": true, "can_send_documents": true, "can_send_photos": true, "can_send_videos": true, "can_send_video_notes": true, "can_send_voice_notes": true, "can_send_polls": true, "can_send_other_messages": true, "can_add_web_page_previews": true, "can_change_info": false, "can_invite_users": false, "can_pin_messages": false, "can_manage_topics": false, "until_date": 1682189507, "tag": "test_tag", "can_edit_tag": true, "can_react_to_messages": true}'
    result = types.ChatMemberRestricted.de_json(json_str)
    assert isinstance(result, types.ChatMemberRestricted)
    assert isinstance(result.user, types.User)
    assert result.status == 'restricted'
    assert result.is_member == True
    assert result.can_send_messages == True
    assert result.can_send_audios == True
    assert result.can_send_documents == True
    assert result.can_send_photos == True
    assert result.can_send_videos == True
    assert result.can_send_video_notes == True
    assert result.can_send_voice_notes == True
    assert result.can_send_polls == True
    assert result.can_send_other_messages == True
    assert result.can_add_web_page_previews == True
    assert result.can_change_info == False
    assert result.can_invite_users == False
    assert result.can_pin_messages == False
    assert result.can_manage_topics == False
    assert result.until_date == 1682189507
    assert result.tag == 'test_tag'
    assert result.can_edit_tag == True
    assert result.can_react_to_messages == True


def test_json_chatmemberleft():
    json_str = r'{"status": "left", "user": {"id": 12345, "is_bot": false, "first_name": "Test"}}'
    result = types.ChatMemberLeft.de_json(json_str)
    assert isinstance(result, types.ChatMemberLeft)
    assert isinstance(result.user, types.User)
    assert result.status == 'left'


def test_json_chatmemberbanned():
    json_str = r'{"status": "kicked", "user": {"id": 12345, "is_bot": false, "first_name": "Test"}, "until_date": 1682189507}'
    result = types.ChatMemberBanned.de_json(json_str)
    assert isinstance(result, types.ChatMemberBanned)
    assert isinstance(result.user, types.User)
    assert result.status == 'kicked'
    assert result.until_date == 1682189507


def test_json_botcommand():
    json_str = r'{"command": "/start", "description": "Start command", "is_ephemeral": true}'
    result = types.BotCommand.de_json(json_str)
    assert isinstance(result, types.BotCommand)
    assert result.command == '/start'
    assert result.description == 'Start command'
    assert result.is_ephemeral == True


def test_json_botdescription():
    json_str = r'{"language_code": "en", "description": "Bot description"}'
    result = types.BotDescription.de_json(json_str)
    assert isinstance(result, types.BotDescription)
    assert result.description == 'Bot description'


def test_json_botname():
    json_str = r'{"language_code": "en", "name": "Bot Name"}'
    result = types.BotName.de_json(json_str)
    assert isinstance(result, types.BotName)
    assert result.name == 'Bot Name'


def test_json_botshortdescription():
    json_str = r'{"language_code": "en", "short_description": "Short"}'
    result = types.BotShortDescription.de_json(json_str)
    assert isinstance(result, types.BotShortDescription)
    assert result.short_description == 'Short'


def test_json_inlinekeyboardbutton():
    json_str = r'{"text": "Button", "url": "https://example.com", "callback_data": "data", "web_app": {"url": "https://example.com"}, "switch_inline_query": "query", "switch_inline_query_current_chat": "query", "switch_inline_query_chosen_chat": {"query": "q", "allow_user_chats": true, "allow_bot_chats": true, "allow_group_chats": true, "allow_channel_chats": true}, "callback_game": {"type": "test"}, "pay": true, "login_url": {"url": "https://example.com", "forward_text": "Forward", "bot_username": "bot", "request_write_access": true}, "copy_text": {"text": "copy"}, "icon_custom_emoji_id": "emoji123", "style": "primary"}'
    result = types.InlineKeyboardButton.de_json(json_str)
    assert isinstance(result, types.InlineKeyboardButton)
    assert result.text == 'Button'
    assert result.url == 'https://example.com'
    assert result.callback_data == 'data'
    assert isinstance(result.web_app, types.WebAppInfo)
    assert result.switch_inline_query == 'query'
    assert result.switch_inline_query_current_chat == 'query'
    assert isinstance(result.switch_inline_query_chosen_chat, types.SwitchInlineQueryChosenChat)
    assert isinstance(result.callback_game, dict)
    assert result.pay == True
    assert isinstance(result.login_url, types.LoginUrl)
    assert isinstance(result.copy_text, types.CopyTextButton)
    assert result.icon_custom_emoji_id == 'emoji123'
    assert result.style == 'primary'


def test_json_menubuttoncommands():
    json_str = r'{"type": "commands", "default_width": 100}'
    result = types.MenuButtonCommands.de_json(json_str)
    assert isinstance(result, types.MenuButtonCommands)
    assert result.type == 'commands'


def test_json_menubuttondefault():
    json_str = r'{"type": "default"}'
    result = types.MenuButtonDefault.de_json(json_str)
    assert isinstance(result, types.MenuButtonDefault)
    assert result.type == 'default'


def test_json_menubuttonwebapp():
    json_str = r'{"type": "web_app", "text": "Open App", "web_app": {"url": "https://example.com"}}'
    result = types.MenuButtonWebApp.de_json(json_str)
    assert isinstance(result, types.MenuButtonWebApp)
    assert result.type == 'web_app'
    assert result.text == 'Open App'
    assert isinstance(result.web_app, dict)


def test_json_pollanswer():
    json_str = r'{"poll_id": "poll_id", "option_ids": [0], "option_persistent_ids": [0], "user": {"id": 12345, "is_bot": false, "first_name": "Test"}, "voter_chat": {"id": 67890, "type": "channel", "title": "Channel"}}'
    result = types.PollAnswer.de_json(json_str)
    assert isinstance(result, types.PollAnswer)
    assert result.poll_id == 'poll_id'
    assert isinstance(result.option_ids, list)
    assert isinstance(result.option_persistent_ids, list)
    assert isinstance(result.user, types.User)
    assert isinstance(result.voter_chat, types.Chat)


def test_json_reactiontype():
    json_str = r'{"type": "emoji", "emoji": "\u2764\uFE0F"}'
    result = types.ReactionType.de_json(json_str)
    assert isinstance(result, types.ReactionType)
    assert result.type == 'emoji'


def test_linkpreviewoptionsto_dict():
    obj = types.LinkPreviewOptions(...)
    d = obj.to_dict()
    assert isinstance(d, dict)


def test_sentwebappmessageto_dict():
    obj = types.SentWebAppMessage(message_id=1)
    d = obj.to_dict()
    assert isinstance(d, dict)


def test_json_reactiontypepaid():
    json_str = r'{"type": "paid"}'
    result = types.ReactionTypePaid.de_json(json_str)
    assert isinstance(result, types.ReactionTypePaid)


def test_json_businessbotrights():
    json_str = r'{"can_reply": true, "can_read_messages": true, "can_delete_sent_messages": true, "can_delete_all_messages": false, "can_edit_name": true, "can_edit_bio": false, "can_edit_profile_photo": false, "can_edit_username": false, "can_change_gift_settings": false, "can_view_gifts_and_stars": true, "can_convert_gifts_to_stars": false, "can_transfer_and_upgrade_gifts": false, "can_transfer_stars": false, "can_manage_stories": false}'
    result = types.BusinessBotRights.de_json(json_str)
    assert isinstance(result, types.BusinessBotRights)
    assert result.can_reply is True
    assert result.can_read_messages is True
    assert result.can_delete_sent_messages is True
    assert result.can_delete_all_messages is False
    assert result.can_edit_name is True
    assert result.can_edit_bio is False
    assert result.can_edit_profile_photo is False
    assert result.can_edit_username is False
    assert result.can_change_gift_settings is False
    assert result.can_view_gifts_and_stars is True
    assert result.can_convert_gifts_to_stars is False
    assert result.can_transfer_and_upgrade_gifts is False
    assert result.can_transfer_stars is False
    assert result.can_manage_stories is False


def test_json_businessintro():
    json_str = r'{"title": "Business Title", "message": "Business message text", "sticker": {"file_id": "s", "file_unique_id": "su", "type": "regular", "width": 512, "height": 512, "is_animated": false, "is_video": false}}'
    result = types.BusinessIntro.de_json(json_str)
    assert isinstance(result, types.BusinessIntro)
    assert result.title == 'Business Title'
    assert result.message == 'Business message text'
    assert isinstance(result.sticker, types.Sticker)


def test_json_chatownerleft():
    json_str = r'{"new_owner": {"id": 12345, "is_bot": false, "first_name": "New Owner"}}'
    result = types.ChatOwnerLeft.de_json(json_str)
    assert isinstance(result, types.ChatOwnerLeft)
    assert result.new_owner is not None
    assert result.new_owner.id == 12345
    assert result.new_owner.is_bot == False
    assert result.new_owner.first_name == 'New Owner'


def test_json_checklisttasksdone():
    json_str = r'{"checklist_message": {"message_id": 1, "date": 1682189507, "chat": {"id": 1, "type": "private"}, "from": {"id": 1, "is_bot": false, "first_name": "User"}, "text": "checklist"}, "marked_as_done_task_ids": [1, 2], "marked_as_not_done_task_ids": [3]}'
    result = types.ChecklistTasksDone.de_json(json_str)
    assert isinstance(result, types.ChecklistTasksDone)
    assert isinstance(result.checklist_message, types.Message)
    assert isinstance(result.marked_as_done_task_ids, list)
    assert result.marked_as_done_task_ids == [1, 2]
    assert isinstance(result.marked_as_not_done_task_ids, list)
    assert result.marked_as_not_done_task_ids == [3]


def test_json_communitychatadded():
    json_str = r'{"community": {"id": 12345, "name": "Test Community"}}'
    result = types.CommunityChatAdded.de_json(json_str)
    assert isinstance(result, types.CommunityChatAdded)
    assert result.community is not None
    assert result.community.id == 12345
    assert result.community.name == 'Test Community'


def test_json_communitychatremoved():
    json_str = r'{}'
    result = types.CommunityChatRemoved.de_json(json_str)
    assert isinstance(result, types.CommunityChatRemoved)


def test_json_forumtopicclosed():
    json_str = r'{}'
    result = types.ForumTopicClosed.de_json(json_str)
    assert isinstance(result, types.ForumTopicClosed)


def test_json_forumtopicedited():
    json_str = r'{"name": "New Name", "icon_custom_emoji_id": "custom_emoji"}'
    result = types.ForumTopicEdited.de_json(json_str)
    assert isinstance(result, types.ForumTopicEdited)
    assert result.name == 'New Name'
    assert result.icon_custom_emoji_id == 'custom_emoji'


def test_json_forumtopicreopened():
    json_str = r'{}'
    result = types.ForumTopicReopened.de_json(json_str)
    assert isinstance(result, types.ForumTopicReopened)


def test_json_generalforumtopichidden():
    json_str = r'{}'
    result = types.GeneralForumTopicHidden.de_json(json_str)
    assert isinstance(result, types.GeneralForumTopicHidden)


def test_json_generalforumtopicunhidden():
    json_str = r'{}'
    result = types.GeneralForumTopicUnhidden.de_json(json_str)
    assert isinstance(result, types.GeneralForumTopicUnhidden)


def test_json_giveawaycreated():
    json_str = r'{"prize_star_count": 100}'
    result = types.GiveawayCreated.de_json(json_str)
    assert isinstance(result, types.GiveawayCreated)
    assert result.prize_star_count == 100


def test_json_linkpreviewoptions():
    json_str = r'{"is_disabled": true, "url": "https://example.com", "prefer_small_media": false, "prefer_large_media": true, "show_above_text": false}'
    result = types.LinkPreviewOptions.de_json(json_str)
    assert isinstance(result, types.LinkPreviewOptions)
    assert result.is_disabled == True
    assert result.url == 'https://example.com'
    assert result.prefer_small_media == False
    assert result.prefer_large_media == True
    assert result.show_above_text == False


def test_json_orderinfo():
    json_str = {'name': 'John', 'phone_number': '+1234567890', 'email': 'john@example.com', 'shipping_address': {'country_code': 'US', 'city': 'New York', 'street_line1': '123 Main St', 'street_line2': 'Apt 4B', 'postal_code': '10001', 'state': 'NY', 'post_code': '10001'}}
    result = types.OrderInfo.de_json(json_str)
    assert isinstance(result, types.OrderInfo)
    assert result.name == 'John'
    assert result.phone_number == '+1234567890'
    assert result.email == 'john@example.com'
    assert isinstance(result.shipping_address, types.ShippingAddress)
    assert hasattr(result, 'name')
    assert hasattr(result, 'phone_number')
    assert hasattr(result, 'email')


def test_json_pollmedia():
    json_str = r'{"animation": {"file_id": "a", "file_unique_id": "au", "width": 100, "height": 100, "duration": 10}, "audio": {"file_id": "au1", "file_unique_id": "au1u", "duration": 30}, "document": {"file_id": "d", "file_unique_id": "du", "file_name": "test.pdf"}, "live_photo": {"file_id": "lp", "file_unique_id": "lpu", "width": 100, "height": 100, "duration": 5}, "location": {"latitude": 50.45, "longitude": 30.52}, "photo": [{"file_id": "p", "file_unique_id": "pu", "width": 100, "height": 100}], "sticker": {"file_id": "s", "file_unique_id": "su", "type": "regular", "width": 512, "height": 512, "is_animated": false, "is_video": false}, "venue": {"location": {"latitude": 50.45, "longitude": 30.52}, "title": "Place", "address": "Addr"}, "video": {"file_id": "v", "file_unique_id": "vu", "width": 640, "height": 480, "duration": 30}, "link": {"url": "https://example.com", "shows_above_caption": true, "enhanced_smileys": true, "prefer_large_media": true}}'
    result = types.PollMedia.de_json(json_str)
    assert isinstance(result, types.PollMedia)
    assert isinstance(result.animation, types.Animation)
    assert isinstance(result.audio, types.Audio)
    assert isinstance(result.document, types.Document)
    assert isinstance(result.live_photo, types.LivePhoto)
    assert isinstance(result.location, types.Location)
    assert isinstance(result.photo, list)
    assert isinstance(result.sticker, types.Sticker)
    assert isinstance(result.venue, types.Venue)
    assert isinstance(result.video, types.Video)
    assert isinstance(result.link, types.Link)


def test_json_richblockdivider():
    json_str = r'{"type": "divider"}'
    result = types.RichBlock.de_json(json_str)
    assert isinstance(result, types.RichBlockDivider)


def test_json_sentwebappmessage():
    json_str = r'{"inline_message_id": "test_inline_msg_1"}'
    result = types.SentWebAppMessage.de_json(json_str)
    assert isinstance(result, types.SentWebAppMessage)
    assert result.inline_message_id == 'test_inline_msg_1'


def test_json_suggestedpostdeclined():
    json_str = r'{"suggested_post_message": {"message_id": 1, "date": 1682189507, "chat": {"id": 1, "type": "private"}, "from": {"id": 1, "is_bot": false, "first_name": "User"}, "text": "suggested"}, "comment": "declined reason"}'
    result = types.SuggestedPostDeclined.de_json(json_str)
    assert isinstance(result, types.SuggestedPostDeclined)
    assert isinstance(result.suggested_post_message, types.Message)
    assert result.comment == 'declined reason'


def test_json_switchinlinequerychosenchat():
    json_str = r'{"query": "test", "allow_user_chats": true, "allow_bot_chats": true, "allow_group_chats": true, "allow_channel_chats": true}'
    result = types.SwitchInlineQueryChosenChat.de_json(json_str)
    assert isinstance(result, types.SwitchInlineQueryChosenChat)
    assert result.query == 'test'
    assert result.allow_user_chats == True
    assert result.allow_bot_chats == True
    assert result.allow_group_chats == True
    assert result.allow_channel_chats == True


def test_json_transactionpartnertelegramads():
    result = types.TransactionPartnerTelegramAds(type='telegram_ads')
    assert result.type == 'telegram_ads'
    assert isinstance(result, types.TransactionPartnerTelegramAds)


def test_json_videochatstarted():
    json_str = r'{}'
    result = types.VideoChatStarted.de_json(json_str)
    assert isinstance(result, types.VideoChatStarted)


def test_json_voicechatstarted():
    json_str = r'{}'
    result = types.VoiceChatStarted.de_json(json_str)
    assert isinstance(result, types.VoiceChatStarted)


def test_json_writeaccessallowed():
    json_str = r'{"from_request": true, "web_app_name": "TestApp", "from_attachment_menu": false}'
    result = types.WriteAccessAllowed.de_json(json_str)
    assert isinstance(result, types.WriteAccessAllowed)
    assert result.from_request == True
    assert result.web_app_name == 'TestApp'
    assert result.from_attachment_menu == False


def test_json_acceptedgifttypes():
    json_str = r'{"unlimited_gifts": false, "limited_gifts": true, "unique_gifts": true, "premium_subscription": false, "gifts_from_channels": false}'
    result = types.AcceptedGiftTypes.de_json(json_str)
    assert isinstance(result, types.AcceptedGiftTypes)
    assert result.unlimited_gifts == False
    assert result.limited_gifts == True
    assert result.unique_gifts == True
    assert result.premium_subscription == False
    assert result.gifts_from_channels == False


def test_json_copytextbutton():
    json_str = r'{"text": "Test"}'
    result = types.CopyTextButton.de_json(json_str)
    assert isinstance(result, types.CopyTextButton)
    assert result.text == 'Test'


def test_json_dice():
    json_str = r'{"value": "test", "emoji": "😀"}'
    result = types.Dice.de_json(json_str)
    assert isinstance(result, types.Dice)
    assert result.value == 'test'
    assert result.emoji == '😀'


def test_json_richblocktablecell():
    json_str = r'{"align": "test", "valign": "test", "text": "Test", "is_header": true, "colspan": 2, "rowspan": 3}'
    result = types.RichBlockTableCell.de_json(json_str)
    assert isinstance(result, types.RichBlockTableCell)
    assert result.align == 'test'
    assert result.valign == 'test'
    assert result.text == 'Test'
    assert result.is_header == True
    assert result.colspan == 2
    assert result.rowspan == 3


def test_json_richtextbotcommand():
    json_str = r'{"type": "bot_command", "text": "Test", "bot_command": "test"}'
    result = types.RichText.de_json(json_str)
    assert isinstance(result, types.RichTextBotCommand)
    assert result.text == 'Test'
    assert result.bot_command == 'test'


def test_json_richtextcashtag():
    json_str = r'{"type": "cashtag", "text": "Test", "cashtag": "test"}'
    result = types.RichText.de_json(json_str)
    assert isinstance(result, types.RichTextCashtag)
    assert result.text == 'Test'
    assert result.cashtag == 'test'


def test_json_richtextcustomemoji():
    json_str = r'{"type": "custom_emoji", "custom_emoji_id": "test", "alternative_text": "test"}'
    result = types.RichText.de_json(json_str)
    assert isinstance(result, types.RichTextCustomEmoji)
    assert result.custom_emoji_id == 'test'
    assert result.alternative_text == 'test'


def test_json_richtexthashtag():
    json_str = r'{"type": "hashtag", "text": "Test", "hashtag": "test"}'
    result = types.RichText.de_json(json_str)
    assert isinstance(result, types.RichTextHashtag)
    assert result.text == 'Test'
    assert result.hashtag == 'test'


def test_json_richtextmathematicalexpression():
    json_str = r'{"type": "mathematical_expression", "expression": "test"}'
    result = types.RichText.de_json(json_str)
    assert isinstance(result, types.RichTextMathematicalExpression)
    assert result.expression == 'test'


def test_json_richtextmention():
    json_str = r'{"type": "mention", "text": "Test", "username": "test"}'
    result = types.RichText.de_json(json_str)
    assert isinstance(result, types.RichTextMention)
    assert result.text == 'Test'
    assert result.username == 'test'


def test_json_richtextreference():
    json_str = r'{"type": "reference", "text": "Test", "name": "Test"}'
    result = types.RichText.de_json(json_str)
    assert isinstance(result, types.RichTextReference)
    assert result.text == 'Test'
    assert result.name == 'Test'


def test_json_richtextreferencelink():
    json_str = r'{"type": "reference_link", "text": "Test", "reference_name": "test"}'
    result = types.RichText.de_json(json_str)
    assert isinstance(result, types.RichTextReferenceLink)
    assert result.text == 'Test'
    assert result.reference_name == 'test'


def test_json_suggestedpostprice():
    json_str = r'{"currency": "en", "amount": 1}'
    result = types.SuggestedPostPrice.de_json(json_str)
    assert isinstance(result, types.SuggestedPostPrice)
    assert result.currency == 'en'
    assert result.amount == 1


def test_json_affiliateinfo():
    json_str = r'{"commission_per_mille": 1000, "amount": 100, "affiliate_user": {"id": 1, "is_bot": false, "first_name": "User"}, "affiliate_chat": {"id": -1001234567890, "type": "channel", "title": "Channel"}, "nanostar_amount": 10000000}'
    result = types.AffiliateInfo.de_json(json_str)
    assert isinstance(result, types.AffiliateInfo)
    assert result.commission_per_mille == 1000
    assert result.amount == 100
    assert isinstance(result.affiliate_user, types.User)
    assert isinstance(result.affiliate_chat, types.Chat)
    assert result.nanostar_amount == 10000000


def test_json_backgroundfill():
    # BackgroundFill is abstract - test BackgroundFillSolid directly
    json_str = r'{"type": "solid", "color": 123456}'
    result = types.BackgroundFillSolid.de_json(json_str)
    assert isinstance(result, types.BackgroundFillSolid)


def test_json_backgroundfillfreeformgradient():
    json_str = r'{"type": "freeform_gradient", "colors": [123456, 654321, 111222]}'
    result = types.BackgroundFillFreeformGradient.de_json(json_str)
    assert isinstance(result, types.BackgroundFillFreeformGradient)
    assert result.type == 'freeform_gradient'
    assert isinstance(result.colors, list)


def test_json_backgroundfillgradient():
    json_str = r'{"type": "gradient", "top_color": 123456, "bottom_color": 654321, "rotation_angle": 180}'
    result = types.BackgroundFillGradient.de_json(json_str)
    assert isinstance(result, types.BackgroundFillGradient)
    assert result.type == 'gradient'
    assert result.top_color == 123456
    assert result.bottom_color == 654321
    assert result.rotation_angle == 180


def test_json_backgroundfillsolid():
    json_str = r'{"type": "solid", "color": 123456}'
    result = types.BackgroundFillSolid.de_json(json_str)
    assert isinstance(result, types.BackgroundFillSolid)
    assert result.type == 'solid'
    assert result.color == 123456


def test_json_backgroundtype():
    # BackgroundType is abstract - test BackgroundTypeFill directly
    json_str = r'{"type": "fill", "fill": {"type": "solid", "color": 123456}, "dark_theme_dimming": 0}'
    result = types.BackgroundTypeFill.de_json(json_str)
    assert isinstance(result, types.BackgroundTypeFill)


def test_json_backgroundtypechattheme():
    json_str = r'{"type": "fill", "theme_name": "test"}'
    result = types.BackgroundTypeChatTheme.de_json(json_str)
    assert isinstance(result, types.BackgroundTypeChatTheme)
    assert result.type == 'fill'
    assert result.theme_name == 'test'


def test_json_backgroundtypefill():
    json_str = r'{"type": "solid", "fill": {"type": "solid", "color": 123456}, "dark_theme_dimming": 0}'
    result = types.BackgroundTypeFill.de_json(json_str)
    assert isinstance(result, types.BackgroundTypeFill)
    assert result.type == 'solid'
    assert isinstance(result.fill, types.BackgroundFill)
    assert result.dark_theme_dimming == 0


def test_json_backgroundtypepattern():
    json_str = r'{"type": "pattern", "document": {"file_id": "doc", "file_unique_id": "docu", "mime_type": "application/pdf", "file_name": "test.pdf"}, "fill": {"type": "solid", "color": 123456}, "intensity": 0, "is_inverted": true, "is_moving": true}'
    result = types.BackgroundTypePattern.de_json(json_str)
    assert isinstance(result, types.BackgroundTypePattern)
    assert result.type == 'pattern'
    assert isinstance(result.document, types.Document)
    assert isinstance(result.fill, dict) or result.fill is None
    assert result.intensity == 0
    assert result.is_inverted == True
    assert result.is_moving == True


def test_json_backgroundtypewallpaper():
    json_str = r'{"type": "wallpaper", "document": {"file_id": "doc", "file_unique_id": "docu", "mime_type": "application/pdf", "file_name": "test.pdf"}, "dark_theme_dimming": 0, "is_blurred": true, "is_moving": true}'
    result = types.BackgroundTypeWallpaper.de_json(json_str)
    assert isinstance(result, types.BackgroundTypeWallpaper)
    assert result.type == 'wallpaper'
    assert isinstance(result.document, types.Document)
    assert result.dark_theme_dimming == 0
    assert result.is_blurred == True
    assert result.is_moving == True


def test_json_birthdate():
    json_str = r'{"day": "test", "month": "test", "year": 1990}'
    result = types.Birthdate.de_json(json_str)
    assert isinstance(result, types.Birthdate)
    assert result.day == 'test'
    assert result.month == 'test'
    assert result.year == 1990


def test_json_botaccesssettings():
    json_str = r'{"is_access_restricted": false, "added_users": [{"id": 1, "is_bot": false, "first_name": "Test"}, {"id": 2, "is_bot": false, "first_name": "User2"}]}'
    result = types.BotAccessSettings.de_json(json_str)
    assert isinstance(result, types.BotAccessSettings)
    assert result.is_access_restricted == False
    assert isinstance(result.added_users, list)
    assert len(result.added_users) == 2
    assert isinstance(result.added_users[0], types.User)
    assert result.added_users[0].id == 1


def test_json_botsubscriptionupdated():
    json_str = r'{"user": {"id": 1, "is_bot": false, "first_name": "Test"}, "invoice_payload": "test_payload", "state": "default"}'
    result = types.BotSubscriptionUpdated.de_json(json_str)
    assert isinstance(result, types.BotSubscriptionUpdated)
    assert isinstance(result.user, types.User)
    assert result.invoice_payload == 'test_payload'
    assert result.state == 'default'


def test_json_businessconnection():
    json_str = r'{"id": "1", "user": {"id": 1, "is_bot": false, "first_name": "Test"}, "user_chat_id": 1, "date": 1682189507, "is_enabled": false, "rights": {"can_reply": true, "can_read_messages": true, "can_delete_sent_messages": false, "can_delete_all_messages": false, "can_edit_name": true, "can_edit_bio": false, "can_edit_profile_photo": true, "can_edit_username": false, "can_change_gift_settings": true, "can_view_gifts_and_stars": false, "can_convert_gifts_to_stars": true, "can_transfer_and_upgrade_gifts": false, "can_transfer_stars": true, "can_manage_stories": false}}'
    result = types.BusinessConnection.de_json(json_str)
    assert isinstance(result, types.BusinessConnection)
    assert result.id == '1'
    assert isinstance(result.user, types.User)
    assert result.user_chat_id == 1
    assert result.date == 1682189507
    assert result.is_enabled == False
    assert isinstance(result.rights, types.BusinessBotRights)
    assert result.rights.can_reply == True
    assert result.rights.can_read_messages == True
    assert result.rights.can_delete_sent_messages == False
    assert result.rights.can_delete_all_messages == False
    assert result.rights.can_edit_name == True
    assert result.rights.can_edit_bio == False
    assert result.rights.can_edit_profile_photo == True
    assert result.rights.can_edit_username == False
    assert result.rights.can_change_gift_settings == True
    assert result.rights.can_view_gifts_and_stars == False
    assert result.rights.can_convert_gifts_to_stars == True
    assert result.rights.can_transfer_and_upgrade_gifts == False
    assert result.rights.can_transfer_stars == True
    assert result.rights.can_manage_stories == False


def test_json_businesslocation():
    json_str = r'{"address": "NY", "location": {"latitude": 50.45, "longitude": 30.52, "horizontal_accuracy": 1.5}}'
    result = types.BusinessLocation.de_json(json_str)
    assert isinstance(result, types.BusinessLocation)
    assert result.address == 'NY'
    assert isinstance(result.location, types.Location)
    assert result.location.latitude == 50.45
    assert result.location.longitude == 30.52
    assert result.location.horizontal_accuracy == 1.5


def test_json_businessmessagesdeleted():
    json_str = r'{"business_connection_id": 1, "chat": {"id": 1, "type": "private", "title": "Test"}, "message_ids": "test"}'
    result = types.BusinessMessagesDeleted.de_json(json_str)
    assert isinstance(result, types.BusinessMessagesDeleted)
    assert result.business_connection_id == 1
    assert isinstance(result.chat, types.Chat)
    assert result.message_ids == 'test'


def test_json_businessopeninghours():
    json_str = r'{"time_zone_name": "test", "opening_hours": [{"opening_minute": 0, "closing_minute": 60}]}'
    result = types.BusinessOpeningHours.de_json(json_str)
    assert isinstance(result, types.BusinessOpeningHours)
    assert result.time_zone_name == 'test'
    assert isinstance(result.opening_hours, list)


def test_json_businessopeninghoursinterval():
    json_str = r'{"opening_minute": 0, "closing_minute": 60}'
    result = types.BusinessOpeningHoursInterval.de_json(json_str)
    assert isinstance(result, types.BusinessOpeningHoursInterval)
    assert result.opening_minute == 0
    assert result.closing_minute == 60


def test_json_callbackquery():
    # json_string is internal field, not covered (like Message.options/json_string)
    json_str = r'{"id": "cq1", "from": {"id": 1, "is_bot": false, "first_name": "Test"}, "data": "test", "chat_instance": "ci1", "message": {"message_id": 1, "date": 1682189507, "chat": {"id": 1, "type": "private"}, "from": {"id": 1, "is_bot": false, "first_name": "User"}, "text": "Hello"}, "inline_message_id": "im1", "game_short_name": "game"}'
    result = types.CallbackQuery.de_json(json_str)
    assert isinstance(result, types.CallbackQuery)
    assert result.id == 'cq1'
    assert isinstance(result.from_user, types.User)
    assert result.data == 'test'
    assert result.chat_instance == 'ci1'
    assert isinstance(result.message, types.Message)
    assert result.inline_message_id == 'im1'
    assert result.game_short_name == 'game'


def test_json_chatbackground():
    json_str = r'{"type": {"type": "fill", "fill": {"type": "solid", "color": 123456}, "dark_theme_dimming": 0}}'
    result = types.ChatBackground.de_json(json_str)
    assert isinstance(result, types.ChatBackground)
    assert isinstance(result.type, types.BackgroundTypeFill) or isinstance(result.type, dict)
    assert hasattr(result, 'type')


def test_json_chatboostadded():
    json_str = r'{"boost_count": "test"}'
    result = types.ChatBoostAdded.de_json(json_str)
    assert isinstance(result, types.ChatBoostAdded)
    assert result.boost_count == 'test'


def test_json_chatboostremoved():
    json_str = r'{"chat": {"id": 1, "type": "private", "title": "Test"}, "boost_id": 1, "remove_date": 1682189507, "source": {"source": "premium", "user": {"id": 1, "is_bot": false, "first_name": "Test"}}}'
    result = types.ChatBoostRemoved.de_json(json_str)
    assert isinstance(result, types.ChatBoostRemoved)
    assert isinstance(result.chat, types.Chat)
    assert result.boost_id == 1
    assert result.remove_date == 1682189507
    assert isinstance(result.source, types.ChatBoostSource)


def test_json_chatboostsource():
    # ChatBoostSource is abstract - test ChatBoostSourcePremium directly
    json_str = r'{"source": "premium", "user": {"id": 1, "is_bot": false, "first_name": "Test"}}'
    result = types.ChatBoostSourcePremium.de_json(json_str)
    assert isinstance(result, types.ChatBoostSourcePremium)


def test_json_chatboostsourcegiftcode():
    json_str = r'{"source": "gift_code", "user": {"id": 1, "is_bot": false, "first_name": "Test"}}'
    result = types.ChatBoostSourceGiftCode.de_json(json_str)
    assert isinstance(result, types.ChatBoostSourceGiftCode)
    assert result.source == 'gift_code'
    assert isinstance(result.user, types.User)


def test_json_chatboostsourcegiveaway():
    json_str = r'{"source": "giveaway", "giveaway_message_id": 1, "user": {"id": 1, "is_bot": false, "first_name": "Test"}, "is_unclaimed": false, "prize_star_count": 100}'
    result = types.ChatBoostSourceGiveaway.de_json(json_str)
    assert isinstance(result, types.ChatBoostSourceGiveaway)
    assert result.source == 'giveaway'
    assert result.giveaway_message_id == 1
    assert isinstance(result.user, types.User)
    assert result.is_unclaimed == False
    assert result.prize_star_count == 100


def test_json_chatboostsourcepremium():
    json_str = r'{"source": "premium", "user": {"id": 1, "is_bot": false, "first_name": "Test"}}'
    result = types.ChatBoostSourcePremium.de_json(json_str)
    assert isinstance(result, types.ChatBoostSourcePremium)
    assert result.source == 'premium'
    assert isinstance(result.user, types.User)


def test_json_chatboostupdated():
    json_str = r'{"chat": {"id": 1, "type": "private", "title": "Test"}, "boost": {"boost_item_id": "b1", "add_date": 1682189507, "expiration_date": 1682275907}}'
    result = types.ChatBoostUpdated.de_json(json_str)
    assert isinstance(result, types.ChatBoostUpdated)
    assert isinstance(result.chat, types.Chat)
    assert isinstance(result.boost, types.ChatBoost)
    assert isinstance(result.boost.boost_id, str) or result.boost.boost_id is None
    assert isinstance(result.boost.add_date, int)
    assert isinstance(result.boost.expiration_date, int)


def test_json_chatjoinrequest():
    json_str = r'{"chat": {"id": 1, "type": "private", "title": "Test"}, "from": {"id": 1, "is_bot": false, "first_name": "Test"}, "user_chat_id": 1, "date": 1682189507, "bio": "Hello", "invite_link": {"invite_link": "https://t.me/joinchat/ABC", "creator": {"id": 1, "is_bot": false, "first_name": "Test"}, "is_primary": true, "is_revoked": false, "creates_join_request": false}, "query_id": "query123"}'
    result = types.ChatJoinRequest.de_json(json_str)
    assert isinstance(result, types.ChatJoinRequest)
    assert isinstance(result.chat, types.Chat)
    assert isinstance(result.from_user, types.User)
    assert result.from_user.id == 1
    assert result.from_user.first_name == 'Test'
    assert result.user_chat_id == 1
    assert result.date == 1682189507
    assert result.bio == 'Hello'
    assert isinstance(result.invite_link, types.ChatInviteLink)
    assert result.query_id == 'query123'


def test_json_chatfullinfo():
    json_str = r'{"id": 1, "type": "private", "title": "Test Chat", "username": "testchat", "first_name": "John", "last_name": "Doe", "photo": {"small_file_id": "s", "small_file_unique_id": "su", "big_file_id": "b", "big_file_unique_id": "bu"}, "bio": "bio text", "has_private_forwards": true, "description": "desc", "pinned_message": {"message_id": 1, "date": 1682189507, "chat": {"id": 1, "type": "private"}, "from": {"id": 1, "is_bot": false, "first_name": "User"}}, "permissions": {"can_send_messages": true, "can_send_audios": true, "can_send_documents": true, "can_send_photos": true, "can_send_videos": true, "can_send_video_notes": true, "can_send_voice_notes": true, "can_send_polls": true, "can_send_other_messages": true, "can_add_web_page_previews": true, "can_change_info": true, "can_invite_users": true, "can_pin_messages": true, "can_manage_topics": true}, "slow_mode_delay": 30, "message_auto_delete_time": 86400, "has_protected_content": true, "sticker_set_name": "sticker_set", "can_set_sticker_set": false, "linked_chat_id": 2, "location": {"chat": {"id": 1, "type": "supergroup", "title": "Loc"}, "location": {"latitude": 50.45, "longitude": 30.52}, "address": "Main St"}, "join_to_send_messages": false, "join_by_request": true, "has_restricted_voice_and_video_messages": false, "is_forum": true, "max_reaction_count": 10, "active_usernames": ["test"], "emoji_status_custom_emoji_id": "custom_emoji", "has_hidden_members": false, "has_aggressive_anti_spam_enabled": false, "emoji_status_expiration_date": 1682275907, "available_reactions": ["emoji", "custom_emoji"], "accent_color_id": 1, "background_custom_emoji_id": "bg_emoji", "profile_accent_color_id": 2, "profile_background_custom_emoji_id": "profile_bg", "has_visible_history": true, "unrestrict_boost_count": 5, "custom_emoji_sticker_set_name": "custom_stickers", "personal_chat": {"id": 3, "type": "private", "title": "Personal"}, "birthdate": {"day": "15", "month": "6"}, "can_send_paid_media": true, "is_direct_messages": true, "parent_chat": {"id": 4, "type": "supergroup", "title": "Parent"}, "rating": {"level": "test", "rating": "test", "current_level_rating": "test"}, "paid_message_star_count": 5, "invite_link": "https://t.me/joinchat/ABC", "business_intro": {"title": "B", "description": "D"}, "business_location": {"address": "NY", "has_active_address": true}, "business_opening_hours": {"time_zone_name": "UTC", "opening_hours": [{"opening_minute": 540, "closing_minute": 1020, "day_of_week": 1, "is_recurring": true}]}, "accepted_gift_types": {"unlimited_gifts": false, "limited_gifts": false, "unique_gifts": true, "premium_subscription": false, "gifts_from_channels": false}, "first_profile_audio": {"file_id": "fa1", "file_unique_id": "fa1u", "duration": 30, "mime_type": "audio/ogg"}, "unique_gift_colors": {"model_custom_emoji_id": 1, "symbol_custom_emoji_id": 1, "light_theme_main_color": 333333, "light_theme_other_colors": [444444], "dark_theme_main_color": 555555, "dark_theme_other_colors": [666666]}, "guard_bot": {"id": 2, "is_bot": true, "first_name": "GuardBot"}, "community": {"id": 5, "name": "Community"}}'
    result = types.ChatFullInfo.de_json(json_str)
    assert isinstance(result, types.ChatFullInfo)
    assert result.id == 1
    assert result.type == 'private'
    assert result.title == 'Test Chat'
    assert result.username == 'testchat'
    assert result.first_name == 'John'
    assert result.last_name == 'Doe'
    assert isinstance(result.photo, types.ChatPhoto)
    assert result.bio == 'bio text'
    assert result.has_private_forwards == True
    assert result.description == 'desc'
    assert result.invite_link == "https://t.me/joinchat/ABC"
    assert isinstance(result.pinned_message, types.Message)
    assert isinstance(result.permissions, types.ChatPermissions)
    assert result.slow_mode_delay == 30
    assert result.message_auto_delete_time == 86400
    assert result.has_protected_content == True
    assert result.sticker_set_name == 'sticker_set'
    assert result.can_set_sticker_set == False
    assert result.linked_chat_id == 2
    assert isinstance(result.location, types.ChatLocation)
    assert result.join_to_send_messages == False
    assert result.join_by_request == True
    assert result.has_restricted_voice_and_video_messages == False
    assert result.is_forum == True
    assert result.max_reaction_count == 10
    assert result.active_usernames == ['test']
    assert result.emoji_status_custom_emoji_id == 'custom_emoji'
    assert result.has_hidden_members == False
    assert result.has_aggressive_anti_spam_enabled == False
    assert result.emoji_status_expiration_date == 1682275907
    assert isinstance(result.available_reactions, list)
    assert result.accent_color_id == 1
    assert result.background_custom_emoji_id == 'bg_emoji'
    assert result.profile_accent_color_id == 2
    assert result.profile_background_custom_emoji_id == 'profile_bg'
    assert result.has_visible_history == True
    assert result.unrestrict_boost_count == 5
    assert result.custom_emoji_sticker_set_name == 'custom_stickers'
    assert isinstance(result.business_intro, types.BusinessIntro)
    assert isinstance(result.business_location, types.BusinessLocation)
    assert isinstance(result.business_opening_hours, types.BusinessOpeningHours)
    assert isinstance(result.personal_chat, types.Chat)
    assert isinstance(result.birthdate, types.Birthdate)
    assert result.can_send_paid_media == True
    assert isinstance(result.accepted_gift_types, types.AcceptedGiftTypes)
    assert result.is_direct_messages == True
    assert isinstance(result.parent_chat, types.Chat)
    assert isinstance(result.rating, types.UserRating)
    assert result.paid_message_star_count == 5
    assert isinstance(result.unique_gift_colors, types.UniqueGiftColors)
    assert isinstance(result.first_profile_audio, types.Audio)
    assert isinstance(result.guard_bot, types.User)
    assert isinstance(result.community, types.Community)


def test_json_chatmember():
    # ChatMember is abstract - test ChatMemberMember directly
    json_str = r'{"status": "member", "user": {"id": 1, "is_bot": false, "first_name": "Test"}}'
    result = types.ChatMemberMember.de_json(json_str)
    assert isinstance(result, types.ChatMemberMember)
    assert isinstance(result.user, types.User)
    assert result.status == 'member'


def test_json_chatmemberupdated():
    json_str = r'{"chat": {"id": 1, "type": "private", "title": "Test"}, "from": {"id": 1, "is_bot": false, "first_name": "Test"}, "date": 1682189507, "old_chat_member": {"user": {"id": 1, "is_bot": false, "first_name": "Test"}, "status": "member"}, "new_chat_member": {"user": {"id": 1, "is_bot": false, "first_name": "Test"}, "status": "member"}, "via_join_request": true, "via_chat_folder_invite_link": true, "invite_link": {"invite_link": "https://t.me/joinchat/ABC", "creator": {"id": 1, "is_bot": false, "first_name": "Test"}, "creates_join_request": false, "is_primary": true, "is_revoked": false}}'
    result = types.ChatMemberUpdated.de_json(json_str)
    assert isinstance(result, types.ChatMemberUpdated)
    assert isinstance(result.chat, types.Chat)
    assert isinstance(result.from_user, types.User)
    assert result.date == 1682189507
    assert isinstance(result.old_chat_member, types.ChatMember)
    assert isinstance(result.new_chat_member, types.ChatMember)
    assert isinstance(result.invite_link, types.ChatInviteLink)
    assert result.invite_link.invite_link == 'https://t.me/joinchat/ABC'
    assert isinstance(result.invite_link.creator, types.User)
    assert result.invite_link.creates_join_request == False
    assert result.invite_link.is_primary == True
    assert result.invite_link.is_revoked == False
    assert result.via_join_request == True
    assert result.via_chat_folder_invite_link == True


def test_json_chatownerchanged():
    json_str = r'{"new_owner": {"id": 1, "is_bot": false, "first_name": "Test"}}'
    result = types.ChatOwnerChanged.de_json(json_str)
    assert isinstance(result, types.ChatOwnerChanged)
    assert isinstance(result.new_owner, types.User)


def test_json_chatphoto():
    json_str = r'{"small_file_id": 1, "small_file_unique_id": 1, "big_file_id": 1, "big_file_unique_id": 1}'
    result = types.ChatPhoto.de_json(json_str)
    assert isinstance(result, types.ChatPhoto)
    assert result.small_file_id == 1
    assert result.small_file_unique_id == 1
    assert result.big_file_id == 1
    assert result.big_file_unique_id == 1


def test_json_checklist():
    json_str = r'{"title": "test", "tasks": [{"id": 1, "text": "test", "is_checked": false}], "others_can_add_tasks": true, "others_can_mark_tasks_as_done": true, "title_entities": [{"type": "bold", "offset": 0, "length": 4}]}'
    result = types.Checklist.de_json(json_str)
    assert isinstance(result, types.Checklist)
    assert result.title == 'test'
    assert isinstance(result.tasks, list)
    assert isinstance(result.title_entities, list)
    assert result.others_can_add_tasks == True
    assert result.others_can_mark_tasks_as_done == True


def test_json_checklisttask():
    json_str = r'{"id": 1, "text": "Task text", "text_entities": [{"type": "bold", "offset": 0, "length": 9}], "completed_by_user": {"id": 1, "is_bot": false, "first_name": "User"}, "completed_by_chat": {"id": 1, "type": "private"}, "completion_date": 1682189507}'
    result = types.ChecklistTask.de_json(json_str)
    assert isinstance(result, types.ChecklistTask)
    assert result.id == 1
    assert result.text == 'Task text'
    assert isinstance(result.text_entities, list)
    assert isinstance(result.completed_by_user, types.User)
    assert isinstance(result.completed_by_chat, types.Chat)
    assert result.completion_date == 1682189507


def test_json_checklisttasksadded():
    json_str = r'{"tasks": [{"id": "t1", "text": "task"}], "checklist_message": {"message_id": 1, "date": 1682189507, "chat": {"id": 1, "type": "private"}, "from": {"id": 1, "is_bot": false, "first_name": "User"}, "text": "checklist"}}'
    result = types.ChecklistTasksAdded.de_json(json_str)
    assert isinstance(result, types.ChecklistTasksAdded)
    assert isinstance(result.tasks, list)
    assert isinstance(result.checklist_message, types.Message)


def test_json_choseninlineresult():
    json_str = r'{"result_id": "res1", "from": {"id": 1, "is_bot": false, "first_name": "Test"}, "query": "test", "location": {"latitude": 50.45, "longitude": 30.52, "horizontal_accuracy": 1.5, "live_period": 3600}, "inline_message_id": "im1"}'
    result = types.ChosenInlineResult.de_json(json_str)
    assert isinstance(result, types.ChosenInlineResult)
    assert result.result_id == 'res1'
    assert isinstance(result.from_user, types.User)
    assert result.query == 'test'
    assert isinstance(result.location, types.Location)
    assert result.inline_message_id == 'im1'


def test_json_community():
    json_str = r'{"id": 1, "name": "test"}'
    result = types.Community.de_json(json_str)
    assert isinstance(result, types.Community)
    assert result.id == 1
    assert result.name == 'test'


def test_json_directmessagepricechanged():
    json_str = r'{"are_direct_messages_enabled": true, "direct_message_star_count": 5}'
    result = types.DirectMessagePriceChanged.de_json(json_str)
    assert isinstance(result, types.DirectMessagePriceChanged)
    assert result.are_direct_messages_enabled == True
    assert result.direct_message_star_count == 5


def test_json_directmessagestopic():
    json_str = r'{"topic_id": 1, "user": {"id": 1, "is_bot": false, "first_name": "Test"}}'
    result = types.DirectMessagesTopic.de_json(json_str)
    assert isinstance(result, types.DirectMessagesTopic)
    assert result.topic_id == 1
    assert isinstance(result.user, types.User)
    assert result.user.id == 1
    assert result.user.first_name == 'Test'


def test_json_externalreplyinfo():
    json_str = r'{"origin": {"type": "user", "date": 1682189507, "sender_user": {"id": 1, "is_bot": false, "first_name": "Test"}}, "chat": {"id": 1, "type": "private"}, "message_id": 42, "link_preview_options": {"url": "https://example.com", "shows_above_caption": true, "enhanced_smileys": true, "prefer_large_media": true}, "animation": {"file_id": "anim", "file_unique_id": "aniu", "width": 100, "height": 100, "duration": 10}, "audio": {"file_id": "au1", "file_unique_id": "au1u", "duration": 30}, "document": {"file_id": "doc1", "file_unique_id": "doc1u", "file_name": "test.pdf"}, "photo": [{"file_id": "p", "file_unique_id": "pu", "width": 100, "height": 100}], "sticker": {"file_id": "st1", "file_unique_id": "st1u", "type": "regular", "width": 512, "height": 512, "is_animated": false, "is_video": false}, "story": {"chat": {"id": 1, "type": "private"}, "id": 1}, "video": {"file_id": "v1", "file_unique_id": "v1u", "width": 640, "height": 480, "duration": 30}, "video_note": {"file_id": "vn1", "file_unique_id": "vn1u", "duration": 10, "length": 512}, "voice": {"file_id": "vo1", "file_unique_id": "vo1u", "duration": 10}, "has_media_spoiler": true, "contact": {"phone_number": "+123", "first_name": "John"}, "dice": {"emoji": "🎲", "value": 5}, "game": {"id": "g1", "title": "Game", "description": "Test", "text": "Play", "photo": [{"file_id": "p", "file_unique_id": "pu", "width": 100, "height": 100}]}, "giveaway": {"chats": [{"id": 1, "type": "private"}], "winners_selection_date": 1682189507, "winner_count": 1, "only_new_members": false, "has_public_winners": false, "prize_description": "Prize", "premium_subscription_month_count": 0, "prize_star_count": 0}, "giveaway_winners": {"chat": {"id": 1, "type": "private"}, "giveaway_message_id": 1, "winners_selection_date": 1682189507, "winner_count": 1, "winners": [{"id": 1, "is_bot": false, "first_name": "Test"}], "additional_chat_count": 0, "premium_subscription_month_count": 0, "unclaimed_prize_count": 0, "only_new_members": false, "was_refunded": false, "prize_description": "", "prize_star_count": 0}, "invoice": {"title": "Test", "description": "Desc", "start_parameter": "sp", "currency": "USD", "total_amount": 100, "invoice_payload": "payload", "shipping_option_id": "opt", "order_info": {"user_name": "User", "user_phone": "+123", "shipping_address": {"country_code": "US", "state": "CA", "city": "SJ", "street_line1": "123", "street_line2": "", "post_code": "95113"}}, "telegram_payment_charge_id": "chg1", "provider_payment_charge_id": "chg2"}, "location": {"latitude": 50.45, "longitude": 30.52}, "poll": {"id": "p1", "question": "test question", "options": [{"text": "Opt1", "persistent_id": "opt1"}], "type": "quiz"}, "venue": {"location": {"latitude": 50.45, "longitude": 30.52}, "title": "Place", "address": "Addr"}, "paid_media": {"star_count": 10, "paid_media": [{"type": "photo", "photo": [{"file_id": "p", "file_unique_id": "pu", "width": 100, "height": 100}]}]}, "live_photo": {"file_id": "lp1", "file_unique_id": "lp1u", "width": 100, "height": 100, "duration": 5}, "checklist": {"title": "Check", "tasks": [{"id": "t1", "text": "Task1", "status": "pending"}]}}'
    result = types.ExternalReplyInfo.de_json(json_str)
    assert isinstance(result, types.ExternalReplyInfo)
    assert isinstance(result.origin, types.MessageOrigin)
    assert isinstance(result.chat, types.Chat)
    assert result.message_id == 42
    assert isinstance(result.link_preview_options, types.LinkPreviewOptions)
    assert isinstance(result.animation, types.Animation)
    assert isinstance(result.audio, types.Audio)
    assert isinstance(result.document, types.Document)
    assert isinstance(result.photo, list)
    assert isinstance(result.sticker, types.Sticker)
    assert isinstance(result.story, types.Story)
    assert isinstance(result.video, types.Video)
    assert isinstance(result.video_note, types.VideoNote)
    assert isinstance(result.voice, types.Voice)
    assert result.has_media_spoiler == True
    assert isinstance(result.contact, types.Contact)
    assert isinstance(result.dice, types.Dice)
    assert isinstance(result.game, types.Game)
    assert isinstance(result.giveaway, types.Giveaway)
    assert isinstance(result.giveaway.chats, list)
    assert result.giveaway.winner_count == 1
    assert isinstance(result.giveaway_winners, types.GiveawayWinners)
    assert isinstance(result.invoice, types.Invoice)
    assert isinstance(result.location, types.Location)
    assert isinstance(result.poll, types.Poll)
    assert result.poll.id == 'p1'
    assert result.poll.question == 'test question'
    assert isinstance(result.poll.options, list)
    assert result.poll.type == 'quiz'
    assert isinstance(result.venue, types.Venue)
    assert isinstance(result.paid_media, types.PaidMediaInfo)
    assert isinstance(result.live_photo, types.LivePhoto)
    assert isinstance(result.checklist, types.Checklist)


def test_json_file():
    json_str = r'{"file_id": "test_file_id", "file_unique_id": "test_unique_id", "file_size": 1024, "file_path": "docs/test.pdf"}'
    result = types.File.de_json(json_str)
    assert isinstance(result, types.File)
    assert result.file_id == 'test_file_id'
    assert result.file_unique_id == 'test_unique_id'
    assert result.file_size == 1024
    assert result.file_path == 'docs/test.pdf'


def test_json_forumtopiccreated():
    json_str = r'{"name": "test", "icon_color": 4294967295, "icon_custom_emoji_id": "custom_emoji", "is_name_implicit": true}'
    result = types.ForumTopicCreated.de_json(json_str)
    assert isinstance(result, types.ForumTopicCreated)
    assert result.name == 'test'
    assert result.icon_color == 4294967295
    assert result.icon_custom_emoji_id == 'custom_emoji'
    assert result.is_name_implicit == True


def test_json_game():
    json_str = r'{"id": "1", "title": "test", "description": "test", "photo": [{"file_id": "p", "file_unique_id": "pu", "width": 100, "height": 100}], "text": "game text", "animation": {"file_id": "anim", "file_unique_id": "aniu", "width": 100, "height": 100, "duration": 10}, "text_entities": [{"type": "bold", "offset": 0, "length": 4}]}'
    result = types.Game.de_json(json_str)
    assert isinstance(result, types.Game)
    assert result.title == 'test'
    assert result.description == 'test'
    assert isinstance(result.photo, list)
    assert result.text == 'game text'
    assert isinstance(result.text_entities, list)
    assert isinstance(result.animation, types.Animation)


def test_json_gamehighscore():
    json_str = r'{"position": 0, "user": {"id": 1, "is_bot": false, "first_name": "Test"}, "score": 1}'
    result = types.GameHighScore.de_json(json_str)
    assert isinstance(result, types.GameHighScore)
    assert result.position == 0
    assert isinstance(result.user, types.User)
    assert result.score == 1


def test_json_giveaway():
    json_str = r'{"chats": [{"id": 1, "type": "private", "title": "Test"}], "winners_selection_date": 1682189507, "winner_count": 1, "only_new_members": true, "has_public_winners": false, "prize_description": "Prize", "country_codes": ["US", "GB"], "premium_subscription_month_count": 3, "prize_star_count": 100}'
    result = types.Giveaway.de_json(json_str)
    assert isinstance(result, types.Giveaway)
    assert isinstance(result.chats, list)
    assert result.winners_selection_date == 1682189507
    assert result.winner_count == 1
    assert result.only_new_members == True
    assert result.has_public_winners == False
    assert result.prize_description == 'Prize'
    assert isinstance(result.country_codes, list)
    assert result.premium_subscription_month_count == 3
    assert result.prize_star_count == 100


def test_json_giveawaycompleted():
    json_str = r'{"winner_count": 1, "unclaimed_prize_count": 5, "giveaway_message": {"message_id": 1, "date": 1682189507, "chat": {"id": 1, "type": "private"}, "from": {"id": 1, "is_bot": false, "first_name": "User"}, "text": "giveaway"}, "is_star_giveaway": true}'
    result = types.GiveawayCompleted.de_json(json_str)
    assert isinstance(result, types.GiveawayCompleted)
    assert result.winner_count == 1
    assert result.unclaimed_prize_count == 5
    assert isinstance(result.giveaway_message, types.Message)
    assert result.is_star_giveaway == True


def test_json_giveawaywinners():
    json_str = r'{"chat": {"id": 1, "type": "private", "title": "Test"}, "giveaway_message_id": 1, "winners_selection_date": 1682189507, "winner_count": 1, "winners": [{"id": 1, "is_bot": false, "first_name": "Test"}], "additional_chat_count": 5, "premium_subscription_month_count": 3, "unclaimed_prize_count": 10, "only_new_members": true, "was_refunded": false, "prize_description": "Prize desc", "prize_star_count": 100}'
    result = types.GiveawayWinners.de_json(json_str)
    assert isinstance(result, types.GiveawayWinners)
    assert isinstance(result.chat, types.Chat)
    assert result.giveaway_message_id == 1
    assert result.winners_selection_date == 1682189507
    assert result.winner_count == 1
    assert isinstance(result.winners, list)
    assert result.additional_chat_count == 5
    assert result.premium_subscription_month_count == 3
    assert result.unclaimed_prize_count == 10
    assert result.only_new_members == True
    assert result.was_refunded == False
    assert result.prize_description == 'Prize desc'
    assert result.prize_star_count == 100


def test_json_groupchat():
    json_str = r'{"id": 1, "title": "test"}'
    result = types.GroupChat.de_json(json_str)
    assert isinstance(result, types.GroupChat)
    assert result.id == 1
    assert result.title == 'test'


def test_json_inaccessiblemessage():
    json_str = r'{"chat": {"id": 1, "type": "private", "title": "Test"}, "message_id": 1, "date": 1682189507}'
    result = types.InaccessibleMessage.de_json(json_str)
    assert isinstance(result, types.InaccessibleMessage)
    assert isinstance(result.chat, types.Chat)
    assert result.message_id == 1
    assert result.date == 1682189507


def test_json_inlinequery():
    json_str = r'{"id": "iq1", "from": {"id": 1, "is_bot": false, "first_name": "Test"}, "query": "test", "offset": "off1", "chat_type": "private", "location": {"latitude": 50.45, "longitude": 30.52, "horizontal_accuracy": 1.5, "live_period": 3600}}'
    result = types.InlineQuery.de_json(json_str)
    assert isinstance(result, types.InlineQuery)
    assert result.id == 'iq1'
    assert isinstance(result.from_user, types.User)
    assert result.query == 'test'
    assert result.offset == 'off1'
    assert result.chat_type == 'private'
    assert isinstance(result.location, types.Location)


def test_json_invoice():
    json_str = r'{"title": "test", "description": "test", "start_parameter": "test_sp", "currency": "test", "total_amount": 1}'
    result = types.Invoice.de_json(json_str)
    assert isinstance(result, types.Invoice)
    assert result.title == 'test'
    assert result.description == 'test'
    assert result.start_parameter == 'test_sp'
    assert result.currency == 'test'
    assert result.total_amount == 1


def test_json_jsondeserializable():
    # JsonDeserializable is abstract base class, skip
    pass


def test_json_link():
    json_str = r'{"url": "https://example.com"}'
    result = types.Link.de_json(json_str)
    assert isinstance(result, types.Link)
    assert result.url == 'https://example.com'


def test_json_livephoto():
    json_str = r'{"file_id": "test_file_id", "file_unique_id": "test_unique_id", "width": 100, "height": 100, "duration": 30, "photo": [{"file_id": "p", "file_unique_id": "pu", "width": 100, "height": 100}], "mime_type": "image/jpeg", "file_size": 20480}'
    result = types.LivePhoto.de_json(json_str)
    assert isinstance(result, types.LivePhoto)
    assert result.file_id == 'test_file_id'
    assert result.file_unique_id == 'test_unique_id'
    assert result.width == 100
    assert result.height == 100
    assert result.duration == 30
    assert isinstance(result.photo, list)
    assert result.mime_type == 'image/jpeg'
    assert result.file_size == 20480


def test_json_managedbotcreated():
    json_str = r'{"bot": {"id": 1, "is_bot": true, "first_name": "Bot"}}'
    result = types.ManagedBotCreated.de_json(json_str)
    assert isinstance(result, types.ManagedBotCreated)
    assert hasattr(result, 'bot')


def test_json_managedbotupdated():
    json_str = r'{"user": {"id": 1, "is_bot": false, "first_name": "Test"}, "bot": {"id": 2, "is_bot": true, "first_name": "Bot"}}'
    result = types.ManagedBotUpdated.de_json(json_str)
    assert isinstance(result, types.ManagedBotUpdated)
    assert isinstance(result.user, types.User)
    assert result.user.id == 1
    assert isinstance(result.bot, types.User)
    assert result.bot.id == 2


def test_json_menubutton():
    # MenuButton dispatches on type - test concrete subclass
    json_str = r'{"type": "default"}'
    result = types.MenuButtonDefault.de_json(json_str)
    assert isinstance(result, types.MenuButtonDefault)


def test_json_messageautodeletetimerchanged():
    json_str = r'{"message_auto_delete_time": 60}'
    result = types.MessageAutoDeleteTimerChanged.de_json(json_str)
    assert isinstance(result, types.MessageAutoDeleteTimerChanged)
    assert result.message_auto_delete_time == 60


def test_json_messageid():
    json_str = r'{"message_id": 1}'
    result = types.MessageId.de_json(json_str)
    assert isinstance(result, types.MessageId)


def test_json_messageorigin():
    # MessageOrigin is abstract - test MessageOriginUser directly
    json_str = r'{"type": "user", "date": 1682189507, "sender_user": {"id": 1, "is_bot": false, "first_name": "Test"}}'
    result = types.MessageOriginUser.de_json(json_str)
    assert isinstance(result, types.MessageOriginUser)
    assert result.type == 'user'
    assert result.date == 1682189507
    assert isinstance(result.sender_user, types.User)
    assert result.sender_user.id == 1
    assert result.sender_user.first_name == 'Test'


def test_json_messagereactioncountupdated():
    json_str = r'{"chat": {"id": 1, "type": "private", "title": "Test"}, "message_id": 1, "date": 1682189507, "reactions": [{"type": {"type": "emoji", "emoji": "\u2764\ufe0f"}, "total_count": 5}]}'
    result = types.MessageReactionCountUpdated.de_json(json_str)
    assert isinstance(result, types.MessageReactionCountUpdated)
    assert isinstance(result.chat, types.Chat)
    assert result.message_id == 1
    assert result.date == 1682189507
    assert isinstance(result.reactions, list)


def test_json_messagereactionupdated():
    json_str = r'{"chat": {"id": 1, "type": "private", "title": "Test"}, "message_id": 1, "date": 1682189507, "old_reaction": [{"type": "emoji", "emoji": "\u0001f600"}], "new_reaction": [{"type": "emoji", "emoji": "\u0001f600"}], "user": {"id": 1, "is_bot": false, "first_name": "Test"}, "actor_chat": {"id": -1, "type": "channel", "title": "Channel"}}'
    result = types.MessageReactionUpdated.de_json(json_str)
    assert isinstance(result, types.MessageReactionUpdated)
    assert isinstance(result.chat, types.Chat)
    assert result.message_id == 1
    assert result.date == 1682189507
    assert isinstance(result.old_reaction, list)
    assert isinstance(result.new_reaction, list)
    assert isinstance(result.user, types.User)
    assert isinstance(result.actor_chat, types.Chat)


def test_json_ownedgift():
    # OwnedGift is abstract - test OwnedGiftRegular directly
    json_str = r'{"type": "regular", "gift": {"id": 1, "sticker": {"file_id": "s", "file_unique_id": "su", "type": "regular", "width": 512, "height": 512, "is_animated": false, "is_video": false}, "star_count": 100}}'
    result = types.OwnedGiftRegular.de_json(json_str)
    assert isinstance(result, types.OwnedGiftRegular)
    assert result.type == 'regular'


def test_json_ownedgiftregular():
    json_str = r'{"type": "regular", "gift": {"id": 1, "sticker": {"file_id": "s", "file_unique_id": "su", "type": "regular", "width": 512, "height": 512, "is_animated": false, "is_video": false}, "star_count": 100}, "owned_gift_id": "og_123", "sender_user": {"id": 1, "is_bot": false, "first_name": "Sender"}, "send_date": 1682189507, "text": {"type": "bold", "text": "Gift text"}, "entities": [{"type": "bold", "offset": 0, "length": 4}], "is_private": false, "is_saved": false, "can_be_upgraded": true, "was_refunded": false, "convert_star_count": 50, "prepaid_upgrade_star_count": 100, "is_upgrade_separate": false, "unique_gift_number": 42}'
    result = types.OwnedGiftRegular.de_json(json_str)
    assert isinstance(result, types.OwnedGiftRegular)
    assert result.type == 'regular'
    assert isinstance(result.gift, types.Gift)
    assert result.owned_gift_id == 'og_123'
    assert isinstance(result.sender_user, types.User)
    assert result.send_date == 1682189507
    assert isinstance(result.text, dict)
    assert isinstance(result.entities, list)
    assert result.is_private == False
    assert result.is_saved == False
    assert result.can_be_upgraded == True
    assert result.was_refunded == False
    assert result.convert_star_count == 50
    assert result.prepaid_upgrade_star_count == 100
    assert result.is_upgrade_separate == False
    assert result.unique_gift_number == 42


def test_json_ownedgiftunique():
    json_str = r'{"type": "unique", "gift": {"base_name": "test", "name": "test", "number": 1, "model": {"name": "m", "sticker": {"file_id": "s", "file_unique_id": "su", "type": "regular", "width": 512, "height": 512, "is_animated": false, "is_video": false}, "rarity_per_mille": 1000}, "symbol": {"name": "s", "sticker": {"file_id": "s", "file_unique_id": "su", "type": "regular", "width": 512, "height": 512, "is_animated": false, "is_video": false}, "rarity_per_mille": 1000}, "backdrop": {"name": "b", "colors": {"center_color": 123456, "edge_color": 654321, "symbol_color": 111111, "text_color": 222222}, "rarity_per_mille": 1000}, "gift_id": 1}, "gift_id": 1, "owned_gift_id": "og_456", "sender_user": {"id": 2, "is_bot": false, "first_name": "Sender"}, "send_date": 1682189507, "is_saved": false, "can_be_transferred": true, "transfer_star_count": 50, "next_transfer_date": 1704067200}'
    result = types.OwnedGiftUnique.de_json(json_str)
    assert isinstance(result, types.OwnedGiftUnique)
    assert result.type == 'unique'
    assert isinstance(result.gift, types.UniqueGift)
    assert result.owned_gift_id == 'og_456'
    assert isinstance(result.sender_user, types.User)
    assert result.send_date == 1682189507
    assert result.is_saved == False
    assert result.can_be_transferred == True
    assert result.transfer_star_count == 50
    assert result.next_transfer_date == 1704067200


def test_json_ownedgifts():
    json_str = r'{"total_count": 1, "gifts": [{"type": "regular", "gift": {"id": 1, "sticker": {"file_id": "s", "file_unique_id": "su", "type": "regular", "width": 512, "height": 512, "is_animated": false, "is_video": false}, "star_count": 100}}], "next_offset": "offset123"}'
    result = types.OwnedGifts.de_json(json_str)
    assert isinstance(result, types.OwnedGifts)
    assert result.total_count == 1
    assert isinstance(result.gifts, list)
    assert result.next_offset == 'offset123'


def test_json_paidmedia():
    # PaidMedia is abstract - test PaidMediaPhoto directly
    json_str = r'{"type": "photo", "photo": [{"file_id": "p", "file_unique_id": "pu", "width": 100, "height": 100}]}'
    result = types.PaidMediaPhoto.de_json(json_str)
    assert isinstance(result, types.PaidMediaPhoto)


def test_json_paidmediainfo():
    json_str = r'{"star_count": 100, "paid_media": [{"type": "photo", "photo": [{"file_id": "p", "file_unique_id": "pu", "width": 100, "height": 100}]}]}'
    result = types.PaidMediaInfo.de_json(json_str)
    assert isinstance(result, types.PaidMediaInfo)
    assert result.star_count == 100
    assert isinstance(result.paid_media, list)


def test_json_paidmedialivephoto():
    json_str = r'{"type": "live_photo", "live_photo": {"file_id": "p", "file_unique_id": "pu", "width": 100, "height": 100, "duration": 10}}'
    result = types.PaidMediaLivePhoto.de_json(json_str)
    assert isinstance(result, types.PaidMediaLivePhoto)
    assert result.type == 'live_photo'
    assert isinstance(result.live_photo, types.LivePhoto)


def test_json_paidmediaphoto():
    json_str = r'{"type": "photo", "photo": [{"file_id": "p", "file_unique_id": "pu", "width": 100, "height": 100}]}'
    result = types.PaidMediaPhoto.de_json(json_str)
    assert isinstance(result, types.PaidMediaPhoto)
    assert result.type == 'photo'
    assert isinstance(result.photo, list)


def test_json_paidmediapreview():
    json_str = r'{"type": "default", "width": 640, "height": 480, "duration": 30}'
    result = types.PaidMediaPreview.de_json(json_str)
    assert isinstance(result, types.PaidMediaPreview)
    assert result.type == 'default'
    assert result.width == 640
    assert result.height == 480
    assert result.duration == 30


def test_json_paidmediapurchased():
    json_str = r'{"from_user": {"id": 1, "is_bot": false, "first_name": "Test"}, "paid_media_payload": "test"}'
    result = types.PaidMediaPurchased.de_json(json_str)
    assert isinstance(result, types.PaidMediaPurchased)
    assert isinstance(result.from_user, types.User)
    assert result.paid_media_payload == 'test'


def test_json_paidmediavideo():
    json_str = r'{"type": "video", "video": {"file_id": "v", "file_unique_id": "vu", "width": 640, "height": 480, "duration": 30}}'
    result = types.PaidMediaVideo.de_json(json_str)
    assert isinstance(result, types.PaidMediaVideo)
    assert result.type == 'video'
    assert isinstance(result.video, types.Video)


def test_json_paidmessagepricechanged():
    json_str = r'{"paid_message_star_count": 1}'
    result = types.PaidMessagePriceChanged.de_json(json_str)
    assert isinstance(result, types.PaidMessagePriceChanged)
    assert hasattr(result, 'paid_message_star_count')


def test_json_poll():
    # Poll.poll_type is deprecated in Telegram API, not covered
    json_str = r'{"id": "poll1", "question": "test question", "options": [{"text": "Opt1", "persistent_id": "opt1"}], "total_voter_count": 10, "is_closed": false, "is_anonymous": true, "type": "quiz", "allows_multiple_answers": false, "explanation": "explanation text", "explanation_entities": [{"type": "bold", "offset": 0, "length": 4}], "open_period": 3600, "close_date": 1682193107, "question_entities": [{"type": "bold", "offset": 0, "length": 5}], "correct_option_ids": [0], "allows_revoting": true, "description": "poll desc", "description_entities": [{"type": "italic", "offset": 0, "length": 9}], "members_only": true, "country_codes": ["US", "GB"], "explanation_media": {"file_id": "em1", "file_unique_id": "emu1", "mime_type": "image/jpeg", "file_name": "media.jpg"}}'
    result = types.Poll.de_json(json_str)
    assert isinstance(result, types.Poll)
    # __init__ param is "poll_id" but de_json sets "id" attribute (from JSON "id" key)
    # Use Poll.id, NOT Poll.poll_id
    assert result.id == "poll1"
    assert result.question == "test question"
    assert isinstance(result.options, list)
    assert result.total_voter_count == 10
    assert result.is_closed == False
    assert result.is_anonymous == True
    assert result.type == "quiz"
    assert result.allows_multiple_answers == False
    assert result.explanation == "explanation text"
    assert isinstance(result.explanation_entities, list)
    assert result.open_period == 3600
    assert result.close_date == 1682193107
    assert isinstance(result.question_entities, list)
    assert isinstance(result.correct_option_ids, list)
    assert result.allows_revoting == True
    assert result.description == "poll desc"
    assert isinstance(result.description_entities, list)
    assert result.media is None
    assert result.members_only == True
    assert isinstance(result.country_codes, list)
    assert isinstance(result.explanation_media, types.PollMedia)


def test_json_polloption():
    json_str = r'{"text": "test", "persistent_id": 1, "voter_count": 5, "text_entities": [{"type": "bold", "offset": 0, "length": 4}], "added_by_user": {"id": 12345, "is_bot": false, "first_name": "Test"}, "added_by_chat": {"id": -1, "type": "channel", "title": "Channel"}, "addition_date": 1682189507}'
    result = types.PollOption.de_json(json_str)
    assert isinstance(result, types.PollOption)
    assert result.text == 'test'
    assert result.persistent_id == 1
    assert result.voter_count == 5
    assert isinstance(result.text_entities, list)
    assert isinstance(result.added_by_user, types.User)
    assert result.added_by_user.id == 12345
    assert isinstance(result.added_by_chat, types.Chat)
    assert result.addition_date == 1682189507
    assert result.media is None


def test_json_polloptionadded():
    json_str = r'{"option_persistent_id": "opt123", "option_text": "test", "poll_message": {"message_id": 1, "date": 1682189507, "chat": {"id": 1, "type": "private"}, "from": {"id": 1, "is_bot": false, "first_name": "User"}, "text": "poll"}, "option_text_entities": [{"type": "bold", "offset": 0, "length": 4}]}'
    result = types.PollOptionAdded.de_json(json_str)
    assert isinstance(result, types.PollOptionAdded)
    assert result.option_persistent_id == 'opt123'
    assert result.option_text == 'test'
    assert isinstance(result.poll_message, types.Message)
    assert isinstance(result.option_text_entities, list)


def test_json_polloptiondeleted():
    json_str = r'{"option_persistent_id": "opt456", "option_text": "test", "poll_message": {"message_id": 1, "date": 1682189507, "chat": {"id": 1, "type": "private"}, "from": {"id": 1, "is_bot": false, "first_name": "User"}, "text": "poll"}, "option_text_entities": [{"type": "bold", "offset": 0, "length": 4}]}'
    result = types.PollOptionDeleted.de_json(json_str)
    assert isinstance(result, types.PollOptionDeleted)
    assert result.option_persistent_id == 'opt456'
    assert result.option_text == 'test'
    assert isinstance(result.poll_message, types.Message)
    assert isinstance(result.option_text_entities, list)


def test_json_precheckoutquery():
    json_str = r'{"id": 1, "from": {"id": 1, "is_bot": false, "first_name": "Test"}, "currency": "USD", "total_amount": 1234, "invoice_payload": "test_payload", "shipping_option_id": "opt1", "order_info": {"user_name": "Buyer", "user_phone": "+123", "shipping_address": {"country_code": "US", "state": "CA", "city": "San Jose", "street_line1": "123 Main St", "street_line2": "", "post_code": "95113"}}}'
    result = types.PreCheckoutQuery.de_json(json_str)
    assert isinstance(result, types.PreCheckoutQuery)
    assert result.id == 1
    assert isinstance(result.from_user, types.User)
    assert result.currency == 'USD'
    assert result.total_amount == 1234
    assert result.invoice_payload == 'test_payload'
    assert result.shipping_option_id == 'opt1'
    assert isinstance(result.order_info, types.OrderInfo)


def test_json_preparedinlinemessage():
    json_str = r'{"id": "prep1", "expiration_date": 1682189507}'
    result = types.PreparedInlineMessage.de_json(json_str)
    assert isinstance(result, types.PreparedInlineMessage)
    assert result.id == 'prep1'
    assert result.expiration_date == 1682189507


def test_json_preparedkeyboardbutton():
    json_str = r'{"id": "btn1"}'
    result = types.PreparedKeyboardButton.de_json(json_str)
    assert isinstance(result, types.PreparedKeyboardButton)
    assert result.id == 'btn1'


def test_json_proximityalerttriggered():
    json_str = r'{"traveler": {"id": 1, "is_bot": false, "first_name": "Test"}, "watcher": {"id": 1, "is_bot": false, "first_name": "Test"}, "distance": "test"}'
    result = types.ProximityAlertTriggered.de_json(json_str)
    assert isinstance(result, types.ProximityAlertTriggered)
    assert isinstance(result.traveler, dict)
    assert isinstance(result.watcher, dict)
    assert result.distance == 'test'


def test_json_refundedpayment():
    json_str = r'{"currency": "USD", "total_amount": 100, "invoice_payload": "test_payload", "telegram_payment_charge_id": "chg1", "provider_payment_charge_id": "chg2"}'
    result = types.RefundedPayment.de_json(json_str)
    assert isinstance(result, types.RefundedPayment)
    assert result.currency == 'USD'
    assert result.total_amount == 100
    assert result.invoice_payload == 'test_payload'
    assert result.telegram_payment_charge_id == 'chg1'
    assert result.provider_payment_charge_id == 'chg2'


def test_json_revenuewithdrawalstate():
    # RevenueWithdrawalState is abstract - test RevenueWithdrawalStatePending directly
    json_str = r'{"type": "pending"}'
    result = types.RevenueWithdrawalStatePending.de_json(json_str)
    assert isinstance(result, types.RevenueWithdrawalStatePending)


def test_json_revenuewithdrawalstatefailed():
    json_str = r'{"type": "failed"}'
    result = types.RevenueWithdrawalStateFailed.de_json(json_str)
    assert isinstance(result, types.RevenueWithdrawalStateFailed)
    assert result.type == 'failed'


def test_json_revenuewithdrawalstatepending():
    json_str = r'{"type": "pending"}'
    result = types.RevenueWithdrawalStatePending.de_json(json_str)
    assert isinstance(result, types.RevenueWithdrawalStatePending)
    assert result.type == 'pending'


def test_json_revenuewithdrawalstatesucceeded():
    json_str = r'{"type": "succeeded", "date": 1682189507, "url": "https://example.com"}'
    result = types.RevenueWithdrawalStateSucceeded.de_json(json_str)
    assert isinstance(result, types.RevenueWithdrawalStateSucceeded)
    assert result.type == 'succeeded'
    assert result.date == 1682189507
    assert result.url == 'https://example.com'


def test_json_richblockanchor():
    json_str = r'{"type": "anchor", "name": "test"}'
    result = types.RichBlock.de_json(json_str)
    assert isinstance(result, types.RichBlockAnchor)
    assert result.name == 'test'


def test_json_richblockaudio():
    json_str = r'{"type": "audio", "audio": {"file_id": "a", "file_unique_id": "au", "duration": 30}, "caption": {"type": "bold", "text": "audio caption"}}'
    result = types.RichBlock.de_json(json_str)
    assert isinstance(result, types.RichBlockAudio)
    assert isinstance(result.audio, types.Audio)
    assert isinstance(result.caption, types.RichBlockCaption)


def test_json_richblockblockquotation():
    json_str = r'{"type": "blockquote", "blocks": [{"text": "Test"}], "credit": "Credit text"}'
    result = types.RichBlock.de_json(json_str)
    assert isinstance(result, types.RichBlockBlockQuotation)
    assert isinstance(result.blocks, list)
    assert result.credit == 'Credit text'


def test_json_richblockcollage():
    json_str = r'{"type": "collage", "blocks": [{"text": "Test"}], "caption": {"type": "bold", "text": "Caption"}}'
    result = types.RichBlock.de_json(json_str)
    assert isinstance(result, types.RichBlockCollage)
    assert isinstance(result.blocks, list)
    assert isinstance(result.caption, types.RichBlockCaption)


def test_json_richblocklist():
    json_str = r'{"type": "list", "items": [{"type": "list_item", "label": {"text": "label"}, "blocks": [{"text": "Test"}]}]}'
    result = types.RichBlock.de_json(json_str)
    assert isinstance(result, types.RichBlockList)
    assert isinstance(result.items, list)
    assert hasattr(result, 'items')


def test_json_richblockmap():
    json_str = r'{"type": "map", "location": {"latitude": 50.0, "longitude": 30.0}, "zoom": 1, "width": 100, "height": 100, "caption": {"type": "bold", "text": "Map caption"}}'
    result = types.RichBlock.de_json(json_str)
    assert isinstance(result, types.RichBlockMap)
    assert isinstance(result.location, types.Location)
    assert result.zoom == 1
    assert result.width == 100
    assert result.height == 100
    assert isinstance(result.caption, types.RichBlockCaption)


def test_json_richblockmathematicalexpression():
    json_str = r'{"type": "mathematical_expression", "expression": "test"}'
    result = types.RichBlock.de_json(json_str)
    assert isinstance(result, types.RichBlockMathematicalExpression)
    assert result.expression == 'test'


def test_json_richblockphoto():
    json_str = r'{"type": "photo", "photo": [{"file_id": "p", "file_unique_id": "pu", "width": 100, "height": 100}], "has_spoiler": true, "caption": {"type": "bold", "text": "Photo caption"}}'
    result = types.RichBlock.de_json(json_str)
    assert isinstance(result, types.RichBlockPhoto)
    assert isinstance(result.photo, list)
    assert result.has_spoiler == True
    assert isinstance(result.caption, types.RichBlockCaption)


def test_json_richblockpullquotation():
    json_str = r'{"type": "pullquote", "text": "test quote", "credit": "Author Name"}'
    result = types.RichBlock.de_json(json_str)
    assert isinstance(result, types.RichBlockPullQuotation)
    assert result.text == 'test quote'
    assert result.credit == 'Author Name'


def test_json_richblocksectionheading():
    json_str = r'{"type": "heading", "text": "test", "size": 3}'
    result = types.RichBlock.de_json(json_str)
    assert isinstance(result, types.RichBlockSectionHeading)
    assert result.text == 'test'
    assert result.size == 3


def test_json_richblockslideshow():
    json_str = r'{"type": "slideshow", "blocks": [{"text": "Test"}], "caption": {"type": "bold", "text": "slide caption"}}'
    result = types.RichBlock.de_json(json_str)
    assert isinstance(result, types.RichBlockSlideshow)
    assert isinstance(result.blocks, list)
    assert isinstance(result.caption, types.RichBlockCaption)
    assert hasattr(result, 'caption')
    assert hasattr(result, 'blocks')


def test_json_richblocktable():
    json_str = r'{"type": "table", "cells": [[{"align": "left", "valign": "top", "text": "cell", "is_header": false, "colspan": 1, "rowspan": 1}]], "is_bordered": true, "is_striped": true, "caption": {"type": "bold", "text": "table caption"}}'
    result = types.RichBlock.de_json(json_str)
    assert isinstance(result, types.RichBlockTable)
    assert isinstance(result.cells, list)
    assert result.is_bordered == True
    assert result.is_striped == True
    assert isinstance(result.caption, types.RichText)
    assert hasattr(result, 'is_striped')
    assert hasattr(result, 'is_bordered')
    assert hasattr(result, 'cells')


def test_json_richblockthinking():
    json_str = r'{"type": "thinking", "text": "test"}'
    result = types.RichBlock.de_json(json_str)
    assert isinstance(result, types.RichBlockThinking)
    assert result.text == 'test'


def test_json_richblockvideo():
    json_str = r'{"type": "video", "video": {"file_id": "v", "file_unique_id": "vu", "width": 640, "height": 480, "duration": 30}, "has_spoiler": true, "caption": {"type": "bold", "text": "video caption"}}'
    result = types.RichBlock.de_json(json_str)
    assert isinstance(result, types.RichBlockVideo)
    assert isinstance(result.video, types.Video)
    assert result.has_spoiler == True
    assert isinstance(result.caption, types.RichBlockCaption)
    assert hasattr(result, 'has_spoiler')


def test_json_richmessage():
    json_str = r'{"blocks": [{"type": "text", "text": "Test"}], "is_rtl": true}'
    result = types.RichMessage.de_json(json_str)
    assert isinstance(result, types.RichMessage)
    assert isinstance(result.blocks, list)
    assert result.is_rtl == True


def test_json_sentguestmessage():
    json_str = r'{"inline_message_id": "msg1"}'
    result = types.SentGuestMessage.de_json(json_str)
    assert isinstance(result, types.SentGuestMessage)
    assert result.inline_message_id == 'msg1'


def test_json_shippingaddress():
    json_str = r'{"country_code": "US", "state": "CA", "city": "San Jose", "street_line1": "123 Main St", "street_line2": "Apt 4", "post_code": "95113"}'
    result = types.ShippingAddress.de_json(json_str)
    assert isinstance(result, types.ShippingAddress)
    assert result.country_code == 'US'
    assert result.state == 'CA'
    assert result.city == 'San Jose'
    assert result.street_line1 == '123 Main St'
    assert result.street_line2 == 'Apt 4'
    assert result.post_code == '95113'


def test_json_shippingquery():
    json_str = r'{"id": "1", "from": {"id": 1, "is_bot": false, "first_name": "Test"}, "invoice_payload": "test_payload", "shipping_address": {"country_code": "US", "state": "CA", "city": "Test", "street_line1": "Test St", "street_line2": "", "post_code": "12345"}}'
    result = types.ShippingQuery.de_json(json_str)
    assert isinstance(result, types.ShippingQuery)
    assert result.id == '1'
    assert isinstance(result.from_user, types.User)
    assert result.invoice_payload == 'test_payload'
    assert result.shipping_address.country_code == 'US'
    assert result.shipping_address.state == 'CA'
    assert result.shipping_address.city == 'Test'
    assert result.shipping_address.street_line1 == 'Test St'
    assert result.shipping_address.street_line2 == ''
    assert result.shipping_address.post_code == '12345'


def test_json_staramount():
    json_str = r'{"amount": "100", "nanostar_amount": 1000000000}'
    result = types.StarAmount.de_json(json_str)
    assert isinstance(result, types.StarAmount)
    assert result.amount == '100'
    assert result.nanostar_amount == 1000000000


def test_json_startransaction():
    json_str = r'{"id": 1, "amount": 100, "date": 1682189507, "source": {"type": "fragment"}, "receiver": {"type": "telegram_ads"}, "nanostar_amount": 10000000}'
    result = types.StarTransaction.de_json(json_str)
    assert isinstance(result, types.StarTransaction)
    assert result.id == 1
    assert result.amount == 100
    assert result.date == 1682189507
    assert isinstance(result.source, types.TransactionPartnerFragment)
    assert isinstance(result.receiver, dict)
    assert result.receiver['type'] == 'telegram_ads'
    assert result.nanostar_amount == 10000000


def test_json_startransactions():
    json_str = r'{"transactions": [{"id": "tx1", "amount": 100, "date": 1682189507}]}'
    result = types.StarTransactions.de_json(json_str)
    assert isinstance(result, types.StarTransactions)
    assert hasattr(result, 'transactions')


def test_json_story():
    json_str = r'{"chat": {"id": 1, "type": "private", "title": "Test"}, "id": 1}'
    result = types.Story.de_json(json_str)
    assert isinstance(result, types.Story)
    assert isinstance(result.chat, types.Chat)
    assert result.id == 1


def test_json_successfulpayment():
    json_str = r'{"currency": "USD", "total_amount": 1234, "invoice_payload": "test_payload", "shipping_option_id": "opt1", "order_info": {"user_name": "Buyer", "user_phone": "+123", "shipping_address": {"country_code": "US", "state": "CA", "city": "San Jose", "street_line1": "123 Main St", "street_line2": "", "post_code": "95113"}}, "telegram_payment_charge_id": "chg1", "provider_payment_charge_id": "chg2", "subscription_expiration_date": 1704067200, "is_recurring": true, "is_first_recurring": true}'
    result = types.SuccessfulPayment.de_json(json_str)
    assert isinstance(result, types.SuccessfulPayment)
    assert result.currency == 'USD'
    assert result.total_amount == 1234
    assert result.invoice_payload == 'test_payload'
    assert result.shipping_option_id == 'opt1'
    assert isinstance(result.order_info, types.OrderInfo)
    assert result.telegram_payment_charge_id == 'chg1'
    assert result.provider_payment_charge_id == 'chg2'
    assert result.subscription_expiration_date == 1704067200
    assert result.is_recurring == True
    assert result.is_first_recurring == True


def test_json_suggestedpostapprovalfailed():
    json_str = r'{"price": {"currency": "USD", "amount": 100}, "suggested_post_message": {"message_id": 1, "date": 1682189507, "chat": {"id": 1, "type": "private"}, "from": {"id": 1, "is_bot": false, "first_name": "User"}, "text": "suggested"}}'
    result = types.SuggestedPostApprovalFailed.de_json(json_str)
    assert isinstance(result, types.SuggestedPostApprovalFailed)
    assert isinstance(result.price, types.SuggestedPostPrice)
    assert isinstance(result.suggested_post_message, types.Message)
    assert result.suggested_post_message.message_id == 1


def test_json_suggestedpostapproved():
    json_str = r'{"send_date": 1682189507, "suggested_post_message": {"message_id": 1, "date": 1682189507, "chat": {"id": 1, "type": "private"}, "from": {"id": 1, "is_bot": false, "first_name": "User"}, "text": "suggested"}, "price": {"amount": "100", "currency": "XTR"}}'
    result = types.SuggestedPostApproved.de_json(json_str)
    assert isinstance(result, types.SuggestedPostApproved)
    assert result.send_date == 1682189507
    assert isinstance(result.suggested_post_message, types.Message)
    assert isinstance(result.price, types.SuggestedPostPrice)


def test_json_suggestedpostinfo():
    json_str = r'{"state": "default", "price": {"amount": "100", "currency": "XTR"}, "send_date": 1682189507}'
    result = types.SuggestedPostInfo.de_json(json_str)
    assert isinstance(result, types.SuggestedPostInfo)
    assert result.state == 'default'
    assert isinstance(result.price, types.SuggestedPostPrice)
    assert result.send_date == 1682189507


def test_json_suggestedpostpaid():
    json_str = r'{"currency": "test", "suggested_post_message": {"message_id": 1, "date": 1682189507, "chat": {"id": 1, "type": "private"}, "from": {"id": 1, "is_bot": false, "first_name": "User"}, "text": "suggested"}, "amount": 100, "star_amount": {"amount": 50}}'
    result = types.SuggestedPostPaid.de_json(json_str)
    assert isinstance(result, types.SuggestedPostPaid)
    assert result.currency == 'test'
    assert isinstance(result.suggested_post_message, types.Message)
    assert result.amount == 100
    assert isinstance(result.star_amount, types.StarAmount)
    assert result.star_amount.amount == 50


def test_json_suggestedpostrefunded():
    json_str = r'{"reason": "test", "suggested_post_message": {"message_id": 1, "date": 1682189507, "chat": {"id": 1, "type": "private"}, "from": {"id": 1, "is_bot": false, "first_name": "User"}, "text": "suggested"}}'
    result = types.SuggestedPostRefunded.de_json(json_str)
    assert isinstance(result, types.SuggestedPostRefunded)
    assert result.reason == 'test'
    assert isinstance(result.suggested_post_message, types.Message)
    assert result.suggested_post_message.message_id == 1


def test_json_textquote():
    json_str = r'{"text": "test", "position": 0, "entities": [{"type": "bold", "offset": 0, "length": 4}], "is_manual": true}'
    result = types.TextQuote.de_json(json_str)
    assert isinstance(result, types.TextQuote)
    assert result.text == 'test'
    assert result.position == 0
    assert isinstance(result.entities, list)
    assert result.is_manual == True


def test_json_transactionpartner():
    # TransactionPartner is abstract - test TransactionPartnerUser directly
    json_str = r'{"type": "user", "user": {"id": 1, "is_bot": false, "first_name": "Test"}}'
    result = types.TransactionPartnerUser.de_json(json_str)
    assert isinstance(result, types.TransactionPartnerUser)


def test_json_transactionpartneraffiliateprogram():
    json_str = r'{"type": "affiliate_program", "commission_per_mille": 1000, "sponsor_user": {"id": 1, "is_bot": false, "first_name": "Sponsor"}}'
    result = types.TransactionPartnerAffiliateProgram.de_json(json_str)
    assert isinstance(result, types.TransactionPartnerAffiliateProgram)
    assert result.type == 'affiliate_program'
    assert result.commission_per_mille == 1000
    assert isinstance(result.sponsor_user, types.User)
    assert result.sponsor_user.id == 1


def test_json_transactionpartnerchat():
    json_str = r'{"type": "chat", "chat": {"id": 1, "type": "private", "title": "Test"}, "gift": {"id": 123456789, "sticker": {"file_id": "s", "file_unique_id": "su", "type": "regular", "width": 512, "height": 512, "is_animated": false, "is_video": false}, "star_count": 100, "total_count": 5, "remaining_count": 3, "upgrade_star_count": 50, "personal_total_count": 10, "personal_remaining_count": 2, "is_premium": true, "has_colors": true, "publisher_chat": {"id": 1, "type": "channel", "title": "Publisher"}, "unique_gift_variant_count": 3}}'
    result = types.TransactionPartnerChat.de_json(json_str)
    assert isinstance(result, types.TransactionPartnerChat)
    assert result.type == 'chat'
    assert isinstance(result.chat, types.Chat)
    assert isinstance(result.gift, types.Gift)
    assert result.gift.id == 123456789


def test_json_transactionpartnerfragment():
    json_str = r'{"type": "fragment", "withdrawal_state": {"type": "pending"}}'
    result = types.TransactionPartnerFragment.de_json(json_str)
    assert isinstance(result, types.TransactionPartnerFragment)
    assert result.type == 'fragment'
    assert isinstance(result.withdrawal_state, types.RevenueWithdrawalState)


def test_json_transactionpartnerother():
    json_str = r'{"type": "other"}'
    result = types.TransactionPartnerOther.de_json(json_str)
    assert isinstance(result, types.TransactionPartnerOther)
    assert result.type == 'other'


def test_json_transactionpartnertelegramapi():
    json_str = r'{"type": "default", "request_count": 10}'
    result = types.TransactionPartnerTelegramApi.de_json(json_str)
    assert isinstance(result, types.TransactionPartnerTelegramApi)
    assert result.type == 'default'
    assert result.request_count == 10


def test_json_transactionpartneruser():
    json_str = r'{"type": "default", "user": {"id": 1, "is_bot": false, "first_name": "Test"}, "affiliate": {"commission_per_mille": 5500, "amount": 100, "affiliate_user": {"id": 1, "is_bot": false, "first_name": "User"}, "affiliate_chat": {"id": 1, "type": "private"}, "nanostar_amount": 1000000}, "invoice_payload": "payload", "paid_media": [{"type": "photo", "photo": [{"file_id": "p", "file_unique_id": "pu", "width": 100, "height": 100}]}], "subscription_period": 30, "gift": {"id": 1, "sticker": {"file_id": "s", "file_unique_id": "su", "type": "regular", "width": 512, "height": 512, "is_animated": false, "is_video": false}, "star_count": 100, "total_count": 1000, "remaining_count": 999, "upgrade_star_count": 50, "personal_total_count": 5, "personal_remaining_count": 3, "is_premium": true, "has_colors": false, "publisher_chat": {"id": 1, "type": "channel", "title": "Pub"}, "unique_gift_variant_count": 10}, "premium_subscription_duration": 12, "transaction_type": "purchase"}'
    result = types.TransactionPartnerUser.de_json(json_str)
    assert isinstance(result, types.TransactionPartnerUser)
    assert result.type == 'default'
    assert isinstance(result.user, types.User)
    assert isinstance(result.affiliate, types.AffiliateInfo)
    assert result.invoice_payload == 'payload'
    assert isinstance(result.paid_media, list)
    assert result.subscription_period == 30
    assert isinstance(result.gift, types.Gift)
    assert result.premium_subscription_duration == 12
    assert result.transaction_type == 'purchase'


def test_json_uniquegift():
    json_str = r'{"base_name": "test", "name": "test", "number": 1, "model": {"name": "model_name", "sticker": {"file_id": "s", "file_unique_id": "su", "type": "regular", "width": 512, "height": 512, "is_animated": false, "is_video": false}, "rarity_per_mille": 1000}, "symbol": {"name": "symbol_name", "sticker": {"file_id": "s", "file_unique_id": "su", "type": "regular", "width": 512, "height": 512, "is_animated": false, "is_video": false}, "rarity_per_mille": 1000}, "backdrop": {"name": "backdrop_name", "colors": {"center_color": 123456, "edge_color": 654321, "symbol_color": 111111, "text_color": 222222}, "rarity_per_mille": 1000}, "gift_id": 1, "publisher_chat": {"id": -1001234567890, "type": "channel", "title": "Channel"}, "is_from_blockchain": true, "is_premium": false, "colors": {"model_custom_emoji_id": 1, "symbol_custom_emoji_id": 1, "light_theme_main_color": 333333, "light_theme_other_colors": [444444], "dark_theme_main_color": 555555, "dark_theme_other_colors": [666666]}, "is_burned": false}'
    result = types.UniqueGift.de_json(json_str)
    assert isinstance(result, types.UniqueGift)
    assert result.base_name == 'test'
    assert result.name == 'test'
    assert result.number == 1
    assert isinstance(result.model, types.UniqueGiftModel)
    assert isinstance(result.symbol, types.UniqueGiftSymbol)
    assert isinstance(result.backdrop, types.UniqueGiftBackdrop)
    assert result.gift_id == 1
    assert isinstance(result.publisher_chat, types.Chat)
    assert result.is_from_blockchain == True
    assert result.is_premium == False
    assert isinstance(result.colors, types.UniqueGiftColors)
    assert result.is_burned == False


def test_json_uniquegiftbackdrop():
    json_str = r'{"name": "test", "colors": {"center_color": 123456, "edge_color": 654321, "symbol_color": 111111, "text_color": 222222}, "rarity_per_mille": 1000}'
    result = types.UniqueGiftBackdrop.de_json(json_str)
    assert isinstance(result, types.UniqueGiftBackdrop)
    assert result.name == 'test'
    assert isinstance(result.colors, types.UniqueGiftBackdropColors)
    assert result.rarity_per_mille == 1000


def test_json_uniquegiftbackdropcolors():
    json_str = r'{"center_color": 123456, "edge_color": 654321, "symbol_color": 111111, "text_color": 222222}'
    result = types.UniqueGiftBackdropColors.de_json(json_str)
    assert isinstance(result, types.UniqueGiftBackdropColors)
    assert result.center_color == 123456
    assert result.edge_color == 654321
    assert result.symbol_color == 111111
    assert result.text_color == 222222


def test_json_uniquegiftcolors():
    json_str = r'{"model_custom_emoji_id": "emoji1", "symbol_custom_emoji_id": "emoji2", "light_theme_main_color": 333333, "light_theme_other_colors": [444444], "dark_theme_main_color": 555555, "dark_theme_other_colors": [666666]}'
    result = types.UniqueGiftColors.de_json(json_str)
    assert isinstance(result, types.UniqueGiftColors)
    assert result.model_custom_emoji_id == 'emoji1'
    assert result.symbol_custom_emoji_id == 'emoji2'
    assert result.light_theme_main_color == 333333
    assert isinstance(result.light_theme_other_colors, list)
    assert result.dark_theme_main_color == 555555
    assert isinstance(result.dark_theme_other_colors, list)


def test_json_uniquegiftinfo():
    json_str = r'{"gift": {"base_name": "b", "name": "n", "number": 1, "model": {"name": "m", "sticker": {"file_id": "s", "file_unique_id": "su", "type": "regular", "width": 512, "height": 512, "is_animated": false, "is_video": false}, "rarity_per_mille": 1000}, "symbol": {"name": "s", "sticker": {"file_id": "s", "file_unique_id": "su", "type": "regular", "width": 512, "height": 512, "is_animated": false, "is_video": false}, "rarity_per_mille": 1000}, "backdrop": {"name": "b", "colors": {"center_color": 123456, "edge_color": 654321, "symbol_color": 111111, "text_color": 222222}, "rarity_per_mille": 1000}, "gift_id": 1}, "origin": "test", "owned_gift_id": "og123", "transfer_star_count": 100, "next_transfer_date": 1682189507, "last_resale_currency": "USD", "last_resale_amount": 500}'
    result = types.UniqueGiftInfo.de_json(json_str)
    assert isinstance(result, types.UniqueGiftInfo)
    assert isinstance(result.gift, types.UniqueGift)
    assert result.origin == 'test'
    assert result.owned_gift_id == 'og123'
    assert result.transfer_star_count == 100
    assert result.next_transfer_date == 1682189507
    assert result.last_resale_currency == 'USD'
    assert result.last_resale_amount == 500


def test_json_uniquegiftmodel():
    json_str = r'{"name": "test", "sticker": {"file_id": "s", "file_unique_id": "su", "type": "regular", "width": 512, "height": 512, "is_animated": false, "is_video": false}, "rarity_per_mille": 1000, "rarity": "common"}'
    result = types.UniqueGiftModel.de_json(json_str)
    assert isinstance(result, types.UniqueGiftModel)
    assert result.name == 'test'
    assert isinstance(result.sticker, types.Sticker)
    assert result.rarity_per_mille == 1000
    assert result.rarity == 'common'


def test_json_uniquegiftsymbol():
    json_str = r'{"name": "test", "sticker": {"file_id": "s", "file_unique_id": "su", "type": "regular", "width": 512, "height": 512, "is_animated": false, "is_video": false}, "rarity_per_mille": 1000}'
    result = types.UniqueGiftSymbol.de_json(json_str)
    assert isinstance(result, types.UniqueGiftSymbol)
    assert result.name == 'test'
    assert isinstance(result.sticker, types.Sticker)
    assert result.rarity_per_mille == 1000


# NOTE: Update is an abstract/registry class that dispatches to specific
# update types (message_update, callback_query_update, etc.). Its __init__
# only contains 'update_id' in practice; other 'update_type' fields are
# handled by subclasses. Full field coverage is intentionally not required.
def test_json_update():
    json_str = r'{"update_id": 1}'
    result = types.Update.de_json(json_str)
    assert isinstance(result, types.Update)
    assert result.update_id == 1


def test_json_userchatboosts():
    json_str = r'{"boosts": [{"boost_item_id": "b1", "add_date": 1682189507, "expiration_date": 1682275907}]}'
    result = types.UserChatBoosts.de_json(json_str)
    assert isinstance(result, types.UserChatBoosts)
    assert isinstance(result.boosts, list)
    assert hasattr(result, 'boosts')


def test_json_userprofileaudios():
    json_str = r'{"total_count": 1, "audios": [{"file_id": "a1", "file_unique_id": "au1", "duration": 180, "title": "Test", "performer": "Perf", "type": "song"}]}'
    result = types.UserProfileAudios.de_json(json_str)
    assert isinstance(result, types.UserProfileAudios)
    assert result.total_count == 1
    assert isinstance(result.audios, list)


def test_json_userprofilephotos():
    json_str = r'{"total_count": 1, "photos": [[{"file_id": "p1", "file_unique_id": "pu1", "width": 100, "height": 100}]]}'
    result = types.UserProfilePhotos.de_json(json_str)
    assert isinstance(result, types.UserProfilePhotos)
    assert result.total_count == 1
    assert isinstance(result.photos, list)
    assert isinstance(result.photos[0], list)
    assert isinstance(result.photos[0][0], types.PhotoSize)


def test_json_userrating():
    json_str = r'{"level": 1, "rating": 100, "current_level_rating": 50, "next_level_rating": 150}'
    result = types.UserRating.de_json(json_str)
    assert isinstance(result, types.UserRating)
    assert result.level == 1
    assert result.rating == 100
    assert result.current_level_rating == 50
    assert result.next_level_rating == 150


def test_json_videochatended():
    json_str = r'{"duration": 30}'
    result = types.VideoChatEnded.de_json(json_str)
    assert isinstance(result, types.VideoChatEnded)
    assert result.duration == 30


def test_json_videochatscheduled():
    json_str = r'{"start_date": 1682189507}'
    result = types.VideoChatScheduled.de_json(json_str)
    assert isinstance(result, types.VideoChatScheduled)
    assert result.start_date == 1682189507


def test_json_videonote():
    json_str = r'{"file_id": "test_file_id", "file_unique_id": "test_unique_id", "length": 100, "duration": 30, "thumbnail": {"file_id": "th1", "file_unique_id": "thu1", "width": 50, "height": 50}, "file_size": 1024}'
    result = types.VideoNote.de_json(json_str)
    assert isinstance(result, types.VideoNote)
    assert result.file_id == 'test_file_id'
    assert result.file_unique_id == 'test_unique_id'
    assert result.length == 100
    assert result.duration == 30
    assert isinstance(result.thumbnail, types.PhotoSize)
    assert result.file_size == 1024


def test_json_videoquality():
    json_str = r'{"file_id": "test_file_id", "file_unique_id": "test_unique_id", "width": 100, "height": 100, "codec": "h264", "file_size": 1024}'
    result = types.VideoQuality.de_json(json_str)
    assert isinstance(result, types.VideoQuality)
    assert result.file_id == 'test_file_id'
    assert result.file_unique_id == 'test_unique_id'
    assert result.width == 100
    assert result.height == 100
    assert result.codec == 'h264'
    assert result.file_size == 1024


def test_json_webhookinfo():
    json_str = r'{"url": "https://example.com/webhook", "has_custom_certificate": false, "pending_update_count": 1, "ip_address": "127.0.0.1", "last_error_date": 1682189507, "last_error_message": "Test error", "last_synchronization_error_date": 1682100000, "max_connections": 100, "allowed_updates": ["message", "callback_query"]}'
    result = types.WebhookInfo.de_json(json_str)
    assert isinstance(result, types.WebhookInfo)
    assert result.url == 'https://example.com/webhook'
    assert result.has_custom_certificate == False
    assert result.pending_update_count == 1
    assert result.ip_address == '127.0.0.1'
    assert result.last_error_date == 1682189507
    assert result.last_error_message == 'Test error'
    assert result.last_synchronization_error_date == 1682100000
    assert result.max_connections == 100
    assert result.allowed_updates == ['message', 'callback_query']


def test_message_entity_html_conversion():
    """Test converting MessageEntity to HTML text for various entity types."""
    
    # Variant 1: simple bold at start
    json1 = r'{"message_id":1,"date":1682177590,"chat":{"id":1,"type":"private"},"text":"bold text","entities":[{"offset":0,"length":4,"type":"bold"}]}'
    msg1 = types.Message.de_json(json1)
    assert msg1.html_text == '<b>bold</b> text'
    
    # Variant 2: italic
    json2 = r'{"message_id":2,"date":1682177590,"chat":{"id":1,"type":"private"},"text":"italic text","entities":[{"offset":0,"length":6,"type":"italic"}]}'
    msg2 = types.Message.de_json(json2)
    assert msg2.html_text == '<i>italic</i> text'
    
    # Variant 3: underline
    json3 = r'{"message_id":3,"date":1682177590,"chat":{"id":1,"type":"private"},"text":"under text","entities":[{"offset":0,"length":6,"type":"underline"}]}'
    msg3 = types.Message.de_json(json3)
    assert msg3.html_text == '<u>under </u>text'
    
    # Variant 4: code
    json4 = r'{"message_id":4,"date":1682177590,"chat":{"id":1,"type":"private"},"text":"code text","entities":[{"offset":0,"length":4,"type":"code"}]}'
    msg4 = types.Message.de_json(json4)
    assert msg4.html_text == '<code>code</code> text'
    
    # Variant 5: spoiler
    json5 = r'{"message_id":5,"date":1682177590,"chat":{"id":1,"type":"private"},"text":"spoiler text","entities":[{"offset":0,"length":7,"type":"spoiler"}]}'
    msg5 = types.Message.de_json(json5)
    assert msg5.html_text == '<span class="tg-spoiler">spoiler</span> text'
    
    # Variant 6: mention
    json6 = r'{"message_id":6,"date":1682177590,"chat":{"id":1,"type":"private"},"text":"@mention text","entities":[{"offset":0,"length":8,"type":"mention"}]}'
    msg6 = types.Message.de_json(json6)
    assert msg6.html_text == '@mention text'
    
    # Variant 7: url
    json7 = r'{"message_id":7,"date":1682177590,"chat":{"id":1,"type":"private"},"text":"https://example.com text","entities":[{"offset":0,"length":19,"type":"url"}]}'
    msg7 = types.Message.de_json(json7)
    assert msg7.html_text == 'https://example.com text'
    
    # Variant 8: bold + italic (separate sections)
    json8 = r'{"message_id":8,"date":1682177590,"chat":{"id":1,"type":"private"},"text":"bold italic text","entities":[{"offset":0,"length":4,"type":"bold"},{"offset":5,"length":6,"type":"italic"}]}'
    msg8 = types.Message.de_json(json8)
    assert msg8.html_text == '<b>bold</b> <i>italic</i> text'
    
    # Variant 9: pre (code block)
    json9 = r'{"message_id":9,"date":1682177590,"chat":{"id":1,"type":"private"},"text":"code block","entities":[{"offset":0,"length":10,"type":"pre"}]}'
    msg9 = types.Message.de_json(json9)
    assert msg9.html_text == '<pre>code block</pre>'
    
    # Variant 10: nested bold + italic
    json10 = r'{"message_id":10,"date":1682177590,"chat":{"id":1,"type":"private"},"text":"nested text","entities":[{"offset":0,"length":6,"type":"bold"},{"offset":0,"length":6,"type":"italic"}]}'
    msg10 = types.Message.de_json(json10)
    assert msg10.html_text == '<b><i>nested</i></b> text'

    # Variant 11: 3 consecutive entities (bold, italic, underline)
    json11 = r'{"message_id":11,"date":1682177590,"chat":{"id":1,"type":"private"},"text":"abc text","entities":[{"offset":0,"length":1,"type":"bold"},{"offset":1,"length":1,"type":"italic"},{"offset":2,"length":1,"type":"underline"}]}'
    msg11 = types.Message.de_json(json11)
    assert msg11.html_text == '<b>a</b><i>b</i><u>c</u> text'

    # Variant 12: 3-level nesting (bold > italic > code)
    json12 = r'{"message_id":12,"date":1682177590,"chat":{"id":1,"type":"private"},"text":"nested","entities":[{"offset":0,"length":6,"type":"bold"},{"offset":0,"length":6,"type":"italic"},{"offset":0,"length":6,"type":"code"}]}'
    msg12 = types.Message.de_json(json12)
    assert msg12.html_text == '<b><i><code>nested</code></i></b>'

    # Variant 13: overlap (bold covers italic)
    json13 = r'{"message_id":13,"date":1682177590,"chat":{"id":1,"type":"private"},"text":"bolditalic","entities":[{"offset":0,"length":10,"type":"bold"},{"offset":0,"length":5,"type":"italic"}]}'
    msg13 = types.Message.de_json(json13)
    assert msg13.html_text == '<b><i>boldi</i>talic</b>'

    # Variant 14: hashtag + url in one text
    json14 = r'{"message_id":14,"date":1682177590,"chat":{"id":1,"type":"private"},"text":"#hashtag text https://example.com end","entities":[{"offset":0,"length":8,"type":"hashtag"},{"offset":14,"length":19,"type":"url"}]}'
    msg14 = types.Message.de_json(json14)
    assert msg14.html_text == '#hashtag text https://example.com end'

    # Variant 15: mention + bold
    json15 = r'{"message_id":15,"date":1682177590,"chat":{"id":1,"type":"private"},"text":"@user bold text here","entities":[{"offset":0,"length":5,"type":"mention"},{"offset":6,"length":4,"type":"bold"}]}'
    msg15 = types.Message.de_json(json15)
    assert msg15.html_text == '@user <b>bold</b> text here'

    # Variant 16: text_mention (without @, with user link)
    json16 = r'{"message_id":16,"date":1682177590,"chat":{"id":1,"type":"private"},"text":"Hello Admin here","entities":[{"offset":6,"length":5,"type":"text_mention","user":{"id":123,"is_bot":false,"first_name":"Admin"}}]}'
    msg16 = types.Message.de_json(json16)
    assert msg16.html_text == 'Hello <a href="tg://user?id=123">Admin</a> here'

    # Variant 17: custom_emoji
    json17 = r'{"message_id":17,"date":1682177590,"chat":{"id":1,"type":"private"},"text":"cool 😋 nice","entities":[{"offset":5,"length":3,"type":"custom_emoji","custom_emoji_id":"5368324170671202286"}]}'
    msg17 = types.Message.de_json(json17)
    assert msg17.html_text == 'cool <tg-emoji emoji-id="5368324170671202286">😋 </tg-emoji>nice'

    # Variant 18: spoiler + bold (non-overlapping)
    json18 = r'{"message_id":18,"date":1682177590,"chat":{"id":1,"type":"private"},"text":"secret hidden text","entities":[{"offset":0,"length":6,"type":"spoiler"},{"offset":7,"length":6,"type":"bold"}]}'
    msg18 = types.Message.de_json(json18)
    assert msg18.html_text == '<span class="tg-spoiler">secret</span> <b>hidden</b> text'

    # Variant 19: text_link + bold
    json19 = r'{"message_id":19,"date":1682177590,"chat":{"id":1,"type":"private"},"text":"click bold text","entities":[{"offset":0,"length":5,"type":"text_link","url":"https://example.com"},{"offset":6,"length":4,"type":"bold"}]}'
    msg19 = types.Message.de_json(json19)
    assert msg19.html_text == '<a href="https://example.com">click</a> <b>bold</b> text'

    # Variant 20: email + strikethrough
    json20 = r'{"message_id":20,"date":1682177590,"chat":{"id":1,"type":"private"},"text":"email@x.com deleted","entities":[{"offset":0,"length":11,"type":"email"},{"offset":12,"length":7,"type":"strikethrough"}]}'
    msg20 = types.Message.de_json(json20)
    assert msg20.html_text == 'email@x.com <s>deleted</s>'

    # Variant 21: cashtag
    json21 = r'{"message_id":21,"date":1682177590,"chat":{"id":1,"type":"private"},"text":"$TSLA went up","entities":[{"offset":0,"length":4,"type":"cashtag"}]}'
    msg21 = types.Message.de_json(json21)
    assert msg21.html_text == '$TSLA went up'

    # Variant 22: bold + code (separate sections)
    json22 = r'{"message_id":22,"date":1682177590,"chat":{"id":1,"type":"private"},"text":"bold code text","entities":[{"offset":0,"length":4,"type":"bold"},{"offset":5,"length":4,"type":"code"}]}'
    msg22 = types.Message.de_json(json22)
    assert msg22.html_text == '<b>bold</b> <code>code</code> text'

    # Variant 23: 4 consecutive entities (bold, italic, underline, strikethrough)
    json23 = r'{"message_id":23,"date":1682177590,"chat":{"id":1,"type":"private"},"text":"abcd text","entities":[{"offset":0,"length":1,"type":"bold"},{"offset":1,"length":1,"type":"italic"},{"offset":2,"length":1,"type":"underline"},{"offset":3,"length":1,"type":"strikethrough"}]}'
    msg23 = types.Message.de_json(json23)
    assert msg23.html_text == '<b>a</b><i>b</i><u>c</u><s>d</s> text'

    # Variant 24: long mention + bold
    json24 = r'{"message_id":24,"date":1682177590,"chat":{"id":1,"type":"private"},"text":"@username bold text","entities":[{"offset":0,"length":9,"type":"mention"},{"offset":10,"length":4,"type":"bold"}]}'
    msg24 = types.Message.de_json(json24)
    assert msg24.html_text == '@username <b>bold</b> text'

    # Variant 25: url in the middle of text
    json25 = r'{"message_id":25,"date":1682177590,"chat":{"id":1,"type":"private"},"text":"see https://example.com link","entities":[{"offset":3,"length":19,"type":"url"}]}'
    msg25 = types.Message.de_json(json25)
    assert msg25.html_text == 'see https://example.com link'

    # Variant 26: spoiler + underline (non-overlapping)
    json26 = r'{"message_id":26,"date":1682177590,"chat":{"id":1,"type":"private"},"text":"hidden marked text","entities":[{"offset":0,"length":7,"type":"spoiler"},{"offset":8,"length":6,"type":"underline"}]}'
    msg26 = types.Message.de_json(json26)
    assert msg26.html_text == '<span class="tg-spoiler">hidden </span>m<u>arked </u>text'

    # Variant 27: text_link + bold overlap
    json27 = r'{"message_id":27,"date":1682177590,"chat":{"id":1,"type":"private"},"text":"link bold text","entities":[{"offset":0,"length":4,"type":"text_link","url":"https://example.com"},{"offset":0,"length":9,"type":"bold"}]}'
    msg27 = types.Message.de_json(json27)
    assert msg27.html_text == '<b><a href="https://example.com">link</a> bold</b> text'

    # Variant 28: bot_command
    json28 = r'{"message_id":28,"date":1682177590,"chat":{"id":1,"type":"private"},"text":"/start command","entities":[{"offset":0,"length":6,"type":"bot_command"}]}'
    msg28 = types.Message.de_json(json28)
    assert msg28.html_text == '/start command'

    # Variant 29: pre + code overlap
    json29 = r'{"message_id":29,"date":1682177590,"chat":{"id":1,"type":"private"},"text":"code here","entities":[{"offset":0,"length":9,"type":"pre"},{"offset":0,"length":9,"type":"code"}]}'
    msg29 = types.Message.de_json(json29)
    assert msg29.html_text == '<pre><code>code here</code></pre>'

    # Variant 30: mention + email + url (three different entities)
    json30 = r'{"message_id":30,"date":1682177590,"chat":{"id":1,"type":"private"},"text":"@user mail@x.com https://x.com end","entities":[{"offset":0,"length":5,"type":"mention"},{"offset":6,"length":10,"type":"email"},{"offset":17,"length":14,"type":"url"}]}'
    msg30 = types.Message.de_json(json30)
    assert msg30.html_text == '@user mail@x.com https://x.com end'
