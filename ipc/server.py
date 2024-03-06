from classes.data_classes import ReturnData, GuildData
from classes.discord_classes import DiscordChannel, DiscordRole, DiscordUser, DiscordInvite, DiscordMember

from database.guild import guild, guild_ids

from utils.log import log
from utils.discord import get_username
from utils.save import update
from utils.saves import new_queue_save, delete_queue_save, rename_queue_save, load_queue_save
from utils.global_vars import GlobalVars

from ipc.main import send_msg, recv_msg

import commands.player
import commands.voice
import commands.queue
import commands.general
import commands.chat_export

import web_func.move
import web_func.queue
import web_func.voice
import web_func.options
import web_func.admin

import asyncio
import pickle
import socket
import sys
import os

inside_docker = os.environ.get("INSIDE_DOCKER", False)

HOST = '127.0.0.1' if not inside_docker or not inside_docker == 'true' else '0.0.0.0'  # The server's hostname or IP address
PORT = 5421  # The port used by the server

async def execute_function(request_dict, glob: GlobalVars) -> ReturnData:
    """
    Execute a function from a request dict
    :param request_dict: A request dict
    :param glob: GlobalVars
    :type request_dict: dict
    :return: ReturnData
    """
    if request_dict['type'] != 'function':
        return ReturnData(False, f'Wrong type: {request_dict["type"]} --> Internal error (contact developer)')

    web_data = request_dict['web_data']
    func_name = request_dict['function_name']

    if request_dict['args'] is None:
        args = {}
    else:
        args = request_dict['args']

    if func_name == 'remove_def':
        return await commands.queue.remove_def(web_data, glob, number=args['number'], list_type=args['list_type'])
    if func_name == 'web_up':
        return await web_func.move.web_up(web_data, glob, number=args['number'])
    if func_name == 'web_down':
        return await web_func.move.web_down(web_data, glob, number=args['number'])
    if func_name == 'web_top':
        return await web_func.move.web_top(web_data, glob, number=args['number'])
    if func_name == 'web_bottom':
        return await web_func.move.web_bottom(web_data, glob, number=args['number'])
    if func_name == 'web_duplicate':
        return await web_func.move.web_duplicate(web_data, glob, number=args['number'])

    if func_name == 'play_def':
        return await commands.player.play_def(web_data, glob)
    if func_name == 'stop_def':
        return await commands.voice.stop_def(web_data, glob)
    if func_name == 'pause_def':
        return await commands.voice.pause_def(web_data, glob)
    if func_name == 'skip_def':
        return await commands.queue.skip_def(web_data, glob)

    if func_name == 'loop_command_def':
        return await commands.player.loop_command_def(web_data, glob)
    if func_name == 'shuffle_def':
        return await commands.queue.shuffle_def(web_data, glob)
    if func_name == 'clear_def':
        return await commands.queue.clear_def(web_data, glob)

    if func_name == 'web_disconnect':
        return await web_func.voice.web_disconnect(web_data, glob)
    if func_name == 'web_join':
        return await web_func.voice.web_join(web_data, glob, form=args['form'])

    if func_name == 'web_queue':
        return await web_func.queue.web_queue(web_data, glob, video_type=args['video_type'], position=args['position'])
    if func_name == 'queue_command_def':
        return await commands.queue.queue_command_def(web_data, glob, url=args['url'])
    if func_name == 'web_queue_from_radio':
        return await web_func.queue.web_queue_from_radio(web_data, glob, radio_name=args['radio_name'])

    if func_name == 'new_queue_save':
        return await new_queue_save(glob, web_data.guild_id, save_name=args['save_name'], author_name=args['author_name'], author_id=args['author_id'])
    if func_name == 'load_queue_save':
        return await load_queue_save(glob, web_data.guild_id, save_name=args['save_name'])
    if func_name == 'delete_queue_save':
        return delete_queue_save(glob, web_data.guild_id, save_name=args['save_name'])
    if func_name == 'rename_queue_save':
        return rename_queue_save(glob, web_data.guild_id, old_name=args['old_name'], new_name=args['new_name'])

    if func_name == 'volume_command_def':
        return await commands.voice.volume_command_def(web_data, glob, volume=args['volume'])
    if func_name == 'set_video_time':
        return await commands.player.set_video_time(web_data, glob, time_stamp=args['time_stamp'])

    # user edit
    if func_name == 'web_user_options_edit':
        return await web_func.options.web_user_options_edit(web_data, glob, form=args['form'])

    # admin
    if func_name == 'web_video_edit':
        return await web_func.admin.web_video_edit(web_data, glob, form=args['form'])
    if func_name == 'web_options_edit':
        return await web_func.admin.web_options_edit(web_data, glob, form=args['form'])

    if func_name == 'web_delete_guild':
        return await web_func.admin.web_delete_guild(web_data, glob, guild_id=args['guild_id'])
    if func_name == 'web_disconnect_guild':
        return asyncio.run_coroutine_threadsafe(web_func.admin.web_disconnect_guild(web_data, glob, args['guild_id']), glob.bot.loop).result()
        # return await web_disconnect_guild(web_data, guild_id=args['guild_id'])
    if func_name == 'web_create_invite':
        return asyncio.run_coroutine_threadsafe(web_func.admin.web_create_invite(web_data, glob, args['guild_id']), glob.bot.loop).result()
        # return await web_create_invite(web_data, guild_id=args['guild_id'])

    if func_name == 'download_guild':
        guild_id = args['guild_id']
        return await commands.chat_export.download_guild(web_data, glob, guild_id)
    if func_name == 'download_guild_channel':
        channel_id = args['channel_id']
        return await commands.chat_export.download_guild_channel(web_data, glob, channel_id)

    # if func_name == 'export_queue':
    #     guild_id = args['guild_id']
    #     return await commands.queue.export_queue(web_data, guild_id)
    # if func_name == 'import_queue':
    #     guild_id = args['guild_id']
    #     queue_data = args['queue_data']
    #     return await commands.queue.import_queue(web_data, queue_data, guild_id)

    return ReturnData(False, f'Unknown function: {func_name}')

