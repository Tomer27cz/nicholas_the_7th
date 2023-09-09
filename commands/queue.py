from classes.data_classes import ReturnData
from classes.video_class import VideoClass
import classes.view

from utils.globals import get_sc, get_guild_dict
from utils.log import log
from utils.translate import tg
from utils.url import get_url_type, extract_yt_id
from utils.cli import get_url_probe_data
from utils.discord import to_queue, create_embed
from utils.spotify import spotify_album_to_yt_video_list, spotify_playlist_to_yt_video_list, spotify_to_yt_video, check_spotify_initialized
from utils.save import save_json, push_update
from utils.convert import convert_duration

import commands.player
import commands.voice
from commands.utils import ctx_check

from typing import Literal
import youtubesearchpython
import discord
import traceback
import asyncio
import random
from sclib import Track, Playlist

import config
from config import VLC_LOGO as vlc_logo

async def queue_command_def(ctx, url=None, position: int = None, mute_response: bool = False, force: bool = False, from_play: bool = False, probe_data: list = None, no_search: bool = False, ephemeral: bool = False, ) -> ReturnData:
    """
    This function tries to queue a song. It is called by the queue command and the play command.

    :param ctx: Context
    :param url: An input string that is either a URL or a search query
    :param position: An integer that represents the position in the queue to insert the song
    :param mute_response: Whether to mute the response or not
    :param force: Whether to force the song to play or not
    :param from_play: Set to True if the command is being called from the play command
    :param probe_data: Data from the probe command
    :param no_search: Whether to search for the song or not when the URL is not a URL
    :param ephemeral: Should the response be ephemeral
    :return: ReturnData(bool, str, VideoClass or None)
    """
    log(ctx, 'queue_command_def', [url, position, mute_response, force, from_play, probe_data, no_search, ephemeral], log_type='function', author=ctx.author)
    is_ctx, guild_id, author_id, guild_object = ctx_check(ctx)
    guild = get_guild_dict()

    if not url:
        message = tg(guild_id, "`url` is **required**")
        if not mute_response:
            await ctx.reply(message, ephemeral=True)
        return ReturnData(False, message)

    url_type, url = get_url_type(url)
    yt_id = extract_yt_id(url)

    if url_type == 'YouTube Playlist':
        if is_ctx:
            if not ctx.interaction.response.is_done():
                await ctx.defer(ephemeral=ephemeral)

        try:
            playlist_videos_result: dict = youtubesearchpython.Playlist.getVideos(url)
            playlist_videos: list = playlist_videos_result['videos']
        except KeyError:
            log(ctx, "------------------------------- playlist -------------------------")
            tb = traceback.format_exc()
            log(ctx, tb)
            log(ctx, "--------------------------------------------------------------")

            message = f'This playlist is not viewable: `{url}`'
            if not mute_response:
                await ctx.reply(message, ephemeral=ephemeral)
            return ReturnData(False, message)

        if position is not None:
            playlist_videos = list(reversed(playlist_videos))

        for index, val in enumerate(playlist_videos):
            url = f"https://www.youtube.com/watch?v={playlist_videos[index]['id']}"
            video = VideoClass('Video', author_id, url)
            to_queue(guild_id, video, position=position, copy_video=False)

        message = f"`{len(playlist_videos)}` {tg(guild_id, 'songs from playlist added to queue!')} -> [Control Panel]({config.WEB_URL}/guild/{guild_id}&key={guild[guild_id].data.key})"
        if not mute_response:
            await ctx.reply(message, ephemeral=ephemeral)
        return ReturnData(True, message)

    if url_type == 'YouTube Playlist Video' and is_ctx:
        view = classes.view.PlaylistOptionView(ctx, url, force, from_play)
        message = tg(guild_id, 'This video is from a **playlist**, do you want to add the playlist to **queue?**')
        await ctx.reply(message, view=view, ephemeral=ephemeral)
        return ReturnData(False, message)

    if url_type == 'Spotify Playlist' or url_type == 'Spotify Album':
        if not check_spotify_initialized():
            message = tg(guild_id, 'Spotify API is not initialized')
            if not mute_response:
                await ctx.reply(message, ephemeral=ephemeral)
            return ReturnData(False, message)
        adding_message = None
        if is_ctx:
            adding_message = await ctx.reply(tg(guild_id, 'Adding songs to queue... (might take a while)'), ephemeral=ephemeral)

        if url_type == 'Spotify Playlist':
            video_list = spotify_playlist_to_yt_video_list(url, author_id)
        else:
            video_list = spotify_album_to_yt_video_list(url, author_id)

        if position is not None:
            video_list = list(reversed(video_list))

        for video in video_list:
            to_queue(guild_id, video, position=position, copy_video=False)

        message = f'`{len(video_list)}` {tg(guild_id, "songs from playlist added to queue!")} -> [Control Panel]({config.WEB_URL}/guild/{guild_id}&key={guild[guild_id].data.key})'
        if is_ctx:
            await adding_message.edit(content=message)
        return ReturnData(True, message)

    if url_type == 'Spotify Track':
        if not check_spotify_initialized():
            message = tg(guild_id, 'Spotify API is not initialized')
            if not mute_response:
                await ctx.reply(message, ephemeral=ephemeral)
            return ReturnData(False, message)
        video = spotify_to_yt_video(url, author_id)
        if video is not None:
            message = to_queue(guild_id, video, position=position, copy_video=False)
            if not mute_response:
                await ctx.reply(message, ephemeral=ephemeral)
            return ReturnData(True, message)

    if url_type == 'Spotify URL':
        if not check_spotify_initialized():
            message = tg(guild_id, 'Spotify API is not initialized')
            if not mute_response:
                await ctx.reply(message, ephemeral=ephemeral)
            return ReturnData(False, message)
        video = spotify_to_yt_video(url, author_id)
        if video is None:
            message = f'{tg(guild_id, "Invalid spotify url")}: `{url}`'
            if not mute_response:
                await ctx.reply(message, ephemeral=ephemeral)
            return ReturnData(False, message)

        message = to_queue(guild_id, video, position=position, copy_video=False)
        if not mute_response:
            await ctx.reply(message, ephemeral=ephemeral)
        return ReturnData(True, message)

    if url_type == 'SoundCloud URL':
        try:
            soundcloud_api = get_sc()
            if soundcloud_api is None:
                message = tg(guild_id, 'SoundCloud API is not initialized')
                if not mute_response:
                    await ctx.reply(message, ephemeral=ephemeral)
                return ReturnData(False, message)
            track = soundcloud_api.resolve(url)
        except Exception as e:
            message = f'{tg(guild_id, "Invalid SoundCloud url")}: {url} -> {e}'
            if not mute_response:
                await ctx.reply(message, ephemeral=ephemeral)
            return ReturnData(False, message)

        if type(track) == Track:
            try:
                video = VideoClass('SoundCloud', author=author_id, url=url)
            except ValueError as e:
                if not mute_response:
                    await ctx.reply(e, ephemeral=ephemeral)
                return ReturnData(False, f"{e}")

            message = to_queue(guild_id, video, position=position, copy_video=False)
            if not mute_response:
                await ctx.reply(message, ephemeral=ephemeral)
            return ReturnData(True, message)

        if type(track) == Playlist:
            tracks = track.tracks
            if position is not None:
                tracks = list(reversed(tracks))

            for index, val in enumerate(tracks):
                duration = int(val.duration * 0.001)
                artist_url = 'https://soundcloud.com/' + track.permalink_url.split('/')[-2]

                video = VideoClass('SoundCloud', author=author_id, url=val.permalink_url, title=val.title,
                                   picture=val.artwork_url, duration=duration, channel_name=val.artist,
                                   channel_link=artist_url)
                to_queue(guild_id, video, position=position, copy_video=False)

            message = f"`{len(tracks)}` {tg(guild_id, 'songs from playlist added to queue!')} -> [Control Panel]({config.WEB_URL}/guild/{guild_id}&key={guild[guild_id].data.key})"
            if not mute_response:
                await ctx.reply(message, ephemeral=ephemeral)
            return ReturnData(True, message)

    if url_type == 'YouTube Video' or yt_id is not None:
        url = f"https://www.youtube.com/watch?v={yt_id}"
        video = VideoClass('Video', author_id, url=url)
        message = to_queue(guild_id, video, position=position, copy_video=False)
        if not mute_response:
            await ctx.reply(message, ephemeral=ephemeral)
        return ReturnData(True, message)

    if url_type == 'String with URL':
        probe, extracted_url = await get_url_probe_data(url)
        if probe:
            if not probe_data:
                probe_data = [extracted_url, extracted_url, extracted_url]

            video = VideoClass('Probe', author_id, url=extracted_url, title=probe_data[0], picture=vlc_logo, duration='Unknown', channel_name=probe_data[1], channel_link=probe_data[2])
            message = to_queue(guild_id, video, position=position, copy_video=False)
            if not mute_response:
                await ctx.reply(message, ephemeral=ephemeral)
            return ReturnData(True, message)

    if is_ctx and not no_search:
        return await search_command_def(ctx, url, display_type='short', force=force, from_play=from_play, ephemeral=ephemeral)

    message = f'`{url}` {tg(guild_id, "is not supported!")} -> [Control Panel]({config.WEB_URL}/guild/{guild_id}&key={get_guild_dict()[guild_id].data.key})'
    if not mute_response:
        await ctx.reply(message, ephemeral=ephemeral)
    return ReturnData(False, message)

