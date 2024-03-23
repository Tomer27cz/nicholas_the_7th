import youtubesearchpython.__future__ as ytsp
from classes.data_classes import ReturnData
from classes.video_class import Queue
from classes.typed_dictionaries import VideoInfo, RadioGardenInfo, RadioInfoDict, TuneInDescribe, RadiosJSON
import classes.view

from utils.log import log
from utils.translate import txt
from utils.url import get_url_type, extract_yt_id
from utils.cli import get_url_probe_data
from utils.discord import to_queue, create_embed, create_search_embed
from utils.spotify import spotify_album_to_yt_video_list, spotify_playlist_to_yt_video_list, spotify_to_yt_video
from utils.save import update, push_update
from utils.global_vars import GlobalVars, radio_dict, sound_effects
from utils.radio import get_radio_garden_info, get_tunein_info

from database.guild import guild, clear_queue, guild_data_key

import commands.player
import commands.voice
from commands.utils import ctx_check

from typing import Literal
from time import time
import asyncio
import random
from sclib import Track, Playlist

import config

async def queue_command_def(ctx,
                            glob: GlobalVars,
                            url=None,
                            position: int = None,
                            mute_response: bool = False,
                            force: bool = False,
                            from_play: bool = False,
                            probe_data: list = None,
                            no_search: bool = False,
                            ephemeral: bool = False
                            ) -> ReturnData:
    """
    This function tries to queue a song. It is called by the queue command and the play command.
    If no_search is False, it will search for the song if the URL is not a URL.

    :param ctx: Context
    :param glob: GlobalVars
    :param url: An input string that is either a URL or a search query
    :param position: An integer that represents the position in the queue to insert the song
    :param mute_response: Whether to mute the response or not
    :param force: Whether to force the song to play or not
    :param from_play: Set to True if the command is being called from the play command
    :param probe_data: Data from the probe command
    :param no_search: Whether to search for the song or not when the URL is not a URL
    :param ephemeral: Should the response be ephemeral
    :return: ReturnData(bool, str, VideoClass child or None)
    """
    log(ctx, 'queue_command_def', locals(), log_type='function', author=ctx.author)
    is_ctx, guild_id, author, guild_object = ctx_check(ctx, glob)

    if not url:
        message = txt(guild_id, glob, "`url` is **required**")
        if not mute_response:
            await ctx.reply(message, ephemeral=True)
        return ReturnData(False, message)

    _guild_key = guild_data_key(glob, guild_id)

    # Get url type
    url_type, url = get_url_type(url)
    yt_id = extract_yt_id(url)

    if url_type in ['Spotify Playlist', 'Spotify Album', 'Spotify Track', 'Spotify URL']:
        if not glob.sp:
            message = txt(guild_id, glob, 'Spotify API is not initialized')
            if not mute_response:
                await ctx.reply(message, ephemeral=ephemeral)
            return ReturnData(False, message)

    # YOUTUBE ----------------------------------------------------------------------------------------------------------

    if url_type == 'YouTube Playlist Video' and is_ctx:
        view = classes.view.PlaylistOptionView(ctx, glob, url, force, from_play)
        message = txt(guild_id, glob, 'This video is from a **playlist**, do you want to add the playlist to **queue?**')
        view.message = await ctx.reply(message, view=view, ephemeral=ephemeral)
        return ReturnData(False, message, terminate=True)

    if url_type == 'YouTube Video' or yt_id is not None:
        url = f"https://www.youtube.com/watch?v={yt_id}"
        video = await Queue.create(glob, 'Video', author, guild_id, url=url)
        message = await to_queue(glob, guild_id, video, position=position, copy_video=False)
        if not mute_response:
            await ctx.reply(message, ephemeral=ephemeral)
        return ReturnData(True, message, video)

    if url_type == 'YouTube Playlist':
        if is_ctx:
            if not ctx.interaction.response.is_done():
                await ctx.defer(ephemeral=ephemeral)

        try:
            playlist = await ytsp.Playlist.getVideos(url)
            playlist_videos: list = playlist['videos']
        except KeyError:
            message = f'This playlist is not viewable: `{url}`'
            if not mute_response:
                await ctx.reply(message, ephemeral=ephemeral)
            return ReturnData(False, message)

        if playlist_videos is None:
            message = f'An error occurred while getting the playlist: `{url}`'
            if not mute_response:
                await ctx.reply(message, ephemeral=ephemeral)
            return ReturnData(False, message)

        if position is not None:
            playlist_videos = list(reversed(playlist_videos))

        for index, val in enumerate(playlist_videos):
            url = f"https://www.youtube.com/watch?v={playlist_videos[index]['id']}"
            video = await Queue.create(glob, 'Video', author, guild_id, url=url)
            await to_queue(glob, guild_id, video, position=position, copy_video=False, no_push=True)

        # _tasks = []
        # for index, val in enumerate(playlist_videos):
        #     url = f"https://www.youtube.com/watch?v={playlist_videos[index]['id']}"
        #     _tasks.append(Queue.create(glob, 'Video', author, guild_id, url=url))
        #
        # _videos = await asyncio.gather(*_tasks)
        # __tasks = []
        # for video in _videos:
        #     __tasks.append(to_queue(glob, guild_id, video, position=position, copy_video=False, no_push=True))
        #
        # await asyncio.gather(*__tasks)

        await push_update(glob, guild_id, ['queue'])

        message = f"`{len(playlist_videos)}` {txt(guild_id, glob, 'songs from playlist added to queue!')} -> [Control Panel]({config.WEB_URL}/guild/{guild_id}?key={_guild_key})"
        if not mute_response:
            await ctx.reply(message, ephemeral=ephemeral)
        return ReturnData(True, message)

    # SPOTIFY ----------------------------------------------------------------------------------------------------------

    if url_type == 'Spotify Playlist' or url_type == 'Spotify Album':
        adding_message = None  # here to shut up the IDE
        if is_ctx:
            adding_message = await ctx.reply(txt(guild_id, glob, 'Adding songs to queue... (might take a while)'),
                                             ephemeral=ephemeral)

        if url_type == 'Spotify Playlist':
            video_list = await spotify_playlist_to_yt_video_list(glob, url, author, guild_id)
        else:
            video_list = await spotify_album_to_yt_video_list(glob, url, author, guild_id)

        if position is not None:
            video_list = list(reversed(video_list))

        for video in video_list:
            await to_queue(glob, guild_id, video, position=position, copy_video=False, no_push=True)
        await push_update(glob, guild_id, ['queue'])

        message = f'`{len(video_list)}` {txt(guild_id, glob, "songs from playlist added to queue!")} -> [Control Panel]({config.WEB_URL}/guild/{guild_id}?key={_guild_key})'
        if is_ctx and adding_message:
            await adding_message.edit(content=message)
        return ReturnData(True, message)

    if url_type in ['Spotify Track', 'Spotify URL']:
        video = await spotify_to_yt_video(glob, url, author, guild_id)
        if video is None:
            message = f'{txt(guild_id, glob, "Invalid spotify url")}: `{url}`'
            if not mute_response:
                await ctx.reply(message, ephemeral=ephemeral)
            return ReturnData(False, message)

        message = await to_queue(glob, guild_id, video, position=position, copy_video=False)
        if not mute_response:
            await ctx.reply(message, ephemeral=ephemeral)
        return ReturnData(True, message, video)

    # SOUND CLOUD ------------------------------------------------------------------------------------------------------

    if url_type == 'SoundCloud URL':
        try:
            soundcloud_api = glob.sc
            if soundcloud_api is None:
                message = txt(guild_id, glob, 'SoundCloud API is not initialized')
                if not mute_response:
                    await ctx.reply(message, ephemeral=ephemeral)
                return ReturnData(False, message)
            track = soundcloud_api.resolve(url)
        except Exception as e:
            message = f'{txt(guild_id, glob, "Invalid SoundCloud url")}: {url} -> {e}'
            if not mute_response:
                await ctx.reply(message, ephemeral=ephemeral)
            return ReturnData(False, message)

        if isinstance(track, Track):
            try:
                video = await Queue.create(glob, 'SoundCloud', author, guild_id, url=url)
            except ValueError as e:
                if not mute_response:
                    await ctx.reply(e, ephemeral=ephemeral)
                return ReturnData(False, f"{e}")

            message = await to_queue(glob, guild_id, video, position=position, copy_video=False)
            if not mute_response:
                await ctx.reply(message, ephemeral=ephemeral)
            return ReturnData(True, message, video)

        if isinstance(track, Playlist):
            tracks = track.tracks
            if position is not None:
                tracks = list(reversed(tracks))

            for index, val in enumerate(tracks):
                duration = int(val.duration * 0.001)
                artist_url = 'https://soundcloud.com/' + track.permalink_url.split('/')[-2]

                video = await Queue.create(glob, 'SoundCloud', author=author, guild_id=guild_id, url=val.permalink_url,
                                           title=val.title, picture=val.artwork_url, duration=duration, channel_name=val.artist,
                                           channel_link=artist_url)
                await to_queue(glob, guild_id, video, position=position, copy_video=False, no_push=True)
            await push_update(glob, guild_id, ['queue'])

            message = f"`{len(tracks)}` {txt(guild_id, glob, 'songs from playlist added to queue!')} -> [Control Panel]({config.WEB_URL}/guild/{guild_id}?key={_guild_key})"
            if not mute_response:
                await ctx.reply(message, ephemeral=ephemeral)
            return ReturnData(True, message)

    # RADIO CZ ---------------------------------------------------------------------------------------------------------

    if url_type == 'RadioCz':
        radio_id = url.split(':')[1]
        if radio_id not in radio_dict.keys():
            message = f'Invalid radio id: `{radio_id}`'
            if not mute_response:
                await ctx.reply(message, ephemeral=ephemeral)
            return ReturnData(False, message)

        radio: RadiosJSON = radio_dict[str(radio_id)]

        radio_info: RadioInfoDict = {
            'type': 'radia_cz',
            'id': radio['id'],
            'station_name': radio['name'],
            'station_picture': radio['logo'],
            'station_website': radio['link'],
            'now_title': None,
            'now_artist': None,
            'now_picture': None,
            'url': radio['nowplay'],
            'stream': radio['streams']['stream'][0]['url'] if type(radio['streams']['stream']) is list else radio['streams']['stream']['url'],
            'last_update': None
        }

        video = await Queue.create(glob, 'RadioCz', author, guild_id, radio_info=radio_info)

        message = await to_queue(glob, guild_id, video, position=position, copy_video=False, stream_strip=False)
        if not mute_response:
            await ctx.reply(message, ephemeral=ephemeral)
        return ReturnData(True, message, video)

    # RADIO GARDEN -----------------------------------------------------------------------------------------------------

    if url_type == 'RadioGarden':
        resp = await get_radio_garden_info(url)
        radio_info: RadioGardenInfo = resp[1]
        if not resp[0]:
            message = f'Failed to get radio.garden info: `{url}`'
            if not mute_response:
                await ctx.reply(message, ephemeral=ephemeral)
            return ReturnData(False, message)

        ri: RadioInfoDict = {
            'type': 'garden',
            'id': radio_info['id'],
            'station_name': radio_info['title'],
            'station_picture': 'https://radio.garden/icons/favicon.png',
            'station_website': radio_info['website'],
            'now_title': None,
            'now_artist': None,
            'now_picture': None,
            'url': f"https://radio.garden{radio_info['url']}",
            'stream': radio_info['stream'],
            'last_update': None
        }

        video = await Queue.create(glob, 'RadioGarden', author, guild_id, radio_info=ri)

        message = await to_queue(glob, guild_id, video, position=position, copy_video=False, stream_strip=False)
        if not mute_response:
            await ctx.reply(message, ephemeral=ephemeral)
        return ReturnData(True, message, video)

    # RADIO TUNEIN -----------------------------------------------------------------------------------------------------

    if url_type == 'RadioTuneIn':
        resp = await get_tunein_info(url)
        ri: TuneInDescribe = resp[1]
        if not resp[0]:
            message = f'Failed to get TuneIn info: `{url}`'
            if not mute_response:
                await ctx.reply(message, ephemeral=ephemeral)
            return ReturnData(False, message)

        radio_info: RadioInfoDict = {
            'type': 'tunein',
            'id': ri['guide_id'],
            'station_name': ri['name'],
            'station_picture': ri['logo'],
            'station_website': ri['url'],
            'now_title': ri['current_song'] if ri['current_song'] is not None else None,
            'now_artist': ri['current_artist'] if ri['current_artist'] is not None else None,
            'now_picture': ri['logo'] if ri['current_artist_art'] is None else ri['current_artist_art'] if ri['current_album_art'] is None else ri['current_album_art'],
            'url': ri['tunein_url'],
            'stream': resp[2],
            'last_update': int(time())
        }

        video = await Queue.create(glob, 'RadioTuneIn', author, guild_id, radio_info=radio_info)

        message = await to_queue(glob, guild_id, video, position=position, copy_video=False, stream_strip=False)
        if not mute_response:
            await ctx.reply(message, ephemeral=ephemeral)
        return ReturnData(True, message, video)

    # LOCAL FILE -------------------------------------------------------------------------------------------------------

    if url_type == 'Local':
        try:
            code = int(url.split(':')[1])
        except (ValueError, TypeError):
            message = f'Invalid local file code: `{url}`'
            if not mute_response:
                await ctx.reply(message, ephemeral=ephemeral)
            return ReturnData(False, message)

        if code > len(sound_effects) or code < 1:
            message = f'Local file code out of range: `{url}`'
            if not mute_response:
                await ctx.reply(message, ephemeral=ephemeral)
            return ReturnData(False, message)

        name = sound_effects[code-1]
        video = await Queue.create(glob, 'Local', author, guild_id, url=f'sound_effects/{name}', title=name, local_number=code, picture=config.VLC_LOGO, duration='Unknown')

        message = await to_queue(glob, guild_id, video, position=position, copy_video=False)
        if not mute_response:
            await ctx.reply(message, ephemeral=ephemeral)
        return ReturnData(True, message, video)

    # URL --------------------------------------------------------------------------------------------------------------

    if url_type == 'String with URL':
        probe, extracted_url = await get_url_probe_data(url)
        if probe:
            if not probe_data:
                probe_data = [extracted_url, extracted_url, extracted_url]

            video = await Queue.create(glob, 'Probe', author, guild_id, url=extracted_url, title=probe_data[0],
                                       picture=config.VLC_LOGO, duration='Unknown', channel_name=probe_data[1],
                                       channel_link=probe_data[2])
            message = await to_queue(glob, guild_id, video, position=position, copy_video=False)
            if not mute_response:
                await ctx.reply(message, ephemeral=ephemeral)
            return ReturnData(True, message, video)

    # SEARCH -----------------------------------------------------------------------------------------------------------

    if is_ctx and not no_search:
        return await search_command_def(ctx, glob, url, display_type='short', force=force, from_play=from_play, ephemeral=ephemeral)

    message = f'`{url}` {txt(guild_id, glob, "is not supported!")} -> [Control Panel]({config.WEB_URL}/guild/{guild_id}?key={_guild_key})'
    if not mute_response:
        await ctx.reply(message, ephemeral=ephemeral)
    return ReturnData(False, message)

