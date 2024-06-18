import classes.data_classes as data_classes
from classes.typed_dictionaries import DBData



def calculate_time_in_vc(data1: list, data2: list, guild_id: int=0) -> int:
    """
    Calculates the time spent in a voice channel
    data1 = joined VC events
    data2 = left VC events

    returns the time spent in VC

    :param data1: list[time, guild_id, channel_id]
    :param data2: list[time, guild_id, channel_id]
    :param guild_id: int (optional) | 0 = all guilds, guild_id = specific guild

    :return: int - time spent in VC
    """
    if guild_id == 0:
        return sum([x[0] for x in data2]) - sum([x[0] for x in data1])

    return sum([x[0] for x in data2 if x[1] == guild_id]) - sum([x[0] for x in data1 if x[1] == guild_id])

def calculate_time_spent_paused(data4: list, data6: list, guild_id: int=0) -> int:
    """
    Calculates the time spent paused
    data4 = un-paused events
    data6 = paused events

    returns the time spent paused

    :param data4: list[time, guild_id]
    :param data6: list[time, guild_id]
    :param guild_id: int (optional) | 0 = all guilds, guild_id = specific guild

    :return: int - time spent paused
    """
    if guild_id == 0:
        return sum([x[0] for x in data6]) - sum([x[0] for x in data4])
    
    return sum([x[0] for x in data6 if x[1] == guild_id]) - sum([x[0] for x in data4 if x[1] == guild_id])

def calculate_time_spent_playing(data3: list, data5: list, time_paused: int, guild_id: int=0) -> int:
    """
    Calculates the time spent playing
    data3 = started playing events
    data5 = stopped playing events

    returns the time spent playing

    :param data3: list[time, guild_id]
    :param data5: list[time, guild_id]
    :param time_paused: int - time spent paused (either all guilds or specific guild - depending on guild_id)
    :param guild_id: int (optional) | 0 = all guilds, guild_id = specific guild

    :return: int - time spent playing
    """
    if guild_id == 0:
        return sum([x[0] for x in data5]) - sum([x[0] for x in data3]) - time_paused
    
    return sum([x[0] for x in data5 if x[1] == guild_id]) - sum([x[0] for x in data3 if x[1] == guild_id]) - time_paused

