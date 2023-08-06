from classes.video_class import VideoClass
from classes.data_classes import ReturnData
import classes.view

from utils.source import GetSource
from utils.log import log
from utils.translate import tg
from utils.save import save_json
from utils.discord import now_to_history, create_embed, to_queue
from utils.globals import get_guild_dict, get_bot, get_radio_dict
from utils.video_time import set_started, set_new_time

import commands.voice
import commands.queue
from commands.utils import ctx_check

import discord
from discord import app_commands
from typing import Literal
from os import path, listdir
import asyncio
import sys
import traceback

import config
from vars import *

# ----------- SOUND EFFECTS ---------------------

def load_sound_effects():
    """
    Loads all sound effects from the sound_effects folder
    to the global variable all_sound_effects
    """
    global all_sound_effects
    all_sound_effects = ["No sound effects found"]
    try:
        all_sound_effects = listdir('sound_effects')
        for file_index, file_val in enumerate(all_sound_effects):
            all_sound_effects[file_index] = all_sound_effects[file_index][:len(file_val) - 4]
    except FileNotFoundError:
        all_sound_effects = ["No sound effects found"]
    log(None, 'Loaded sound_effects folder')
all_sound_effects = ["No sound effects found"]
load_sound_effects()

async def play_def(ctx, url=None, force=False, mute_response=False, after=False) -> ReturnData:
    log(ctx, 'play_def', [url, force, mute_response, after], log_type='function', author=ctx.author)
    is_ctx, guild_id, author_id, guild_object = ctx_check(ctx)
    guild = get_guild_dict()
    response = ReturnData(False, tg(guild_id, 'Unknown error'))

    notif = f' -> [Control Panel]({config.WEB_URL}/guild/{guild_id}&key={guild[guild_id].data.key})'

    if after and guild[guild_id].options.stopped:
        log(ctx, "play_def -> stopped play next loop")
        now_to_history(guild_id)
        return ReturnData(False, tg(guild_id, "Stopped play next loop"))

    voice = guild_object.voice_client

    if not voice:
        if not is_ctx:
            return ReturnData(False, tg(guild_id, 'Bot is not connected to a voice channel'))

        if ctx.author.voice is None:
            message = tg(guild_id, "You are **not connected** to a voice channel")
            if not mute_response:
                await ctx.reply(message)
            return ReturnData(False, message)

    if is_ctx:
        if not ctx.interaction.response.is_done():
            await ctx.defer()

    if url:
        if voice:
            if not voice.is_playing():
                force = True

        position = 0 if force else None
        response = await commands.queue.queue_command_def(ctx, url=url, position=position, mute_response=True, force=force, from_play=True)

        if not response or not response.response:
            return response

    if not guild_object.voice_client:
        # if not is_ctx:
        #     if not ctx.interaction.response.is_done():
        #         await ctx.defer()
        join_response = await commands.voice.join_def(ctx, None, True)
        voice = guild_object.voice_client
        if not join_response.response:
            return join_response

    if voice.is_playing():
        if not guild[guild_id].options.is_radio and not force:
            if url:
                if response.video is not None:
                    message = f'{tg(guild_id, "**Already playing**, added to queue")}: [`{response.video.title}`](<{response.video.url}>) {notif}'
                    if not mute_response:
                        await ctx.reply(message)
                    return ReturnData(False, message)

                message = f'{tg(guild_id, "**Already playing**, added to queue")} {notif}'
                if not mute_response:
                    await ctx.reply(message)
                return ReturnData(False, message)

            message = f'{tg(guild_id, "**Already playing**")} {notif}'
            if not mute_response:
                await ctx.reply(message)
            return ReturnData(False, message)

        voice.stop()
        guild[guild_id].options.stopped = True
        guild[guild_id].options.is_radio = False

    if voice.is_paused():
        return await commands.voice.resume_def(ctx)

    if not guild[guild_id].queue:
        message = f'{tg(guild_id, "There is **nothing** in your **queue**")} {notif}'
        if not after and not mute_response:
            await ctx.reply(message)
        now_to_history(guild_id)
        return ReturnData(False, message)

    video = guild[guild_id].queue[0]
    now_to_history(guild_id)

    if video.class_type not in ['Video', 'Probe', 'SoundCloud']:
        guild[guild_id].queue.pop(0)
        if video.class_type == 'Radio':
            return await radio_def(ctx, video.title)
        if video.class_type == 'Local':
            return await ps_def(ctx, video.local_number)

        message = tg(guild_id, "Unknown type")
        if not mute_response:
            await ctx.reply(message)
        return ReturnData(False, message)

    if not force:
        guild[guild_id].options.stopped = False

    try:
        source, chapters = await GetSource.create_source(guild_id, video.url, source_type=video.class_type, video_class=video)
        voice.play(source, after=lambda e: asyncio.run_coroutine_threadsafe(play_def(ctx, after=True), get_bot().loop))

        await commands.voice.volume_command_def(ctx, guild[guild_id].options.volume * 100, False, True)

        # Variables update
        guild[guild_id].options.stopped = False
        # video variables
        set_started(video, guild_object, chapters=chapters)

        # Queue update
        # if guild[guild_id].options.loop:
        #     to_queue(guild_id, video)
        guild[guild_id].queue.pop(0)

        save_json()

        # Response
        options = guild[guild_id].options
        response_type = options.response_type

        message = f'{tg(guild_id, "Now playing")} [`{video.title}`](<{video.url}>) {notif}'
        view = classes.view.PlayerControlView(ctx)

        if response_type == 'long':
            if not mute_response:
                embed = create_embed(video, tg(guild_id, "Now playing"), guild_id)
                if options.buttons:
                    await ctx.reply(embed=embed, view=view)
                else:
                    await ctx.reply(embed=embed)
            return ReturnData(True, message)

        elif response_type == 'short':
            if not mute_response:
                if options.buttons:
                    await ctx.reply(message, view=view)
                else:
                    await ctx.reply(message)
            return ReturnData(True, message)

        else:
            return ReturnData(True, message)

    except (AttributeError, IndexError, TypeError, discord.errors.ClientException,
            discord.errors.NotFound):
        log(ctx, "------------------------------- play -------------------------")
        tb = traceback.format_exc()
        log(ctx, tb)
        log(ctx, "--------------------------------------------------------------")
        message = f'{tg(guild_id, "An **error** occurred while trying to play the song")} {get_bot().get_user(my_id).mention} ({sys.exc_info()[0]})'
        await ctx.reply(message)
        return ReturnData(False, message)

