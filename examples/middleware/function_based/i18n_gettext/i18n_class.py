import gettext
import os
import threading


class I18N:
    """
    This class provides high-level tool for internationalization
    It is based on gettext util.
    """

    context_lang = threading.local()

    def __init__(self, translations_path, domain_name: str):
        self.path = translations_path
        self.domain = domain_name
        self.translations = self.find_translations()

    @property
    def available_translations(self):
        return list(self.translations)

    def gettext(self, text: str, lang: str = None):
        """
        Singular translations
        """

        if lang is None:
            lang = self.context_lang.language

        if lang not in self.translations:
            return text

        translator = self.translations[lang]
        return translator.gettext(text)

    def ngettext(self, singular: str, plural: str, lang: str = None, n=1):
        """
        Plural translations
        """
        if lang is None:
            lang = self.context_lang.language

        if lang not in self.translations:
            if n == 1:
                return singular
            return plural

        translator = self.translations[lang]
        return translator.ngettext(singular, plural, n)


    def find_translations(self):
        """
        Looks for translations with passed 'domain' in passed 'path'
        """
        if not os.path.exists(self.path):
            raise RuntimeError(f"Translations directory by path: {self.path!r} was not found")

        result = {}

        for name in os.listdir(self.path):
            translations_path = os.path.join(self.path, name, 'LC_MESSAGES')

            if not os.path.isdir(translations_path):
                continue

            po_file = os.path.join(translations_path, self.domain + '.po')
            mo_file = po_file[:-2] + 'mo'

            if os.path.isfile(po_file) and not os.path.isfile(mo_file):
                raise FileNotFoundError(f"Translations for: {name!r} were not compiled!")

            with open(mo_file, 'rb') as file:
                result[name] = gettext.GNUTranslations(file)

        return result