async def execute_get_data(request_dict, glob: GlobalVars):
    data_type = request_dict['data_type']
    # guild = get_guild_dict() # TODO: get some data directly from db --- done

    def get_guild_bot_status(global_vars: GlobalVars, g_id):
        g_object = global_vars.bot.get_guild(g_id)
        if not g_object:
            return 'Unknown'
        voice = g_object.voice_client
        if voice is None:
            return 'Not connected'
        if voice.is_playing():
            return 'Playing'
        if voice.is_paused():
            return 'Paused'
        elif voice.is_connected():
            return 'Connected'
        return 'Unknown'

    # Voice Channels
    if data_type == 'guild_voice_channels':
        guild_id = request_dict['guild_id']
        guild_channels = []
        guild_object = glob.bot.get_guild(guild_id)
        if not guild_object:
            return None
        for channel in guild_object.voice_channels:
            guild_channels.append(DiscordChannel(glob, channel.id, no_members=True))
        return guild_channels
    elif data_type == 'guild_voice_channels_index':
        guild_id = request_dict['guild_id']
        start_index = request_dict['start_index']
        end_index = request_dict['end_index']
        guild_channels = []
        guild_object = glob.bot.get_guild(guild_id)
        if not guild_object:
            return None
        for index, channel in enumerate(guild_object.voice_channels[start_index:end_index]):
            guild_channels.append(DiscordChannel(glob, channel.id, no_members=True))
        return guild_channels

    # Text channels
    elif data_type == 'guild_text_channels':
        guild_id = request_dict['guild_id']
        guild_channels = []
        guild_object = glob.bot.get_guild(guild_id)
        if not guild_object:
            return None
        for channel in guild_object.text_channels:
            guild_channels.append(DiscordChannel(glob, channel.id, no_members=True))
        return guild_channels
    elif data_type == 'guild_text_channels_index':
        guild_id = request_dict['guild_id']
        start_index = request_dict['start_index']
        end_index = request_dict['end_index']
        guild_channels = []
        guild_object = glob.bot.get_guild(guild_id)
        if not guild_object:
            return None
        for index, channel in enumerate(guild_object.text_channels[start_index:end_index]):
            guild_channels.append(DiscordChannel(glob, channel.id, no_members=True))
        return guild_channels

    # Channel members
    elif data_type == 'guild_channel_members':
        guild_id = request_dict['guild_id']
        channel_id = request_dict['channel_id']
        guild_users = []
        guild_object = glob.bot.get_guild(guild_id)
        if not guild_object:
            return None
        channel_object = guild_object.get_channel(channel_id)
        if not channel_object:
            return None
        for member in channel_object.members:
            guild_users.append(DiscordMember(glob, member))
        return guild_users

    # Channel transcript
    elif data_type == 'channel_transcript':
        channel_id = request_dict['channel_id']
        channel_object = DiscordChannel(glob, channel_id)
        return await channel_object.get_first_messages(glob, 100)

    # Guild members
    elif data_type == 'guild_members':
        guild_id = request_dict['guild_id']
        guild_users = []
        guild_object = glob.bot.get_guild(guild_id)
        if not guild_object:
            return None
        for member in guild_object.members:
            guild_users.append(DiscordMember(glob, member))
        return guild_users
    elif data_type == 'guild_members_index':
        guild_id = request_dict['guild_id']
        start_index = request_dict['start_index']
        end_index = request_dict['end_index']
        guild_users = []
        guild_object = glob.bot.get_guild(guild_id)
        if not guild_object:
            return None
        for index, member in enumerate(guild_object.members[start_index:end_index]):
            guild_users.append(DiscordMember(glob, member))
        return guild_users

    # Guild roles
    elif data_type == 'guild_roles':
        guild_id = request_dict['guild_id']
        guild_roles = []
        guild_object = glob.bot.get_guild(guild_id)
        if not guild_object:
            return None
        for role in guild_object.roles:
            guild_roles.append(DiscordRole(glob, role_id=role.id, guild_id=guild_id, no_members=True))
        return guild_roles
    elif data_type == 'guild_roles_index':
        guild_id = request_dict['guild_id']
        start_index = request_dict['start_index']
        end_index = request_dict['end_index']
        guild_roles = []
        guild_object = glob.bot.get_guild(guild_id)
        if not guild_object:
            return None
        for index, role in enumerate(guild_object.roles[start_index:end_index]):
            guild_roles.append(DiscordRole(glob, role_id=role.id, guild_id=guild_id, no_members=True))
        return guild_roles
    elif data_type == 'guild_role_members':
        guild_id = request_dict['guild_id']
        role_id = request_dict['role_id']
        guild_users = []
        guild_object = glob.bot.get_guild(guild_id)
        if not guild_object:
            return None
        role_object = guild_object.get_role(role_id)
        if not role_object:
            return None
        for member in role_object.members:
            guild_users.append(DiscordMember(glob, member))
        return guild_users
    elif data_type == 'guild_role_permissions':
        guild_id = request_dict['guild_id']
        role_id = request_dict['role_id']
        guild_object = glob.bot.get_guild(guild_id)
        if not guild_object:
            return None
        role_object = guild_object.get_role(role_id)
        if not role_object:
            return None
        return role_object.permissions

    # Guild invites
    elif data_type == 'guild_invites':
        guild_id = request_dict['guild_id']
        guild_invites = []
        guild_object = glob.bot.get_guild(guild_id)
        if not guild_object:
            return None

        # if not guild_object.permissions_for(guild_object.me).speak: #TODO: check for permission to view invites

        invites = asyncio.run_coroutine_threadsafe(guild_object.invites(), glob.bot.loop).result()
        if not invites:
            return None

        for invite in invites:
            guild_invites.append(DiscordInvite(glob, invite))

        return guild_invites

    # User
    elif data_type == 'user_name':
        user_id = request_dict['user_id']
        return get_username(glob, user_id)
    elif data_type == 'user_data':
        user_id = request_dict['user_id']
        return DiscordUser(glob, user_id)

    # Video
    if data_type == 'renew':
        queue_type = request_dict['queue_type']
        index = request_dict['index']
        guild_id = request_dict['guild_id']

        if queue_type == 'now_playing':
            await guild(glob, guild_id).now_playing.renew(glob)
        elif queue_type == 'queue':
            try:
                await guild(glob, guild_id).queue[index].renew(glob)
            except IndexError:
                pass

    # BOT
    elif data_type == 'bot_guilds':
        update(glob)
        bot_guilds = []
        for bot_guild in glob.bot.guilds:
            to_append = GuildData(glob, bot_guild.id, {})
            bot_guilds.append(to_append)
        return bot_guilds
    elif data_type == 'guilds_bot_status':
        guilds_status = {}
        for guild_id in guild_ids(glob):
            guilds_status[guild_id] = get_guild_bot_status(glob, guild_id)
        return guilds_status
    elif data_type == 'guild_bot_status':
        return get_guild_bot_status(glob, request_dict['guild_id'])
    else:
        print(f'Unknown data type: {data_type}', file=sys.stderr, flush=True)

# handle client
async def handle_client(client, glob: GlobalVars):
    request_data = await recv_msg(client)
    request_dict = pickle.loads(request_data)

    request_type = request_dict['type']

    if request_type == 'get_data':
        response = await execute_get_data(request_dict, glob)
    elif request_type == 'function':
        response = await execute_function(request_dict, glob)
    else:
        raise ValueError(f'Unknown request type: {request_type}')

    if response:
        # serialize response
        serialized_response = pickle.dumps(response)
        await send_msg(client, serialized_response)

    client.close()

async def run_server(glob: GlobalVars):
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((HOST, PORT))
    server.listen(8)
    server.setblocking(False)

    log(None, f'IPC server is running on {HOST}:{PORT}')

    loop = asyncio.get_event_loop()

    ipc = True
    while ipc:
        client, _ = await loop.sock_accept(server)
        await loop.create_task(handle_client(client, glob))

def ipc_run(glob: GlobalVars):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    loop.run_until_complete(run_server(glob))
    loop.close()
