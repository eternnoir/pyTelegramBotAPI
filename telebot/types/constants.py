from enum import Enum
from typing import Optional, Union


class StrEnum(Enum):
    def __str__(self) -> str:
        return self.value

    def __repr__(self) -> str:
        return str(self)


class MediaContentType(StrEnum):
    text = "text"
    audio = "audio"
    animation = "animation"
    document = "document"
    photo = "photo"
    sticker = "sticker"
    video = "video"
    video_note = "video_note"
    voice = "voice"
    contact = "contact"
    dice = "dice"
    poll = "poll"
    venue = "venue"
    location = "location"


class ServiceContentType(StrEnum):
    new_chat_members = "new_chat_members"
    left_chat_member = "left_chat_member"
    new_chat_title = "new_chat_title"
    new_chat_photo = "new_chat_photo"
    delete_chat_photo = "delete_chat_photo"
    group_chat_created = "group_chat_created"
    supergroup_chat_created = "supergroup_chat_created"
    channel_chat_created = "channel_chat_created"
    migrate_to_chat_id = "migrate_to_chat_id"
    migrate_from_chat_id = "migrate_from_chat_id"
    pinned_message = "pinned_message"
    proximity_alert_triggered = "proximity_alert_triggered"
    video_chat_scheduled = "video_chat_scheduled"
    video_chat_started = "video_chat_started"
    video_chat_ended = "video_chat_ended"
    video_chat_participants_invited = "video_chat_participants_invited"
    message_auto_delete_timer_changed = "message_auto_delete_timer_changed"


ContentType = Union[MediaContentType, ServiceContentType]


def content_type_from_str(ct: str) -> Optional[ContentType]:
    try:
        return MediaContentType(ct)
    except ValueError:
        try:
            return ServiceContentType(ct)
        except ValueError:
            return None


class UpdateType(StrEnum):
    message = "message"
    edited_message = "edited_message"
    channel_post = "channel_post"
    edited_channel_post = "edited_channel_post"
    inline_query = "inline_query"
    chosen_inline_result = "chosen_inline_result"
    callback_query = "callback_query"
    shipping_query = "shipping_query"
    pre_checkout_query = "pre_checkout_query"
    poll = "poll"
    poll_answer = "poll_answer"
    my_chat_member = "my_chat_member"
    chat_member = "chat_member"
    chat_join_request = "chat_join_request"


class ChatType(StrEnum):
    private = "private"
    group = "group"
    supergroup = "supergroup"
    channel = "channel"
