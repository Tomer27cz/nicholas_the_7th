from classes.data_classes import ReturnData, SlowedUser, TorturedUser, TimeLog, Guild
from classes.typed_dictionaries import DBData

from commands.utils import ctx_check

from database.guild import guild, is_user_tortured, delete_tortured_user, guild_ids

from utils.log import log
from utils.translate import txt
from utils.save import update, push_update
from utils.convert import to_bool, struct_to_time, convert_duration_long
from utils.global_vars import languages_dict, GlobalVars
from utils.discord import guilds_get_connected_status, get_guild_bot_status
from utils.stats import db_data

from discord.ext import commands as dc_commands
from typing import Union

import sys
import asyncio
import random
import discord
import time
import psutil
import cpuinfo
import requests

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
    await ctx.reply(txt(guild_id, glob, "Committing seppuku..."))
    sys.exit(3)

# noinspection DuplicatedCode
async def options_def(ctx: dc_commands.Context, glob: GlobalVars,
                      server: Union[str, int, None]=None,
                      stopped: str = None,
                      loop: str = None,
                      is_radio: str = None,
                      buttons: str = None,
                      language: str = None,
                      response_type: str = None,
                      buffer: str = None,
                      history_length: str = None,
                      volume: str = None,
                      search_query: str = None,
                      ephemeral=True
                      ):
    log(ctx, 'options_def', options=locals(), log_type='function', author=ctx.author)
    is_ctx, guild_id, author, guild_object = ctx_check(ctx, glob)

    guilds_to_change = []
    if server is None:
        pass

    elif server == 'this':
        guilds_to_change.append(guild_id)

    elif server == 'all':
        for _guild_id in guild_ids(glob):
            guilds_to_change.append(_guild_id)

    else:
        try:
            server = int(server)
        except (ValueError, TypeError):
            message = txt(guild_id, glob, "That is not a **guild id!**")
            await ctx.reply(message, ephemeral=ephemeral)
            return ReturnData(False, message)

        if server not in guild_ids(glob):
            message = txt(guild_id, glob, "That guild doesn't exist or the bot is not in it")
            await ctx.reply(message, ephemeral=ephemeral)
            return ReturnData(False, message)

        guilds_to_change.append(server)

    for for_guild_id in guilds_to_change:
        options = guild(glob, for_guild_id).options

        bool_list_t = ['True', 'true', '1']
        bool_list_f = ['False', 'false', '0']
        bool_list = bool_list_f + bool_list_t

        response_types = ['long', 'short']

        def check_none(value):
            if value == 'None':
                return None
            return value

        stopped = check_none(stopped)
        loop = check_none(loop)
        is_radio = check_none(is_radio)
        buttons = check_none(buttons)
        language = check_none(language)
        response_type = check_none(response_type)
        buffer = check_none(buffer)
        history_length = check_none(history_length)
        volume = check_none(volume)
        search_query = check_none(search_query)

        async def bool_check(value):
            if value is None:
                return ReturnData(True, 'value is None')

            if value not in bool_list:
                _msg = f'{value.__name__} has to be: {bool_list} --> {value}'
                await ctx.reply(_msg, ephemeral=ephemeral)
                return ReturnData(False, _msg)

            return ReturnData(True, 'value is ok')

        stopped_check = await bool_check(stopped)
        if not stopped_check.response:
            return stopped_check

        loop_check = await bool_check(loop)
        if not loop_check.response:
            return loop_check

        is_radio_check = await bool_check(is_radio)
        if not is_radio_check.response:
            return is_radio_check

        buttons_check = await bool_check(buttons)
        if not buttons_check.response:
            return buttons_check

        async def is_resp_type(value):
            if value is None:
                return ReturnData(True, 'value is None')

            if value not in response_types:
                _msg = f'{value.__name__} has to be: {response_types} --> {value}'
                await ctx.reply(_msg, ephemeral=ephemeral)
                return ReturnData(False, _msg)

            return ReturnData(True, 'value is ok')

        response_type_check = await is_resp_type(response_type)
        if not response_type_check.response:
            return response_type_check

        async def is_lang(value):
            if value is None:
                return ReturnData(True, 'value is None')

            if value not in languages_dict.keys():
                _msg = f'{value.__name__} has to be: {languages_dict.keys()} --> {value}'
                await ctx.reply(_msg, ephemeral=ephemeral)
                return ReturnData(False, _msg)

            return ReturnData(True, 'value is ok')

        language_check = await is_lang(language)
        if not language_check.response:
            return language_check

        async def is_int(value):
            if value is None:
                return ReturnData(True, 'value is None')

            if not value.isdigit():
                _msg = f'{value.__name__} has to be a number: {value}'
                await ctx.reply(_msg, ephemeral=ephemeral)
                return ReturnData(False, _msg)

            return ReturnData(True, 'value is ok')

        volume_check = await is_int(volume)
        if not volume_check.response:
            return volume_check

        buffer_check = await is_int(buffer)
        if not buffer_check.response:
            return buffer_check

        history_length_check = await is_int(history_length)
        if not history_length_check.response:
            return history_length_check

        options.stopped = to_bool(stopped) if stopped is not None else options.stopped
        options.loop = to_bool(loop) if loop is not None else options.loop
        options.is_radio = to_bool(is_radio) if is_radio is not None else options.is_radio
        options.buttons = to_bool(buttons) if buttons is not None else options.buttons

        options.language = language if language is not None else options.language
        options.search_query = search_query if search_query is not None else options.search_query
        options.response_type = response_type if response_type is not None else options.response_type

        options.volume = float(int(volume) / 100) if volume is not None else options.volume
        options.buffer = int(buffer) if buffer is not None else options.buffer
        options.history_length = int(history_length) if history_length is not None else options.history_length

        update(glob)

    if len(guilds_to_change) < 2:
        if len(guilds_to_change) == 0:
            db_guild = guild(glob, guild_id)
            options = db_guild.options
            add = False
        else:
            db_guild = guild(glob, guilds_to_change[0])
            options = db_guild.options
            add = True

        message = f"""
        {txt(guild_id, glob, f'Edited options successfully!') + f' - `{db_guild.id}` ({db_guild.data.name})' if add else ''}\n**Options:**
        stopped -> `{options.stopped}`
        loop -> `{options.loop}`
        is_radio -> `{options.is_radio}`
        buttons -> `{options.buttons}`
        language -> `{options.language}`
        response_type -> `{options.response_type}`
        buffer -> `{options.buffer}`
        history_length -> `{options.history_length}`
        volume -> `{options.volume*100}`
        search_query -> `{options.search_query}`
        """

        await ctx.reply(message, ephemeral=ephemeral)
        return ReturnData(True, message)

    message = txt(guild_id, glob, f'Edited options successfully!')
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
            message = txt(guild_id, glob, "There are no slowed users!")
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
        message = txt(guild_id, glob, "Slowed time cannot be negative!")
        await ctx.reply(message, ephemeral=ephemeral)
        return ReturnData(False, message)

    slowed_user = SlowedUser(guild_id=guild_id, user_id=member.id, user_name=member.name, slowed_for=slowed_for)
    with glob.ses.no_autoflush:
        glob.ses.add(slowed_user)
        glob.ses.commit()

    message = f"{txt(guild_id, glob, 'Added slowed user:')} <@{member.id}> -> {slowed_for}"
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
        message = txt(guild_id, glob, "Slowed time cannot be negative!")
        await ctx.reply(message, ephemeral=ephemeral)
        return ReturnData(False, message)

    slowed_users = []
    for member in guild_obj.members:
        slowed_user = SlowedUser(guild_id=guild_obj.id, user_id=member.id, user_name=member.name, slowed_for=slowed_for)
        slowed_users.append(slowed_user)

    with glob.ses.no_autoflush:
        glob.ses.add_all(slowed_users)
        glob.ses.commit()

    message = f"{txt(guild_id, glob, 'Added slowed users:')} {len(slowed_users)}"
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
        message = txt(guild_id, glob, "That user is not slowed!")
        await ctx.reply(message, ephemeral=ephemeral)
        return ReturnData(False, message)

    with glob.ses.no_autoflush:
        glob.ses.delete(slowed_user)
        glob.ses.commit()

    message = f"{txt(guild_id, glob, 'Removed slowed user:')} <@{member.id}>"
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
        message = txt(guild_id, glob, "There are no slowed users!")
        await ctx.reply(message, ephemeral=ephemeral)
        return ReturnData(False, message)

    with glob.ses.no_autoflush:
        for slowed_user in slowed_users:
            glob.ses.delete(slowed_user)
        glob.ses.commit()

    message = f"{txt(guild_id, glob, 'Removed slowed users:')} {len(slowed_users)}"
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
        message = txt(guild_id, glob, "Time cannot be negative!")
        await ctx.reply(message, ephemeral=ephemeral)
        return ReturnData(False, message)

    if member.voice is None:
        message = txt(guild_id, glob, "That user is not in a voice channel!")
        await ctx.reply(message, ephemeral=ephemeral)
        return ReturnData(False, message)

    voice_channels = ctx.guild.voice_channels
    if len(voice_channels) < 2:
        message = txt(guild_id, glob, "There are not enough voice channels to torture!")
        await ctx.reply(message, ephemeral=ephemeral)
        return ReturnData(False, message)

    tu = glob.ses.query(TorturedUser).filter_by(user_id=member.id, guild_id=guild_id).first()
    if tu is not None:
        tu.torture_delay = delay
        glob.ses.commit()
        message = f"{txt(guild_id, glob, 'Updated torture delay for user:')} <@{member.id}> -> {delay}"
        await ctx.reply(message, ephemeral=ephemeral)
        return ReturnData(True, message)
    glob.ses.add(TorturedUser(guild_id=guild_id, user_id=member.id, torture_delay=delay))
    glob.ses.commit()

    message = f"{txt(guild_id, glob, 'Torturing user:')} <@{member.id}> -> {delay}"
    await ctx.reply(message, ephemeral=ephemeral)

    while True:
        is_tortured, delay = is_user_tortured(glob, member.id, guild_id)
        if not is_tortured:
            delete_tortured_user(glob, member.id, guild_id)

            message = txt(guild_id, glob, "That user is not being tortured!")
            await ctx.reply(message, ephemeral=ephemeral)
            return ReturnData(False, message)

        await asyncio.sleep(delay)

        if member.voice is None:
            delete_tortured_user(glob, member.id, guild_id)

            message = txt(guild_id, glob, "That user is not in a voice channel!")
            await ctx.reply(message, ephemeral=ephemeral)
            return ReturnData(False, message)
        if member.voice.channel is None:
            delete_tortured_user(glob, member.id, guild_id)

            message = txt(guild_id, glob, "That user is not in a voice channel!")
            await ctx.reply(message, ephemeral=ephemeral)
            return ReturnData(False, message)
        if member.voice.channel == ctx.guild.afk_channel:
            delete_tortured_user(glob, member.id, guild_id)

            message = txt(guild_id, glob, "That user is in the AFK channel!")
            await ctx.reply(message, ephemeral=ephemeral)
            return ReturnData(False, message)

        random_channel = random.choice([channel for channel in voice_channels if channel != member.voice.channel])
        try:
            await member.move_to(random_channel)
        except discord.Forbidden:
            message = txt(guild_id, glob, "I don't have permission to move that user!")
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
        message = txt(guild_id, glob, "That user is not being tortured!")
        await ctx.reply(message, ephemeral=ephemeral)
        return ReturnData(False, message)

    with glob.ses.no_autoflush:
        glob.ses.delete(tortured_user)
        glob.ses.commit()

    message = f"{txt(guild_id, glob, 'Stopped torturing user:')} <@{member.id}>"
    await ctx.reply(message, ephemeral=ephemeral)
    return ReturnData(True, message)

