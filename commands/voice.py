from classes.data_classes import ReturnData

from commands.utils import ctx_check

from database.guild import guild, clear_queue

from utils.log import log
from utils.translate import txt
from utils.save import update, push_update
from utils.discord import now_to_history, get_voice_client
from utils.video_time import set_stopped, set_resumed
from utils.global_vars import GlobalVars

from discord.ext import commands as dc_commands
from typing import Union
import discord
import traceback


async def stop_def(ctx, glob: GlobalVars, mute_response: bool = False, keep_loop: bool = False) -> ReturnData:
    """
    Stops player
    :param ctx: Context
    :param glob: GlobalVars
    :param mute_response: Should bot response be muted
    :param keep_loop: Should loop be kept
    :return: ReturnData
    """
    log(ctx, 'stop_def', options=locals(), log_type='function', author=ctx.author)
    is_ctx, guild_id, author_id, guild_object = ctx_check(ctx, glob)
    db_guild = guild(glob, guild_id)

    voice: discord.voice_client.VoiceClient = get_voice_client(glob.bot.voice_clients, guild=guild_object)

    if not voice:
        message = txt(guild_id, glob, "Bot is not connected to a voice channel")
        if not mute_response:
            await ctx.reply(message, ephemeral=True)
        return ReturnData(False, message)

    voice.stop()

    with glob.ses.no_autoflush:
        db_guild.options.stopped = True
        if not keep_loop:
            db_guild.options.loop = False
        glob.ses.commit()

    await now_to_history(glob, guild_id)

    push_update(glob, guild_id, ['all'])

    message = txt(guild_id, glob, "Player **stopped!**")
    if not mute_response:
        await ctx.reply(message, ephemeral=True)
    return ReturnData(True, message)

async def pause_def(ctx, glob, mute_response: bool = False) -> ReturnData:
    """
    Pause player
    :param ctx: Context
    :param glob: GlobalVars
    :param mute_response: Should bot response be muted
    :return: ReturnData
    """
    log(ctx, 'pause_def', options=locals(), log_type='function', author=ctx.author)
    is_ctx, guild_id, author_id, guild_object = ctx_check(ctx, glob)
    db_guild = guild(glob, guild_id)

    voice: discord.voice_client.VoiceClient = get_voice_client(glob.bot.voice_clients, guild=guild_object)

    if voice:
        if voice.is_playing():
            voice.pause()
            if db_guild.now_playing:
                set_stopped(glob, db_guild.now_playing)
            message = txt(guild_id, glob, "Player **paused!**")
            resp = True
        elif voice.is_paused():
            message = txt(guild_id, glob, "Player **already paused!**")
            resp = False
        else:
            message = txt(guild_id, glob, 'No audio playing')
            resp = False
    else:
        message = txt(guild_id, glob, "Bot is not connected to a voice channel")
        resp = False

    update(glob)
    push_update(glob, guild_id, ['all'])

    if not mute_response:
        await ctx.reply(message, ephemeral=True)
    return ReturnData(resp, message)

async def resume_def(ctx, glob: GlobalVars, mute_response: bool = False) -> ReturnData:
    """
    Resume player
    :param ctx: Context
    :param glob: GlobalVars
    :param mute_response: Should bot response be muted
    :return: ReturnData
    """
    log(ctx, 'resume_def', options=locals(), log_type='function', author=ctx.author)
    is_ctx, guild_id, author_id, guild_object = ctx_check(ctx, glob)
    db_guild = guild(glob, guild_id)

    voice: discord.voice_client.VoiceClient = get_voice_client(glob.bot.voice_clients, guild=guild_object)

    if voice:
        if voice.is_paused():
            voice.resume()
            if db_guild.now_playing:
                set_resumed(glob, db_guild.now_playing)
            message = txt(guild_id, glob, "Player **resumed!**")
            resp = True
        elif voice.is_playing():
            message = txt(guild_id, glob, "Player **already resumed!**")
            resp = False
        else:
            message = txt(guild_id, glob, 'No audio playing')
            resp = False
    else:
        message = txt(guild_id, glob, "Bot is not connected to a voice channel")
        resp = False

    update(glob)
    push_update(glob, guild_id, ['all'])

    if not mute_response:
        await ctx.reply(message, ephemeral=True)
    return ReturnData(resp, message)

