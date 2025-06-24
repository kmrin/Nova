import os
import yaml

from typing import Optional
from pydantic import BaseModel, Field

from .paths import Path

testing_servers = str(os.getenv("TESTING_SERVERS", "")).split(",")


class _Status(BaseModel):
    language: str
    interval: int
    log: bool


class _SpamFilter(BaseModel):
    enabled: bool
    time_window: int
    max_per_window: int


class _Danbooru(BaseModel):
    enabled: bool
    api_key: Optional[str] = None


class _Rule34(BaseModel):
    enabled: bool
    api_key: Optional[str] = None


class _E621(BaseModel):
    enabled: bool
    api_key: Optional[str] = None


class _NSFWExtensions(BaseModel):
    danbooru: _Danbooru
    rule34: _Rule34
    e621: _E621


class _Lavalink(BaseModel):
    host: str
    port: int
    password: str


class Config(BaseModel):
    version: str
    debug: bool
    forward_discord_logs: bool
    always_sync: bool
    status: _Status
    spam_filter: _SpamFilter = Field(alias="spam-filter")
    nsfw_extensions: _NSFWExtensions = Field(alias="nsfw-extensions")
    lavalink: _Lavalink
    testing_servers: Optional[list[int]] = Field(alias="testing-servers", default_factory=list)
    tasks: list[str]
    internal_extensions: list[str] = Field(alias="internal-extensions")
    intents: dict[str, bool]


def load_config() -> Config:
    try:
        with open(Path.CONFIG, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)

            if not data:
                raise ValueError("Config file is empty or invalid")

            config = Config.model_validate(data)
            config.testing_servers = [int(server) for server in testing_servers]
            
            return config

    except FileNotFoundError:
        raise FileNotFoundError(f"Configuration file not found at {Path.CONFIG.value}")

    except yaml.YAMLError as e:
        raise ValueError(f"Error parsing YAML configuration: {e}")

    except Exception as e:
        raise ValueError(f"Error loading configuration: {e}")


conf = load_config()