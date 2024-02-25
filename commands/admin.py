from classes.data_classes import ReturnData, SlowedUser, TorturedUser

from commands.utils import ctx_check

from database.guild import guild, is_user_tortured, delete_tortured_user

from utils.log import log
from utils.translate import text
from utils.save import update
from utils.checks import is_float
from utils.convert import to_bool
from utils.global_vars import languages_dict, GlobalVars

from discord.ext import commands as dc_commands
from typing import Union

import sys
import asyncio
import random
import discord


async def announce_command_def(ctx, glob: GlobalVars, message: str, ephemeral: bool = False) -> ReturnData:
    """
    Announce message to all servers
    :param glob: GlobalVars
    :param ctx: Context
    :param message: Message to announce
    :param ephemeral: Should bot response be ephemeral
    :return: ReturnData
    """
    log(ctx, 'announce_command_def', options=locals(), log_type='function', author=ctx.author)
    for guild_object in glob.bot.guilds:
        try:
            await guild_object.system_channel.send(message)
        except Exception as e:
            log(ctx, f"Error while announcing message to ({guild_object.name}): {e}", {'guild_id': guild_object.id, 'guild_name': guild_object.name, 'message': message, 'ephemeral': ephemeral}, log_type='error', author=ctx.author)

    message = f'Announced message to all servers: `{message}`'
    await ctx.reply(message, ephemeral=ephemeral)
    return ReturnData(True, message)

async def kys_def(ctx: dc_commands.Context, glob: GlobalVars):
    log(ctx, 'kys_def', options=locals(), log_type='function', author=ctx.author)
    guild_id = ctx.guild.id
    await ctx.reply(text(guild_id, glob, "Committing seppuku..."))
    sys.exit(3)

# noinspection DuplicatedCode
async def options_def(ctx: dc_commands.Context, glob: GlobalVars, server: Union[str, int, None]=None, stopped: str = None, loop: str = None, is_radio: str = None,
                      buttons: str = None, language: str = None, response_type: str = None, buffer: str = None,
                      history_length: str = None, volume: str = None, search_query: str = None, last_updated: str = None,
                      ephemeral=True):
    log(ctx, 'options_def', options=locals(), log_type='function', author=ctx.author)
    is_ctx, guild_id, author_id, guild_object = ctx_check(ctx, glob)

    db_guild = guild(glob, guild_id)

    if not server:
        options = db_guild.options

        message = f"""
        **Options:**
        stopped -> `{options.stopped}`
        loop -> `{options.loop}`
        is_radio -> `{options.is_radio}`
        buttons -> `{options.buttons}`
        language -> `{options.language}`
        response_type -> `{options.response_type}`
        buffer -> `{options.buffer}`
        history_length -> `{options.history_length}`
        volume -> `{options.volume}`
        search_query -> `{options.search_query}`
        last_updated -> `{options.last_updated}`
        """

        await ctx.reply(message, ephemeral=ephemeral)
        return ReturnData(True, message)

    guilds = []

    if server == 'this':
        guilds.append(guild_id)

    elif server == 'all':
        for guild_id in db_guild.keys():
            guilds.append(guild_id)

    else:
        try:
            server = int(server)
        except (ValueError, TypeError):
            message = text(guild_id, glob, "That is not a **guild id!**")
            await ctx.reply(message, ephemeral=ephemeral)
            return ReturnData(False, message)

        if server not in db_guild.keys():
            message = text(guild_id, glob, "That guild doesn't exist or the bot is not in it")
            await ctx.reply(message, ephemeral=ephemeral)
            return ReturnData(False, message)

        guilds.append(server)

    for for_guild_id in guilds:
        options = guild(glob, for_guild_id).options

        bool_list_t = ['True', 'true', '1']
        bool_list_f = ['False', 'false', '0']
        bool_list = bool_list_f + bool_list_t
        response_types = ['long', 'short']

        if stopped not in bool_list and stopped is not None and stopped != 'None':
            msg = f'stopped has to be: {bool_list} --> {stopped}'
            await ctx.reply(msg, ephemeral=ephemeral)
            return ReturnData(False, msg)
        if loop not in bool_list and loop is not None and loop != 'None':
            msg = f'loop has to be: {bool_list} --> {loop}'
            await ctx.reply(msg, ephemeral=ephemeral)
            return ReturnData(False, msg)
        if is_radio not in bool_list and is_radio is not None and is_radio != 'None':
            msg = f'is_radio has to be: {bool_list} --> {is_radio}'
            await ctx.reply(msg, ephemeral=ephemeral)
            return ReturnData(False, msg)
        if buttons not in bool_list and buttons is not None and buttons != 'None':
            msg = f'buttons has to be: {bool_list} --> {buttons}'
            await ctx.reply(msg, ephemeral=ephemeral)
            return ReturnData(False, msg)

        if response_type not in response_types and response_type is not None and response_type != 'None':
            msg = f'response_type has to be: {response_types} --> {response_type}'
            await ctx.reply(msg, ephemeral=ephemeral)
            return ReturnData(False, msg)

        if language not in languages_dict() and language is not None and language != 'None':
            msg = f'language has to be: {languages_dict().keys()} --> {language}'
            await ctx.reply(msg, ephemeral=ephemeral)
            return ReturnData(False, msg)

        if not is_float(volume) and volume is not None and volume != 'None':
            msg = f'volume has to be a number: {volume}'
            await ctx.reply(msg, ephemeral=ephemeral)
            return ReturnData(False, msg)
        if not buffer.isdigit() and buffer is not None and buffer != 'None':
            msg = f'buffer has to be a number: {buffer}'
            await ctx.reply(msg, ephemeral=ephemeral)
            return ReturnData(False, msg)
        if not history_length.isdigit() and history_length is not None and history_length != 'None':
            msg = f'history_length has to be a number: {history_length}'
            await ctx.reply(msg, ephemeral=ephemeral)
            return ReturnData(False, msg)
        if not last_updated.isdigit() and last_updated is not None and last_updated != 'None':
            msg = f'last_updated has to be a number: {last_updated}'
            await ctx.reply(msg, ephemeral=ephemeral)
            return ReturnData(False, msg)

        if stopped is not None and stopped != 'None':
            options.stopped = to_bool(stopped)
        if loop is not None and loop != 'None':
            options.loop = to_bool(loop)
        if is_radio is not None and is_radio != 'None':
            options.is_radio = to_bool(is_radio)
        if buttons is not None and buttons != 'None':
            options.buttons = to_bool(buttons)

        if language is not None and language != 'None':
            options.language = language
        if search_query is not None and search_query != 'None':
            options.search_query = search_query
        if response_type is not None and response_type != 'None':
            options.response_type = response_type

        if volume is not None and volume != 'None':
            options.volume = float(int(volume) / 100)
        if buffer is not None and buffer != 'None':
            options.buffer = int(buffer)
        if history_length is not None and history_length != 'None':
            options.history_length = int(history_length)
        if last_updated is not None and last_updated != 'None':
            options.last_updated = int(last_updated)

        update(glob)

    message = text(guild_id, glob, f'Edited options successfully!')
    await ctx.reply(message, ephemeral=ephemeral)
    return ReturnData(True, message)


