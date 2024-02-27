from classes.typed_dictionaries import RadioGardenChannel, RadioGardenPlace, RadioGardenInfo

import aiohttp

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
