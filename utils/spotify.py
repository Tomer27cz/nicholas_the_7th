from youtubesearchpython.__future__ import VideosSearch

from classes.video_class import Queue
from classes.typed_dictionaries import VideoInfo

from utils.global_vars import GlobalVars

async def spotify_to_yt_video(glob: GlobalVars, spotify_url: str, author, guild_id: int):
    """
    Converts spotify url to youtube video
    :param glob: GlobalVars
    :param spotify_url: str - spotify url
    :param author: author of command
    :param guild_id: guild id
    :return: VideoClass child object
    """
    # noinspection PyBroadException
    try:
        spotify_api = glob.sp
        if not spotify_api:
            raise Exception("Spotify API not initialized")
        spotify_track = spotify_api.track(spotify_url)
    except Exception:
        return None

    title = spotify_track['name']
    artist = spotify_track['artists'][0]['name']
    search_query = f"{title} {artist}"

    cs = VideosSearch(search_query, limit=1)
    csr = await cs.next()
    custom_search = csr['result']

    if not custom_search:
        return None

    video: VideoInfo = custom_search[0]

    yt_url = video['link']
    yt_title = video['title']
    yt_picture = 'https://img.youtube.com/vi/' + video['id'] + '/default.jpg'
    yt_duration = video['duration']
    yt_channel_name = video['channel']['name']
    yt_channel_link = video['channel']['link']

    video_class = await Queue.create(glob, 'Video', author, guild_id, url=yt_url, title=yt_title, picture=yt_picture, duration=yt_duration,
                        channel_name=yt_channel_name, channel_link=yt_channel_link)

    return video_class

async def spotify_playlist_to_yt_video_list(glob: GlobalVars, spotify_playlist_url: str, author, guild_id: int) -> list or None:
    """
    Converts spotify playlist url to list of youtube videos
    :param glob: GlobalVars
    :param spotify_playlist_url: str - spotify playlist url
    :param author: author of command
    :param guild_id: guild id
    :return: [VideoClass child, VideoClass child, ...] or None
    """
    # noinspection PyBroadException
    try:
        spotify_api = glob.sp
        if not spotify_api:
            raise Exception("Spotify API not initialized")
        spotify_playlist = spotify_api.playlist_items(spotify_playlist_url, fields='items.track.name, items.track.artists.name')
    except Exception:
        return None

    video_list = []

    for index, item in enumerate(spotify_playlist['items']):
        spotify_track = item['track']

        title = spotify_track['name']
        artist = spotify_track['artists'][0]['name']
        search_query = f"{title} {artist}"

        cs = VideosSearch(search_query, limit=1)
        csr = await cs.next()
        custom_search = csr['result']

        if not custom_search:
            return None

        video: VideoInfo = custom_search[0]

        yt_url = video['link']
        yt_title = video['title']
        yt_picture = 'https://img.youtube.com/vi/' + video['id'] + '/default.jpg'
        yt_duration = video['duration']
        yt_channel_name = video['channel']['name']
        yt_channel_link = video['channel']['link']

        video_class = await Queue.create(glob, 'Video', author, guild_id, url=yt_url, title=yt_title, picture=yt_picture, duration=yt_duration,
                            channel_name=yt_channel_name, channel_link=yt_channel_link)

        video_list.append(video_class)

    return video_list

async def spotify_album_to_yt_video_list(glob: GlobalVars, spotify_album_url: str, author, guild_id: int) -> list or None:
    """
    Converts spotify album url to list of youtube videos
    :param glob: GlobalVars
    :param spotify_album_url: str - spotify album url
    :param author: author of command
    :param guild_id: guild id
    :return: [VideoClass child, VideoClass child, ...] or None
    """
    # noinspection PyBroadException
    try:
        spotify_api = glob.sp
        if not spotify_api:
            raise Exception("Spotify API not initialized")
        spotify_album = spotify_api.album_tracks(spotify_album_url)
    except Exception:
        return None

    video_list = []

    for index, spotify_track in enumerate(spotify_album['items']):
        title = spotify_track['name']
        artist = spotify_track['artists'][0]['name']
        search_query = f"{title} {artist}"

        cs = VideosSearch(search_query, limit=1)
        csr = await cs.next()
        custom_search = csr['result']

        if not custom_search:
            return None

        video: VideoInfo = custom_search[0]

        yt_url = video['link']
        yt_title = video['title']
        yt_picture = 'https://img.youtube.com/vi/' + video['id'] + '/default.jpg'
        yt_duration = video['duration']
        yt_channel_name = video['channel']['name']
        yt_channel_link = video['channel']['link']

        video_class = await Queue.create(glob, 'Video', author, guild_id, url=yt_url, title=yt_title, picture=yt_picture, duration=yt_duration,
                            channel_name=yt_channel_name, channel_link=yt_channel_link)

        video_list.append(video_class)

    return video_list