async def radio_def(ctx, favourite_radio: Literal['Rádio BLANÍK', 'Rádio BLANÍK CZ', 'Evropa 2', 'Fajn Radio', 'Hitrádio PopRock', 'Český rozhlas Pardubice', 'Radio Beat', 'Country Radio', 'Radio Kiss', 'Český rozhlas Vltava', 'Hitrádio Černá Hora'] = None,
                    radio_code: int = None) -> ReturnData:
    """
    Play radio
    :param ctx: Context
    :param favourite_radio: ('Rádio BLANÍK', 'Rádio BLANÍK CZ', 'Evropa 2', 'Fajn Radio', 'Hitrádio PopRock', 'Český rozhlas Pardubice', 'Radio Beat', 'Country Radio', 'Radio Kiss', 'Český rozhlas Vltava', 'Hitrádio Černá Hora')
    :param radio_code: (0-95)
    :return: ReturnData
    """
    log(ctx, 'radio_def', [favourite_radio, radio_code], log_type='function', author=ctx.author)
    is_ctx, guild_id, author_id, guild_object = ctx_check(ctx)
    guild = get_guild_dict()
    radio_dict = get_radio_dict()

    # noinspection PyUnresolvedReferences
    if is_ctx:
        if not ctx.interaction.response.is_done():
            await ctx.defer()
    if favourite_radio and radio_code:
        message = tg(guild_id, "Only **one** argument possible!")
        await ctx.reply(message, ephemeral=True)
        return ReturnData(False, message)

    if favourite_radio:
        radio_type: str = favourite_radio
    elif radio_code:
        radio_type: str = list(radio_dict.keys())[radio_code]
    else:
        radio_type: str = 'Evropa 2'

    if not guild_object.voice_client:
        response = await commands.voice.join_def(ctx, None, True)
        if not response.response:
            return response

    if guild_object.voice_client.is_playing():
        await commands.voice.stop_def(ctx, mute_response=True)

    guild[guild_id].options.is_radio = True

    url = radio_dict[radio_type]['stream']
    video = VideoClass('Radio', author_id, radio_info=dict(name=radio_type), stream_url=url)
    video.renew()

    source, chapters = await GetSource.create_source(guild_id, url, source_type='Radio', video_class=video)
    set_started(video, chapters=chapters, guild_object=guild_object)

    guild_object.voice_client.play(source)

    await commands.voice.volume_command_def(ctx, guild[guild_id].options.volume * 100, False, True)

    embed = create_embed(video, tg(guild_id, "Now playing"), guild_id)
    if guild[guild_id].options.buttons:
        view = classes.view.PlayerControlView(ctx)
        await ctx.reply(embed=embed, view=view)
    else:
        await ctx.reply(embed=embed)

    save_json()

    return ReturnData(True, tg(guild_id, "Radio **started**"))

