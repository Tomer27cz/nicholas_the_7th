import classes.data_classes as data_classes
import classes.video_class as video_class
from utils.globals import get_session, get_radio_dict

def guild(guild_id: int):
    """
    Returns a guild object
    :param guild_id: ID of the guild
    :return: Guild object
    """
    with get_session().no_autoflush:
        return get_session().query(data_classes.Guild).filter_by(id=int(guild_id)).first()

def guild_data(guild_id: int):
    """
    Returns a guild data object
    :param guild_id: ID of the guild
    :return: GuildData object
    """
    with get_session().no_autoflush:
        return get_session().query(data_classes.GuildData).filter_by(id=int(guild_id)).first()

def guild_exists(guild_id: int):
    """
    Returns whether or not a guild exists
    :param guild_id: ID of the guild
    :return: bool
    """
    with get_session().no_autoflush:
        return get_session().query(data_classes.Guild).filter_by(id=guild_id).first() is not None

def guild_dict():
    """
    Returns a dictionary of guild objects
    :return: {guild_id: Guild object, ...}
    """
    with get_session().no_autoflush:
        guilds = {}
        for guild_object in get_session().query(data_classes.Guild).all():
            guilds[guild_object.id] = guild_object
        return guilds

def guild_ids():
    """
    Returns a list of guild IDs
    :return: [guild_id, ...]
    """
    with get_session().no_autoflush:
        guilds = []
        for guild_object in get_session().query(data_classes.Guild).all():
            guilds.append(guild_object.id)
        return guilds

def guild_bar(guild_id: int) -> (int, int):
    """
    Returns the bar of the guild
    :param guild_id: ID of the guild
    :return: (bar, max_bar)
    """
    return guild(guild_id).bar, guild(guild_id).max_bar

# Guild Save
def guild_save_count(guild_id: int):
    """
    Returns the number of saves in a guild
    :param guild_id: ID of the guild
    :return: int
    """
    with get_session().no_autoflush:
        return get_session().query(data_classes.Save).filter_by(guild_id=int(guild_id)).count()

def guild_save_queue_count(guild_id: int, save_id: int):
    """
    Returns the number of videos in a save
    :param guild_id: ID of the guild
    :param save_id: ID of the save
    :return: int
    """
    with get_session().no_autoflush:
        return get_session().query(video_class.SaveVideo).filter_by(guild_id=int(guild_id), save_id=save_id).count()

def guild_save(guild_id: int, save_id: int):
    """
    Returns a save object
    :param guild_id: ID of the guild
    :param save_id: ID of the save
    :return: Save object
    """
    with get_session().no_autoflush:
        return get_session().query(data_classes.Save).filter_by(guild_id=int(guild_id), id=int(save_id)).first()

def guild_save_names(guild_id: int):
    """
    Returns a list of save names
    :param guild_id: ID of the guild
    :return: [save_name, ...]
    """
    with get_session().no_autoflush:
        names = []
        for save_object in get_session().query(data_classes.Save).filter_by(guild_id=int(guild_id)).all():
            names.append(save_object.name)
        return names

# Guild Commands
def create_guild(guild_id: int):
    """
    Creates a guild object
    :param guild_id: ID of the guild
    :return: Guild object
    """
    with get_session().no_autoflush:
        guild_object = data_classes.Guild(guild_id)
        get_session().add(guild_object)
        get_session().commit()
def delete_guild(guild_id: int):
    """
    Deletes a guild object
    :param guild_id: ID of the guild
    :return: None
    """
    with get_session().no_autoflush:
        get_session().query(data_classes.Guild).filter_by(id=guild_id).all().delete()
        get_session().query(data_classes.GuildData).filter_by(id=guild_id).all().delete()
        get_session().query(data_classes.Options).filter_by(id=guild_id).all().delete()
        get_session().query(data_classes.Save).filter_by(id=guild_id).all().delete()

        get_session().query(video_class.SearchList).filter_by(guild_id=guild_id).all().delete()
        get_session().query(video_class.Queue).filter_by(guild_id=guild_id).all().delete()
        get_session().query(video_class.NowPlaying).filter_by(guild_id=guild_id).all().delete()
        get_session().query(video_class.History).filter_by(guild_id=guild_id).all().delete()
        get_session().query(video_class.SaveVideo).filter_by(guild_id=guild_id).all().delete()

        get_session().commit()

# Radio
def get_radio_info(radio_name: str):
    """
    Returns a radio object
    :param radio_name: Name of the radio
    :return: Radio object
    """
    with get_session().no_autoflush:
        radio_info_class = get_session().query(video_class.RadioInfo).filter_by(name=str(radio_name)).first()
        if radio_info_class is None:
            radio_dictionary = get_radio_dict()
            if radio_name not in radio_dictionary.keys():
                raise ValueError("Radio name not found")
            radio_info_class = video_class.RadioInfo(radio_id=get_radio_dict()[radio_name]['id'])
            get_session().add(radio_info_class)
            get_session().commit()
        return radio_info_class

# Slowed Users
def is_user_slowed(user_id: int, guild_id: int) -> (bool, int):
    """
    Returns whether or not a user is slowed
    :param user_id: ID of the user
    :param guild_id: ID of the guild
    :return: (bool, slowed_for)
    """
    with get_session().no_autoflush:
        slowed_user = get_session().query(data_classes.SlowedUser).filter_by(user_id=user_id, guild_id=guild_id).first()
        if slowed_user is None:
            return False, None
        return True, slowed_user.slowed_for

# Torture
def is_user_tortured(user_id: int, guild_id: int) -> (bool, int):
    """
    Returns whether or not a user is tortured
    :param user_id: ID of the user
    :param guild_id: ID of the guild
    :return: (bool, tortured_for)
    """
    with get_session().no_autoflush:
        tortured_user = get_session().query(data_classes.TorturedUser).filter_by(user_id=user_id, guild_id=guild_id).first()
        if tortured_user is None:
            return False, None
        return True, tortured_user.torture_delay

def delete_tortured_user(user_id: int, guild_id: int):
    """
    Deletes a tortured user
    :param user_id: ID of the user
    :param guild_id: ID of the guild
    :return: None
    """
    with get_session().no_autoflush:
        get_session().query(data_classes.TorturedUser).filter_by(user_id=user_id, guild_id=guild_id).delete()
        get_session().commit()