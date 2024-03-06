from classes.video_class import Queue
from classes.data_classes import ReturnData
from commands.utils import ctx_check

from database.guild import guild, clear_queue

from utils.source import GetSource
from utils.log import log
from utils.translate import txt
from utils.save import update, push_update
from utils.discord import now_to_history, create_embed, to_queue
from utils.video_time import set_started, set_new_time
from utils.global_vars import sound_effects, GlobalVars
from utils.url import get_url_type, command_for_type

import classes.view
import commands.voice
import commands.queue
import commands.autocomplete

import discord
import asyncio
import random
import sys
import traceback

import config

async def play_def(ctx, glob: GlobalVars,
                   url=None,
                   force: bool=False,
                   mute_response: bool=False,
                   after: bool=False,
                   no_search: bool=False,
                   embed: bool=None,
                   radio: bool=None,
                   player_id: int=None,
                   no_after: bool=None
                   ) -> ReturnData:
    log(ctx, 'play_def', options=locals(), log_type='function', author=ctx.author)
    is_ctx, guild_id, author_id, guild_object = ctx_check(ctx, glob)
    db_guild = guild(glob, guild_id)

    response = ReturnData(False, txt(guild_id, glob, 'Unknown error'))
    notif = f' -> [Control Panel]({config.WEB_URL}/guild/{guild_id}&key={db_guild.data.key})'

    if after and db_guild.options.stopped or after and player_id != db_guild.options.player_id or after and no_after is True:
        log(ctx, f"play_def -> loop stopped (stopped: {db_guild.options.stopped}, id: {player_id}, db_id: {db_guild.options.player_id}, no_after: {no_after})", log_type='function')
        # if not db_guild.options.is_radio:
        #     await now_to_history(glob, guild_id)
        return ReturnData(False, txt(guild_id, glob, "Stopped play next loop"))

    p_id = player_id if player_id else random.choice([i for i in range(0, 9) if i not in [db_guild.options.player_id]])
    db_guild.options.player_id = p_id
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
        response = await commands.queue.queue_command_def(ctx, glob, url=url, position=position, mute_response=True, force=force, from_play=True, no_search=no_search)

        if not response or not response.response:
            if not mute_response:
                if response is None:
                    return ReturnData(False, 'terminated')

                if response.terminate:
                    return ReturnData(False, 'terminated')

                await ctx.reply(response.message)
            return response

    if not guild_object.voice_client:
        join_response = await commands.voice.join_def(ctx, glob, None, True)
        voice = guild_object.voice_client
        if not join_response.response:
            if not mute_response:
                await ctx.reply(join_response.message)
            return join_response

    if voice.is_playing():
        if not force:  # not db_guild.options.is_radio and
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
        # db_guild.options.stopped = True
        # db_guild.options.is_radio = False if radio is False else True
        # glob.ses.commit()

    if voice.is_paused():
        return await commands.voice.resume_def(ctx, glob)

    if not db_guild.queue:
        message = f'{txt(guild_id, glob, "There is **nothing** in your **queue**")} {notif}'
        if not after and not mute_response:
            await ctx.reply(message)
        await now_to_history(glob, guild_id)
        return ReturnData(False, message)

    db_guild = guild(glob, guild_id)
    video = db_guild.queue[0]
    await now_to_history(glob, guild_id, no_push=True)

    stream_url = video.url
    if video.class_type in ['RadioCz', 'RadioGarden', 'RadioTuneIn']:
        stream_url = video.radio_info['stream']
        embed = True if embed is None else embed

    # elif video.class_type == 'Local':
    #     glob.ses.query(video.__class__).filter_by(id=video.id).delete()
    #     glob.ses.commit()
    #     return await ps_def(ctx, glob, video.local_number)

    elif video.class_type in ['Video', 'Probe', 'SoundCloud', 'Local']:
        pass

    else:
        message = txt(guild_id, glob, "Unknown type")
        if not mute_response:
            await ctx.reply(message)
        return ReturnData(False, message)

    if not force:
        db_guild.options.stopped = False
        glob.ses.commit()

    try:
        source, chapters = await GetSource.create_source(glob, guild_id, stream_url, source_type=video.class_type, video_class=video)
        voice.play(source, after=lambda e: asyncio.run_coroutine_threadsafe(play_def(ctx, glob, after=True, player_id=p_id, no_after=no_after), glob.bot.loop))

        await commands.voice.volume_command_def(ctx, glob, db_guild.options.volume * 100, False, True)

        # Variables update
        db_guild.options.stopped = False
        # video variables
        await set_started(glob, video, guild_object, chapters=chapters)

        # Queue update
        # if guild[guild_id].options.loop:
        #     await to_queue(guild_id, video)
        glob.ses.query(Queue).filter_by(id=video.id).delete()
        glob.ses.commit()

        push_update(glob, guild_id)
        update(glob)

        # Response
        options = db_guild.options
        response_type = options.response_type

        message = f'{txt(guild_id, glob, "Now playing")} [`{video.title}`](<{video.url}>) {notif}'
        view = classes.view.PlayerControlView(ctx, glob)

        if response_type == 'long' or embed:
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

async def local_def(ctx, glob: GlobalVars, effect: str, mute_response: bool = False) -> ReturnData:
    """
    Play sound effect
    :param glob: GlobalVars
    :param ctx: Context
    :param effect: str - Sound effect name or number
    :param mute_response: bool - Should bot response be muted
    :return: ReturnData
    """
    log(ctx, 'ps_def', options=locals(), log_type='function', author=ctx.author)
    is_ctx, guild_id, author_id, guild_object = ctx_check(ctx, glob)

    url_type, url = get_url_type(effect)
    if url_type not in ['Local', 'String']:
        message = txt(guild_id, glob, "Wrong command! Try ") + f"`/{command_for_type(url_type)}`"
        if not mute_response:
            await ctx.reply(message)
        return ReturnData(False, message)

    if url_type == 'Local':
        return await play_def(ctx, glob, url, force=True, no_search=True, mute_response=mute_response, no_after=True)

    try:
        code = int(effect)
        if 1 <= code <= len(sound_effects):
            return await local_def(ctx, glob, f'_local:{code}', mute_response)
    except (ValueError, TypeError):
        pass

    effects: list[discord.app_commands.Choice] = await commands.autocomplete.local_autocomplete_def(None, effect, 5)
    if not effects:
        message = txt(guild_id, glob, "Effect **not found**")
        if not mute_response:
            await ctx.reply(message)
        return ReturnData(False, message)

    view = classes.view.OptionView(ctx, glob, [effect.value for effect in effects], 'Local')

    message = txt(guild_id, glob, "Choose effect")
    for index, effect in enumerate(effects):
        message += f"\n**{index + 1}#** `{effect.name}`"

    if not mute_response:
        view.message = await ctx.reply(message, view=view)
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
            await db_guild.now_playing.renew(glob, force=True)
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
        await to_queue(glob, guild_id, db_guild.now_playing)
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
        await to_queue(glob, guild_id, db_guild.now_playing)
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