# Slow mode
async def slowed_users_command_def(ctx: dc_commands.Context, glob: GlobalVars, guild_id: int=0, list_all: bool=False, ephemeral: bool=True):
    """
    Lists all slowed users
    :param ctx: Context
    :param glob: GlobalVars
    :param guild_id: Guild id - 0 for current guild
    :param list_all: List all slowed users and their guilds
    :param ephemeral: Should bot response be ephemeral
    """
    log(ctx, 'slowed_users', options=locals(), log_type='function', author=ctx.author)
    guild_id = ctx.guild.id if guild_id == 0 else guild_id

    if list_all:
        slowed_users = glob.ses.query(SlowedUser).all()
        if slowed_users is None:
            message = text(guild_id, glob, "There are no slowed users!")
            await ctx.reply(message, ephemeral=ephemeral)
            return ReturnData(False, message)

        message = f"**Slowed users:**\n"
        for slowed_user in slowed_users:
            message += f"> <@{slowed_user.user_id}> -> {slowed_user.slowed_for} ({slowed_user.guild_id})\n"

        await ctx.reply(message, ephemeral=ephemeral)
        return ReturnData(True, message)

    slowed_users = guild(glob, guild_id).slowed_users

    message = f"**Slowed users:**\n"
    for slowed_user in slowed_users:
        message += f"> <@{slowed_user.user_id}> -> {slowed_user.slowed_for}\n"

    await ctx.reply(message, ephemeral=ephemeral)
    return ReturnData(True, message)

async def slowed_users_add_command_def(ctx: dc_commands.Context, glob: GlobalVars, member: discord.Member, slowed_for: int, guild_id: int=0, ephemeral: bool=True):
    """
    Adds a slowed user
    :param ctx: Context
    :param glob: GlobalVars
    :param member: Member object
    :param slowed_for: Time to slow the user for
    :param guild_id: Guild id - 0 for current guild
    :param ephemeral: Should bot response be ephemeral
    """
    log(ctx, 'slowed_users_add', options=locals(), log_type='function', author=ctx.author)
    guild_id = ctx.guild.id if guild_id == 0 else guild_id

    if slowed_for < 0:
        message = text(guild_id, glob, "Slowed time cannot be negative!")
        await ctx.reply(message, ephemeral=ephemeral)
        return ReturnData(False, message)

    slowed_user = SlowedUser(guild_id=guild_id, user_id=member.id, user_name=member.name, slowed_for=slowed_for)
    with glob.ses.no_autoflush:
        glob.ses.add(slowed_user)
        glob.ses.commit()

    message = f"{text(guild_id, glob, 'Added slowed user:')} <@{member.id}> -> {slowed_for}"
    await ctx.reply(message, ephemeral=ephemeral)
    return ReturnData(True, message)

