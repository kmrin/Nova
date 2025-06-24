import os
import time
import asyncio
import discord
import platform
import wavelink
import tempfile

from discord.app_commands import Command, ContextMenu
from discord import Interaction, VoiceState, Guild, Member, Message, Embed
from discord import Forbidden
from typing import TYPE_CHECKING
from gtts import gTTS

from ..helpers import value_to_colour
from ..utils import get_full_command, get_channel, get_user_avatar
from ..conf import conf
from ..log import Logger, log_exception, format_exception
from ..subclasses import Cog
from ..objects import TTSClient
from ..models import Guilds, GuildConfig, Warns, Users

if TYPE_CHECKING:
    from ..client import Client

logger = Logger.EVENTS
user_msg_times: dict[int, list[float]] = {}

SPAM_TIME_WINDOW = conf.spam_filter.time_window
SPAM_MAX_PER_WINDOW = conf.spam_filter.max_per_window


async def play_tts(client: TTSClient, message: str) -> None:
    async def _wait() -> None:
        while client.client.is_playing():
            await asyncio.sleep(0.5)
    
    if not client.client.is_connected():
        logger.error(f"Failed to play TTS message: {message} - Not connected to a voice channel")
        return
    
    temp_audio_path = None
    
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as temp_file:
            temp_audio_path = temp_file.name
            
            await asyncio.to_thread(gTTS(message, lang=client.language).write_to_fp, temp_file)
        
        await _wait()
        client.client.play(discord.FFmpegPCMAudio(temp_audio_path))
        await _wait()
        
    except Exception as e:
        logger.error(f"Failed to play TTS message: {message} - {format_exception(e)}")
        log_exception(e, logger)
    
    finally:
        if temp_audio_path and os.path.exists(temp_audio_path):
            try:
                await asyncio.to_thread(os.remove, temp_audio_path)
            except Exception as e:
                logger.warning(f"Failed to cleanup temporary TTS file {temp_audio_path}: {format_exception(e)}")


