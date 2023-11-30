import discord

from classes.data_classes import ReturnData, SlowedUser

from utils.log import log
from utils.translate import tg
from utils.save import save_json
from utils.globals import get_bot, get_languages_dict, get_session
from utils.checks import is_float
from utils.convert import to_bool

from database.guild import guild

from commands.utils import ctx_check

import sys
from discord.ext import commands as dc_commands
from typing import Union

async def announce_command_def(ctx, message: str, ephemeral: bool = False) -> ReturnData:
    """
    Announce message to all servers
    :param ctx: Context
    :param message: Message to announce
    :param ephemeral: Should bot response be ephemeral
    :return: ReturnData
    """
    log(ctx, 'announce_command_def', [message, ephemeral], log_type='function', author=ctx.author)
    for guild_object in get_bot().guilds:
        try:
            await guild_object.system_channel.send(message)
        except Exception as e:
            log(ctx, f"Error while announcing message to ({guild_object.name}): {e}", [guild_object.id, ephemeral],
                log_type='error', author=ctx.author)

    message = f'Announced message to all servers: `{message}`'
    await ctx.reply(message, ephemeral=ephemeral)
    return ReturnData(True, message)

async def kys_def(ctx: dc_commands.Context):
    log(ctx, 'kys_def', [], log_type='function', author=ctx.author)
    guild_id = ctx.guild.id
    await ctx.reply(tg(guild_id, "Committing seppuku..."))
    sys.exit(3)

async def options_def(ctx: dc_commands.Context, server: Union[str, int, None]=None, stopped: str = None, loop: str = None, is_radio: str = None,
                      buttons: str = None, language: str = None, response_type: str = None, buffer: str = None,
                      history_length: str = None, volume: str = None, search_query: str = None, last_updated: str = None,
                      ephemeral=True):
    log(ctx, 'options_def',
        [server, stopped, loop, is_radio, buttons, language, response_type, buffer, history_length, volume, search_query, last_updated, ephemeral],
        log_type='function', author=ctx.author)
    is_ctx, guild_id, author_id, guild_object = ctx_check(ctx)

    db_guild = guild(guild_id)

    if not server:
        options = guild(guild_id).options

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
            message = tg(guild_id, "That is not a **guild id!**")
            await ctx.reply(message, ephemeral=ephemeral)
            return ReturnData(False, message)

        if not server in db_guild.keys():
            message = tg(guild_id, "That guild doesn't exist or the bot is not in it")
            await ctx.reply(message, ephemeral=ephemeral)
            return ReturnData(False, message)

        guilds.append(server)

    for for_guild_id in guilds:
        options = guild(for_guild_id).options

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

        if language not in get_languages_dict() and language is not None and language != 'None':
            msg = f'language has to be: {get_languages_dict().keys()} --> {language}'
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

        save_json()

    message = tg(guild_id, f'Edited options successfully!')
    await ctx.reply(message, ephemeral=ephemeral)
    return ReturnData(True, message)


# Slow mode
async def slowed_users_command_def(ctx: dc_commands.Context):
    """
    Lists all slowed users
    :param ctx: Context
    """
    log(ctx, 'slowed_users', [], log_type='function', author=ctx.author)
    guild_id = ctx.guild.id
    slowed_users = guild(guild_id).slowed_users

    message = f"**Slowed users:**\n"
    for slowed_user in slowed_users:
        message += f"<@{slowed_user.user_id}> -> {slowed_user.slowed_for}\n"

    await ctx.reply(message)
    return ReturnData(True, message)

async def slowed_users_add_command_def(ctx: dc_commands.Context, member: discord.Member, slowed_for: int, ephemeral: bool=True):
    """
    Adds a slowed user
    :param ctx: Context
    :param member: Member object
    :param slowed_for: Time to slow the user for
    :param ephemeral: Should bot response be ephemeral
    """
    log(ctx, 'slowed_users_add', [member.id, slowed_for], log_type='function', author=ctx.author)
    guild_id = ctx.guild.id

    if slowed_for < 0:
        message = tg(guild_id, "Slowed time cannot be negative!")
        await ctx.reply(message, ephemeral=ephemeral)
        return ReturnData(False, message)

    slowed_user = SlowedUser(guild_id=guild_id, user_id=member.id, user_name=member.name, slowed_for=slowed_for)
    get_session().add(slowed_user)
    get_session().commit()

    message = f"Added slowed user: <@{member.id}> -> {slowed_for}"
    await ctx.reply(message, ephemeral=ephemeral)
    return ReturnData(True, message)