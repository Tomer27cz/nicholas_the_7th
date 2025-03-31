from youtube_search_python.__future__ import VideosSearch

from classes.video_class import Queue
from classes.typed_dictionaries import VideoInfo, VideoAuthor

from utils.global_vars import GlobalVars

async def track_to_yt_video(glob: GlobalVars, track, author: VideoAuthor, guild_id: int):
    """
    Converts track to youtube video
    :param glob: GlobalVars
    :param track: str - track
    :param author: author of command
    :param guild_id: guild id
    :return: VideoClass child object
    """
    title = track['name']
    artist = track['artists'][0]['name']
    search_query = f"{title} {artist}"

    cs = VideosSearch(search_query, limit=1)
    csr = await cs.next()
    custom_search = csr['result']

    if not custom_search:
        return None

    video: VideoInfo = custom_search[0]

    yt_url = video['link']
    return await Queue.create(glob, 'Video', author, guild_id, url=yt_url)

async def spotify_to_yt_video(glob: GlobalVars, spotify_url: str, author: VideoAuthor, guild_id: int):
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

    return await track_to_yt_video(glob, spotify_track, author, guild_id)

async def spotify_playlist_to_yt_video_list(glob: GlobalVars, spotify_playlist_url: str, author: VideoAuthor, guild_id: int) -> list or None:
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

        video_class = await track_to_yt_video(glob, spotify_track, author, guild_id)
        video_list.append(video_class)

    return video_list

async def spotify_album_to_yt_video_list(glob: GlobalVars, spotify_album_url: str, author: VideoAuthor, guild_id: int) -> list or None:
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
        video_class = await track_to_yt_video(glob, spotify_track, author, guild_id)
        video_list.append(video_class)

    return video_list
