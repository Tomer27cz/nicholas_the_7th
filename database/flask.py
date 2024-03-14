from utils.convert import struct_to_time

import classes.data_classes as data_classes
import classes.video_class as video_class

from flask_sqlalchemy import SQLAlchemy

def flask_guild(db: SQLAlchemy, guild_id: int) -> data_classes.Guild:
    """
    Returns a guild object
    :param db: SQLAlchemy
    :param guild_id: ID of the guild
    :return: Guild object
    """
    with db.session.no_autoflush:
        return db.session.query(data_classes.Guild).filter_by(id=int(guild_id)).first()

def flask_guilds(db: SQLAlchemy) -> list[data_classes.Guild]:
    """
    Returns a list of guild objects
    :param db: SQLAlchemy
    :return: [Guild object, ...]
    """
    with db.session.no_autoflush:
        return db.session.query(data_classes.Guild).all()

def flask_guilds_last_played(db: SQLAlchemy) -> dict[int, str]:
    """
    Returns a dictionary of guild ids and when was the last time they played a song
    if they never played a song, it will return "None"
    if they are playing a song, it will return "Now"
    :param db: SQLAlchemy
    :return: [Guild object, ...]
    """
    with db.session.no_autoflush:
        guilds_dict = {}
        for guild_object in db.session.query(data_classes.Guild).all():
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

def flask_guild_data(db: SQLAlchemy, guild_id: int) -> data_classes.GuildData:
    """
    Returns a guild data object
    :param db: SQLAlchemy
    :param guild_id: ID of the guild
    :return: GuildData object
    """
    with db.session.no_autoflush:
        return db.session.query(data_classes.GuildData).filter_by(id=int(guild_id)).first()

def flask_guild_exists(db: SQLAlchemy, guild_id: int) -> bool:
    """
    Returns whether or not a guild exists
    :param db: SQLAlchemy
    :param guild_id: ID of the guild
    :return: bool
    """
    with db.session.no_autoflush:
        return db.session.query(data_classes.Guild).filter_by(id=guild_id).first() is not None

def flask_guild_dict(db: SQLAlchemy) -> dict[int, data_classes.Guild]:
    """
    Returns a dictionary of guild objects
    :param db: SQLAlchemy
    :return: {guild_id: Guild object, ...}
    """
    with db.session.no_autoflush:
        _guilds = {}
        for guild_object in db.session.query(data_classes.Guild).all():
            _guilds[guild_object.id] = guild_object
        return _guilds

def flask_guild_ids(db: SQLAlchemy) -> list[int]:
    """
    Returns a list of guild IDs
    :param db: SQLAlchemy
    :return: [guild_id, ...]
    """
    with db.session.no_autoflush:
        _guilds = []
        for guild_object in db.session.query(data_classes.Guild).all():
            _guilds.append(guild_object.id)
        return _guilds

# def flask_guild_bar(db: SQLAlchemy, guild_id: int) -> (int, int):
#     """
#     Returns the bar of the guild
#     :param db: SQLAlchemy
#     :param guild_id: ID of the guild
#     :return: (bar, max_bar)
#     """
#     return guild(glob, guild_id).bar, guild(glob, guild_id).max_bar

# Guild variables
def flask_guild_last_updated(db: SQLAlchemy, guild_id: int) -> dict:
    """
    Returns the last updated of the guild
    :param db: SQLAlchemy
    :param guild_id: ID of the guild
    :return: int
    """
    with db.session.no_autoflush:
        return db.session.query(data_classes.Guild).filter_by(id=guild_id).with_entities(data_classes.Guild.last_updated)[0][0]

def flask_guild_data_key(db: SQLAlchemy, guild_id: int) -> str:
    """
    Returns the key of the guild
    :param db: SQLAlchemy
    :param guild_id: ID of the guild
    :return: str
    """
    with db.session.no_autoflush:
        return db.session.query(data_classes.GuildData).filter_by(id=guild_id).with_entities(data_classes.GuildData.key)[0][0]
def flask_guild_options_loop(db: SQLAlchemy, guild_id: int) -> bool:
    """
    Returns the loop of the guild
    :param db: SQLAlchemy
    :param guild_id: ID of the guild
    :return: bool
    """
    with db.session.no_autoflush:
        return db.session.query(data_classes.Options).filter_by(id=guild_id).with_entities(data_classes.Options.loop)[0][0]
