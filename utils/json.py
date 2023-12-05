import classes.video_class
from classes.data_classes import Guild

def guild_to_json(guild_object):
    """
    Converts guild object to json
    :param guild_object: guild object from 'guild' global list
    :return: dict - guild object in python dict
    """
    guild_dict = {}
    search_dict = {}
    queue_dict = {}
    history_dict = {}

    if guild_object.search_list:
        for index, video in enumerate(guild_object.search_list):
            search_dict[index] = video.__dict__

    if guild_object.queue:
        for index, video in enumerate(guild_object.queue):
            queue_dict[index] = video.__dict__

    if guild_object.history:
        for index, video in enumerate(guild_object.history):
            history_dict[index] = video.__dict__

    guild_dict['id'] = guild_object.id
    guild_dict['connected'] = guild_object.connected
    guild_dict['options'] = guild_object.options.__dict__
    guild_dict['data'] = guild_object.data.__dict__
    guild_dict['saves'] = guild_object.saves
    guild_dict['queue'] = queue_dict
    guild_dict['search_list'] = search_dict
    guild_dict['history'] = history_dict
    if guild_object.now_playing:
        guild_dict['now_playing'] = guild_object.now_playing.__dict__
    else:
        guild_dict['now_playing'] = {}

    return guild_dict

def guilds_to_json(guild_dict):
    """
    Converts guilds dict to json
    :param guild_dict: global guilds dict
    :return: dict - guilds dict in python dict
    """
    guilds_dict = {}
    for guild_id, guilds_object in guild_dict.items():
        guilds_dict[int(guild_id)] = guild_to_json(guilds_object)
    return guilds_dict

# ----

def json_to_video(video_dict):
    """
    Converts video dict to VideoClass child object
    :param video_dict: dict - video dict
    :return: VideoClass child object
    """
    if not video_dict:
        return None

    class_type = video_dict['class_type']

    if class_type not in ['Video', 'Radio', 'Local', 'Probe', 'SoundCloud']:
        raise ValueError('Wrong class_type')

    video = classes.video_class.Queue(class_type,
                       created_at=video_dict['created_at'],
                       played_duration=video_dict['played_duration'],
                       url=video_dict['url'],
                       author=video_dict['author'],
                       title=video_dict['title'],
                       picture=video_dict['picture'],
                       duration=video_dict['duration'],
                       channel_name=video_dict['channel_name'],
                       channel_link=video_dict['channel_link'],
                       radio_info=video_dict['radio_info'],
                       local_number=video_dict['local_number'],
                       discord_channel=video_dict['discord_channel'])

    return video

def json_to_guild(guild_dict):
    """
    Converts guild dict to Guild object
    :param guild_dict: dict - guild dict
    :return: Guild object
    """
    guild_object = Guild(guild_dict['id'])
    guild_object.options.__dict__ = guild_dict['options']
    guild_object.data.__dict__ = guild_dict['data']
    guild_object.saves = guild_dict['saves']
    guild_object.queue = [json_to_video(video_dict) for video_dict in guild_dict['queue'].values()]
    guild_object.search_list = [json_to_video(video_dict) for video_dict in guild_dict['search_list'].values()]
    guild_object.history = [json_to_video(video_dict) for video_dict in guild_dict['history'].values()]
    guild_object.now_playing = json_to_video(guild_dict['now_playing'])
    guild_object.connected = guild_dict['connected']

    return guild_object

def json_to_guilds(guilds_dict):
    """
    Converts guilds dict to guilds object
    :param guilds_dict: dict - guilds dict
    :return: global dict - guilds object
    """
    guilds_object = {}
    for guild_id, guild_dict in guilds_dict.items():
        guilds_object[int(guild_id)] = json_to_guild(guild_dict)

    return guilds_object


def load_json_to_database(json_data):
    """
    Loads json data to database
    :param json_data: json data
    """
    from utils.globals import get_session
    from classes.data_classes import Guild

    session = get_session()

    with get_session().no_autoflush:
        for guild_id, guild_dict in json_data.items():
            if guild_id == 0 or guild_id == '0':
                print("Skipping guild_id 0")
                continue
            print(f"Atempting to add {guild_id} to database")
            guild = Guild(guild_id, json_data=guild_dict)
            session.add(guild)

        session.commit()