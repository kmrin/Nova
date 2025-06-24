import asyncio

from discord import Interaction, Embed, Colour, DMChannel
from discord.app_commands import CheckFailure

from .managers.locale import get_interaction_locale, get_localised_string
from .log import Logger
from .utils import get_full_command
from .responder import respond

logger = Logger.ERRORS


class NovaError(Exception):
    ...


class NovaBaseError(NovaError):
    def __init__(self, interaction: Interaction, *args, **kwargs) -> None:
        self.interaction = interaction
        
        self.locale = get_interaction_locale(interaction)
        self.command = get_full_command(interaction)
        self.author = interaction.user
        self.guild = interaction.guild if interaction.guild else None
        self.channel = interaction.channel if interaction.channel else None
                
        asyncio.create_task(self._do_action(*args, **kwargs))
    
    async def _do_action(self, *args, **kwargs) -> None:
        raise NotImplementedError


class UserNotOwner(NovaBaseError):
    async def _do_action(self, empty: bool = False) -> None:
        msg = get_localised_string(self.locale, "error_not_owner")
        empty_msg = get_localised_string(self.locale, "error_owners_empty")
        channel = "DMs" if isinstance(self.channel, DMChannel) else self.channel.name if self.channel else "Unknown"
        
        logger.warning(
            f"Someone tried running a command of class 'owner' but they're not on this class: " \
            f"[Command: {self.command} | Who: {self.author.display_name} " \
            f"| Where: {self.guild.name if self.guild else channel}]"
        )
        
        await respond(self.interaction, Colour.red(), msg, hidden=True)
        
        if empty:
            await respond(self.interaction, Colour.red(), empty_msg, hidden=True)


class UserNotAdmin(NovaBaseError):
    async def _do_action(self) -> None:
        msg = get_localised_string(self.locale, "error_not_admin")
        
        logger.warning(
            f"Someone tried running a command of class 'admin' but they're not on this class: " \
            f"[Command: {self.command} | Who: {self.author.display_name} " \
            f"| Where: {self.guild.name if self.guild else self.channel}]"
        )
        
        await respond(self.interaction, Colour.red(), msg, hidden=True)


class UserBlacklisted(NovaBaseError):
    async def _do_action(self) -> None:
        msg = get_localised_string(self.locale, "error_blacklisted")
        
        logger.warning(
            f"Someone tried running a command of class 'blacklisted' but they're blacklisted: " \
            f"[Command: {self.command} | Who: {self.author.display_name} " \
            f"| Where: {self.guild.name if self.guild else self.channel}]"
        )
        
        await respond(self.interaction, Colour.red(), msg, hidden=True)


class UserNotInGuild(NovaBaseError):
    async def _do_action(self) -> None:
        msg = get_localised_string(self.locale, "error_not_in_guild")
        
        logger.warning(
            f"Someone tried running a command of class 'in_guild' but they're not in a guild: " \
            f"[Command: {self.command} | Who: {self.author.display_name} " \
            f"| Where: {self.channel}]"
        )
        
        await respond(self.interaction, Colour.red(), msg, hidden=True)
