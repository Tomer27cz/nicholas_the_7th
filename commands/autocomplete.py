from youtubesearchpython.__future__ import VideosSearch

from classes.video_class import Queue
from classes.typed_dictionaries import TuneInSearch, RadioGardenSearch, WebSearchResult

from utils.global_vars import GlobalVars, radio_dict, sound_effects
from utils.url import get_url_type
from utils.convert import czech_to_ascii
from utils.radio import search_tunein

from typing import List
import discord
import aiohttp
import asyncio
import urllib.parse

from config import VLC_LOGO

# ------------------------------------------------------ QUERY ---------------------------------------------------------

async def youtube_autocomplete_def(ctx: discord.Interaction or None, query: str, limit: int=5, raw: bool=False) -> List[discord.app_commands.Choice] or List[WebSearchResult]:
    """
    Autocomplete for a YouTube query
    :param ctx: Interaction
    :param query: String to be autocompleted
    :param limit: Limit of the results
    :param raw: Return the raw data (not as a discord.app_commands.Choice)
    :return: List[discord.app_commands.Choice]
    """
    if not query:
        return []

    custom_search = VideosSearch(query, limit=limit)
    custom_search_result = await custom_search.next()

    if custom_search_result['result']:
        if raw:
            return [{'title': song['title'], 'value': song['link'], 'source': 'YouTube', 'picture': f'https://img.youtube.com/vi/{song["id"]}/default.jpg'} for song in custom_search_result['result']]

        return [discord.app_commands.Choice(name=f"YouTube: {song['title']}", value=song['link']) for song in custom_search_result['result']]

    return []
async def tunein_autocomplete_def(ctx: discord.Interaction or None, query: str, limit: int=5, raw: bool=False) -> List[discord.app_commands.Choice] or List[WebSearchResult]:
    """
    Autocomplete for a TuneIn query
    :param ctx: Interaction
    :param query: String to be autocompleted
    :param limit: Limit of the results
    :param raw: Return the raw data (not as a discord.app_commands.Choice)
    :return: List[discord.app_commands.Choice]
    """
    if not query:
        return []

    resp = await search_tunein(query, limit=5)
    tunein_status = resp[0]
    tunein_result: list[TuneInSearch] = resp[1]
    if tunein_status:
        if raw:
            return [{'title': station['text'], 'value': f"_tunein:{station['guide_id']}", 'source': 'TuneIn', 'picture': station['image']} for station in tunein_result]

        _return = [discord.app_commands.Choice(name=f"TuneIn: {station['text']}", value=f"_tunein:{station['guide_id']}") for station in tunein_result]
        return _return[:limit]

    return []
async def garden_autocomplete_def(ctx: discord.Interaction or None, query: str, limit: int=5, raw: bool=False) -> List[discord.app_commands.Choice] or List[WebSearchResult]:
    """
    Autocomplete for a RadioGarden query
    :param ctx: Interaction
    :param query: String to be autocompleted
    :param limit: Limit of the results
    :param raw: Return the raw data (not as a discord.app_commands.Choice)
    :return: List[discord.app_commands.Choice]
    """
    if not query:
        return []

    url = f'https://radio.garden/api/search?q={urllib.parse.quote_plus(query)}'
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            data: RadioGardenSearch = await response.json()

    results = data['hits']['hits']

    if results:
        results = [station for station in results if station['_source']['type'] == 'channel']

        if raw:
            return [{'title': station['_source']['title'], 'value': f"https://radio.garden{station['_source']['url']}", 'source': 'RadioGarden', 'picture': 'https://radio.garden/icons/favicon.png'} for station in results]

        _return = [discord.app_commands.Choice(name=f"RadioGarden: {station['_source']['title']}", value=f"https://radio.garden{station['_source']['url']}") for station in results]
        return _return[:limit]

    return []

