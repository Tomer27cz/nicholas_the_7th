from youtubesearchpython.__future__ import VideosSearch

from classes.video_class import Queue

from utils.global_vars import GlobalVars, radio_dict
from utils.url import get_url_type
from utils.convert import czech_to_ascii

from typing import List
import discord

async def query_autocomplete_def(ctx: discord.Interaction, query: str) -> List[discord.app_commands.Choice]:
    """
    Autocompletion for a query (play, nextup, queue, search ...)
    :param ctx: Interaction
    :param query: String to be autocompleted
    :return: List[discord.app_commands.Choice]
    """
    if not query:
        return []

    url_type = get_url_type(query)
    if url_type[0] == "String":
        custom_search = VideosSearch(query, limit=5)
        custom_search_result = await custom_search.next()

        if not custom_search_result['result']:
            return []

        # noinspection PyTypeChecker
        return [discord.app_commands.Choice(name=custom_search_result['result'][i]['title'], value=custom_search_result['result'][i]['link']) for i in range(5)]

    return []


async def song_autocomplete_def(ctx: discord.Interaction, query: str, glob: GlobalVars) -> List[discord.app_commands.Choice]:
    """
    Autocomplete for the songs in the queue
    :param ctx: Interaction
    :param query: String to be autocompleted
    :param glob: GlobalVars
    :return: str
    """
    song_data = [_ for _ in glob.ses.query(Queue).filter(Queue.guild_id == ctx.guild.id).with_entities(Queue.title, Queue.position).all()]

    if not query:
        if len(song_data) > 25:
            return [discord.app_commands.Choice(name=f"{song[1]} - {song[0]}", value=str(song[1])) for song in song_data[:25]]
        return [discord.app_commands.Choice(name=f"{song[1]} - {song[0]}", value=str(song[1])) for song in song_data]

    if query.isdigit():
        return [discord.app_commands.Choice(name=f"{song[1]} - {song[0]}", value=str(song[1])) for song in song_data if query in str(song[1])]

    return [discord.app_commands.Choice(name=f"{song[1]} - {song[0]}", value=str(song[1])) for song in song_data if query.lower() in song[0].lower()]


async def radio_autocomplete_def(ctx: discord.Interaction, query: str) -> List[discord.app_commands.Choice]:
    """
    Autocomplete for the radio stations
    :param ctx: Interaction
    :param query: String to be autocompleted
    :return: List[discord.app_commands.Choice]
    """
    if not query:
        return [discord.app_commands.Choice(name=radio, value=radio) for radio in ['Rádio BLANÍK', 'Rádio BLANÍK CZ', 'Evropa 2', 'Fajn Radio', 'Hitrádio PopRock', 'Český rozhlas Pardubice', 'Radio Beat', 'Country Radio', 'Radio Kiss', 'Český rozhlas Vltava', 'Hitrádio Černá Hora']]

    if query.isdigit():
        return [discord.app_commands.Choice(name=f"{station['id']} - {station['name']}", value=station['name']) for station in radio_dict.values() if query in str(station['id'])]

    data = []
    for station in radio_dict.values():
        if czech_to_ascii(query.lower()) in czech_to_ascii(station['name'].lower()):
            data.append(discord.app_commands.Choice(name=f"{station['id']} - {station['name']}", value=station['name']))

    if len(data) > 25:
        return data[:25]

    return data


async def help_autocomplete_def(ctx: discord.Interaction, query: str, glob: GlobalVars) -> List[discord.app_commands.Choice]:
    """
    Autocomplete for the help command
    :param ctx: Interaction
    :param query: String to be autocompleted
    :param glob: GlobalVars
    :return: List[discord.app_commands.Choice]
    """

    list_of_commands = [command.name for command in glob.bot.commands if not command.hidden]
    list_of_commands.sort()

    if not query:
        return [discord.app_commands.Choice(name=command, value=command) for command in list_of_commands[:25]]

    data = []
    for command in list_of_commands:
        if query.lower() in command.lower():
            data.append(discord.app_commands.Choice(name=command, value=command))

    if len(data) > 25:
        return data[:25]

    return data