async def next_up_def(ctx, url, ephemeral: bool = False):
    """
    Adds a song to the queue and plays it if the queue is empty
    :param ctx: Context
    :param url: An input url
    :param ephemeral: Should the response be ephemeral
    :return: None
    """
    log(ctx, 'next_up_def', [url, ephemeral], log_type='function', author=ctx.author)
    is_ctx, guild_id, author_id, guild_object = ctx_check(ctx)
    response = await queue_command_def(ctx, url, position=0, mute_response=True, force=True)

    if response.response:
        if guild_object.voice_client:
            if not guild_object.voice_client.is_playing():
                await commands.player.play_def(ctx)
                return
        else:
            await commands.player.play_def(ctx)
            return

        await ctx.reply(response.message, ephemeral=ephemeral)

    else:
        return

    save_json()

async def skip_def(ctx) -> ReturnData:
    """
    Skips the current song
    :param ctx: Context
    :return: ReturnData
    """
    log(ctx, 'skip_def', [], log_type='function', author=ctx.author)
    is_ctx, guild_id, author_id, guild_object = ctx_check(ctx)

    if guild_object.voice_client:
        if guild_object.voice_client.is_playing():
            stop_response = await commands.voice.stop_def(ctx, mute_response=True, keep_loop=True)
            if not stop_response.response:
                return stop_response

            await asyncio.sleep(0.5)

            play_response = await commands.player.play_def(ctx)
            if not play_response.response:
                return play_response

            return ReturnData(True, 'Skipped!')

    message = tg(guild_id, "There is **nothing to skip!**")
    await ctx.reply(message, ephemeral=True)
    return ReturnData(False, message)

