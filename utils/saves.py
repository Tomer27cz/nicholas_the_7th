from classes.data_classes import ReturnData, Save
from classes.video_class import to_save_video_class, to_queue_class, SaveVideo

from utils.convert import ascii_nospace
from utils.translate import tg
from utils.globals import get_session

from database.guild import guild, guild_ids, guild_save_names

def find_save(guild_id: int, save_name: str) -> Save or None:
    """
    Finds a save object
    :param guild_id: int - id of guild
    :param save_name: str - name of save
    :return: Save - save object
    """
    guild_object = guild(guild_id)
    for save in guild_object.saves:
        if save.name == save_name:
            return save
    return None

def new_queue_save(guild_id: int, save_name: str, author_name:str, author_id: int) -> ReturnData:
    """
    Creates new queue save
    :param guild_id: int - id of guild
    :param save_name: str - name of save
    :param author_name: str - name of author
    :param author_id: int - id of author
    :return: ReturnData - return data
    """
    guild_object = guild(guild_id)

    save_name = ascii_nospace(save_name)
    if save_name is False:
        return ReturnData(False, tg(guild_id, 'Save name must be alphanumeric'))

    if save_name in guild_save_names(guild_id):
        return ReturnData(False, tg(guild_id, 'save already exists'))

    if not guild_object.queue:
        return ReturnData(False, tg(guild_id, 'Queue is empty'))

    guild_object.saves.append(Save(guild_id, save_name, author_name, author_id))
    new_save = find_save(guild_id, save_name)
    for index, video in enumerate(guild_object.queue):
        new_save.queue.append(to_save_video_class(video, new_save.id))
    get_session().commit()

    return ReturnData(True, tg(guild_id, 'queue saved'))

def load_queue_save(guild_id: int, save_name: str) -> ReturnData:
    """
    Loads queue save
    :param guild_id: int - id of guild
    :param save_name: str - name of save
    :return: ReturnData - return data
    """

    if guild_id not in guild_ids():
        return ReturnData(False, tg(guild_id, 'no guild found for specified guild id'))

    if not guild_save_names(guild_id):
        return ReturnData(False, tg(guild_id, 'no saves found for specified guild'))

    if save_name not in guild_save_names(guild_id):
        return ReturnData(False, tg(guild_id, 'save not found'))

    load_save = find_save(guild_id, save_name)
    guild(guild_id).queue = [to_queue_class(video) for video in load_save.queue]
    get_session().commit()

    return ReturnData(True, tg(guild_id, 'queue loaded'))

def delete_queue_save(guild_id: int, save_name: str) -> ReturnData:
    """
    Deletes queue save
    :param guild_id: int - id of guild
    :param save_name: str - name of save
    :return: ReturnData - return data
    """
    if guild_id not in guild_ids():
        return ReturnData(False, tg(guild_id, 'no guild found for specified guild id'))

    if not guild_save_names(guild_id):
        return ReturnData(False, tg(guild_id, 'no saves found for specified guild'))

    if save_name not in guild_save_names(guild_id):
        return ReturnData(False, tg(guild_id, 'save not found'))

    save_delete = find_save(guild_id, save_name)
    get_session().query(SaveVideo).filter('save_id' == save_delete.id).all().delete()
    get_session().delete(save_delete)
    get_session().commit()

    return ReturnData(True, tg(guild_id, 'queue save deleted'))

def rename_queue_save(guild_id: int, old_name: str, new_name: str) -> ReturnData:
    """
    Renames queue save
    :param guild_id: int - id of guild
    :param old_name: str - old name of save
    :param new_name: str - new name of save
    :return: ReturnData - return data
    """

    new_name = ascii_nospace(new_name)
    if new_name is False:
        return ReturnData(False, tg(guild_id, 'Save name must be alphanumeric'))

    if guild_id not in guild_ids():
        return ReturnData(False, tg(guild_id, 'no guild found for specified guild id'))

    if not guild_save_names(guild_id):
        return ReturnData(False, tg(guild_id, 'no saves found for specified guild'))

    if old_name not in guild_save_names(guild_id):
        return ReturnData(False, tg(guild_id, 'save not found'))

    if new_name not in guild_save_names(guild_id):
        return ReturnData(False, tg(guild_id, 'save already exists'))

    find_save(guild_id, old_name).name = new_name
    get_session().commit()

    return ReturnData(True, tg(guild_id, 'queue save renamed'))