# Development
async def dev_command_def(ctx: dc_commands.Context, glob: GlobalVars, command: str, ephemeral: bool=True):
    """
    Development command
    :param glob: GlobalVars
    :param ctx: Context
    :param command: Command to run
    :param ephemeral: Should bot response be ephemeral
    """
    log(ctx, 'dev', locals(), log_type='function', author=ctx.author)

    raise Exception('This command raises an exception! - for dev')

    # from database.guild import guild_data_key
    #
    # key = guild_data_key(glob, int(command))
    #
    # message = f"Key: {key}"
    # await ctx.reply(message, ephemeral=ephemeral)
    # return ReturnData(True, message)

    print(f'Running command: {command}')
    print(f'time() = {int(time.time())}')

    await push_update(glob, guild_id=ctx.guild.id, update_type=['all'])

    await ctx.reply(f'Pushed update to guild: {ctx.guild.id}', ephemeral=ephemeral)


    #
    # import json
    # import aiohttp
    #
    # # &render=json
    # base_url = 'https://opml.radiotime.com'
    #
    # query = 'evropa 2'
    #
    # #  limit search to 5
    # search_url = f'{base_url}/Search.ashx?query={query}&types=station&render=json&limit=5'
    #
    #
    # async with aiohttp.ClientSession() as session:
    #     async with session.get(search_url) as response:
    #         output = await response.json()
    #         url = output['body'][0]['URL'] + '&render=json'
    #
    # print(url)
    #
    # async with aiohttp.ClientSession() as session:
    #     async with session.get(url) as response:
    #         stream_url = (await response.json())['body'][0]['url']
    #
    # print(stream_url)
    #
    # await join_def(ctx, glob)
    #
    # source, chapters = await GetSource.create_source(glob, ctx.guild.id, stream_url, 'Probe')
    # ctx.guild.voice_client.play(source)
    #
    # await ctx.reply(f'Playing: {url}', ephemeral=ephemeral)
    # return ReturnData(True, f'Playing: {url}')


    # return await play_def(ctx, glob, url)

