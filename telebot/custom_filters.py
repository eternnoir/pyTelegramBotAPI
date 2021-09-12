from telebot import util



class TextFilter(util.AdvancedCustomFilter):
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

class TextContains(util.AdvancedCustomFilter):
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

class UserFilter(util.AdvancedCustomFilter):
    """
    Check whether chat_id corresponds to given chat_id.

    Example:
    @bot.message_handler(chat_id=[99999])

    """

    key = 'chat_id'
    def check(self, message, text):
        return message.chat.id in text


class TextStarts(util.AdvancedCustomFilter):
    """
    Filter to check whether message starts with some text.

    Example:
    # Will work if message.text starts with 'Sir'.
    @bot.message_handler(text_startswith='Sir')

    """

    key = 'text_startswith'
    def check(self, message, text):
        return message.text.startswith(text) 