async def slowed_users_add_all_command_def(ctx: dc_commands.Context, glob: GlobalVars, guild_obj: discord.Guild, slowed_for: int, guild_id: int=0, ephemeral: bool=True):
    """
    Adds all users in a guild to the slowed users list
    :param glob: GlobalVars
    :param ctx: Context
    :param guild_obj: Guild object
    :param slowed_for: Time to slow the user for
    :param guild_id: Guild id - 0 for current guild
    :param ephemeral: Should bot response be ephemeral
    """
    log(ctx, 'slowed_users_add_all',
        options={'ctx': ctx, 'glob': glob, 'guild_obj': guild_obj.id, 'slowed_for': slowed_for, 'ephemeral': ephemeral},
        log_type='function', author=ctx.author)
    guild_id = ctx.guild.id if guild_id == 0 else guild_id

    if slowed_for < 0:
        message = text(guild_id, glob, "Slowed time cannot be negative!")
        await ctx.reply(message, ephemeral=ephemeral)
        return ReturnData(False, message)

    slowed_users = []
    for member in guild_obj.members:
        slowed_user = SlowedUser(guild_id=guild_obj.id, user_id=member.id, user_name=member.name, slowed_for=slowed_for)
        slowed_users.append(slowed_user)

    with glob.ses.no_autoflush:
        glob.ses.add_all(slowed_users)
        glob.ses.commit()

    message = f"{text(guild_id, glob, 'Added slowed users:')} {len(slowed_users)}"
    await ctx.reply(message, ephemeral=ephemeral)
    return ReturnData(True, message)

async def slowed_users_remove_command_def(ctx: dc_commands.Context, glob: GlobalVars, member: discord.Member, guild_id: int=0, ephemeral: bool=True):
    """
    Removes a slowed user
    :param glob: GlobalVars
    :param ctx: Context
    :param member: Member object
    :param guild_id: Guild id - 0 for current guild
    :param ephemeral: Should bot response be ephemeral
    """
    log(ctx, 'slowed_users_remove', {'ctx': ctx, 'glob': glob, 'member': member.id, 'ephemeral': ephemeral}, log_type='function', author=ctx.author)
    guild_id = ctx.guild.id if guild_id == 0 else guild_id

    slowed_user = glob.ses.query(SlowedUser).filter_by(user_id=member.id, guild_id=guild_id).first()
    if slowed_user is None:
        message = text(guild_id, glob, "That user is not slowed!")
        await ctx.reply(message, ephemeral=ephemeral)
        return ReturnData(False, message)

    with glob.ses.no_autoflush:
        glob.ses.delete(slowed_user)
        glob.ses.commit()

    message = f"{text(guild_id, glob, 'Removed slowed user:')} <@{member.id}>"
    await ctx.reply(message, ephemeral=ephemeral)
    return ReturnData(True, message)

async def slowed_users_remove_all_command_def(ctx: dc_commands.Context, glob: GlobalVars, guild_obj: discord.Guild, guild_id: int=0, ephemeral: bool=True):
    """
    Removes all slowed users in a guild
    :param glob: GlobalVars
    :param ctx: Context
    :param guild_obj: Guild object
    :param guild_id: Guild id - 0 for current guild
    :param ephemeral: Should bot response be ephemeral
    """
    log(ctx, 'slowed_users_remove_all', options=locals(), log_type='function', author=ctx.author)
    guild_id = ctx.guild.id if guild_id == 0 else guild_id

    slowed_users = glob.ses.query(SlowedUser).filter_by(guild_id=guild_obj.id).all()
    if slowed_users is None:
        message = text(guild_id, glob, "There are no slowed users!")
        await ctx.reply(message, ephemeral=ephemeral)
        return ReturnData(False, message)

    with glob.ses.no_autoflush:
        for slowed_user in slowed_users:
            glob.ses.delete(slowed_user)
        glob.ses.commit()

    message = f"{text(guild_id, glob, 'Removed slowed users:')} {len(slowed_users)}"
    await ctx.reply(message, ephemeral=ephemeral)
    return ReturnData(True, message)