# List bot status for servers
async def list_connected_def(ctx: dc_commands.Context, glob: GlobalVars, ephemeral: bool=True):
    """
    List all connected servers
    :param glob: GlobalVars
    :param ctx: Context
    :param ephemeral: Should bot response be ephemeral
    """
    log(ctx, 'list_connected', locals(), log_type='function', author=ctx.author)

    list_connected = guilds_get_connected_status(glob)
    count = list_connected.pop(0)

    # 'Playing': 0,
    # 'Paused': 0,
    # 'Connected': 0,
    # 'Not connected': 0,
    # 'Unknown': 0

    # "... others are not connected" - len 40 (to be sure)

    message = f"**Connected servers:**\n"
    for name, number in count.items():
        message += f">{name}: {number}\n"
    message += "\n**List of Servers:**\n"

    worth_mentioning = count['Playing'] + count['Paused'] + count['Connected']
    if worth_mentioning == 0:
        message += "> No servers are connected"
        await ctx.reply(message, ephemeral=ephemeral)
        return ReturnData(True, message)

    for index, c_guild in enumerate(list_connected):
        m_add = f"> {c_guild['status']} - ({c_guild['id']}){c_guild['name']}\n"
        if c_guild['status'] not in ['Playing', 'Paused', 'Connected']:
            m_add += "> ... others are not connected"

        if len(message) + len(m_add) > 4096:
            await ctx.reply(message, ephemeral=ephemeral)
            message = m_add
            continue

        message += m_add

    await ctx.reply(message, ephemeral=ephemeral)
    return ReturnData(True, message)

