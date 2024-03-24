from __future__ import annotations
from youtubesearchpython.__future__ import Video
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from classes.typed_dictionaries import *
    from utils.global_vars import GlobalVars

from database.main import *

from utils.convert import convert_duration
from utils.global_vars import radio_dict

import utils.video_time
import utils.save

from sclib import Track
from time import time
# from youtubesearchpython import Video

import xmltodict
import aiohttp

import config

async def get_video_data(url: str) -> (dict, str) or (None, str):
    """
    Returns youtube video info
    :param url: str - youtube video url
    :return: dict - video info
    """
    try:
        video: VideoInfo = await Video.getInfo(url)  # mode=ResultMode.json
        if not video:
            return None, 'not video'
    except Exception as e:
        return None, e

    return video, 'ok'

# Video Class Functions

# class_type: Literal['Video', 'RadioCz', 'RadioGarden', 'RadioTuneIn', 'Local', 'Probe', 'SoundCloud']

async def video_class_init(self,
                           glob: GlobalVars,
                           class_type: str,
                           author: VideoAuthor,
                           guild_id: int,
                           url: str = None,
                           title: str = None,
                           picture: str = None,
                           duration: Union[str, int] = None,
                           channel_name: str = None,
                           channel_link: str = None,
                           radio_info: RadioInfoDict = None,
                           local_number: int = None,
                           created_at: int = None,
                           played_duration: [TimeSegment] = None,
                           chapters: [VideoChapter] = None,
                           stream_url: str = None,
                           discord_channel: DiscordChannelInfo = None,
                           only_set: bool = False
                           ):
    self.class_type = class_type
    self.author = author
    self.guild_id = guild_id
    self.url = url
    self.title = title
    self.picture = picture
    self.duration = duration
    self.channel_name = channel_name
    self.channel_link = channel_link
    self.radio_info = radio_info
    self.local_number = local_number
    self.created_at = created_at
    self.played_duration = played_duration
    self.chapters = chapters
    self.discord_channel = discord_channel
    if only_set:
        self.stream_url = stream_url
        return

    if created_at is None:
        self.created_at = int(time())

    if played_duration is None:
        # [{'start': {'epoch': None, 'time_stamp': None},'end': {'epoch': None, 'time_stamp': None}}]
        self.played_duration = []

    if self.class_type in ['RadioCz', 'RadioGarden', 'RadioTuneIn']:
        if self.radio_info is None:
            raise ValueError("radio_info required")

        provider_name_dict = {'radia_cz': 'radia.cz', 'tunein': 'tunein.com', 'garden': 'radio.garden'}
        provider_url_dict = {'radia_cz': 'station_website', 'tunein': 'url', 'garden': 'url'}

        provider_name = provider_name_dict.get(self.radio_info['type'], 'Unknown')
        # noinspection PyTypedDict
        provider_url = self.radio_info[provider_url_dict.get(self.radio_info['type'], 'url')]

        self.url = self.radio_info['station_website'] if self.url is None else self.url
        self.title = self.radio_info['station_name'] if self.title is None else self.title
        self.picture = self.radio_info['station_picture'] if self.picture is None else self.picture
        self.duration = 'Stream' if self.duration is None else self.duration

        self.channel_name = provider_name if self.channel_name is None else self.channel_name
        self.channel_link = provider_url if self.channel_link is None else self.channel_link

        self.stream_url = self.radio_info['stream'] if self.stream_url is None else self.stream_url
        stream_url = self.radio_info['stream']

    if self.class_type == 'Video':
        if url is None:
            raise ValueError("URL is required")

        if any(v is None for v in [title, picture, duration, channel_name, channel_link]):
            video, msg = await get_video_data(url)
            if msg != 'ok':
                raise ValueError(msg)

            self.title = video['title']
            self.picture = 'https://img.youtube.com/vi/' + video['id'] + '/default.jpg'
            self.duration = video['duration']['secondsText']
            self.channel_name = video['channel']['name']
            self.channel_link = video['channel']['link']

    elif self.class_type == 'RadioCz':
        if self.radio_info is None:
            raise ValueError("radio_info required")

        if self.radio_info['station_name'] is None:
            raise ValueError("station_name required")

        self.radio_info['station_website'] = self.radio_info.get('station_website', radio_dict[self.radio_info['id']]['link'])
        self.radio_info['url'] = self.radio_info.get('url', radio_dict[self.radio_info['id']]['nowplay'])
        self.radio_info['station_picture'] = self.radio_info.get('station_picture', radio_dict[self.radio_info['id']]['logo'])
        self.radio_info['stream'] = self.radio_info.get('stream', radio_dict[self.radio_info['id']]['streams']['stream'][0]['url'] if type(radio_dict[self.radio_info['id']]['streams']['stream']) is list else radio_dict[self.radio_info['id']]['streams']['stream']['url'])

        self.url = self.radio_info['station_website'] if self.url is None else self.url
        self.title = self.radio_info['station_name'] if self.title is None else self.title
        self.picture = self.radio_info['station_picture'] if self.picture is None else self.picture
        self.stream_url = self.radio_info['stream'] if self.stream_url is None else self.stream_url
        stream_url = self.radio_info['stream']

        await video_class_renew(self, glob, from_init=True)

    elif self.class_type == 'RadioGarden':
        if self.radio_info is None:
            raise ValueError("radio_info required")

        self.radio_info['station_picture'] = self.radio_info.get('station_picture', 'https://radio.garden/icons/favicon.png')
        self.picture = self.radio_info['station_picture'] if self.picture is None else self.picture

    elif self.class_type == 'RadioTuneIn':
        if self.radio_info is None:
            raise ValueError("radio_info required")

        self.radio_info['station_picture'] = self.radio_info.get('station_picture', 'https://tunein.com/favicon.ico')
        self.picture = self.radio_info['station_picture'] if self.picture is None else self.picture

        await video_class_renew(self, glob, from_init=True)

    elif self.class_type == 'Local':
        if local_number is None:
            raise ValueError("Local number required")

        self.picture = config.VLC_LOGO
        self.channel_name = 'Local File'

    elif self.class_type == 'Probe':
        if url is None:
            raise ValueError("URL is required")

    elif self.class_type == 'SoundCloud':
        if url is None:
            raise ValueError("URL is required")

        if any(v is None for v in [title, picture, duration, channel_name, channel_link]):
            try:
                soundcloud_api = glob.sc
                if soundcloud_api is None:
                    raise ValueError("SoundCloud API is not initialized")
                track = soundcloud_api.resolve(self.url)
                assert type(track) is Track
            except Exception as e:
                raise ValueError(f"Not a SoundCloud Track link: {e}")

            self.url = track.permalink_url
            self.title = track.title
            self.picture = track.artwork_url
            self.duration = int(track.duration * 0.001)
            self.channel_name = track.artist
            self.channel_link = 'https://soundcloud.com/' + track.permalink_url.split('/')[-2]

    else:
        raise ValueError(f"Invalid class type: {class_type}")

    # set stream_url at the end for json readability
    self.stream_url = stream_url

