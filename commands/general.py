from classes.data_classes import ReturnData

from commands.utils import ctx_check

from database.guild import guild, guild_data_key

from utils.log import log
from utils.translate import txt
from utils.save import update
from utils.global_vars import radio_dict, sound_effects, languages_dict, GlobalVars
from utils.convert import convert_duration
from utils.discord import create_embed

import commands.admin

from discord.ext import commands as dc_commands
from typing import Literal
import discord

import config

async def ping_def(ctx, glob: GlobalVars) -> ReturnData:
    """
    Ping command
    :param ctx: Context
    :param glob: GlobalVars
    :return: ReturnData
    """
    log(ctx, 'ping_def', options=locals(), log_type='function', author=ctx.author)
    update(glob)

    message = f'**Pong!** Latency: {round(glob.bot.latency * 1000)}ms'
    await ctx.reply(message)
    return ReturnData(True, message)

# noinspection PyTypeHints
async def language_command_def(ctx, glob: GlobalVars, country_code: Literal[tuple(languages_dict)]) -> ReturnData:
    """
    Change language of bot in guild
    :param ctx: Context
    :param glob: GlobalVars
    :param country_code: Country code of language (e.g. en, cs, sk ...)
    :return: ReturnData
    """
    log(ctx, 'language_command_def', options=locals(), log_type='function', author=ctx.author)
    is_ctx, guild_id, author, guild_object = ctx_check(ctx, glob)
    db_guild = guild(glob, guild_id)

    db_guild.options.language = country_code
    update(glob)

    message = f'{txt(guild_id, glob, "Changed the language for this server to: ")} `{db_guild.options.language}`'
    await ctx.reply(message)
    return ReturnData(True, message)

async def list_command_def(ctx, glob: GlobalVars, list_type: Literal['queue', 'history', 'effects', 'radios'], display_type: Literal['short', 'medium', 'long']=None, ephemeral: bool = True) -> ReturnData:
    """
    List of all sound effects or radios
    :param ctx: Context
    :param glob: GlobalVars
    :param display_type: Type of list (short, medium, long) - text, embed, embed with info and picture
    :param list_type: Type of list (effects, radios)
    :param ephemeral: Should bot response be ephemeral
    :return: ReturnData
    """
    log(ctx, 'list_def', options=locals(), log_type='function', author=ctx.author)
    is_ctx, guild_id, author, guild_object = ctx_check(ctx, glob)

    if not is_ctx:
        return ReturnData(False, txt(guild_id, glob, 'Command cannot be used in WEB'))

        # db_guild = guild(glob, guild_id)
    if list_type in ['queue', 'history']:
        db_guild = guild(glob, guild_id)

        max_embed = 5

        if list_type not in ['queue', 'history']:
            message = txt(guild_id, glob, 'Bad list_type')
            await ctx.reply(message, ephemeral=ephemeral)
            return ReturnData(False, message)

        show_list = db_guild.queue if list_type == 'queue' else list(reversed(db_guild.history))
        if not show_list:
            message = txt(guild_id, glob, "Nothing to **show**, queue is **empty!**")
            await ctx.reply(message, ephemeral=ephemeral)
            return ReturnData(True, message)

        display_type = display_type if display_type else 'long' if len(show_list) <= max_embed else 'short'
        loop = db_guild.options.loop
        key = db_guild.data.key

        if display_type == 'long':
            message = f"**THE {list_type.capitalize()}**\n **Loop** mode  `{loop}`,  **Display** type `{display_type}`, [Control Panel]({config.WEB_URL}/guild/{guild_id}?key={key})"
            await ctx.send(message, ephemeral=ephemeral, mention_author=False)

            for index, val in enumerate(show_list):
                embed = create_embed(glob, val, f'{txt(guild_id, glob, f"{list_type.upper()} #")}{index}', guild_id)
                await ctx.send(embed=embed, ephemeral=ephemeral, mention_author=False, silent=True)

            return ReturnData(True, f'{list_type.capitalize()} list')

        if display_type == 'medium':
            embed = discord.Embed(title=f"Song {list_type}", color=0x00ff00,
                                  description=f'Loop: {loop} | Display type: {display_type} | [Control Panel]({config.WEB_URL}/guild/{guild_id}?key={loop})',
                                  )

            message = ''
            for index, val in enumerate(show_list):
                add = f'**{index}** --> `{convert_duration(val.duration)}`  [{val.title}](<{val.url}>) \n'

                if len(message) + len(add) > 1023:
                    embed.add_field(name="", value=message, inline=False)
                    message = ''
                    continue

                message = message + add

            embed.add_field(name="", value=message, inline=False)

            if len(embed) < 6000:
                await ctx.reply(embed=embed, ephemeral=ephemeral, mention_author=False)
                return ReturnData(True, f'{list_type.capitalize()} list')

            await ctx.reply("HTTPException(discord 6000 character limit) >> using display type `short`", ephemeral=ephemeral, mention_author=False)
            display_type = 'short'

        if display_type == 'short':
            send = f"**THE {list_type.upper()}**\n **Loop** mode  `{loop}`,  **Display** type `{display_type}`, [Control Panel]({config.WEB_URL}/guild/{guild_id}?key={key})"
            # noinspection PyUnresolvedReferences
            if ctx.interaction.response.is_done():
                await ctx.send(send, ephemeral=ephemeral, mention_author=False)
            else:
                await ctx.reply(send, ephemeral=ephemeral, mention_author=False)

            message = ''
            for index, val in enumerate(show_list):
                add = f'**{txt(guild_id, glob, f"{list_type.upper()} #")}{index}**  `{convert_duration(val.duration)}`  [`{val.title}`](<{val.url}>) \n'

                if len(message) + len(add) > 2000:
                    if ephemeral:
                        await ctx.send(message, ephemeral=ephemeral, mention_author=False)
                        message = ''
                        continue

                    await ctx.message.channel.send(content=message, mention_author=False)
                    message = ''
                    continue

                message = message + add

            update(glob)

            if ephemeral:
                await ctx.send(message, ephemeral=ephemeral, mention_author=False)
                return ReturnData(True, f'{list_type.capitalize()} list')

            await ctx.message.channel.send(content=message, mention_author=False)
            return ReturnData(True, f'{list_type.capitalize()} list')

    if list_type == 'effects':
        embed = False
        if display_type in ['long', 'medium']:
            embed = discord.Embed(title="Sound Effects", colour=discord.Colour.from_rgb(241, 196, 15))

        message = ''
        for index, val in enumerate(sound_effects):
            add = f'**{index}** -> {val}\n'

            if len(message) + len(add) > 1023 and embed:
                embed.add_field(name="", value=message, inline=False)
                message = ''
                continue

            message = message + add

        update(glob)

        if embed:
            embed.add_field(name="", value=message, inline=False)
            await ctx.send(embed=embed, ephemeral=ephemeral)
            return ReturnData(True, txt(guild_id, glob, 'Sound effects'))

        await ctx.send(message, ephemeral=ephemeral)
        return ReturnData(True, txt(guild_id, glob, 'Sound effects'))
    elif list_type == 'radios':
        embed = False
        if display_type in ['long', 'medium']:
            embed = discord.Embed(title="Radio List")

        message = ''
        for radio_id, val in radio_dict.items():
            if radio_id == 'last_updated':
                continue

            add = f'**{radio_id}** -> {val['name']}\n'

            if len(message) + len(add) > 1023 and embed:
                embed.add_field(name="", value=message, inline=False)
                message = ''
                continue

            message = message + add

        update(glob)

        if embed:
            embed.add_field(name="", value=message, inline=False)
            await ctx.send(embed=embed, ephemeral=ephemeral)
            return ReturnData(True, txt(guild_id, glob, 'Radio list'))

        await ctx.send(message, ephemeral=ephemeral)
        return ReturnData(True, txt(guild_id, glob, 'Radio list'))

    message = txt(guild_id, glob, 'Wrong list type')
    await ctx.reply(message, ephemeral=ephemeral)
    return ReturnData(False, message)

