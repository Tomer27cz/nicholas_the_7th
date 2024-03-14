from classes.data_classes import ReturnData, Guild
from classes.video_class import to_queue_class, to_now_playing_class, to_history_class, Queue

from commands.utils import ctx_check

from database.guild import guild, delete_guild

from utils.log import log, send_to_admin
from utils.translate import txt
from utils.save import update, push_update
from utils.global_vars import GlobalVars

import commands.admin

import discord
import ast
import json

async def web_video_edit(web_data, glob: GlobalVars, form) -> ReturnData:
    log(web_data, 'web_video_edit', options=locals(), log_type='function', author=web_data.author)
    is_ctx, ctx_guild_id, ctx_author_id, ctx_guild_object = ctx_check(web_data, glob)
    guild_id = web_data.guild_id
    db_guild = guild(glob, guild_id)
    index = form['edit_btn']
    is_queue = True
    is_np = False

    if index == 'np':
        is_np = True

    elif not index.isdigit():
        is_queue = False
        try:
            index = int(index[1:])
            if index < 0 or index >= len(db_guild.history):
                return ReturnData(False, txt(ctx_guild_id, glob, 'Invalid index (out of range)'))
        except (TypeError, ValueError, IndexError):
            return ReturnData(False, txt(ctx_guild_id, glob, 'Invalid index (not a number)'))

    elif index.isdigit():
        is_queue = True
        index = int(index)
        if index < 0 or index >= len(db_guild.queue):
            return ReturnData(False, txt(ctx_guild_id, glob, 'Invalid index (out of range)'))

    else:
        return ReturnData(False, txt(ctx_guild_id, glob, 'Invalid index (not a number)'))

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

    if author in none_list:
        author = None
    if url in none_list:
        url = None
    if title in none_list:
        title = None
    if picture in none_list:
        picture = None
    if duration in none_list:
        duration = None
    if channel_name in none_list:
        channel_name = None
    if channel_link in none_list:
        channel_link = None
    if radio_info in none_list:
        radio_info = None
    if local_number in none_list:
        local_number = None
    if created_at in none_list:
        created_at = None
    if played_duration in none_list:
        played_duration = None
    if chapters in none_list:
        chapters = None
    if discord_channel in none_list:
        discord_channel = None
    if stream_url in none_list:
        stream_url = None

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
            assert isinstance(radio_info, dict)
        except (TypeError, ValueError, json.decoder.JSONDecodeError, AssertionError, SyntaxError):
            return ReturnData(False, f'Invalid radio info: {radio_info}')

    if played_duration:
        try:
            played_duration = ast.literal_eval(played_duration)
            assert isinstance(played_duration, list)
        except (TypeError, ValueError, json.decoder.JSONDecodeError, AssertionError, SyntaxError):
            return ReturnData(False, f'Invalid played duration: {played_duration}')

    if chapters:
        try:
            chapters = ast.literal_eval(chapters)
            assert isinstance(chapters, list)
        except (TypeError, ValueError, json.decoder.JSONDecodeError, AssertionError, SyntaxError):
            return ReturnData(False, f'Invalid chapters: {chapters}')

    if discord_channel:
        try:
            discord_channel = ast.literal_eval(discord_channel)
            assert isinstance(discord_channel, dict)
        except (TypeError, ValueError, json.decoder.JSONDecodeError, AssertionError, SyntaxError):
            return ReturnData(False, f'Invalid discord channel: {discord_channel}')

    video = await Queue.create(glob, class_type, author, guild_id, url=url, title=title, picture=picture, duration=duration,
                  channel_name=channel_name, channel_link=channel_link, radio_info=radio_info,
                  local_number=local_number, created_at=created_at, played_duration=played_duration, chapters=chapters,
                  discord_channel=discord_channel, stream_url=stream_url)

    if is_np:
        db_guild.now_playing = await to_now_playing_class(glob, video)
    else:
        if is_queue:
            db_guild.queue[index] = await to_queue_class(glob, video)
        else:
            db_guild.history[index] = await to_history_class(glob, video)

    push_update(glob, guild_id, ['all'])
    update(glob)

    return ReturnData(True,
                      txt(ctx_guild_id, glob, 'Edited item') + f' {"h" if not is_queue else ""}{index} ' + txt(ctx_guild_id, glob,
                                                                                                       'successfully!'))

