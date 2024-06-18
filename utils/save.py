import config
from classes.data_classes import Guild, DiscordCommand
from classes.typed_dictionaries import DiscordCommandDict

import database.guild as guild
import utils.bot

from utils.log import log
from utils.global_vars import GlobalVars
from typing import List, Literal

from time import time
import aiohttp
import os

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

        guild_object = glob.ses.query(Guild).filter(Guild.id == guild_id).first()
        guild_data_object = guild_object.data
        if guild_data_object is None:
            continue

        if guild_object.last_updated['data'] < int(time()) - 3600:
            guild_data_object.renew(glob)


        # ses.commit()
        # ses.query(GuildData).filter(GuildData.id == guild_id).first().renew()

        # db_g_data = ses.query(GuildData).filter(GuildData.id == guild_id).first()
        # print(db_g_data)

async def push_update(glob, guild_id: int, update_type: List[Literal['queue', 'now', 'history', 'saves', 'options', 'data', 'slowed', 'all']]):
    """
    Updates guild.options.last_updated to current time
    :param glob: GlobalVars
    :param guild_id: int - id of guild
    :param update_type: str - type of update
    :return: None
    """
    if not config.ENABLE_WEB:
        return

    guild_object = glob.ses.query(Guild).filter(Guild.id == guild_id).first()
    last_updated = guild_object.last_updated

    full_address = f"http://{os.environ.get('SOCKET_HOST', '127.0.0.1')}:{os.environ.get('SOCKET_PORT', '5001')}/push?id={guild_id}"

    try:
        async with aiohttp.ClientSession() as session:
            await session.get(full_address)
    except Exception as e:
        log(guild_id, f'Failed to push update to server: {repr(e)}')

    last_updated['queue'] = int(time())
    glob.ses.query(Guild).filter(Guild.id == guild_id).update({'last_updated': last_updated})
    glob.ses.commit()

def update_db_commands(glob: GlobalVars):
    """
    Updates the database with the current commands
    :param glob: GlobalVars
    :return: None
    """
    discord_commands: List[DiscordCommandDict] = utils.bot.get_commands(glob)

    for command in discord_commands:
        db_command = glob.ses.query(DiscordCommand).filter(DiscordCommand.name == command['name']).first()
        if db_command:
            glob.ses.delete(db_command)
        glob.ses.add(DiscordCommand(command['name'], command['description'], command['category'], command['attributes']))
