from classes.video_class import NowPlaying, Queue, to_now_playing_class
from classes.data_classes import ReturnData
from classes.typed_dictionaries import RadioGardenInfo

from commands.utils import ctx_check

from database.guild import guild, clear_queue

from utils.source import GetSource
from utils.log import log
from utils.translate import txt
from utils.save import update, push_update
from utils.discord import now_to_history, create_embed, to_queue
from utils.source import url_checker
from utils.video_time import set_started, set_new_time
from utils.global_vars import sound_effects, radio_dict, GlobalVars
from utils.radio_garden import get_radio_garden_info

import classes.view
import commands.voice
import commands.queue

from discord import app_commands
from os import path
import discord
import asyncio
import sys
import traceback
import typing

import config

async def play_def(ctx, glob: GlobalVars, url=None, force=False, mute_response=False, after=False) -> ReturnData:
    log(ctx, 'play_def', options=locals(), log_type='function', author=ctx.author)
    is_ctx, guild_id, author_id, guild_object = ctx_check(ctx, glob)
    db_guild = guild(glob, guild_id)
    response = ReturnData(False, txt(guild_id, glob, 'Unknown error'))

    notif = f' -> [Control Panel]({config.WEB_URL}/guild/{guild_id}&key={db_guild.data.key})'

    if after and db_guild.options.stopped:
        log(ctx, "play_def -> stopped play next loop")
        if not db_guild.options.is_radio:
            now_to_history(glob, guild_id)
        return ReturnData(False, txt(guild_id, glob, "Stopped play next loop"))

    voice = guild_object.voice_client

    if not voice:
        if not is_ctx:
            return ReturnData(False, txt(guild_id, glob, 'Bot is not connected to a voice channel'))

        if ctx.author.voice is None:
            message = txt(guild_id, glob, "You are **not connected** to a voice channel")
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
        response = await commands.queue.queue_command_def(ctx, glob, url=url, position=position, mute_response=True, force=force, from_play=True)

        if not response or not response.response:
            if not mute_response:
                if response is None:
                    return ReturnData(False, 'terminated')

                if response.terminate:
                    return ReturnData(False, 'terminated')

                await ctx.reply(response.message)
            return response

    if not guild_object.voice_client:
        # if not is_ctx:
        #     if not ctx.interaction.response.is_done():
        #         await ctx.defer()
        join_response = await commands.voice.join_def(ctx, glob, None, True)
        voice = guild_object.voice_client
        if not join_response.response:
            if not mute_response:
                await ctx.reply(join_response.message)
            return join_response

    if voice.is_playing():
        if not db_guild.options.is_radio and not force:
            if url:
                if response.video is not None:
                    message = f'{txt(guild_id, glob, "**Already playing**, added to queue")}: [`{response.video.title}`](<{response.video.url}>) {notif}'
                    if not mute_response:
                        await ctx.reply(message)
                    return ReturnData(False, message)

                message = f'{txt(guild_id, glob, "**Already playing**, added to queue")} {notif}'
                if not mute_response:
                    await ctx.reply(message)
                return ReturnData(False, message)

            message = f'{txt(guild_id, glob, "**Already playing**")} {notif}'
            if not mute_response:
                await ctx.reply(message)
            return ReturnData(False, message)

        voice.stop()
        db_guild.options.stopped = True
        db_guild.options.is_radio = False
        glob.ses.commit()

    if voice.is_paused():
        return await commands.voice.resume_def(ctx, glob)

    if not db_guild.queue:
        message = f'{txt(guild_id, glob, "There is **nothing** in your **queue**")} {notif}'
        if not after and not mute_response:
            await ctx.reply(message)
        now_to_history(glob, guild_id)
        return ReturnData(False, message)

    video = db_guild.queue[0]
    now_to_history(glob, guild_id)

    if video.class_type not in ['Video', 'Probe', 'SoundCloud']:
        glob.ses.query(video.__class__).filter_by(id=video.id).delete()
        glob.ses.commit()
        if video.class_type == 'Radio':
            return await radio_def(ctx, glob, video.title, video_from_queue=video, radio_type='czech')
        if video.class_type == 'RadioGarden':
            return await radio_def(ctx, glob, video.title, video_from_queue=video, radio_type='garden')
        if video.class_type == 'Local':
            return await ps_def(ctx, glob, video.local_number)

        message = txt(guild_id, glob, "Unknown type")
        if not mute_response:
            await ctx.reply(message)
        return ReturnData(False, message)

    if not force:
        db_guild.options.stopped = False
        glob.ses.commit()

    try:
        source, chapters = await GetSource.create_source(glob, guild_id, video.url, source_type=video.class_type, video_class=video)
        voice.play(source, after=lambda e: asyncio.run_coroutine_threadsafe(play_def(ctx, glob, after=True), glob.bot.loop))

        await commands.voice.volume_command_def(ctx, glob, db_guild.options.volume * 100, False, True)

        # Variables update
        db_guild.options.stopped = False
        # video variables
        set_started(glob, video, guild_object, chapters=chapters)

        # Queue update
        # if guild[guild_id].options.loop:
        #     to_queue(guild_id, video)
        glob.ses.query(Queue).filter_by(id=video.id).delete()
        glob.ses.commit()

        push_update(glob, guild_id)
        update(glob)

        # Response
        options = db_guild.options
        response_type = options.response_type

        message = f'{txt(guild_id, glob, "Now playing")} [`{video.title}`](<{video.url}>) {notif}'
        view = classes.view.PlayerControlView(ctx, glob)

        if response_type == 'long':
            if not mute_response:
                embed = create_embed(glob, video, txt(guild_id, glob, "Now playing"), guild_id)
                if options.buttons:
                    view.message = await ctx.reply(embed=embed, view=view)
                else:
                    await ctx.reply(embed=embed)
            return ReturnData(True, message)

        elif response_type == 'short':
            if not mute_response:
                if options.buttons:
                    view.message = await ctx.reply(message, view=view)
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
        message = f'{txt(guild_id, glob, "An **error** occurred while trying to play the song")} {glob.bot.get_user(config.DEVELOPER_ID).mention} ({sys.exc_info()[0]})'
        await ctx.reply(message)
        return ReturnData(False, message)