async def key_def(ctx: dc_commands.Context, glob: GlobalVars) -> ReturnData:
    """
    Get key of guild
    :param ctx: Context
    :param glob: GlobalVars
    :return: ReturnData
    """
    log(ctx, 'key_def', options=locals(), log_type='function', author=ctx.author)
    guild_key = guild_data_key(glob, ctx.guild.id)
    update(glob)

    message = f'Key: `{guild_key}` -> [Control Panel]({config.WEB_URL}/guild/{ctx.guild.id}?key={guild_key})'
    await ctx.reply(message)
    return ReturnData(True, message)

async def options_command_def(ctx, glob: GlobalVars, loop=None, language=None, response_type=None, buttons=None, volume=None, buffer=None, history_length=None, subtitles=None) -> ReturnData:
    log(ctx, 'options_command_def', options=locals(), log_type='function', author=ctx.author)
    is_ctx, guild_id, author, guild_object = ctx_check(ctx, glob)

    if not is_ctx:
        return ReturnData(False, txt(guild_id, glob, 'Command cannot be used in WEB'))

    if all(v is None for v in [loop, language, response_type, buttons, volume, buffer, history_length, subtitles]):
        return await commands.admin.options_def(ctx, glob, server=None, ephemeral=False)

    return await commands.admin.options_def(ctx, glob, server=guild_id, ephemeral=False, loop=str(loop), language=str(language),
                                            response_type=str(response_type), buttons=str(buttons), volume=str(volume),
                                            buffer=str(buffer), history_length=str(history_length), subtitles=str(subtitles))

async def subtitles_command_def(ctx, glob: GlobalVars, subtitles, mute_response: bool=True) -> ReturnData:
    log(ctx, 'subtitles_command_def', options=locals(), log_type='function', author=ctx.author)
    is_ctx, guild_id, author, guild_object = ctx_check(ctx, glob)
    db_guild = guild(glob, guild_id)

    if subtitles in ['False', 'false', 'off', 'no', 'disable', 'disabled', '0', 'f', False, None, 0]:
        db_guild.options.subtitles = 'False'
        update(glob)

        message = txt(guild_id, glob, 'Subtitles disabled')
        if not mute_response:
            await ctx.reply(message)
        return ReturnData(True, message)

    if subtitles in ['True', 'true', 'on', 'yes', 'enable', 'enabled', '1', 't', True, 1]:
        db_guild.options.subtitles = 'True'
        update(glob)

        message = txt(guild_id, glob, 'Subtitles enabled')
        if not mute_response:
            await ctx.reply(message)
        return ReturnData(True, message)

    try:
        assert isinstance(subtitles, str)

        db_guild.options.subtitles = subtitles.lower()
        update(glob)

        message = txt(guild_id, glob, 'Subtitles changed to: ') + subtitles
        if not mute_response:
            await ctx.reply(message)
        return ReturnData(True, message)

    except AssertionError:
        message = txt(guild_id, glob, 'Bad subtitle')
        if not mute_response:
            await ctx.reply(message)
        return ReturnData(False, message)