def flask_guild_options_buffer(db: SQLAlchemy, guild_id: int) -> int:
    """
    Returns the buffer of the guild
    :param db: SQLAlchemy
    :param guild_id: ID of the guild
    :return: int
    """
    with db.session.no_autoflush:
        return db.session.query(data_classes.Options).filter_by(id=guild_id).with_entities(data_classes.Options.buffer)[0][0]
def flask_guild_options_response_type(db: SQLAlchemy, guild_id: int) -> str:
    """
    Returns the response type of the guild
    :param db: SQLAlchemy
    :param guild_id: ID of the guild
    :return: str
    """
    with db.session.no_autoflush:
        return db.session.query(data_classes.Options).filter_by(id=guild_id).with_entities(data_classes.Options.response_type)[0][0]
def flask_guild_options_search_query(db: SQLAlchemy, guild_id: int) -> str:
    """
    Returns the search query of the guild
    :param db: SQLAlchemy
    :param guild_id: ID of the guild
    :return: str
    """
    with db.session.no_autoflush:
        return db.session.query(data_classes.Options).filter_by(id=guild_id).with_entities(data_classes.Options.search_query)[0][0]
def flask_guild_options_language(db: SQLAlchemy, guild_id: int) -> str:
    """
    Returns the language of the guild
    :param db: SQLAlchemy
    :param guild_id: ID of the guild
    :return: str
    """
    with db.session.no_autoflush:
        return db.session.query(data_classes.Options).filter_by(id=guild_id).with_entities(data_classes.Options.language)[0][0]
def flask_guild_options_is_radio(db: SQLAlchemy, guild_id: int) -> bool:
    """
    Returns whether or not the guild is a radio
    :param db: SQLAlchemy
    :param guild_id: ID of the guild
    :return: bool
    """
    with db.session.no_autoflush:
        return db.session.query(data_classes.Options).filter_by(id=guild_id).with_entities(data_classes.Options.is_radio)[0][0]
def flask_guild_options_volume(db: SQLAlchemy, guild_id: int) -> float:
    """
    Returns the volume of the guild
    :param db: SQLAlchemy
    :param guild_id: ID of the guild
    :return: float
    """
    with db.session.no_autoflush:
        return db.session.query(data_classes.Options).filter_by(id=guild_id).with_entities(data_classes.Options.volume)[0][0]
def flask_guild_options_buttons(db: SQLAlchemy, guild_id: int) -> bool:
    """
    Returns the buttons of the guild
    :param db: SQLAlchemy
    :param guild_id: ID of the guild
    :return: bool
    """
    with db.session.no_autoflush:
        return db.session.query(data_classes.Options).filter_by(id=guild_id).with_entities(data_classes.Options.buttons)[0][0]
# Guild Save
def flask_guild_save_count(db: SQLAlchemy, guild_id: int) -> int:
    """
    Returns the number of saves in a guild
    :param db: SQLAlchemy
    :param guild_id: ID of the guild
    :return: int
    """
    with db.session.no_autoflush:
        return db.session.query(data_classes.Save).filter_by(guild_id=int(guild_id)).count()
def flask_guild_save_queue_count(db: SQLAlchemy, guild_id: int, save_id: int) -> int:
    """
    Returns the number of videos in a save
    :param db: SQLAlchemy
    :param guild_id: ID of the guild
    :param save_id: ID of the save
    :return: int
    """
    with db.session.no_autoflush:
        return db.session.query(video_class.SaveVideo).filter_by(guild_id=int(guild_id), save_id=save_id).count()
def flask_guild_save(db: SQLAlchemy, guild_id: int, save_id: int) -> data_classes.Save:
    """
    Returns a save object
    :param db: SQLAlchemy
    :param guild_id: ID of the guild
    :param save_id: ID of the save
    :return: Save object
    """
    with db.session.no_autoflush:
        return db.session.query(data_classes.Save).filter_by(guild_id=int(guild_id), id=int(save_id)).first()
