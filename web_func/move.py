from classes.data_classes import ReturnData

from utils.log import log
from utils.translate import tg
from utils.save import save_json
from utils.discord import to_queue
from utils.globals import get_guild_dict

from commands.utils import ctx_check

async def move_def(ctx, org_number, destination_number, ephemeral=True) -> ReturnData:
    log(ctx, 'web_move', [org_number, destination_number], log_type='function', author=ctx.author)
    is_ctx, guild_id, author_id, guild_object = ctx_check(ctx)
    guild = get_guild_dict()
    queue_length = len(guild[guild_id].queue)

    if queue_length == 0:
        log(ctx, "move_def -> No songs in queue")
        message = tg(guild_id, "No songs in queue")
        await ctx.reply(message, ephemeral=ephemeral)
        return ReturnData(False, message)

    org_number = int(org_number)
    destination_number = int(destination_number)

    if queue_length - 1 >= org_number >= 0:
        if queue_length - 1 >= destination_number >= 0:
            video = guild[guild_id].queue.pop(org_number)
            guild[guild_id].queue.insert(destination_number, video)

            save_json()

            message = f"{tg(guild_id, 'Moved')} #{org_number} to #{destination_number} : {video.title}"
            await ctx.reply(message, ephemeral=ephemeral)
            return ReturnData(True, message)

        message = f'{tg(guild_id, "Destination number must be between 0 and")} {queue_length - 1}'
        log(guild_id, f"move_def -> {message}")
        await ctx.reply(message, ephemeral=ephemeral)
        return ReturnData(False, message)

    message = f'{tg(guild_id, "Original number must be between 0 and")} {queue_length - 1}'
    log(guild_id, f"move_def -> {message}")
    await ctx.reply(message, ephemeral=ephemeral)
    return ReturnData(False, message)

async def web_up(web_data, number) -> ReturnData:
    log(web_data, 'web_up', [number], log_type='function', author=web_data.author)
    is_ctx, ctx_guild_id, ctx_author_id, ctx_guild_object = ctx_check(web_data)
    guild_id = web_data.guild_id
    queue_length = len(get_guild_dict()[guild_id].queue)
    number = int(number)

    if queue_length == 0:
        log(guild_id, "web_up -> No songs in queue")
        return ReturnData(False, tg(ctx_guild_id, 'No songs in queue'))

    if number == 0:
        return await move_def(web_data, 0, queue_length - 1)

    return await move_def(web_data, number, number - 1)

async def web_down(web_data, number) -> ReturnData:
    log(web_data, 'web_down', [number], log_type='function', author=web_data.author)
    is_ctx, ctx_guild_id, ctx_author_id, ctx_guild_object = ctx_check(web_data)
    guild_id = web_data.guild_id
    queue_length = len(get_guild_dict()[guild_id].queue)
    number = int(number)

    if queue_length == 0:
        log(guild_id, "web_down -> No songs in queue")
        return ReturnData(False, tg(ctx_guild_id, 'No songs in queue'))

    if number == queue_length - 1:
        return await move_def(web_data, number, 0)

    return await move_def(web_data, number, number + 1)

async def web_top(web_data, number) -> ReturnData:
    log(web_data, 'web_top', [number], log_type='function', author=web_data.author)
    is_ctx, ctx_guild_id, ctx_author_id, ctx_guild_object = ctx_check(web_data)
    guild_id = web_data.guild_id
    queue_length = len(get_guild_dict()[guild_id].queue)
    number = int(number)

    if queue_length == 0:
        log(guild_id, "web_top -> No songs in queue")
        return ReturnData(False, tg(ctx_guild_id, 'No songs in queue'))

    if number == 0:
        log(guild_id, "web_top -> Already at the top")
        return ReturnData(False, tg(ctx_guild_id, 'Already at the top'))

    return await move_def(web_data, number, 0)

async def web_bottom(web_data, number) -> ReturnData:
    log(web_data, 'web_bottom', [number], log_type='function', author=web_data.author)
    is_ctx, ctx_guild_id, ctx_author_id, ctx_guild_object = ctx_check(web_data)
    guild_id = web_data.guild_id
    queue_length = len(get_guild_dict()[guild_id].queue)
    number = int(number)

    if queue_length == 0:
        log(guild_id, "web_bottom -> No songs in queue")
        return ReturnData(False, tg(ctx_guild_id, 'No songs in queue'))

    if number == queue_length - 1:
        log(guild_id, "web_bottom -> Already at the bottom")
        return ReturnData(False, tg(ctx_guild_id, 'Already at the bottom'))

    return await move_def(web_data, number, queue_length - 1)

async def web_duplicate(web_data, number) -> ReturnData:
    log(web_data, 'web_duplicate', [number], log_type='function', author=web_data.author)
    is_ctx, ctx_guild_id, ctx_author_id, ctx_guild_object = ctx_check(web_data)
    guild = get_guild_dict()
    guild_id = web_data.guild_id
    queue_length = len(guild[guild_id].queue)
    number = int(number)

    if queue_length == 0:
        log(guild_id, "web_duplicate -> No songs in queue")
        return ReturnData(False, tg(ctx_guild_id, 'No songs in queue'))

    video = guild[guild_id].queue[number]

    to_queue(guild_id, video, position=number+1)

    message = f'{tg(ctx_guild_id, "Duplicated")} #{number} : {video.title}'
    log(guild_id, f"web_duplicate -> {message}")
    return ReturnData(True, message)