async def ps_def(ctx, effect_number: app_commands.Range[int, 1, len(all_sound_effects)], mute_response: bool = False) -> ReturnData:
    """
    Play sound effect
    :param ctx: Context
    :param effect_number: index of sound effect (show all sound effects with sound_effects_def)
    :param mute_response: bool - Should bot response be muted
    :return: ReturnData
    """
    log(ctx, 'ps_def', [effect_number, mute_response], log_type='function', author=ctx.author)
    is_ctx, guild_id, author_id, guild_object = ctx_check(ctx)
    guild = get_guild_dict()
    guild[guild_id].options.is_radio = False
    try:
        name = all_sound_effects[effect_number]
    except IndexError:
        message = tg(guild_id, "Number **not in list** (use `/sound` to get all sound effects)")
        if not mute_response:
            await ctx.reply(message, ephemeral=True)
        return ReturnData(False, message)

    filename = f"{config.PARENT_DIR}sound_effects/{name}.mp3"
    if path.exists(filename):
        source, chapters = await GetSource.create_source(guild_id, filename, source_type='Local')
    else:
        filename = f"{config.PARENT_DIR}sound_effects/{name}.wav"
        if path.exists(filename):
            source, chapters = await GetSource.create_source(guild_id, filename, source_type='Local')
        else:
            message = tg(guild_id, "No such file/website supported")
            if not mute_response:
                await ctx.reply(message, ephemeral=True)
            return ReturnData(False, message)

    if not guild_object.voice_client:
        join_response = await commands.voice.join_def(ctx, None, True)
        if not join_response.response:
            return join_response

    stop_response = await commands.voice.stop_def(ctx, mute_response=True)
    if not stop_response.response:
        return stop_response

    video = VideoClass('Local', author_id, title=name, duration='Unknown', local_number=effect_number, stream_url=filename)
    set_started(video, guild_object, chapters=chapters)

    voice = guild_object.voice_client
    voice.play(source)
    await commands.voice.volume_command_def(ctx, guild[guild_id].options.volume * 100, False, True)

    message = tg(guild_id, "Playing sound effect number") + f" `{effect_number}`"
    if not mute_response:
        await ctx.reply(message, ephemeral=True)
    return ReturnData(True, message)

async def now_def(ctx, ephemeral: bool = False) -> ReturnData:
    """
    Show now playing song
    :param ctx: Context
    :param ephemeral: Should bot response be ephemeral
    :return: ReturnData
    """
    log(ctx, 'now_def', [ephemeral], log_type='function', author=ctx.author)
    is_ctx, guild_id, author_id, guild_object = ctx_check(ctx)
    guild = get_guild_dict()
    if not is_ctx:
        return ReturnData(False, tg(guild_id, 'This command cant be used in WEB'))

    if ctx.voice_client:
        if ctx.voice_client.is_playing():
            guild[guild_id].now_playing.renew()
            embed = create_embed(guild[guild_id].now_playing, tg(guild_id, "Now playing"), guild_id)

            view = classes.view.PlayerControlView(ctx)

            if guild[guild_id].options.buttons:
                await ctx.reply(embed=embed, view=view, ephemeral=ephemeral)
                return ReturnData(True, tg(guild_id, "Now playing"))

            await ctx.reply(embed=embed, ephemeral=ephemeral)
            return ReturnData(True, tg(guild_id, "Now playing"))

        if ctx.voice_client.is_paused():
            message = f'{tg(guild_id, "There is no song playing right **now**, but there is one **paused:**")} [`{guild[guild_id].now_playing.title}`](<{guild[guild_id].now_playing.url}>)'
            await ctx.reply(message, ephemeral=ephemeral)
            return ReturnData(False, message)

        message = tg(guild_id, 'There is no song playing right **now**')
        await ctx.reply(message, ephemeral=ephemeral)
        return ReturnData(False, message)

    message = tg(guild_id, 'There is no song playing right **now**')
    await ctx.reply(message, ephemeral=ephemeral)
    return ReturnData(False, message)

