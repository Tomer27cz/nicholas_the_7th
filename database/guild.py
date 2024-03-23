from utils.convert import struct_to_time
from utils.global_vars import GlobalVars

import classes.data_classes as data_classes
import classes.video_class as video_class

from flask_sqlalchemy import SQLAlchemy

def get_session(glob: GlobalVars or SQLAlchemy):
    if isinstance(glob, GlobalVars):
        return glob.ses
    elif isinstance(glob, SQLAlchemy):
        return glob.session
    else:
        raise TypeError("glob must be either GlobalVars or SQLAlchemy")

def guild(glob: GlobalVars or SQLAlchemy, guild_id: int) -> data_classes.Guild:
    """
    Returns a guild object
    :param glob: GlobalVars or SQLAlchemy
    :param guild_id: ID of the guild
    :return: Guild object
    """
    session = get_session(glob)
    with session.no_autoflush:
        return session.query(data_classes.Guild).filter_by(id=int(guild_id)).first()

def guilds(glob: GlobalVars or SQLAlchemy) -> list[data_classes.Guild]:
    """
    Returns a list of guild objects
    :param glob: GlobalVars or SQLAlchemy
    :return: [Guild object, ...]
    """
    session = get_session(glob)
    with session.no_autoflush:
        return session.query(data_classes.Guild).all()

def guilds_last_played(glob: GlobalVars or SQLAlchemy) -> dict[int, str]:
    """
    Returns a dictionary of guild ids and when was the last time they played a song
    if they never played a song, it will return "None"
    if they are playing a song, it will return "Now"
    :param glob: GlobalVars or SQLAlchemy
    :return: [Guild object, ...]
    """
    session = get_session(glob)
    with session.no_autoflush:
        guilds_dict = {}
        for guild_object in session.query(data_classes.Guild).all():
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

def guild_data(glob: GlobalVars or SQLAlchemy, guild_id: int) -> data_classes.GuildData:
    """
    Returns a guild data object
    :param glob: GlobalVars or SQLAlchemy
    :param guild_id: ID of the guild
    :return: GuildData object
    """
    session = get_session(glob)
    with session.no_autoflush:
        return session.query(data_classes.GuildData).filter_by(id=int(guild_id)).first()

def guild_exists(glob: GlobalVars or SQLAlchemy, guild_id: int) -> bool:
    """
    Returns whether or not a guild exists
    :param glob: GlobalVars or SQLAlchemy
    :param guild_id: ID of the guild
    :return: bool
    """
    session = get_session(glob)
    with session.no_autoflush:
        return session.query(data_classes.Guild).filter_by(id=guild_id).first() is not None

def guild_dict(glob: GlobalVars or SQLAlchemy) -> dict[int, data_classes.Guild]:
    """
    Returns a dictionary of guild objects
    :param glob: GlobalVars or SQLAlchemy
    :return: {guild_id: Guild object, ...}
    """
    session = get_session(glob)
    with session.no_autoflush:
        _guilds = {}
        for guild_object in session.query(data_classes.Guild).all():
            _guilds[guild_object.id] = guild_object
        return _guilds

def guild_ids(glob: GlobalVars or SQLAlchemy) -> list[int]:
    """
    Returns a list of guild IDs
    :param glob: GlobalVars or SQLAlchemy
    :return: [guild_id, ...]
    """
    session = get_session(glob)
    with session.no_autoflush:
        _guilds = []
        for guild_object in session.query(data_classes.Guild).all():
            _guilds.append(guild_object.id)
        return _guilds

def guild_bar(glob: GlobalVars or SQLAlchemy, guild_id: int) -> (int, int):
    """
    Returns the bar of the guild
    :param glob: GlobalVars or SQLAlchemy
    :param guild_id: ID of the guild
    :return: (bar, max_bar)
    """
    return guild(glob, guild_id).bar, guild(glob, guild_id).max_bar

