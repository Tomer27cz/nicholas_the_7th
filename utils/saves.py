from classes.data_classes import ReturnData
from utils.json import json_to_video
from utils.convert import ascii_nospace
from utils.translate import tg
from utils.globals import get_guild_dict

import json

def new_queue_save(guild_id: int, save_name: str) -> ReturnData:
    """
    Creates new queue save
    :param guild_id: int - id of guild
    :param save_name: str - name of save
    :return: ReturnData - return data
    """
    guild = get_guild_dict()

    save_name = ascii_nospace(save_name)
    if save_name is False:
        return ReturnData(False, tg(guild_id, 'Save name must be alphanumeric'))

    if save_name in guild[guild_id].saves:
        return ReturnData(False, tg(guild_id, 'save already exists'))

    if not guild[guild_id].queue:
        return ReturnData(False, tg(guild_id, 'Queue is empty'))

    with open(f'db/saves.json', 'r', encoding='utf-8') as f:
        saves = json.load(f)

    guild[guild_id].saves.append(save_name)

    if str(guild_id) not in saves.keys():
        guild[guild_id].saves = [save_name]
        saves[str(guild_id)] = {}

    if not list(saves[str(guild_id)].keys()) == guild[guild_id].saves:
        guild[guild_id].saves = list(saves[str(guild_id)].keys())

    queue_dict = {}
    for index, video in enumerate(guild[guild_id].queue):
        queue_dict[index] = video.__dict__
    saves[str(guild_id)][save_name] = queue_dict

    with open(f'db/saves.json', 'w', encoding='utf-8') as f:
        f.write(json.dumps(saves, indent=4))

    del saves

    return ReturnData(True, tg(guild_id, 'queue saved'))

def load_queue_save(guild_id: int, save_name: str) -> ReturnData:
    """
    Loads queue save
    :param guild_id: int - id of guild
    :param save_name: str - name of save
    :return: ReturnData - return data
    """
    guild = get_guild_dict()

    with open(f'db/saves.json', 'r', encoding='utf-8') as f:
        saves = json.loads(f.read())

    if guild_id not in guild.keys():
        return ReturnData(False, tg(guild_id, 'no guild found for specified guild id'))

    if str(guild_id) not in saves.keys():
        guild[guild_id].saves = []
        return ReturnData(False, tg(guild_id, 'no saves found for specified guild'))

    if save_name not in saves[str(guild_id)].keys():
        return ReturnData(False, tg(guild_id, 'save not found'))

    guild[guild_id].queue = [json_to_video(video_dict) for video_dict in saves[str(guild_id)][save_name].values()]

    del saves

    return ReturnData(True, tg(guild_id, 'queue loaded'))

def delete_queue_save(guild_id: int, save_name: str) -> ReturnData:
    """
    Deletes queue save
    :param guild_id: int - id of guild
    :param save_name: str - name of save
    :return: ReturnData - return data
    """
    guild = get_guild_dict()

    with open(f'db/saves.json', 'r', encoding='utf-8') as f:
        saves = json.loads(f.read())

    if guild_id not in guild.keys():
        return ReturnData(False, tg(guild_id, 'no guild found for specified guild id'))

    if str(guild_id) not in saves.keys():
        guild[guild_id].saves = []
        return ReturnData(False, tg(guild_id, 'no saves found for specified guild'))

    if save_name not in saves[str(guild_id)].keys():
        return ReturnData(False, tg(guild_id, 'save not found'))

    del saves[str(guild_id)][save_name]

    with open(f'db/saves.json', 'w', encoding='utf-8') as f:
        f.write(json.dumps(saves, indent=4))

    guild[guild_id].saves = list(saves[str(guild_id)].keys())

    del saves

    return ReturnData(True, tg(guild_id, 'queue save deleted'))

def rename_queue_save(guild_id: int, old_name: str, new_name: str) -> ReturnData:
    """
    Renames queue save
    :param guild_id: int - id of guild
    :param old_name: str - old name of save
    :param new_name: str - new name of save
    :return: ReturnData - return data
    """
    guild = get_guild_dict()

    new_name = ascii_nospace(new_name)
    if new_name is False:
        return ReturnData(False, tg(guild_id, 'Save name must be alphanumeric'))

    if guild_id not in guild.keys():
        return ReturnData(False, tg(guild_id, 'no guild found for specified guild id'))

    with open(f'db/saves.json', 'r', encoding='utf-8') as f:
        saves = json.loads(f.read())

    if str(guild_id) not in saves.keys():
        guild[guild_id].saves = []
        return ReturnData(False, tg(guild_id, 'no saves found for specified guild'))

    if old_name not in saves[str(guild_id)].keys():
        return ReturnData(False, tg(guild_id, 'save not found'))

    if new_name in saves[str(guild_id)].keys():
        return ReturnData(False, tg(guild_id, 'save already exists'))

    saves[str(guild_id)][new_name] = saves[str(guild_id)][old_name]
    del saves[str(guild_id)][old_name]

    with open(f'db/saves.json', 'w', encoding='utf-8') as f:
        f.write(json.dumps(saves, indent=4))

    guild[guild_id].saves = list(saves[str(guild_id)].keys())

    del saves

    return ReturnData(True, tg(guild_id, 'queue save renamed'))