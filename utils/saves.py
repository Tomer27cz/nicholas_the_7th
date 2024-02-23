from utils.global_vars import GlobalVars

from classes.data_classes import ReturnData, Save
from classes.video_class import to_save_video_class, to_queue_class, SaveVideo

from utils.convert import ascii_nospace
from utils.translate import text

from database.guild import guild, guild_ids, guild_save_names

def find_save(glob: GlobalVars, guild_id: int, save_name: str) -> Save or None:
    """
    Finds a save object
    :param glob: GlobalVars
    :param guild_id: int - id of guild
    :param save_name: str - name of save
    :return: Save - save object
    """
    guild_object = guild(glob, guild_id)
    for save in guild_object.saves:
        if save.name == save_name:
            return save
    return None

def new_queue_save(glob: GlobalVars, guild_id: int, save_name: str, author_name: str, author_id: int) -> ReturnData:
    """
    Creates new queue save
    :param glob: GlobalVars
    :param guild_id: int - id of guild
    :param save_name: str - name of save
    :param author_name: str - name of author
    :param author_id: int - id of author
    :return: ReturnData - return data
    """
    guild_object = guild(glob, guild_id)

    save_name = ascii_nospace(save_name)
    if save_name is False:
        return ReturnData(False, text(guild_id, glob, 'Save name must be alphanumeric'))

    if save_name in guild_save_names(glob, guild_id):
        return ReturnData(False, text(guild_id, glob, 'save already exists'))

    if not guild_object.queue:
        return ReturnData(False, text(guild_id, glob, 'Queue is empty'))

    guild_object.saves.append(Save(guild_id, save_name, author_name, author_id))
    new_save = find_save(glob, guild_id, save_name)
    for index, video in enumerate(guild_object.queue):
        new_save.queue.append(to_save_video_class(glob, video, new_save.id))
    glob.ses.commit()

    return ReturnData(True, text(guild_id, glob, 'queue saved'))

def load_queue_save(glob: GlobalVars, guild_id: int, save_name: str) -> ReturnData:
    """
    Loads queue save
    :param glob: GlobalVars
    :param guild_id: int - id of guild
    :param save_name: str - name of save
    :return: ReturnData - return data
    """

    if guild_id not in guild_ids(glob):
        return ReturnData(False, text(guild_id, glob, 'no guild found for specified guild id'))

    if not guild_save_names(glob, guild_id):
        return ReturnData(False, text(guild_id, glob, 'no saves found for specified guild'))

    if save_name not in guild_save_names(glob, guild_id):
        return ReturnData(False, text(guild_id, glob, 'save not found'))

    load_save = find_save(glob, guild_id, save_name)
    guild(glob, guild_id).queue = [to_queue_class(glob, video) for video in load_save.queue]
    glob.ses.commit()

    return ReturnData(True, text(guild_id, glob, 'queue loaded'))

def delete_queue_save(glob: GlobalVars, guild_id: int, save_name: str) -> ReturnData:
    """
    Deletes queue save
    :param glob: GlobalVars
    :param guild_id: int - id of guild
    :param save_name: str - name of save
    :return: ReturnData - return data
    """
    if guild_id not in guild_ids(glob):
        return ReturnData(False, text(guild_id, glob, 'no guild found for specified guild id'))

    if not guild_save_names(glob, guild_id):
        return ReturnData(False, text(guild_id, glob, 'no saves found for specified guild'))

    if save_name not in guild_save_names(glob, guild_id):
        return ReturnData(False, text(guild_id, glob, 'save not found'))

    save_delete = find_save(glob, guild_id, save_name)
    glob.ses.query(SaveVideo).filter('save_id' == save_delete.id).delete()
    glob.ses.delete(save_delete)
    glob.ses.commit()

    return ReturnData(True, text(guild_id, glob, 'queue save deleted'))

def rename_queue_save(glob: GlobalVars, guild_id: int, old_name: str, new_name: str) -> ReturnData:
    """
    Renames queue save
    :param glob: GlobalVars
    :param guild_id: int - id of guild
    :param old_name: str - old name of save
    :param new_name: str - new name of save
    :return: ReturnData - return data
    """

    new_name = ascii_nospace(new_name)
    if new_name is False:
        return ReturnData(False, text(guild_id, glob, 'Save name must be alphanumeric'))

    if guild_id not in guild_ids(glob):
        return ReturnData(False, text(guild_id, glob, 'no guild found for specified guild id'))

    if not guild_save_names(glob, guild_id):
        return ReturnData(False, text(guild_id, glob, 'no saves found for specified guild'))

    if old_name not in guild_save_names(glob, guild_id):
        return ReturnData(False, text(guild_id, glob, 'save not found'))

    if new_name not in guild_save_names(glob, guild_id):
        return ReturnData(False, text(guild_id, glob, 'save already exists'))

    find_save(glob, guild_id, old_name).name = new_name
    glob.ses.commit()

    return ReturnData(True, text(guild_id, glob, 'queue save renamed'))