# Guild variables
def guild_last_updated(glob: GlobalVars or SQLAlchemy, guild_id: int) -> int or None:
    """
    Returns the last updated time of the guild
    :param glob: GlobalVars or SQLAlchemy
    :param guild_id: ID of the guild
    :return: int or None
    """
    session = get_session(glob)
    with session.no_autoflush:
        result = session.query(data_classes.Guild).filter_by(id=guild_id).with_entities(data_classes.Guild.last_updated).first()
        return result[0] if result is not None else None
# noinspection DuplicatedCode
def guild_data_key(glob: GlobalVars or SQLAlchemy, guild_id: int) -> str:
    """
    Returns the key of the guild
    :param glob: GlobalVars or SQLAlchemy
    :param guild_id: ID of the guild
    :return: str
    """
    session = get_session(glob)
    with session.no_autoflush:
        result = session.query(data_classes.GuildData).filter_by(id=guild_id).with_entities(data_classes.GuildData.key).first()
        return result[0] if result is not None else None
# noinspection DuplicatedCode
def guild_options_loop(glob: GlobalVars or SQLAlchemy, guild_id: int) -> bool:
    """
    Returns the loop of the guild
    :param glob: GlobalVars or SQLAlchemy
    :param guild_id: ID of the guild
    :return: bool
    """
    session = get_session(glob)
    with session.no_autoflush:
        result = session.query(data_classes.Options).filter_by(id=guild_id).with_entities(data_classes.Options.loop).first()
        return result[0] if result is not None else None
# noinspection DuplicatedCode
def guild_options_buffer(glob: GlobalVars or SQLAlchemy, guild_id: int) -> int:
    """
    Returns the buffer of the guild
    :param glob: GlobalVars or SQLAlchemy
    :param guild_id: ID of the guild
    :return: int
    """
    session = get_session(glob)
    with session.no_autoflush:
        result = session.query(data_classes.Options).filter_by(id=guild_id).with_entities(data_classes.Options.buffer).first()
        return result[0] if result is not None else None
# noinspection DuplicatedCode
def guild_options_response_type(glob: GlobalVars or SQLAlchemy, guild_id: int) -> str:
    """
    Returns the response type of the guild
    :param glob: GlobalVars or SQLAlchemy
    :param guild_id: ID of the guild
    :return: str
    """
    session = get_session(glob)
    with session.no_autoflush:
        result = session.query(data_classes.Options).filter_by(id=guild_id).with_entities(data_classes.Options.response_type).first()
        return result[0] if result is not None else None
# noinspection DuplicatedCode
def guild_options_search_query(glob: GlobalVars or SQLAlchemy, guild_id: int) -> str:
    """
    Returns the search query of the guild
    :param glob: GlobalVars or SQLAlchemy
    :param guild_id: ID of the guild
    :return: str
    """
    session = get_session(glob)
    with session.no_autoflush:
        result = session.query(data_classes.Options).filter_by(id=guild_id).with_entities(data_classes.Options.search_query).first()
        return result[0] if result is not None else None
# noinspection DuplicatedCode
def guild_options_language(glob: GlobalVars or SQLAlchemy, guild_id: int) -> str:
    """
    Returns the language of the guild
    :param glob: GlobalVars or SQLAlchemy
    :param guild_id: ID of the guild
    :return: str
    """
    session = get_session(glob)
    with session.no_autoflush:
        result = session.query(data_classes.Options).filter_by(id=guild_id).with_entities(data_classes.Options.language).first()
        return result[0] if result is not None else None
# noinspection DuplicatedCode
def guild_options_is_radio(glob: GlobalVars or SQLAlchemy, guild_id: int) -> bool:
    """
    Returns whether or not the guild is a radio
    :param glob: GlobalVars or SQLAlchemy
    :param guild_id: ID of the guild
    :return: bool
    """
    session = get_session(glob)
    with session.no_autoflush:
        result = session.query(data_classes.Options).filter_by(id=guild_id).with_entities(data_classes.Options.is_radio).first()
        return result[0] if result is not None else None