async def radio_def(ctx, glob: GlobalVars, query, video_from_queue=None, radio_type: typing.Literal['czech', 'garden']='czech') -> ReturnData:
    """
    Play radio from radio.garden
    :param glob: GlobalVars
    :param ctx: Context
    :param query: str - czech radio id or radio.garden url
    :param video_from_queue: VideoClass child
    :param radio_type: 'czech' or 'garden'
    :return: ReturnData
    """
    log(ctx, 'radio_def', options=locals(), log_type='function', author=ctx.author)
    is_ctx, guild_id, author_id, guild_object = ctx_check(ctx, glob)

    # noinspection PyUnresolvedReferences
    if is_ctx:
        if not ctx.interaction.response.is_done():
            await ctx.defer()

    # Check if radio_type is correct
    if radio_type not in ['czech', 'garden']:
        message = txt(guild_id, glob, "Unknown radio type")
        await ctx.reply(message)
        return ReturnData(False, message)

    if radio_type == 'czech' and not video_from_queue:
        if query not in radio_dict.keys():
            return await radio_def(ctx, glob, query, radio_type='garden')

        # Check if radio still exists
        response, code = await url_checker(radio_dict[query]['stream'])
        if not response:
            message = txt(guild_id, glob, "Radio **not available**")
            await ctx.reply(message)
            return ReturnData(False, message)

        url = radio_dict[query]['stream']
        video = NowPlaying(glob, 'Radio', author_id, guild_id, radio_info=dict(name=query), stream_url=url)

    elif radio_type == 'garden' and not video_from_queue:
        resp = await get_radio_garden_info(query)
        radio_info: RadioGardenInfo = resp[1]
        if not resp[0]:
            message = txt(guild_id, glob, "Radio **not available**")
            await ctx.reply(message)
            return ReturnData(False, message)

        url = radio_info['stream']
        video = NowPlaying(glob, 'RadioGarden', author_id, guild_id, url=f"https://radio.garden{radio_info['url']}",
                           title=radio_info['title'], channel_name=radio_info['title'], channel_link=radio_info['website'],
                           stream_url=radio_info['stream'])

    elif video_from_queue:
        # Translate video to NowPlaying class
        video = to_now_playing_class(glob, video_from_queue)
        url = video.stream_url

    else:
        message = txt(guild_id, glob, "Unknown radio type")
        await ctx.reply(message)
        return ReturnData(False, message)

    # Connect to voice channel
    if not guild_object.voice_client:
        response = await commands.voice.join_def(ctx, glob, None, True)
        if not response.response:
            return response

    db_guild = guild(glob, guild_id)

    # Set is_radio to True
    db_guild.options.is_radio = True
    glob.ses.commit()

    # Check if something is playing and stop it
    if guild_object.voice_client.is_playing():
        await commands.voice.stop_def(ctx, glob, mute_response=True)

    # Get source
    source, chapters = await GetSource.create_source(glob, guild_id, url, source_type=video.class_type, video_class=video)
    set_started(glob, video, chapters=chapters, guild_object=guild_object)

    # Play
    guild_object.voice_client.play(source)

    # Set volume
    await commands.voice.volume_command_def(ctx, glob, db_guild.options.volume * 100, False, True)

    # Response
    embed = create_embed(glob, video, txt(guild_id, glob, "Now playing"), guild_id)
    if db_guild.options.buttons:
        view = classes.view.PlayerControlView(ctx, glob)
        view.message = await ctx.reply(embed=embed, view=view)
    else:
        await ctx.reply(embed=embed)

    update(glob)

    return ReturnData(True, txt(guild_id, glob, "Radio **started**"))