async def video_class_renew(self, glob: GlobalVars or None=None, from_init: bool = False):
    if self.class_type not in ['RadioCz', 'RadioGarden', 'RadioTuneIn']:
        return

    if self.radio_info is None:
        return

    ri: RadioInfoDict = self.radio_info

    try:
        if int(time()) - int(ri['last_update']) < 10 and not from_init:
            return
    except (ValueError, TypeError):
        pass

    if ri['type'] == 'radia_cz':
        async with aiohttp.ClientSession() as session:
            async with session.get(ri['url']) as resp:
                resp.encoding = 'utf-8'
                xml_dict: RadiosCzNow = xmltodict.parse(await resp.text())

        def get_xml_picture(xml_radio: RadiosCzNow) -> str:
            _now_picture = 'https://radia.cz/build/no-artwork.svg'
            if not xml_radio['NowPlay']:
                return _now_picture

            if not xml_radio['NowPlay']['Item']:
                return _now_picture

            if not xml_radio['NowPlay']['Item']['Images']:
                return _now_picture

            if type(xml_radio['NowPlay']['Item']['Images']['Image']) is list:
                return xml_radio['NowPlay']['Item']['Images']['Image'][0]['#text']

            return xml_radio['NowPlay']['Item']['Images']['Image']['#text']

        def get_xml_title(xml_radio: RadiosCzNow) -> str or None:
            _now_title = None
            if not xml_radio['NowPlay']:
                return _now_title

            if not xml_radio['NowPlay']['Item']:
                return _now_title

            if not xml_radio['NowPlay']['Item']['Song']:
                return _now_title

            if type(xml_radio['NowPlay']['Item']['Song']) is dict:
                return xml_radio['NowPlay']['Item']['Song']['#text']

            return xml_radio['NowPlay']['Item']['Song']

        def get_xml_artist(xml_radio: RadiosCzNow) -> str or None:
            _now_artist = None
            if not xml_radio['NowPlay']:
                return _now_artist

            if not xml_radio['NowPlay']['Item']:
                return _now_artist

            if not xml_radio['NowPlay']['Item']['Artist']:
                return _now_artist

            if type(xml_radio['NowPlay']['Item']['Artist']) is dict:
                return xml_radio['NowPlay']['Item']['Artist']['#text']

            return xml_radio['NowPlay']['Item']['Artist']

        ri['now_title'] = get_xml_title(xml_dict)
        ri['now_picture'] = get_xml_picture(xml_dict)
        ri['now_artist'] = get_xml_artist(xml_dict)

    elif ri['type'] == 'garden':
        pass

    elif ri['type'] == 'tunein':
        async with aiohttp.ClientSession() as session:
            async with session.get(f'https://opml.radiotime.com/Describe.ashx?id={ri["id"]}&render=json') as resp:
                json_resp = await resp.json()
                r = json_resp['body'][0]

        ri['station_name'] = r['name']
        ri['station_picture'] = r['logo']
        ri['station_website'] = r['url']

        ri['now_title'] = r['current_song'] if r['current_song'] is not None else None
        ri['now_picture'] = r['logo'] if r['current_artist_art'] is None else r['current_artist_art'] if r['current_album_art'] is None else r['current_album_art']
        ri['now_artist'] = r['current_artist'] if r['current_artist'] is not None else None

    ri['last_update'] = int(time())
    self.radio_info = ri

