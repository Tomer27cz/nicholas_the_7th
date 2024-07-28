from classes.data_classes import ReturnData, Save
from classes.video_class import to_save_video_class, to_queue_class, SaveVideo
from classes.typed_dictionaries import VideoAuthor

from database.guild import guild, guild_ids, guild_save_names

from utils.global_vars import GlobalVars
from utils.convert import ascii_nospace, czech_to_ascii
from utils.translate import txt

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

async def new_queue_save(glob: GlobalVars, guild_id: int, save_name: str, author: VideoAuthor) -> ReturnData:
    """
    Creates new queue save
    :param glob: GlobalVars
    :param guild_id: int - id of guild
    :param save_name: str - name of save
    :param author: VideoAuthor - author of save
    :return: ReturnData - return data
    """
    guild_object = guild(glob, guild_id)

    save_name = ascii_nospace(czech_to_ascii(save_name))
    if save_name is False:
        return ReturnData(False, txt(guild_id, glob, 'Save name must be alphanumeric'))

    if save_name in guild_save_names(glob, guild_id):
        return ReturnData(False, txt(guild_id, glob, 'Save already exists: ') + save_name)

    if not guild_object.queue:
        return ReturnData(False, txt(guild_id, glob, 'Queue is empty'))

    guild_object.saves.append(Save(guild_id, save_name, author))
    new_save = find_save(glob, guild_id, save_name)
    for index, video in enumerate(guild_object.queue):
        new_save.queue.append(await to_save_video_class(glob, video, new_save.id))
    glob.ses.commit()

    return ReturnData(True, txt(guild_id, glob, 'Queue saved: ') + save_name)

async def load_queue_save(glob: GlobalVars, guild_id: int, save_name: str) -> ReturnData:
    """
    Loads queue save
    :param glob: GlobalVars
    :param guild_id: int - id of guild
    :param save_name: str - name of save
    :return: ReturnData - return data
    """

    if guild_id not in guild_ids(glob):
        return ReturnData(False, txt(guild_id, glob, 'No guild found for specified guild id'))

    if not guild_save_names(glob, guild_id):
        return ReturnData(False, txt(guild_id, glob, 'No saves found for specified guild'))

    if save_name not in guild_save_names(glob, guild_id):
        return ReturnData(False, txt(guild_id, glob, 'Save not found: ') + save_name)

    load_save = find_save(glob, guild_id, save_name)
    guild(glob, guild_id).queue = [await to_queue_class(glob, video) for video in load_save.queue]
    glob.ses.commit()

    return ReturnData(True, txt(guild_id, glob, 'Queue loaded: ') + save_name)

def delete_queue_save(glob: GlobalVars, guild_id: int, save_name: str) -> ReturnData:
    """
    Deletes queue save
    :param glob: GlobalVars
    :param guild_id: int - id of guild
    :param save_name: str - name of save
    :return: ReturnData - return data
    """
    if guild_id not in guild_ids(glob):
        return ReturnData(False, txt(guild_id, glob, 'No guild found for specified guild id'))

    if not guild_save_names(glob, guild_id):
        return ReturnData(False, txt(guild_id, glob, 'No saves found for specified guild'))

    if save_name not in guild_save_names(glob, guild_id):
        return ReturnData(False, txt(guild_id, glob, 'Save not found: ') + save_name)

    save_delete = find_save(glob, guild_id, save_name)
    glob.ses.query(SaveVideo).filter('save_id' == save_delete.id).delete()
    glob.ses.delete(save_delete)
    glob.ses.commit()

    return ReturnData(True, txt(guild_id, glob, 'Queue save deleted: ') + save_name)

def rename_queue_save(glob: GlobalVars, guild_id: int, old_name: str, new_name: str) -> ReturnData:
    """
    Renames queue save
    :param glob: GlobalVars
    :param guild_id: int - id of guild
    :param old_name: str - old name of save
    :param new_name: str - new name of save
    :return: ReturnData - return data
    """

    new_name = ascii_nospace(czech_to_ascii(new_name))
    if new_name is False:
        return ReturnData(False, txt(guild_id, glob, 'Save name must be alphanumeric'))

    if guild_id not in guild_ids(glob):
        return ReturnData(False, txt(guild_id, glob, 'No guild found for specified guild id'))

    if not guild_save_names(glob, guild_id):
        return ReturnData(False, txt(guild_id, glob, 'No saves found for specified guild'))

    if old_name not in guild_save_names(glob, guild_id):
        return ReturnData(False, txt(guild_id, glob, 'Save not found: ') + old_name)

    if new_name not in guild_save_names(glob, guild_id):
        return ReturnData(False, txt(guild_id, glob, 'Save already exists: ') + new_name)

    find_save(glob, guild_id, old_name).name = new_name
    glob.ses.commit()

    return ReturnData(True, txt(guild_id, glob, 'Queue save renamed: ') + f"{old_name} -> {new_name}")
