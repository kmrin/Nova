"""
Nova's "core" extension

Commands:
    * /info - Shows information about Nova
    * /help - Shows a paginated help embed
    * /ping - Shows the bot's latency to Discord
    * /sync <global> - Sync Nova's command tree to the current guild or globally
    * /owner me <token> - Adds the caster to the owner list using the token provided during Nova's initialization
    * /owner add <user> - Adds a user to the owner list
    * /owner remove <user> - Removes a user from the owner list
    * /extension list - Lists all loaded and unloaded extensions
    * /extension load <extension> - Loads an extension
    * /extension unload <extension> - Unloads an extension
    * /extension reload <extension> - Reloads an extension
"""

import os
import discord
import platform

from datetime import datetime

from discord import (
    Interaction,
    Colour,
    Embed,
    Member,
    User,
    Object,
)

from discord.app_commands import (
    Group,
    Choice,
    locale_str,
    command,
    choices,
    allowed_contexts,
    allowed_installs,
    describe,
    rename
)

from discord.ext.commands import (
    ExtensionNotFound,
    ExtensionAlreadyLoaded,
    ExtensionNotLoaded,
    NoEntryPointError
)

from ..conf import conf
from ..client import Client
from ..subclasses import Cog
from ..checks import commands
from ..objects import CommandOptions
from ..paths import Path
from ..models import Owners
from ..ui.default_pagination import DefaultPagination
from ..responder import respond
from ..log import Logger
from ..helpers import remove_newline_from_string_list, choice_to_bool
from ..utils import get_user_avatar

from ..managers.locale import (
    get_interaction_locale as get_locale,
    get_localised_list as get_list,
    get_localised_string as get_str
)

logger = Logger.EXTENSIONS


