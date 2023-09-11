from classes.data_classes import ReturnData

from utils.log import log
from utils.translate import tg
from utils.save import save_json
from utils.globals import get_bot, get_languages_dict, get_guild_dict, get_all_sound_effects, get_radio_dict

import commands.admin
from commands.utils import ctx_check

import discord
import json
from discord.ext import commands as dc_commands
from typing import Literal

import config

with open('db/languages.json', 'r', encoding='utf-8') as file:
    languages_dict = json.load(file)

async def ping_def(ctx) -> ReturnData:
    """
    Ping command
    :param ctx: Context
    :return: ReturnData
    """
    log(ctx, 'ping_def', [], log_type='function', author=ctx.author)
    save_json()

    message = f'**Pong!** Latency: {round(get_bot().latency * 1000)}ms'
    await ctx.reply(message)
    return ReturnData(True, message)

# noinspection PyTypeHints
async def language_command_def(ctx, country_code: Literal[tuple(languages_dict)]) -> ReturnData:
    """
    Change language of bot in guild
    :param ctx: Context
    :param country_code: Country code of language (e.g. en, cs, sk ...)
    :return: ReturnData
    """
    log(ctx, 'language_command_def', [country_code], log_type='function', author=ctx.author)
    is_ctx, guild_id, author_id, guild_object = ctx_check(ctx)
    guild = get_guild_dict()

    guild[guild_id].options.language = country_code
    save_json()

    message = f'{tg(guild_id, "Changed the language for this server to: ")} `{guild[guild_id].options.language}`'
    await ctx.reply(message)
    return ReturnData(True, message)

async def sound_effects_def(ctx, ephemeral: bool = True) -> ReturnData:
    """
    List of all sound effects
    :param ctx: Context
    :param ephemeral: Should bot response be ephemeral
    :return: ReturnData
    """
    log(ctx, 'sound_effects_def', [ephemeral], log_type='function', author=ctx.author)
    is_ctx, guild_id, author_id, guild_object = ctx_check(ctx)

    if not is_ctx:
        return ReturnData(False, tg(guild_id, 'Command cannot be used in WEB'))

    embed = discord.Embed(title="Sound Effects", colour=discord.Colour.from_rgb(241, 196, 15))
    message = ''
    for index, val in enumerate(get_all_sound_effects()):
        add = f'**{index}** -> {val}\n'

        if len(message) + len(add) > 1023:
            embed.add_field(name="", value=message, inline=False)
            message = ''
        else:
            message = message + add

    embed.add_field(name="", value=message, inline=False)

    save_json()
    await ctx.send(embed=embed, ephemeral=ephemeral)
    return ReturnData(True, tg(guild_id, 'Sound effects'))

async def list_radios_def(ctx, ephemeral: bool = True) -> ReturnData:
    """
    List of all radios
    :param ctx: Context
    :param ephemeral: Should bot response be ephemeral
    :return: ReturnData
    """
    log(ctx, 'list_radios_def', [ephemeral], log_type='function', author=ctx.author)
    is_ctx, guild_id, author_id, guild_object = ctx_check(ctx)

    if not is_ctx:
        return ReturnData(False, tg(guild_id, 'Command cannot be used in WEB'))

    embed = discord.Embed(title="Radio List")
    message = ''
    for index, (name, val) in enumerate(get_radio_dict().items()):
        add = f'**{index}** -> {name}\n'

        if len(message) + len(add) > 1023:
            embed.add_field(name="", value=message, inline=False)
            message = ''
        else:
            message = message + add

    embed.add_field(name="", value=message, inline=False)

    save_json()
    await ctx.send(embed=embed, ephemeral=ephemeral)
    return ReturnData(True, tg(guild_id, 'Radio list'))

async def key_def(ctx: dc_commands.Context) -> ReturnData:
    """
    Get key of guild
    :param ctx: Context
    :return: ReturnData
    """
    log(ctx, 'key_def', [], log_type='function', author=ctx.author)
    guild = get_guild_dict()
    save_json()

    message = f'Key: `{guild[ctx.guild.id].data.key}` -> [Control Panel]({config.WEB_URL}/guild/{ctx.guild.id}&key={guild[ctx.guild.id].data.key})'
    await ctx.reply(message)
    return ReturnData(True, message)

async def options_command_def(ctx, loop=None, language=None, response_type=None, buttons=None, volume=None, buffer=None, history_length=None) -> ReturnData:
    log(ctx, 'options_command_def', [loop, language, response_type, buttons, volume, buffer, history_length],
        log_type='function', author=ctx.author)
    is_ctx, guild_id, author_id, guild_object = ctx_check(ctx)

    if not is_ctx:
        return ReturnData(False, tg(guild_id, 'Command cannot be used in WEB'))

    if all(v is None for v in [loop, language, response_type, buttons, volume, buffer, history_length]):
        return await commands.admin.options_def(ctx, server=None, ephemeral=False)

    return await commands.admin.options_def(ctx, server=guild_id, ephemeral=False, loop=str(loop), language=str(language),
                             response_type=str(response_type), buttons=str(buttons), volume=str(volume),
                             buffer=str(buffer), history_length=str(history_length))