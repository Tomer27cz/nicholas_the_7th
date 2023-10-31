import classes.data_classes as data_classes
import classes.video_class as video_class
from utils.globals import get_session

def guild(guild_id: int):
    """
    Returns a guild object
    :param guild_id: ID of the guild
    :return: Guild object
    """
    return get_session().query(data_classes.Guild).filter_by(id=guild_id).first()


def guild_dict():
    """
    Returns a dictionary of guild objects
    :return: {guild_id: Guild object, ...}
    """
    guilds = {}
    for guild_object in get_session().query(data_classes.Guild).all():
        guilds[guild_object.id] = guild_object
    return guilds

def guild_ids():
    """
    Returns a list of guild IDs
    :return: [guild_id, ...]
    """
    guilds = []
    for guild_object in get_session().query(data_classes.Guild).all():
        guilds.append(guild_object.id)
    return guilds

def save_names(guild_id: int):
    """
    Returns a list of save names
    :param guild_id: ID of the guild
    :return: [save_name, ...]
    """
    return [save.name for save in guild(guild_id).saves]

def save_dict(guild_id: int):
    """
    Returns a dictionary of save objects
    :param guild_id: ID of the guild
    :return: {save_name: Save object, ...}
    """
    saves = {}
    for save in guild(guild_id).saves:
        saves[save.name] = save.queue
    return saves

def create_guild(guild_id: int):
    """
    Creates a guild object
    :param guild_id: ID of the guild
    :return: Guild object
    """
    guild_object = data_classes.Guild(guild_id)
    get_session().add(guild_object)
    get_session().commit()


def delete_guild(guild_id: int):
    """
    Deletes a guild object
    :param guild_id: ID of the guild
    :return: None
    """
    get_session().query(data_classes.Guild).filter_by(id=guild_id).delete()
    get_session().query(data_classes.GuildData).filter_by(id=guild_id).delete()
    get_session().query(data_classes.Options).filter_by(id=guild_id).delete()
    get_session().query(data_classes.Save).filter_by(id=guild_id).delete()

    get_session().query(video_class.SearchList).filter_by(guild_id=guild_id).delete()
    get_session().query(video_class.Queue).filter_by(guild_id=guild_id).delete()
    get_session().query(video_class.NowPlaying).filter_by(guild_id=guild_id).delete()
    get_session().query(video_class.History).filter_by(guild_id=guild_id).delete()
    get_session().query(video_class.SaveVideo).filter_by(guild_id=guild_id).delete()

    get_session().commit()