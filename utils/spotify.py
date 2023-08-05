from classes.video_class import VideoClass
from utils.globals import get_sp

import youtubesearchpython

def spotify_to_yt_video(spotify_url: str, author) -> VideoClass or None:
    """
    Converts spotify url to youtube video
    :param spotify_url: str - spotify url
    :param author: author of command
    :return: VideoClass object
    """
    # noinspection PyBroadException
    try:
        sp = get_sp()
        spotify_track = sp.track(spotify_url)
    except Exception:
        return None

    title = spotify_track['name']
    artist = spotify_track['artists'][0]['name']
    search_query = f"{title} {artist}"

    custom_search = youtubesearchpython.VideosSearch(search_query, limit=1)

    if not custom_search.result()['result']:
        return None

    custom_result: dict = custom_search.result()
    video: dict = custom_result['result'][0]

    yt_url = video['link']
    yt_title = video['title']
    yt_picture = 'https://img.youtube.com/vi/' + video['id'] + '/default.jpg'
    yt_duration = video['duration']
    yt_channel_name = video['channel']['name']
    yt_channel_link = video['channel']['link']

    video_class = VideoClass('Video', author, url=yt_url, title=yt_title, picture=yt_picture, duration=yt_duration,
                             channel_name=yt_channel_name, channel_link=yt_channel_link)

    return video_class

def spotify_playlist_to_yt_video_list(spotify_playlist_url: str, author) -> list or None:
    """
    Converts spotify playlist url to list of youtube videos
    :param spotify_playlist_url: str - spotify playlist url
    :param author: author of command
    :return: [VideoClass, VideoClass, ...] or None
    """
    # noinspection PyBroadException
    try:
        sp = get_sp()
        spotify_playlist = sp.playlist_items(spotify_playlist_url, fields='items.track.name, items.track.artists.name')
    except Exception:
        return None

    video_list = []

    for index, item in enumerate(spotify_playlist['items']):
        spotify_track = item['track']

        title = spotify_track['name']
        artist = spotify_track['artists'][0]['name']
        search_query = f"{title} {artist}"

        custom_search = youtubesearchpython.VideosSearch(search_query, limit=1)

        if not custom_search.result()['result']:
            continue

        custom_result: dict = custom_search.result()
        video: dict = custom_result['result'][0]

        yt_url = video['link']
        yt_title = video['title']
        yt_picture = 'https://img.youtube.com/vi/' + video['id'] + '/default.jpg'
        yt_duration = video['duration']
        yt_channel_name = video['channel']['name']
        yt_channel_link = video['channel']['link']

        video_class = VideoClass('Video', author, url=yt_url, title=yt_title, picture=yt_picture, duration=yt_duration,
                                 channel_name=yt_channel_name, channel_link=yt_channel_link)

        video_list.append(video_class)

    return video_list

def spotify_album_to_yt_video_list(spotify_album_url: str, author) -> list or None:
    """
    Converts spotify album url to list of youtube videos
    :param spotify_album_url: str - spotify album url
    :param author: author of command
    :return: [VideoClass, VideoClass, ...] or None
    """
    # noinspection PyBroadException
    try:
        sp = get_sp()
        spotify_album = sp.album_tracks(spotify_album_url)
    except Exception:
        return None

    video_list = []

    for index, spotify_track in enumerate(spotify_album['items']):
        title = spotify_track['name']
        artist = spotify_track['artists'][0]['name']
        search_query = f"{title} {artist}"

        custom_search = youtubesearchpython.VideosSearch(search_query, limit=1)

        if not custom_search.result()['result']:
            continue

        custom_result: dict = custom_search.result()
        video: dict = custom_result['result'][0]

        yt_url = video['link']
        yt_title = video['title']
        yt_picture = 'https://img.youtube.com/vi/' + video['id'] + '/default.jpg'
        yt_duration = video['duration']
        yt_channel_name = video['channel']['name']
        yt_channel_link = video['channel']['link']

        video_class = VideoClass('Video', author, url=yt_url, title=yt_title, picture=yt_picture, duration=yt_duration,
                                 channel_name=yt_channel_name, channel_link=yt_channel_link)

        video_list.append(video_class)

    return video_list