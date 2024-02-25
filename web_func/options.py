from classes.data_classes import ReturnData

from commands.utils import ctx_check

from database.guild import guild

from utils.log import log
from utils.translate import text
from utils.convert import to_bool
from utils.global_vars import languages_dict, GlobalVars

async def web_user_options_edit(web_data, glob: GlobalVars, form) -> ReturnData:
    log(web_data, 'web_user_options_edit', options=locals(), log_type='function', author=web_data.author)
    is_ctx, ctx_guild_id, ctx_author_id, ctx_guild_object = ctx_check(web_data, glob)
    options = guild(glob, web_data.guild_id).options

    loop = form['loop']
    language = form['language']
    response_type = form['response_type']
    buttons = form['buttons']
    volume = form['volume']
    buffer = form['buffer']
    history_length = form['history_length']

    bool_list_t = ['True', 'true', '1']
    bool_list_f = ['False', 'false', '0']
    bool_list = bool_list_f + bool_list_t
    response_types = ['long', 'short']

    if loop not in bool_list:
        return ReturnData(False, f'loop has to be: {bool_list} --> {loop}')
    if buttons not in bool_list:
        return ReturnData(False, f'single has to be: {bool_list} --> {buttons}')

    if response_type not in response_types:
        return ReturnData(False, f'response_type has to be: {response_types} --> {response_type}')

    if language not in languages_dict():
        return ReturnData(False, f'language has to be: {languages_dict()} --> {language}')

    if not volume.isdigit():
        return ReturnData(False, f'volume has to be a number: {volume}')
    if not buffer.isdigit():
        return ReturnData(False, f'buffer has to be a number: {buffer}')
    if not history_length.isdigit():
        return ReturnData(False, f'history_length has to be a number: {history_length}')

    options.loop = to_bool(loop)
    options.buttons = to_bool(buttons)

    options.language = language
    options.response_type = response_type

    options.volume = float(int(volume) * 0.01)
    options.buffer = int(buffer)
    options.history_length = int(history_length)

    return ReturnData(True, text(ctx_guild_id, glob, f'Edited options successfully!'))
