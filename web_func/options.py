from classes.data_classes import ReturnData

from utils.log import log
from utils.translate import tg
from utils.convert import to_bool
from utils.globals import get_guild_dict, get_languages_dict

from commands.utils import ctx_check

async def web_user_options_edit(web_data, form) -> ReturnData:
    log(web_data, 'web_user_options_edit', [form], log_type='function', author=web_data.author)
    is_ctx, ctx_guild_id, ctx_author_id, ctx_guild_object = ctx_check(web_data)
    options = get_guild_dict()[web_data.guild_id].options

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
        return ReturnData(False, f'buttons has to be: {bool_list} --> {buttons}')

    if response_type not in response_types:
        return ReturnData(False, f'response_type has to be: {response_types} --> {response_type}')

    if language not in get_languages_dict():
        return ReturnData(False, f'language has to be: {get_languages_dict()} --> {language}')

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

    return ReturnData(True, tg(ctx_guild_id, f'Edited options successfully!'))