async def web_options_edit(web_data, glob: GlobalVars, form) -> ReturnData:
    log(web_data, 'web_options_edit', options=locals(), log_type='function', author=web_data.author)
    is_ctx, ctx_guild_id, ctx_author_id, ctx_guild_object = ctx_check(web_data, glob)

    try:
        stopped = form['stopped']
        loop = form['loop']
        is_radio = form['is_radio']
        language = form['language']
        response_type = form['response_type']
        search_query = form['search_query']
        buttons = form['single']
        volume = form['volume']
        buffer = form['buffer']
        history_length = form['history_length']
    except KeyError:
        return ReturnData(False, txt(ctx_guild_id, glob,
                                    'Missing form data - please contact the developer (he fucked up when doing an update)'))

    return await commands.admin.options_def(web_data, glob, server='this', stopped=stopped, loop=loop,
                                            is_radio=is_radio, language=language,
                                            response_type=response_type, search_query=search_query, buttons=buttons,
                                            volume=volume, buffer=buffer, history_length=history_length)

# TODO: Figure out how to do this
async def web_delete_guild(web_data, glob: GlobalVars, guild_id) -> ReturnData:
    log(web_data, 'web_delete_guild', options=locals(), log_type='function', author=web_data.author)
    is_ctx, ctx_guild_id, ctx_author_id, ctx_guild_object = ctx_check(web_data, glob)

    db_guilds = [db_guild_object.id for db_guild_object in glob.ses.query(Guild).all()]

    try:
        guild_id = int(guild_id)
    except (TypeError, ValueError):
        return ReturnData(False, txt(ctx_guild_id, glob, 'Invalid guild id') + f': {guild_id}')

    if guild_id not in db_guilds:
        return ReturnData(False, txt(ctx_guild_id, glob, 'Guild not found') + f': {guild_id}')

    delete_guild(glob, int(guild_id))

    update(glob)

    return ReturnData(True, txt(ctx_guild_id, glob, 'Deleted guild') + f' {guild_id} ' + txt(ctx_guild_id, glob, 'successfully!'))

async def web_disconnect_guild(web_data, glob: GlobalVars, guild_id) -> ReturnData:
    log(web_data, 'web_disconnect_guild', options=locals(), log_type='function', author=web_data.author)
    is_ctx, ctx_guild_id, ctx_author_id, ctx_guild_object = ctx_check(web_data, glob)
    try:
        guild_id = int(guild_id)
    except (TypeError, ValueError):
        return ReturnData(False, txt(ctx_guild_id, glob, 'Invalid guild id') + f': {guild_id}')

    bot_guild_ids = [guild_object.id for guild_object in glob.bot.guilds]

    if guild_id not in bot_guild_ids:
        return ReturnData(False, txt(ctx_guild_id, glob, 'Guild not found in bot.guilds') + f': {guild_id}')

    guild_to_disconnect = glob.bot.get_guild(guild_id)

    try:
        await guild_to_disconnect.leave()
    except discord.HTTPException as e:
        return ReturnData(False, f"Something Failed -> HTTPException: {e}")

    update(glob)

    return ReturnData(True, txt(ctx_guild_id, glob, 'Left guild') + f' {guild_id} ' + txt(ctx_guild_id, glob, 'successfully!'))

async def web_create_invite(web_data, glob: GlobalVars, guild_id):
    log(web_data, 'web_create_invite', options=locals(), log_type='function', author=web_data.author)
    is_ctx, ctx_guild_id, ctx_author_id, ctx_guild_object = ctx_check(web_data, glob)
    try:
        guild_object = glob.bot.get_guild(int(guild_id))
    except (TypeError, ValueError):
        return ReturnData(False, txt(ctx_guild_id, glob, 'Invalid guild id') + f': {guild_id}')

    if not guild_object:
        return ReturnData(False, txt(ctx_guild_id, glob, 'Guild not found:') + f' {guild_id}')

    try:
        guild_object_invites = await guild_object.invites()
    except discord.HTTPException as e:
        return ReturnData(False, txt(ctx_guild_id, glob, "Something Failed -> HTTPException") + f": {e}")

    if guild_object_invites:
        message = f'Guild ({guild_object.id}) invites -> {guild_object_invites}'
        log(None, message)
        await send_to_admin(glob, message)
        return ReturnData(True, message)

    if not guild_object_invites:
        try:
            channel = guild_object.text_channels[0]
            invite = await channel.create_invite()
            message = txt(ctx_guild_id, glob, 'Invite for guild') + f' ({guild_object.id}) -> {invite}'
            log(None, message)
            await send_to_admin(glob, message)
            return ReturnData(True, message)
        except discord.HTTPException as e:
            return ReturnData(False, txt(ctx_guild_id, glob, "Something Failed -> HTTPException") + f": {e}")
