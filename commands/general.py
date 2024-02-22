from utils.global_vars import GlobalVars

from classes.data_classes import ReturnData

from utils.log import log
from utils.translate import tg
from utils.save import update
from utils.global_vars import radio_dict, sound_effects
from database.guild import guild
from utils.global_vars import languages_dict

import commands.admin
from commands.utils import ctx_check

import discord
from discord.ext import commands as dc_commands
from typing import Literal

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
    is_ctx, guild_id, author_id, guild_object = ctx_check(ctx, glob)
    db_guild = guild(glob, guild_id)

    db_guild.options.language = country_code
    update(glob)

    message = f'{tg(guild_id, "Changed the language for this server to: ")} `{db_guild.options.language}`'
    await ctx.reply(message)
    return ReturnData(True, message)

async def sound_effects_def(ctx, glob: GlobalVars, ephemeral: bool = True) -> ReturnData:
    """
    List of all sound effects
    :param ctx: Context
    :param glob: GlobalVars
    :param ephemeral: Should bot response be ephemeral
    :return: ReturnData
    """
    log(ctx, 'sound_effects_def', options=locals(), log_type='function', author=ctx.author)
    is_ctx, guild_id, author_id, guild_object = ctx_check(ctx, glob)

    if not is_ctx:
        return ReturnData(False, tg(guild_id, 'Command cannot be used in WEB'))

    embed = discord.Embed(title="Sound Effects", colour=discord.Colour.from_rgb(241, 196, 15))
    message = ''
    for index, val in enumerate(sound_effects):
        add = f'**{index}** -> {val}\n'

        if len(message) + len(add) > 1023:
            embed.add_field(name="", value=message, inline=False)
            message = ''
        else:
            message = message + add

    embed.add_field(name="", value=message, inline=False)

    update(glob)
    await ctx.send(embed=embed, ephemeral=ephemeral)
    return ReturnData(True, tg(guild_id, 'Sound effects'))

async def list_radios_def(ctx, glob: GlobalVars, ephemeral: bool = True) -> ReturnData:
    """
    List of all radios
    :param ctx: Context
    :param glob: GlobalVars
    :param ephemeral: Should bot response be ephemeral
    :return: ReturnData
    """
    log(ctx, 'list_radios_def', options=locals(), log_type='function', author=ctx.author)
    is_ctx, guild_id, author_id, guild_object = ctx_check(ctx, glob)

    if not is_ctx:
        return ReturnData(False, tg(guild_id, 'Command cannot be used in WEB'))

    embed = discord.Embed(title="Radio List")
    message = ''
    for index, (name, val) in enumerate(radio_dict.items()):
        add = f'**{index}** -> {name}\n'

        if len(message) + len(add) > 1023:
            embed.add_field(name="", value=message, inline=False)
            message = ''
        else:
            message = message + add

    embed.add_field(name="", value=message, inline=False)

    update(glob)
    await ctx.send(embed=embed, ephemeral=ephemeral)
    return ReturnData(True, tg(guild_id, 'Radio list'))

async def key_def(ctx: dc_commands.Context, glob: GlobalVars) -> ReturnData:
    """
    Get key of guild
    :param ctx: Context
    :param glob: GlobalVars
    :return: ReturnData
    """
    log(ctx, 'key_def', options=locals(), log_type='function', author=ctx.author)
    db_guild = guild(glob, ctx.guild.id)
    update(glob)

    message = f'Key: `{db_guild.data.key}` -> [Control Panel]({config.WEB_URL}/guild/{ctx.guild.id}&key={db_guild.data.key})'
    await ctx.reply(message)
    return ReturnData(True, message)

async def options_command_def(ctx, glob: GlobalVars, loop=None, language=None, response_type=None, buttons=None, volume=None, buffer=None, history_length=None) -> ReturnData:
    log(ctx, 'options_command_def', options=locals(), log_type='function', author=ctx.author)
    is_ctx, guild_id, author_id, guild_object = ctx_check(ctx, glob)

    if not is_ctx:
        return ReturnData(False, tg(guild_id, 'Command cannot be used in WEB'))

    if all(v is None for v in [loop, language, response_type, buttons, volume, buffer, history_length]):
        return await commands.admin.options_def(ctx, glob, server=None, ephemeral=False)

    return await commands.admin.options_def(ctx, glob, server=guild_id, ephemeral=False, loop=str(loop), language=str(language),
                                            response_type=str(response_type), buttons=str(buttons), volume=str(volume),
                                            buffer=str(buffer), history_length=str(history_length))