async def join_def(ctx, glob: GlobalVars, channel_id=None, mute_response: bool = False) -> ReturnData:
    """
    Join voice channel
    :param ctx: Context
    :param glob: GlobalVars
    :param channel_id: id of channel to join
    :param mute_response: Should bot response be muted
    :return: ReturnData
    """
    log(ctx, 'join_def', options=locals(), log_type='function', author=ctx.author)
    is_ctx, guild_id, author_id, guild_object = ctx_check(ctx, glob)

    # if video in now_playing -> add to history
    await now_to_history(glob, guild_id)

    # define author channel (for ide)
    author_channel = None

    if not channel_id:
        # if not from ctx and no channel_id provided return False
        if not is_ctx:
            return ReturnData(False, txt(guild_id, glob, 'No channel_id provided'))

        if ctx.author.voice:
            # get author voice channel
            author_channel = ctx.author.voice.channel

            if ctx.voice_client:
                # if bot is already connected to author channel return True
                if ctx.voice_client.channel == author_channel:
                    message = txt(guild_id, glob, "I'm already in this channel")
                    if not mute_response:
                        await ctx.reply(message, ephemeral=True)
                    return ReturnData(True, message)
        else:
            # if author is not connected to a voice channel return False
            message = txt(guild_id, glob, "You are **not connected** to a voice channel")
            await ctx.reply(message, ephemeral=True)
            return ReturnData(False, message)

    try:
        # get voice channel
        if author_channel:
            voice_channel = author_channel
        else:
            voice_channel = glob.bot.get_channel(int(channel_id))

        # check if bot has permission to join channel
        if not voice_channel.permissions_for(guild_object.me).connect:
            message = txt(guild_id, glob, "I don't have permission to join this channel")
            await ctx.reply(message, ephemeral=True)
            return ReturnData(False, message)

        # check if bot has permission to speak in channel
        if not voice_channel.permissions_for(guild_object.me).speak:
            message = txt(guild_id, glob, "I don't have permission to speak in this channel")
            await ctx.reply(message, ephemeral=True)
            return ReturnData(False, message)

        # check if the channel is empty
        if not len(voice_channel.members) > 0:
            message = txt(guild_id, glob, "The channel is empty")
            await ctx.reply(message, ephemeral=True)
            return ReturnData(False, message)

        # disconnect from voice channel if connected
        if guild_object.voice_client:
            await guild_object.voice_client.disconnect(force=True)
        # connect to voice channel
        await voice_channel.connect()
        # deafen bot
        await guild_object.change_voice_state(channel=voice_channel, self_deaf=True)

        push_update(glob, guild_id, ['all'])

        message = f"{txt(guild_id, glob, 'Joined voice channel:')}  `{voice_channel.name}`"
        if not mute_response:
            await ctx.reply(message, ephemeral=True)
        return ReturnData(True, message)

    except (discord.ext.commands.errors.CommandInvokeError, discord.errors.ClientException, AttributeError, ValueError,
            TypeError):
        log(ctx, "------------------------------- join -------------------------")
        tb = traceback.format_exc()
        log(ctx, tb)
        log(ctx, "--------------------------------------------------------------")

        message = txt(guild_id, glob, "Channel **doesn't exist** or bot doesn't have **sufficient permission** to join")
        await ctx.reply(message, ephemeral=True)
        return ReturnData(False, message)

async def disconnect_def(ctx, glob: GlobalVars, mute_response: bool = False) -> ReturnData:
    """
    Disconnect bot from voice channel
    :param ctx: Context
    :param glob: GlobalVars
    :param mute_response: Should bot response be muted
    :return: ReturnData
    """
    log(ctx, 'disconnect_def', options=locals(), log_type='function', author=ctx.author)
    is_ctx, guild_id, author_id, guild_object = ctx_check(ctx, glob)

    if guild_object.voice_client:
        await stop_def(ctx, glob, mute_response=True)
        clear_queue(glob, guild_id)

        channel = guild_object.voice_client.channel
        await guild_object.voice_client.disconnect(force=True)

        push_update(glob, guild_id, ['all'])
        await now_to_history(glob, guild_id)

        message = f"{txt(guild_id, glob, 'Left voice channel:')} `{channel}`"
        if not mute_response:
            await ctx.reply(message, ephemeral=True)
        return ReturnData(True, message)
    else:
        await now_to_history(glob, guild_id)
        message = txt(guild_id, glob, "Bot is **not** in a voice channel")
        if not mute_response:
            await ctx.reply(message, ephemeral=True)
        return ReturnData(False, message)

async def volume_command_def(ctx, glob: GlobalVars, volume: Union[float, int] = None, ephemeral: bool = False, mute_response: bool = False) -> ReturnData:
    """
    Change volume of player
    :param ctx: Context
    :param glob: GlobalVars
    :param volume: volume to set
    :param ephemeral: Should bot response be ephemeral
    :param mute_response: Should bot response be muted
    :return: ReturnData
    """
    log(ctx, 'volume_command_def', options=locals(), log_type='function', author=ctx.author)
    is_ctx, guild_id, author_id, guild_object = ctx_check(ctx, glob)
    db_guild = guild(glob, guild_id)

    if volume:
        try:
            volume = int(volume)
        except (ValueError, TypeError):
            message = txt(guild_id, glob, f'Invalid volume')
            if not mute_response:
                await ctx.reply(message, ephemeral=ephemeral)
            return ReturnData(False, message)

        new_volume = volume / 100

        db_guild.options.volume = new_volume
        glob.ses.commit()
        voice = guild_object.voice_client
        if voice:
            try:
                if voice.source:
                    voice.source.volume = new_volume
                    # voice.source = discord.PCMVolumeTransformer(voice.source, volume=new_volume) -- just trouble
            except AttributeError:
                pass

        message = f'{txt(guild_id, glob, "Changed the volume for this server to:")} `{int(db_guild.options.volume * 100)}%`'
    else:
        message = f'{txt(guild_id, glob, "The volume for this server is:")} `{int(db_guild.options.volume * 100)}%`'

    update(glob)

    if not mute_response:
        await ctx.reply(message, ephemeral=ephemeral)
    return ReturnData(True, message)