def video_class_current_chapter(self, glob: GlobalVars or None=None):
    if self.played_duration is None:
        return None
    if self.chapters is None:
        return None
    if self.played_duration[-1]['end']['epoch'] is not None:
        return None

    time_from_play = int(utils.video_time.video_time_from_start(self))

    try:
        duration = int(self.duration)
        if time_from_play > duration:
            return None
    except (ValueError, TypeError):
        return None

    for chapter in self.chapters:
        if chapter['start_time'] < time_from_play < chapter['end_time']:
            return chapter['title']

def video_class_time(self, glob: GlobalVars or None=None) -> str:
    """
    Returns time from start and duration of video
    @param self: VideoClass object child
    @param glob: GlobalVars - consistency
    @return: str - '{elapsed_time} / {duration}'
    """
    if self.duration is None or self.played_duration is None:
        return '0:00 / 0:00'

    # # i dont know why this is here past me?
    # if self.played_duration[-1]['end']['epoch'] is not None:
    #     return '0:00 / ' + convert_duration(self.duration)

    # will be 0.0 if never played
    elapsed_time = int(utils.video_time.video_time_from_start(self))

    try:
        duration = int(self.duration)
    except (ValueError, TypeError):
        return f'{convert_duration(elapsed_time)} / {self.duration}'

    if elapsed_time == 0:
        return '0:00 / ' + convert_duration(duration)

    return f'{convert_duration(elapsed_time)} / {convert_duration(duration)}'

