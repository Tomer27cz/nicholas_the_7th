from utils.log import log
from utils.globals import get_bot, get_session
import database.guild as guild

from classes.data_classes import Guild, GuildData
from time import time

def save_json():
    """
    Commits data to the database
    Updates guilds ( update_guilds() )
    :return: None
    """
    get_session().commit()
    update_guilds()
    get_session().commit()

def update_guilds():
    """
    Checks if bot is in a new guild or left a guild
    and renews all guild objects
    :return: None
    """
    get_session().commit()
    db_guilds = [db_guild_object.id for db_guild_object in get_session().query(Guild).all()]
    bot_guilds = [guild_object.id for guild_object in get_bot().guilds]

    for bot_guild_id in bot_guilds:
        if bot_guild_id not in db_guilds:
            bot_guild_object = get_bot().get_guild(bot_guild_id)
            get_session().add(Guild(bot_guild_id))
            log(None, f'Discovered a New guild: {bot_guild_id} = {bot_guild_object.name} -> Added to Database')

    for guild_id in db_guilds:
        guild_object = guild.guild(guild_id)

        if guild_id not in bot_guilds:
            if guild_object.connected:
                guild_object.connected = False
                log(None, f'Guild left: {guild_id} = {guild_object.data.name} -> Marked as disconnected')

        if guild_id in bot_guilds:
            if not guild_object.connected:
                log(None, f'Marked guild as connected: {guild_object.id} = {guild_object.data.name}')
                guild_object.connected = True

        # get_session().commit()
        # get_session().query(GuildData).filter(GuildData.id == guild_id).first().renew()

        # db_g_data = get_session().query(GuildData).filter(GuildData.id == guild_id).first()
        # print(db_g_data)


def push_update(guild_id: int):
    get_session().commit()
    guild.guild(guild_id).options.last_updated = int(time())
