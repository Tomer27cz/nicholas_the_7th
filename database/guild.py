from utils.global_vars import radio_dict
from utils.convert import struct_to_time
from utils.global_vars import GlobalVars

import classes.data_classes as data_classes
import classes.video_class as video_class

def guild(glob: GlobalVars, guild_id: int):
    """
    Returns a guild object
    :param glob: GlobalVars
    :param guild_id: ID of the guild
    :return: Guild object
    """
    with glob.ses.no_autoflush:
        return glob.ses.query(data_classes.Guild).filter_by(id=int(guild_id)).first()

def guilds(glob: GlobalVars):
    """
    Returns a list of guild objects
    :param glob: GlobalVars
    :return: [Guild object, ...]
    """
    with glob.ses.no_autoflush:
        return glob.ses.query(data_classes.Guild).all()

def guilds_last_played(glob: GlobalVars):
    """
    Returns a dictionary of guild ids and when was the last time they played a song
    if they never played a song, it will return "None"
    if they are playing a song, it will return "Now"
    :param glob: GlobalVars
    :return: [Guild object, ...]
    """
    with glob.ses.no_autoflush:
        guilds_dict = {}
        for guild_object in glob.ses.query(data_classes.Guild).all():
            if guild_object.now_playing is not None:
                guilds_dict[guild_object.id] = "Now"
                continue

            if not guild_object.history:
                guilds_dict[guild_object.id] = "None"
                continue

            last_played = guild_object.history[-1]
            if last_played is None:
                guilds_dict[guild_object.id] = "history[-1] is None"
                continue

            if not isinstance(last_played, video_class.History):
                guilds_dict[guild_object.id] = "last_played not history class"
                continue

            if last_played.played_duration is None:
                guilds_dict[guild_object.id] = "played_duration is None"
                continue

            if last_played.played_duration[-1]['end']['epoch'] is None:
                if last_played.played_duration[-1]['start']['epoch'] is None:
                    guilds_dict[guild_object.id] = "played_duration end&start = None"
                    continue
                guilds_dict[guild_object.id] = f"end none({struct_to_time(last_played.played_duration[-1]['start']['epoch'])})"
                continue

            guilds_dict[guild_object.id] = last_played.played_duration[-1]['end']['epoch']

        return guilds_dict

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
        _guilds = {}
        for guild_object in glob.ses.query(data_classes.Guild).all():
            _guilds[guild_object.id] = guild_object
        return _guilds

def guild_ids(glob: GlobalVars):
    """
    Returns a list of guild IDs
    :param glob: GlobalVars
    :return: [guild_id, ...]
    """
    with glob.ses.no_autoflush:
        _guilds = []
        for guild_object in glob.ses.query(data_classes.Guild).all():
            _guilds.append(guild_object.id)
        return _guilds

def guild_bar(glob: GlobalVars, guild_id: int) -> (int, int):
    """
    Returns the bar of the guild
    :param glob: GlobalVars
    :param guild_id: ID of the guild
    :return: (bar, max_bar)
    """
    return guild(glob, guild_id).bar, guild(glob, guild_id).max_bar

# Guild variables
def guild_data_key(glob: GlobalVars, guild_id: int):
    """
    Returns the key of the guild
    :param glob: GlobalVars
    :param guild_id: ID of the guild
    :return: str
    """
    return glob.ses.query(data_classes.GuildData).filter_by(id=guild_id).with_entities(data_classes.GuildData.key)[0][0]
def guild_options_loop(glob: GlobalVars, guild_id: int):
    """
    Returns the loop of the guild
    :param glob: GlobalVars
    :param guild_id: ID of the guild
    :return: bool
    """
    return glob.ses.query(data_classes.Options).filter_by(id=guild_id).with_entities(data_classes.Options.loop)[0][0]
def guild_options_buffer(glob: GlobalVars, guild_id: int):
    """
    Returns the buffer of the guild
    :param glob: GlobalVars
    :param guild_id: ID of the guild
    :return: int
    """
    return glob.ses.query(data_classes.Options).filter_by(id=guild_id).with_entities(data_classes.Options.buffer)[0][0]