async def remove_def(ctx, number: int, display_type: Literal['short', 'long'] = None, ephemeral: bool = False, list_type: Literal['queue', 'history'] = 'queue') -> ReturnData:
    """
    Removes a song from the queue or history
    :param ctx: Context
    :param number: index of the song to be removed
    :param display_type: ('short' or 'long') How the response should be displayed
    :param ephemeral: Should the response be ephemeral
    :param list_type: ('queue' or 'history') Which list to remove from
    :return: ReturnData
    """
    log(ctx, 'remove_def', [number, display_type, ephemeral], log_type='function', author=ctx.author)
    is_ctx, guild_id, author_id, guild_object = ctx_check(ctx)
    guild = get_guild_dict()

    if not display_type:
        display_type = guild[guild_id].options.response_type

    if list_type == 'queue':
        if number or number == 0 or number == '0':
            if number > len(guild[guild_id].queue):
                if not guild[guild_id].queue:
                    message = tg(guild_id, "Nothing to **remove**, queue is **empty!**")
                    await ctx.reply(message, ephemeral=True)
                    return ReturnData(False, message)
                message = tg(guild_id, "Index out of range!")
                await ctx.reply(message, ephemeral=True)
                return ReturnData(False, message)

            video = guild[guild_id].queue[number]

            message = f'REMOVED #{number} : [`{video.title}`](<{video.url}>)'

            if display_type == 'long':
                embed = create_embed(video, f'{tg(guild_id, "REMOVED #")}{number}', guild_id)
                await ctx.reply(embed=embed, ephemeral=ephemeral)
            if display_type == 'short':
                await ctx.reply(message, ephemeral=ephemeral)

            guild[guild_id].queue.pop(number)

            save_json()

            return ReturnData(True, message)

    elif list_type == 'history':
        if number or number == 0 or number == '0':
            if number > len(guild[guild_id].history):
                if not guild[guild_id].history:
                    message = tg(guild_id, "Nothing to **remove**, history is **empty!**")
                    await ctx.reply(message, ephemeral=True)
                    return ReturnData(False, message)
                message = tg(guild_id, "Index out of range!")
                await ctx.reply(message, ephemeral=True)
                return ReturnData(False, message)

            video = guild[guild_id].history[number]

            message = f'REMOVED #{number} : [`{video.title}`](<{video.url}>)'

            if display_type == 'long':
                embed = create_embed(video, f'{tg(guild_id, "REMOVED #")}{number}', guild_id)
                await ctx.reply(embed=embed, ephemeral=ephemeral)
            if display_type == 'short':
                await ctx.reply(message, ephemeral=ephemeral)

            guild[guild_id].history.pop(number)

            save_json()

            return ReturnData(True, message)

    else:
        save_json()
        message = tg(guild_id, 'Invalid list type!')
        await ctx.reply(message, ephemeral=True)
        return ReturnData(False, message)

    save_json()

    return ReturnData(False, tg(guild_id, 'No number given!'))