async def nextup_def(ctx, glob: GlobalVars, url, ephemeral: bool = False):
    """
    Adds a song to the queue and plays it if the queue is empty
    :param ctx: Context
    :param glob: GlobalVars
    :param url: An input url
    :param ephemeral: Should the response be ephemeral
    :return: None
    """
    log(ctx, 'nextup_def', options=locals(), log_type='function', author=ctx.author)
    is_ctx, guild_id, author, guild_object = ctx_check(ctx, glob)
    response = await queue_command_def(ctx, glob, url, position=0, mute_response=True, force=True)

    if response.response:
        if guild_object.voice_client:
            if not guild_object.voice_client.is_playing():
                await commands.player.play_def(ctx, glob)
                return
        else:
            await commands.player.play_def(ctx, glob)
            return

        await ctx.reply(response.message, ephemeral=ephemeral)

    else:
        return

    update(glob)

async def skip_def(ctx, glob: GlobalVars) -> ReturnData:
    """
    Skips the current song
    :param ctx: Context
    :param glob: GlobalVars
    :return: ReturnData
    """
    log(ctx, 'skip_def', options=locals(), log_type='function', author=ctx.author)
    is_ctx, guild_id, author, guild_object = ctx_check(ctx, glob)

    if guild_object.voice_client:
        if guild_object.voice_client.is_playing():
            play_response = await commands.player.play_def(ctx, glob, force=True)
            if not play_response.response:
                return play_response

            return ReturnData(True, 'Skipped!')

    message = txt(guild_id, glob, "There is **nothing to skip!**")
    await ctx.reply(message, ephemeral=True)
    return ReturnData(False, message)

