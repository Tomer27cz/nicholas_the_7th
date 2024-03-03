from classes.data_classes import ReturnData

from commands.utils import ctx_check
from commands.autocomplete import radio_autocomplete_def, tunein_autocomplete_def

import classes.view
import commands.player

from utils.log import log
from utils.translate import txt
from utils.global_vars import GlobalVars
from utils.radio import update_radio_dict
from utils.url import get_url_type, command_for_type

import discord

async def radio_cz_def(ctx, glob: GlobalVars, query: str, mute_response: bool=False) -> ReturnData:
    """
    Play radio from radia.cz
    :param ctx: Context
    :param glob: GlobalVars
    :param query: str - czech radio id or name
    :param mute_response: bool - mute response
    :return: ReturnData
    """
    log(ctx, 'radio_cz_def', options=locals(), log_type='function', author=ctx.author)
    is_ctx, guild_id, author_id, guild_object = ctx_check(ctx, glob)

    # noinspection PyUnresolvedReferences
    if is_ctx:
        if not ctx.interaction.response.is_done():
            await ctx.defer()

    await update_radio_dict()

    url_type, url = get_url_type(query)
    if url_type not in ['RadioCz', 'String']:
        message = txt(guild_id, glob, "Wrong command! Try ") + f"`/{command_for_type(url_type)}`"
        if not mute_response:
            await ctx.reply(message)
        return ReturnData(False, message)

    if url_type == 'RadioCz':
        return await commands.player.play_def(ctx, glob, url, force=True, no_search=True, embed=True, mute_response=mute_response, radio=True)

    radios: list[discord.app_commands.Choice] = await radio_autocomplete_def(None, query, 5)
    if not radios:
        message = txt(guild_id, glob, "Radio **not found**")
        if not mute_response:
            await ctx.reply(message)
        return ReturnData(False, message)

    view = classes.view.OptionView(ctx, glob, [radio.value for radio in radios], 'RadioCz')

    message = txt(guild_id, glob, "Choose radio")
    for index, radio in enumerate(radios):
        message += f"\n**{index + 1}#** `{radio.name}`"

    if not mute_response:
        view.message = await ctx.reply(message, view=view)
    return ReturnData(True, message)

async def radio_garden_def(ctx, glob: GlobalVars, query: str, mute_response: bool=False) -> ReturnData:
    """
    Play radio from radio.garden
    :param ctx: Context
    :param glob: GlobalVars
    :param query: str - radio.garden
    :param mute_response: bool - mute response
    :return: ReturnData
    """
    log(ctx, 'radio_garden_def', options=locals(), log_type='function', author=ctx.author)
    is_ctx, guild_id, author_id, guild_object = ctx_check(ctx, glob)

    # noinspection PyUnresolvedReferences
    if is_ctx:
        if not ctx.interaction.response.is_done():
            await ctx.defer()

    url_type, url = get_url_type(query)
    if url_type not in ['RadioGarden', 'String']:
        message = txt(guild_id, glob, "Wrong command! Try ") + f"`/{command_for_type(url_type)}`"
        if not mute_response:
            await ctx.reply(message)
        return ReturnData(False, message)

    if url_type == 'RadioGarden':
        return await commands.player.play_def(ctx, glob, query, force=True, no_search=True, embed=True, mute_response=mute_response, radio=True)

    radios: list[discord.app_commands.Choice] = await radio_autocomplete_def(None, query, 5)
    if not radios:
        message = txt(guild_id, glob, "Radio **not found**")
        if not mute_response:
            await ctx.reply(message)
        return ReturnData(False, message)

    view = classes.view.OptionView(ctx, glob, [radio.value for radio in radios], 'RadioGarden')

    message = txt(guild_id, glob, "Choose radio")
    for index, radio in enumerate(radios):
        message += f"\n**{index + 1}#** `{radio.name}`"

    if not mute_response:
        view.message = await ctx.reply(message, view=view)
    return ReturnData(True, message)

async def radio_tunein_def(ctx, glob: GlobalVars, query: str, mute_response: bool=False) -> ReturnData:
    """
    Play radio from tunein
    :param ctx: Context
    :param glob: GlobalVars
    :param query: str - tunein id or name
    :param mute_response: bool - mute response
    :return: ReturnData
    """
    log(ctx, 'radio_tunein_def', options=locals(), log_type='function', author=ctx.author)
    is_ctx, guild_id, author_id, guild_object = ctx_check(ctx, glob)

    # noinspection PyUnresolvedReferences
    if is_ctx:
        if not ctx.interaction.response.is_done():
            await ctx.defer()

    url_type, url = get_url_type(query)
    if url_type not in ['RadioTuneIn', 'String']:
        message = txt(guild_id, glob, "Wrong command! Try ") + f"`/{command_for_type(url_type)}`"
        if not mute_response:
            await ctx.reply(message)
        return ReturnData(False, message)

    if url_type == 'RadioTuneIn':
        return await commands.player.play_def(ctx, glob, query, force=True, no_search=True, embed=True, mute_response=mute_response, radio=True)

    radios: list[discord.app_commands.Choice] = await tunein_autocomplete_def(None, query)
    if not radios:
        message = txt(guild_id, glob, "Radio **not found**")
        if not mute_response:
            await ctx.reply(message)
        return ReturnData(False, message)

    view = classes.view.OptionView(ctx, glob, [radio.value for radio in radios], 'RadioTuneIn')

    message = txt(guild_id, glob, "Choose radio")
    for index, radio in enumerate(radios):
        message += f"\n**{index+1}#** `{radio.name}`"

    if not mute_response:
        view.message = await ctx.reply(message, view=view)
    return ReturnData(True, message)