class Core(Cog, name="core"):
    def __init__(self, client: Client) -> None:
        self.client = client
    
    # /owner
    owner_group = Group(
        name=locale_str("core_owner_gp_name"),
        description=locale_str("core_owner_gp_desc")
    )
    
    # /extension
    extension_group = Group(
        name=locale_str("core_extension_gp_name"),
        description=locale_str("core_extension_gp_desc")
    )
    
    # /info
    @command(
        name=locale_str("core_info_name"),
        description=locale_str("core_info_desc")
    )
    @commands.not_blacklisted()
    async def _info(self, interaction: Interaction) -> None:
        locale = get_locale(interaction)
        
        created_at_list = get_list(locale, "core_info_created")
        created_at_date = datetime.fromtimestamp(float(created_at_list[1])).strftime("%d/%m/%Y")
        created_at_time = f"<t:{int(created_at_list[1])}:R>"
        
        developer = get_list(locale, "core_info_developer")
        testers = get_list(locale, "core_info_testers")
        
        py_info = get_str(locale, "core_info_py")
        dc_info = get_str(locale, "core_info_dc")
        requested_by = get_str(locale, "core_info_requested", user=interaction.user.display_name)
        title = get_str(locale, "core_info_title", version=conf.version)
        
        embed = Embed(
            title=title,
            colour=Colour.purple()
        )
        
        embed.set_thumbnail(url=await get_user_avatar(self.client.user))
        
        fields = [
            (created_at_list[0], f"**{created_at_date}**\n{created_at_time}", True),
            (developer[0], developer[1], True),
            (testers[0], testers[1], True),
            (py_info, f"{platform.python_version()}", True),
            (dc_info, f"{discord.__version__}", True)
        ]
        
        for field in fields:
            embed.add_field(
                name=field[0],
                value=field[1],
                inline=field[2]
            )
        
        embed.set_footer(
            text=requested_by,
            icon_url=await get_user_avatar(interaction.user)
        )
        
        await respond(interaction, message=embed)

    # /help
    @command(
        name=locale_str("core_help_name"),
        description=locale_str("core_help_desc")
    )
    @commands.not_blacklisted()
    async def _help(self, interaction: Interaction) -> None:
        locale = get_locale(interaction)
        help_path = os.path.join(Path.DOCS, f"help_{locale}.md")
        
        if not os.path.exists(help_path):
            logger.warning(f"Help file for locale {locale} not found, using default")
            help_path = os.path.join(Path.DOCS, "help_en-GB.md")
            
            if not os.path.exists(help_path):
                logger.error(f"Help file for default locale not found")
                return await self.respond_with_failure(interaction, "core_help_not_found", hidden=True)
        
        with open(help_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
            lines = "\n".join(remove_newline_from_string_list(lines)).split("\n")
            
            chunks = [lines[i:i+15] for i in range(0, len(lines), 15)]
            
            embed = Embed(
                description="\n".join(chunks[0]),
                colour=Colour.purple()
            )
            
            view = DefaultPagination(embed, chunks)
            
            await respond(interaction, message=embed, view=view, outside_content=get_str(locale, "core_help_title"))
    
    # /ping
    @command(
        name=locale_str("core_ping_name"),
        description=locale_str("core_ping_desc")
    )
    @commands.not_blacklisted()
    async def _ping(self, interaction: Interaction) -> None:
        locale = get_locale(interaction)
        ping_response = get_str(locale, "core_ping_response", ping=round(self.client.latency * 1000))
        
        await respond(interaction, Colour.purple(), ping_response)
    
    # /sync
    @command(
        name=locale_str("core_sync_name"),
        description=locale_str("core_sync_desc")
    )
    @rename(full=locale_str("core_sync_full_name"))
    @describe(full=locale_str("core_sync_full_desc"))
    @choices(full=CommandOptions.BASIC_CONFIRMATION)
    @allowed_contexts(guilds=True)
    @allowed_installs(True, False)
    @commands.is_owner()
    async def _sync(self, interaction: Interaction, full: Choice[int]) -> None:
        locale = get_locale(interaction)
        full = choice_to_bool(full)  # type: ignore
        guild = Object(id=interaction.guild.id) if full else None  # type: ignore
        
        await respond(interaction, Colour.green(), get_str(locale, "core_sync_success"))
        await self.client.tree.sync(guild=guild)
    
    async def _add_owner(self, user: User | Member) -> bool:
        new_owner = await Owners.objects.acreate(
            user_id=user.id,
            user_name=user.display_name
        )
        await new_owner.asave()
        
        return new_owner is not None
    
    # /owner me
    @owner_group.command(
        name=locale_str("core_owner_me_name"),
        description=locale_str("core_owner_me_desc")
    )
    @rename(token=locale_str("core_owner_me_token_name"))
    @describe(token=locale_str("core_owner_me_token_desc"))
    @commands.not_blacklisted()
    async def _owner_me(self, interaction: Interaction, token: str) -> None:
        locale = get_locale(interaction)
        
        if await Owners.objects.filter(user_id=interaction.user.id).aexists():
            return await self.respond_with_failure(
                interaction, "core_owner_me_already_owner", hidden=True
            )
        
        if token != self.client._owner_token:
            return await self.respond_with_failure(
                interaction, "core_owner_me_invalid_token", hidden=True
            )
        
        if not await self._add_owner(interaction.user):
            return await self.respond_with_failure(
                interaction, "core_owner_me_failed", hidden=True
            )
        
        await respond(interaction, Colour.green(), get_str(locale, "core_owner_me_success"))
    
    # /owner add
    @owner_group.command(
        name=locale_str("core_owner_add_name"),
        description=locale_str("core_owner_add_desc")
    )
    @rename(user=locale_str("core_owner_user_name"))
    @describe(user=locale_str("core_owner_add_user_desc"))
    @commands.is_owner()
    async def _owner_add(self, interaction: Interaction, user: Member) -> None:
        locale = get_locale(interaction)
        
        if await Owners.objects.filter(user_id=user.id).aexists():
            return await self.respond_with_failure(
                interaction, "core_owner_add_already_owner", hidden=True
            )
        
        if not await self._add_owner(user):
            return await self.respond_with_failure(
                interaction, "core_owner_add_failed", hidden=True
            )
        
        await respond(interaction, Colour.green(), get_str(locale, "core_owner_add_success"))
    
    # /owner remove
    @owner_group.command(
        name=locale_str("core_owner_remove_name"),
        description=locale_str("core_owner_remove_desc")
    )
    @rename(user=locale_str("core_owner_user_name"))
    @describe(user=locale_str("core_owner_remove_user_desc"))
    @commands.is_owner()
    async def _owner_remove(self, interaction: Interaction, user: Member) -> None:
        locale = get_locale(interaction)
        
        if not await Owners.objects.filter(user_id=user.id).aexists():
            return await self.respond_with_failure(
                interaction, "core_owner_remove_not_owner", hidden=True
            )
        
        await Owners.objects.filter(user_id=user.id).adelete()
        await respond(interaction, Colour.green(), get_str(locale, "core_owner_remove_success"))
    
    # /extension list
    @extension_group.command(
        name=locale_str("core_extension_list_name"),
        description=locale_str("core_extension_list_desc")
    )
    @commands.is_owner()
    async def _extension_list(self, interaction: Interaction) -> None:
        locale = get_locale(interaction)
        extensions: list[dict] = []
        
        # Loaded extensions
        for extension in self.client.cogs:
            extensions.append({"name": extension, "loaded": True})
        
        # Unloaded extensions
        for extension in os.listdir(Path.EXTENSIONS):
            if extension.endswith(".py"):
                extension = extension[:-3]
                
                if extension not in [e["name"] for e in extensions]:
                    extensions.append({"name": extension, "loaded": False})
        
        lines = [f"* {'🟢' if e['loaded'] else '🔴'} {e['name']}" for e in extensions]
        chunks = [lines[i:i+15] for i in range(0, len(lines), 15)]
        view = None
        
        embed = Embed(
            title=get_str(locale, "core_extension_list_header"),
            description="\n".join(chunks[0]),
            colour=Colour.gold()
        )
        
        if len(chunks) > 1:
            view = DefaultPagination(embed, chunks)
        
        await respond(
            interaction,
            message=embed,
            view=view,
            outside_content=get_str(locale, "core_extension_list_helper")
        )
    
    # /extension load
    @extension_group.command(
        name=locale_str("core_extension_load_name"),
        description=locale_str("core_extension_load_desc")
    )
    @rename(extension=locale_str("core_extension_ext_name"))
    @describe(extension=locale_str("core_extension_ext_desc"))
    @commands.is_owner()
    async def _extension_load(self, interaction: Interaction, extension: str) -> None:
        locale = get_locale(interaction)
        
        if extension.lower() in ["core", "event_handler"]:
            return await self.respond_with_failure(
                interaction, "core_extension_internal", hidden=True
            )
        
        try:
            await self.client.load_extension(f"apps.bot.extensions.{extension}")
            
            message = get_str(locale, "core_extension_load_success")
            colour = Colour.green()
        
        except ExtensionNotFound:
            message = get_str(locale, "core_extension_not_found")
            colour = Colour.red()
        except ExtensionAlreadyLoaded:
            message = get_str(locale, "core_extension_already_loaded")
            colour = Colour.red()
        except NoEntryPointError:
            message = get_str(locale, "core_extension_no_entry")
            colour = Colour.red()
        
        await respond(interaction, colour, message)
        await self.client.tree_syncer.sync(force=True)
    
    # /extension unload
    @extension_group.command(
        name=locale_str("core_extension_unload_name"),
        description=locale_str("core_extension_unload_desc")
    )
    @rename(extension=locale_str("core_extension_ext_name"))
    @describe(extension=locale_str("core_extension_ext_desc"))
    @commands.is_owner()
    async def _extension_unload(self, interaction: Interaction, extension: str) -> None:
        locale = get_locale(interaction)
        
        if extension.lower() in ["core", "event_handler"]:
            return await self.respond_with_failure(
                interaction, "core_extension_internal", hidden=True
            )
        
        try:
            await self.client.unload_extension(f"apps.bot.extensions.{extension}")
            
            message = get_str(locale, "core_extension_unload_success")
            colour = Colour.green()
        
        except ExtensionNotFound:
            message = get_str(locale, "core_extension_not_found")
            colour = Colour.red()
        except ExtensionNotLoaded:
            message = get_str(locale, "core_extension_not_loaded")
            colour = Colour.red()
        
        await respond(interaction, colour, message)
        await self.client.tree_syncer.sync(force=True)
    
    # /extension reload
    @extension_group.command(
        name=locale_str("core_extension_reload_name"),
        description=locale_str("core_extension_reload_desc")
    )
    @rename(extension=locale_str("core_extension_ext_name"))
    @describe(extension=locale_str("core_extension_ext_desc"))
    @commands.is_owner()
    async def _extension_reload(self, interaction: Interaction, extension: str) -> None:
        locale = get_locale(interaction)
        
        try:
            await self.client.reload_extension(f"apps.bot.extensions.{extension}")
            
            message = get_str(locale, "core_extension_reload_success")
            colour = Colour.green()
        
        except ExtensionNotFound:
            message = get_str(locale, "core_extension_not_found")
            colour = Colour.red()
        except ExtensionNotLoaded:
            try:
                await self.client.load_extension(f"apps.bot.extensions.{extension}")
                
                message = get_str(locale, "core_extension_reload_success")
                colour = Colour.green()
            
            except NoEntryPointError:
                message = get_str(locale, "core_extension_no_entry")
                colour = Colour.red()
        
        await respond(interaction, colour, message)
        await self.client.tree_syncer.sync(force=True)


async def setup(bot: Client) -> None:
    await bot.add_cog(Core(bot))