# Status
async def status_def(ctx: dc_commands.Context, glob: GlobalVars, time_filter: str='all', guild_id: int=0, ephemeral: bool=True):
    """
    Change bot status
    :param glob: GlobalVars
    :param ctx: Context
    :param time_filter: Time filter for status [day, week, month, year, all]
    :param guild_id: Guild id - 0 for all guilds
    :param ephemeral: Should bot response be ephemeral
    """
    log(ctx, 'status', locals(), log_type='function', author=ctx.author)

    org_message = await ctx.reply('Getting Info...', ephemeral=ephemeral)

    current_time = int(time.time())
    time_periods = {
        'day': 86400,
        'week': 604800,
        'month': 2592000,
        'year': 31536000,
        'all': current_time
    }
    cutoff = current_time - time_periods.get(time_filter, current_time)

    start_time = time.time()

    # DESCRIPTION ------------------------------------------------------------------------------------------------------

    with open('VERSION', 'r') as f:
        bot_version = f.read().strip()
    ping = int(glob.bot.latency * 1000)  # in ms
    bot_status = get_guild_bot_status(glob, ctx.guild.id)

    # CONNECTED VC -----------------------------------------------------------------------------------------------------

    guilds_status = guilds_get_connected_status(glob)
    guilds_status_dict = guilds_status.pop(0)
    all_connected = sum(guilds_status_dict.values())

    # DATABASE ---------------------------------------------------------------------------------------------------------

    currently_connected_guilds = len(glob.bot.guilds)
    db_guilds = glob.ses.query(Guild).count()

    # DATABASE TIME ----------------------------------------------------------------------------------------------------

    data: DBData = db_data(glob, cutoff, guild_id)

    # HARDWARE INFO ----------------------------------------------------------------------------------------------------
    # CPU
    cpu_info = cpuinfo.get_cpu_info()

    cpu_boot_time = psutil.boot_time()
    cpu_arch = f"{cpu_info['arch_string_raw']} {cpu_info['arch']} ({cpu_info['bits']} bits)"
    cpu_name = cpu_info['brand_raw']
    cpu_cores = f"{psutil.cpu_count(logical=False)} cores ({psutil.cpu_count()} threads)"
    cpu_speed = cpu_info['hz_actual_friendly']
    cpu_family = cpu_info['family']
    cpu_model = cpu_info['model']
    cpu_vendor = cpu_info['vendor_id_raw']

    # MEMORY
    memory = psutil.virtual_memory()
    swap = psutil.swap_memory()

    # NETWORK
    net_io = psutil.net_io_counters()
    net_info = psutil.net_if_addrs()

    response = requests.get('https://api64.ipify.org?format=json')
    public_ip = response.json()['ip'] if response.status_code == 200 else 'api64.ipify.org is down or broken'

    # EMBEDS -----------------------------------------------------------------------------------------------------------

    # STATUS EMBED
    embed1 = discord.Embed(title=f"Bot Status", color=0x00ff00, description=f"Version: `{bot_version}` | Ping: `{ping}ms` | Status: `{bot_status}` | Filter: `{time_filter}` | Guild: `{guild_id}`")
    embed1.add_field(name="Uptime",
                     value=f"""
                     Started at: `{struct_to_time(int(data['bot_boot_time']))}`
                     Duration: `{convert_duration_long(int(time.time() - data['bot_boot_time']))}`
                     Bot started: `{data['count_bot_boot']}` times
                     """)

    # ANALYTICS EMBED
    embed2 = discord.Embed(title=f"Analytics", color=0x00ff00)
    embed2.add_field(name="VC Time",
                     value=f"""
                     Time: `{convert_duration_long(data['time_in_vc'])}`
                     Playing: `{convert_duration_long(data['time_playing'])}`
                     Paused: `{convert_duration_long(data['time_paused'])}`
                     """)
    embed2.add_field(name="Count",
                     value=f"""
                     Commands: `{data['count_command']}`
                     Songs played: `{data['count_songs_played']}`
                     Skipped: `{data['count_skipped']}`
                     Errors: `{data['count_error']}`
                     Voice Sessions: `{data['count_voice_sessions']}`
                     """)
    embed2.add_field(name="Guild Count",
                     value=f"""
                     Guilds joined: `{data['count_guild_joined']}`
                     Guilds left: `{data['count_guild_left']}`
                     """)

    # CURRENT STATUS EMBED
    embed3 = discord.Embed(title=f"Current Status", color=0x00ff00)
    embed3.add_field(name=f"Connected to {all_connected} guilds",
                     value=''.join([f'{key}: `{value}`\n' for key, value in guilds_status_dict.items()]))
    embed3.add_field(name=f"Database",
                     value=f"""
                     Guilds in DB: `{db_guilds}`
                     Currently Connected Guilds: `{currently_connected_guilds}`
                     """)
    embed3.add_field(name=f"Guilds List",
                     value="Use `/zz_list_connected` to get the list of connected guilds",
                     inline=False)

    # HARDWARE INFO EMBED
    embed4 = discord.Embed(title=f"Hardware Info", color=0x00ff00)
    embed4.add_field(name="CPU",
                     value=f"""
                     Name: `{cpu_name}`
                     Architecture: `{cpu_arch}`
                     Cores: `{cpu_cores}`
                     Speed: `{cpu_speed}`
                     Family: `{cpu_family}`
                     Model: `{cpu_model}`
                     Vendor: `{cpu_vendor}`
                     Boot Time: `{struct_to_time(cpu_boot_time)}`
                     Boot Duration: `{convert_duration_long(int(time.time() - cpu_boot_time))}`
                     """)
    embed4.add_field(name="Virtual Memory",
                     value=f"""
                     Total: `{memory.total / (1024 ** 3):.2f}GB`
                     Available: `{memory.available / (1024 ** 3):.2f}GB`
                     Used: `{memory.used / (1024 ** 3):.2f}GB`
                     Percent: `{memory.percent}%`
                     **Swap Memory**
                     Total: `{swap.total / (1024 ** 3):.2f}GB`
                     Used: `{swap.used / (1024 ** 3):.2f}GB`
                     Free: `{swap.free / (1024 ** 3):.2f}GB`
                     Percent: `{swap.percent}%`
                     """)

    # NETWORK INFO EMBED
    embed5 = discord.Embed(title=f"Network Info", color=0x00ff00)
    embed5.add_field(name="Traffic",
                     value=f"""
                     Total Bytes Sent: `{net_io.bytes_sent / (1024 ** 3):.2f} GB`
                     Total Bytes Received: `{net_io.bytes_recv / (1024 ** 3):.2f} GB`
                     Packets Sent: `{net_io.packets_sent}`
                     Packets Received: `{net_io.packets_recv}`
                     """)
    embed5.add_field(name="Public IP",
                     value=f"""
                     IP: `{public_ip}`
                     """)

    # NETWORK INTERFACE INFO EMBED
    embed6 = discord.Embed(title=f"Network Interface Info", color=0x00ff00)
    for interface, address in net_info.items():
        msg = ''
        for addr in address:
            msg += f"""Address Family: {addr.family.name}
            Address: {addr.address}
            Netmask: {addr.netmask}
            Broadcast: {addr.broadcast}
            PTP: {addr.ptp}"""

        embed6.add_field(name=f"Interface: {interface}",
                         value=msg)

    await org_message.edit(content='**Bot Status**', embeds=[embed1, embed2, embed3, embed4, embed5, embed6])
    return ReturnData(True, 'Status Sent')
