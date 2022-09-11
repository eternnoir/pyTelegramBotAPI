import inspect
import math
import time
import uuid
from collections import defaultdict, deque
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from types import MethodType
from typing import Any, Callable, Optional, TypeVar, Union

from telebot import AsyncTeleBot, api, constants, filters, types


@dataclass
class MethodCall:
    method_name: str
    timestamp: float
    args: tuple[Any, ...]
    kwargs: dict[str, Any]
    full_kwargs: dict[str, Any]  # dict with args converted to kwargs for easy access


MOCKED_METHOD_NAMES: set[str] = set()

# MockAsyncTeleBot aims at mocking only "active" bot actions like sending a message,
# so these should work as usual
UNMOCKABLE_METHOD_NAMES = {
    "close",
    "log_out",
    "reply_to",  # conveniense method, calls, send_message
    "close_session",
    "get_updates",
    "infinity_polling",
    "update_listener",
    "add_custom_filter",
    "skip_updates",
    # update processing logic
    "process_new_updates",
    "_process_update",
    "_test_handler",
    "_test_filter",
    "_test_custom_filters",
    # functions for registering handlers do not require mocking
    "message_handler",
    "edited_message_handler",
    "channel_post_handler",
    "edited_channel_post_handler",
    "callback_query_handler",
    "_simple_handler",
    "inline_query_handler",
    "chosen_inline_result_handler",
    "shipping_query_handler",
    "pre_checkout_query_handler",
    "poll_handler",
    "poll_answer_handler",
    "my_chat_member_handler",
    "chat_member_handler",
    "chat_join_request_handler",
}


AsyncTeleBotMethodT = TypeVar("AsyncTeleBotMethodT", bound=Callable)


NO_DEFAULT_RETURN_VALUE = object()


class NoDefaultValueException(Exception):
    pass


def mocked(method: AsyncTeleBotMethodT, method_name: Optional[str] = None) -> AsyncTeleBotMethodT:
    method_name_ = method_name or method.__name__
    MOCKED_METHOD_NAMES.add(method_name_)

    async def decorated(self: "MockedAsyncTeleBot", *args, **kwargs):
        method_param_names = [
            param_name for param_name in inspect.signature(method).parameters.keys() if param_name != "self"
        ]
        full_kwargs = dict(zip(method_param_names, args))
        full_kwargs.update(kwargs)
        method_call = MethodCall(
            method_name=method_name_,
            timestamp=time.time(),
            args=args,
            kwargs=kwargs,
            full_kwargs=full_kwargs,
        )
        self.method_calls[method_name_].append(method_call)
        try:
            default = await method(self, *args, **kwargs)
        except NoDefaultValueException:
            default = NO_DEFAULT_RETURN_VALUE
        return_value = self._from_return_values_queue(method_name_, default)
        if default is NO_DEFAULT_RETURN_VALUE and return_value is NO_DEFAULT_RETURN_VALUE:
            raise RuntimeError(
                f"Bad test setup: {method_name_!r} was called, but this mocked method does not specify "
                + "default return value and no return values were found in the queue; to fix this, call "
                + f'mocked_bot_instance.add_return_values("{method_name_}", return_value_1, return_value_2, ...); '
                + f"method call details: {method_call}"
            )
        if isinstance(return_value, Exception):
            raise return_value
        else:
            return return_value

    return decorated  # type: ignore


MethodReturnValueT = TypeVar("MethodReturnValueT")


