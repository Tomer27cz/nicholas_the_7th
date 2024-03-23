from classes.data_classes import ReturnData
from classes.discord_classes import DiscordChannel

from commands.utils import ctx_check

from utils.log import log
from utils.translate import txt
from utils.cli import execute
from utils.global_vars import GlobalVars

from os import path, makedirs, listdir
import asyncio
import subprocess
import discord
import json

import config

async def save_channel_info_to_file(glob: GlobalVars, guild_id: int, file_path) -> ReturnData:
    """
    Saves all channels of a guild to a json file
    :type glob: GlobalVars
    :param guild_id: ID of the guild
    :param file_path: Path of the resulting json file
    :return: ReturnData
    """
    log(None, 'save_channel_info_to_file', options=locals(), log_type='function')

    guild_object = glob.bot.get_guild(guild_id)
    if not guild_object:
        return ReturnData(False, f'Guild ({guild_id}) not found')

    channels = guild_object.text_channels
    channels_dict = {}
    for channel in channels:
        channels_dict[int(channel.id)] = DiscordChannel(glob, channel.id, no_members=True).__dict__

    file_path_rel = f'{file_path}/channels.json'
    makedirs(path.dirname(file_path_rel), exist_ok=True)

    with open(file_path_rel, 'w', encoding='utf-8') as f:
        f.write(json.dumps(channels_dict, indent=4))

    return ReturnData(True, f'Saved channels of ({guild_id}) to file')

async def download_guild_channel(ctx, glob, channel_id: int, mute_response: bool=False, ephemeral: bool=True):
    log(ctx, 'download_guild_channel', options=locals(), log_type='function')
    is_ctx, ctx_guild_id, author, ctx_guild_object = ctx_check(ctx, glob)
    try:
        channel_id = int(channel_id)
    except (ValueError, TypeError):
        message = f'({channel_id}) ' + txt(ctx_guild_id, glob, 'is not an id')
        if not mute_response:
            await ctx.reply(message, ephemeral=ephemeral)
        return ReturnData(False, message)

    channel_object = glob.bot.get_channel(channel_id)
    if not channel_object:
        message = f'Channel ({channel_id}) is not accessible'
        if not mute_response:
            await ctx.reply(message, ephemeral=ephemeral)
        return ReturnData(False, message)

    guild_id = channel_object.guild.id
    response = await save_channel_info_to_file(glob, guild_id, f'{config.PARENT_DIR}db/guilds/{guild_id}')
    if not response.response:
        message = txt(ctx_guild_id, glob, f'Error while saving channel info to file') + ': {response.message}'
        if not mute_response:
            await ctx.reply(message, ephemeral=ephemeral)
        return ReturnData(False, message)

    rel_path = f'{config.PARENT_DIR}dce/DiscordChatExporter.Cli.dll'
    output_file_path = f'{config.PARENT_DIR}db/guilds/%g/%c/file.html'
    command = f'dotnet "{rel_path}" export -c {channel_id} -t {config.BOT_TOKEN} -o "{output_file_path}" -p 1mb --dateformat "dd/MM/yyyy HH:mm:ss"'

    log(ctx, f'download_guild_channel -> executing command: {command}')
    msg = f'Guild channel ({channel_id}) will be downloaded'
    org_msg = await ctx.reply(msg, ephemeral=ephemeral)

    try:
        asyncio.run_coroutine_threadsafe(execute(command), glob.bot.loop)
        # for path_output in execute(command):
        #     print(path_output)
    except subprocess.CalledProcessError as e:
        message = txt(ctx_guild_id, glob, f'Command raised an error') + ": " + str(e)
        if not mute_response and is_ctx:
            await org_msg.edit(content=message)
        return ReturnData(False, message)

    return ReturnData(True, msg)

