from utils.global_vars import GlobalVars

from classes.data_classes import ReturnData
from classes.video_class import Queue

from utils.log import log
from utils.translate import tg
from utils.save import save_json, push_update
from utils.discord import to_queue
from database.guild import guild

from commands.utils import ctx_check

async def move_def(ctx, glob: GlobalVars, org_number, destination_number, ephemeral=True) -> ReturnData:
    log(ctx, 'web_move', [org_number, destination_number], log_type='function', author=ctx.author)
    is_ctx, guild_id, author_id, guild_object = ctx_check(ctx, glob)
    db_guild = guild(glob, guild_id)
    queue_length = len(db_guild.queue)

    if queue_length == 0:
        log(ctx, "move_def -> No songs in queue")
        message = tg(guild_id, "No songs in queue")
        await ctx.reply(message, ephemeral=ephemeral)
        return ReturnData(False, message)

    org_number = int(org_number)
    destination_number = int(destination_number)

    if queue_length - 1 >= org_number >= 0:
        if queue_length - 1 >= destination_number >= 0:
            video = db_guild.queue.pop(org_number)
            db_guild.queue.insert(destination_number, video)

            save_json(glob)
            push_update(glob, guild_id)

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

async def web_up(web_data, glob: GlobalVars, number) -> ReturnData:
    log(web_data, 'web_up', [number], log_type='function', author=web_data.author)
    is_ctx, ctx_guild_id, ctx_author_id, ctx_guild_object = ctx_check(web_data, glob)
    guild_id = web_data.guild_id
    queue_length = len(guild(glob, guild_id).queue)
    number = int(number)

    if queue_length == 0:
        log(guild_id, "web_up -> No songs in queue")
        return ReturnData(False, tg(ctx_guild_id, 'No songs in queue'))

    if number == 0:
        return await move_def(web_data, glob, 0, queue_length - 1)

    return await move_def(web_data, glob, number, number - 1)

async def web_down(web_data, glob: GlobalVars, number) -> ReturnData:
    log(web_data, 'web_down', [number], log_type='function', author=web_data.author)
    is_ctx, ctx_guild_id, ctx_author_id, ctx_guild_object = ctx_check(web_data, glob)
    guild_id = web_data.guild_id
    queue_length = len(guild(glob, guild_id).queue)
    number = int(number)

    if queue_length == 0:
        log(guild_id, "web_down -> No songs in queue")
        return ReturnData(False, tg(ctx_guild_id, 'No songs in queue'))

    if number == queue_length - 1:
        return await move_def(web_data, glob, number, 0)

    return await move_def(web_data, glob, number, number + 1)

async def web_top(web_data, glob: GlobalVars, number) -> ReturnData:
    log(web_data, 'web_top', [number], log_type='function', author=web_data.author)
    is_ctx, ctx_guild_id, ctx_author_id, ctx_guild_object = ctx_check(web_data, glob)
    guild_id = web_data.guild_id
    queue_length = len(guild(glob, guild_id).queue)
    number = int(number)

    if queue_length == 0:
        log(guild_id, "web_top -> No songs in queue")
        return ReturnData(False, tg(ctx_guild_id, 'No songs in queue'))

    if number == 0:
        log(guild_id, "web_top -> Already at the top")
        return ReturnData(False, tg(ctx_guild_id, 'Already at the top'))

    return await move_def(web_data, glob, number, 0)

async def web_bottom(web_data, glob: GlobalVars, number) -> ReturnData:
    log(web_data, 'web_bottom', [number], log_type='function', author=web_data.author)
    is_ctx, ctx_guild_id, ctx_author_id, ctx_guild_object = ctx_check(web_data, glob)
    guild_id = web_data.guild_id
    queue_length = len(guild(glob, guild_id).queue)
    number = int(number)

    if queue_length == 0:
        log(guild_id, "web_bottom -> No songs in queue")
        return ReturnData(False, tg(ctx_guild_id, 'No songs in queue'))

    if number == queue_length - 1:
        log(guild_id, "web_bottom -> Already at the bottom")
        return ReturnData(False, tg(ctx_guild_id, 'Already at the bottom'))

    return await move_def(web_data, glob, number, queue_length - 1)

async def web_duplicate(web_data, glob: GlobalVars, number) -> ReturnData:
    log(web_data, 'web_duplicate', [number], log_type='function', author=web_data.author)
    is_ctx, ctx_guild_id, ctx_author_id, ctx_guild_object = ctx_check(web_data, glob)
    guild_id = web_data.guild_id
    db_guild = guild(glob, guild_id)
    queue_length = len(db_guild.queue)
    number = int(number)

    if queue_length == 0:
        log(guild_id, "web_duplicate -> No songs in queue")
        return ReturnData(False, tg(ctx_guild_id, 'No songs in queue'))

    video = db_guild.queue[number]

    new_video = Queue(glob,class_type=video.class_type,
                    author=video.author,
                    guild_id=video.guild_id,
                    url=video.url,
                    title=video.title,
                    picture=video.picture,
                    duration=video.duration,
                    channel_name=video.channel_name,
                    channel_link=video.channel_link,
                    radio_info=video.radio_info,
                    local_number=video.local_number)

    to_queue(glob, guild_id, new_video, position=number+1, copy_video=True)

    message = f'{tg(ctx_guild_id, "Duplicated")} #{number} : {video.title}'
    log(guild_id, f"web_duplicate -> {message}")
    return ReturnData(True, message)