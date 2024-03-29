from utils.save import update
from utils.global_vars import GlobalVars

import classes.data_classes

from discord.ext import commands as dc_commands
import discord

def ctx_check(ctx: dc_commands.Context or classes.data_classes.WebData, glob: GlobalVars) -> (bool, int, int, discord.Guild):
    """
    This function checks if the context is a discord context or a web context and returns the relevant information.

    is_ctx - True if the context is a discord context, False if it is a web context
    guild_id - The guild id of the context
    author_id - The author id of the context
    guild_object - The guild object of the context

    :type ctx: dc_commands.Context | WebData
    :type glob: GlobalVars
    :param ctx: dc_commands.Context | WebData
    :param glob: GlobalVars
    :return: (is_ctx, guild_id, author_id, guild) - (bool, int, int, discord.Guild)
    """
    update(glob)

    if isinstance(ctx, classes.data_classes.WebData):
        bot = glob.bot
        is_ctx = False
        guild_id = ctx.guild_id
        author = ctx.author
        guild_object = bot.get_guild(guild_id)

    elif isinstance(ctx, dc_commands.Context):
        is_ctx = True
        guild_id = ctx.guild.id
        author = {'id': ctx.author.id, 'name': ctx.author.name}
        guild_object = ctx.guild

    else:
        raise TypeError(f'ctx_check: ctx is not a valid type: {type(ctx)}')

    return is_ctx, guild_id, author, guild_object
