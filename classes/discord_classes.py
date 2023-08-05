from utils.globals import get_bot
from vars import default_discord_avatar

import discord
import asyncio
import chat_exporter

class DiscordUser:
    def __init__(self, user_id: int):
        bot = get_bot()
        user_object = bot.get_user(user_id)

        if user_object:
            self.name = user_object.name
            self.id = user_object.id
            self.discriminator = user_object.discriminator
            if user_object.avatar:
                self.avatar = user_object.avatar.url
            else:
                self.avatar = default_discord_avatar
            self.bot = user_object.bot
            self.created_at = user_object.created_at.strftime("%d/%m/%Y %H:%M:%S")
            self.display_name = user_object.display_name

        else:
            self.name = None
            self.id = None
            self.discriminator = None
            self.avatar = None
            self.bot = None
            self.created_at = None
            self.display_name = None
            self.status = None

class DiscordMember:
    def __init__(self, member_object: discord.Member):
        self.name = member_object.name
        self.id = member_object.id
        self.discriminator = member_object.discriminator
        if member_object.avatar:
            self.avatar = member_object.avatar.url
        else:
            self.avatar = default_discord_avatar
        self.bot = member_object.bot
        self.created_at = member_object.created_at.strftime("%d/%m/%Y %H:%M:%S")
        self.status = member_object.status.__str__()
        self.joined_at = member_object.joined_at.strftime("%d/%m/%Y %H:%M:%S")

class DiscordChannel:
    def __init__(self, channel_id: int, no_members=False):
        self.id = channel_id
        self.name = None
        self.created_at = None
        self.members = []
        self.html = None

        bot = get_bot()
        channel_object = bot.get_channel(channel_id)

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

    async def get_first_messages(self, num_of_messages: int):
        """
        Gets the first messages of a channel
        :param num_of_messages: Number of messages to get
        :return: ReturnData object
        """
        async def get_messages(ch_obj, num):
            msg_list = [message_object async for message_object in ch_obj.history(limit=num)]
            return msg_list

        bot = get_bot()
        channel_object = bot.get_channel(self.id)
        if not channel_object:
            return None
        if not channel_object.permissions_for(channel_object.guild.me).read_message_history:
            return None

        messages = asyncio.run_coroutine_threadsafe(get_messages(channel_object, num_of_messages), bot.loop).result()

        transcript = asyncio.run_coroutine_threadsafe(chat_exporter.raw_export(channel=channel_object,
                                                                               messages=messages,
                                                                               tz_info='GMT',
                                                                               guild=channel_object.guild,
                                                                               bot=bot,
                                                                               military_time=True,
                                                                               support_dev=False), bot.loop).result()
        self.html = transcript

        return self.html

class DiscordRole:
    def __init__(self, role_id: int, guild_id: int):
        bot = get_bot()
        role_object = bot.get_guild(guild_id).get_role(role_id)

        if role_object:
            self.id = role_object.id
            self.name = role_object.name
            self.created_at = role_object.created_at.strftime("%d/%m/%Y %H:%M:%S")
            self.color = role_object.color
            self.permissions = role_object.permissions

            self.members = []
            if role_object.members:
                for member in role_object.members:
                    member_object = DiscordMember(member)
                    self.members.append(member_object)

        else:
            self.id = None
            self.name = None
            self.created_at = None
            self.color = None
            self.permissions = None
            self.members = []

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