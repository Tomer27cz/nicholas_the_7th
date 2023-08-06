from classes.data_classes import ReturnData
from classes.video_class import VideoClass

from utils.log import log, send_to_admin
from utils.translate import tg
from utils.save import save_json
from utils.globals import get_guild_dict, get_bot

import commands.admin
from commands.utils import ctx_check

import discord
import ast
import json

async def web_video_edit(web_data, form) -> ReturnData:
    log(web_data, 'web_video_edit', [form], log_type='function', author=web_data.author)
    is_ctx, ctx_guild_id, ctx_author_id, ctx_guild_object = ctx_check(web_data)
    guild = get_guild_dict()
    guild_id = web_data.guild_id
    index = form['edit_btn']
    is_queue = True
    is_np = False

    if index == 'np':
        is_np = True

    elif not index.isdigit():
        is_queue = False
        try:
            index = int(index[1:])
            if index < 0 or index >= len(guild[guild_id].history):
                return ReturnData(False, tg(ctx_guild_id, 'Invalid index (out of range)'))
        except (TypeError, ValueError, IndexError):
            return ReturnData(False, tg(ctx_guild_id, 'Invalid index (not a number)'))

    elif index.isdigit():
        is_queue = True
        index = int(index)
        if index < 0 or index >= len(guild[guild_id].queue):
            return ReturnData(False, tg(ctx_guild_id, 'Invalid index (out of range)'))

    else:
        return ReturnData(False, tg(ctx_guild_id, 'Invalid index (not a number)'))

    class_type = form['class_type']
    author = form['author']
    url = form['url']
    title = form['title']
    picture = form['picture']
    duration = form['duration']
    channel_name = form['channel_name']
    channel_link = form['channel_link']
    radio_info = form['radio_info']
    local_number = form['local_number']
    created_at = form['created_at']
    played_duration = form['played_duration']
    chapters = form['chapters']
    discord_channel = form['discord_channel']
    stream_url = form['stream_url']

    none_list = ['None', '']

    if author in none_list: author = None
    if url in none_list: url = None
    if title in none_list: title = None
    if picture in none_list: picture = None
    if duration in none_list: duration = None
    if channel_name in none_list: channel_name = None
    if channel_link in none_list: channel_link = None
    if radio_info in none_list: radio_info = None
    if local_number in none_list: local_number = None
    if created_at in none_list: created_at = None
    if played_duration in none_list: played_duration = None
    if chapters in none_list: chapters = None
    if discord_channel in none_list: discord_channel = None
    if stream_url in none_list: stream_url = None

    if class_type not in ['Video', 'Radio', 'Local', 'Probe', 'SoundCloud']:
        return ReturnData(False, f'Invalid class type: {class_type}')

    if created_at:
        if not created_at.isdigit():
            return ReturnData(False, f'Invalid struct time: {created_at}')
        created_at = int(created_at)

    if local_number:
        if not local_number.isdigit():
            return ReturnData(False, f'Invalid local number: {local_number}')
        local_number = int(local_number)

    if author and author.isdigit():
        author = int(author)

    if duration and duration.isdigit():
        duration = int(duration)

    if radio_info:
        try:
            radio_info = ast.literal_eval(radio_info)
            assert type(radio_info) == dict
        except (TypeError, ValueError, json.decoder.JSONDecodeError, AssertionError, SyntaxError):
            return ReturnData(False, f'Invalid radio info: {radio_info}')

    if played_duration:
        try:
            played_duration = ast.literal_eval(played_duration)
            assert type(played_duration) == list
        except (TypeError, ValueError, json.decoder.JSONDecodeError, AssertionError, SyntaxError):
            return ReturnData(False, f'Invalid played duration: {played_duration}')

    if chapters:
        try:
            chapters = ast.literal_eval(chapters)
            assert type(chapters) == list
        except (TypeError, ValueError, json.decoder.JSONDecodeError, AssertionError, SyntaxError):
            return ReturnData(False, f'Invalid chapters: {chapters}')

    if discord_channel:
        try:
            discord_channel = ast.literal_eval(discord_channel)
            assert type(discord_channel) == dict
        except (TypeError, ValueError, json.decoder.JSONDecodeError, AssertionError, SyntaxError):
            return ReturnData(False, f'Invalid discord channel: {discord_channel}')

    video = VideoClass(class_type, author, url=url, title=title, picture=picture, duration=duration, channel_name=channel_name, channel_link=channel_link, radio_info=radio_info, local_number=local_number, created_at=created_at, played_duration=played_duration, chapters=chapters, discord_channel=discord_channel, stream_url=stream_url)

    if is_np:
        guild[guild_id].now_playing = video
    else:
        if is_queue:
            guild[guild_id].queue[index] = video
        else:
            guild[guild_id].history[index] = video

    save_json()

    return ReturnData(True, tg(ctx_guild_id, 'Edited item') + f' {"h" if not is_queue else ""}{index} ' + tg(ctx_guild_id, 'successfully!'))

