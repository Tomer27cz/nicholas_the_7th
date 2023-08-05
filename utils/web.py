from ipc.flaskapp import send_arg
from config import PARENT_DIR
import utils.files
import classes.data_classes
import os

def execute_function(function_name: str, web_data: classes.data_classes.WebData, **kwargs) -> classes.data_classes.ReturnData:
    # create argument dictionary
    arg_dict = {
        'type': 'function',
        'function_name': function_name,
        'web_data': web_data,
        'args': kwargs
    }
    response = send_arg(arg_dict)

    if response is None:
        return classes.data_classes.ReturnData(False, 'An unexpected error occurred')

    return response

def get_guild(guild_id: int):
    """
    Get a guild from the database
    :param guild_id: guild id
    :return: guild object
    """
    # create argument dictionary
    arg_dict = {
        'type': 'get_data',
        'data_type': 'guild',
        'guild_id': guild_id
    }
    # send argument dictionary
    return send_arg(arg_dict)

def get_guilds():
    """
    Get the guilds list from database
    :return: list - list of guild objects
    """
    arg_dict = {
        'type': 'get_data',
        'data_type': 'guilds'
    }
    # send argument dictionary
    import __main__
    guild = send_arg(arg_dict)
    __main__.guild = guild
    return guild

def get_bot_guilds():
    """
    Get the guilds list from bot instance
    :return: list - list of guild objects
    """
    arg_dict = {
        'type': 'get_data',
        'data_type': 'bot_guilds'
    }
    # send argument dictionary
    bot_guilds = send_arg(arg_dict)
    return bot_guilds

# guild specific data
def get_guild_channels(guild_id: int):
    """
    Get the guild channels list from database
    :param guild_id: guild id
    :return: list - list of channel objects
    """
    # create argument dictionary
    arg_dict = {
        'type': 'get_data',
        'data_type': 'guild_channels',
        'guild_id': guild_id
    }
    # send argument dictionary
    return send_arg(arg_dict)

def get_guild_text_channels(guild_id: int):
    """
    Get the guild text channels list from database
    :param guild_id: guild id
    :return: list - list of channel objects
    """
    # create argument dictionary
    arg_dict = {
        'type': 'get_data',
        'data_type': 'guild_text_channels',
        'guild_id': guild_id
    }
    # send argument dictionary
    response = send_arg(arg_dict)
    if response is None:
        return utils.files.get_guild_text_channels_file(guild_id)
    return response

def get_guild_members(guild_id: int):
    """
    Get the members of a guild
    :param guild_id: guild id
    :return: list - list of members
    """
    # create argument dictionary
    arg_dict = {
        'type': 'get_data',
        'data_type': 'guild_members',
        'guild_id': guild_id
    }
    # send argument dictionary
    return send_arg(arg_dict)

def get_guild_roles(guild_id: int):
    """
    Get the roles of a guild
    :param guild_id: guild id
    :return: list - list of roles
    """
    # create argument dictionary
    arg_dict = {
        'type': 'get_data',
        'data_type': 'guild_roles',
        'guild_id': guild_id
    }
    # send argument dictionary
    return send_arg(arg_dict)

def get_guild_invites(guild_id: int):
    """
    Get the invites of a guild
    :param guild_id: guild id
    :return: list - list of invites
    """
    # create argument dictionary
    arg_dict = {
        'type': 'get_data',
        'data_type': 'guild_invites',
        'guild_id': guild_id
    }
    # send argument dictionary
    return send_arg(arg_dict)

def get_update(guild_id: int):
    """
    Get update variable state from the database
    :param guild_id: guild id
    :return: bool - update variable state
    """
    # create argument dictionary
    arg_dict = {
        'type': 'get_data',
        'data_type': 'update',
        'guild_id': guild_id
    }
    # send argument dictionary
    return send_arg(arg_dict)

def get_language(guild_id: int):
    """
    Get language from the database
    :param guild_id: guild id
    :return: language
    """
    # create argument dictionary
    arg_dict = {
        'type': 'get_data',
        'data_type': 'language',
        'guild_id': guild_id
    }
    # send argument dictionary
    return send_arg(arg_dict)

def get_channel_content(guild_id: int, channel_id: int):
    try:
        path = f'{PARENT_DIR}db/guilds/{guild_id}/{channel_id}'
        if not os.path.exists(path):
            return None

        files = os.listdir(path)
        if len(files) == 0:
            return None

        path = f'{path}/{files[0]}'
        with open(path, 'r', encoding='utf-8') as f:
            return f.read()
    except (FileNotFoundError, IndexError, PermissionError):
        return None

def get_fast_channel_content(channel_id: int):
    """
    Get the content of a channel (fast nad up-to-date)
    :param channel_id: channel id
    :return: content
    """
    # create argument dictionary
    arg_dict = {
        'type': 'get_data',
        'data_type': 'channel_transcript',
        'channel_id': channel_id
    }
    # send argument dictionary
    return send_arg(arg_dict)

def get_renew(guild_id: int, queue_type: str, index: int):
    """
    Get a renew from the database
    :param guild_id: guild id
    :param queue_type: queue or now_playing
    :param index: index in queue
    :return: renew object
    """
    # create argument dictionary
    arg_dict = {
        'type': 'get_data',
        'data_type': 'renew',
        'guild_id': guild_id,
        'queue_type': queue_type,
        'index': index
    }
    # send argument dictionary
    return send_arg(arg_dict)

# user specific data
def get_username(user_id: int):
    """
    Get a user from the database
    :param user_id: user id
    :return: user object
    """
    # create argument dictionary
    arg_dict = {
        'type': 'get_data',
        'data_type': 'user_name',
        'user_id': user_id
    }
    # send argument dictionary
    return send_arg(arg_dict)

def get_user_data(user_id: int):
    """
    Get a user from the database
    :param user_id: user id
    :return: user object
    """
    # create argument dictionary
    arg_dict = {
        'type': 'get_data',
        'data_type': 'user_data',
        'user_id': user_id
    }
    # send argument dictionary
    return send_arg(arg_dict)
