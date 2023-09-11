from classes.data_classes import ReturnData

from utils.log import log
from utils.translate import tg
from utils.save import save_json
from utils.globals import get_bot, get_languages_dict, get_guild_dict
from utils.json import json_to_guilds
from utils.checks import is_float
from utils.convert import to_bool

from commands.utils import ctx_check

import discord
import sys
import json
from os import path
from discord.ext import commands as dc_commands
from typing import Literal, Union

import config

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

async def file_command_def(ctx: dc_commands.Context, config_file: discord.Attachment = None, config_type: Literal[
    'guilds', 'other', 'radio', 'languages', 'log', 'data', 'activity', 'apache_activity', 'apache_error'] = 'log'):
    log(ctx, 'config_command_def', [config_file, config_type], log_type='function', author=ctx.author)

    config_types = {
        'guilds': '.json',
        'other': '.json',
        'radio': '.json',
        'languages': '.json',
        'saves': '.json',
        'log': '.log',
        'data': '.log',
        'activity': '.log',
        'apache_activity': '.log',
        'apache_error': '.log'
    }

    if config_type in ['guilds', 'other', 'languages', 'radio', 'saves']:
        file_path = f'{config.PARENT_DIR}db/{config_type}{config_types[config_type]}'
    else:
        file_path = f'{config.PARENT_DIR}db/log/{config_type}{config_types[config_type]}'

    if config_file is None:
        if not path.exists(file_path):
            message = f'File `{config_type}{config_types[config_type]}` does not exist'
            await ctx.reply(message, ephemeral=True)
            return ReturnData(False, message)

        file_to_send = discord.File(file_path, filename=f"{config_type}{config_types[config_type]}")
        await ctx.reply(file=file_to_send)
        return ReturnData(True, f"Sent file: `{config_type}{config_types[config_type]}`")

    filename = config_file.filename
    file_name_list = filename.split('.')
    filename_type = '.' + file_name_list[-1]
    file_name_list.pop(-1)
    filename_name = '.'.join(file_name_list)

    if not filename_type in config_types.values():
        message = 'You need to upload a `.json` or `.log` file'
        await ctx.reply(message, ephemeral=True)
        return ReturnData(False, message)

    if not filename_name in config_types.keys():
        message = 'You need to upload a file with a valid name (guilds, other, radio, languages, saves, log, data, activity, apache_activity, apache_error)'
        await ctx.reply(message, ephemeral=True)
        return ReturnData(False, message)

    if filename_name in config_types.keys() and filename_name != config_type:
        config_type = filename_name

    # read file
    content = await config_file.read()
    if not content:
        message = f"no content in file: `{file_path}`"
        await ctx.reply(message, ephemeral=True)
        return ReturnData(False, message)

    # get original content
    with open(file_path, 'rb', encoding='utf-8') as f:
        org_content = f.read()

    if config_type == 'guilds':
        try:
            json_to_guilds(json.loads(content))
        except Exception as e:
            message = f'This file might be outdated or corrupted: `{config_type}{config_types[config_type]}` -> {e}'
            log(ctx, message, [config_type, config_types[config_type]], log_type='error', author=ctx.author)
            await ctx.reply(message, ephemeral=True)
            return ReturnData(False, message)

    with open(file_path, 'wb', encoding='utf-8') as f:
        try:
            # write new content
            f.write(content)
        except Exception as e:
            # write original content back if error
            f.write(org_content)
            # send error message
            message = f"Error while saving file: {e}"
            log(ctx, message, [config_type, config_types[config_type]], log_type='error', author=ctx.author)
            await ctx.reply(message, ephemeral=True)
            return ReturnData(False, message)

    if config_type == 'guilds':
        with open('db/guilds.json', 'r', encoding='utf-8') as f:
            try:
                globals()['guild'] = json_to_guilds(json.load(f))
            except Exception as e:
                message = f'This file might be outdated or corrupted: `{config_type}{config_types[config_type]}` -> {e}'
                log(ctx, message, [config_type, config_types[config_type]], log_type='error', author=ctx.author)
                await ctx.reply(message, ephemeral=True)
                return ReturnData(False, message)

        log(None, 'Loaded guilds.json')
        await ctx.reply("Loaded new `guilds.json`", ephemeral=True)
    else:
        await ctx.reply(f"Saved new `{config_type}{config_types[config_type]}`", ephemeral=True)

async def options_def(ctx: dc_commands.Context, server: Union[str, int, None]=None, stopped: str = None, loop: str = None, is_radio: str = None,
                      buttons: str = None, language: str = None, response_type: str = None, buffer: str = None,
                      history_length: str = None, volume: str = None, search_query: str = None, last_updated: str = None,
                      ephemeral=True):
    log(ctx, 'options_def',
        [server, stopped, loop, is_radio, buttons, language, response_type, buffer, history_length, volume, search_query, last_updated, ephemeral],
        log_type='function', author=ctx.author)
    is_ctx, guild_id, author_id, guild_object = ctx_check(ctx)
    guild = get_guild_dict()

    if not server:
        options = guild[guild_id].options

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
        for guild_id in guild.keys():
            guilds.append(guild_id)

    else:
        try:
            server = int(server)
        except (ValueError, TypeError):
            message = tg(guild_id, "That is not a **guild id!**")
            await ctx.reply(message, ephemeral=ephemeral)
            return ReturnData(False, message)

        if not server in guild.keys():
            message = tg(guild_id, "That guild doesn't exist or the bot is not in it")
            await ctx.reply(message, ephemeral=ephemeral)
            return ReturnData(False, message)

        guilds.append(server)

    for for_guild_id in guilds:
        options = guild[for_guild_id].options

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