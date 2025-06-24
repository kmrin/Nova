from discord import (
    Interaction,
    Embed,
    Colour,
    Message,
    NotFound,
    InteractionResponded,
    HTTPException,
    InteractionCallbackResponse
)

from discord import ForumChannel, CategoryChannel, DMChannel
from discord.ui import View
from discord.utils import MISSING
from discord.client import Client
from typing import Optional

from .objects import Response
from .log import Logger, log_exception
from .helpers import filter_dict

logger = Logger.RESPONDER


async def _send(
        ctx: Interaction,
        embed: Optional[Embed] = MISSING,
        view: Optional[View] = MISSING,
        content: Optional[str] = MISSING,
        ephemeral: bool = False,
        response_type: Response = Response.SEND,
        _attemped_followup: bool = False,
        _attempted_channel: bool = False,
) -> Optional[Message | InteractionCallbackResponse[Client]]:
    try:
        args = {
            "embed": embed if embed else MISSING,
            "view": view if view else MISSING,
            "content": content if content else MISSING,
            "ephemeral": ephemeral
        }
        
        if response_type == Response.SEND:
            return await ctx.response.send_message(**args)
        
        elif response_type == Response.FOLLOWUP:
            return await ctx.followup.send(**args)
        
        elif response_type == Response.CHANNEL:
            if ctx.channel and not isinstance(ctx.channel, (ForumChannel, CategoryChannel)):
                return await ctx.channel.send(**filter_dict(args, ["ephemeral"]))
            
            logger.warning(f"Attempted to send a message to a channel that is not suitable: {ctx.channel}")
        
        return None
    
    except (NotFound, InteractionResponded):
        if not _attemped_followup:
            logger.warning("Failed to send response, attempting followup")
            return await _send(
                ctx, embed, view, content, ephemeral, Response.FOLLOWUP,
                True, _attempted_channel
            )
        
        elif not _attempted_channel:
            logger.warning("Failed to send follow-up, trying channel message")
            return await _send(
                ctx, embed, view, content, ephemeral, Response.CHANNEL,
                True, True
            )
        
        else:
            logger.error("Failed to send response, all methods failed")
            return None
    
    except HTTPException as e:
        logger.error(
            f"An HTTP error occurred while trying to respond: "
            f"[HTTP CODE: {e.status} | DC CODE: {e.code} | TEXT {e.text}]"
        )
        return None
    
    except Exception as e:
        log_exception(e, logger)
        return None


async def respond(
        ctx: Interaction,
        colour: Colour = Colour.blurple(),
        message: Optional[str | Embed] = None,
        title: Optional[str] = None,
        view: Optional[View] = MISSING,
        outside_content: Optional[str] = None,
        hidden: bool = False,
        response_type: Response = Response.SEND,
        silent: bool = False
) -> None:
    if isinstance(message, Embed):
        embed = message
    else:
        if message and title:
            embed = Embed(title=title, description=message, colour=colour)
        elif message:
            embed = Embed(description=message, colour=colour)
        elif title:
            embed = Embed(title=title, colour=colour)
        else:
            embed = None
    
    author = ctx.user
    guild = ctx.guild if ctx.guild else None
    channel = ctx.channel
    
    await _send(
        ctx,
        embed=embed,
        view=view,
        content=outside_content,
        ephemeral=hidden,
        response_type=response_type
    )
    
    if silent:
        return
    
    if embed and view:
        response_type_str = "Embed + View"
    elif embed:
        response_type_str = "Embed"
    elif view:
        response_type_str = "View"
    else:
        response_type_str = "Text"
    
    message_content = embed.description or embed.title if embed else outside_content or "[No content]"
    
    if channel:
        if isinstance(channel, DMChannel):
            logger.info(
                f"Response sent: [TYPE: {response_type_str} | "
                f"AUTHOR: {author} (ID: {author.id if author else 0}) | "
                f"DMs | MSG: {message_content}]"
            )

        elif guild:
            logger.info(
                f"Response sent: [TYPE: {response_type_str} | "
                f"GUILD: {guild} (ID: {guild.id}) | "
                f"AUTHOR: {author} (ID: {author.id if author else 0}) | "
                f"CH: {channel.name} (ID: {channel.id}) | "
                f"MSG: {message_content}]"
            )