async def query_autocomplete_def(ctx: discord.Interaction or None, query: str,
                                 include_youtube: bool=False,
                                 include_tunein: bool=False,
                                 include_radio: bool=False,
                                 include_garden: bool=False,
                                 include_local: bool=False,
                                 raw: bool=False,
                                 limit: int=5
                                 ) -> List[discord.app_commands.Choice] or List[WebSearchResult]:
    """
    Autocompletion for a query (play, nextup, queue, search ...)
    :param ctx: Interaction
    :param query: String to be autocompleted
    :param include_youtube: Include YouTube in the results
    :param include_tunein: Include TuneIn in the results
    :param include_radio: Include RadiaCz in the results
    :param include_garden: Include RadioGarden in the results
    :param include_local: Include local files in the results
    :param raw: Return the raw data (not as a discord.app_commands.Choice)
    :param limit: Limit of the results per source
    :return: List[discord.app_commands.Choice]
    """
    if not query:
        return []

    url_type = get_url_type(query)
    if url_type[0] not in ["String", "String with URL"]:
        if raw:
            return [{'title': f"{url_type[0]}: {url_type[1]}", 'value': url_type[1], 'source': f'{url_type[0]}', 'picture': None}]

        return [discord.app_commands.Choice(name=f"{url_type[0]}: {url_type[1]}", value=url_type[1])]

    tasks = []
    if include_youtube:
        tasks.append(youtube_autocomplete_def(ctx, query, raw=raw, limit=limit))

    if include_tunein:
        tasks.append(tunein_autocomplete_def(ctx, query, raw=raw, limit=limit))

    if include_radio:
        tasks.append(radio_autocomplete_def(ctx, query, raw=raw, limit=limit))

    if include_garden:
        tasks.append(garden_autocomplete_def(ctx, query, raw=raw, limit=limit))

    if include_local:
        tasks.append(local_autocomplete_def(ctx, query, raw=raw, limit=limit))

    async with aiohttp.ClientSession() as _session:
        _results = await asyncio.gather(*tasks, return_exceptions=False)

    data = []
    for _item in _results:
        data += _item

    return data

# ------------------------------------------------------- LOCAL --------------------------------------------------------

async def help_autocomplete_def(ctx: discord.Interaction or None, query: str, glob: GlobalVars) -> List[discord.app_commands.Choice]:
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

async def radio_autocomplete_def(ctx: discord.Interaction or None, query: str, limit: int=5, raw: bool=False) -> List[discord.app_commands.Choice] or List[WebSearchResult]:
    """
    Autocomplete for the radio stations
    :param ctx: Interaction
    :param query: String to be autocompleted
    :param limit: Limit of the results
    :param raw: Return the raw data (not as a discord.app_commands.Choice)
    :return: List[discord.app_commands.Choice]
    """
    if not query and not raw:
        return [discord.app_commands.Choice(name=f"RadiaCz: {station['id']} - {station['name']}", value=f'_radia_cz:{station['id']}') for station in list(radio_dict.values())[:-1]][:limit]

    if query.isdigit():
        stations = [station for station in list(radio_dict.values())[:-1] if query in str(station['id'])]
        if raw:
            return [{'title': f"{station['name']}", 'value': f'_radia_cz:{station['id']}', 'source': 'RadiaCz', 'picture': station['logo']} for station in stations][:limit]

        return [discord.app_commands.Choice(name=f"RadiaCz: {station['id']} - {station['name']}", value=f'_radia_cz:{station['id']}') for station in stations][:limit]

    radios = []
    for station in list(radio_dict.values())[:-1]:
        if czech_to_ascii(query.lower()) in czech_to_ascii(station['name'].lower()):
            if raw:
                radios.append({'title': f"{station['name']}", 'value': f'_radia_cz:{station['id']}', 'source': 'RadiaCz', 'picture': station['logo']})
                continue

            radios.append(discord.app_commands.Choice(name=f"RadiaCz: {station['id']} - {station['name']}", value=f'_radia_cz:{station['id']}'))

    return radios[:limit]

async def local_autocomplete_def(ctx: discord.Interaction or None, query: str, limit: int=5, raw: bool=False) -> List[discord.app_commands.Choice] or List[WebSearchResult]:
    """
    Autocomplete for the sound effects
    :param ctx: Interaction
    :param query: String to be autocompleted
    :param limit: Limit of the results
    :param raw: Return the raw data (not as a discord.app_commands.Choice)
    :return: List[discord.app_commands.Choice]
    """
    if not query and not raw:
        return [discord.app_commands.Choice(name=f"Local: {index+1} - {sound}", value=f'_local:{index+1}') for index, sound in enumerate(sound_effects[:limit])]

    if query.isdigit():
        if raw:
            return [{'title': f"{index+1} - {sound}", 'value': f'_local:{index+1}', 'source': 'Local', 'picture': VLC_LOGO} for index, sound in enumerate(sound_effects) if query in str(index+1)][:limit]

        return [discord.app_commands.Choice(name=f"Local: {index+1} - {sound}", value=f'_local:{index+1}') for index, sound in enumerate(sound_effects) if query in str(index+1)][:limit]

    if raw:
        return [{'title': f"{index+1} - {sound}", 'value': f'_local:{index+1}', 'source': 'Local', 'picture': VLC_LOGO} for index, sound in enumerate(sound_effects) if query.lower() in sound.lower()][:limit]

    return [discord.app_commands.Choice(name=f"Local: {index+1} - {sound}", value=f'_local:{index+1}') for index, sound in enumerate(sound_effects) if query.lower() in sound.lower()][:limit]