async def clear_def(ctx, ephemeral: bool = False) -> ReturnData:
    """
    Clears the queue
    :param ctx: Context
    :param ephemeral: Should the response be ephemeral
    :return: ReturnData
    """
    log(ctx, 'clear_def', [ephemeral], log_type='function', author=ctx.author)
    is_ctx, guild_id, author_id, guild_object = ctx_check(ctx)

    get_guild_dict()[guild_id].queue.clear()
    save_json()

    message = tg(guild_id, 'Removed **all** songs from queue')
    await ctx.reply(message, ephemeral=ephemeral)
    return ReturnData(True, message)

async def shuffle_def(ctx, ephemeral: bool = False) -> ReturnData:
    """
    Shuffles the queue
    :param ctx: Context
    :param ephemeral: Should the response be ephemeral
    :return: ReturnData
    """
    log(ctx, 'shuffle_def', [ephemeral], log_type='function', author=ctx.author)
    is_ctx, guild_id, author_id, guild_object = ctx_check(ctx)

    random.shuffle(get_guild_dict()[guild_id].queue)
    save_json()

    message = tg(guild_id, 'Songs in queue shuffled')
    await ctx.reply(message, ephemeral=ephemeral)
    return ReturnData(True, message)

async def show_def(ctx, display_type: Literal['short', 'medium', 'long'] = None, list_type: Literal['queue', 'history'] = 'queue', ephemeral: bool = False) -> ReturnData:
    """
    Shows the queue or history (only in discord)
    :param ctx: Context
    :param display_type: ('short', 'medium' or 'long') How the response should be displayed
    :param list_type: ('queue' or 'history') Which list to show
    :param ephemeral: Should the response be ephemeral
    :return: ReturnData
    """
    log(ctx, 'show_def', [display_type, list_type, ephemeral], log_type='function', author=ctx.author)
    is_ctx, guild_id, author_id, guild_object = ctx_check(ctx)
    guild = get_guild_dict()

    if not is_ctx:
        return ReturnData(False, tg(guild_id, 'Cannot use this command in WEB'))

    if list_type == 'queue':
        show_list = guild[guild_id].queue
    elif list_type == 'history':
        show_list = list(reversed(guild[guild_id].history))
    else:
        return ReturnData(False, tg(guild_id, 'Bad list_type'))

    max_embed = 5
    if not show_list:
        message = tg(guild_id, "Nothing to **show**, queue is **empty!**")
        await ctx.reply(message, ephemeral=ephemeral)
        return ReturnData(True, message)

    if not display_type:
        if len(show_list) <= max_embed:
            display_type = 'long'
        else:
            display_type = 'medium'

    if display_type == 'long':
        message = f"**THE {list_type.capitalize()}**\n **Loop** mode  `{guild[guild_id].options.loop}`,  **Display** type `{display_type}`, [Control Panel]({config.WEB_URL}/guild/{guild_id}&key={guild[guild_id].data.key})"
        await ctx.send(message, ephemeral=ephemeral, mention_author=False)

        for index, val in enumerate(show_list):
            embed = create_embed(val, f'{tg(guild_id, f"{list_type.upper()} #")}{index}', guild_id)

            await ctx.send(embed=embed, ephemeral=ephemeral, mention_author=False)

    if display_type == 'medium':
        embed = discord.Embed(title=f"Song {list_type}",
                              description=f'Loop: {guild[guild_id].options.loop} | Display type: {display_type} | [Control Panel]({config.WEB_URL}/guild/{guild_id}&key={guild[guild_id].data.key})',
                              color=0x00ff00)

        message = ''
        for index, val in enumerate(show_list):
            add = f'**{index}** --> `{convert_duration(val.duration)}`  [{val.title}](<{val.url}>) \n'

            if len(message) + len(add) > 1023:
                embed.add_field(name="", value=message, inline=False)
                message = ''
            else:
                message = message + add

        embed.add_field(name="", value=message, inline=False)

        if len(embed) < 6000:
            await ctx.reply(embed=embed, ephemeral=ephemeral, mention_author=False)
        else:
            await ctx.reply("HTTPException(discord 6000 character limit) >> using display type `short`",
                            ephemeral=ephemeral, mention_author=False)
            display_type = 'short'

    if display_type == 'short':
        send = f"**THE {list_type.upper()}**\n **Loop** mode  `{guild[guild_id].options.loop}`,  **Display** type `{display_type}`, [Control Panel]({config.WEB_URL}/guild/{guild_id}&key={guild[guild_id].data.key})"
        # noinspection PyUnresolvedReferences
        if ctx.interaction.response.is_done():
            await ctx.send(send, ephemeral=ephemeral, mention_author=False)
        else:
            await ctx.reply(send, ephemeral=ephemeral, mention_author=False)

        message = ''
        for index, val in enumerate(show_list):
            add = f'**{tg(guild_id, f"{list_type.upper()} #")}{index}**  `{convert_duration(val.duration)}`  [`{val.title}`](<{val.url}>) \n'
            if len(message) + len(add) > 2000:
                if ephemeral:
                    await ctx.send(message, ephemeral=ephemeral, mention_author=False)
                else:
                    await ctx.message.channel.send(content=message, mention_author=False)
                message = ''
            else:
                message = message + add

        if ephemeral:
            await ctx.send(message, ephemeral=ephemeral, mention_author=False)
        else:
            await ctx.message.channel.send(content=message, mention_author=False)

    save_json()

