import asyncio

from discord import Client, Intents, User
from discord.errors import NotFound
from typing import Optional

from ..log import Logger

logger = Logger.GENERIC_CHECKS


async def check_token(token: str, user_id: int) -> tuple[bool, Optional[User]]:
    logger.info(f"Checking user ID {user_id}")
    
    dummy = Client(intents=Intents.default())
    check_result = asyncio.Event()
    data = (False, None)
    
    @dummy.event
    async def on_ready() -> None:
        nonlocal data
        
        try:
            user = await dummy.fetch_user(user_id)
            data = (True, user)
            
            logger.info(f"Nice to meet you, {user.display_name}!")
        
        except NotFound:
            pass
        
        finally:
            await dummy.close()
            check_result.set()
    
    await dummy.start(token)
    await check_result.wait()
    
    return data