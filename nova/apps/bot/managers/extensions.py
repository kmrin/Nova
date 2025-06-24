import os

from typing import TYPE_CHECKING

from ..log import Logger, log_exception
from ..paths import Path
from ..conf import conf

if TYPE_CHECKING:
    from ..client import Client

logger = Logger.LOADER


async def load_extensions(client: "Client") -> None:
    for file in os.listdir(Path.EXTENSIONS):
        if file.endswith(".py"):
            extension = file[:-3]
            
            try:
                await client.load_extension(f"apps.bot.extensions.{extension}")
            
            except Exception as e:
                logger.error(f"Failed to load extension {extension}")
                log_exception(e, logger)
                continue