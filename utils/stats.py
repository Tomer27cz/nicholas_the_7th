import classes.data_classes as data_classes
from classes.typed_dictionaries import DBData

def db_data(glob, cutoff: int, guild_id: int=0) -> DBData:
    """
    Collects data from the database - for all guilds
    :param glob: GlobalVars object
    :param cutoff: int - cutoff timestamp
    :param guild_id: int - guild_id
    :return: dict - data
    """

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
        'count_error': 0,
        'count_voice_sessions': 0,
    }

    # DATA 0
    data0 = glob.ses.query(data_classes.TimeLog).filter(data_classes.TimeLog.timestamp > cutoff, data_classes.TimeLog.log_type == 0).with_entities(data_classes.TimeLog.timestamp).all()
    return_dict['bot_boot_time'] = int(data0[-1][0]) if data0 else 0
    return_dict['count_bot_boot'] = len(data0)
    del data0

    # TIME IN VC
    voice_data = glob.ses.query(data_classes.VoiceLogDB).filter(data_classes.VoiceLogDB.connected_at > cutoff, gid_filter(data_classes.VoiceLogDB.guild_id)).with_entities(data_classes.VoiceLogDB.time_in_vc, data_classes.VoiceLogDB.time_playing, data_classes.VoiceLogDB.time_paused).all()
    return_dict['time_in_vc'] = sum([x[0] for x in voice_data])
    return_dict['time_playing'] = sum([x[1] for x in voice_data])
    return_dict['time_paused'] = sum([x[2] for x in voice_data])
    return_dict['count_voice_sessions'] = len(voice_data)
    del voice_data

    # DATA 7 + 8
    return_dict['count_guild_joined'] = glob.ses.query(data_classes.TimeLog).filter(data_classes.TimeLog.timestamp > cutoff, data_classes.TimeLog.log_type == 7).count()
    return_dict['count_guild_left'] = glob.ses.query(data_classes.TimeLog).filter(data_classes.TimeLog.timestamp > cutoff, data_classes.TimeLog.log_type == 8).count()

    # DATA 9 + 10 + 11 + 12
    return_dict['count_command'] = glob.ses.query(data_classes.TimeLog).filter(data_classes.TimeLog.timestamp > cutoff, data_classes.TimeLog.log_type == 9, gid_filter(data_classes.TimeLog.guild_id)).count()
    return_dict['count_songs_played'] = glob.ses.query(data_classes.TimeLog).filter(data_classes.TimeLog.timestamp > cutoff, data_classes.TimeLog.log_type == 10, gid_filter(data_classes.TimeLog.guild_id)).count()
    return_dict['count_skipped'] = glob.ses.query(data_classes.TimeLog).filter(data_classes.TimeLog.timestamp > cutoff, data_classes.TimeLog.log_type == 11, gid_filter(data_classes.TimeLog.guild_id)).count()
    return_dict['count_error'] = glob.ses.query(data_classes.TimeLog).filter(data_classes.TimeLog.timestamp > cutoff, data_classes.TimeLog.log_type == 12, gid_filter(data_classes.TimeLog.guild_id)).count()

    return return_dict