async def search_command_def(ctx, search_query, display_type: Literal['short', 'long'] = None, force: bool = False, from_play: bool = False, ephemeral: bool = False) -> ReturnData:
    """
    Search for a song and add it to the queue with buttons (only in discord)
    :param ctx: Context
    :param search_query: String to be searched for in YouTube
    :param display_type: ('short' or 'long') How the response should be displayed
    :param force: bool - if True, the song will be added to the front of the queue
    :param from_play: bool - if True, the song will be played after it is added to the queue, even if another one is already playing
    :param ephemeral: Should the response be ephemeral
    :return: ReturnData
    """
    log(ctx, 'search_command_def', [search_query, display_type, force, from_play, ephemeral], log_type='function',
        author=ctx.author)
    is_ctx, guild_id, author_id, guild_object = ctx_check(ctx)
    guild = get_guild_dict()

    if not is_ctx:
        return ReturnData(False, tg(guild_id, 'Search command cannot be used in WEB'))

    # noinspection PyUnresolvedReferences
    if not ctx.interaction.response.is_done():
        await ctx.defer(ephemeral=ephemeral)

    guild[guild_id].options.search_query = search_query

    if display_type is None:
        display_type = guild[guild_id].options.response_type

    message = f'**Search query:** `{search_query}`\n'

    if display_type == 'long':
        await ctx.reply(tg(guild_id, 'Searching...'), ephemeral=ephemeral)

    custom_search = youtubesearchpython.VideosSearch(search_query, limit=5)
    guild[guild_id].search_list.clear()

    view = classes.view.SearchOptionView(ctx, force, from_play)

    if not custom_search.result()['result']:
        message = tg(guild_id, 'No results found!')
        await ctx.reply(message, ephemeral=ephemeral)
        return ReturnData(False, message)

    for i in range(5):
        # noinspection PyTypeChecker
        url = custom_search.result()['result'][i]['link']
        video = VideoClass('Video', ctx.author.id, url)
        guild[guild_id].search_list.append(video)

        if display_type == 'long':
            embed = create_embed(video, f'{tg(guild_id, "Result #")}{i + 1}', guild_id)
            await ctx.message.channel.send(embed=embed, ephemeral=ephemeral)
        if display_type == 'short':
            message += f'{tg(guild_id, "Result #")}{i + 1} : [`{video.title}`](<{video.url}>)\n'
    if display_type == 'short':
        await ctx.reply(message, view=view, ephemeral=ephemeral)

    save_json()