def guild_options_response_type(glob: GlobalVars, guild_id: int):
    """
    Returns the response type of the guild
    :param glob: GlobalVars
    :param guild_id: ID of the guild
    :return: str
    """
    return glob.ses.query(data_classes.Options).filter_by(id=guild_id).with_entities(data_classes.Options.response_type)[0][0]
def guild_options_search_query(glob: GlobalVars, guild_id: int):
    """
    Returns the search query of the guild
    :param glob: GlobalVars
    :param guild_id: ID of the guild
    :return: str
    """
    return glob.ses.query(data_classes.Options).filter_by(id=guild_id).with_entities(data_classes.Options.search_query)[0][0]
def guild_options_language(glob: GlobalVars, guild_id: int):
    """
    Returns the language of the guild
    :param glob: GlobalVars
    :param guild_id: ID of the guild
    :return: str
    """
    return glob.ses.query(data_classes.Options).filter_by(id=guild_id).with_entities(data_classes.Options.language)[0][0]
def guild_options_is_radio(glob: GlobalVars, guild_id: int):
    """
    Returns whether or not the guild is a radio
    :param glob: GlobalVars
    :param guild_id: ID of the guild
    :return: bool
    """
    return glob.ses.query(data_classes.Options).filter_by(id=guild_id).with_entities(data_classes.Options.is_radio)[0][0]
def guild_options_volume(glob: GlobalVars, guild_id: int):
    """
    Returns the volume of the guild
    :param glob: GlobalVars
    :param guild_id: ID of the guild
    :return: float
    """
    return glob.ses.query(data_classes.Options).filter_by(id=guild_id).with_entities(data_classes.Options.volume)[0][0]
def guild_options_buttons(glob: GlobalVars, guild_id: int):
    """
    Returns the buttons of the guild
    :param glob: GlobalVars
    :param guild_id: ID of the guild
    :return: bool
    """
    return glob.ses.query(data_classes.Options).filter_by(id=guild_id).with_entities(data_classes.Options.buttons)[0][0]

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
        guild_object = data_classes.Guild(glob, guild_id, {})
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
        glob.ses.query(data_classes.Guild).filter_by(id=guild_id).delete()
        glob.ses.query(data_classes.GuildData).filter_by(id=guild_id).delete()
        glob.ses.query(data_classes.Options).filter_by(id=guild_id).delete()
        glob.ses.query(data_classes.Save).filter_by(id=guild_id).delete()

        glob.ses.query(video_class.Queue).filter_by(guild_id=guild_id).delete()
        glob.ses.query(video_class.NowPlaying).filter_by(guild_id=guild_id).delete()
        glob.ses.query(video_class.History).filter_by(guild_id=guild_id).delete()
        glob.ses.query(video_class.SaveVideo).filter_by(guild_id=guild_id).delete()

        glob.ses.commit()

# Queue
def guild_queue(glob: GlobalVars, guild_id: int):
    """
    Returns a list of videos in the queue
    :param glob: GlobalVars
    :param guild_id: ID of the guild
    :return: [Queue object, ...]
    """
    with glob.ses.no_autoflush:
        return glob.ses.query(video_class.Queue).filter_by(guild_id=guild_id).all()
def guild_history(glob: GlobalVars, guild_id: int):
    """
    Returns a list of videos in the history
    :param glob: GlobalVars
    :param guild_id: ID of the guild
    :return: [History object, ...]
    """
    with glob.ses.no_autoflush:
        return glob.ses.query(video_class.History).filter_by(guild_id=guild_id).all()

def clear_queue(glob: GlobalVars, guild_id: int) -> int:
    """
    Clears the queue
    :param glob: GlobalVars
    :param guild_id: ID of the guild
    :return: int - number of videos deleted
    """
    with glob.ses.no_autoflush:
        query = glob.ses.query(video_class.Queue).filter_by(guild_id=guild_id)
        query_count = query.count()
        query.delete()
        glob.ses.commit()
        return query_count

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
