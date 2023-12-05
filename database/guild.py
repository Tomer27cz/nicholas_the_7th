from utils.global_vars import GlobalVars

import classes.data_classes as data_classes
import classes.video_class as video_class
from utils.global_vars import radio_dict

def guild(glob: GlobalVars, guild_id: int):
    """
    Returns a guild object
    :param glob: GlobalVars
    :param guild_id: ID of the guild
    :return: Guild object
    """
    with glob.ses.no_autoflush:
        return glob.ses.query(data_classes.Guild).filter_by(id=int(guild_id)).first()

def guild_data(glob: GlobalVars, guild_id: int):
    """
    Returns a guild data object
    :param glob: GlobalVars
    :param guild_id: ID of the guild
    :return: GuildData object
    """
    with glob.ses.no_autoflush:
        return glob.ses.query(data_classes.GuildData).filter_by(id=int(guild_id)).first()

def guild_exists(glob: GlobalVars, guild_id: int):
    """
    Returns whether or not a guild exists
    :param glob: GlobalVars
    :param guild_id: ID of the guild
    :return: bool
    """
    with glob.ses.no_autoflush:
        return glob.ses.query(data_classes.Guild).filter_by(id=guild_id).first() is not None

def guild_dict(glob: GlobalVars):
    """
    Returns a dictionary of guild objects
    :param glob: GlobalVars
    :return: {guild_id: Guild object, ...}
    """
    with glob.ses.no_autoflush:
        guilds = {}
        for guild_object in glob.ses.query(data_classes.Guild).all():
            guilds[guild_object.id] = guild_object
        return guilds

def guild_ids(glob: GlobalVars):
    """
    Returns a list of guild IDs
    :param glob: GlobalVars
    :return: [guild_id, ...]
    """
    with glob.ses.no_autoflush:
        guilds = []
        for guild_object in glob.ses.query(data_classes.Guild).all():
            guilds.append(guild_object.id)
        return guilds

def guild_bar(glob: GlobalVars, guild_id: int) -> (int, int):
    """
    Returns the bar of the guild
    :param glob: GlobalVars
    :param guild_id: ID of the guild
    :return: (bar, max_bar)
    """
    return guild(glob, guild_id).bar, guild(glob, guild_id).max_bar

# Guild Save
def guild_save_count(glob: GlobalVars, guild_id: int):
    """
    Returns the number of saves in a guild
    :param glob: GlobalVars
    :param guild_id: ID of the guild
    :return: int
    """
    with glob.ses.no_autoflush:
        return glob.ses.query(data_classes.Save).filter_by(guild_id=int(guild_id)).count()

def guild_save_queue_count(glob: GlobalVars, guild_id: int, save_id: int):
    """
    Returns the number of videos in a save
    :param glob: GlobalVars
    :param guild_id: ID of the guild
    :param save_id: ID of the save
    :return: int
    """
    with glob.ses.no_autoflush:
        return glob.ses.query(video_class.SaveVideo).filter_by(guild_id=int(guild_id), save_id=save_id).count()

def guild_save(glob: GlobalVars, guild_id: int, save_id: int):
    """
    Returns a save object
    :param glob: GlobalVars
    :param guild_id: ID of the guild
    :param save_id: ID of the save
    :return: Save object
    """
    with glob.ses.no_autoflush:
        return glob.ses.query(data_classes.Save).filter_by(guild_id=int(guild_id), id=int(save_id)).first()

def guild_save_names(glob: GlobalVars, guild_id: int):
    """
    Returns a list of save names
    :param glob: GlobalVars
    :param guild_id: ID of the guild
    :return: [save_name, ...]
    """
    with glob.ses.no_autoflush:
        names = []
        for save_object in glob.ses.query(data_classes.Save).filter_by(guild_id=int(guild_id)).all():
            names.append(save_object.name)
        return names

# Guild Commands
def create_guild(glob: GlobalVars, guild_id: int):
    """
    Creates a guild object
    :param glob: GlobalVars
    :param guild_id: ID of the guild
    :return: Guild object
    """
    with glob.ses.no_autoflush:
        guild_object = data_classes.Guild(glob, guild_id)
        glob.ses.add(guild_object)
        glob.ses.commit()
def delete_guild(glob: GlobalVars, guild_id: int):
    """
    Deletes a guild object
    :param glob: GlobalVars
    :param guild_id: ID of the guild
    :return: None
    """
    with glob.ses.no_autoflush:
        glob.ses.query(data_classes.Guild).filter_by(id=guild_id).all().delete()
        glob.ses.query(data_classes.GuildData).filter_by(id=guild_id).all().delete()
        glob.ses.query(data_classes.Options).filter_by(id=guild_id).all().delete()
        glob.ses.query(data_classes.Save).filter_by(id=guild_id).all().delete()

        glob.ses.query(video_class.SearchList).filter_by(guild_id=guild_id).all().delete()
        glob.ses.query(video_class.Queue).filter_by(guild_id=guild_id).all().delete()
        glob.ses.query(video_class.NowPlaying).filter_by(guild_id=guild_id).all().delete()
        glob.ses.query(video_class.History).filter_by(guild_id=guild_id).all().delete()
        glob.ses.query(video_class.SaveVideo).filter_by(guild_id=guild_id).all().delete()

        glob.ses.commit()

# Radio
def get_radio_info(glob: GlobalVars, radio_name: str):
    """
    Returns a radio object
    :param glob: GlobalVars
    :param radio_name: Name of the radio
    :return: Radio object
    """
    with glob.ses.no_autoflush:
        radio_info_class = glob.ses.query(video_class.RadioInfo).filter_by(name=str(radio_name)).first()
        if radio_info_class is None:
            radio_dictionary = radio_dict
            if radio_name not in radio_dictionary.keys():
                raise ValueError("Radio name not found")
            radio_info_class = video_class.RadioInfo(radio_id=radio_dict[radio_name]['id'])
            glob.ses.add(radio_info_class)
            glob.ses.commit()
        return radio_info_class

# Slowed Users
def is_user_slowed(glob: GlobalVars, user_id: int, guild_id: int) -> (bool, int):
    """
    Returns whether or not a user is slowed
    :param glob: GlobalVars
    :param user_id: ID of the user
    :param guild_id: ID of the guild
    :return: (bool, slowed_for)
    """
    with glob.ses.no_autoflush:
        slowed_user = glob.ses.query(data_classes.SlowedUser).filter_by(user_id=user_id, guild_id=guild_id).first()
        if slowed_user is None:
            return False, None
        return True, slowed_user.slowed_for

# Torture
def is_user_tortured(glob: GlobalVars, user_id: int, guild_id: int) -> (bool, int):
    """
    Returns whether or not a user is tortured
    :param glob: GlobalVars
    :param user_id: ID of the user
    :param guild_id: ID of the guild
    :return: (bool, tortured_for)
    """
    with glob.ses.no_autoflush:
        tortured_user = glob.ses.query(data_classes.TorturedUser).filter_by(user_id=user_id, guild_id=guild_id).first()
        if tortured_user is None:
            return False, None
        return True, tortured_user.torture_delay

def delete_tortured_user(glob: GlobalVars, user_id: int, guild_id: int):
    """
    Deletes a tortured user
    :param glob: GlobalVars
    :param user_id: ID of the user
    :param guild_id: ID of the guild
    :return: None
    """
    with glob.ses.no_autoflush:
        glob.ses.query(data_classes.TorturedUser).filter_by(user_id=user_id, guild_id=guild_id).delete()
        glob.ses.commit()