# -------------------------------- IMPORT / EXPORT --------------------------------

async def export_queue(ctx, guild_id: int=None, ephemeral: bool=False):
    log(ctx, 'export_queue', [guild_id, ephemeral], log_type='function')
    is_ctx, ctx_guild_id, author_id, ctx_guild_object = ctx_check(ctx)

    if not guild_id:
        if is_ctx:
            guild_id = ctx.guild.id
        else:
            guild_id = ctx.guild_id

    try:
        guild_id = int(guild_id)
    except (ValueError, TypeError):
        message = f'({guild_id}) ' + tg(ctx_guild_id, 'is not an id')
        await ctx.reply(message, ephemeral=ephemeral)
        return ReturnData(False, message)

    try:
        queue_dict = get_guild_dict()[guild_id].queue
    except Exception as e:
        message = f"Error: {e}"
        await ctx.reply(message, ephemeral=ephemeral)
        return ReturnData(False, message)

    if not queue_dict:
        message = tg(ctx_guild_id, f"Queue is empty")
        await ctx.reply(message, ephemeral=ephemeral)
        return ReturnData(False, message)

    queue_list = []
    for item in queue_dict:
        if item.class_type == 'Video':
            data = extract_yt_id(item.url)
        elif item.class_type == 'Radio':
            data = item.radio_info['name']
        elif item.class_type == 'Local':
            data = item.local_number
        elif item.class_type == 'Probe':
            data = item.url
        elif item.class_type == 'SoundCloud':
            data = item.url
        else:
            data = item.url

        queue_list.append(f'{item.class_type}:{data}')

    queue_string = ','.join(queue_list)

    try:
        # data = queue_to_json(queue_dict)
        # await ctx.reply(file=discord.File(str(data), filename=f'queue_{guild_id}.json'), ephemeral=ephemeral)
        await ctx.reply(f"Queue String: `{queue_string}`", ephemeral=ephemeral)

        return ReturnData(True, queue_string)
    except Exception as e:
        message = f"Error: {e}"
        await ctx.reply(message, ephemeral=ephemeral)
        return ReturnData(False, message)

async def import_queue(ctx, queue_data, guild_id: int=None, ephemeral: bool=False):
    log(ctx, 'import_queue', [queue_data, guild_id, ephemeral], log_type='function')
    is_ctx, ctx_guild_id, author_id, ctx_guild_object = ctx_check(ctx)

    if type(queue_data) == discord.Attachment:
        queue_data = queue_data.read()

    if not guild_id:
        if is_ctx:
            guild_id = ctx.guild.id
        else:
            guild_id = ctx.guild_id

    try:
        guild_id = int(guild_id)
    except (ValueError, TypeError):
        message = f'({guild_id}) ' + tg(ctx_guild_id, 'is not an id')
        await ctx.reply(message, ephemeral=ephemeral)
        return ReturnData(False, message)

    queue_list = []
    for item in queue_data.split(','):
        item = item.split(':')
        if item[0] == 'Video':
            video = VideoClass('Video', author_id, item[1])
        elif item[0] == 'Radio':
            video = VideoClass('Radio', author_id, radio_info=dict(name=item[1]))
        elif item[0] == 'Local':
            video = VideoClass('Local', author_id, local_number=item[1])
        elif item[0] == 'Probe':
            video = VideoClass('Probe', author_id, url=item[1])
        elif item[0] == 'SoundCloud':
            video = VideoClass('SoundCloud', author_id, url=item[1])
        else:
            message = f"Error: {item[0]} is not a valid class type"
            await ctx.reply(message, ephemeral=ephemeral)
            return ReturnData(False, message)

        video.renew()
        queue_list.append(video)

    get_guild_dict()[guild_id].queue += queue_list
    push_update(guild_id)

    message = f"Added to queue: `{len(queue_list)}` items"
    await ctx.reply(message, ephemeral=ephemeral)

    return ReturnData(True, message)