# noinspection DuplicatedCode
def guild_options_volume(glob: GlobalVars or SQLAlchemy, guild_id: int) -> float:
    """
    Returns the volume of the guild
    :param glob: GlobalVars or SQLAlchemy
    :param guild_id: ID of the guild
    :return: float
    """
    session = get_session(glob)
    with session.no_autoflush:
        result = session.query(data_classes.Options).filter_by(id=guild_id).with_entities(data_classes.Options.volume).first()
        return result[0] if result is not None else None
# noinspection DuplicatedCode
def guild_options_buttons(glob: GlobalVars or SQLAlchemy, guild_id: int) -> bool:
    """
    Returns the buttons of the guild
    :param glob: GlobalVars or SQLAlchemy
    :param guild_id: ID of the guild
    :return: bool
    """
    session = get_session(glob)
    with session.no_autoflush:
        result = session.query(data_classes.Options).filter_by(id=guild_id).with_entities(data_classes.Options.buttons).first()
        return result[0] if result is not None else None

# Guild Save
def guild_save_count(glob: GlobalVars or SQLAlchemy, guild_id: int) -> int:
    """
    Returns the number of saves in a guild
    :param glob: GlobalVars or SQLAlchemy
    :param guild_id: ID of the guild
    :return: int
    """
    session = get_session(glob)
    with session.no_autoflush:
        return session.query(data_classes.Save).filter_by(guild_id=int(guild_id)).count()
def guild_save_queue_count(glob: GlobalVars or SQLAlchemy, guild_id: int, save_id: int) -> int:
    """
    Returns the number of videos in a save
    :param glob: GlobalVars or SQLAlchemy
    :param guild_id: ID of the guild
    :param save_id: ID of the save
    :return: int
    """
    session = get_session(glob)
    with session.no_autoflush:
        return session.query(video_class.SaveVideo).filter_by(guild_id=int(guild_id), save_id=save_id).count()
def guild_save(glob: GlobalVars or SQLAlchemy, guild_id: int, save_id: int) -> data_classes.Save:
    """
    Returns a save object
    :param glob: GlobalVars or SQLAlchemy
    :param guild_id: ID of the guild
    :param save_id: ID of the save
    :return: Save object
    """
    session = get_session(glob)
    with session.no_autoflush:
        return session.query(data_classes.Save).filter_by(guild_id=int(guild_id), id=int(save_id)).first()
def guild_save_names(glob: GlobalVars or SQLAlchemy, guild_id: int) -> list[str]:
    """
    Returns a list of save names
    :param glob: GlobalVars or SQLAlchemy
    :param guild_id: ID of the guild
    :return: [save_name, ...]
    """
    session = get_session(glob)
    with session.no_autoflush:
        names = []
        for save_object in session.query(data_classes.Save).filter_by(guild_id=int(guild_id)).all():
            names.append(save_object.name)
        return names
def guild_saves(glob: GlobalVars or SQLAlchemy, guild_id: int) -> list[data_classes.Save]:
    """
    Returns a list of save objects
    :param glob: GlobalVars or SQLAlchemy
    :param guild_id: ID of the guild
    :return: [Save object, ...]
    """
    session = get_session(glob)
    with session.no_autoflush:
        return session.query(data_classes.Save).filter_by(guild_id=int(guild_id)).all()

# Guild Commands
def create_guild(glob: GlobalVars or SQLAlchemy, guild_id: int) -> None:
    """
    Creates a guild object
    :param glob: GlobalVars or SQLAlchemy
    :param guild_id: ID of the guild
    :return: Guild object
    """
    session = get_session(glob)
    with session.no_autoflush:
        guild_object = data_classes.Guild(glob, guild_id, {})
        session.add(guild_object)
        session.commit()
