import os
import json
import hashlib

from discord import Interaction, Colour
from discord.app_commands import MissingPermissions, BotMissingPermissions, Command, Group
from discord.app_commands.errors import AppCommandError, TransformerError
from typing import Optional, TYPE_CHECKING

from .managers.locale import get_interaction_locale, get_localised_string
from .log import Logger, log_exception
from .responder import respond
from .errors import NovaError
from .paths import Path
from .conf import conf
from .utils import get_guild

if TYPE_CHECKING:
    from .client import Client

logger = Logger.TREE


async def on_error(interaction: Interaction, error: AppCommandError) -> None:
    locale = get_interaction_locale(interaction)
    string = None
    
    if isinstance(error, MissingPermissions):
        key = "tree_missing_perms"
        perms = ", ".join(error.missing_permissions)
        string = get_localised_string(locale, key, perms=perms) if perms else get_localised_string(locale, key)
        
    elif isinstance(error, BotMissingPermissions):
        key = "tree_bot_missing_perms"
        perms = ", ".join(error.missing_permissions)
        string = get_localised_string(locale, key, perms=perms) if perms else get_localised_string(locale, key)
        
    elif isinstance(error, TransformerError):
        key = "tree_transformer_error"
        string = get_localised_string(locale, key)
        
        logger.warning(f"Transformer failure: [Converting: {error.value} | To: {error.transformer._error_display_name!s}]")
    
    elif isinstance(error, NovaError):
        pass
    
    else:
        try:
            raise error
        except Exception as e:
            log_exception(e, logger)
    
    if string:
        await respond(interaction, Colour.red(), string, hidden=True)


class TreeSyncer:
    def __init__(self, client: "Client") -> None:
        self.client = client
    
    def _process_group(self, group: Group) -> dict:
        logger.debug(f"Processing group: {group.name}")
        
        group_data = {
            "name": group.name,
            "description": group.description,
            "allowed_installs": [
                group.allowed_installs.guild,
                group.allowed_installs.user
            ] if group.allowed_installs else [],
            "allowed_contexts": [
                group.allowed_contexts.guild,
                group.allowed_contexts.dm_channel,
                group.allowed_contexts.private_channel
            ] if group.allowed_contexts else [],
            "nsfw": group.nsfw,
            "commands": []
        }
        
        for sub in group.commands:
            if isinstance(sub, Command):
                group_data["commands"].append(self._process_command(sub, group.name))
            elif isinstance(sub, Group):
                group_data["commands"].append(self._process_group(sub))
        
        return group_data
    
    def _process_command(self, command: Command, group_name: Optional[str] = None) -> dict:
        logger.debug(f"Processing command: {command.name}")

        cmd_data = {
            "name": command.name,
            "description": command.description,
            "allowed_installs": [
                command.allowed_installs.guild,
                command.allowed_installs.user
            ] if command.allowed_installs else [],
            "allowed_contexts": [
                command.allowed_contexts.guild,
                command.allowed_contexts.dm_channel,
                command.allowed_contexts.private_channel
            ] if command.allowed_contexts else [],
            "nsfw": command.nsfw,
            "parent": group_name,
            "options": [
                {
                    "name": opt.name,
                    "description": opt.description,
                    "required": opt.required,
                    "type": str(opt.type),
                    "choices": [
                        {
                            "name": choice.name,
                            "value": choice.value
                        }
                        for choice in opt.choices
                    ] if hasattr(opt, "choices") and opt.choices else []
                }
                for opt in command.parameters
            ] if command.parameters else []
        }
        
        return cmd_data
    
    def _generate_hash(self) -> str:
        logger.info("Generating hash")
        
        command_data = []
        
        for cmd in self.client.tree.get_commands():             
            if isinstance(cmd, Group):
                command_data.append(self._process_group(cmd))
            
            elif isinstance(cmd, Command):
                command_data.append(self._process_command(cmd))
        
        commands_json = json.dumps(command_data, sort_keys=True)
        commands_hash = hashlib.sha256(commands_json.encode()).hexdigest()
        
        logger.debug(f"Command tree hash: {commands_hash}")
        
        return commands_hash

    def _save_hash(self) -> None:
        logger.info("Saving hash")
        
        hash = self._generate_hash()
        
        with open(Path.TREE_HASH.value, "w") as f:
            f.write(hash)

    def _load_hash(self) -> Optional[str]:
        logger.info("Loading hash")
        
        try:
            with open(Path.TREE_HASH.value, "r") as f:
                return f.read()
        
        except FileNotFoundError:
            return None

    def _compare_hash(self) -> bool:
        logger.info("Checking for command changes")
        
        saved_hash = self._load_hash()
        
        if saved_hash is None:
            logger.warning("No tree hash found")            
            return False
        
        new_hash = self._generate_hash()
        
        return saved_hash == new_hash

    async def _sync(self) -> None:
        logger.info("Syncing commands")
        
        await self.client.tree.sync()
        
        if conf.testing_servers:
            logger.info("Trying to sync to provided testing guild(s)")
            
            for guild_id in conf.testing_servers:
                guild = await get_guild(self.client, guild_id)
                
                if guild:
                    await self.client.tree.sync(guild=guild)
                    
                    logger.info(f"Synced to guild {guild.name} ({guild_id})")
                
                else:
                    logger.warning(f"Failed to sync to guild '{guild_id}', null returned")

        self._save_hash()

    async def sync(self, force: bool = False) -> None:
        if conf.always_sync or force:
            return await self._sync()
        
        if self._compare_hash():
            logger.info("No command changes detected")
        else:
            await self._sync()