def video_to_json(self) -> dict:
    """
    Returns video data as json
    @param self: VideoClass object child
    @return: dict - video data
    """
    return {
        'class_type': self.class_type,
        'author': self.author,
        'guild_id': self.guild_id,
        'url': self.url,
        'title': self.title,
        'picture': self.picture,
        'duration': self.duration,
        'channel_name': self.channel_name,
        'channel_link': self.channel_link,
        'radio_info': self.radio_info,
        'local_number': self.local_number,
        'created_at': self.created_at,
        'played_duration': self.played_duration,
        'chapters': self.chapters,
        'stream_url': self.stream_url,
        'discord_channel': self.discord_channel
    }

# Video Classes

# class VideoClass(Base):
#     """
#     Stores all the data for each video
#     Can do, YouTube, SoundCloud, Czech Radios, Url Probes, Local Files and Fake Spotify
#
#     Raises ValueError: If URL is not provided or is incorrect for class_type
#     """
#     __tablename__ = 'videos'
#
#     id = Column(Integer, primary_key=True)
#     position = Column(Integer)
#     class_type = Column(String)
#     author = Column(String)
#     guild_id = Column(Integer, ForeignKey('guilds.id'))
#     url = Column(String)
#     title = Column(String)
#     picture = Column(String)
#     duration = Column(String)
#     channel_name = Column(String)
#     channel_link = Column(String)
#     radio_info = Column(JSON)
#     local_number = Column(Integer)
#     created_at = Column(Integer)
#     played_duration = Column(JSON)
#     chapters = Column(JSON)
#     stream_url = Column(String)
#     discord_channel = Column(JSON)
#
#     def __init__(self,
#                  class_type: str,
#                  author: Union[str, int],
#                  guild_id: int,
#                  url: str=None,
#                  title: str=None,
#                  picture: str=None,
#                  duration: Union[str, int]=None,
#                  channel_name: str=None,
#                  channel_link: str=None,
#                  radio_info: RadioInfoDict=None,
#                  local_number: int=None,
#                  created_at: int=None,
#                  played_duration: [TimeSegment]=None,
#                  chapters: [VideoChapter]=None,
#                  stream_url: str=None,
#                  discord_channel: DiscordChannelInfo=None
#                  ):
#         video_class_init(self,
#                          class_type=class_type,
#                          author=author,
#                          guild_id=guild_id,
#                          url=url,
#                          title=title,
#                          picture=picture,
#                          duration=duration,
#                          channel_name=channel_name,
#                          channel_link=channel_link,
#                          radio_info=radio_info,
#                          local_number=local_number,
#                          created_at=created_at,
#                          played_duration=played_duration,
#                          chapters=chapters,
#                          stream_url=stream_url,
#                          discord_channel=discord_channel)
#
#     def renew(self):
#         video_class_renew(self)
#
#     def current_chapter(self):
#         return video_class_current_chapter(self)
#
#     def time(self):
#         return video_class_time(self)

