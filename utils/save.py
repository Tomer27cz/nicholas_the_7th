from classes.data_classes import Guild, GuildData

import database.guild as guild

from utils.log import log
from utils.global_vars import GlobalVars

from time import time

def update(glob: GlobalVars):
    """
    Commits data to the database
    Updates guilds ( update_guilds() )
    :param glob: GlobalVars object
    :return: None
    """
    glob.ses.commit()
    _update_guilds(glob)
    glob.ses.commit()

def _update_guilds(glob: GlobalVars):
    """
    Checks if bot is in a new guild or left a guild
    and renews all guild objects if they have not been renewed in the last hour
    :param glob: GlobalVars object
    :return: None
    """

    glob.ses.commit()
    db_guilds = [_[0] for _ in glob.ses.query(Guild.id).with_entities(Guild.id).all()]
    bot_guilds = [guild_object.id for guild_object in glob.bot.guilds]

    for bot_guild_id in bot_guilds:
        if bot_guild_id not in db_guilds:
            bot_guild_object = glob.bot.get_guild(bot_guild_id)
            glob.ses.add(Guild(glob, bot_guild_id, {}))
            log(None, f'Discovered a New guild: {bot_guild_id} = {bot_guild_object.name} -> Added to Database')

    for guild_id in db_guilds:
        guild_object = guild.guild(glob, guild_id)

        if guild_id not in bot_guilds:
            if guild_object.connected:
                guild_object.connected = False
                log(None, f'Guild left: {guild_id} = {guild_object.data.name} -> Marked as disconnected')

        if guild_id in bot_guilds:
            if not guild_object.connected:
                log(None, f'Marked guild as connected: {guild_object.id} = {guild_object.data.name}')
                guild_object.connected = True

        guild_data_object = glob.ses.query(GuildData).filter(GuildData.id == guild_id).first()
        if guild_data_object is None:
            continue

        if not isinstance(guild_data_object.last_updated, int):
            guild_data_object.renew(glob)

        if guild_data_object.last_updated < int(time()) - 3600:
            guild_data_object.renew(glob)


        # ses.commit()
        # ses.query(GuildData).filter(GuildData.id == guild_id).first().renew()

        # db_g_data = ses.query(GuildData).filter(GuildData.id == guild_id).first()
        # print(db_g_data)

def push_update(glob: GlobalVars, guild_id: int):
    glob.ses.commit()
    guild.guild(glob, guild_id).options.last_updated = int(time())
