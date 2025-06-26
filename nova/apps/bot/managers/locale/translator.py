import os

from discord import Locale
from typing import Optional

from discord.app_commands import (
    locale_str,
    Translator as DCTranslator,
    TranslationContextTypes
)

from .manager import get_localised_string

from ...paths import Path

SUPPORTED_LOCALES = os.listdir(Path.LOCALE)


class Translator(DCTranslator):
    async def translate(
            self,
            string: locale_str | str,
            locale: Locale,
            context: TranslationContextTypes | None = None,
    ) -> str:
        if isinstance(string, locale_str):
            msg = string.message
        else:
            msg = string
        
        if not msg:
            return ""
        
        if (locale == Locale.american_english) or (locale.value not in SUPPORTED_LOCALES):
            locale = Locale.british_english
        
        return get_localised_string(locale.value, msg, default=msg)