class Queue(Base):
    """
    Stores all the data for each video
    Can do, YouTube, SoundCloud, Czech Radios, Url Probes, Local Files and Fake Spotify

    Raises ValueError: If URL is not provided or is incorrect for class_type
    """
    __tablename__ = 'queue'

    id = Column(Integer, primary_key=True)
    position = Column(Integer)
    class_type = Column(String)
    author = Column(JSON)
    guild_id = Column(Integer, ForeignKey('guilds.id'))
    url = Column(String)
    title = Column(String)
    picture = Column(String)
    duration = Column(String)
    channel_name = Column(String)
    channel_link = Column(String)
    radio_info = Column(JSON)
    local_number = Column(Integer)
    created_at = Column(Integer)
    played_duration = Column(JSON)
    chapters = Column(JSON)
    stream_url = Column(String)
    discord_channel = Column(JSON)

    @classmethod
    async def create(cls,
                     glob: GlobalVars or None,
                     class_type: str,
                     author: VideoAuthor,
                     guild_id: int,
                     url: str = None,
                     title: str = None,
                     picture: str = None,
                     duration: Union[str, int] = None,
                     channel_name: str = None,
                     channel_link: str = None,
                     radio_info: RadioInfoDict = None,
                     local_number: int = None,
                     created_at: int = None,
                     played_duration: [TimeSegment] = None,
                     chapters: [VideoChapter] = None,
                     stream_url: str = None,
                     discord_channel: DiscordChannelInfo = None,
                     only_set: bool = False
                     ) -> Queue:
        self = cls()
        await video_class_init(self,
                               glob,
                               class_type=class_type,
                               author=author,
                               guild_id=guild_id,
                               url=url,
                               title=title,
                               picture=picture,
                               duration=duration,
                               channel_name=channel_name,
                               channel_link=channel_link,
                               radio_info=radio_info,
                               local_number=local_number,
                               created_at=created_at,
                               played_duration=played_duration,
                               chapters=chapters,
                               stream_url=stream_url,
                               discord_channel=discord_channel,
                               only_set=only_set)

        return self

    async def renew(self, glob: GlobalVars or None=None, force: bool = False):
        await video_class_renew(self, glob, from_init=force)

    def current_chapter(self, glob: GlobalVars or None=None):
        return video_class_current_chapter(self, glob)

    def time(self, glob: GlobalVars or None=None):
        return video_class_time(self, glob)

    def to_json(self):
        return video_to_json(self)

class NowPlaying(Base):
    """
    Stores all the data for each video
    Can do, YouTube, SoundCloud, Czech Radios, Url Probes, Local Files and Fake Spotify

    Raises ValueError: If URL is not provided or is incorrect for class_type
    """
    __tablename__ = 'now_playing'

    id = Column(Integer, primary_key=True)
    position = Column(Integer)
    class_type = Column(String)
    author = Column(JSON)
    guild_id = Column(Integer, ForeignKey('guilds.id'))
    url = Column(String)
    title = Column(String)
    picture = Column(String)
    duration = Column(String)
    channel_name = Column(String)
    channel_link = Column(String)
    radio_info = Column(JSON)
    local_number = Column(Integer)
    created_at = Column(Integer)
    played_duration = Column(JSON)
    chapters = Column(JSON)
    stream_url = Column(String)
    discord_channel = Column(JSON)

    @classmethod
    async def create(cls,
                     glob: GlobalVars or None,
                     class_type: str,
                     author: VideoAuthor,
                     guild_id: int,
                     url: str = None,
                     title: str = None,
                     picture: str = None,
                     duration: Union[str, int] = None,
                     channel_name: str = None,
                     channel_link: str = None,
                     radio_info: RadioInfoDict = None,
                     local_number: int = None,
                     created_at: int = None,
                     played_duration: [TimeSegment] = None,
                     chapters: [VideoChapter] = None,
                     stream_url: str = None,
                     discord_channel: DiscordChannelInfo = None,
                     only_set: bool = False
                     ) -> NowPlaying:
        self = cls()
        await video_class_init(self,
                               glob,
                               class_type=class_type,
                               author=author,
                               guild_id=guild_id,
                               url=url,
                               title=title,
                               picture=picture,
                               duration=duration,
                               channel_name=channel_name,
                               channel_link=channel_link,
                               radio_info=radio_info,
                               local_number=local_number,
                               created_at=created_at,
                               played_duration=played_duration,
                               chapters=chapters,
                               stream_url=stream_url,
                               discord_channel=discord_channel,
                               only_set=only_set)
        return self

    async def renew(self, glob: GlobalVars or None=None, force: bool = False):
        await video_class_renew(self, glob, from_init=force)

    def current_chapter(self, glob: GlobalVars or None=None):
        return video_class_current_chapter(self, glob)

    def time(self, glob: GlobalVars or None=None):
        return video_class_time(self, glob)

    def to_json(self):
        return video_to_json(self)

