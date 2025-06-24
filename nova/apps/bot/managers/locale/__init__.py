from .manager import (
    get_locale,
    get_interaction_locale,
    get_localised_string,
    get_localised_list
)

from .translator import Translator

LOCALE_MAPPING = {
    "en-US": "en",
    "en-GB": "en",
    "zh-CN": "zh",
    "zh-TW": "zh",
    "es-419": "es",
    "pt-BR": "pt",
    "es-ES": "es",
    "sv-SE": "sv"
}