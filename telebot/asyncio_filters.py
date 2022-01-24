from abc import ABC

class SimpleCustomFilter(ABC):
    """
    Simple Custom Filter base class.
    Create child class with check() method.
    Accepts only message, returns bool value, that is compared with given in handler.
    """

    async def check(self, message):
        """
        Perform a check.
        """
        pass


class AdvancedCustomFilter(ABC):
    """
    Simple Custom Filter base class.
    Create child class with check() method.
    Accepts two parameters, returns bool: True - filter passed, False - filter failed.
    message: Message class
    text: Filter value given in handler
    """

    async def check(self, message, text):
        """
        Perform a check.
        """
        pass


class TextMatchFilter(AdvancedCustomFilter):
    """
    Filter to check Text message.
    key: text

    Example:
    @bot.message_handler(text=['account'])
    """

    key = 'text'

    async def check(self, message, text):
        if type(text) is list:return message.text in text
        else: return text == message.text

class TextContainsFilter(AdvancedCustomFilter):
    """
    Filter to check Text message.
    key: text

    Example:
    # Will respond if any message.text contains word 'account'
    @bot.message_handler(text_contains=['account'])
    """

    key = 'text_contains'

    async def check(self, message, text):
        return text in message.text

class TextStartsFilter(AdvancedCustomFilter):
    """
    Filter to check whether message starts with some text.

    Example:
    # Will work if message.text starts with 'Sir'.
    @bot.message_handler(text_startswith='Sir')
    """

    key = 'text_startswith'
    async def check(self, message, text):
        return message.text.startswith(text) 

class ChatFilter(AdvancedCustomFilter):
    """
    Check whether chat_id corresponds to given chat_id.

    Example:
    @bot.message_handler(chat_id=[99999])
    """

    key = 'chat_id'
    async def check(self, message, text):
        return message.chat.id in text

class ForwardFilter(SimpleCustomFilter):
    """
    Check whether message was forwarded from channel or group.

    Example:

    @bot.message_handler(is_forwarded=True)
    """

    key = 'is_forwarded'

    async def check(self, message):
        return message.forward_from_chat is not None

class IsReplyFilter(SimpleCustomFilter):
    """
    Check whether message is a reply.

    Example:

    @bot.message_handler(is_reply=True)
    """

    key = 'is_reply'

    async def check(self, message):
        return message.reply_to_message is not None



class LanguageFilter(AdvancedCustomFilter):
    """
    Check users language_code.

    Example:

    @bot.message_handler(language_code=['ru'])
    """

    key = 'language_code'

    async def check(self, message, text):
        if type(text) is list:return message.from_user.language_code in text
        else: return message.from_user.language_code == text

class IsAdminFilter(SimpleCustomFilter):
    """
    Check whether the user is administrator / owner of the chat.

    Example:
    @bot.message_handler(chat_types=['supergroup'], is_chat_admin=True)
    """

    key = 'is_chat_admin'

    def __init__(self, bot):
        self._bot = bot

    async def check(self, message):
        result = await self._bot.get_chat_member(message.chat.id, message.from_user.id)
        return result.status in ['creator', 'administrator']

class StateFilter(AdvancedCustomFilter):
    """
    Filter to check state.

    Example:
    @bot.message_handler(state=1)
    """
    def __init__(self, bot):
        self.bot = bot
    key = 'state'

    async def check(self, message, text):
        if text == '*': return True
        if message.chat.type == 'group':
            group_state = await self.bot.current_states.get_state(message.chat.id, message.from_user.id)
            if group_state == text:
                return True
            elif group_state in text and type(text) is list:
                return True
            
            
        else:
            user_state = await self.bot.current_states.get_state(message.chat.id,message.from_user.id)
            if user_state == text:
                return True
            elif type(text) is list and user_state in text:
                return True

class IsDigitFilter(SimpleCustomFilter):
    """
    Filter to check whether the string is made up of only digits.

    Example:
    @bot.message_handler(is_digit=True)
    """
    key = 'is_digit'

    async def check(self, message):
        return message.text.isdigit()