class History(Base):
    """
    Stores all the data for each video
    Can do, YouTube, SoundCloud, Czech Radios, Url Probes, Local Files and Fake Spotify

    Raises ValueError: If URL is not provided or is incorrect for class_type
    """
    __tablename__ = 'history'

    id = Column(Integer, primary_key=True)
    position = Column(Integer)
    class_type = Column(String)
    author = Column(JSON)
    guild_id = Column(Integer, ForeignKey('guilds.id'))
    url = Column(String)
    title = Column(String)
    picture = Column(String)
    duration = Column(String)
    channel_name = Column(String)
    channel_link = Column(String)
    radio_info = Column(JSON)
    local_number = Column(Integer)
    created_at = Column(Integer)
    played_duration = Column(JSON)
    chapters = Column(JSON)
    stream_url = Column(String)
    discord_channel = Column(JSON)

    @classmethod
    async def create(cls,
                     glob: GlobalVars or None,
                     class_type: str,
                     author: VideoAuthor,
                     guild_id: int,
                     url: str = None,
                     title: str = None,
                     picture: str = None,
                     duration: Union[str, int] = None,
                     channel_name: str = None,
                     channel_link: str = None,
                     radio_info: RadioInfoDict = None,
                     local_number: int = None,
                     created_at: int = None,
                     played_duration: [TimeSegment] = None,
                     chapters: [VideoChapter] = None,
                     stream_url: str = None,
                     discord_channel: DiscordChannelInfo = None,
                     only_set: bool = False
                     ) -> History:
        self = cls()
        await video_class_init(self,
                               glob,
                               class_type=class_type,
                               author=author,
                               guild_id=guild_id,
                               url=url,
                               title=title,
                               picture=picture,
                               duration=duration,
                               channel_name=channel_name,
                               channel_link=channel_link,
                               radio_info=radio_info,
                               local_number=local_number,
                               created_at=created_at,
                               played_duration=played_duration,
                               chapters=chapters,
                               stream_url=stream_url,
                               discord_channel=discord_channel,
                               only_set=only_set)
        return self

    async def renew(self, glob: GlobalVars or None=None, force: bool = False):
        await video_class_renew(self, glob, from_init=force)

    def current_chapter(self, glob: GlobalVars or None=None):
        return video_class_current_chapter(self, glob)

    def time(self, glob: GlobalVars or None=None):
        return video_class_time(self, glob)

    def to_json(self):
        return video_to_json(self)

class SaveVideo(Base):
    """
    Stores all the data for each video
    Can do, YouTube, SoundCloud, Czech Radios, Url Probes, Local Files and Fake Spotify

    Raises ValueError: If URL is not provided or is incorrect for class_type
    """
    __tablename__ = 'save_videos'

    save_id = Column(Integer, ForeignKey('saves.id'))

    id = Column(Integer, primary_key=True)
    position = Column(Integer)
    class_type = Column(String)
    author = Column(JSON)
    guild_id = Column(Integer, ForeignKey('guilds.id'))
    url = Column(String)
    title = Column(String)
    picture = Column(String)
    duration = Column(String)
    channel_name = Column(String)
    channel_link = Column(String)
    radio_info = Column(JSON)
    local_number = Column(Integer)
    created_at = Column(Integer)
    played_duration = Column(JSON)
    chapters = Column(JSON)
    stream_url = Column(String)
    discord_channel = Column(JSON)

    @classmethod
    async def create(cls,
                     glob: GlobalVars or None,
                     class_type: str,
                     author: VideoAuthor,
                     guild_id: int,
                     save_id: int,
                     url: str = None,
                     title: str = None,
                     picture: str = None,
                     duration: Union[str, int] = None,
                     channel_name: str = None,
                     channel_link: str = None,
                     radio_info: RadioInfoDict = None,
                     local_number: int = None,
                     created_at: int = None,
                     played_duration: [TimeSegment] = None,
                     chapters: [VideoChapter] = None,
                     stream_url: str = None,
                     discord_channel: DiscordChannelInfo = None,
                     only_set: bool = False
                     ) -> SaveVideo:
        self = cls()
        self.save_id = save_id
        await video_class_init(self,
                               glob,
                               class_type=class_type,
                               author=author,
                               guild_id=guild_id,
                               url=url,
                               title=title,
                               picture=picture,
                               duration=duration,
                               channel_name=channel_name,
                               channel_link=channel_link,
                               radio_info=radio_info,
                               local_number=local_number,
                               created_at=created_at,
                               played_duration=played_duration,
                               chapters=chapters,
                               stream_url=stream_url,
                               discord_channel=discord_channel,
                               only_set=only_set)
        return self

    async def renew(self, glob: GlobalVars or None=None, force: bool = False):
        await video_class_renew(self, glob, from_init=force)

    def current_chapter(self, glob: GlobalVars or None=None):
        return video_class_current_chapter(self, glob)

    def time(self, glob: GlobalVars or None=None):
        return video_class_time(self, glob)

    def to_json(self):
        return video_to_json(self)