async def ps_def(ctx, glob: GlobalVars, effect_number: app_commands.Range[int, 1, len(sound_effects)], mute_response: bool = False) -> ReturnData:
    """
    Play sound effect
    :param glob: GlobalVars
    :param ctx: Context
    :param effect_number: index of sound effect (show all sound effects with sound_effects_def)
    :param mute_response: bool - Should bot response be muted
    :return: ReturnData
    """
    log(ctx, 'ps_def', options=locals(), log_type='function', author=ctx.author)
    is_ctx, guild_id, author_id, guild_object = ctx_check(ctx, glob)
    db_guild = guild(glob, guild_id)
    db_guild.options.is_radio = False
    glob.ses.commit()
    try:
        name = sound_effects[effect_number]
    except IndexError:
        message = txt(guild_id, glob, "Number **not in list** (use `/sound` to get all sound effects)")
        if not mute_response:
            await ctx.reply(message, ephemeral=True)
        return ReturnData(False, message)

    filename = f"{config.PARENT_DIR}sound_effects/{name}.mp3"
    if path.exists(filename):
        source, chapters = await GetSource.create_source(glob, guild_id, filename, source_type='Local')
    else:
        filename = f"{config.PARENT_DIR}sound_effects/{name}.wav"
        if path.exists(filename):
            source, chapters = await GetSource.create_source(glob, guild_id, filename, source_type='Local')
        else:
            message = txt(guild_id, glob, "No such file/website supported")
            if not mute_response:
                await ctx.reply(message, ephemeral=True)
            return ReturnData(False, message)

    if not guild_object.voice_client:
        join_response = await commands.voice.join_def(ctx, glob, None, True)
        if not join_response.response:
            return join_response

    stop_response = await commands.voice.stop_def(ctx, glob, mute_response=True)
    if not stop_response.response:
        return stop_response

    video = NowPlaying(glob, 'Local', author_id, guild_id, title=name, duration='Unknown', local_number=effect_number, stream_url=filename)
    set_started(glob, video, guild_object, chapters=chapters)

    voice = guild_object.voice_client
    voice.play(source)
    await commands.voice.volume_command_def(ctx, glob, db_guild.options.volume * 100, False, True)

    message = txt(guild_id, glob, "Playing sound effect number") + f" `{effect_number}`"
    if not mute_response:
        await ctx.reply(message, ephemeral=True)
    return ReturnData(True, message)

