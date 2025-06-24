from enum import Enum
from typing import Optional
from dataclasses import dataclass
from discord import TextChannel, VoiceClient
from discord.app_commands import Choice, locale_str


class Response(Enum):
    SEND = 1
    FOLLOWUP = 2
    CHANNEL = 3


@dataclass
class Localisation:
    system: dict[str, str | int | list[str | int]]
    commands: dict[str, str | int | list[str | int]]
    responses: dict[str, str | int | list[str | int]]
    
    def all(self) -> dict[str, str | int | list[str | int]]:
        return self.system | self.commands | self.responses


@dataclass
class Track:
    title: str
    url: str
    duration: str
    uploader: Optional[str] = None


@dataclass
class Playlist:
    title: str
    url: str
    count: int
    uploader: Optional[str] = None


@dataclass
class TTSClient:
    channel: TextChannel
    client: VoiceClient
    language: str
    blame: bool


class CommandOptions:
    YES = [Choice(name=locale_str("state_yes"), value=1)]
    NO = [Choice(name=locale_str("state_no"), value=0)]

    BASIC_CONFIRMATION = [
        Choice(name=locale_str("state_yes"), value=1),
        Choice(name=locale_str("state_no"), value=0)
    ]

    EXTENSION_MANIPULATE_OPTS = [
        Choice(name=locale_str("core_ext_manipulate_load_action"), value=0),
        Choice(name=locale_str("core_ext_manipulate_unload_action"), value=1),
        Choice(name=locale_str("core_ext_manipulate_reload_action"), value=2)
    ]

    CONFIG_SET_GREETING_EMBED_PFP = [
        Choice(name=locale_str("config_set_greeting_embed_no_picture"), value=0),
        Choice(name=locale_str("config_set_greeting_embed_small"), value=1),
        Choice(name=locale_str("config_set_greeting_embed_large"), value=2),
    ]


class Perms:
    def __init__(self):
        self.create_instant_invite = self._perm('create_instant_invite')
        self.kick_members = self._perm('kick_members')
        self.ban_members = self._perm('ban_members')
        self.administrator = self._perm('administrator')
        self.manage_channels = self._perm('manage_channels')
        self.manage_guild = self._perm('manage_guild')
        self.add_reactions = self._perm('add_reactions')
        self.view_audit_log = self._perm('view_audit_log')
        self.priority_speaker = self._perm('priority_speaker')
        self.stream = self._perm('stream')
        self.view_channel = self._perm('view_channel')
        self.send_messages = self._perm('send_messages')
        self.send_tts_messages = self._perm('send_tts_messages')
        self.manage_messages = self._perm('manage_messages')
        self.embed_links = self._perm('embed_links')
        self.attach_files = self._perm('attach_files')
        self.read_message_history = self._perm('read_message_history')
        self.mention_everyone = self._perm('mention_everyone')
        self.use_external_emojis = self._perm('use_external_emojis')
        self.view_guild_insights = self._perm('view_guild_insights')
        self.connect = self._perm('connect')
        self.speak = self._perm('speak')
        self.mute_members = self._perm('mute_members')
        self.deafen_members = self._perm('deafen_members')
        self.move_members = self._perm('move_members')
        self.use_vad = self._perm('use_vad')
        self.change_nickname = self._perm('change_nickname')
        self.manage_nicknames = self._perm('manage_nicknames')
        self.manage_roles = self._perm('manage_roles')
        self.manage_webhooks = self._perm('manage_webhooks')
        self.manage_emojis_and_stickers = self._perm('manage_emojis_and_stickers')
        self.use_application_commands = self._perm('use_application_commands')
        self.request_to_speak = self._perm('request_to_speak')
        self.manage_threads = self._perm('manage_threads')
        self.use_public_threads = self._perm('use_public_threads')
        self.use_private_threads = self._perm('use_private_threads')
        self.use_external_stickers = self._perm('use_external_stickers')
        self.send_messages_in_threads = self._perm('send_messages_in_threads')
        self.start_embedded_activities = self._perm('start_embedded_activities')
        self.moderate_members = self._perm('moderate_members')

    @classmethod
    def _perm(cls, permission_name: str):
        return {permission_name: True}