def delete_guild(glob: GlobalVars or SQLAlchemy, guild_id: int) -> None:
    """
    Deletes a guild object
    :param glob: GlobalVars or SQLAlchemy
    :param guild_id: ID of the guild
    :return: None
    """
    session = get_session(glob)
    with session.no_autoflush:
        session.query(data_classes.Guild).filter_by(id=guild_id).delete()
        session.query(data_classes.GuildData).filter_by(id=guild_id).delete()
        session.query(data_classes.Options).filter_by(id=guild_id).delete()
        session.query(data_classes.Save).filter_by(id=guild_id).delete()

        session.query(video_class.Queue).filter_by(guild_id=guild_id).delete()
        session.query(video_class.NowPlaying).filter_by(guild_id=guild_id).delete()
        session.query(video_class.History).filter_by(guild_id=guild_id).delete()
        session.query(video_class.SaveVideo).filter_by(guild_id=guild_id).delete()

        session.commit()

# Queue
def guild_queue(glob: GlobalVars or SQLAlchemy, guild_id: int):
    """
    Returns a list of videos in the queue
    :param glob: GlobalVars or SQLAlchemy
    :param guild_id: ID of the guild
    :return: [Queue object, ...]
    """
    session = get_session(glob)
    with session.no_autoflush:
        return session.query(video_class.Queue).filter_by(guild_id=guild_id).all()
def guild_history(glob: GlobalVars or SQLAlchemy, guild_id: int):
    """
    Returns a list of videos in the history
    :param glob: GlobalVars or SQLAlchemy
    :param guild_id: ID of the guild
    :return: [History object, ...]
    """
    session = get_session(glob)
    with session.no_autoflush:
        return session.query(video_class.History).filter_by(guild_id=guild_id).all()

def clear_queue(glob: GlobalVars or SQLAlchemy, guild_id: int) -> int:
    """
    Clears the queue
    :param glob: GlobalVars or SQLAlchemy
    :param guild_id: ID of the guild
    :return: int - number of videos deleted
    """
    session = get_session(glob)
    with session.no_autoflush:
        query = session.query(video_class.Queue).filter_by(guild_id=guild_id)
        query_count = query.count()
        query.delete()
        session.commit()
        return query_count

# Slowed Users
def is_user_slowed(glob: GlobalVars or SQLAlchemy, user_id: int, guild_id: int) -> (bool, int):
    """
    Returns whether or not a user is slowed
    :param glob: GlobalVars or SQLAlchemy
    :param user_id: ID of the user
    :param guild_id: ID of the guild
    :return: (bool, slowed_for)
    """
    session = get_session(glob)
    with session.no_autoflush:
        slowed_user = session.query(data_classes.SlowedUser).filter_by(user_id=user_id, guild_id=guild_id).first()
        if slowed_user is None:
            return False, None
        return True, slowed_user.slowed_for

# Torture
def is_user_tortured(glob: GlobalVars or SQLAlchemy, user_id: int, guild_id: int) -> (bool, int):
    """
    Returns whether or not a user is tortured
    :param glob: GlobalVars or SQLAlchemy
    :param user_id: ID of the user
    :param guild_id: ID of the guild
    :return: (bool, tortured_for)
    """
    session = get_session(glob)
    with session.no_autoflush:
        tortured_user = session.query(data_classes.TorturedUser).filter_by(user_id=user_id, guild_id=guild_id).first()
        if tortured_user is None:
            return False, None
        return True, tortured_user.torture_delay
def delete_tortured_user(glob: GlobalVars or SQLAlchemy, user_id: int, guild_id: int) -> None:
    """
    Deletes a tortured user
    :param glob: GlobalVars or SQLAlchemy
    :param user_id: ID of the user
    :param guild_id: ID of the guild
    :return: None
    """
    session = get_session(glob)
    with session.no_autoflush:
        session.query(data_classes.TorturedUser).filter_by(user_id=user_id, guild_id=guild_id).delete()
        session.commit()
