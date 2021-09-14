from abc import ABC

class SimpleCustomFilter(ABC):
    """
    Simple Custom Filter base class.
    Create child class with check() method.
    Accepts only message, returns bool value, that is compared with given in handler.
    """

    def check(self, message):
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

    def check(self, message, text):
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

    def check(self, message, text):
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

    def check(self, message, text):
        return text in message.text

class TextStartsFilter(AdvancedCustomFilter):
    """
    Filter to check whether message starts with some text.

    Example:
    # Will work if message.text starts with 'Sir'.
    @bot.message_handler(text_startswith='Sir')
    """

    key = 'text_startswith'
    def check(self, message, text):
        return message.text.startswith(text) 

class ChatFilter(AdvancedCustomFilter):
    """
    Check whether chat_id corresponds to given chat_id.

    Example:
    @bot.message_handler(chat_id=[99999])
    """

    key = 'chat_id'
    def check(self, message, text):
        return message.chat.id in text

class ForwardFilter(SimpleCustomFilter):
    """
    Check whether message was forwarded from channel or group.

    Example:

    @bot.message_handler(is_forwarded=True)
    """

    key = 'is_forwarded'

    def check(self, message):
        return message.forward_from_chat is not None

class IsReplyFilter(SimpleCustomFilter):
    """
    Check whether message is a reply.

    Example:

    @bot.message_handler(is_reply=True)
    """

    key = 'is_reply'

    def check(self, message):
        return message.reply_to_message is not None



class LanguageFilter(AdvancedCustomFilter):
    """
    Check users language_code.

    Example:

    @bot.message_handler(language_code=['ru'])
    """

    key = 'language_code'

    def check(self, message, text):
        if type(text) is list:return message.from_user.language_code in text
        else: return message.from_user.language_code == text