async def remove_def(ctx, glob: GlobalVars, number, display_type: Literal['short', 'long'] = None,
                     ephemeral: bool = False, list_type: Literal['queue', 'history'] = 'queue') -> ReturnData:
    """
    Removes a song from the queue or history
    :param ctx: Context
    :param glob: GlobalVars
    :param number: index of the song to be removed
    :param display_type: ('short' or 'long') How the response should be displayed
    :param ephemeral: Should the response be ephemeral
    :param list_type: ('queue' or 'history') Which list to remove from
    :return: ReturnData
    """
    log(ctx, 'remove_def', options=locals(), log_type='function', author=ctx.author)
    is_ctx, guild_id, author, guild_object = ctx_check(ctx, glob)

    try:
        number = int(number)
    except ValueError:
        message = txt(guild_id, glob, 'Invalid number!')
        await ctx.reply(message, ephemeral=True)
        return ReturnData(False, message)

    db_guild = guild(glob, guild_id)

    if not display_type:
        display_type = db_guild.options.response_type

    if list_type == 'queue':
        if number or number == 0 or number == '0':
            if number > len(db_guild.queue):
                if not db_guild.queue:
                    message = txt(guild_id, glob, "Nothing to **remove**, queue is **empty!**")
                    await ctx.reply(message, ephemeral=True)
                    return ReturnData(False, message)
                message = txt(guild_id, glob, "Index out of range!")
                await ctx.reply(message, ephemeral=True)
                return ReturnData(False, message)

            video = db_guild.queue[number]

            message = f'REMOVED #{number} : [`{video.title}`](<{video.url}>)'

            if display_type == 'long':
                embed = create_embed(glob, video, f'{txt(guild_id, glob, "REMOVED #")}{number}', guild_id)
                await ctx.reply(embed=embed, ephemeral=ephemeral)
            if display_type == 'short':
                await ctx.reply(message, ephemeral=ephemeral)

            db_guild.queue.pop(number)

            await push_update(glob, guild_id, ['queue'])
            update(glob)

            return ReturnData(True, message)

    elif list_type == 'history':
        if number or number == 0 or number == '0':
            if number > len(db_guild.history):
                if not db_guild.history:
                    message = txt(guild_id, glob, "Nothing to **remove**, history is **empty!**")
                    await ctx.reply(message, ephemeral=True)
                    return ReturnData(False, message)
                message = txt(guild_id, glob, "Index out of range!")
                await ctx.reply(message, ephemeral=True)
                return ReturnData(False, message)

            video = db_guild.history[number]

            message = f'REMOVED #{number} : [`{video.title}`](<{video.url}>)'

            if display_type == 'long':
                embed = create_embed(glob, video, f'{txt(guild_id, glob, "REMOVED #")}{number}', guild_id)
                await ctx.reply(embed=embed, ephemeral=ephemeral)
            if display_type == 'short':
                await ctx.reply(message, ephemeral=ephemeral)

            db_guild.history.pop(number)

            await push_update(glob, guild_id, ['history'])
            update(glob)

            return ReturnData(True, message)

    else:
        update(glob)
        message = txt(guild_id, glob, 'Invalid list type!')
        await ctx.reply(message, ephemeral=True)
        return ReturnData(False, message)

    update(glob)

    return ReturnData(False, txt(guild_id, glob, 'No number given!'))