class MockedAsyncTeleBot(AsyncTeleBot):
    """
    Mocked AsyncTeleBot provides the same interface as the real one, but returns mocked data and
    stores all method calls internally as MethodCall objects. Please note that it may not be
    sophisticated enough for testing complex behaviours, but should cover basic cases like
    answering a message or handling inline menu clicks.

    The class is packaged with the rest of the library to allow downstream apps to use it for testing.

    Example usage:
    >>> bot = MockAsyncTeleBot("dummy-token")
    """

    def __init__(
        self,
        token: str,
        parse_mode: Optional[str] = None,
        offset: Optional[int] = None,
        custom_filters: Optional[list[filters.AnyCustomFilter]] = None,
        force_allowed_updates: Optional[list[constants.UpdateType]] = None,
    ):
        super().__init__(token, parse_mode, offset, custom_filters, force_allowed_updates)
        self.method_calls: dict[str, list[MethodCall]] = defaultdict(list)
        self._return_value_queues: dict[str, deque[Any]] = defaultdict(deque)
        self._repeating_return_values: dict[str, deque[Any]] = defaultdict(deque)
        self._latest_message_id_by_chat: dict[Union[int, str], int] = defaultdict(lambda: 0)

        no_default_method_names = {
            mn
            for mn in dir(AsyncTeleBot)
            if not (mn.startswith("__") or mn in UNMOCKABLE_METHOD_NAMES or mn in MOCKED_METHOD_NAMES)
        }
        for method_name in no_default_method_names:
            setattr(
                self,
                method_name,
                MethodType(mocked(self._no_default_value_mocked_method, method_name=method_name), self),
            )

    async def _no_default_value_mocked_method(self, *args, **kwargs):
        raise NoDefaultValueException()

    def add_return_values(self, method_name: str, *values: Any, repeating: bool = False):
        """Can be used from tests to specify return values of mocked methods. Also supports exception to emulate
        errors occuring during Telegram API call"""
        if repeating:
            self._repeating_return_values[method_name].extend(values)
        else:
            self._return_value_queues[method_name].extend(values)

    def _from_return_values_queue(self, method_name: str, default: MethodReturnValueT) -> MethodReturnValueT:
        """Called from mocked methods to return values from return value queue or default, if the queue is empty"""
        try:
            return self._return_value_queues[method_name].popleft()
        except IndexError:
            try:
                queue = self._repeating_return_values[method_name]
                v = queue.popleft()
                queue.append(v)
                return v
            except IndexError:
                return default

    def _get_new_message_id(self, chat_id: Union[int, str]) -> int:
        # each time the bot requests new message id (e.g. to emulate sent message) we advance id counter by 2
        # to emulate some other activity in the chat (user/service messages); this should not be a problem
        # unless the app relies on specific message id offsets
        self._latest_message_id_by_chat[chat_id] += 2
        return self._latest_message_id_by_chat[chat_id]

    @mocked
    async def add_sticker_to_set(
        self,
        user_id: int,
        name: str,
        emojis: str,
        png_sticker: Optional[Union[Any, str]] = None,
        tgs_sticker: Optional[Union[Any, str]] = None,
        webm_sticker: Optional[Union[Any, str]] = None,
        mask_position: Optional[types.MaskPosition] = None,
    ) -> bool:
        return True

    @mocked
    async def answer_callback_query(
        self,
        callback_query_id: int,
        text: Optional[str] = None,
        show_alert: Optional[bool] = None,
        url: Optional[str] = None,
        cache_time: Optional[int] = None,
    ) -> bool:
        return True

    @mocked
    async def answer_inline_query(
        self,
        inline_query_id: str,
        results: list[Any],
        cache_time: Optional[int] = None,
        is_personal: Optional[bool] = None,
        next_offset: Optional[str] = None,
        switch_pm_text: Optional[str] = None,
        switch_pm_parameter: Optional[str] = None,
    ) -> bool:
        return True

    @mocked
    async def answer_pre_checkout_query(
        self, pre_checkout_query_id: int, ok: bool, error_message: Optional[str] = None
    ) -> bool:
        return True

    @mocked
    async def answer_shipping_query(
        self,
        shipping_query_id: str,
        ok: bool,
        shipping_options: Optional[list[types.ShippingOption]] = None,
        error_message: Optional[str] = None,
    ) -> bool:
        return True

    @mocked
    async def answer_web_app_query(
        self, web_app_query_id: str, result: types.InlineQueryResultBase
    ) -> types.SentWebAppMessage:
        return types.SentWebAppMessage()

    @mocked
    async def approve_chat_join_request(self, chat_id: Union[str, int], user_id: Union[int, str]) -> bool:
        return True

    @mocked
    async def ban_chat_member(
        self,
        chat_id: Union[int, str],
        user_id: int,
        until_date: Optional[Union[int, datetime]] = None,
        revoke_messages: Optional[bool] = None,
    ) -> bool:
        return True

    @mocked
    async def ban_chat_sender_chat(self, chat_id: Union[int, str], sender_chat_id: Union[int, str]) -> bool:
        return True

    @mocked
    async def copy_message(
        self,
        chat_id: Union[int, str],
        from_chat_id: Union[int, str],
        message_id: int,
        caption: Optional[str] = None,
        parse_mode: Optional[str] = None,
        caption_entities: Optional[list[types.MessageEntity]] = None,
        disable_notification: Optional[bool] = None,
        protect_content: Optional[bool] = None,
        reply_to_message_id: Optional[int] = None,
        allow_sending_without_reply: Optional[bool] = None,
        reply_markup: Optional[types.ReplyMarkup] = None,
        timeout: Optional[int] = None,
    ) -> types.MessageID:
        return types.MessageID(self._get_new_message_id(chat_id))

    def _get_me(self) -> types.User:
        return types.User(
            id=abs(hash(self.token)) % 100_000,
            is_bot=True,
            first_name="MockedAsyncTeleBot",
            username="MockedAsyncTeleBot",
        )

    @mocked
    async def get_me(self) -> types.User:
        return self._get_me()

    @mocked
    async def create_chat_invite_link(
        self,
        chat_id: Union[int, str],
        name: Optional[str] = None,
        expire_date: Optional[Union[int, datetime]] = None,
        member_limit: Optional[int] = None,
        creates_join_request: Optional[bool] = None,
    ) -> types.ChatInviteLink:
        return types.ChatInviteLink(
            invite_link=f"https://mocked-invite-link-to-{chat_id}-{uuid.uuid4()}",
            creator=self._get_me(),
            creates_join_request=bool(creates_join_request),
            is_primary=True,
            is_revoked=False,
            name=name,
            expire_date=date2int(expire_date),
            member_limit=member_limit,
            pending_join_request_count=0,
        )

    @mocked
    async def create_new_sticker_set(
        self,
        user_id: int,
        name: str,
        title: str,
        emojis: str,
        png_sticker: Union[Any, str] = None,
        tgs_sticker: Union[Any, str] = None,
        webm_sticker: Union[Any, str] = None,
        contains_masks: Optional[bool] = None,
        mask_position: Optional[types.MaskPosition] = None,
    ) -> bool:
        return True

    @mocked
    async def decline_chat_join_request(self, chat_id: Union[str, int], user_id: Union[int, str]) -> bool:
        return True

    @mocked
    async def delete_chat_photo(self, chat_id: Union[int, str]) -> bool:
        return True

    @mocked
    async def delete_chat_sticker_set(self, chat_id: Union[int, str]) -> bool:
        return True

    @mocked
    async def delete_message(self, chat_id: Union[int, str], message_id: int, timeout: Optional[int] = None) -> bool:
        return True

    @mocked
    async def delete_my_commands(
        self, scope: Optional[types.BotCommandScope] = None, language_code: Optional[int] = None
    ) -> bool:
        return True

    @mocked
    async def delete_sticker_from_set(self, sticker: str) -> bool:
        return True

    @mocked
    async def delete_webhook(
        self, drop_pending_updates: Optional[bool] = None, timeout: Optional[float] = None
    ) -> None:
        return None

    @mocked
    async def download_file(self, file_path: str) -> bytes:
        return b"mock downloaded file bytes"

    @mocked
    async def edit_chat_invite_link(
        self,
        chat_id: Union[int, str],
        invite_link: Optional[str] = None,
        name: Optional[str] = None,
        expire_date: Optional[Union[int, datetime]] = None,
        member_limit: Optional[int] = None,
        creates_join_request: Optional[bool] = None,
    ) -> types.ChatInviteLink:
        return types.ChatInviteLink(
            invite_link=f"https://mocked-invite-link-edited-from-{invite_link}",
            creator=self._get_me(),
            creates_join_request=bool(creates_join_request),
            is_primary=True,
            is_revoked=False,
            name=name,
            expire_date=date2int(expire_date),
            member_limit=member_limit,
            pending_join_request_count=0,
        )

    def _get_dummy_message(
        self,
        chat_id: Optional[Union[int, str]] = None,
        message_id: Optional[int] = None,
    ) -> types.Message:
        return types.Message(
            message_id=message_id or self._get_new_message_id(force_int_chat_id(chat_id)),
            from_user=dummy_message_author(chat_id, message_id),
            date=int((datetime.now() - timedelta(days=3)).timestamp()),
            chat=dummy_chat(chat_id),
            content_type="text",
            options={},
            json_string="",
        )

    @mocked
    async def edit_message_caption(
        self,
        caption: str,
        chat_id: Optional[Union[int, str]] = None,
        message_id: Optional[int] = None,
        inline_message_id: Optional[str] = None,
        parse_mode: Optional[str] = None,
        caption_entities: Optional[list[types.MessageEntity]] = None,
        reply_markup: Optional[types.ReplyMarkup] = None,
    ) -> Union[types.Message, bool]:
        """inline message editing is not supported by the mock"""
        msg = self._get_dummy_message(chat_id, message_id)
        msg.caption_entities = caption_entities
        if isinstance(reply_markup, types.InlineKeyboardMarkup):
            msg.reply_markup = reply_markup
        return msg

    @mocked
    async def edit_message_live_location(
        self,
        latitude: float,
        longitude: float,
        chat_id: Optional[Union[int, str]] = None,
        message_id: Optional[int] = None,
        inline_message_id: Optional[str] = None,
        reply_markup: Optional[types.ReplyMarkup] = None,
        timeout: Optional[int] = None,
        horizontal_accuracy: Optional[float] = None,
        heading: Optional[int] = None,
        proximity_alert_radius: Optional[int] = None,
    ) -> types.Message:
        msg = self._get_dummy_message(chat_id, message_id)
        if isinstance(reply_markup, types.InlineKeyboardMarkup):
            msg.reply_markup = reply_markup
        msg.location = types.Location(
            longitude,
            latitude,
            horizontal_accuracy=horizontal_accuracy,
            proximity_alert_radius=proximity_alert_radius,
            heading=heading,
        )
        return msg

    @mocked
    async def edit_message_reply_markup(
        self,
        chat_id: Optional[Union[int, str]] = None,
        message_id: Optional[int] = None,
        inline_message_id: Optional[str] = None,
        reply_markup: Optional[types.ReplyMarkup] = None,
    ) -> Union[types.Message, bool]:
        msg = self._get_dummy_message(chat_id, message_id)
        if isinstance(reply_markup, types.InlineKeyboardMarkup):
            msg.reply_markup = reply_markup
        return msg

    @mocked
    async def edit_message_text(
        self,
        text: str,
        chat_id: Optional[Union[int, str]] = None,
        message_id: Optional[int] = None,
        inline_message_id: Optional[str] = None,
        parse_mode: Optional[str] = None,
        entities: Optional[list[types.MessageEntity]] = None,
        disable_web_page_preview: Optional[bool] = None,
        reply_markup: Optional[types.ReplyMarkup] = None,
    ) -> Union[types.Message, bool]:
        msg = self._get_dummy_message(chat_id, message_id)
        msg.text = text
        msg.entities = entities
        if isinstance(reply_markup, types.InlineKeyboardMarkup):
            msg.reply_markup = reply_markup
        return msg

    @mocked
    async def export_chat_invite_link(self, chat_id: Union[int, str]) -> str:
        return f"https://new-invite-link-to-{chat_id}"

    @mocked
    async def forward_message(
        self,
        chat_id: Union[int, str],
        from_chat_id: Union[int, str],
        message_id: int,
        disable_notification: Optional[bool] = None,
        protect_content: Optional[bool] = None,
        timeout: Optional[int] = None,
    ) -> types.Message:
        msg = self._get_dummy_message(chat_id)
        msg.forward_from_chat = dummy_chat(from_chat_id)
        msg.forward_from_message_id = message_id
        msg.forward_from = dummy_message_author(from_chat_id, message_id)
        msg.forward_date = int((datetime.now() - timedelta(days=5)).timestamp())
        return msg

    @mocked
    async def get_chat(self, chat_id: Union[int, str]) -> types.Chat:
        return dummy_chat(chat_id)

    @mocked
    async def get_chat_administrators(self, chat_id: Union[int, str]) -> list[types.ChatMember]:
        return [
            types.ChatMemberOwner(
                user=types.User(id=10, is_bot=False, first_name="Real", last_name="Person"),
                status="creator",
            ),
            types.ChatMemberAdministrator(
                user=types.User(id=20, is_bot=True, first_name="Bot"),
                status="administrator",
            ),
        ]

    @mocked
    async def get_chat_member(self, chat_id: Union[int, str], user_id: int) -> types.ChatMember:
        return types.ChatMember(
            user=types.User(id=user_id, is_bot=False, first_name="Real", last_name="Person"),
            status="member",
        )

    @mocked
    async def get_chat_member_count(self, chat_id: Union[int, str]) -> int:
        return 15

    @mocked
    async def get_file(self, file_id: str) -> types.File:
        return types.File(
            file_id=file_id,
            file_unique_id="22222222222",
            file_size=1024,
            file_path="never-gonna-give-you-up.mp4",
        )

    @mocked
    async def get_file_url(self, file_id: str) -> str:
        return f"https://api.telegram.org/file/bot{self.token}/never-gonna-give-you-up.mp4"

    @mocked
    async def get_sticker_set(self, name: str) -> types.StickerSet:
        return types.StickerSet(
            name=name,
            title=f"Mocked sticker set {name}",
            is_animated=False,
            is_video=False,
            contains_masks=False,
            stickers=[
                types.Sticker(
                    file_id=str(hash(emoji)),
                    file_unique_id=str(hash(emoji)),
                    width=640,
                    height=640,
                    is_animated=False,
                    is_video=False,
                    emoji=emoji,
                    set_name=name,
                )
                for emoji in ["❤️", "✨", "🏳️‍🌈"]
            ],
        )

    @mocked
    async def get_user_profile_photos(
        self, user_id: int, offset: Optional[int] = None, limit: Optional[int] = None
    ) -> types.UserProfilePhotos:
        return types.UserProfilePhotos(
            total_count=2,
            photos=[
                [types.PhotoSize(file_id="alsdfj", file_unique_id="kjhkajdfhka", width=1200, height=1200)],
                [types.PhotoSize(file_id="aksjhflkajdf", file_unique_id="askljdhflkajdshf", width=1200, height=1200)],
            ],
        )

    @mocked
    async def get_webhook_info(self, timeout=None) -> types.WebhookInfo:
        return types.WebhookInfo(
            url=f"https://webhook-url-for-{self.token}",
            has_custom_certificate=False,
            pending_update_count=0,
        )

    @mocked
    async def leave_chat(self, chat_id: Union[int, str]) -> bool:
        return True

    @mocked
    async def pin_chat_message(
        self, chat_id: Union[int, str], message_id: int, disable_notification: Optional[bool] = False
    ) -> bool:
        return True

    @mocked
    async def promote_chat_member(
        self,
        chat_id: Union[int, str],
        user_id: int,
        can_change_info: Optional[bool] = None,
        can_post_messages: Optional[bool] = None,
        can_edit_messages: Optional[bool] = None,
        can_delete_messages: Optional[bool] = None,
        can_invite_users: Optional[bool] = None,
        can_restrict_members: Optional[bool] = None,
        can_pin_messages: Optional[bool] = None,
        can_promote_members: Optional[bool] = None,
        is_anonymous: Optional[bool] = None,
        can_manage_chat: Optional[bool] = None,
        can_manage_video_chats: Optional[bool] = None,
    ) -> bool:
        return True

    @mocked
    async def restrict_chat_member(
        self,
        chat_id: Union[int, str],
        user_id: int,
        until_date: Optional[Union[int, datetime]] = None,
        can_send_messages: Optional[bool] = None,
        can_send_media_messages: Optional[bool] = None,
        can_send_polls: Optional[bool] = None,
        can_send_other_messages: Optional[bool] = None,
        can_add_web_page_previews: Optional[bool] = None,
        can_change_info: Optional[bool] = None,
        can_invite_users: Optional[bool] = None,
        can_pin_messages: Optional[bool] = None,
    ) -> bool:
        return True

    @mocked
    async def revoke_chat_invite_link(self, chat_id: Union[int, str], invite_link: str) -> types.ChatInviteLink:
        return types.ChatInviteLink(
            invite_link=invite_link,
            creator=self._get_me(),
            creates_join_request=False,
            is_primary=True,
            is_revoked=True,
        )

    def _enrich_message_fields(
        self,
        m: types.Message,
        caption: Optional[str] = None,
        caption_entities: Optional[list[types.MessageEntity]] = None,
        protect_content: Optional[bool] = None,
        reply_to_message_id: Optional[int] = None,
        reply_markup: Optional[types.ReplyMarkup] = None,
    ) -> None:
        m.caption = caption
        m.caption_entities = caption_entities
        m.has_protected_content = bool(protect_content)
        if isinstance(reply_markup, types.InlineKeyboardMarkup):
            m.reply_markup = reply_markup
        if reply_to_message_id:
            m.reply_to_message = self._get_dummy_message(m.chat.id, reply_to_message_id)

    @mocked
    async def send_animation(
        self,
        chat_id: Union[int, str],
        animation: Union[Any, str],
        duration: Optional[int] = None,
        width: Optional[int] = None,
        height: Optional[int] = None,
        thumb: Optional[Union[Any, str]] = None,
        caption: Optional[str] = None,
        parse_mode: Optional[str] = None,
        caption_entities: Optional[list[types.MessageEntity]] = None,
        disable_notification: Optional[bool] = None,
        protect_content: Optional[bool] = None,
        reply_to_message_id: Optional[int] = None,
        allow_sending_without_reply: Optional[bool] = None,
        reply_markup: Optional[types.ReplyMarkup] = None,
        timeout: Optional[int] = None,
    ) -> types.Message:
        msg = self._get_dummy_message(chat_id)
        msg.animation = types.Animation(
            file_id="dkjahflksdjfh",
            file_unique_id="kjahdsflkjahsdf",
            width=width,
            height=height,
            duration=duration,
            thumb=thumb,
        )
        self._enrich_message_fields(msg, caption, caption_entities, protect_content, reply_to_message_id, reply_markup)
        return msg

    @mocked
    async def send_audio(
        self,
        chat_id: Union[int, str],
        audio: Union[Any, str],
        caption: Optional[str] = None,
        duration: Optional[int] = None,
        performer: Optional[str] = None,
        title: Optional[str] = None,
        reply_to_message_id: Optional[int] = None,
        reply_markup: Optional[types.ReplyMarkup] = None,
        parse_mode: Optional[str] = None,
        disable_notification: Optional[bool] = None,
        timeout: Optional[int] = None,
        thumb: Optional[Union[Any, str]] = None,
        caption_entities: Optional[list[types.MessageEntity]] = None,
        allow_sending_without_reply: Optional[bool] = None,
        protect_content: Optional[bool] = None,
    ) -> types.Message:
        msg = self._get_dummy_message(chat_id)
        msg.audio = types.Audio(
            file_id="LKDfhjklajsdhflkajsdhflkajsdhf",
            file_unique_id="lakhdflkjahdslkfjadfb",
            duration=duration,
            performer=performer,
            title=title,
            thumb=thumb,
        )
        self._enrich_message_fields(msg, caption, caption_entities, protect_content, reply_to_message_id, reply_markup)
        return msg

    @mocked
    async def send_chat_action(self, chat_id: Union[int, str], action: str, timeout: Optional[int] = None) -> bool:
        return True

    @mocked
    async def send_contact(
        self,
        chat_id: Union[int, str],
        phone_number: str,
        first_name: str,
        last_name: Optional[str] = None,
        vcard: Optional[str] = None,
        disable_notification: Optional[bool] = None,
        reply_to_message_id: Optional[int] = None,
        reply_markup: Optional[types.ReplyMarkup] = None,
        timeout: Optional[int] = None,
        allow_sending_without_reply: Optional[bool] = None,
        protect_content: Optional[bool] = None,
    ) -> types.Message:
        msg = self._get_dummy_message(chat_id)
        msg.contact = types.Contact(
            phone_number=phone_number,
            first_name=first_name,
            last_name=last_name,
            vcard=vcard,
        )
        self._enrich_message_fields(
            msg, reply_markup=reply_markup, reply_to_message_id=reply_to_message_id, protect_content=protect_content
        )
        return msg

    @mocked
    async def send_dice(
        self,
        chat_id: Union[int, str],
        emoji: Optional[str] = None,
        disable_notification: Optional[bool] = None,
        reply_to_message_id: Optional[int] = None,
        reply_markup: Optional[types.ReplyMarkup] = None,
        timeout: Optional[int] = None,
        allow_sending_without_reply: Optional[bool] = None,
        protect_content: Optional[bool] = None,
    ) -> types.Message:
        msg = self._get_dummy_message(chat_id)
        msg.dice = types.Dice(value=1, emoji=emoji)
        self._enrich_message_fields(
            msg, reply_to_message_id=reply_to_message_id, reply_markup=reply_markup, protect_content=protect_content
        )
        return msg

    @mocked
    async def send_document(
        self,
        chat_id: Union[int, str],
        document: Union[Any, str],
        reply_to_message_id: Optional[int] = None,
        caption: Optional[str] = None,
        reply_markup: Optional[types.ReplyMarkup] = None,
        parse_mode: Optional[str] = None,
        disable_notification: Optional[bool] = None,
        timeout: Optional[int] = None,
        thumb: Optional[Union[Any, str]] = None,
        caption_entities: Optional[list[types.MessageEntity]] = None,
        allow_sending_without_reply: Optional[bool] = None,
        visible_file_name: Optional[str] = None,
        disable_content_type_detection: Optional[bool] = None,
        data: Optional[Union[Any, str]] = None,
        protect_content: Optional[bool] = None,
    ) -> types.Message:
        msg = self._get_dummy_message(chat_id)
        msg.document = types.Document(
            file_id="JDHFKJHDF:ASDKJ",
            file_unique_id="LKJHDiuhfdlkajsdhfpOIUH",
            thumb=thumb,
            file_name=visible_file_name,
        )
        self._enrich_message_fields(msg, caption, caption_entities, protect_content, reply_to_message_id, reply_markup)
        return msg

    @mocked
    async def send_location(
        self,
        chat_id: Union[int, str],
        latitude: float,
        longitude: float,
        live_period: Optional[int] = None,
        reply_to_message_id: Optional[int] = None,
        reply_markup: Optional[types.ReplyMarkup] = None,
        disable_notification: Optional[bool] = None,
        timeout: Optional[int] = None,
        horizontal_accuracy: Optional[float] = None,
        heading: Optional[int] = None,
        proximity_alert_radius: Optional[int] = None,
        allow_sending_without_reply: Optional[bool] = None,
        protect_content: Optional[bool] = None,
    ) -> types.Message:
        msg = self._get_dummy_message(chat_id)
        msg.location = types.Location(
            longitude=longitude,
            latitude=latitude,
            horizontal_accuracy=horizontal_accuracy,
            heading=heading,
            proximity_alert_radius=proximity_alert_radius,
        )
        self._enrich_message_fields(
            msg, protect_content=protect_content, reply_to_message_id=reply_to_message_id, reply_markup=reply_markup
        )
        return msg

    @mocked
    async def send_message(
        self,
        chat_id: Union[int, str],
        text: str,
        parse_mode: Optional[str] = None,
        entities: Optional[list[types.MessageEntity]] = None,
        disable_web_page_preview: Optional[bool] = None,
        disable_notification: Optional[bool] = None,
        protect_content: Optional[bool] = None,
        reply_to_message_id: Optional[int] = None,
        allow_sending_without_reply: Optional[bool] = None,
        reply_markup: Optional[types.ReplyMarkup] = None,
        timeout: Optional[int] = None,
    ) -> types.Message:
        msg = self._get_dummy_message(chat_id)
        msg.from_user = self._get_me()
        msg.text = text
        msg.entities = entities
        self._enrich_message_fields(
            msg, protect_content=protect_content, reply_to_message_id=reply_to_message_id, reply_markup=reply_markup
        )
        return msg

    @mocked
    async def send_media_group(
        self,
        chat_id: Union[int, str],
        media: list[
            Union[
                types.InputMediaAudio,
                types.InputMediaDocument,
                types.InputMediaPhoto,
                types.InputMediaVideo,
            ]
        ],
        disable_notification: Optional[bool] = None,
        protect_content: Optional[bool] = None,
        reply_to_message_id: Optional[int] = None,
        timeout: Optional[int] = None,
        allow_sending_without_reply: Optional[bool] = None,
    ) -> list[types.Message]:
        msgs: list[types.Message] = []
        for media_item in media:
            msg = self._get_dummy_message(chat_id)
            if isinstance(media_item, types.InputMediaAudio):
                msg.audio = types.Audio(
                    file_id=str(hash(media_item.media)),
                    file_unique_id=str(1 + hash(media_item.media)),
                    duration=media_item.duration,
                    performer=media_item.performer,
                    title=media_item.title,
                )
            elif isinstance(media_item, types.InputMediaDocument):
                msg.document = types.Document(
                    file_id=str(hash(media_item.media)),
                    file_unique_id=str(1 + hash(media_item.media)),
                )
            elif isinstance(media_item, types.InputMediaPhoto):
                msg.photo = [
                    types.PhotoSize(
                        file_id=str(hash(media_item.media)),
                        file_unique_id=str(1 + hash(media_item.media)),
                        width=320,
                        height=240,
                    )
                ]
            elif isinstance(media_item, types.InputMediaVideo):
                msg.video = types.Video(
                    file_id=str(hash(media_item.media)),
                    file_unique_id=str(1 + hash(media_item.media)),
                    width=media_item.width,
                    height=media_item.height,
                    duration=media_item.duration,
                    thumb=media_item.thumb,
                )
            self._enrich_message_fields(msg, protect_content=protect_content, reply_to_message_id=reply_to_message_id)
            msgs.append(msg)
        return msgs

    @mocked
    async def set_webhook(
        self,
        url: str,
        certificate: Optional[api.FileObject] = None,
        max_connections: Optional[int] = None,
        ip_address: Optional[str] = None,
        drop_pending_updates: Optional[bool] = None,
        timeout: Optional[float] = None,
    ):
        return True


def date2int(d: Union[None, int, datetime]) -> Optional[int]:
    if d is None:
        return None
    elif isinstance(d, int):
        return d
    else:
        return int(d.timestamp())


def force_int_chat_id(chat_id: Union[int, str, None]) -> int:
    if not isinstance(chat_id, int):
        return 1312
    else:
        return chat_id


def infer_chat_type(chat_id: Union[int, str, None]) -> str:
    if isinstance(chat_id, int):
        return "private"  # no way to infer "group" or "supergroup", so whatever
    else:
        return "channel"


def dummy_chat(chat_id: Union[int, str, None]) -> types.Chat:
    return types.Chat(id=force_int_chat_id(chat_id), type=infer_chat_type(chat_id))


def dummy_message_author(chat_id: Union[int, str, None], message_id: Union[int, None]) -> types.User:
    return types.User(
        id=abs(hash(message_id) + hash(chat_id)) % 100_000,
        is_bot=False,
        first_name="John",
        last_name="Doe",
        username="johndoe",
    )
