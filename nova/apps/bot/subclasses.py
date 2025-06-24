from discord import Interaction, Embed, Colour
from discord.ext.commands import Cog as DiscordCog
from typing import Optional

from .managers.locale import get_interaction_locale, get_localised_string
from .utils import get_full_command
from .log import Logger
from .responder import respond, _send
from .objects import Response

logger = Logger.SUBCLASSES
responder_logger = Logger.RESPONDER


class Cog(DiscordCog):
    @staticmethod
    async def respond_with_defaults(
            interaction: Interaction,
            key: str,
            hidden: bool = False,
            *args,
            **kwargs
    ) -> None:
        locale = get_interaction_locale(interaction)
        message = get_localised_string(locale, key, *args, **kwargs)
        
        await respond(interaction, message=message, hidden=hidden)
    
    @staticmethod
    async def respond_without_embed(
            interaction: Interaction,
            key: str,
            hidden: bool = False,
            response_type: Response = Response.SEND,
            *args, **kwargs
    ) -> None:
        locale = get_interaction_locale(interaction)
        string = get_localised_string(locale, key, *args, **kwargs)
        
        author = interaction.user
        
        await _send(
            ctx=interaction,
            response_type=response_type,
            content=string,
            ephemeral=hidden
        )
        
        responder_logger.info(
            f"Basic response sent: [Author: {author.display_name} (ID: {author.id}) | MSG.: {string}]"
        )
    
    @staticmethod
    async def respond_with_success(interaction: Interaction, key: str, hidden: bool = False, *args, **kwargs) -> None:
        locale = get_interaction_locale(interaction)
        
        await respond(
            interaction, Colour.green(),
            get_localised_string(locale, key, *args, **kwargs),
            hidden=hidden
        )
    
    @staticmethod
    async def respond_with_failure(interaction: Interaction, key: str, hidden: bool = False, *args, **kwargs) -> None:
        locale = get_interaction_locale(interaction)
        
        await respond(
            interaction, Colour.red(),
            get_localised_string(locale, key, *args, **kwargs),
            hidden=hidden
        )
    
    @staticmethod
    async def respond_with_unknown_failure(interaction: Interaction) -> None:
        locale = get_interaction_locale(interaction)
        
        await respond(
            interaction, Colour.red(),
            get_localised_string(locale, "error_unknown"),
            hidden=True
        )
    
    @staticmethod
    async def respond_with_invalid_args(
            interaction: Interaction,
            arguments: str,
            response_type: Response = Response.SEND
    ) -> None:
        locale = get_interaction_locale(interaction)
        command = get_full_command(interaction)
        
        logger.info(f"Responding with invalid args for interaction: [Command: {command} | Args.: '{arguments}']")
        
        await respond(
            interaction, Colour.red(),
            get_localised_string(locale, "error_invalid_arguments", arguments=arguments),
            hidden=True,
            response_type=response_type
        )
    
    @staticmethod
    async def respond_with_timeout(interaction: Interaction) -> None:
        locale = get_interaction_locale(interaction)
        message = get_localised_string(locale, "error_timeout")
        
        await interaction.edit_original_response(
            content=None,
            embed=Embed(
                description=message,
                colour=Colour.yellow()
            ),
            view=None
        )