async def clear_def(ctx, glob: GlobalVars, ephemeral: bool = False) -> ReturnData:
    """
    Clears the queue
    :param ctx: Context
    :param glob: GlobalVars
    :param ephemeral: Should the response be ephemeral
    :return: ReturnData
    """
    log(ctx, 'clear_def', options=locals(), log_type='function', author=ctx.author)
    is_ctx, guild_id, author, guild_object = ctx_check(ctx, glob)

    queue_count = clear_queue(glob, guild_id)
    await push_update(glob, guild_id, ['queue'])
    update(glob)

    message = txt(guild_id, glob, 'Removed **all** songs from queue') + ' -> ' + f'`{queue_count}` songs removed'
    await ctx.reply(message, ephemeral=ephemeral)
    return ReturnData(True, message)

async def shuffle_def(ctx, glob: GlobalVars, ephemeral: bool = False) -> ReturnData:
    """
    Shuffles the queue
    :param ctx: Context
    :param glob: GlobalVars
    :param ephemeral: Should the response be ephemeral
    :return: ReturnData
    """
    log(ctx, 'shuffle_def', options=locals(), log_type='function', author=ctx.author)
    is_ctx, guild_id, author, guild_object = ctx_check(ctx, glob)

    queue = guild(glob, guild_id).queue
    rand_list = list(range(len(queue)))
    random.shuffle(rand_list)

    for index, vid in enumerate(queue):
        vid.position = rand_list.index(index)
    glob.ses.commit()
    await push_update(glob, guild_id, ['queue'])
    update(glob)

    message = txt(guild_id, glob, 'Songs in queue shuffled')
    await ctx.reply(message, ephemeral=ephemeral)
    return ReturnData(True, message)

