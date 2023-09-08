from __future__ import annotations
from typing import TYPE_CHECKING, Union
if TYPE_CHECKING:
    from classes.typed_dictionaries import *

from utils.globals import get_radio_dict, get_sc
from utils.convert import convert_duration
import utils.video_time
import utils.save

from sclib import Track
from time import time
from bs4 import BeautifulSoup
import requests
import youtubesearchpython

from config import VLC_LOGO as vlc_logo
from config import WEB_URL

class VideoClass:
    """
    Stores all the data for each video
    Can do, YouTube, SoundCloud, Czech Radios, Url Probes, Local Files and Fake Spotify

    Raises ValueError: If URL is not provided or is incorrect for class_type
    """

    def __init__(self,
                 class_type: str,
                 author: Union[str, int],
                 url: str=None,
                 title: str=None,
                 picture: str=None,
                 duration: Union[str, int]=None,
                 channel_name: str=None,
                 channel_link: str=None,
                 radio_info: RadioInfo=None,
                 local_number: int=None,
                 created_at: int=None,
                 played_duration: [TimeSegment]=None,
                 chapters: [VideoChapter]=None,
                 stream_url: str=None,
                 discord_channel: DiscordChannelInfo=None
                 ):
        self.class_type = class_type
        self.author = author
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

        if created_at is None:
            self.created_at = int(time())

        if played_duration is None:
            # [{'start': {'epoch': None, 'time_stamp': None},'end': {'epoch': None, 'time_stamp': None}}]
            self.played_duration = []

        if self.class_type == 'Video':
            if url is None:
                raise ValueError("URL is required")

            if any(v is None for v in [title, picture, duration, channel_name, channel_link]):
                video, msg = get_video_data(url)
                if msg != 'ok':
                    raise ValueError(msg)

                self.title = video['title']
                self.picture = 'https://img.youtube.com/vi/' + video['id'] + '/default.jpg'
                self.duration = video['duration']['secondsText']
                self.channel_name = video['channel']['name']
                self.channel_link = video['channel']['link']

        elif self.class_type == 'Radio':
            if radio_info is None:
                raise ValueError("radio_info required")

            if type(radio_info) != dict:
                raise ValueError("radio_info must be a dict")

            if 'name' not in radio_info.keys():
                raise ValueError("radio_info must contain name")

            if any(v is None for v in [url, title, picture, duration, channel_name, channel_link]):
                radio_dict = get_radio_dict()
                radio_name = radio_info['name']
                self.url = radio_dict[radio_name]['url']
                self.title = radio_dict[radio_name]['name']
                self.picture = f'{WEB_URL}/static/radio_png/png_radio_{radio_dict[radio_name]["id"]}.png'
                self.duration = 'Stream'
                self.channel_name = radio_dict[radio_name]['type']
                self.channel_link = self.url
                self.radio_info['website'] = radio_dict[radio_name]['type']

        elif self.class_type == 'Local':
            if local_number is None:
                raise ValueError("Local number required")

            self.picture = vlc_logo
            self.channel_name = 'Local File'

        elif self.class_type == 'Probe':
            if url is None:
                raise ValueError("URL is required")

        elif self.class_type == 'SoundCloud':
            if url is None:
                raise ValueError("URL is required")

            if any(v is None for v in [title, picture, duration, channel_name, channel_link]):
                try:
                    soundcloud_api = get_sc()
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

    def renew(self):
        if self.class_type == 'Radio':
            if self.radio_info['website'] == 'radia_cz':
                html = requests.get(self.url).text
                soup = BeautifulSoup(html, features="lxml")
                data1 = soup.find('div', attrs={'class': 'interpret-image'})
                data2 = soup.find('div', attrs={'class': 'interpret-info'})

                self.radio_info['picture'] = data1.find('img')['src']
                self.radio_info['channel_name'] = data2.find('div', attrs={'class': 'nazev'}).text.lstrip().rstrip()
                self.radio_info['title'] = data2.find('div', attrs={'class': 'song'}).text.lstrip().rstrip()

            elif self.radio_info['website'] == 'actve':
                r = requests.get(self.url).json()
                self.radio_info['picture'] = r['coverBase']
                self.radio_info['channel_name'] = r['artist']
                self.radio_info['title'] = r['title']

            else:
                raise ValueError("Invalid radio website")

        utils.save.save_json()

    def current_chapter(self):
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

        utils.save.save_json()

    def time(self):
        if self.duration is None:
            return '0:00 / 0:00'
        if self.played_duration[-1]['end']['epoch'] is not None:
            return '0:00 / ' + convert_duration(self.duration)

        time_from_play = int(utils.video_time.video_time_from_start(self))

        try:
            duration = int(self.duration)
        except (ValueError, TypeError):
            return f'{convert_duration(time_from_play)} / {self.duration}'

        if time_from_play == 0:
            return '0:00 / ' + convert_duration(duration)

        utils.save.save_json()

        return f'{convert_duration(time_from_play)} / {convert_duration(duration)}'

def get_video_data(url: str) -> (dict, str) or (None, str):
    """
    Returns youtube video info
    :param url: str - youtube video url
    :return: dict - video info
    """
    try:
        video = youtubesearchpython.Video.getInfo(url)  # mode=ResultMode.json
        if not video:
            return None, 'not video'
    except Exception as e:
        return None, e

    return video, 'ok'