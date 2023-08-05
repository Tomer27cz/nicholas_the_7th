from utils.json import guilds_to_json
from utils.log import log
from utils.globals import get_bot, get_guild_dict

from classes.data_classes import Guild

import json
from time import time

def save_json():
    """
    Updates guild objects and
    Saves guild objects to guilds.json
    :return: None
    """
    guild = get_guild_dict()
    update_guilds()

    with open('db/guilds.json', 'w', encoding='utf-8') as f:
        json.dump(guilds_to_json(guild), f, indent=4)

def update_guilds():
    """
    Checks if bot is in a new guild or left a guild
    and renews all guild objects
    :return: None
    """
    bot = get_bot()
    guild = get_guild_dict()

    bot_guilds = [guild_object.id for guild_object in bot.guilds]
    guilds_json = [int(guild_id) for guild_id in guild.keys()]

    for bot_guild_id in bot_guilds:
        if bot_guild_id not in guilds_json:
            bot_guild_object = bot.get_guild(bot_guild_id)
            guild[bot_guild_id] = Guild(bot_guild_id)
            log(None, f'Discovered a New guild: {bot_guild_id} = {bot_guild_object.name} -> Added to guilds.json')

    for guild_object in guild.values():
        if guild_object.id not in bot_guilds:
            if guild_object.connected:
                log(None, f'Guild left: {guild_object.id} = {guild_object.data.name} -> Marked as disconnected')
                guild[guild_object.id].connected = False

        else:
            if not guild_object.connected:
                log(None, f'Marked guild as connected: {guild_object.id} = {guild_object.data.name}')
                guild[guild_object.id].connected = True

        guild_object.renew()

def push_update(guild_id: int):
    guild = get_guild_dict()
    guild[guild_id].options.last_updated = int(time())