async def search_command_def(ctx, glob: GlobalVars, search_query, display_type: Literal['short', 'long'] = None,
                             force: bool = False, from_play: bool = False, ephemeral: bool = False) -> ReturnData:
    """
    Search for a song and add it to the queue with single (only in discord)
    :param ctx: Context
    :param glob: GlobalVars
    :param search_query: String to be searched for in YouTube
    :param display_type: ('short' or 'long') How the response should be displayed
    :param force: bool - if True, the song will be added to the front of the queue
    :param from_play: bool - if True, the song will be played after it is added to the queue, even if another one is already playing
    :param ephemeral: Should the response be ephemeral
    :return: ReturnData
    """
    log(ctx, 'search_command_def', options=locals(), log_type='function',
        author=ctx.author)
    is_ctx, guild_id, author, guild_object = ctx_check(ctx, glob)

    if not is_ctx:
        return ReturnData(False, txt(guild_id, glob, 'Search command cannot be used in WEB'))

    if display_type == 'long' and ephemeral:
        message = txt(guild_id, glob, 'Cannot use display type `long` user-only')
        await ctx.reply(message, ephemeral=ephemeral)
        return ReturnData(False, message)

    # noinspection PyUnresolvedReferences
    if ctx.interaction:
        if not ctx.interaction.response.is_done():
            await ctx.defer(ephemeral=ephemeral)

    db_guild = guild(glob, guild_id)
    db_guild.options.search_query = search_query

    if display_type is None:
        display_type = db_guild.options.response_type

    message = f'**Search query:** `{search_query}`\n'
    if display_type == 'long':
        await ctx.reply(txt(guild_id, glob, 'Searching...'), ephemeral=ephemeral)

    cs = ytsp.VideosSearch(search_query, limit=5)
    csr = await cs.next()
    custom_search: list[VideoInfo] = csr['result']

    if not custom_search:
        message = txt(guild_id, glob, 'No results found!')
        await ctx.reply(message, ephemeral=ephemeral)
        return ReturnData(False, message)

    for i in range(5):
        if display_type == 'long':
            embed = create_search_embed(glob, custom_search[i], f'{txt(guild_id, glob, "Result #")}{i + 1}', guild_id)
            await ctx.message.channel.send(embed=embed)
        if display_type == 'short':
            message += f'**#{i + 1}** [`{custom_search[i]["title"]}`](<{custom_search[i]["link"]}>) by [`{custom_search[i]["channel"]["name"]}`](<{custom_search[i]["channel"]["link"]}>)\n'

    view = classes.view.SearchOptionView(ctx, glob, custom_search, force, from_play)
    if display_type == 'long':
        view.message = await ctx.message.channel.send("Choose a song", view=view)
    if display_type == 'short':
        view.message = await ctx.reply(message, view=view, ephemeral=ephemeral)

    update(glob)

    return ReturnData(False, 'Process terminated', terminate=True)


