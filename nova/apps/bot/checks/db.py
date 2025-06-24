from typing import TYPE_CHECKING

from ..utils import log_errors
from ..log import Logger

from ..models import (
    Guilds,
    Users,
    UserConfig,
    GuildConfig
)

if TYPE_CHECKING:
    from ..client import Client

logger = Logger.DB


class DBManager:
    def __init__(self, client: "Client") -> None:
        self.client = client
    
    @log_errors(logger)
    async def populate_database(self) -> None:
        logger.info("Populating database")

        async for guild in self.client.fetch_guilds():
            try:
                db_guild = await Guilds.objects.aget(guild_id=guild.id)
                
                db_guild.guild_name = guild.name
                db_guild.guild_icon_url = guild.icon.url if guild.icon else ""
                
                await db_guild.asave()
                
                logger.debug(f"Updated: {guild.name} ({guild.id})")
            
            except Guilds.DoesNotExist:
                guild_config = await GuildConfig.objects.acreate()
                db_guild = await Guilds.objects.acreate(
                    guild_id=guild.id,
                    guild_name=guild.name,
                    guild_icon_url=guild.icon.url if guild.icon else "",
                    config=guild_config
                )
                
                logger.info(f"Added missing: {guild.name} ({guild.id})")
            
            async for member in guild.fetch_members(limit=None):
                try:
                    db_member = await Users.objects.aget(user_id=member.id)
                    
                    db_member.user_name = member.name
                    db_member.global_name = member.global_name
                    db_member.avatar_url = member.avatar.url if member.avatar else ""
                    
                    await db_member.asave()
                    
                    logger.debug(f"Updated: {member.name} ({member.id})")
                
                except Users.DoesNotExist:
                    user_config = await UserConfig.objects.acreate()
                    db_member = await Users.objects.acreate(
                        user_id=member.id,
                        user_name=member.name,
                        global_name=member.global_name,
                        avatar_url=member.avatar.url if member.avatar else "",
                        config=user_config
                    )
                    
                    logger.info(f"Added missing: {member.name} ({member.id})")
                
                if not await db_guild.users.filter(user_id=db_member.user_id).aexists():
                    await db_guild.users.aadd(db_member)
    
    @log_errors(logger)
    async def purge_database(self) -> None:
        logger.info("Purging database")
        
        current_guild_ids = [g.id for g in self.client.guilds]
        current_user_ids = [u.id for u in self.client.users]
        
        async for guild in Guilds.objects.all():
            if guild.guild_id not in current_guild_ids:
                logger.info(f"Guild '{guild.guild_name}' ({guild.guild_id}) no longer exists or bot is no longer in it")
                await guild.adelete()
        
        async for user in Users.objects.all():
            if user.user_id not in current_user_ids:
                logger.info(f"User '{user.user_name}' ({user.user_id}) is no longer visible to the bot")
                await user.adelete()