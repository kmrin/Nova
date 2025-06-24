import os

from discord import Interaction, Locale
from dataclasses import fields
from typing import Optional

from ..files.yaml import read

from ...objects import Localisation
from ...log import Logger
from ...paths import Path

logger = Logger.LOCALE
locale_class = Localisation

SECTIONS = [field.name for field in fields(locale_class)]
CHECKED: dict[str, bool] = {}
INVALID_REPORTED_KEYS: dict[str, list[str]] = {}


def check_sections(locale_file: str, locale_data: dict) -> bool:
    for section in SECTIONS:
        if section not in locale_data:
            logger.error(f"Section '{section}' is missing from '{locale_file}'")
            return False
        
        if not isinstance(locale_data[section], dict):
            logger.error(f"Section '{section}' is not a dictionary in '{locale_file}'")
            return False
        
    if locale_file not in CHECKED:
        logger.debug(f"Locale file '{locale_file}' is valid")
    
    CHECKED[locale_file] = True
    
    return True


def get_locale(locale: str | Locale) -> Optional[Localisation]:
    base_locale_path = os.path.join(Path.LOCALE, f"{locale}.yml")
    
    if not os.path.exists(base_locale_path):
        logger.error(f"Locale file at '{base_locale_path}' doesn't exist")
        return None
    
    locale_data = read(base_locale_path, silent=True)
    
    if locale_data is None or not isinstance(locale_data, dict) or not locale_data:
        logger.error(f"Locale file at '{base_locale_path}' is empty, invalid or doesn't exist")
        return None
    
    if not check_sections(base_locale_path, locale_data):
        logger.error(f"Locale file at '{base_locale_path}' is invalid, section check failed")
        return None
    
    return Localisation(**locale_data)


def get_interaction_locale(interaction: Interaction) -> str:
    locale = interaction.locale if interaction.locale else Locale.british_english
    
    if locale == Locale.american_english:
        locale = Locale.british_english
    
    return locale.value


def get_localised_string(locale: str | Locale, key: str, default: str = "", *args, **kwargs) -> str:
    if isinstance(locale, tuple):
        locale = locale[0]
    
    text_data = get_locale(locale)
    
    if not text_data:
        logger.error(f"Locale code '{locale}' not present in locale list, defaulting to 'en_GB'")
        text_data = get_locale(Locale.british_english.value)
        
        if not text_data:
            logger.error(f"Failed to load default locale, returning default")
            return default
    
    all_text = text_data.all()
    value = all_text.get(key, None)
    
    if not value:
        logger.error(f"Key '{key}' not present in locale data, returning default")
        return default
    
    if not isinstance(value, str):
        logger.error(f"Key '{key}' is not a string in locale data, returning default")
        return default
    
    return value.format(*args, **kwargs)


def get_localised_list(locale: str | Locale, key: str, default: list[str] = []) -> list[str]:
    if isinstance(locale, tuple):
        locale = locale[0]
    
    text_data = get_locale(locale)
    
    if not text_data:
        logger.error(f"Locale code '{locale}' not present in locale list, defaulting to 'en_GB'")
        text_data = get_locale(Locale.british_english.value)
        
        if not text_data:
            logger.error(f"Failed to load default locale, returning default")
            return default
    
    all_text = text_data.all()
    value = all_text.get(key, None)
    
    if not value:
        logger.error(f"Key '{key}' not present in locale data, returning default")
        return default
    
    if not isinstance(value, list):
        logger.error(f"Key '{key}' is not a list in locale data, returning default")
        return default
    
    return value