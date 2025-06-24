import inspect

from discord import (
    Interaction,
    Guild,
    Member,
    User,
    Forbidden,
    NotFound
)

from discord import (
    ForumChannel,
    TextChannel,
    CategoryChannel,
    StageChannel,
    VoiceChannel
)

from discord.abc import PrivateChannel
from discord.threads import Thread
from discord.app_commands import Command
from typing import Optional, Union, TYPE_CHECKING
from logging import Logger as LoggingLogger
from functools import wraps

from .managers.locale import (
    get_interaction_locale,
    get_localised_string
)

from .log import Logger, log_exception

if TYPE_CHECKING:
    from .client import Client

util_logger = Logger.UTILS


def get_full_command(interaction: Interaction) -> str:
    locale = get_interaction_locale(interaction)
    command = interaction.command
    
    if not command:
        return "unknown_command"

    command_name = get_localised_string(locale, command.name)
    
    if isinstance(command, Command):
        if command.parent:
            command_group = get_localised_string(locale, command.parent.name)
            command_name = f"/{command_group} {command_name}"
    
    return command_name


async def get_guild(client: "Client", guild_id: int) -> Optional[Guild]:
    try:
        guild = client.get_guild(guild_id)
        
        if not guild:
            guild = await client.fetch_guild(guild_id)
        
        return guild
    
    except (Forbidden, NotFound):
        return None


async def get_member(client: "Client", guild: Guild | int, member_id: int) -> Optional[Member]:
    try:
        if isinstance(guild, int):
            guild_obj = await get_guild(client, guild)
        else:
            guild_obj = guild
        
        if not guild_obj:
            util_logger.error(f"Failed to fetch member {member_id}, guild is None")
            return None
        
        member = guild_obj.get_member(member_id)
        
        if not member:
            member = await guild_obj.fetch_member(member_id)
        
        return member if member else None
    
    except (Forbidden, NotFound):
        return None


async def get_user(client: "Client", user_id: int) -> Optional[User]:
    try:
        user = client.get_user(user_id)
        
        if not user:
            user = await client.fetch_user(user_id)
        
        return user if user else None
    
    except (Forbidden, NotFound):
        return None


async def get_user_avatar(user: User | Member, as_bytes: bool = False) -> str | bytes:
    if as_bytes:
        return await user.avatar.read() if user.avatar else await user.default_avatar.read()
    else:
        return user.avatar.url if user.avatar else user.default_avatar.url


async def get_channel(
        client: "Client",
        channel_id: int
) -> Optional[
        Thread |
        PrivateChannel | 
        Union[
            ForumChannel,
            TextChannel,
            CategoryChannel,
            StageChannel,
            VoiceChannel
        ]
    ]:
    
    try:
        channel = client.get_channel(channel_id)
        
        if not channel:
            channel = await client.fetch_channel(channel_id)
        
        return channel if channel else None
    
    except (Forbidden, NotFound):
        return None


def log_errors(logger: LoggingLogger):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                log_exception(e, logger)
                return None
        
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                log_exception(e, logger)
                return None
        
        if inspect.iscoroutinefunction(func):
            return async_wrapper
        return wrapper
    
    return decorator