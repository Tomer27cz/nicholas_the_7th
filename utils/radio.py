from classes.typed_dictionaries import RadioGardenChannel, RadioGardenPlace, RadioGardenInfo, RadiosJSON

from utils.global_vars import radio_dict
from utils.log import log

import aiohttp
import urllib.parse
import xmltodict
import time
import json
import asyncio

# -------------------------------------------- Radio Garden Info -------------------------------------------------------

async def get_radio_garden_info(url: str) -> (bool, RadioGardenInfo) or (bool, dict):
    """
    Returns the radio.garden radio info from the url
    :param url: str - radio.garden url
    :return: (bool, RadioGardenInfo) or (bool, str) - (successful, radio info)
    """
    async def get_radio_garden_radio_code(_url: str) -> (bool, str, RadioGardenChannel, str) or (bool, str, RadioGardenPlace, str):
        """
        Returns the first radio code from the radio.garden url
        if url is radio, returns the code
        if url is place, returns the first radio code from the place
        :param _url: str - radio.garden url
        :return: (bool, str, RadioGardenChannel) or (bool, str, RadioGardenPlace) - (successful, radio url, radio info)
        """
        _code = _url.split('/')[-1]

        # check if url is radio
        async with aiohttp.ClientSession() as _session:
            async with _session.get('https://radio.garden/api/ara/content/channel/' + _code) as _response:
                if _response.status == 200:
                    _json_response: RadioGardenChannel = await _response.json()
                    return True, _json_response['data']['url'], _json_response, 'radio'

        # check if url is place
        async with aiohttp.ClientSession() as _session:
            async with _session.get('https://radio.garden/api/ara/content/secure/page/' + _code) as _response:
                if _response.status == 200:
                    _json_response: RadioGardenPlace = await _response.json()
                    return True, _json_response['data']['content'][0]['items'][0]['href'], _json_response, 'place'

        return False, 'Error', {}, 'Error'

    success, radio_url, info, info_type = await get_radio_garden_radio_code(url)
    if not success:
        return success, info

    if info_type == 'place':
        success, radio_url, info, info_type = await get_radio_garden_radio_code(radio_url)

    if info_type == 'radio':
        radio_info: RadioGardenInfo = {
            "id": info['data']['id'],
            "title": info['data']['title'],
            "url": info['data']['url'],
            "website": info['data']['website'],
            "stream": f'https://radio.garden/api/ara/content/listen/{info["data"]["id"]}/channel.mp3',
            "place": info['data']['place'],
            "country": info['data']['country']
        }
        return True, radio_info

    return False, 'Error'

# ---------------------------------------------- Radio TuneIn ----------------------------------------------------------

async def get_tunein_stream(code: str) -> (bool, str):
    """
    Returns the tunein radio stream from the code
    :param code: str - tunein code
    :return: (bool, str) - (successful, radio stream)
    """
    url = f'https://opml.radiotime.com/Tune.ashx?id={code}&render=json'
    async with aiohttp.ClientSession() as _session:
        async with _session.get(url) as _response:
            if _response.status == 200:
                _json_response = await _response.json()
                return True, _json_response['body'][0]['url']

    return False, ''

async def get_tunein_info(url: str) -> (bool, dict, str):
    """
    Returns the tunein radio info from the url
    :param url: str - tunein url or tunein id (_tunein:s123456)
    :return: (bool, dict, str) - (successful, radio info, stream url)
    """
    base_url = 'https://opml.radiotime.com'  # &render=json
    if url.startswith('_tunein:'):
        code = url.split(':')[1]
    else:
        return False, {}  # TODO: get tunein id from url

    describe_url = f'{base_url}/Describe.ashx?id={code}&render=json'
    async with aiohttp.ClientSession() as _session:
        async with _session.get(describe_url) as _response:
            if _response.status == 200:
                _json_response = await _response.json()
                stream_success, stream = await get_tunein_stream(code)
                if stream_success:
                    return True, _json_response['body'][0], stream

                # return True, _json_response['body'][0], await get_tunein_stream(code)

    return False, {}, ''

async def search_tunein(query: str, limit: int=5) -> (bool, list):
    """
    Returns the tunein search results from the query
    :param query: str - search query
    :param limit: int - search limit
    :return: (bool, list) - (successful, search results)
    """
    url = f'https://opml.radiotime.com/Search.ashx?query={urllib.parse.quote_plus(query)}&types=station&render=json&limit={limit}'
    async with aiohttp.ClientSession() as _session:
        async with _session.get(url) as _response:
            if _response.status == 200:
                _json_response = await _response.json()
                return True, _json_response['body'][:limit]

    return False, []

async def update_radio_dict(force_update: bool=False) -> dict[str, RadiosJSON] or None or str:
    """
    Updates the radio_dict with the latest radio data
    :param force_update: bool - force update
    """
    if int(time.time()) - int(radio_dict['last_updated']) < 86400 and not force_update:
        return 'up_to_date'

    log(None, "Updating radio_dict")

    radios_url = "https://radia.cz/xmlapp/zakladni-seznam-radii-v2.xml"

    async with aiohttp.ClientSession() as _session:
        async with _session.get(radios_url) as _response:
            if _response.status != 200:
                return 'status_error'
            _xml_data = xmltodict.parse(await _response.text(encoding='utf-8'))

    _radios = []
    for _category in _xml_data['categories']['category']:
        if type(_category['radios']['radio']) is list:
            for _radio in _category['radios']['radio']:
                _radios.append(_radio)
            continue

        _radios.append(_category['radios']['radio'])

    _radios_xml_links = [__radio['xmllink'] for __radio in _radios]

    async def get_station_info(url, session):
        r = await session.request('GET', url=f'{url}')
        return xmltodict.parse(await r.text(encoding='utf-8'))

    _radios_info = []
    async with aiohttp.ClientSession() as _session:
        _tasks = []
        for _url in _radios_xml_links:
            _tasks.append(get_station_info(url=_url, session=_session))
        _results = await asyncio.gather(*_tasks, return_exceptions=True)

    _return = {}
    for _item in _results:
        _ret_radio = _item['radio']
        _ret_radio['link'] = "https://radia.cz" + _item['radio']['link']
        _ret_radio['listened'] = [___radio['listened'] for ___radio in _radios if ___radio['id'] == _ret_radio['id']][0]
        _return[_item['radio']['id']] = _ret_radio

    _return = dict(sorted(_return.items(), key=lambda x: int(x[1]['listened']), reverse=True))
    _return['last_updated'] = int(time.time())

    with open('json/radios.json', 'w') as f:
        json.dump(_return, f, indent=4)

    globals()['radio_dict'] = _return

    return _return
