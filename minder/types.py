from __future__ import annotations

import discord
import logging
import pytz

from dataclasses import dataclass, InitVar
from datetime import datetime
from discord.ext import commands
from typing import Union, Optional, TypeVar

from minder.errors import MinderBotError

logger = logging.getLogger(__name__)

DateTimeType = Union[float, int, datetime]
TimezoneType = Union[pytz.tzinfo.BaseTzInfo, TypeVar('Timezone'), str]
GuildType = Union[discord.Guild, int]
MemberType = Union[discord.User, discord.Member]
ChannelType = Union[discord.TextChannel, discord.DMChannel]
ContextOrGuild = Union[commands.Context, discord.Guild]


@dataclass
class DiscordMember:
    id: int
    name: str

    _guild: InitVar[discord.Guild] = None
    _member: InitVar[MemberType] = None

    @property
    def mention(self) -> str:
        return self._member.mention if self._member else self.name

    @property
    def guild(self) -> Optional[discord.Guild]:
        if self._guild:
            return self._guild

        if self._member and self._member.guild:
            return self._member.guild

        return None

    @property
    def member(self) -> Optional[MemberType]:
        return self._member

    @classmethod
    def build(cls, id: int, name: Optional[str], context_or_guild: ContextOrGuild = None) -> DiscordMember:
        guild, member = None, None

        if not context_or_guild:
            if not name:
                raise MinderBotError(f'No guild/context provided when looking up user "{id}" with no provided username. Provide "name" explicitly')
        else:
            guild = context_or_guild if not isinstance(context_or_guild, commands.Context) else context_or_guild.guild
            member = cls.resolve(id, guild)

            if not name:
                if not member:
                    ctx = context_or_guild if isinstance(context_or_guild, commands.Context) else None
                    raise MinderBotError(f'Failed to resolve member ID {id} and no "name" provided.', context=ctx)

                name = member.name

        return DiscordMember(id=id, name=name, _guild=guild, _member=member)

    @staticmethod
    def resolve(id: int, guild: discord.Guild) -> Optional[MemberType]:
        try:
            member = guild.get_member(id)
        except Exception as ex:
            if not isinstance(ex, discord.errors.NotFound):
                raise MinderBotError(f'General error lookup up member ID {id}: {ex}', base_exception=ex)

            logger.warning(f'No member found for ID {id} on guild "{guild.name}" (ID {guild.id}). Not resolving.')
            member = None

        return member

    @classmethod
    def from_member(cls, member: MemberType) -> DiscordMember:
        return DiscordMember(id=member.id, name=member.name, _guild=member.guild, _member=member)


@dataclass
class DiscordChannel:
    id: int
    name: str

    is_dm: Optional[bool] = None
    _guild: InitVar[discord.Guild] = None
    _channel: InitVar[ChannelType] = None

    @property
    def mention(self) -> str:
        return self._channel.mention if self._channel else self.name

    @property
    def guild(self) -> Optional[discord.Guild]:
        if self._guild:
            return self._guild

        if self._channel and self._channel.guild:
            return self._channel.guild

        return None

    @property
    def channel(self) -> Optional[ChannelType]:
        return self._channel

    @classmethod
    def build(cls, id: int, name: str, is_dm: bool = None, context_or_guild: ContextOrGuild = None) -> DiscordChannel:
        guild, channel = None, None

        if not context_or_guild:
            if not name:
                raise MinderBotError(f'No guild/context provided when looking up channel "{id}" with no provided username. Provide "name" explicitly')
        else:
            guild = context_or_guild if not isinstance(context_or_guild, commands.Context) else context_or_guild.guild
            channel = cls.resolve(id, guild)

            if not name:
                if not channel:
                    ctx = context_or_guild if isinstance(context_or_guild, commands.Context) else None
                    raise MinderBotError(f'Failed to resolve channel ID {id} and no "name" provided.', context=ctx)

                name = channel.name

        if is_dm is None and channel:
            is_dm = isinstance(channel, discord.DMChannel)

        return DiscordChannel(id=id, name=name, is_dm=is_dm, _guild=guild, _channel=channel)

    @staticmethod
    def resolve(id: int, guild: discord.Guild) -> Optional[ChannelType]:
        try:
            channel = guild.get_channel(id)
        except Exception as ex:
            if not isinstance(ex, discord.errors.NotFound):
                raise MinderBotError(f'General error lookup up channel ID {id}: {ex}', base_exception=ex)

            logger.warning(f'No channel found for ID {id} on guild "{guild.name}" (ID {guild.id}). Not resolving.')
            channel = None

        return channel

    @classmethod
    def from_channel(cls, channel: ChannelType) -> DiscordChannel:
        return DiscordChannel(id=channel.id, name=channel.name, is_dm=isinstance(channel, discord.DMChannel), _channel=channel)