def flask_guild_save_names(db: SQLAlchemy, guild_id: int) -> list[str]:
    """
    Returns a list of save names
    :param db: SQLAlchemy
    :param guild_id: ID of the guild
    :return: [save_name, ...]
    """
    with db.session.no_autoflush:
        names = []
        for save_object in db.session.query(data_classes.Save).filter_by(guild_id=int(guild_id)).all():
            names.append(save_object.name)
        return names

# Guild Commands
def flask_create_guild(db: SQLAlchemy, guild_id: int) -> None:
    """
    Creates a guild object
    :param db: SQLAlchemy``
    :param guild_id: ID of the guild
    :return: Guild object
    """
    with db.session.no_autoflush:
        guild_object = data_classes.Guild(None, guild_id, {})
        db.session.add(guild_object)
        db.session.commit()
def flask_delete_guild(db: SQLAlchemy, guild_id: int) -> None:
    """
    Deletes a guild object
    :param db: SQLAlchemy
    :param guild_id: ID of the guild
    :return: None
    """
    with db.session.no_autoflush:
        db.session.query(data_classes.Guild).filter_by(id=guild_id).delete()
        db.session.query(data_classes.GuildData).filter_by(id=guild_id).delete()
        db.session.query(data_classes.Options).filter_by(id=guild_id).delete()
        db.session.query(data_classes.Save).filter_by(id=guild_id).delete()

        db.session.query(video_class.Queue).filter_by(guild_id=guild_id).delete()
        db.session.query(video_class.NowPlaying).filter_by(guild_id=guild_id).delete()
        db.session.query(video_class.History).filter_by(guild_id=guild_id).delete()
        db.session.query(video_class.SaveVideo).filter_by(guild_id=guild_id).delete()

        db.session.commit()

# Queue
def flask_guild_queue(db: SQLAlchemy, guild_id: int):
    """
    Returns a list of videos in the queue
    :param db: SQLAlchemy
    :param guild_id: ID of the guild
    :return: [Queue object, ...]
    """
    with db.session.no_autoflush:
        return db.session.query(video_class.Queue).filter_by(guild_id=guild_id).all()
def flask_guild_history(db: SQLAlchemy, guild_id: int):
    """
    Returns a list of videos in the history
    :param db: SQLAlchemy
    :param guild_id: ID of the guild
    :return: [History object, ...]
    """
    with db.session.no_autoflush:
        return db.session.query(video_class.History).filter_by(guild_id=guild_id).all()

def flask_clear_queue(db: SQLAlchemy, guild_id: int) -> int:
    """
    Clears the queue
    :param db: SQLAlchemy
    :param guild_id: ID of the guild
    :return: int - number of videos deleted
    """
    with db.session.no_autoflush:
        query = db.session.query(video_class.Queue).filter_by(guild_id=guild_id)
        query_count = query.count()
        query.delete()
        db.session.commit()
        return query_count

# Slowed Users
def flask_is_user_slowed(db: SQLAlchemy, user_id: int, guild_id: int) -> (bool, int):
    """
    Returns whether or not a user is slowed
    :param db: SQLAlchemy
    :param user_id: ID of the user
    :param guild_id: ID of the guild
    :return: (bool, slowed_for)
    """
    with db.session.no_autoflush:
        slowed_user = db.session.query(data_classes.SlowedUser).filter_by(user_id=user_id, guild_id=guild_id).first()
        if slowed_user is None:
            return False, None
        return True, slowed_user.slowed_for

# Torture
def flask_is_user_tortured(db: SQLAlchemy, user_id: int, guild_id: int) -> (bool, int):
    """
    Returns whether or not a user is tortured
    :param db: SQLAlchemy
    :param user_id: ID of the user
    :param guild_id: ID of the guild
    :return: (bool, tortured_for)
    """
    with db.session.no_autoflush:
        tortured_user = db.session.query(data_classes.TorturedUser).filter_by(user_id=user_id, guild_id=guild_id).first()
        if tortured_user is None:
            return False, None
        return True, tortured_user.torture_delay
def flask_delete_tortured_user(db: SQLAlchemy, user_id: int, guild_id: int) -> None:
    """
    Deletes a tortured user
    :param db: SQLAlchemy
    :param user_id: ID of the user
    :param guild_id: ID of the guild
    :return: None
    """
    with db.session.no_autoflush:
        db.session.query(data_classes.TorturedUser).filter_by(user_id=user_id, guild_id=guild_id).delete()
        db.session.commit()