async def web_options_edit(web_data, form) -> ReturnData:
    log(web_data, 'web_options_edit', [form], log_type='function', author=web_data.author)
    is_ctx, ctx_guild_id, ctx_author_id, ctx_guild_object = ctx_check(web_data)

    try:
        stopped = form['stopped']
        loop = form['loop']
        is_radio = form['is_radio']
        language = form['language']
        response_type = form['response_type']
        search_query = form['search_query']
        buttons = form['buttons']
        volume = form['volume']
        buffer = form['buffer']
        history_length = form['history_length']
        last_updated = form['last_updated']
    except KeyError:
        return ReturnData(False, tg(ctx_guild_id, 'Missing form data - please contact the developer (he fucked up when doing an update)'))

    return await commands.admin.options_def(web_data, server='this', stopped=stopped, loop=loop, is_radio=is_radio, language=language,
                             response_type=response_type, search_query=search_query, buttons=buttons, volume=volume,
                             buffer=buffer, history_length=history_length, last_updated=last_updated)

async def web_delete_guild(web_data, guild_id) -> ReturnData:
    log(web_data, 'web_delete_guild', [guild_id], log_type='function', author=web_data.author)
    is_ctx, ctx_guild_id, ctx_author_id, ctx_guild_object = ctx_check(web_data)
    guild = get_guild_dict()
    try:
        guild_id = int(guild_id)
    except (TypeError, ValueError):
        return ReturnData(False, tg(ctx_guild_id, 'Invalid guild id') + f': {guild_id}')

    if guild_id not in guild.keys():
        return ReturnData(False, tg(ctx_guild_id, 'Guild not found') + f': {guild_id}')

    del guild[guild_id]

    save_json()

    return ReturnData(True, tg(ctx_guild_id, 'Deleted guild') + f' {guild_id} ' + tg(ctx_guild_id, 'successfully!'))

async def web_disconnect_guild(web_data, guild_id) -> ReturnData:
    log(web_data, 'web_disconnect_guild', [guild_id], log_type='function', author=web_data.author)
    is_ctx, ctx_guild_id, ctx_author_id, ctx_guild_object = ctx_check(web_data)
    try:
        guild_id = int(guild_id)
    except (TypeError, ValueError):
        return ReturnData(False, tg(ctx_guild_id, 'Invalid guild id') + f': {guild_id}')

    bot_guild_ids = [guild_object.id for guild_object in get_bot().guilds]

    if guild_id not in bot_guild_ids:
        return ReturnData(False, tg(ctx_guild_id, 'Guild not found in bot.guilds') + f': {guild_id}')

    guild_to_disconnect = get_bot().get_guild(guild_id)

    try:
        await guild_to_disconnect.leave()
    except discord.HTTPException as e:
        return ReturnData(False, f"Something Failed -> HTTPException: {e}")

    save_json()

    return ReturnData(True, tg(ctx_guild_id, 'Left guild') + f' {guild_id} ' + tg(ctx_guild_id, 'successfully!'))

async def web_create_invite(web_data, guild_id):
    log(web_data, 'web_create_invite', [guild_id], log_type='function', author=web_data.author)
    is_ctx, ctx_guild_id, ctx_author_id, ctx_guild_object = ctx_check(web_data)
    try:
        guild_object = get_bot().get_guild(int(guild_id))
    except (TypeError, ValueError):
        return ReturnData(False, tg(ctx_guild_id, 'Invalid guild id') + f': {guild_id}')

    if not guild_object:
        return ReturnData(False, tg(ctx_guild_id, 'Guild not found:') + f' {guild_id}')

    try:
        guild_object_invites = await guild_object.invites()
    except discord.HTTPException as e:
        return ReturnData(False, tg(ctx_guild_id, "Something Failed -> HTTPException") + f": {e}")

    if guild_object_invites:
        message = f'Guild ({guild_object.id}) invites -> {guild_object_invites}'
        log(None, message)
        await send_to_admin(message)
        return ReturnData(True, message)

    if not guild_object_invites:
        try:
            channel = guild_object.text_channels[0]
            invite = await channel.create_invite()
            message = tg(ctx_guild_id, 'Invite for guild') + f' ({guild_object.id}) -> {invite}'
            log(None, message)
            await send_to_admin(message)
            return ReturnData(True, message)
        except discord.HTTPException as e:
            return ReturnData(False, tg(ctx_guild_id, "Something Failed -> HTTPException") + f": {e}")