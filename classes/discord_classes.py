from utils.globals import get_bot
from config import DEFAULT_DISCORD_AVATAR as default_discord_avatar

import discord
import asyncio
import chat_exporter

class DiscordGuild:
    def __init__(self, guild_id: int):
        guild_object = get_bot().get_guild(guild_id)

        if guild_object:
            self.id = guild_object.id
            self.name = guild_object.name
            self.created_at = guild_object.created_at.timestamp()
            self.icon = guild_object.icon.url if guild_object.icon else None
            self.member_count = guild_object.member_count
        else:
            self.id = None
            self.name = None
            self.created_at = None
            self.icon = None
            self.member_count = None


class DiscordUser:
    def __init__(self, user_id: int):
        user_object = get_bot().get_user(user_id)

        if user_object:
            # color
            self.accent_color = user_object.accent_color.__str__() if user_object.accent_color else None
            self.color = user_object.color.__str__() if user_object.color else None

            # avatar and banner
            self.avatar = user_object.avatar.url if user_object.avatar else None
            self.display_avatar = user_object.display_avatar.url if user_object.display_avatar else None
            self.default_avatar = user_object.default_avatar.url if user_object.default_avatar else None
            self.banner = user_object.banner.url if user_object.banner else None

            # name
            self.name = user_object.name
            self.display_name = user_object.display_name
            self.global_name = user_object.global_name

            # id
            self.id = user_object.id
            self.discriminator = user_object.discriminator

            # bool
            self.bot = user_object.bot
            self.system = user_object.system

            # timestamp
            self.created_at = user_object.created_at.timestamp()

            # mutual guilds
            guilds = []
            for guild in user_object.mutual_guilds:
                guilds.append(DiscordGuild(guild.id))
            self.mutual_guilds = guilds

            # public flags
            self.badges = dict(iter(user_object.public_flags))

        else:
            self.accent_color = None
            self.color = None
            self.avatar = None
            self.display_avatar = None
            self.default_avatar = None
            self.banner = None
            self.name = None
            self.display_name = None
            self.global_name = None
            self.id = None
            self.discriminator = None
            self.bot = None
            self.system = None
            self.created_at = None
            self.mutual_guilds = None
            self.badges = None

class DiscordMember:
    def __init__(self, member_object: discord.Member):
        # id
        self.id = member_object.id
        self.discriminator = member_object.discriminator
        self.bot = member_object.bot

        # name
        self.name = member_object.name  # username
        self.nick = member_object.nick  # guild nickname
        self.global_name = member_object.global_name  # global display name
        self.display_name = member_object.display_name  # guild display name

        # get url from Asset class else none
        self.avatar = member_object.avatar.url if member_object.avatar else None
        self.banner = member_object.banner.url if member_object.banner else None

        # Color is a class, so we need to convert it to hex
        self.color = member_object.color.__str__() if member_object.color else None
        self.accent_color = member_object.accent_color.__str__() if member_object.accent_color else None

        # epoch time
        self.created_at = member_object.created_at.timestamp()
        self.joined_at = member_object.joined_at.timestamp()

        # status as string
        self.raw_status = member_object.raw_status

        # Badges
        self.badges = dict(iter(member_object.public_flags))

        # Guild icon
        self.guild_icon = None
        if member_object.guild:
            self.guild_icon = member_object.guild.icon.url if member_object.guild.icon else None

        # Roles
        self.roles = []
        for role in member_object.roles:
            self.roles.append(DiscordRole(role.id, member_object.guild.id, stripped=True))


class DiscordChannel:
    def __init__(self, channel_id: int, no_members=False, json_data=None):
        if json_data:
            self.id = json_data['id']
            self.name = json_data['name']
            self.created_at = json_data['created_at']
            self.members = json_data['members']
            self.member_count = 0
            self.html = json_data['html']
            return

        self.id = channel_id
        self.name = None
        self.created_at = None
        self.members = []
        self.member_count = None
        self.html = None

        channel_object = get_bot().get_channel(channel_id)

        if channel_object:
            self.id = channel_object.id
            self.name = channel_object.name
            self.created_at = channel_object.created_at.strftime("%d/%m/%Y %H:%M:%S")

            members = []
            if not no_members:
                if channel_object.members:
                    for member in channel_object.members:
                        member_object = DiscordMember(member)
                        members.append(member_object)

            self.members = members
            self.member_count = len(channel_object.members)

    async def get_first_messages(self, num_of_messages: int):
        """
        Gets the first messages of a channel
        :param num_of_messages: Number of messages to get
        :return: ReturnData object
        """
        async def get_messages(ch_obj, num):
            msg_list = [message_object async for message_object in ch_obj.history(limit=num)]
            return msg_list


        channel_object = get_bot().get_channel(self.id)
        if not channel_object:
            return None
        if not channel_object.permissions_for(channel_object.guild.me).read_message_history:
            return None

        messages = asyncio.run_coroutine_threadsafe(get_messages(channel_object, num_of_messages), get_bot().loop).result()

        transcript = asyncio.run_coroutine_threadsafe(chat_exporter.raw_export(channel=channel_object,
                                                                               messages=messages,
                                                                               tz_info='GMT',
                                                                               guild=channel_object.guild,
                                                                               bot=get_bot(),
                                                                               military_time=True,
                                                                               support_dev=False), get_bot().loop).result()
        self.html = transcript

        return self.html

class DiscordRole:
    def __init__(self, role_id: int, guild_id: int, no_members: bool=False, stripped: bool=False):
        role_object = get_bot().get_guild(guild_id).get_role(role_id)

        if role_object:
            if stripped:
                self.id = role_object.id
                self.name = role_object.name
                self.created_at = None
                self.color = role_object.color.__str__() if role_object.color else None
                self.permissions = None
                self.members = []
                self.member_count = None
                return


            self.id = role_object.id
            self.name = role_object.name
            self.created_at = role_object.created_at.strftime("%d/%m/%Y %H:%M:%S")
            self.color = role_object.color
            self.permissions = role_object.permissions

            self.members = []
            if not no_members:
                if role_object.members:
                    for member in role_object.members:
                        member_object = DiscordMember(member)
                        self.members.append(member_object)
            self.member_count = len(role_object.members)

        else:
            self.id = None
            self.name = None
            self.created_at = None
            self.color = None
            self.permissions = None
            self.members = []
            self.member_count = None

class DiscordInvite:
    def __init__(self, invite_object: discord.Invite):
        if invite_object:
            self.id = invite_object.id
            self.url = invite_object.url
            self.code = invite_object.code

            if invite_object.inviter:
                self.inviter = DiscordUser(invite_object.inviter.id)

            self.created_at = invite_object.created_at.strftime("%d/%m/%Y %H:%M:%S")

            self.temporary = invite_object.temporary
            if self.temporary:
                self.expires_at = invite_object.expires_at.strftime("%d/%m/%Y %H:%M:%S")
            else:
                self.expires_at = None

            self.approximate_member_count = invite_object.approximate_member_count
            self.approximate_presence_count = invite_object.approximate_presence_count

            self.max_age = invite_object.max_age
            self.max_uses = invite_object.max_uses
            self.uses = invite_object.uses
            self.revoked = invite_object.revoked

        else:
            self.id = None
            self.url = None
            self.code = None
            self.inviter = None
            self.created_at = None
            self.expires_at = None
            self.temporary = None
            self.approximate_member_count = None
            self.approximate_presence_count = None
            self.max_age = None
            self.max_uses = None
            self.uses = None
            self.revoked = None