import random

from discord.ext import tasks
from discord import CustomActivity, Status
from typing import TYPE_CHECKING

from ..locale import get_locale

from ...log import Logger
from ...conf import conf

if TYPE_CHECKING:
    from ...client import Client

logger = Logger.TASKS


class TaskList:
    def __init__(self, client: "Client") -> None:
        self.client = client
    
    @tasks.loop(minutes=conf.status.interval)
    async def status_loop(self) -> None:
        locale = conf.status.language
        text_data = get_locale(locale)
        
        if not text_data:
            logger.error(f"Locale '{locale}' not found, failed to fetch status messages")
            return
        
        if conf.debug:
            status = text_data.system.get("maintenance_status", "Couldn't fetch maintenance status")
            
            if isinstance(status, str):
                await self.client.change_presence(status=Status.dnd, activity=CustomActivity(name=status))
            
            return
        
        statuses = text_data.system.get("statuses", ["Couldn't fetch status messages"])
        status = random.choice(statuses)
        
        await self.client.change_presence(activity=CustomActivity(name=status))
        
        if conf.status.log:
            logger.info(f"Status changed to '{status}'")