async def download_guild(ctx, glob: GlobalVars, guild_id: int, mute_response: bool=False, ephemeral: bool=True):
    log(ctx, 'download_guild', options=locals(), log_type='function')
    is_ctx, ctx_guild_id, author, ctx_guild_object = ctx_check(ctx, glob)
    try:
        guild_id = int(guild_id)
    except (ValueError, TypeError):
        message = f'({guild_id}) ' + txt(ctx_guild_id, glob, 'is not an id')
        if not mute_response:
            await ctx.reply(message, ephemeral=ephemeral)
        return ReturnData(False, message)

    guild_object = glob.bot.get_guild(guild_id)
    if not guild_object:
        message = f'Guild ({guild_id}) ' + txt(ctx_guild_id, glob, 'is not accessible')
        if not mute_response:
            await ctx.reply(message, ephemeral=ephemeral)
        return ReturnData(False, message)

    guild_id = guild_object.id
    response = await save_channel_info_to_file(glob, guild_id, f'{config.PARENT_DIR}db/guilds/{guild_id}')
    if not response.response:
        message = txt(ctx_guild_id, glob, f'Error while saving channel info to file') + ":" + response.message
        if not mute_response:
            await ctx.reply(message, ephemeral=ephemeral)
        return ReturnData(False, message)

    rel_path = f'{config.PARENT_DIR}dce/DiscordChatExporter.Cli.dll'
    output_file_path = f'{config.PARENT_DIR}db/guilds/%g/%c/file.html'
    command = f'dotnet "{rel_path}" exportguild -g {guild_id} -t {config.BOT_TOKEN} -o "{output_file_path}" -p 1mb --dateformat "dd/MM/yyyy HH:mm:ss"'

    log(ctx, f'download_guild_channel -> executing command: {command}')
    msg = f'Guild ({guild_id}) will be downloaded (can take more than 1min depending on the size)'
    org_msg = await ctx.reply(msg, ephemeral=ephemeral)

    try:
        asyncio.run_coroutine_threadsafe(execute(command), glob.bot.loop)
        # for path_output in execute(command):
        #     print(path_output)
    except subprocess.CalledProcessError as e:
        log(ctx, f'download_guild_channel -> error: {e}')
        message = txt(ctx_guild_id, glob, f'Command raised an error')
        if not mute_response and is_ctx:
            await org_msg.edit(content=message)
        return ReturnData(False, message)

    return ReturnData(True, msg)

async def get_guild_channel(ctx, glob: GlobalVars, channel_id: int, mute_response: bool=False, guild_id=None, ephemeral: bool=True):
    log(ctx, 'get_guild_channel', options=locals(), log_type='function')
    is_ctx, ctx_guild_id, author, ctx_guild_object = ctx_check(ctx, glob)

    try:
        channel_id = int(channel_id)
    except (ValueError, TypeError):
        message = f'({channel_id}) ' + txt(ctx_guild_id, glob, 'is not an id')
        if not mute_response:
            await ctx.reply(message, ephemeral=ephemeral)
        return ReturnData(False, message)

    if is_ctx:
        if not ctx.interaction.response.is_done():
            await ctx.defer(ephemeral=ephemeral)

    channel_object = glob.bot.get_channel(channel_id)
    channel_name = guild_id
    if channel_object:
        guild_id = channel_object.guild.id
        channel_name = channel_object.name

    path_of_folder = f'{config.PARENT_DIR}db/guilds/{guild_id}/{channel_id}'

    if not path.exists(path_of_folder):
        message = f'Channel ({channel_id}) has not been downloaded'
        if not mute_response:
            await ctx.reply(message, ephemeral=ephemeral)
        return ReturnData(False, message)

    try:
        files_in_folder = listdir(path_of_folder)

        files_to_send = []
        for file_name in files_in_folder:
            files_to_send.append(discord.File(f'{path_of_folder}/{file_name}'))
    except (FileNotFoundError, PermissionError) as e:
        message = f'Channel ({channel_id}) has not yet been downloaded or an error occurred: {e}'
        if not mute_response:
            await ctx.reply(message, ephemeral=ephemeral)
        return ReturnData(False, message)

    await ctx.reply(files=files_to_send, content=f'Channel: {channel_name}', ephemeral=ephemeral)
    return ReturnData(True, 'files sent')

async def get_guild(ctx, glob: GlobalVars, guild_id: int, mute_response: bool=False, ephemeral: bool=True):
    log(ctx, 'get_guild', options=locals(), log_type='function')
    is_ctx, ctx_guild_id, author, ctx_guild_object = ctx_check(ctx, glob)
    try:
        guild_id = int(guild_id)
    except (ValueError, TypeError):
        message = f'({guild_id}) ' + txt(ctx_guild_id, glob, 'is not an id')
        if not mute_response:
            await ctx.reply(message, ephemeral=ephemeral)
        return ReturnData(False, message)

    if is_ctx:
        if not ctx.interaction.response.is_done():
            await ctx.defer(ephemeral=ephemeral)

    path_of_folder = f'{config.PARENT_DIR}db/guilds/{guild_id}'

    if not path.exists(path_of_folder):
        message = f'Guild ({guild_id}) has not been downloaded'
        if not mute_response:
            await ctx.reply(message, ephemeral=ephemeral)
        return ReturnData(False, message)

    try:
        channels_in_folder = listdir(path_of_folder)
        for channel in channels_in_folder:
            await get_guild_channel(ctx, glob, channel_id=int(channel), mute_response=mute_response, ephemeral=ephemeral, guild_id=guild_id)
    except (FileNotFoundError, PermissionError) as e:
        message = f'Guild ({guild_id}) has not yet been downloaded or an error occurred: {e}'
        if not mute_response:
            await ctx.reply(message, ephemeral=ephemeral)
        return ReturnData(False, message)

    return ReturnData(True, 'files sent')