class EventHandler(Cog, name="event_handler"):
    def __init__(self, client: "Client") -> None:
        self.client = client
    
    @Cog.listener()
    async def on_ready(self) -> None:
        logger.info(
            f"""
            ┌─────────────────────────────────────
            │ > Nova {conf.version}
            ├─────────────────────────────────────
            │ > Logged in as: {self.client.user.name if self.client.user else "Unknown"}
            │ > Discord.py version: {discord.__version__}
            │ > Python ver: {platform.python_version()}
            │ > Running on: {platform.system()} {platform.release()}
            └─────────────────────────────────────
            """
        )
        
        self.client.start_time = time.time()
        
        # Connect to lavalink
        await self._connect_to_lavalink()
        
        # Update DB
        await self.client.db_manager.populate_database()
        await self.client.db_manager.purge_database()
        
        # Run tasks
        await self.client.task_handler.start()
        
        startup_time = time.time() - self.client.start_time
        logger.info(f"Nova took {startup_time:.2f}s to start")
    
    async def _connect_to_lavalink(self, max_retries: int = 5, retry_delay: float = 1.0) -> None:
        async def check_retries(attempt: int) -> None:
            if attempt < max_retries:
                logger.info(f"Retrying")
                await asyncio.sleep(retry_delay)
            
            else:
                logger.critical("Maximum retries reached. Could not connect to Lavalink server, check host and port")
                await self.client.stop()
        
        for attempt in range(1, max_retries + 1):
            try:
                logger.info(f"Connecting to Lavalink (Attempt {attempt}/{max_retries})")
                
                node = wavelink.Node(
                    uri=f"http://{conf.lavalink.host}:{conf.lavalink.port}",
                    password=conf.lavalink.password,
                    retries=1
                )
                
                await wavelink.Pool.connect(nodes=[node], client=self.client)
                logger.info("Successfully connected to Lavalink")
                
                break
            
            except wavelink.LavalinkException as e:
                logger.error(f"Failed to connect to Lavalink: {format_exception(e)}")
                await check_retries(attempt)
            
            except Exception as e:
                logger.error(f"An unexpected error occurred while connecting to Lavalink: {format_exception(e)}")
                await check_retries(attempt)
            
            await asyncio.sleep(retry_delay)
               
    @Cog.listener()
    async def on_wavelink_node_ready(self, payload: wavelink.NodeReadyEventPayload) -> None:
        logger.info(
            f"Wavelink node ready: [Node {payload.node} | Res.: {payload.resumed} | S. ID: {payload.session_id}]")

    @Cog.listener()
    async def on_guild_join(self, guild: Guild) -> None:
        logger.info(f"Joined guild: {guild.name} (ID: {guild.id})")
        await self.client.db_manager.populate_database()
    
    @Cog.listener()
    async def on_guild_remove(self, guild: Guild) -> None:
        logger.info(f"Left guild: {guild.name} (ID: {guild.id})")
        await self.client.db_manager.purge_database()
    
    @Cog.listener()
    async def on_member_join(self, member: Member) -> None:
        logger.info(f"Member {member.name} joined: {member.guild.name} (ID: {member.guild.id})")
        await self.client.db_manager.populate_database()

        await self._on_member_join_action_welcome(member)
        await self._on_member_join_action_role(member)
    
    async def _on_member_join_action_welcome(self, member: Member) -> None:
        guild = member.guild
        guild_data = await Guilds.objects.aget(guild_id=guild.id)
        guild_config: GuildConfig = guild_data.config
        
        if not guild_config.welcome_active or not guild_config.welcome_channel_id:
            return
        
        logger.info(f"Performing welcome action for {member.display_name} on {guild.name} (ID: {guild.id})")
        
        channel = await get_channel(self.client, guild_config.welcome_channel_id)
        
        if not channel:
            logger.error(f"Welcome channel not found for {guild.name} (ID: {guild.id})")
            return
        
        if not isinstance(channel, discord.TextChannel):
            logger.error(f"Welcome channel is not a text channel for {guild.name} (ID: {guild.id})")
            return
        
        title: str = guild_config.welcome_title
        description: str = guild_config.welcome_description
        show_pfp: bool = guild_config.welcome_show_pfp
        
        if "<username>" in title:
            title = title.replace("<username>", member.display_name)
        if "<guildname>" in title:
            title = title.replace("<guildname>", guild.name)
        
        embed = Embed(title=title, colour=value_to_colour(guild_config.welcome_colour))
        
        if description:
            if "<username>" in description:
                description = description.replace("<username>", member.display_name)
            elif "<mention>" in description:
                description = description.replace("<mention>", member.mention)
            elif "<guildname>" in description:
                description = description.replace("<guildname>", guild.name)
            
            embed.description = description
        
        user_pic = get_user_avatar(member)
        
        if show_pfp == 1:
            embed.set_thumbnail(url=user_pic)
        elif show_pfp == 2:
            embed.set_image(url=user_pic)
        
        await channel.send(embed=embed)
    
    async def _on_member_join_action_role(self, member: Member) -> None:
        guild = member.guild
        guild_data = await Guilds.objects.aget(guild_id=guild.id)
        guild_config: GuildConfig = guild_data.config
        me = guild.me
        
        if not guild_config.auto_role_active or not guild_config.auto_role_id:
            return
        
        logger.info(f"Performing auto role action for {member.display_name} on {guild.name} (ID: {guild.id})")
        
        role = await guild.fetch_role(guild_config.auto_role_id)
        
        if not role:
            logger.error(f"Role with ID {guild_config.auto_role_id} not found on {guild.name} (ID: {guild.id})")
            return
        
        if role in member.roles:
            logger.info(f"{member.display_name} already has the role on {guild.name} (ID: {guild.id})")
            return
        
        logger.info(f"Adding role {role.name} to {member.display_name} on {guild.name} (ID: {guild.id})")
        
        if not me.guild_permissions.manage_roles:
            logger.error(f"I don't have the necessary permissions to manage roles on {guild.name} (ID: {guild.id})")
            return
        
        try:
            await member.add_roles(role)
        except Forbidden:
            logger.warning(
                f"I am unable to assign '{role.name}' to {member.display_name} on {guild.name} (ID: {guild.id})" \
                f", my role is probably lower than the role I'm trying to assign"
            )
    
    @Cog.listener()
    async def on_member_remove(self, member: Member) -> None:
        logger.info(f"Member {member.display_name} left: {member.guild.name} (ID: {member.guild.id})")
    
    async def _on_spam_action(self, message: Message) -> None:
        guild = message.guild
        
        if not guild:
            return
        
        async def _delete_message() -> None:
            if me.guild_permissions.manage_messages:
                try:
                    logger.info(f"Deleting message")
                    await message.delete()
                except Forbidden:
                    logger.warning(f"I am unable to delete '{message.content}' on {guild.name} (ID: {guild.id})")
            else:
                logger.warning(
                    f"I don't have the necessary permissions to manage messages on {guild.name} (ID: {guild.id})")
        
        async def _send_message(msg: str) -> None:
            if "<username>" in msg:
                msg = msg.replace("<username>", message.author.display_name)
            elif "<mention>" in msg:
                msg = msg.replace("<mention>", message.author.mention)
                
            await message.channel.send(msg)
        
        guild_data: Guilds = await Guilds.objects.aget(guild_id=guild.id)
        guild_config: GuildConfig = guild_data.config
        
        me = guild.me
        
        action: int = guild_config.spam_filter_action
        spam_message: str = guild_config.spam_filter_message
        
        if action == 0:
            logger.info(f"Spam filter action is disabled for {guild.name} (ID: {guild.id})")
            return
        
        elif action == 1:
            logger.info(f"Spam filter action is set to 'Delete' for {guild.name} (ID: {guild.id})")
            await _delete_message()
            
            if spam_message:
                await _send_message(spam_message)
        
        elif action == 2:
            logger.info(f"Spam filter action is set to 'Warn' for {guild.name} (ID: {guild.id})")
            await _delete_message()
            
            if spam_message:
                await _send_message(spam_message)
            
            try:
                user_data = await Users.objects.aget(user_id=message.author.id)
                
                warn = await Warns.objects.acreate(
                    user=user_data,
                    reason="Spam",
                    is_active=True
                )
                
                await guild_data.warns.aadd(warn)
            
            except Exception as e:
                logger.error(
                    f"Failed to create warn for {message.author.display_name} on {guild.name} (ID: {guild.id})"
                    f" - {format_exception(e)}"
                )
                log_exception(e, logger)
    
    async def _on_message_tts(self, message: Message) -> None:
        guild = message.guild
        
        if not guild:
            return
        
        if (
            guild.id in self.client.tts_clients.keys()
            and message.content and len(message.content) <= 250
        ):
            tts_client = self.client.tts_clients.get(guild.id)
            
            if not tts_client:
                logger.error(f"No TTS client found for {guild.name} (ID: {guild.id})")
                return
            
            msg = f"{message.author.name}: {message.content}" if tts_client.blame else message.content
            
            await play_tts(tts_client, msg)
    
    @Cog.listener()
    async def on_message(self, message: Message) -> None:
        guild = message.guild
        author = message.author
        
        if (
            author.bot or author.system or author == self.client.user
            or not guild
        ):
            return
        
        if conf.debug and message.content:
            logger.debug(
                f"Message '{message.content}' sent by {message.author.display_name} " \
                f"in {message.channel} at {message.guild}"
            )
        
        # Anti-spam
        if conf.spam_filter.enabled:
            user_id = author.id
            curr_time = time.time()
            
            if user_id not in user_msg_times:
                user_msg_times[user_id] = []
            
            user_msg_times[user_id] = [
                t for t in user_msg_times[user_id]
                if curr_time - t <= SPAM_TIME_WINDOW
            ]
            user_msg_times[user_id].append(curr_time)
            
            if len(user_msg_times[user_id]) > SPAM_MAX_PER_WINDOW:
                return await self._on_spam_action(message)
        
        await self._on_message_tts(message)
    
    @Cog.listener()
    async def on_voice_state_update(self, member: Member, before: VoiceState, after: VoiceState) -> None:
        if not self.client.user:
            return
        
        if (member.id != self.client.user.id) or (before.channel is None):
            return
        
        if after.channel:
            for member in after.channel.members:
                if member.id == self.client.user.id:
                    return
        
        guild = before.channel.guild
        
        if not guild:
            return
        
        logger.warning(f"Disconnected from '{before.channel.name}' on {guild.name} (ID: {guild.id})")
        
        if guild.id in self.client.tts_clients.keys():
            if guild.id in self.client.tts_clients.keys():
                del self.client.tts_clients[guild.id]
                logger.info(f"Closed a TTS client that was active there")
            
        elif guild.id in self.client.music_clients.keys():
            if guild.id in self.client.music_clients.keys():
                del self.client.music_clients[guild.id]
                logger.info(f"Closed a music client that was active there")
    
    @Cog.listener()
    async def on_app_command_completion(self, interaction: Interaction, command: Command | ContextMenu) -> None:
        guild = interaction.guild.name if interaction.guild else "DMs"
        guild_id = interaction.guild.id if interaction.guild else None
        user = interaction.user.name
        user_id = interaction.user.id
        
        command_name = get_full_command(interaction)
        
        logger.info(
            f"Command '{command_name}' executed by {user} (ID: {user_id}) " \
            f"on {guild} (ID: {guild_id})"
        )