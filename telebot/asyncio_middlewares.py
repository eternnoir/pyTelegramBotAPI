import contextvars

try:
    from babel.support import LazyProxy

    babel_imported = True
except ImportError:
    babel_imported = False

from telebot import util


class BaseMiddleware:
    """
    Base class for middleware.

    Your middlewares should be inherited from this class.
    """

    def __init__(self):
        pass

    async def pre_process(self, message, data):
        raise NotImplementedError

    async def post_process(self, message, data, exception):
        raise NotImplementedError


class I18N(BaseMiddleware):
    """
    This middleware provides high-level tool for internationalization
    It is based on gettext util.
    """

    context_lang = contextvars.ContextVar('language', default=None)

    def __init__(self, translations_path, domain_name: str):
        super().__init__()
        self.update_types = self.process_update_types()

        self.path = translations_path
        self.domain = domain_name
        self.translations = util.find_translations(self.path, self.domain)

    @property
    def available_translations(self):
        return list(self.translations)

    def gettext(self, text: str, lang: str = None):
        """
        Singular translations
        """

        if lang is None:
            lang = self.context_lang.get()

        if lang not in self.translations:
            return text

        translator = self.translations[lang]
        return translator.gettext(text)

    def ngettext(self, singular: str, plural: str, lang: str = None, n=1):
        """
        Plural translations
        """
        if lang is None:
            lang = self.context_lang.get()

        if lang not in self.translations:
            if n == 1:
                return singular
            return plural

        translator = self.translations[lang]
        return translator.ngettext(singular, plural, n)

    def lazy_gettext(self, text: str, lang: str = None):
        if not babel_imported:
            raise RuntimeError('babel module is not imported. Check that you installed it.')
        return LazyProxy(self.gettext, text, lang, enable_cache=False)

    def lazy_ngettext(self, singular: str, plural: str, lang: str = None, n=1):
        if not babel_imported:
            raise RuntimeError('babel module is not imported. Check that you installed it.')
        return LazyProxy(self.ngettext, singular, plural, lang, n, enable_cache=False)

    async def get_user_language(self, obj):
        """
        You need to override this method and return user language
        """
        raise NotImplementedError

    def process_update_types(self) -> list:
        """
        You need to override this method and return any update types which you want to be processed
        """
        raise NotImplementedError

    async def pre_process(self, message, data):
        """
        context language variable will be set each time when update from 'process_update_types' comes
        value is the result of 'get_user_language' method
        """
        self.context_lang.set(await self.get_user_language(obj=message))

    async def post_process(self, message, data, exception):
        pass