async def now_def(ctx, glob: GlobalVars, ephemeral: bool = False) -> ReturnData:
    """
    Show now playing song
    :param ctx: Context
    :param glob: GlobalVars
    :param ephemeral: Should bot response be ephemeral
    :return: ReturnData
    """
    log(ctx, 'now_def', options=locals(), log_type='function', author=ctx.author)
    is_ctx, guild_id, author_id, guild_object = ctx_check(ctx, glob)
    db_guild = guild(glob, guild_id)
    if not is_ctx:
        return ReturnData(False, txt(guild_id, glob, 'This command cant be used in WEB'))

    if ctx.voice_client:
        if ctx.voice_client.is_playing():
            db_guild.now_playing.renew(glob, force=True)
            embed = create_embed(glob, db_guild.now_playing, txt(guild_id, glob, "Now playing"), guild_id)

            view = classes.view.PlayerControlView(ctx, glob)

            if db_guild.options.buttons:
                view.message = await ctx.reply(embed=embed, view=view, ephemeral=ephemeral)
                return ReturnData(True, txt(guild_id, glob, "Now playing"))

            await ctx.reply(embed=embed, ephemeral=ephemeral)
            return ReturnData(True, txt(guild_id, glob, "Now playing"))

        if ctx.voice_client.is_paused():
            message = f'{txt(guild_id, glob, "There is no song playing right **now**, but there is one **paused:**")} [`{db_guild.now_playing.title}`](<{db_guild.now_playing.url}>)'
            await ctx.reply(message, ephemeral=ephemeral)
            return ReturnData(False, message)

        message = txt(guild_id, glob, 'There is no song playing right **now**')
        await ctx.reply(message, ephemeral=ephemeral)
        return ReturnData(False, message)

    message = txt(guild_id, glob, 'There is no song playing right **now**')
    await ctx.reply(message, ephemeral=ephemeral)
    return ReturnData(False, message)

async def last_def(ctx, glob: GlobalVars, ephemeral: bool = False) -> ReturnData:
    """
    Show last played song
    :param ctx: Context
    :param glob: GlobalVars
    :param ephemeral: Should bot response be ephemeral
    :return: ReturnData
    """
    log(ctx, 'last_def', options=locals(), log_type='function', author=ctx.author)
    is_ctx, guild_id, author_id, guild_object = ctx_check(ctx, glob)
    db_guild = guild(glob, guild_id)
    if not is_ctx:
        return ReturnData(False, txt(guild_id, glob, 'This command cant be used in WEB'))

    if not db_guild.history:
        message = txt(guild_id, glob, 'There is no song played yet')
        await ctx.reply(message, ephemeral=ephemeral)
        return ReturnData(False, message)

    embed = create_embed(glob, db_guild.history[-1], txt(guild_id, glob, "Last Played"), guild_id)
    view = classes.view.PlayerControlView(ctx, glob)

    if db_guild.options.buttons:
        view.message = await ctx.reply(embed=embed, view=view, ephemeral=ephemeral)
    else:
        await ctx.reply(embed=embed, ephemeral=ephemeral)

    return ReturnData(True, txt(guild_id, glob, "Last Played"))

async def loop_command_def(ctx, glob: GlobalVars, clear_queue_opt: bool=False, ephemeral: bool=False) -> ReturnData:
    """
    Loop command
    :param ctx: Context
    :param glob: GlobalVars
    :param clear_queue_opt: Should queue be cleared
    :param ephemeral: Should bot response be ephemeral
    :return: ReturnData
    """
    log(ctx, 'loop_command_def', options=locals(), log_type='function', author=ctx.author)
    is_ctx, guild_id, author_id, guild_object = ctx_check(ctx, glob)
    db_guild = guild(glob, guild_id)

    # add now_playing to queue if loop is activated
    add_to_queue_when_activated = False

    options = db_guild.options

    if clear_queue_opt:
        if options.loop:
            message = txt(guild_id, glob, "Loop mode is already enabled")
            await ctx.reply(message, ephemeral=ephemeral)
            return ReturnData(False, message)

        if not db_guild.now_playing or not guild_object.voice_client.is_playing:
            message = txt(guild_id, glob, "There is no song playing right **now**")
            await ctx.reply(message, ephemeral=ephemeral)
            return ReturnData(False, message)

        clear_queue(glob, guild_id)
        to_queue(glob, guild_id, db_guild.now_playing)
        db_guild.options.loop = True
        push_update(glob, guild_id)
        update(glob)

        message = f'{txt(guild_id, glob, "Queue **cleared**, Player will now loop **currently** playing song:")} [`{db_guild.now_playing.title}`](<{db_guild.now_playing.url}>)'
        await ctx.reply(message)
        return ReturnData(True, message)

    if options.loop:
        db_guild.options.loop = False
        push_update(glob, guild_id)
        update(glob)

        message = txt(guild_id, glob, "Loop mode: `False`")
        await ctx.reply(message, ephemeral=ephemeral)
        return ReturnData(True, message)

    db_guild.options.loop = True
    if db_guild.now_playing and add_to_queue_when_activated:
        to_queue(glob, guild_id, db_guild.now_playing)
    push_update(glob, guild_id)
    update(glob)

    message = txt(guild_id, glob, 'Loop mode: `True`')
    await ctx.reply(message, ephemeral=True)
    return ReturnData(True, message)