# # -------------------------------- IMPORT / EXPORT --------------------------------
#
# async def export_queue(ctx, guild_id: int=None, ephemeral: bool=False):
#     log(ctx, 'export_queue', [guild_id, ephemeral], log_type='function')
#     is_ctx, ctx_guild_id, author, ctx_guild_object = ctx_check(ctx, bot, ses)
#
#     if not guild_id:
#         if is_ctx:
#             guild_id = ctx.guild.id
#         else:
#             guild_id = ctx.guild_id
#
#     try:
#         guild_id = int(guild_id)
#     except (ValueError, TypeError):
#         message = f'({guild_id}) ' + txt(ctx_guild_id, glob, 'is not an id')
#         await ctx.reply(message, ephemeral=ephemeral)
#         return ReturnData(False, message)
#
#     try:
#         queue_dict = guild(glob, guild_id).queue
#     except Exception as e:
#         message = f"Error: {e}"
#         await ctx.reply(message, ephemeral=ephemeral)
#         return ReturnData(False, message)
#
#     if not queue_dict:
#         message = txt(ctx_guild_id, glob, f"Queue is empty")
#         await ctx.reply(message, ephemeral=ephemeral)
#         return ReturnData(False, message)
#
#     queue_list = []
#     for item in queue_dict:
#         if item.class_type == 'Video':
#             data = extract_yt_id(item.url)
#         elif item.class_type == 'Radio':
#             data = item.radio_info['name']
#         elif item.class_type == 'Local':
#             data = item.local_number
#         elif item.class_type == 'Probe':
#             data = item.url
#         elif item.class_type == 'SoundCloud':
#             data = item.url
#         else:
#             data = item.url
#
#         queue_list.append(f'{item.class_type}:{data}')
#
#     queue_string = ','.join(queue_list)
#
#     try:
#         # data = queue_to_json(queue_dict)
#         # await ctx.reply(file=discord.File(str(data), filename=f'queue_{guild_id}.json'), ephemeral=ephemeral)
#         await ctx.reply(f"Queue String: `{queue_string}`", ephemeral=ephemeral)
#
#         return ReturnData(True, queue_string)
#     except Exception as e:
#         message = f"Error: {e}"
#         await ctx.reply(message, ephemeral=ephemeral)
#         return ReturnData(False, message)
#
# async def import_queue(ctx, queue_data, guild_id: int=None, ephemeral: bool=False):
#     log(ctx, 'import_queue', [queue_data, guild_id, ephemeral], log_type='function')
#     is_ctx, ctx_guild_id, author, ctx_guild_object = ctx_check(ctx, bot, ses)
#
#     if type(queue_data) == discord.Attachment:
#         queue_data = queue_data.read()
#
#     if not guild_id:
#         if is_ctx:
#             guild_id = ctx.guild.id
#         else:
#             guild_id = ctx.guild_id
#
#     try:
#         guild_id = int(guild_id)
#     except (ValueError, TypeError):
#         message = f'({guild_id}) ' + txt(ctx_guild_id, glob, 'is not an id')
#         await ctx.reply(message, ephemeral=ephemeral)
#         return ReturnData(False, message)
#
#     queue_list = []
#     for item in queue_data.split(','):
#         item = item.split(':')
#         if item[0] == 'Video':
#             video = await Queue.create('Video', author, guild_id, item[1])
#         elif item[0] == 'Radio':
#             video = await Queue.create('Radio', author, guild_id, radio_info=dict(name=item[1]))
#         elif item[0] == 'Local':
#             video = await Queue.create('Local', author, guild_id, local_number=item[1])
#         elif item[0] == 'Probe':
#             video = await Queue.create('Probe', author, guild_id, url=item[1])
#         elif item[0] == 'SoundCloud':
#             video = await Queue.create('SoundCloud', author, guild_id, url=item[1])
#         else:
#             message = f"Error: {item[0]} is not a valid class type"
#             await ctx.reply(message, ephemeral=ephemeral)
#             return ReturnData(False, message)
#
#         video.renew()
#         queue_list.append(await to_queue_class(video))
#
#     guild(glob, guild_id).queue += queue_list
#     ses.commit()
#     await push_update(glob, guild_id)
#
#     message = f"Added to queue: `{len(queue_list)}` items"
#     await ctx.reply(message, ephemeral=ephemeral)
#
#     return ReturnData(True, message)