def db_data(glob, cutoff: int, guild_id: int=0) -> DBData:
    """
    Collects data from the database - for all guilds
    :param glob: GlobalVars object
    :param cutoff: int - cutoff timestamp
    :param guild_id: int - guild_id
    :return: dict - data
    """

    # TODO: Do this more efficiently
    # TODO: Fix inaccuracy and edge cases
    # Edge cases:
    # start of playing event, then disconnected by user = end of playing is never logged = time spent playing is inaccurate
    # Step through all the vents for a guild and calculate time spent playing, paused, in vc, etc. | BETTER
    # disconnect event - also as stopped playing event and un-paused event

    def gid_filter(db_id: int) -> bool:
        if guild_id == 0:
            return True
        return db_id == guild_id

    return_dict: DBData = {
        'bot_boot_time': 0,
        'count_bot_boot': 0,
        'time_in_vc': 0,
        'time_paused': 0,
        'time_playing': 0,
        'count_guild_joined': 0,
        'count_guild_left': 0,
        'count_command': 0,
        'count_songs_played': 0,
        'count_skipped': 0,
        'count_error': 0
    }

    # DATA 0
    data0 = glob.ses.query(data_classes.TimeLog).filter(data_classes.TimeLog.timestamp > cutoff, data_classes.TimeLog.log_type == 0).with_entities(data_classes.TimeLog.timestamp).all()
    return_dict['bot_boot_time'] = int(data0[-1][0]) if data0 else 0
    return_dict['count_bot_boot'] = len(data0)
    del data0

    # DATA 1 + 2
    data1 = glob.ses.query(data_classes.TimeLog).filter(data_classes.TimeLog.timestamp > cutoff, data_classes.TimeLog.log_type == 1, gid_filter(data_classes.TimeLog.guild_id)).with_entities(data_classes.TimeLog.timestamp, data_classes.TimeLog.guild_id, data_classes.TimeLog.channel_id).all()
    data2 = glob.ses.query(data_classes.TimeLog).filter(data_classes.TimeLog.timestamp > cutoff, data_classes.TimeLog.log_type == 2, gid_filter(data_classes.TimeLog.guild_id)).with_entities(data_classes.TimeLog.timestamp, data_classes.TimeLog.guild_id, data_classes.TimeLog.channel_id).all()
    return_dict['time_in_vc'] = calculate_time_in_vc(data1, data2, guild_id)
    del data1, data2

    # DATA 4 + 6
    data4 = glob.ses.query(data_classes.TimeLog).filter(data_classes.TimeLog.timestamp > cutoff, data_classes.TimeLog.log_type == 4, gid_filter(data_classes.TimeLog.guild_id)).with_entities(data_classes.TimeLog.timestamp, data_classes.TimeLog.guild_id, data_classes.TimeLog.channel_id).all()
    data6 = glob.ses.query(data_classes.TimeLog).filter(data_classes.TimeLog.timestamp > cutoff, data_classes.TimeLog.log_type == 6, gid_filter(data_classes.TimeLog.guild_id)).with_entities(data_classes.TimeLog.timestamp, data_classes.TimeLog.guild_id, data_classes.TimeLog.channel_id).all()
    time_paused = calculate_time_spent_paused(data4, data6, guild_id)
    return_dict['time_paused'] = time_paused
    del data4, data6

    # DATA 3 + 5
    data3 = glob.ses.query(data_classes.TimeLog).filter(data_classes.TimeLog.timestamp > cutoff, data_classes.TimeLog.log_type == 3, gid_filter(data_classes.TimeLog.guild_id)).with_entities(data_classes.TimeLog.timestamp, data_classes.TimeLog.guild_id, data_classes.TimeLog.channel_id).all()
    data5 = glob.ses.query(data_classes.TimeLog).filter(data_classes.TimeLog.timestamp > cutoff, data_classes.TimeLog.log_type == 5, gid_filter(data_classes.TimeLog.guild_id)).with_entities(data_classes.TimeLog.timestamp, data_classes.TimeLog.guild_id, data_classes.TimeLog.channel_id).all()

    return_dict['time_playing'] = calculate_time_spent_playing(data3, data5, time_paused, guild_id)
    del data3, data5

    # DATA 7 + 8
    return_dict['count_guild_joined'] = glob.ses.query(data_classes.TimeLog).filter(data_classes.TimeLog.timestamp > cutoff, data_classes.TimeLog.log_type == 7).count()
    return_dict['count_guild_left'] = glob.ses.query(data_classes.TimeLog).filter(data_classes.TimeLog.timestamp > cutoff, data_classes.TimeLog.log_type == 8).count()

    # DATA 9 + 10 + 11 + 12
    return_dict['count_command'] = glob.ses.query(data_classes.TimeLog).filter(data_classes.TimeLog.timestamp > cutoff, data_classes.TimeLog.log_type == 9, gid_filter(data_classes.TimeLog.guild_id)).count()
    return_dict['count_songs_played'] = glob.ses.query(data_classes.TimeLog).filter(data_classes.TimeLog.timestamp > cutoff, data_classes.TimeLog.log_type == 10, gid_filter(data_classes.TimeLog.guild_id)).count()
    return_dict['count_skipped'] = glob.ses.query(data_classes.TimeLog).filter(data_classes.TimeLog.timestamp > cutoff, data_classes.TimeLog.log_type == 11, gid_filter(data_classes.TimeLog.guild_id)).count()
    return_dict['count_error'] = glob.ses.query(data_classes.TimeLog).filter(data_classes.TimeLog.timestamp > cutoff, data_classes.TimeLog.log_type == 12, gid_filter(data_classes.TimeLog.guild_id)).count()

    return return_dict