# Transforms

async def to_queue_class(glob, _video_class) -> Queue:
    if _video_class.__class__.__name__ == 'Queue':
        return _video_class

    return await Queue.create(
        glob,
        class_type=_video_class.class_type,
        author=_video_class.author,
        guild_id=_video_class.guild_id,
        url=_video_class.url,
        title=_video_class.title,
        picture=_video_class.picture,
        duration=_video_class.duration,
        channel_name=_video_class.channel_name,
        channel_link=_video_class.channel_link,
        radio_info=_video_class.radio_info,
        local_number=_video_class.local_number,
        created_at=_video_class.created_at,
        played_duration=_video_class.played_duration,
        chapters=_video_class.chapters,
        stream_url=_video_class.stream_url,
        discord_channel=_video_class.discord_channel,
        only_set=True
    )

async def to_now_playing_class(glob, _video_class) -> NowPlaying:
    if _video_class.__class__.__name__ == 'NowPlaying':
        return _video_class

    return await NowPlaying.create(
        glob,
        class_type=_video_class.class_type,
        author=_video_class.author,
        guild_id=_video_class.guild_id,
        url=_video_class.url,
        title=_video_class.title,
        picture=_video_class.picture,
        duration=_video_class.duration,
        channel_name=_video_class.channel_name,
        channel_link=_video_class.channel_link,
        radio_info=_video_class.radio_info,
        local_number=_video_class.local_number,
        created_at=_video_class.created_at,
        played_duration=_video_class.played_duration,
        chapters=_video_class.chapters,
        stream_url=_video_class.stream_url,
        discord_channel=_video_class.discord_channel,
        only_set=True
    )

async def to_history_class(glob, _video_class) -> History:
    if _video_class.__class__.__name__ == 'History':
        return _video_class

    return await History.create(
        glob,
        class_type=_video_class.class_type,
        author=_video_class.author,
        guild_id=_video_class.guild_id,
        url=_video_class.url,
        title=_video_class.title,
        picture=_video_class.picture,
        duration=_video_class.duration,
        channel_name=_video_class.channel_name,
        channel_link=_video_class.channel_link,
        radio_info=_video_class.radio_info,
        local_number=_video_class.local_number,
        created_at=_video_class.created_at,
        played_duration=_video_class.played_duration,
        chapters=_video_class.chapters,
        stream_url=_video_class.stream_url,
        discord_channel=_video_class.discord_channel,
        only_set=True
    )

async def to_save_video_class(glob, _video_class, save_id) -> SaveVideo:
    if _video_class.__class__.__name__ == 'SaveVideo':
        return _video_class

    return await SaveVideo.create(
        glob,
        class_type=_video_class.class_type,
        author=_video_class.author,
        guild_id=_video_class.guild_id,
        save_id=save_id,
        url=_video_class.url,
        title=_video_class.title,
        picture=_video_class.picture,
        duration=_video_class.duration,
        channel_name=_video_class.channel_name,
        channel_link=_video_class.channel_link,
        radio_info=_video_class.radio_info,
        local_number=_video_class.local_number,
        created_at=_video_class.created_at,
        played_duration=_video_class.played_duration,
        chapters=_video_class.chapters,
        stream_url=_video_class.stream_url,
        discord_channel=_video_class.discord_channel,
        only_set=True
    )
