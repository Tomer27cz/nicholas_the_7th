from __future__ import annotations

from database.guild import guild

from utils.log import log
from utils.global_vars import GlobalVars

import discord
import asyncio
import yt_dlp
import aiohttp

YTDL_OPTIONS = {
    'format': 'bestaudio/best',
    'extractaudio': True,
    'audioformat': 'mp3',
    'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0',
}

FFMPEG_OPTIONS = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
    'options': '-vn',
}

async def url_checker(url):
    if url.endswith('.m3u8'):
        return True, 200

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 200:
                    return True, response.status
                return False, response.status
    except Exception as e:
        return False, e

def format_subtitles(subtitles: dict, subtitle_type: str='captions') -> dict:
    """
    Format subtitles only leave the json3 format like this:
    {'lang': 'url'}

    :param subtitles: dict
    :param subtitle_type: str - 'captions' or 'subtitles'
    :return formatted_subtitles: dict
    """

    if subtitles is None or not subtitles or not isinstance(subtitles, dict) or len(subtitles) == 0:
        return None

    if subtitles.get('live_chat', None) is not None:
        return None

    if subtitle_type not in ['captions', 'subtitles']:
        raise ValueError('Invalid subtitle type. Must be either "captions" or "subtitles".')

    url_template = None

    subtitle_keys = [k for k in list(subtitles.keys()) if k != 'en'] # remove english
    if subtitle_keys:
        first_ext = [url for url in subtitles[subtitle_keys[0]] if url.get('ext', None) == 'json3']
        if first_ext:
            url_template = first_ext[0]['url']
            if subtitle_type == 'captions':
                if '&tlang=' in url_template:
                    url_template = url_template[:url_template.index('&tlang=') + 7]
            else:
                if '&lang=' in url_template:
                    url_template = url_template[:url_template.index('&lang=') + 6]

    subtitle_dict = {
        'en': None,
        'langs': {},
        'url': url_template,
    }

    for lang, data in subtitles.items():
        for ext in data:
            if ext.get('ext', None) == 'json3':
                if lang == 'en':
                    subtitle_dict['en'] = ext.get('url', None)

                subtitle_dict['langs'][lang] = ext.get('name', None)
                break

    return subtitle_dict

def round_heatmap(heatmap: list[dict]) -> dict:
    """
    Round all to 2 decimal places
    [{'start_time': float, 'end_time': float, 'value': float}, ...]
    """
    if heatmap is None:
        return heatmap

    return [{'start_time': round(data['start_time'], 2), 'end_time': round(data['end_time'], 2), 'value': round(data['value'], 2)} for data in heatmap]

class GetSource(discord.PCMVolumeTransformer):
    ytdl = yt_dlp.YoutubeDL(YTDL_OPTIONS)

    def __init__(self, glob: GlobalVars, guild_id: int, source: discord.FFmpegPCMAudio):
        super().__init__(source, guild(glob, guild_id).options.volume)

    @classmethod
    async def create_source(cls, glob: GlobalVars, guild_id: int, url: str, source_type: str = 'Video', time_stamp: int=None, video_class=None, attempt: int=0) -> tuple[GetSource, dict]:
        """
        Get source from url

        When the source type is 'Video', the url is a youtube video url
        When the source type is 'SoundCloud', the url is a soundcloud track url
        Other it tries to get the source from the url

        :param glob: GlobalVars
        :param guild_id: int
        :param url: str
        :param video_class: VideoClass child
        :param source_type: str ('Video', 'SoundCloud') - default: 'Video' > anything else for direct url
        :param time_stamp: int - time stamp in seconds
        :param attempt: int - how many times has this function been called

        :return source: discord.FFmpegPCMAudio, additional_data: dict
        """
        source_ffmpeg_options = {
            'before_options': f'{f"-ss {time_stamp} " if time_stamp else ""}-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
            'options': '-vn'
        }
        chapters = None
        heatmap = None
        subtitles = None
        captions = None

        if source_type == 'Video':
            org_url = url
            loop = asyncio.get_event_loop()
            data = await loop.run_in_executor(None, lambda: cls.ytdl.extract_info(url, download=False))

            if 'chapters' in data:
                chapters = data['chapters']

            if 'heatmap' in data:
                heatmap = round_heatmap(data['heatmap'])

            if 'subtitles' in data:
                subtitles = format_subtitles(data['subtitles'], 'subtitles')

            if 'automatic_captions' in data:
                captions = format_subtitles(data['automatic_captions'], 'captions')

            if 'entries' in data:
                data = data['entries'][0]

            url = data['url']
            response, code = await url_checker(url)
            if not response:
                log(guild_id, f'Failed to get source', options={'attempt': attempt, 'org_url': org_url, 'code': code, 'url': url},  log_type='error')
                if attempt >= 5:
                    raise ConnectionRefusedError(f'Failed to get source after 5 attempts: `{org_url}`')
                else:
                    attempt += 1
                    return await cls.create_source(glob, guild_id, org_url, source_type, time_stamp, video_class, attempt)

        if source_type == 'SoundCloud':
            track = glob.sc.resolve(url)
            url = track.get_stream_url()

        if source_type == 'Local':
            source_ffmpeg_options = {
                'before_options': f'{f"-ss {time_stamp} " if time_stamp else ""}',
                'options': '-vn'
            }

        if source_type in ['RadiaCz', 'RadioGarden', 'RadioTuneIn']:
            if not video_class:
                raise ValueError('video_class is required for RadioGarden source')
            url = video_class.radio_info['stream']  # somehow sqlalchemy drops the stream url

        if video_class:
            video_class.stream_url = url

        return cls(glob, guild_id, discord.FFmpegPCMAudio(url, **source_ffmpeg_options)), {'chapters': chapters, 'heatmap': heatmap, 'subtitles': subtitles, 'captions': captions}