# Torture
async def voice_torture_command_def(ctx: dc_commands.Context, glob: GlobalVars, member: discord.Member, delay: int, guild_id: int=0, ephemeral: bool=True):
    """
    Keeps swapping the user between voice channels with n second delay
    :param glob: GlobalVars
    :param ctx: Context
    :param member: Member object
    :param delay: Time to torture the user for
    :param guild_id: Guild id - 0 for current guild
    :param ephemeral: Should bot response be ephemeral
    """
    log(ctx, 'voice_torture', {'ctx': ctx, 'glob': glob, 'member': member.id, 'delay': delay, 'ephemeral': ephemeral},
        log_type='function', author=ctx.author)
    guild_id = ctx.guild.id if guild_id == 0 else guild_id

    if delay < 0:
        message = text(guild_id, glob, "Time cannot be negative!")
        await ctx.reply(message, ephemeral=ephemeral)
        return ReturnData(False, message)

    if member.voice is None:
        message = text(guild_id, glob, "That user is not in a voice channel!")
        await ctx.reply(message, ephemeral=ephemeral)
        return ReturnData(False, message)

    voice_channels = ctx.guild.voice_channels
    if len(voice_channels) < 2:
        message = text(guild_id, glob, "There are not enough voice channels to torture!")
        await ctx.reply(message, ephemeral=ephemeral)
        return ReturnData(False, message)

    tu = glob.ses.query(TorturedUser).filter_by(user_id=member.id, guild_id=guild_id).first()
    if tu is not None:
        tu.torture_delay = delay
        glob.ses.commit()
        message = f"{text(guild_id, glob, 'Updated torture delay for user:')} <@{member.id}> -> {delay}"
        await ctx.reply(message, ephemeral=ephemeral)
        return ReturnData(True, message)
    glob.ses.add(TorturedUser(guild_id=guild_id, user_id=member.id, torture_delay=delay))
    glob.ses.commit()

    message = f"{text(guild_id, glob, 'Torturing user:')} <@{member.id}> -> {delay}"
    await ctx.reply(message, ephemeral=ephemeral)

    while True:
        is_tortured, delay = is_user_tortured(glob, member.id, guild_id)
        if not is_tortured:
            delete_tortured_user(glob, member.id, guild_id)

            message = text(guild_id, glob, "That user is not being tortured!")
            await ctx.reply(message, ephemeral=ephemeral)
            return ReturnData(False, message)

        await asyncio.sleep(delay)

        if member.voice is None:
            delete_tortured_user(glob, member.id, guild_id)

            message = text(guild_id, glob, "That user is not in a voice channel!")
            await ctx.reply(message, ephemeral=ephemeral)
            return ReturnData(False, message)
        if member.voice.channel is None:
            delete_tortured_user(glob, member.id, guild_id)

            message = text(guild_id, glob, "That user is not in a voice channel!")
            await ctx.reply(message, ephemeral=ephemeral)
            return ReturnData(False, message)
        if member.voice.channel == ctx.guild.afk_channel:
            delete_tortured_user(glob, member.id, guild_id)

            message = text(guild_id, glob, "That user is in the AFK channel!")
            await ctx.reply(message, ephemeral=ephemeral)
            return ReturnData(False, message)

        random_channel = random.choice([channel for channel in voice_channels if channel != member.voice.channel])
        try:
            await member.move_to(random_channel)
        except discord.Forbidden:
            message = text(guild_id, glob, "I don't have permission to move that user!")
            await ctx.reply(message, ephemeral=ephemeral)
            return ReturnData(False, message)

async def voice_torture_stop_command_def(ctx: dc_commands.Context, glob: GlobalVars, member: discord.Member, guild_id: int=0, ephemeral: bool=True):
    """
    Stops torturing the user
    :param glob: GlobalVars
    :param ctx: Context
    :param member: Member object
    :param guild_id: Guild id - 0 for current guild
    :param ephemeral: Should bot response be ephemeral
    """
    log(ctx, 'voice_torture_stop', {'ctx': ctx, 'glob': glob, 'member': member.id, 'ephemeral': ephemeral}, log_type='function', author=ctx.author)
    guild_id = ctx.guild.id if guild_id == 0 else guild_id

    tortured_user = glob.ses.query(TorturedUser).filter_by(user_id=member.id, guild_id=guild_id).first()
    if tortured_user is None:
        message = text(guild_id, glob, "That user is not being tortured!")
        await ctx.reply(message, ephemeral=ephemeral)
        return ReturnData(False, message)

    with glob.ses.no_autoflush:
        glob.ses.delete(tortured_user)
        glob.ses.commit()

    message = f"{text(guild_id, glob, 'Stopped torturing user:')} <@{member.id}>"
    await ctx.reply(message, ephemeral=ephemeral)
    return ReturnData(True, message)