async def set_video_time(ctx, glob: GlobalVars, time_stamp: int, mute_response: bool=False, ephemeral: bool=False):
    log(ctx, 'set_video_time', options=locals(), log_type='function')
    is_ctx, ctx_guild_id, author_id, ctx_guild_object = ctx_check(ctx, glob)
    try:
        time_stamp = int(time_stamp)
    except (ValueError, TypeError):
        try:
            time_stamp = int(float(time_stamp))
        except (ValueError, TypeError):
            message = f'({time_stamp}) ' + txt(ctx_guild_id, glob, 'is not an int')
            if not mute_response:
                await ctx.reply(message, ephemeral=ephemeral)
            return ReturnData(False, message)

    voice = ctx_guild_object.voice_client
    if not voice:
        message = txt(ctx_guild_id, glob, f'Bot is not in a voice channel')
        if not mute_response:
            await ctx.reply(message, ephemeral=ephemeral)
        return ReturnData(False, message)

    # if not voice.is_playing():
    #     message = f'Bot is not playing anything'
    #     if not mute_response:
    #         await ctx.reply(message, ephemeral=ephemeral)
    #     return ReturnData(False, message)

    now_playing_video = guild(glob, ctx_guild_id).now_playing
    if not now_playing_video:
        message = txt(ctx_guild_id, glob, f'Bot is not playing anything')
        if not mute_response:
            await ctx.reply(message, ephemeral=ephemeral)
        return ReturnData(False, message)

    url = now_playing_video.stream_url
    if not url:
        url = now_playing_video.url

    new_source, new_chapters = await GetSource.create_source(glob, ctx_guild_id, url, time_stamp=time_stamp, video_class=now_playing_video, source_type=now_playing_video.class_type)

    voice.source = new_source
    set_new_time(glob, now_playing_video, time_stamp)
    push_update(glob, ctx_guild_id)

    message = txt(ctx_guild_id, glob, f'Video time set to') + ": " + str(time_stamp)
    if not mute_response:
        await ctx.reply(message, ephemeral=ephemeral)
    return ReturnData(True, message)

async def earrape_command_def(ctx, glob: GlobalVars):
    log(ctx, 'ear_rape_command_def', options=locals(), log_type='function', author=ctx.author)
    is_ctx, ctx_guild_id, author_id, ctx_guild_object = ctx_check(ctx, glob)
    times = 10
    new_volume = 10000000000000

    guild(glob, ctx_guild_id).options.volume = 1.0

    voice = ctx.voice_client
    if voice:
        try:
            if voice.source:
                for i in range(times):
                    voice.source.volume = new_volume
                    voice.source = discord.PCMVolumeTransformer(voice.source, volume=new_volume)
        except AttributeError:
            pass

        await ctx.reply(txt(ctx_guild_id, glob, f'Haha get ear raped >>> effect can only be turned off by `/disconnect`'), ephemeral=True)
    else:
        await ctx.reply(txt(ctx_guild_id, glob, f'Ear Rape can only be activated if the bot is in a voice channel'), ephemeral=True)

    update(glob)
