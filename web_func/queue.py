from classes.video_class import Queue
from classes.data_classes import ReturnData

from commands.utils import ctx_check

from database.guild import guild

from utils.log import log
from utils.translate import txt
from utils.save import update
from utils.discord import to_queue
from utils.global_vars import radio_dict, GlobalVars

async def web_queue(web_data, glob: GlobalVars, video_type, position=None) -> ReturnData:
    log(web_data, 'web_queue', options=locals(), log_type='function', author=web_data.author)
    is_ctx, ctx_guild_id, ctx_author, ctx_guild_object = ctx_check(web_data, glob)
    guild_id = web_data.guild_id
    db_guild = guild(glob, guild_id)

    if video_type == 'np':
        video = db_guild.now_playing
    else:
        try:
            index = int(video_type[1:])
            video = db_guild.history[index]
        except (TypeError, ValueError, IndexError):
            log(guild_id, "web_queue -> Invalid video type", log_type='function')
            return ReturnData(False, txt(ctx_guild_id, glob, 'Invalid video type (Internal web error -> contact developer)'))

    if video.class_type == 'Radio':
        return await web_queue_from_radio(web_data, glob, video.radio_info['name'], position)

    try:
        await to_queue(glob, guild_id, video, position=position)

        update(glob)
        log(guild_id, f"web_queue -> Queued: {video.url}", log_type='function')
        return ReturnData(True, f'{txt(ctx_guild_id, glob, "Queued")} {video.title}', video)

    except Exception as e:
        log(guild_id, f"web_queue -> Error while queuing: {e}", log_type='function')
        return ReturnData(False, txt(ctx_guild_id, glob, 'Error while queuing (Internal web error -> contact developer)'))

async def web_queue_from_radio(web_data, glob: GlobalVars, radio_name=None, position=None) -> ReturnData:
    log(web_data, 'web_queue_from_radio', options=locals(), log_type='function', author=web_data.author)
    is_ctx, ctx_guild_id, ctx_author, ctx_guild_object = ctx_check(web_data, glob)

    if radio_name in radio_dict.keys():
        video = await Queue.create(glob, 'Radio', web_data.author, ctx_guild_id, radio_info=dict(name=radio_name))

        if position == 'start':
            await to_queue(glob, web_data.guild_id, video, position=0, copy_video=False)
        else:
            await to_queue(glob, web_data.guild_id, video, copy_video=False)

        message = f'`{video.title}` ' + txt(ctx_guild_id, glob, 'added to queue!')
        update(glob)
        return ReturnData(True, message, video)

    else:
        message = txt(ctx_guild_id, glob, 'Radio station') + f' `{radio_name}` ' + txt(ctx_guild_id, glob, 'does not exist!')
        update(glob)
        return ReturnData(False, message)
