from youtubesearchpython.__future__ import CustomSearch, SearchMode, Search

from classes.video_class import Queue
from classes.typed_dictionaries import TuneInSearch, RadioGardenSearch, WebSearchResult

from utils.global_vars import GlobalVars, radio_dict, sound_effects
from utils.url import get_url_type
from utils.convert import czech_to_ascii
from utils.radio import search_tunein

from typing import List, Literal
import discord
import aiohttp
import asyncio
import urllib.parse

from config import VLC_LOGO

# ------------------------------------------------------ PICTURE -------------------------------------------------------

def get_picture(source: str) -> str:
    """
    Get the picture of the source
    :param source: Source of the picture
    :return: str
    """
    if source in ['YouTube Playlist', 'YouTube Playlist Video', 'YouTube Video']:
        return 'https://www.youtube.com/yts/img/favicon_32-vflOogEID.png'

    if source in ['Spotify Playlist', 'Spotify Album', 'Spotify Track', 'Spotify URL']:
        return 'https://www.scdn.co/i/_global/favicon.png'

    if source in ['SoundCloud URL']:
        return 'https://soundcloud.com/favicon.ico'

    if source in ['RadioGarden']:
        return 'https://radio.garden/icons/favicon.png'

    if source in ['RadioTuneIn']:
        return 'https://tunein.com/favicon.ico'

    if source in ['RadioCz']:
        return 'https://www.radia.cz/favicon.ico'

    if source in ['Local']:
        return VLC_LOGO

    return ''

# ------------------------------------------------------ QUERY ---------------------------------------------------------

async def youtube_autocomplete_def(ctx: discord.Interaction or None,
                                   query: str,
                                   limit: int=5,
                                   raw: bool=False,
                                   search_type: str='videos'
                                   ):
    """
    Autocomplete for a YouTube query
    :param ctx: Interaction
    :param query: String to be autocompleted
    :param limit: Limit of the results
    :param raw: Return the raw data (not as a discord.app_commands.Choice)
    :param search_type: Type of search (videos, playlists, livestreams, all)
    :return: List[discord.app_commands.Choice]
    """
    if not query:
        return []

    if search_type == 'videos':
        search = CustomSearch(query, searchPreferences=SearchMode.videos)
    elif search_type == 'playlists':
        search = CustomSearch(query, searchPreferences=SearchMode.playlists)
    elif search_type == 'livestreams':
        search = CustomSearch(query, searchPreferences=SearchMode.livestreams)
    else:
        search = Search(query)

    custom_search_result = await search.next()
    if custom_search_result['result']:
        _return = []

        for result in custom_search_result['result']:
            if result['type'] == 'channel':
                continue

            if raw:
                thumbnail = result['thumbnails'][0]['url'] if result['thumbnails'] else f'https://img.youtube.com/vi/{result["id"]}/default.jpg'
                _return.append({'title': result['title'], 'value': result['link'], 'source': 'YouTube', 'picture': thumbnail})
                continue

            _return.append(discord.app_commands.Choice(name=f"YouTube: {result['title']}", value=result['link']))

        return _return[:limit]
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
    audio_results: list[TuneInSearch] = [result for result in tunein_result if result.get('type', None) == 'audio']

    if tunein_status:
        if raw:
            return [{'title': station['text'], 'value': f"_tunein:{station['guide_id']}", 'source': 'TuneIn', 'picture': station['image']} for station in audio_results]

        _return = [discord.app_commands.Choice(name=f"TuneIn: {station['text']}", value=f"_tunein:{station['guide_id']}") for station in audio_results]
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
                                 limit: int=5,
                                 youtube_search_type: str='videos'
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
    :param youtube_search_type: Type of search for YouTube
    :return: List[discord.app_commands.Choice]
    """
    if not query:
        return []

    url_type = get_url_type(query)
    if url_type[0] not in ["String", "String with URL"]:
        if raw:
            return [{'title': f"{url_type[0]}: {url_type[1]}", 'value': url_type[1], 'source': f'{url_type[0]}', 'picture': get_picture(f'{url_type[0]}')}]

        return [discord.app_commands.Choice(name=f"{url_type[0]}: {url_type[1]}", value=url_type[1])]

    tasks = []
    if include_youtube:
        tasks.append(youtube_autocomplete_def(ctx, query, raw=raw, limit=limit, search_type=youtube_search_type))

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








