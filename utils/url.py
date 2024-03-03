import re
from typing import Literal

def extract_yt_id(url_string: str) -> str or None:
    """
    Extracts youtube video id from url
    https://youtube.com/watch?v={video_id} => video_id

    :param url_string: str - url
    :return: str - youtube video id
    """
    magic_regex = r"^(?:https?://|//)?(?:www\.|m\.|.+\.)?(?:youtu\.be/|youtube\.com/(?:embed/|v/|shorts/|feeds/api/videos/|watch\?v=|watch\?.+&v=))([\w-]{11})(?![\w-])"
    regex = re.compile(magic_regex)
    results = regex.search(url_string)

    if results is None:
        return None
    return results.group(1)

def get_playlist_from_url(url: str) -> str:
    """
    Returns playlist url from video url
    :param url: str - video url
    :return: str - playlist url
    """
    try:
        code = url[url.index('&list=') + 1:url.index('&index=')]
    except ValueError:
        code = url[url.index('&list=') + 1:]
    playlist_url = 'https://www.youtube.com/playlist?' + code
    return playlist_url

def get_url_of(string: str, section: str) -> str or None:
    """
    Returns url of section in string
    or None if not found
    :param string: str - string to search in
    :param section: str - section to search for
    :return: str - url or None
    """
    separated_string = string.split(' ')

    for s_string in separated_string:
        if section in s_string:
            return get_first_url(s_string)

    return None

def get_first_url(string: str) -> str or None:
    """
    Returns first url in string using regex
    or None if not found
    :param string: str - string to search in
    :return: str - url or None
    """
    re_search = re.search(r"(http|ftp|https)://([\w_-]+(?:\.[\w_-]+)+)([\w.,@?^=%&:/~+#-]*[\w@?^=%&/~+#-])", string)
    if re_search is None:
        return None
    return re_search[0]

def get_url_type(string: str) -> tuple[Literal['YouTube Playlist',
                                               'YouTube Playlist Video',
                                               'YouTube Video',
                                               'Spotify Playlist',
                                               'Spotify Album',
                                               'Spotify Track',
                                               'Spotify URL',
                                               'SoundCloud URL',
                                               'RadioGarden',
                                               'RadioTuneIn',
                                               'RadioCz',
                                               'Local',
                                               'String with URL',
                                               'String'], str]:
    """
    Returns type of url

    :param string: str - string to search in
    :return: (
    'YouTube Playlist',
    'YouTube Playlist Video',
    'YouTube Video',
    'Spotify Playlist',
    'Spotify Album',
    'Spotify Track',
    'Spotify URL',
    'SoundCloud URL',
    'RadioGarden',
    'RadioTuneIn',
    'RadioCz',
    'Local',
    'String with URL',
    'String'
    ), url: str
    """
    first_url = get_first_url(string)
    yt_id = extract_yt_id(string)

    if '/playlist?list=' in string and extract_yt_id(string) is None:
        extracted_url = get_url_of(string, '/playlist?list=')
        if extracted_url is None:
            return 'String', string
        return 'YouTube Playlist', extracted_url

    if any(param in string for param in {'index=', 'list='}) and extract_yt_id(string) is not None:
        extracted_url = get_url_of(string, 'index=')
        if extracted_url is None:
            extracted_url = get_url_of(string, 'list=')
            if extracted_url is None:
                return 'String', string
        return 'YouTube Playlist Video', extracted_url

    if yt_id is not None:
        return 'YouTube Video', string

    if 'spotify.com/playlist/' in string:
        extracted_url = get_url_of(string, 'spotify.com/playlist/')
        if extracted_url is None:
            return 'String', string
        return 'Spotify Playlist', extracted_url

    if 'spotify.com/album/' in string:
        extracted_url = get_url_of(string, 'spotify.com/album/')
        if extracted_url is None:
            return 'String', string
        return 'Spotify Album', extracted_url

    if 'spotify.com/track/' in string:
        extracted_url = get_url_of(string, 'spotify.com/track/')
        if extracted_url is None:
            return 'String', string
        return 'Spotify Track', extracted_url

    if 'spotify.com/' in string:
        extracted_url = get_url_of(string, 'spotify.com/')
        if extracted_url is None:
            return 'String', string
        return 'Spotify URL', extracted_url

    if 'soundcloud.com/' in string:
        extracted_url = get_url_of(string, 'soundcloud.com/')
        if extracted_url is None:
            return 'String', string
        return 'SoundCloud URL', extracted_url

    if 'radio.garden/' in string:
        extracted_url = get_url_of(string, 'radio.garden/')
        if extracted_url is None:
            return 'String', string
        return 'RadioGarden', extracted_url

    if string.startswith('_tunein:'):
        return 'RadioTuneIn', string

    if string.startswith('_radia_cz:'):
        return 'RadioCz', string

    if string.startswith('_local:'):
        return 'Local', string

    if first_url is not None:
        return 'String with URL', first_url

    return 'String', string

def command_for_type(url_type: str) -> str:
    """
    Returns command for url type
    :param url_type: str - url type
    :return: str - command
    """
    if url_type in ['YouTube Playlist', 'YouTube Playlist Video', 'YouTube Video']:
        return 'play'

    if url_type in ['Spotify Playlist', 'Spotify Album', 'Spotify Track', 'Spotify URL']:
        return 'play'

    if url_type in ['SoundCloud URL', 'String with URL']:
        return 'play'

    if url_type == "Local":
        return "ps"

    if url_type == "RadioCz":
        return "radio cz"

    if url_type == "RadioTuneIn":
        return "radio tunein"

    if url_type == "RadioGarden":
        return "radio garden"

    return 'search'
