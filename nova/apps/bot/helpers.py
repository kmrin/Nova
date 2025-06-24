import os
import re
import json
import pickle
import string
import random

from typing import Literal, Optional, Any
from discord import Colour, Intents
from discord.app_commands import Choice
from translate import Translator
from langdetect import detect

CHARS = string.ascii_letters + string.digits


# Checks
def is_hex_colour(value: str) -> bool:
    return bool(re.match(r"^#([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})$", value))


def is_serializable(obj: Any, method: Literal["json", "pickle"] = "json") -> bool:
    try:
        if method == "json":
            json.dumps(obj)
        elif method == "pickle":
            pickle.dumps(obj)
        return True
    
    except (TypeError, ValueError, OverflowError, pickle.PicklingError):
        return False


# Converters
def choice_to_bool(choice: Literal[0, 1] | Choice) -> bool:
    if isinstance(choice, Choice):
        return choice.value == 1
    
    return bool(choice)


def ms_to_string(ms: int) -> str:
    s = ms / 1000
    m = s /60
    h = m / 60
    
    return (
        f"{h:02d}:{m:02d}:{s:02d}"
        if h > 0 else
        f"{m:02d}:{s:02d}"
    )


def split_list(l: list, size: int) -> list[list]:
    return [l[i:i + size] for i in range(0, len(l), size)]


def text_to_chunks(text: str, size: int = 25) -> list[list[str]]:
    lines = text.split("\n")
    return [lines[i:i + size] for i in range(0, len(lines), size)]


def value_to_colour(value: str) -> Colour:
    return Colour.from_str(value)


# Formatters
def remove_newline_from_string_list(l: list[str]) -> list[str]:
    return [x.strip() for x in l]


def translate(text: str, to_lang: str, from_lang: Optional[str] = None) -> str:
    if not from_lang:
        from_lang = detect(text)
    
    translator = Translator(to_lang, from_lang)
    
    return translator.translate(text)


def filter_dict(d: dict, keys: list[str], reverse: bool = False) -> dict:
    if reverse:
        return {k: v for k, v in d.items() if k in keys}
    
    return {k: v for k, v in d.items() if k not in keys}


# Getters
def get_os_path(path: str, from_root: bool = False) -> str:
    if from_root:
        return os.path.realpath(path)
    
    return os.path.realpath(os.path.join(os.path.dirname(__file__), path))


# Generators
def gen_random_string(length: int) -> str:
    return "".join(random.choices(CHARS, k=length))


def generate_intents(intents_config: dict[str, bool]) -> Intents:
    intents = Intents.default()
    
    for intent, enabled in intents_config.items():
        setattr(intents, intent, enabled)
    
    return intents