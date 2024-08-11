"""
Contains classes for states and state groups.
"""

from telebot import types


class State:
    """
    Class representing a state.

    .. code-block:: python3

        class MyStates(StatesGroup):
            my_state = State() # returns my_state:State string.
    """

    def __init__(self) -> None:
        self.name: str = None
        self.group: StatesGroup = None

    def __str__(self) -> str:
        return f"<{self.name}>"


class StatesGroup:
    """
    Class representing common states.

    .. code-block:: python3

        class MyStates(StatesGroup):
            my_state = State() # returns my_state:State string.
    """

    def __init_subclass__(cls) -> None:
        state_list = []
        for name, value in cls.__dict__.items():
            if (
                not name.startswith("__")
                and not callable(value)
                and isinstance(value, State)
            ):
                # change value of that variable
                value.name = ":".join((cls.__name__, name))
                value.group = cls
                state_list.append(value)
        cls._state_list = state_list

    @classmethod
    def state_list(self):
        return self._state_list


def resolve_context(message, bot_id: int) -> tuple:
    # chat_id, user_id, business_connection_id, bot_id, message_thread_id

    # message, edited_message, channel_post, edited_channel_post, business_message, edited_business_message
    if isinstance(message, types.Message):
        return (
            message.chat.id,
            message.from_user.id,
            message.business_connection_id,
            bot_id,
            message.message_thread_id if message.is_topic_message else None,
        )
    elif isinstance(message, types.CallbackQuery):  # callback_query
        return (
            message.message.chat.id,
            message.from_user.id,
            message.message.business_connection_id,
            bot_id,
            (
                message.message.message_thread_id
                if message.message.is_topic_message
                else None
            ),
        )
    elif isinstance(message, types.BusinessConnection):  # business_connection
        return (message.user_chat_id, message.user.id, message.id, bot_id, None)
    elif isinstance(
        message, types.BusinessMessagesDeleted
    ):  # deleted_business_messages
        return (
            message.chat.id,
            message.chat.id,
            message.business_connection_id,
            bot_id,
            None,
        )
    elif isinstance(message, types.MessageReactionUpdated):  # message_reaction
        return (message.chat.id, message.user.id, None, bot_id, None)
    elif isinstance(
        message, types.MessageReactionCountUpdated
    ):  # message_reaction_count
        return (message.chat.id, None, None, bot_id, None)
    elif isinstance(message, types.InlineQuery):  # inline_query
        return (None, message.from_user.id, None, bot_id, None)
    elif isinstance(message, types.ChosenInlineResult):  # chosen_inline_result
        return (None, message.from_user.id, None, bot_id, None)
    elif isinstance(message, types.ShippingQuery):  # shipping_query
        return (None, message.from_user.id, None, bot_id, None)
    elif isinstance(message, types.PreCheckoutQuery):  # pre_checkout_query
        return (None, message.from_user.id, None, bot_id, None)
    elif isinstance(message, types.PollAnswer):  # poll_answer
        return (None, message.user.id, None, bot_id, None)
    elif isinstance(message, types.ChatMemberUpdated):  # chat_member # my_chat_member
        return (message.chat.id, message.from_user.id, None, bot_id, None)
    elif isinstance(message, types.ChatJoinRequest):  # chat_join_request
        return (message.chat.id, message.from_user.id, None, bot_id, None)
    elif isinstance(message, types.ChatBoostRemoved):  # removed_chat_boost
        return (
            message.chat.id,
            message.source.user.id if message.source else None,
            None,
            bot_id,
            None,
        )
    elif isinstance(message, types.ChatBoostUpdated):  # chat_boost
        return (
            message.chat.id,
            message.boost.source.user.id if message.boost.source else None,
            None,
            bot_id,
            None,
        )
    else:
        pass  # not yet supported :(