async def last_def(ctx, ephemeral: bool = False) -> ReturnData:
    """
    Show last played song
    :param ctx: Context
    :param ephemeral: Should bot response be ephemeral
    :return: ReturnData
    """
    log(ctx, 'last_def', [ephemeral], log_type='function', author=ctx.author)
    is_ctx, guild_id, author_id, guild_object = ctx_check(ctx)
    guild = get_guild_dict()
    if not is_ctx:
        return ReturnData(False, tg(guild_id, 'This command cant be used in WEB'))

    if not guild[guild_id].history:
        message = tg(guild_id, 'There is no song played yet')
        await ctx.reply(message, ephemeral=ephemeral)
        return ReturnData(False, message)

    embed = create_embed(guild[guild_id].history[-1], tg(guild_id, "Last Played"), guild_id)
    view = classes.view.PlayerControlView(ctx)

    if guild[guild_id].options.buttons:
        await ctx.reply(embed=embed, view=view, ephemeral=ephemeral)
    else:
        await ctx.reply(embed=embed, ephemeral=ephemeral)

    return ReturnData(True, tg(guild_id, "Last Played"))

async def loop_command_def(ctx, clear_queue: bool=False, ephemeral: bool=False) -> ReturnData:
    """
    Loop command
    :param ctx: Context
    :param clear_queue: Should queue be cleared
    :param ephemeral: Should bot response be ephemeral
    :return: ReturnData
    """
    log(ctx, 'loop_command_def', [clear_queue, ephemeral], log_type='function', author=ctx.author)
    is_ctx, guild_id, author_id, guild_object = ctx_check(ctx)
    guild = get_guild_dict()

    # add now_playing to queue if loop is activated
    add_to_queue_when_activated = False

    options = guild[guild_id].options

    if clear_queue:
        if options.loop:
            message = tg(guild_id, "Loop mode is already enabled")
            await ctx.reply(message, ephemeral=ephemeral)
            return ReturnData(False, message)

        if not guild[guild_id].now_playing or not guild_object.voice_client.is_playing:
            message = tg(guild_id, "There is no song playing right **now**")
            await ctx.reply(message, ephemeral=ephemeral)
            return ReturnData(False, message)

        guild[guild_id].queue.clear()
        to_queue(guild_id, guild[guild_id].now_playing)
        guild[guild_id].options.loop = True
        save_json()

        message = f'{tg(guild_id, "Queue **cleared**, Player will now loop **currently** playing song:")} [`{guild[guild_id].now_playing.title}`](<{guild[guild_id].now_playing.url}>)'
        await ctx.reply(message)
        return ReturnData(True, message)

    if options.loop:
        guild[guild_id].options.loop = False
        save_json()

        message = tg(guild_id, "Loop mode: `False`")
        await ctx.reply(message, ephemeral=ephemeral)
        return ReturnData(True, message)

    guild[guild_id].options.loop = True
    if guild[guild_id].now_playing and add_to_queue_when_activated:
        to_queue(guild_id, guild[guild_id].now_playing)
    save_json()

    message = tg(guild_id, 'Loop mode: `True`')
    await ctx.reply(message, ephemeral=True)
    return ReturnData(True, message)

async def set_video_time(ctx, time_stamp: int, mute_response: bool=False, ephemeral: bool=False):
    log(ctx, 'set_video_time', [time_stamp, mute_response, ephemeral], log_type='function')
    is_ctx, ctx_guild_id, author_id, ctx_guild_object = ctx_check(ctx)
    try:
        time_stamp = int(time_stamp)
    except (ValueError, TypeError):
        try:
            time_stamp = int(float(time_stamp))
        except (ValueError, TypeError):
            message = f'({time_stamp}) ' + tg(ctx_guild_id, 'is not an int')
            if not mute_response:
                await ctx.reply(message, ephemeral=ephemeral)
            return ReturnData(False, message)

    voice = ctx_guild_object.voice_client
    if not voice:
        message = tg(ctx_guild_id, f'Bot is not in a voice channel')
        if not mute_response:
            await ctx.reply(message, ephemeral=ephemeral)
        return ReturnData(False, message)

    # if not voice.is_playing():
    #     message = f'Bot is not playing anything'
    #     if not mute_response:
    #         await ctx.reply(message, ephemeral=ephemeral)
    #     return ReturnData(False, message)

    now_playing_video = get_guild_dict()[ctx_guild_id].now_playing
    if not now_playing_video:
        message = tg(ctx_guild_id, f'Bot is not playing anything')
        if not mute_response:
            await ctx.reply(message, ephemeral=ephemeral)
        return ReturnData(False, message)

    url = now_playing_video.stream_url
    if not url:
        url = now_playing_video.url

    new_source, new_chapters = await GetSource.create_source(ctx_guild_id, url, time_stamp=time_stamp, video_class=now_playing_video, source_type=now_playing_video.class_type)

    voice.source = new_source
    set_new_time(now_playing_video, time_stamp)

    message = tg(ctx_guild_id, f'Video time set to') + ": " +str(time_stamp)
    if not mute_response:
        await ctx.reply(message, ephemeral=ephemeral)
    return ReturnData(True, message)