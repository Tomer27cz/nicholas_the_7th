import asyncio
import json
import os
import random
import re
import subprocess
import sys
import threading
import traceback
from os import path, listdir
from time import time, strftime, gmtime
from typing import Literal

import spotipy
import discord
import requests
import youtubesearchpython
import yt_dlp
from bs4 import BeautifulSoup
from discord import FFmpegPCMAudio, app_commands
from discord.ext import commands
from discord.ui import View
from spotipy.oauth2 import SpotifyClientCredentials
from sclib import SoundcloudAPI, Track, Playlist
from flask import Flask, render_template, request, url_for, redirect, session, send_file

import config
from oauth import Oauth

# ---------------- Bot class ------------

class Bot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.all()
        super().__init__(command_prefix=prefix, intents=intents)
        self.synced = False

    async def on_ready(self):
        await self.wait_until_ready()
        if not self.synced:
            log(None, "Trying to sync commands")
            await self.tree.sync()
            log(None, f"Synced slash commands for {self.user}")
        await bot.change_presence(activity=discord.Game(name=f"/help"))
        log(None, f'Logged in as:\n{bot.user.name}\n{bot.user.id}')

    async def on_guild_join(self, guild_object):
        log(guild_object.id, f"Joined guild {guild_object.name} with {guild_object.member_count} members and {len(guild_object.voice_channels)} voice channels")
        guild[guild_object.id] = Guild(guild_object.id)
        save_json()
        text_channels = guild_object.text_channels
        sys_channel = guild_object.system_channel

        message = f"Hello **`{guild_object.name}`**! I am `{self.user.display_name}`. Thank you for inviting me.\n\nTo see what commands I have available type `/help`\n\nIf you have any questions, you can DM my developer <@!{my_id}>#4272"
        if sys_channel is not None:
            if sys_channel.permissions_for(guild_object.me).send_messages:
                await sys_channel.send(message)
                return
        else:
            await text_channels[0].send(message)


    async def on_voice_state_update(self, member, before, after):
        voice_state = member.guild.voice_client
        if voice_state is not None and len(voice_state.channel.members) == 1:
            guild[member.guild.id].options.stopped = True
            voice_state.stop()
            await voice_state.disconnect()
            log(member.guild.id, "-->> Disconnecting when last person left <<--")
            now_to_history(member.guild.id)
        if not member.id == self.user.id:
            return
        elif before.channel is None:
            voice = after.channel.guild.voice_client
            time_var= 0
            while True:
                await asyncio.sleep(1)
                time_var +=  1
                if voice.is_playing() and not voice.is_paused():
                    time_var = 0
                if time_var >= guild[member.guild.id].options.buffer:  # how many seconds of inactivity to disconnect | 300 = 5min | 600 = 10min
                    guild[member.guild.id].options.stopped = True
                    voice.stop()
                    await voice.disconnect()
                    log(member.guild.id, f"-->> Disconnecting after {guild[member.guild.id].options.buffer} seconds of nothing playing <<--")
                    now_to_history(member.guild.id)
                if not voice.is_connected():
                    break

    async def on_command_error(self, ctx, error):
        if isinstance(error, commands.CheckFailure):
            log(ctx, f'Error for ({ctx.author}) -> ({ctx.command}) with error ({error})')
            await ctx.reply("（ ͡° ͜ʖ ͡°)つ━☆・。\n"
                            "⊂　　 ノ 　　　・゜+.\n"
                            "　しーＪ　　　°。+ ´¨)\n"
                            "　　　　　　　　　.· ´¸.·´¨) ¸.·*¨)\n"
                            "　　　　　　　　　　(¸.·´ (¸.·' ☆ **Fuck off**\n"
                            "*You don't have permission to use this command*")
        else:
            log(ctx, f"{error}")
            await ctx.reply(f"{error}   {bot.get_user(my_id).mention}", ephemeral=True)

    async def on_message(self, message):
        if message.author == bot.user:
            return
        if not message.guild:
            try:
                await message.channel.send(f"I'm sorry, but I only work in servers.\n\nIf you want me to join your server, you can invite me with this link: {config.INVITE_URL}\n\nIf you have any questions, you can DM my developer <@!{my_id}>#4272")
            except discord.errors.Forbidden:
                pass
        else:
            pass

# ---------------- Data Classes ------------

class WebData:
    """
    Replaces commands.Context when there is None
    """

    def __init__(self, guild_id, author, author_id):
        self.guild_id = guild_id
        self.author = author
        self.author_id = author_id

    async def reply(self, content=None,  **kwargs):
        pass

    async def send(self, content=None, **kwargs):
        pass


class Options:
    """
    Options for each guild
    (data class)
    """
    def __init__(self, guild_id):
        self.id = guild_id
        self.stopped = False
        self.loop = False
        self.is_radio = False
        self.language = 'cs'
        self.response_type = 'short'  # long or short
        self.search_query = 'Never gonna give you up'
        self.buttons = False
        self.volume = 1.0
        self.buffer = 600 # how many seconds of nothing before it disconnects | 600 = 10min
        self.history_length = 10


class GuildData:
    """
    Stores and updates the data for each guild
    """
    def __init__(self, guild_id):
        self.id = guild_id

        guild_object = bot.get_guild(int(guild_id))
        if guild_object:
            self.name = guild_object.name
            self.id = guild_object.id

            random.seed(self.id)
            self.key = ''.join(random.choice('abcdefghijklmnopqrstuvwxyz0123456789') for _ in range(6))

            self.member_count = guild_object.member_count
            self.owner_id = guild_object.owner_id
            self.owner_name = guild_object.owner.name
            self.created_at = guild_object.created_at.strftime("%d/%m/%Y %H:%M:%S")
            self.description = guild_object.description
            self.large = guild_object.large

            if guild_object.icon is not None: self.icon = guild_object.icon.url
            else: self.icon = None

            if guild_object.banner is not None: self.banner = guild_object.banner.url
            else: self.banner = None

            if guild_object.splash is not None: self.splash = guild_object.splash.url
            else: self.splash = None

            if guild_object.discovery_splash is not None: self.discovery_splash = guild_object.discovery_splash.url
            else:self.discovery_splash = None

            if guild_object.voice_channels:
                self.voice_channels = [{'name': channel.name, 'id': channel.id} for channel in guild_object.voice_channels]
            else:
                self.voice_channels = None

        else:
            if 'guild' in globals():
                if guild:
                    if guild_id in guild.keys():
                        if guild[guild_id].data.name is not None:
                            self.name = guild[guild_id].data.name
                            self.id = guild[guild_id].data.id
                            self.key = guild[guild_id].data.key
                            self.member_count = guild[guild_id].data.member_count
                            self.owner_id = guild[guild_id].data.owner_id
                            self.owner_name = guild[guild_id].data.owner_name
                            self.created_at = guild[guild_id].data.created_at
                            self.description = guild[guild_id].data.description
                            self.large = guild[guild_id].data.large
                            self.icon = guild[guild_id].data.icon
                            self.banner = guild[guild_id].data.banner
                            self.splash = guild[guild_id].data.splash
                            self.discovery_splash = guild[guild_id].data.discovery_splash
                            self.voice_channels = guild[guild_id].data.voice_channels
                            return

            self.name = None
            self.id = None
            self.key = None
            self.member_count = None
            self.owner_id = None
            self.owner_name = None
            self.created_at = None
            self.description = None
            self.large = None
            self.icon = None
            self.banner = None
            self.splash = None
            self.discovery_splash = None
            self.voice_channels = None


class Guild:
    """
    Stores all the variables, data classes and lists for each guild
    """
    def __init__(self, guild_id):
        self.id = guild_id
        self.options = Options(guild_id)
        self.queue = []
        self.search_list = []
        self.now_playing = None
        self.history = [VideoClass('Video',
                                      created_at=1000212400,
                                      url='https://www.youtube.com/watch?v=dQw4w9WgXcQ',
                                      author=my_id,
                                      title='Never gonna give you up',
                                      picture='https://img.youtube.com/vi/dQw4w9WgXcQ/default.jpg',
                                      duration='3:33',
                                      channel_name='Rick Astley',
                                      channel_link='https://www.youtube.com/channel/UCuAXFkgsw1L7xaCfnd5JJOw')]
        self.data = GuildData(guild_id)

    def renew(self):
        self.data = GuildData(self.id)

# ----------------- Video Class ----------------

class VideoClass:
    """
    Stores all the data for each video
    Can do, YouTube, SoundCloud, Czech Radios, Url Probes, Local Files and Fake Spotify

    Raises ValueError: If URL is not provided or is incorrect for class_type
    """
    def __init__(self, class_type: str, author, url=None, title=None, picture=None, duration=None, channel_name=None, channel_link=None, radio_name=None, radio_website=None, local_number=None, created_at=None, played_at=None, stopped_at=None):
        self.class_type = class_type
        self.author = author

        self.created_at = created_at
        if created_at is None:
            self.created_at = int(time())

        self.played_at = played_at
        self.stopped_at = stopped_at

        if self.class_type == 'Video':
            if url is None:
                raise ValueError("URL is required")

            self.url = url

            if title is None:
                try:
                    video = youtubesearchpython.Video.getInfo(url)  # mode=ResultMode.json
                except Exception as e:
                    raise ValueError(f"Not a youtube link: {e}")

                if not video:
                    raise ValueError(f"Not a youtube link: {url}")

                self.title = video['title']
                self.picture = 'https://img.youtube.com/vi/' + video['id'] + '/default.jpg'
                self.duration = video['duration']['secondsText']
                self.channel_name = video['channel']['name']
                self.channel_link = video['channel']['link']

            else:
                self.title = title
                self.picture = picture
                self.duration = duration
                self.channel_name = channel_name
                self.channel_link = channel_link

            self.radio_name = None
            self.radio_website = None
            self.local_number = None

        elif self.class_type == 'Radio':
            if radio_name is None:
                raise ValueError("Radio name required")

            self.radio_name = radio_name

            if title is None:
                self.url = radio_dict[radio_name]['url']
                self.title = radio_dict[radio_name]['name']
                self.picture = radio_dict[radio_name]['thumbnail']
                self.duration = 'Stream'
                self.channel_name = radio_dict[radio_name]['type']
                self.channel_link = self.url
                self.radio_website = radio_dict[radio_name]['type']


            else:
                self.url = url
                self.title = title
                self.picture = picture
                self.duration = duration
                self.channel_name = channel_name
                self.channel_link = channel_link
                self.radio_website = radio_website

            self.local_number = None

        elif self.class_type == 'Local':
            if local_number is None:
                raise ValueError("Local number required")

            self.local_number = local_number
            self.url = None
            self.title = title
            self.picture = vlc_logo
            self.duration = duration
            self.channel_name = 'Local File'
            self.channel_link = None
            self.radio_name = None
            self.radio_website = None

        elif self.class_type == 'Probe':
            self.url = url
            self.title = title
            self.picture = picture
            self.duration = duration
            self.channel_name = channel_name
            self.channel_link = channel_link
            self.radio_name = None
            self.radio_website = None
            self.local_number = None

        elif self.class_type == 'SoundCloud':
            if url is None:
                raise ValueError("URL is required")

            self.url = url

            if title is None:
                try:
                    track = sc.resolve(self.url)
                    assert type(track) is Track
                except Exception as e:
                    raise ValueError(f"Not a SoundCloud Track link: {e}")

                if not track:
                    raise ValueError(f"Not a SoundCloud link: {self.url}")

                self.url = track.permalink_url

                self.title = track.title
                self.picture = track.artwork_url
                self.duration = (track.duration * 0.001)
                self.channel_name = track.artist
                self.channel_link = 'https://soundcloud.com/' + track.permalink_url.split('/')[-2]
            else:
                self.title = title
                self.picture = picture
                self.duration = duration
                self.channel_name = channel_name
                self.channel_link = channel_link
            self.radio_name = None
            self.radio_website = None
            self.local_number = None

        else:
            raise ValueError(f"Invalid class type: {class_type}")

    def renew(self):
        if self.class_type == 'Radio':
            if self.radio_website == 'radia_cz':
                html = requests.get(self.url).text
                soup = BeautifulSoup(html, features="lxml")
                data1 = soup.find('div', attrs={'class': 'interpret-image'})
                data2 = soup.find('div', attrs={'class': 'interpret-info'})

                self.picture = data1.find('img')['src']
                self.channel_name = data2.find('div', attrs={'class': 'nazev'}).text.lstrip().rstrip()
                self.title = data2.find('div', attrs={'class': 'song'}).text.lstrip().rstrip()
                self.duration = 'Stream'

            elif self.radio_website == 'actve':
                r = requests.get(self.url).json()
                self.picture = r['coverBase']
                self.channel_name = r['artist']
                self.title = r['title']
                self.duration = 'Stream'

            else:
                raise ValueError("Invalid radio website")
        else:
            pass
        return

# -------- Get SoundEffects ------------

def load_sound_effects():
    # noinspection PyGlobalUndefined
    global all_sound_effects
    all_sound_effects = ["No sound effects found"]
    try:
        all_sound_effects = listdir('sound_effects')
        for file_index, file_val in enumerate(all_sound_effects):
            all_sound_effects[file_index] = all_sound_effects[file_index][:len(file_val) - 4]
    except FileNotFoundError:
        all_sound_effects = ["No sound effects found"]
    log(None, 'Loaded sound_effects folder')

# ----------- TIME ---------------------

def struct_to_time(struct_time, first='date'):
    if type(struct_time) != int:
        try:
            struct_time = int(struct_time)
        except (ValueError, TypeError):
            return struct_time

    if first == 'date':
        return strftime("%d/%m/%Y %H:%M:%S", gmtime(struct_time))

    if first == 'time':
        return strftime("%H:%M:%S %d/%m/%Y", gmtime(struct_time))

    return strftime("%H:%M:%S %d/%m/%Y", gmtime(struct_time))

# ------------ PRINT --------------------

def log(ctx, text_data, options=None, log_type='text', author=None):
    now_time_str = struct_to_time(time())

    if type(ctx) == commands.Context:
        guild_id = ctx.guild.id
    elif type(ctx) == WebData:
        guild_id = ctx.guild_id
    else:
        guild_id = ctx

    if log_type == 'command':
        message = f"{now_time_str} | C {guild_id} | Command ({text_data}) was requested by ({author}) -> {options}"
    elif log_type == 'function':
        message = f"{now_time_str} | F {guild_id} | {text_data} -> {options}"
    elif log_type == 'web':
        message = f"{now_time_str} | W {guild_id} | Command ({text_data}) was requested by ({author}) -> {options}"
    elif log_type == 'text':
        message = f"{now_time_str} | T {guild_id} | {text_data}"
    elif log_type == 'ip':
        message = f"{now_time_str} | I {guild_id} | Requested: {text_data}"
    else:
        raise ValueError('Wrong log_type')

    print(message)

    with open("log/log.txt", "a", encoding="utf-8") as f:
        f.write(message + "\n")

def collect_data(data):
    now_time_str = struct_to_time(time())
    message = f"{now_time_str} | {data}\n"

    with open("log/data.txt", "a", encoding="utf-8") as f:
        f.write(message)

# ---------------------------------------------- GUILD TO JSON ---------------------------------------------------------

def guild_to_json(guild_object):
    guild_dict = {}
    search_dict = {}
    queue_dict = {}
    history_dict = {}

    if guild_object.search_list:
        for index, video in enumerate(guild_object.search_list):
            search_dict[index] = video.__dict__

    if guild_object.queue:
        for index, video in enumerate(guild_object.queue):
            queue_dict[index] = video.__dict__

    if guild_object.history:
        for index, video in enumerate(guild_object.history):
            history_dict[index] = video.__dict__

    guild_dict['id'] = guild_object.id
    guild_dict['options'] = guild_object.options.__dict__
    guild_dict['data'] = GuildData(guild_object.id).__dict__
    guild_dict['queue'] = queue_dict
    guild_dict['search_list'] = search_dict
    guild_dict['history'] = history_dict
    if guild_object.now_playing:
        guild_dict['now_playing'] = guild_object.now_playing.__dict__
    else:
        guild_dict['now_playing'] = {}

    return guild_dict

def guilds_to_json(guild_dict):
    guilds_dict = {}
    for guild_id, guilds_object in guild_dict.items():
        guilds_dict[int(guild_id)] = guild_to_json(guilds_object)
    return guilds_dict

# ---------------------------------------------- JSON TO GUILD ---------------------------------------------------------

def json_to_video(video_dict):
    if not video_dict:
        return None

    class_type = video_dict['class_type']

    if class_type not in ['Video', 'Radio', 'Local', 'Probe', 'SoundCloud']:
        raise ValueError('Wrong class_type')

    video = VideoClass(class_type,
                       created_at=video_dict['created_at'],
                       played_at=video_dict['played_at'],
                       stopped_at=video_dict['stopped_at'],
                       url=video_dict['url'],
                       author=video_dict['author'],
                       title=video_dict['title'],
                       picture=video_dict['picture'],
                       duration=video_dict['duration'],
                       channel_name=video_dict['channel_name'],
                       channel_link=video_dict['channel_link'],
                       radio_name=video_dict['radio_name'],
                       radio_website=video_dict['radio_website'],
                       local_number=video_dict['local_number'])

    return video

def json_to_guild(guild_dict):
    guild_object = Guild(guild_dict['id'])
    guild_object.options.__dict__ = guild_dict['options']
    guild_object.data.__dict__ = guild_dict['data']
    guild_object.queue = [json_to_video(video_dict) for video_dict in guild_dict['queue'].values()]
    guild_object.search_list = [json_to_video(video_dict) for video_dict in guild_dict['search_list'].values()]
    guild_object.history = [json_to_video(video_dict) for video_dict in guild_dict['history'].values()]
    guild_object.now_playing = json_to_video(guild_dict['now_playing'])

    return guild_object

def json_to_guilds(guilds_dict):
    guilds_object = {}
    for guild_id, guild_dict in guilds_dict.items():
        guilds_object[int(guild_id)] = json_to_guild(guild_dict)

    return guilds_object

# ---------------------------------------------- LOAD -------------------------------------------------------------
log(None, "--------------------------------------- NEW / REBOOTED ----------------------------------------")

build_new_guilds = False

with open('src/radio.json', 'r') as file:
    radio_dict = json.load(file)
log(None, 'Loaded radio.json')


with open('src/languages.json', 'r') as file:
    languages_dict = json.load(file)
    text = languages_dict['en']
log(None, 'Loaded languages.json')


with open('src/other.json', 'r') as file:
    other = json.load(file)
    react_dict = other['reactions']
    prefix = other['prefix']
    my_id = other['my_id']
    bot_id = other['bot_id']
    vlc_logo = other['logo']
    authorized_users = other['authorized']
log(None, 'Loaded other.json')


# ---------------------------------------------- BOT -------------------------------------------------------------------

bot = Bot()

log(None, 'Discord API initialized')

# ---------------------------------------------- SPOTIPY ---------------------------------------------------------------

credentials = SpotifyClientCredentials(client_id=config.SPOTIPY_CLIENT_ID, client_secret=config.SPOTIPY_CLIENT_SECRET)
sp = spotipy.Spotify(client_credentials_manager=credentials)

log(None, 'Spotify API initialized')

# --------------------------------------------- SOUNDCLOUD -------------------------------------------------------------

sc = SoundcloudAPI(client_id=config.SOUNDCLOUD_CLIENT_ID)

log(None, 'SoundCloud API initialized')

# ----------------------------------------------------------------------------------------------------------------------


if build_new_guilds:
    log(None, 'Building new guilds.json ...')
    with open('src/guilds.json', 'r') as file:
        jf = json.load(file)
    guild = dict(zip(jf.keys(), [Guild(int(guild)) for guild in jf.keys()]))

    try:
        json = json.dumps(guilds_to_json(guild), indent=4)
    except Exception as ex:
        print("something failed, figure it out")
        print(ex)
        exit(0)
    with open('src/guilds.json', 'w') as file:
        file.write(json)
    exit(0)


with open('src/guilds.json', 'r') as file:
    guild = json_to_guilds(json.load(file))
log(None, 'Loaded guilds.json')


all_sound_effects = ["No sound effects found"]
load_sound_effects()


# ---------------------------------------------- SAVE JSON -------------------------------------------------------------

def save_json():
    for guild_object in guild.values():
        guild_object.renew()

    with open('src/guilds.json', 'w') as f:
        json.dump(guilds_to_json(guild), f, indent=4)

# ---------------------------------------------- TEXT ----------------------------------------------------------

def tg(guild_id, content):
    lang = guild[guild_id].options.language
    try:
        to_return = languages_dict[lang][content]
    except KeyError:
        log(None, f'KeyError: {content} in {lang}')
        to_return = content
    return to_return

# ---------------------------------------------- SPOTIFY -------------------------------------------------------

def spotify_to_yt_video(spotify_url, author):
    # noinspection PyBroadException
    try:
        spotify_track = sp.track(spotify_url)
    except Exception:
        return None

    title = spotify_track['name']
    artist = spotify_track['artists'][0]['name']
    search_query = f"{title} {artist}"

    custom_search = youtubesearchpython.VideosSearch(search_query, limit=1)

    if not custom_search.result()['result']:
        return None

    video = custom_search.result()['result'][0]

    yt_url = video['link']
    yt_title = video['title']
    yt_picture = 'https://img.youtube.com/vi/' + video['id'] + '/default.jpg'
    yt_duration = video['duration']
    yt_channel_name = video['channel']['name']
    yt_channel_link = video['channel']['link']

    video_class = VideoClass('Video', author, url=yt_url, title=yt_title, picture=yt_picture, duration=yt_duration, channel_name=yt_channel_name, channel_link=yt_channel_link)

    return video_class

def spotify_playlist_to_yt_video_list(spotify_playlist_url, author):
    # noinspection PyBroadException
    try:
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

        video = custom_search.result()['result'][0]

        yt_url = video['link']
        yt_title = video['title']
        yt_picture = 'https://img.youtube.com/vi/' + video['id'] + '/default.jpg'
        yt_duration = video['duration']
        yt_channel_name = video['channel']['name']
        yt_channel_link = video['channel']['link']

        video_class = VideoClass('Video', author, url=yt_url, title=yt_title, picture=yt_picture, duration=yt_duration, channel_name=yt_channel_name, channel_link=yt_channel_link)

        video_list.append(video_class)

    return video_list

def spotify_album_to_yt_video_list(spotify_album_url, author):
    # noinspection PyBroadException
    try:
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

        video = custom_search.result()['result'][0]

        yt_url = video['link']
        yt_title = video['title']
        yt_picture = 'https://img.youtube.com/vi/' + video['id'] + '/default.jpg'
        yt_duration = video['duration']
        yt_channel_name = video['channel']['name']
        yt_channel_link = video['channel']['link']

        video_class = VideoClass('Video', author, url=yt_url, title=yt_title, picture=yt_picture, duration=yt_duration, channel_name=yt_channel_name, channel_link=yt_channel_link)

        video_list.append(video_class)

    return video_list

# ---------------------------------------------- YOUTUBE -------------------------------------------------------

def extract_yt_id(url_string: str):
    magic_regex = "^(?:https?://|//)?(?:www\.|m\.|.+\.)?(?:youtu\.be/|youtube\.com/(?:embed/|v/|shorts/|feeds/api/videos/|watch\?v=|watch\?.+&v=))([\w-]{11})(?![\w-])"
    regex = re.compile(magic_regex)
    results = regex.search(url_string)

    if results is None:
        return None
    return results.group(1)

def get_playlist_from_url(url: str):
    try:
        code = url[url.index('&list=')+1:url.index('&index=')]
    except ValueError:
        code = url[url.index('&list=')+1:]
    playlist_url = 'https://www.youtube.com/playlist?' + code
    return playlist_url

# ---------------------------------------------- URL -----------------------------------------------------------

def get_url_of(string: str, section: str):
    separated_string = string.split(' ')

    for s_string in separated_string:
        if section in s_string:
            return get_first_url(s_string)

    return None

def get_first_url(string: str):
    re_search = re.search(r"(http|ftp|https)://([\w_-]+(?:\.[\w_-]+)+)([\w.,@?^=%&:/~+#-]*[\w@?^=%&/~+#-])", string)
    if re_search is None:
        return None
    return re_search[0]

def get_url_type(string: str):
    first_url = get_first_url(string)
    yt_id = extract_yt_id(string)

    if '/playlist?list=' in string:
        extracted_url = get_url_of(string, '/playlist?list=')
        if extracted_url is None:
            return 'String', string
        return 'YouTube Playlist', extracted_url

    if any(param in string for param in {'index=', 'list='}):
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

    if first_url is not None:
        return 'String with URL', first_url

    return 'String', string

# ---------------------------------------------- PROBE ---------------------------------------------------------

async def get_url_probe_data(url: str):
    extracted_url = get_first_url(url)
    if extracted_url is None:
        return None, extracted_url

    # noinspection PyBroadException
    try:
        executable = 'ffmpeg'
        exe = executable[:2] + 'probe' if executable in ('ffmpeg', 'avconv') else executable
        args = [exe, '-v', 'quiet', '-print_format', 'json', '-show_streams', '-select_streams', 'a:0', extracted_url]
        output = subprocess.check_output(args, timeout=20)
        codec = bitrate = None

        if output:
            data = json.loads(output)
            streamdata = data['streams'][0]

            codec = streamdata.get('codec_name')
            bitrate = int(streamdata.get('bit_rate', 0))
            bitrate = max(round(bitrate / 1000), 512)

    except:
        codec, bitrate = None, None

    if codec and bitrate:
        return (codec, bitrate), extracted_url

    return None, extracted_url

# ---------------------------------------------- CONVERT -------------------------------------------------------

def convert_duration(duration):
    try:
        if duration is None or duration == 0 or duration == '0':
            return 'Stream'
        seconds = int(duration) % (24 * 3600)
        hour = seconds // 3600
        seconds %= 3600
        minutes = seconds // 60
        seconds %= 60
        if hour:
            if not minutes:
                minutes = 00
            if not seconds:
                seconds = 00
            return "%d:%02d:%02d" % (hour, minutes, seconds)
        if not hour:
            if not minutes:
                minutes = 00
            if not seconds:
                seconds = 00
            return "%02d:%02d" % (minutes, seconds)
    except (ValueError, TypeError):
        return duration

# ---------------------------------------------- GET -----------------------------------------------------------

def get_username(user_id: int):
    # noinspection PyBroadException
    try:
        return bot.get_user(int(user_id)).name
    except:
        return user_id

def get_content_of_message(message: discord.Message):
    if message.attachments:
        url = message.attachments[0].url
        filename = message.attachments[0].filename
        message_author = f"Message by {get_username(message.author.id)}"
        message_link = message.jump_url
        probe_data = [filename, message_author, message_link]
    elif message.embeds:
        if message.content:
            url = message.content
            probe_data = None
        else:
            embed = message.embeds[0]
            embed_dict = embed.to_dict()
            embed_dict.pop('thumbnail')
            embed_str = str(embed_dict)
            url = embed_str
            probe_data = None
    else:
        url = message.content
        probe_data = None

    return url, probe_data

# ---------------------------------------------- CHECK ---------------------------------------------------------

def to_bool(text_bool):
    bool_list_t = ['True', 'true', '1']
    bool_list_f = ['False', 'false', '0']

    if text_bool in bool_list_t:
        return True
    elif text_bool in bool_list_f:
        return False
    else:
        return None

def is_float(value):
  if value is None:
      return False
  # noinspection PyBroadException
  try:
      float(value)
      return True
  except:
      return False

# ---------------------------------------------- DISCORD -------------------------------------------------------

def create_embed(video, name, guild_id):
    embed = (discord.Embed(title=name, description=f'```\n{video.title}\n```', color=discord.Color.blurple()))
    embed.add_field(name=tg(guild_id, 'Duration'), value=convert_duration(video.duration))

    try:
        embed.add_field(name=tg(guild_id, 'Requested by'), value=bot.get_user(video.author).mention)
    except AttributeError:
        embed.add_field(name=tg(guild_id, 'Requested by'), value=video.author)

    embed.add_field(name=tg(guild_id, 'Author'), value=f'[{video.channel_name}]({video.channel_link})')
    embed.add_field(name=tg(guild_id, 'URL'), value=f'[{video.url}]({video.url})')
    embed.set_thumbnail(url=video.picture)
    embed.set_footer(text=f'Requested at {struct_to_time(video.created_at, "time")}')

    return embed

def now_to_history(guild_id: int):
    if guild[guild_id].now_playing is not None:
        if len(guild[guild_id].history) >= guild[guild_id].options.history_length:
            while len(guild[guild_id].history) >= guild[guild_id].options.history_length:
                guild[guild_id].history.pop(0)

        guild[guild_id].now_playing.stopped_at = int(time())
        guild[guild_id].history.append(guild[guild_id].now_playing)
        guild[guild_id].now_playing = None
        save_json()

async def to_queue(guild_id: int, video: VideoClass, position: int = None, ctx=None, mute_response: bool=False, ephemeral: bool=False, return_message: bool=False):
    if position is None:
        guild[guild_id].queue.append(video)
    else:
        guild[guild_id].queue.insert(position, video)

    save_json()

    if return_message:
        message = f'[`{video.title}`](<{video.url}>) {tg(guild_id, "added to queue!")} -> [Control Panel]({config.WEB_URL}/guild/{guild_id}&key={guild[guild_id].data.key})'
        if not mute_response:
            await ctx.reply(message, ephemeral=ephemeral)
        return [True, message, video]


# ---------------------------------------------- SOURCE -------------------------------------------------------

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

class GetSource(discord.PCMVolumeTransformer):
    """
    Get source from url

    When the source type is 'Video', the url is a youtube video url
    When the source type is 'SoundCloud', the url is a soundcloud track url
    Other it tries to get the source from the url

    :param guild_id: int
    :param url: str
    :param source_type: str ('Video', 'SoundCloud') - default: 'Video'

    :return source: discord.FFmpegPCMAudio
    """
    ytdl = yt_dlp.YoutubeDL(YTDL_OPTIONS)

    def __init__(self, guild_id: int, source: discord.FFmpegPCMAudio):
        super().__init__(source, guild[guild_id].options.volume)

    @classmethod
    async def create_source(cls, guild_id: int, url: str, source_type: str='Video'):
        if source_type == 'Video':
            loop = asyncio.get_event_loop()
            data = await loop.run_in_executor(None, lambda: cls.ytdl.extract_info(url, download=False))

            if 'entries' in data:
                data = data['entries'][0]

            url = data['url']

        if source_type == 'SoundCloud':
            track = sc.resolve(url)
            url = track.get_stream_url()

        return cls(guild_id, discord.FFmpegPCMAudio(url, **FFMPEG_OPTIONS))

# ------------------------------------ View Classes --------------------------------------------------------------------

class PlayerControlView(View):

    def __init__(self, ctx):
        super().__init__(timeout=7200)
        if type(ctx) == commands.Context:
            self.guild = ctx.guild
            self.guild_id = ctx.guild.id

    @discord.ui.button(emoji=react_dict['play'], style=discord.ButtonStyle.blurple, custom_id='play')
    async def callback(self, interaction, button):
        voice = discord.utils.get(bot.voice_clients, guild=self.guild)
        if voice:
            if voice.is_paused():
                voice.resume()
                # noinspection PyUnresolvedReferences
                pause_button = [x for x in self.children if x.custom_id == 'pause'][0]
                pause_button.style = discord.ButtonStyle.blurple
                button.style = discord.ButtonStyle.grey
                await interaction.response.edit_message(view=self)
            elif voice.is_playing():
                await interaction.response.send_message(tg(self.guild_id, "Player **already resumed!**"),
                                                        ephemeral=True)
            else:
                await interaction.response.send_message(tg(self.guild_id, "No audio playing"), ephemeral=True)
        else:
            await interaction.response.send_message(tg(self.guild_id, "No audio"), ephemeral=True)

    @discord.ui.button(emoji=react_dict['pause'], style=discord.ButtonStyle.blurple, custom_id='pause')
    async def pause_callback(self, interaction, button):
        voice = discord.utils.get(bot.voice_clients, guild=self.guild)
        if voice:
            if voice.is_playing():
                voice.pause()
                # noinspection PyUnresolvedReferences
                play_button = [x for x in self.children if x.custom_id == 'play'][0]
                play_button.style = discord.ButtonStyle.blurple
                button.style = discord.ButtonStyle.grey
                await interaction.response.edit_message(view=self)
            elif voice.is_paused():
                await interaction.response.send_message(tg(self.guild_id, "Player **already paused!**"),
                                                        ephemeral=True)
            else:
                await interaction.response.send_message(tg(self.guild_id, "No audio playing"), ephemeral=True)
        else:
            await interaction.response.send_message(tg(self.guild_id, "No audio"), ephemeral=True)

    # noinspection PyUnusedLocal
    @discord.ui.button(emoji=react_dict['stop'], style=discord.ButtonStyle.red, custom_id='stop')
    async def stop_callback(self, interaction, button):
        voice = discord.utils.get(bot.voice_clients, guild=self.guild)
        if voice:
            if voice.is_playing() or voice.is_paused():
                voice.stop()
                guild[interaction.guild_id].options.stopped = True
                await interaction.response.edit_message(view=None)
            else:
                await interaction.response.send_message(tg(self.guild_id, "No audio playing"), ephemeral=True)
        else:
            await interaction.response.send_message(tg(self.guild_id, "No audio"), ephemeral=True)

class SearchOptionView(View):

    def __init__(self, ctx, force=False, from_play=False):
        super().__init__(timeout=180)

        if type(ctx) == commands.Context:
            self.ctx = ctx
            self.guild = ctx.guild
            self.guild_id = ctx.guild.id
            self.force = force
            self.from_play = from_play

    # noinspection PyUnusedLocal
    @discord.ui.button(emoji=react_dict['1'], style=discord.ButtonStyle.blurple, custom_id='1')
    async def callback_1(self, interaction, button):
        video = guild[self.guild_id].search_list[0]
        if self.force:
            guild[self.guild_id].queue.insert(0, video)
        else:
            guild[self.guild_id].queue.append(video)
        save_json()
        await interaction.response.edit_message(content=f'[`{video.title}`](<{video.url}>) '
                                                        f'{tg(self.guild_id, "added to queue!")}', view=None)
        if self.from_play:
            await play_def(self.ctx)

    # noinspection PyUnusedLocal
    @discord.ui.button(emoji=react_dict['2'], style=discord.ButtonStyle.blurple, custom_id='2')
    async def callback_2(self, interaction, button):
        video = guild[self.guild_id].search_list[1]
        if self.force:
            guild[self.guild_id].queue.insert(0, video)
        else:
            guild[self.guild_id].queue.append(video)
        save_json()
        await interaction.response.edit_message(content=f'[`{video.title}`](<{video.url}>) '
                                                        f'{tg(self.guild_id, "added to queue!")}', view=None)
        if self.from_play:
            await play_def(self.ctx)

    # noinspection PyUnusedLocal
    @discord.ui.button(emoji=react_dict['3'], style=discord.ButtonStyle.blurple, custom_id='3')
    async def callback_3(self, interaction, button):
        video = guild[self.guild_id].search_list[2]
        if self.force:
            guild[self.guild_id].queue.insert(0, video)
        else:
            guild[self.guild_id].queue.append(video)
        save_json()
        await interaction.response.edit_message(content=f'[`{video.title}`](<{video.url}>) '
                                                        f'{tg(self.guild_id, "added to queue!")}', view=None)
        if self.from_play:
            await play_def(self.ctx)

    # noinspection PyUnusedLocal
    @discord.ui.button(emoji=react_dict['4'], style=discord.ButtonStyle.blurple, custom_id='4')
    async def callback_4(self, interaction, button):
        video = guild[self.guild_id].search_list[3]
        if self.force:
            guild[self.guild_id].queue.insert(0, video)
        else:
            guild[self.guild_id].queue.append(video)
        save_json()
        await interaction.response.edit_message(content=f'[`{video.title}`](<{video.url}>) '
                                                        f'{tg(self.guild_id, "added to queue!")}', view=None)
        if self.from_play:
            await play_def(self.ctx)

    # noinspection PyUnusedLocal
    @discord.ui.button(emoji=react_dict['5'], style=discord.ButtonStyle.blurple, custom_id='5')
    async def callback_5(self, interaction, button):
        video = guild[self.guild_id].search_list[4]
        if self.force:
            guild[self.guild_id].queue.insert(0, video)
        else:
            guild[self.guild_id].queue.append(video)
        save_json()
        await interaction.response.edit_message(content=f'[`{video.title}`](<{video.url}>) '
                                                        f'{tg(self.guild_id, "added to queue!")}', view=None)
        if self.from_play:
            await play_def(self.ctx)

class PlaylistOptionView(View):
    def __init__(self, ctx, url, force=False, from_play=False):
        super().__init__(timeout=180)

        if type(ctx) == commands.Context:
            self.ctx = ctx
            self.url = url
            self.guild = ctx.guild
            self.guild_id = ctx.guild.id
            self.force = force
            self.from_play = from_play

    # noinspection PyUnusedLocal
    @discord.ui.button(label='Yes', style=discord.ButtonStyle.blurple)
    async def callback_1(self, interaction, button):
        playlist_url = get_playlist_from_url(self.url)
        await interaction.response.edit_message(content=tg(self.guild_id, "Adding playlist to queue..."), view=None)
        if self.force:
            response = await queue_command_def(self.ctx, playlist_url, position=0, mute_response=True, force=self.force)
        else:
            response = await queue_command_def(self.ctx, playlist_url, mute_response=True, force=self.force)

        msg = await interaction.original_response()
        await msg.edit(content=response[1])

        if self.from_play:
            await play_def(self.ctx)

    # noinspection PyUnusedLocal
    @discord.ui.button(label='No, just this', style=discord.ButtonStyle.blurple)
    async def callback_2(self, interaction, button):
        pure_url = self.url[:self.url.index('&list=')]
        if self.force:
            response = await queue_command_def(self.ctx, pure_url, position=0, mute_response=True, force=self.force)
        else:
            response = await queue_command_def(self.ctx, pure_url, mute_response=True, force=self.force)
        await interaction.response.edit_message(content=response[1], view=None)
        if self.from_play:
            await play_def(self.ctx)

# --------------------------------------- QUEUE --------------------------------------------------

@bot.hybrid_command(name='queue', with_app_command=True, description=text['queue_add'], help=text['queue_add'])
@app_commands.describe(url=text['url'], position=text['pos'])
async def queue_command(ctx: commands.Context, url, position: int = None):
    log(ctx, 'queue', [url, position], log_type='command', author=ctx.author)

    await queue_command_def(ctx, url, position=position)

@bot.hybrid_command(name='next_up', with_app_command=True, description=text['next_up'], help=text['next_up'])
@app_commands.describe(url=text['url'], user_only=text['ephemeral'])
async def next_up(ctx: commands.Context, url, user_only: bool = False):
    log(ctx, 'next_up', [url, user_only], log_type='command', author=ctx.author)

    await next_up_def(ctx, url, user_only)

@bot.hybrid_command(name='skip', with_app_command=True, description=text['skip'], help=text['skip'])
async def skip(ctx: commands.Context):
    log(ctx, 'skip', [], log_type='command', author=ctx.author)

    await skip_def(ctx)

@bot.hybrid_command(name='remove', with_app_command=True, description=text['queue_remove'], help=text['queue_remove'])
@app_commands.describe(number=text['number'], user_only=text['ephemeral'])
async def remove(ctx: commands.Context, number: int, user_only: bool = False):
    log(ctx, 'remove', [number, user_only], log_type='command', author=ctx.author)

    await remove_def(ctx, number, ephemeral=user_only)

@bot.hybrid_command(name='clear', with_app_command=True, description=text['clear'], help=text['clear'])
@app_commands.describe(user_only=text['ephemeral'])
async def clear(ctx: commands.Context, user_only: bool = False):
    log(ctx, 'clear', [user_only], log_type='command', author=ctx.author)

    await clear_def(ctx, user_only)

@bot.hybrid_command(name='shuffle', with_app_command=True, description=text['shuffle'], help=text['shuffle'])
@app_commands.describe(user_only=text['ephemeral'])
async def shuffle(ctx: commands.Context, user_only: bool = False):
    log(ctx, 'shuffle', [user_only], log_type='command', author=ctx.author)

    await shuffle_def(ctx, user_only)

@bot.hybrid_command(name='show', with_app_command=True, description=text['queue_show'], help=text['queue_show'])
@app_commands.describe(display_type=text['display_type'], user_only=text['ephemeral'])
async def show(ctx: commands.Context, display_type: Literal['short', 'medium', 'long'] = None, list_type: Literal['queue', 'history']='queue', user_only: bool = False):
    log(ctx, 'show', [display_type, user_only], log_type='command', author=ctx.author)

    await show_def(ctx, display_type, list_type, user_only)

@bot.hybrid_command(name='search', with_app_command=True, description=text['search'],  help=text['search'])
@app_commands.describe(search_query=text['search_query'])
async def search_command(ctx: commands.Context, search_query):
    log(ctx, 'search', [search_query], log_type='command', author=ctx.author)

    await search_command_def(ctx, search_query)

# --------------------------------------- PLAYER --------------------------------------------------

@bot.hybrid_command(name='play', with_app_command=True, description=text['play'], help=text['play'])
@app_commands.describe(url=text['play'], force=text['force'])
async def play(ctx: commands.Context, url=None, force=False):
    log(ctx, 'play', [url, force], log_type='command', author=ctx.author)

    await play_def(ctx, url, force)

@bot.hybrid_command(name='radio', with_app_command=True, description=text['radio'], help=text['radio'])
@app_commands.describe(favourite_radio=text['favourite_radio'], radio_code=text['radio_code'])
async def radio(ctx: commands.Context, favourite_radio: Literal['Rádio BLANÍK','Rádio BLANÍK CZ','Evropa 2','Fajn Radio','Hitrádio PopRock','Český rozhlas Pardubice','Radio Beat','Country Radio','Radio Kiss','Český rozhlas Vltava','Hitrádio Černá Hora'] = None, radio_code: int = None):
    log(ctx, 'radio', [favourite_radio, radio_code], log_type='command', author=ctx.author)

    await radio_def(ctx, favourite_radio, radio_code)

@bot.hybrid_command(name='ps', with_app_command=True, description=text['ps'], help=text['ps'])
@app_commands.describe(effect_number=text['effects_number'])
async def ps(ctx: commands.Context, effect_number: app_commands.Range[int, 1, len(all_sound_effects)]):
    log(ctx, 'ps', [effect_number], log_type='command', author=ctx.author)

    await ps_def(ctx, effect_number)

@bot.hybrid_command(name='nowplaying', with_app_command=True, description=text['nowplaying'], help=text['nowplaying'])
@app_commands.describe(user_only=text['ephemeral'])
async def nowplaying(ctx: commands.Context, user_only: bool = False):
    log(ctx, 'nowplaying', [user_only], log_type='command', author=ctx.author)

    await now_def(ctx, user_only)

@bot.hybrid_command(name='last', with_app_command=True, description=text['last'], help=text['last'])
@app_commands.describe(user_only=text['ephemeral'])
async def last(ctx: commands.Context, user_only: bool = False):
    log(ctx, 'last', [user_only], log_type='command', author=ctx.author)

    await last_def(ctx, user_only)

@bot.hybrid_command(name='loop', with_app_command=True, description=text['loop'], help=text['loop'])
async def loop_command(ctx: commands.Context):
    log(ctx, 'loop', [], log_type='command', author=ctx.author)

    await loop_command_def(ctx)

@bot.hybrid_command(name='loop_this', with_app_command=True, description=text['loop_this'], help=text['loop_this'])
async def loop_this(ctx: commands.Context):
    log(ctx, 'loop_this', [], log_type='command', author=ctx.author)

    await loop_this_def(ctx)

# --------------------------------------- VOICE --------------------------------------------------

@bot.hybrid_command(name='stop', with_app_command=True, description=f'Stop the player')
async def stop(ctx: commands.Context):
    log(ctx, 'stop', [], log_type='command', author=ctx.author)

    await stop_def(ctx)

@bot.hybrid_command(name='pause', with_app_command=True, description=f'Pause the player')
async def pause(ctx: commands.Context):
    log(ctx, 'pause', [], log_type='command', author=ctx.author)

    await pause_def(ctx)

@bot.hybrid_command(name='resume', with_app_command=True, description=f'Resume the player')
async def resume(ctx: commands.Context):
    log(ctx, 'resume', [], log_type='command', author=ctx.author)

    await resume_def(ctx)

@bot.hybrid_command(name='join', with_app_command=True, description=text['join'], help=text['join'])
@app_commands.describe(channel_id=text['channel_id'])
async def join(ctx: commands.Context, channel_id=None):
    log(ctx, 'join', [channel_id], log_type='command', author=ctx.author)

    await join_def(ctx, channel_id)

@bot.hybrid_command(name='disconnect', with_app_command=True, description=text['die'], help=text['die'])
async def disconnect(ctx: commands.Context):
    log(ctx, 'disconnect', [], log_type='command', author=ctx.author)

    await disconnect_def(ctx)

@bot.hybrid_command(name='volume', with_app_command=True, description=text['volume'], help=text['volume'])
@app_commands.describe(volume=text['volume'], user_only=text['ephemeral'])
async def volume_command(ctx: commands.Context, volume = None, user_only: bool = False):
    log(ctx, 'volume', [volume, user_only], log_type='command', author=ctx.author)

    await volume_command_def(ctx, volume, user_only)

# --------------------------------------- MENU --------------------------------------------------

@bot.tree.context_menu(name='Play now')
async def play_now(inter, message: discord.Message):
    ctx = await bot.get_context(inter)
    log(ctx, 'play_now', [message], log_type='command', author=ctx.author)

    if ctx.author.voice is None:
        await inter.response.send_message(content=tg(ctx.guild.id, 'You are **not connected** to a voice channel'), ephemeral=True)
        return

    url, probe_data = get_content_of_message(message)

    response = await queue_command_def(ctx, url, mute_response=True, probe_data=probe_data, ephemeral=True, position=0, from_play=True)
    if response:
        if response[0]:
            await play_def(ctx, force=True)
        else:
            if not inter.response.is_done():
                await inter.response.send_message(content=response[1], ephemeral=True)

@bot.tree.context_menu(name='Add to queue')
async def add_to_queue(inter, message: discord.Message):
    ctx = await bot.get_context(inter)
    log(ctx, 'add_to_queue', [message], log_type='command', author=ctx.author)

    url, probe_data = get_content_of_message(message)

    response = await queue_command_def(ctx, url, mute_response=True, probe_data=probe_data, ephemeral=True)
    if not inter.response.is_done():
        await inter.response.send_message(content=response[1], ephemeral=True)

@bot.tree.context_menu(name='Show Profile')
async def show_profile(inter, member: discord.Member):
    ctx = await bot.get_context(inter)
    log(ctx, 'show_profile', [member], log_type='command', author=ctx.author)

    embed = discord.Embed(title=f"{member.name}#{member.discriminator}", description=f"ID: `{member.id}` | Name: `{member.display_name}` | Nickname: `{member.nick}`")
    embed.add_field(name="Created at", value=member.created_at.strftime("%d/%m/%Y %H:%M:%S"), inline=True)
    embed.add_field(name="Joined at", value=member.joined_at.strftime("%d/%m/%Y %H:%M:%S"), inline=True)

    embed.add_field(name="Roles", value=", ".join([role.mention for role in member.roles[1:]]), inline=False)

    embed.add_field(name='Top Role', value=f'{member.top_role.mention}', inline=True)

    # noinspection PyUnresolvedReferences
    embed.add_field(name='Badges', value=', '.join([badge.name for badge in member.public_flags.all()]), inline=False)

    embed.add_field(name='Avatar', value=f'[Default Avatar]({member.avatar}) | [Display Avatar]({member.display_avatar})', inline=False)

    embed.add_field(name='Activity', value=f'`{member.activity}`', inline=False)

    embed.add_field(name='Activities', value=f'`{member.activities}`', inline=True)
    embed.add_field(name='Status', value=f'`{member.status}`', inline=True)
    embed.add_field(name='Web Status', value=f'`{member.web_status}`', inline=True)

    embed.add_field(name='Raw Status', value=f'`{member.raw_status}`', inline=True)
    embed.add_field(name='Desktop Status', value=f'`{member.desktop_status}`', inline=True)
    embed.add_field(name='Mobile Status', value=f'`{member.mobile_status}`', inline=True)

    embed.add_field(name='Voice', value=f'`{member.voice}`', inline=False)

    embed.add_field(name='Premium Since', value=f'`{member.premium_since}`', inline=False)

    embed.add_field(name='Accent Color', value=f'`{member.accent_color}`', inline=True)
    embed.add_field(name='Color', value=f'`{member.color}`', inline=True)
    embed.add_field(name='Banner', value=f'`{member.banner}`', inline=True)

    embed.add_field(name='System', value=f'`{member.system}`', inline=True)
    embed.add_field(name='Pending', value=f'`{member.pending}`', inline=True)
    embed.add_field(name='Bot', value=f'`{member.bot}`', inline=True)


    embed.set_thumbnail(url=member.avatar)
    await inter.response.send_message(embed=embed, ephemeral=True)

# --------------------------------------- GENERAL --------------------------------------------------

@bot.hybrid_command(name='ping', with_app_command=True, description=text['ping'], help=text['ping'])
async def ping_command(ctx: commands.Context):
    log(ctx, 'ping', [], log_type='command', author=ctx.author)

    await ping_def(ctx)

# noinspection PyTypeHints
@bot.hybrid_command(name='language', with_app_command=True, description=text['language'], help=text['language'])
@app_commands.describe(country_code=text['country_code'])
async def language_command(ctx: commands.Context, country_code: Literal[tuple(languages_dict.keys())]):
    log(ctx, 'language', [country_code], log_type='command', author=ctx.author)

    await language_command_def(ctx, country_code)

@bot.hybrid_command(name='sound_effects', with_app_command=True, description=text['sound'], help=text['sound'])
@app_commands.describe(user_only=text['ephemeral'])
async def sound_effects(ctx: commands.Context, user_only: bool = True):
    log(ctx, 'sound_effects', [user_only], log_type='command', author=ctx.author)

    await sound_effects_def(ctx, user_only)

@bot.hybrid_command(name='list_radios', with_app_command=True, description=text['list_radios'], help=text['list_radios'])
@app_commands.describe(user_only=text['ephemeral'])
async def list_radios(ctx: commands.Context, user_only: bool = True):
    log(ctx, 'list_radios', [user_only], log_type='command', author=ctx.author)

    await list_radios_def(ctx, user_only)

@bot.hybrid_command(name='key', with_app_command=True, description=text['key'], help=text['key'])
async def key_command(ctx: commands.Context):
    log(ctx, 'key', [], log_type='command', author=ctx.author)

    await key_def(ctx)

# ---------------------------------------- ADMIN --------------------------------------------------

async def is_authorised(ctx):
    if ctx.author.id in authorized_users or ctx.author.id == 349164237605568513:
        return True

@bot.hybrid_command(name='zz_announce', with_app_command=True)
@commands.check(is_authorised)
async def announce_command(ctx: commands.Context, message):
    log(ctx, 'announce', [message], log_type='command', author=ctx.author)

    await announce_command_def(ctx, message)

@bot.hybrid_command(name='zz_earrape_play', with_app_command=True)
@commands.check(is_authorised)
async def earrape_play_command(ctx: commands.Context, effect_number: int = None, channel_id = None):
    log(ctx, 'zz_ear_rape_play', [effect_number, channel_id], log_type='command', author=ctx.author)

    await rape_play_command_def(ctx, effect_number, channel_id)

@bot.hybrid_command(name='zz_earrape', with_app_command=True)
@commands.check(is_authorised)
async def earrape_command(ctx: commands.Context):
    log(ctx, 'earrape', [], log_type='command', author=ctx.author)

    await ear_rape_command_def(ctx)

@bot.hybrid_command(name='zz_kys', with_app_command=True)
@commands.check(is_authorised)
async def kys(ctx: commands.Context):
    log(ctx, 'kys', [], log_type='command', author=ctx.author)

    await kys_def(ctx)

@bot.hybrid_command(name='zz_config', with_app_command=True)
@commands.check(is_authorised)
async def config_command(ctx: commands.Context, config_file: discord.Attachment, config_type:  Literal['guilds', 'other', 'radio', 'languages'] = 'guilds'):
    log(ctx, 'config', [config_file, config_type], log_type='command', author=ctx.author)

    await config_command_def(ctx, config_file, config_type)

@bot.hybrid_command(name='zz_log', with_app_command=True)
@commands.check(is_authorised)
async def log_command(ctx: commands.Context, log_type: Literal['log.txt', 'guilds.json', 'other.json', 'radio.json', 'languages.json', 'activity.log', 'data.txt'] = 'log.txt'):
    log(ctx, 'log', [log_type], log_type='command', author=ctx.author)

    await log_command_def(ctx, log_type)

# noinspection PyTypeHints
@bot.hybrid_command(name='zz_change_options', with_app_command=True)
@app_commands.describe(server='all, this, {guild_id}', volume='No division', buffer='In seconds', language='Language code', response_type='short, long', buttons='True, False', is_radio='True, False', loop='True, False', stopped='True, False', history_length='Number of items in history (100 is probably a lot)')
@commands.check(is_authorised)
async def change_options(ctx: commands.Context,
                        stopped: bool = None,
                        loop: bool = None,
                        is_radio: bool = None,
                        buttons: bool = None,
                        language: Literal[tuple(languages_dict.keys())] = None,
                        response_type: Literal['short', 'long'] = None,
                        buffer: int = None,
                        history_length: int = None,
                        volume = None,
                        server = None,
                        ):
    log(ctx, 'zz_change_options', [stopped, loop, is_radio, buttons, language, response_type, buffer, history_length, volume, server], log_type='command', author=ctx.author)

    await change_options_def(ctx, stopped, loop, is_radio, buttons, language, response_type, buffer, history_length, volume, server)

# --------------------------------------------- COMMAND FUNCTIONS ------------------------------------------------------

def ctx_check(ctx):
    if type(ctx) == commands.Context:
        return True, ctx.guild.id, ctx.author.id, ctx.guild
    else:
        return False, ctx.guild_id, ctx.author_id, bot.get_guild(ctx.guild_id)

# --------------------------------------- QUEUE --------------------------------------------------

async def queue_command_def(ctx,
                            url=None,
                            position: int = None,
                            mute_response: bool = False,
                            force: bool = False,
                            from_play: bool = False,
                            probe_data: list = None,
                            no_search: bool = False,
                            ephemeral: bool = False,
                            ):
    """
    This function tries to queue a song. It is called by the queue command and the play command.

    :param ctx: Context
    :param url: An input string that is either a URL or a search query
    :param position: An integer that represents the position in the queue to insert the song
    :param mute_response: Whether to mute the response or not
    :param force: Whether to force the song to play or not
    :param from_play: Set to True if the command is being called from the play command
    :param probe_data: Data from the probe command
    :param no_search: Whether to search for the song or not when the URL is not a URL
    :param ephemeral: Should the response be ephemeral
    :return: [bool, str, VideoClass or None] - Whether the command was successful, the response message, and the VideoClass object or None
    """

    log(ctx, 'queue_command_def', [url, position, mute_response, force, from_play, probe_data, no_search, ephemeral], log_type='function', author=ctx.author)
    is_ctx, guild_id, author_id, guild_object = ctx_check(ctx)

    if not url:
        message = tg(guild_id, "`url` is **required**")
        if not mute_response:
            await ctx.reply(message, ephemeral=True)
        return [False, message]

    url_type, url = get_url_type(url)
    yt_id = extract_yt_id(url)

    if url_type == 'YouTube Playlist':
        if is_ctx:
            if not ctx.interaction.response.is_done():
                await ctx.defer(ephemeral=ephemeral)

        try:
            playlist_videos = youtubesearchpython.Playlist.getVideos(url)
            playlist_videos = playlist_videos['videos']
        except KeyError:
            log(ctx, "------------------------------- playlist -------------------------")
            tb = traceback.format_exc()
            log(ctx, tb)
            log(ctx, "--------------------------------------------------------------")

            message = f'This playlist is unviewable: `{url}`'
            if not mute_response:
                await ctx.reply(message, ephemeral=ephemeral)
            return [False, message]

        if position is not None:
            playlist_videos = list(reversed(playlist_videos))

        for index, val in enumerate(playlist_videos):
            url = f"https://www.youtube.com/watch?v={playlist_videos[index]['id']}"
            video = VideoClass('Video', author_id, url)
            await to_queue(guild_id, video, position)

        message = f"`{len(playlist_videos)}` {tg(guild_id, 'songs from playlist added to queue!')} -> [Control Panel]({config.WEB_URL}/guild/{guild_id}&key={guild[guild_id].data.key})"
        if not mute_response:
            await ctx.reply(message, ephemeral=ephemeral)
        return [True, message, None]

    if url_type == 'YouTube Playlist Video' and is_ctx:
        view = PlaylistOptionView(ctx, url, force, from_play)
        message = tg(guild_id, 'This video is from a **playlist**, do you want to add the playlist to **queue?**')
        await ctx.reply(message, view=view, ephemeral=ephemeral)
        return [False, message, None]

    if url_type == 'Spotify Playlist' or url_type == 'Spotify Album':
        adding_message = None
        if is_ctx:
            adding_message = await ctx.reply(tg(guild_id, 'Adding songs to queue... (might take a while)'), ephemeral=ephemeral)

        if url_type == 'Spotify Playlist':
            video_list = spotify_playlist_to_yt_video_list(url, author_id)
        else:
            video_list = spotify_album_to_yt_video_list(url, author_id)

        if position is not None:
            video_list = list(reversed(video_list))

        for video in video_list:
            await to_queue(guild_id, video, position)

        message = f'`{len(video_list)}` {tg(guild_id, "songs from playlist added to queue!")} -> [Control Panel]({config.WEB_URL}/guild/{guild_id}&key={guild[guild_id].data.key})'
        if is_ctx:
            await adding_message.edit(content=message)
        return [True, message, None]

    if url_type == 'Spotify Track':
        video = spotify_to_yt_video(url, author_id)
        if video is not None:
            return await to_queue(guild_id, video, position, ctx, mute_response, ephemeral, True)

    if url_type == 'Spotify URL':
        video = spotify_to_yt_video(url, author_id)
        if video is None:
            message = f'Invalid spotify url: `{url}`'
            if not mute_response:
                await ctx.reply(message, ephemeral=ephemeral)
            return [False, message, None]

        return await to_queue(guild_id, video, position, ctx, mute_response, ephemeral, True)

    if url_type == 'SoundCloud URL':
        try:
            track = sc.resolve(url)
        except Exception as e:
            message = f'Invalid SoundCloud url: {url} -> {e}'
            if not mute_response:
                await ctx.reply(message, ephemeral=ephemeral)
            return [False, message, None]

        if type(track) == Track:
            try:
                video = VideoClass('SoundCloud', author=author_id, url=url)
            except ValueError as e:
                if not mute_response:
                    await ctx.reply(e, ephemeral=ephemeral)
                return [False, e, None]

            return await to_queue(guild_id, video, position, ctx, mute_response, ephemeral, True)

        if type(track) == Playlist:
            tracks = track.tracks
            if position is not None:
                tracks = list(reversed(tracks))

            for index, val in enumerate(tracks):
                duration = int(val.duration * 0.001)
                artist_url = 'https://soundcloud.com/' + track.permalink_url.split('/')[-2]

                video = VideoClass('SoundCloud', author=author_id, url=val.permalink_url, title=val.title, picture=val.artwork_url, duration=duration, channel_name=val.artist, channel_link=artist_url)
                await to_queue(guild_id, video, position)

            message = f"`{len(tracks)}` {tg(guild_id, 'songs from playlist added to queue!')} -> [Control Panel]({config.WEB_URL}/guild/{guild_id}&key={guild[guild_id].data.key})"
            if not mute_response:
                await ctx.reply(message, ephemeral=ephemeral)
            return [True, message, None]

    if url_type == 'YouTube Video' or yt_id is not None:
        url = f"https://www.youtube.com/watch?v={yt_id}"
        video = VideoClass('Video', author_id, url=url)
        return await to_queue(guild_id, video, position, ctx, mute_response, ephemeral, True)

    if url_type == 'String with URL':
        probe, extracted_url = await get_url_probe_data(url)
        if probe:
            if not probe_data:
                probe_data = [extracted_url, extracted_url, extracted_url]

            video = VideoClass('Probe', author_id, url=extracted_url, title=probe_data[0], picture=vlc_logo, duration='Unknown', channel_name=probe_data[1], channel_link=probe_data[2])
            return await to_queue(guild_id, video, position, ctx, mute_response, ephemeral, True)

    if is_ctx and not no_search:
        await search_command_def(ctx, url, display_type='short', force=force, from_play=from_play,ephemeral=ephemeral)

    message = f'`{url}` {tg(guild_id, "is not supported!")} -> [Control Panel]({config.WEB_URL}/guild/{guild_id}&key={guild[guild_id].data.key})'
    if not mute_response:
        await ctx.reply(message, ephemeral=ephemeral)
    return [False, message]


async def next_up_def(ctx,
                      url,
                      ephemeral: bool = False
                      ):
    log(ctx, 'next_up_def', [url, ephemeral], log_type='function', author=ctx.author)
    is_ctx, guild_id, author_id, guild_object = ctx_check(ctx)
    response = await queue_command_def(ctx, url, position=0, mute_response=True, force=True)

    if response[0]:
        if guild_object.voice_client:
            if not guild_object.voice_client.is_playing():
                await play_def(ctx)
                return
        else:
            await play_def(ctx)
            return

        await ctx.reply(response[1], ephemeral=ephemeral)

    else:
        return

    save_json()

async def skip_def(ctx):
    log(ctx, 'skip_def', [], log_type='function', author=ctx.author)
    is_ctx, guild_id, author_id, guild_object = ctx_check(ctx)

    if guild_object.voice_client:
        if guild_object.voice_client.is_playing():
            await stop_def(ctx, True)
            await asyncio.sleep(0.5)
            await play_def(ctx)
            return [True, 'Skipped!']

    message = tg(guild_id, "There is **nothing to skip!**")
    await ctx.reply(message, ephemeral=True)
    return [False, message]

async def remove_def(ctx,
                     number: int,
                     display_type: Literal['short', 'long'] = None,
                     ephemeral: bool = False,
                     list_type: Literal['queue', 'history'] = 'queue'
                     ):
    log(ctx, 'remove_def', [number, display_type, ephemeral], log_type='function', author=ctx.author)
    is_ctx, guild_id, author_id, guild_object = ctx_check(ctx)

    if not display_type:
        display_type = guild[guild_id].options.response_type

    if list_type == 'queue':
        if number or number == 0 or number == '0':
            if number > len(guild[guild_id].queue):
                if not guild[guild_id].queue:
                    message = tg(guild_id, "Nothing to **remove**, queue is **empty!**")
                    await ctx.reply(message, ephemeral=True)
                    return [False, message]
                message = tg(guild_id, "Index out of range!")
                await ctx.reply(message, ephemeral=True)
                return [False, message]

            video = guild[guild_id].queue[number]

            message = f'REMOVED #{number} : [`{video.title}`](<{video.url}>)'

            if display_type == 'long':
                embed = create_embed(video, f'{tg(guild_id, "REMOVED #")}{number}', guild_id)
                await ctx.reply(embed=embed, ephemeral=ephemeral)
            if display_type == 'short':
                await ctx.reply(message, ephemeral=ephemeral)

            guild[guild_id].queue.pop(number)

            save_json()

            return [True, message]

    elif list_type == 'history':
        if number or number == 0 or number == '0':
            if number > len(guild[guild_id].history):
                if not guild[guild_id].history:
                    message = tg(guild_id, "Nothing to **remove**, history is **empty!**")
                    await ctx.reply(message, ephemeral=True)
                    return [False, message]
                message = tg(guild_id, "Index out of range!")
                await ctx.reply(message, ephemeral=True)
                return [False, message]

            video = guild[guild_id].history[number]

            message = f'REMOVED #{number} : [`{video.title}`](<{video.url}>)'

            if display_type == 'long':
                embed = create_embed(video, f'{tg(guild_id, "REMOVED #")}{number}', guild_id)
                await ctx.reply(embed=embed, ephemeral=ephemeral)
            if display_type == 'short':
                await ctx.reply(message, ephemeral=ephemeral)

            guild[guild_id].history.pop(number)

            save_json()

            return [True, message]

    else:
        save_json()
        message = 'Invalid list type!'
        await ctx.reply(message, ephemeral=True)
        return [False, message]

    save_json()

    return [False, 'No number given!']

async def clear_def(ctx,
                    ephemeral: bool = False
                    ):
    log(ctx, 'clear_def', [ephemeral], log_type='function', author=ctx.author)
    is_ctx, guild_id, author_id, guild_object = ctx_check(ctx)
    guild[guild_id].queue.clear()
    message = tg(guild_id, 'Removed **all** songs from queue')
    await ctx.reply(message, ephemeral=ephemeral)
    return [True, message]

async def shuffle_def(ctx,
                      ephemeral: bool = False
                      ):
    log(ctx, 'shuffle_def', [ephemeral], log_type='function', author=ctx.author)
    is_ctx, guild_id, author_id, guild_object = ctx_check(ctx)
    random.shuffle(guild[guild_id].queue)
    message = tg(guild_id, 'Songs in queue shuffled')
    await ctx.reply(message, ephemeral=ephemeral)
    return [True, message]

async def show_def(ctx,
                   display_type: Literal['short', 'medium', 'long'] = None,
                   list_type: Literal['queue', 'history']='queue',
                   ephemeral: bool = False
                   ):
    log(ctx, 'show_def', [display_type, list_type,ephemeral], log_type='function', author=ctx.author)
    is_ctx, guild_id, author_id, guild_object = ctx_check(ctx)

    if not is_ctx:
        return [False, 'Cannot use this command in WEB']

    if list_type == 'queue':
        show_list = guild[guild_id].queue
    elif list_type == 'history':
        show_list = guild[guild_id].history
    else:
        return [False, 'Bad list_type']

    max_embed = 5
    if not show_list:
        await ctx.reply(tg(guild_id, "Nothing to **show**, queue is **empty!**"), ephemeral=ephemeral)
        return

    if not display_type:
        if len(show_list) <= max_embed:
            display_type = 'long'
        else:
            display_type = 'medium'

    if display_type == 'long':
        message = f"**THE {list_type.capitalize()}**\n **Loop** mode  `{guild[guild_id].options.loop}`,  **Display** type `{display_type}`, [Control Panel]({config.WEB_URL}/guild/{guild_id}&key={guild[guild_id].data.key})"
        await ctx.send(message, ephemeral=ephemeral, mention_author=False)

        for index, val in enumerate(show_list):
            embed = create_embed(val, f'{tg(guild_id, f"{list_type.upper()} #")}{index}', guild_id)

            await ctx.send(embed=embed, ephemeral=ephemeral, mention_author=False)


    if display_type == 'medium':
        embed = discord.Embed(title=f"Song {list_type}", description=f'Loop: {guild[guild_id].options.loop} | Display type: {display_type} | [Control Panel]({config.WEB_URL}/guild/{guild_id}&key={guild[guild_id].data.key})', color=0x00ff00)

        message = ''
        for index, val in enumerate(show_list):
            add = f'**{index}** --> `{convert_duration(val.duration)}`  [{val.title}](<{val.url}>) \n'

            if len(message) + len(add) > 1023:
                embed.add_field(name="", value=message, inline=False)
                message = ''
            else:
                message = message + add

        embed.add_field(name="", value=message, inline=False)

        if len(embed) < 6000:
            await ctx.reply(embed=embed, ephemeral=ephemeral, mention_author=False)
        else:
            await ctx.reply("HTTPException(discord 6000 character limit) >> using display type `short`", ephemeral=ephemeral, mention_author=False)
            display_type = 'short'


    if display_type == 'short':
        send = f"**THE {list_type.upper()}**\n **Loop** mode  `{guild[guild_id].options.loop}`,  **Display** type `{display_type}`, [Control Panel]({config.WEB_URL}/guild/{guild_id}&key={guild[guild_id].data.key})"
        # noinspection PyUnresolvedReferences
        if ctx.interaction.response.is_done(): await ctx.send(send, ephemeral=ephemeral, mention_author=False)
        else: await ctx.reply(send, ephemeral=ephemeral, mention_author=False)

        message = ''
        for index, val in enumerate(show_list):
            add = f'**{tg(guild_id, f"{list_type.upper()} #")}{index}**  `{convert_duration(val.duration)}`  [`{val.title}`](<{val.url}>) \n'
            if len(message) + len(add) > 2000:
                if ephemeral:
                    await ctx.send(message, ephemeral=ephemeral, mention_author=False)
                else:
                    await ctx.message.channel.send(content=message, mention_author=False)
                message = ''
            else:
                message = message + add

        if ephemeral:
            await ctx.send(message, ephemeral=ephemeral, mention_author=False)
        else:
            await ctx.message.channel.send(content=message, mention_author=False)

    save_json()

async def search_command_def(ctx,
                             search_query,
                             display_type: Literal['short', 'long'] = None,
                             force: bool = False,
                             from_play: bool = False,
                             ephemeral: bool = False
                             ):
    log(ctx, 'search_command_def', [search_query, display_type, force, from_play, ephemeral], log_type='function', author=ctx.author)
    is_ctx, guild_id, author_id, guild_object = ctx_check(ctx)

    if not is_ctx:
        return [False, 'Search command cannot be used in WEB']

    # noinspection PyUnresolvedReferences
    if not ctx.interaction.response.is_done():
        await ctx.defer(ephemeral=ephemeral)

    guild[guild_id].options.search_query = search_query

    if display_type is None:
        display_type = guild[guild_id].options.response_type

    message = f'**Search query:** `{search_query}`\n'

    if display_type == 'long':
        await ctx.reply(tg(guild_id, 'Searching...'), ephemeral=ephemeral)

    custom_search = youtubesearchpython.VideosSearch(search_query, limit=5)
    guild[guild_id].search_list.clear()

    view = SearchOptionView(ctx, force, from_play)

    if not custom_search.result()['result']:
        await ctx.reply(tg(guild_id, 'No results found!'), ephemeral=ephemeral)
        return

    for i in range(5):
        # noinspection PyTypeChecker
        url = custom_search.result()['result'][i]['link']
        video = VideoClass('Video', ctx.author.id, url)
        guild[guild_id].search_list.append(video)

        if display_type == 'long':
            embed = create_embed(video, f'{tg(guild_id, "Result #")}{i + 1}', guild_id)
            await ctx.message.channel.send(embed=embed, ephemeral=ephemeral)
        if display_type == 'short':
            message += f'{tg(guild_id, "Result #")}{i+1} : [`{video.title}`](<{video.url}>)\n'
    if display_type == 'short':
        await ctx.reply(message, view=view, ephemeral=ephemeral)

    save_json()

# --------------------------------------- PLAYER --------------------------------------------------

async def play_def(ctx,
                   url=None,
                   force=False,
                   mute_response=False
                   ):
    log(ctx, 'play_def', [url, force, mute_response], log_type='function', author=ctx.author)
    is_ctx, guild_id, author_id, guild_object = ctx_check(ctx)
    response = []

    notif = f'\n{tg(guild_id, "Check out the new")} [Control Panel]({config.WEB_URL}/guild/{guild_id}&key={guild[guild_id].data.key})'

    if url == 'next':
        if guild[guild_id].options.stopped:
            log(ctx, "play_def -> stopped play next loop")
            now_to_history(guild_id)
            return [False, "Stopped play next loop"]

    voice = guild_object.voice_client

    if not voice or voice is None:
        if not is_ctx:
            return [False, 'Bot is not connected to a voice channel']

        if ctx.author.voice is None:
            message = tg(guild_id, "You are **not connected** to a voice channel")
            if not mute_response:
                await ctx.reply(message)
            return [False, message]

    if url and url != 'next':
        if voice:
            if not voice.is_playing():
                force = True
        if force:
            response = await queue_command_def(ctx, url=url, position=0, mute_response=True, force=force, from_play=True)
        else:
            response = await queue_command_def(ctx, url=url, position=None, mute_response=True, force=force, from_play=True)
        if not response[0]:
            return [False, response[1]]

    voice = guild_object.voice_client

    if not voice or voice is None:
        # noinspection PyUnresolvedReferences
        if not is_ctx:
            if not ctx.interaction.response.is_done():
                await ctx.defer()
        join_response = await join_def(ctx, None, True)
        voice = guild_object.voice_client
        if not join_response[0]:
            return [False, join_response[1]]

    if voice.is_playing():
        if not guild[guild_id].options.is_radio and not force:
            if url:
                if response:
                    if response[2]:
                        message = f'{tg(guild_id, "**Already playing**, added to queue")}: [`{response[2].title}`](<{response[2].url}>) {notif}'
                        if not mute_response:
                            await ctx.reply(message)
                        return [False, message]
                message = f'{tg(guild_id, "**Already playing**, added to queue")} {notif}'
                if not mute_response:
                    await ctx.reply(message)
                return [False, message]

            message = f'{tg(guild_id, "**Already playing**")} {notif}'
            if not mute_response:
                await ctx.reply(message, ephemeral=True)
            return [False, message]

        voice.stop()
        guild[guild_id].options.stopped = True
        guild[guild_id].options.is_radio = False

    if not guild[guild_id].queue:
        message = f'{tg(guild_id, "There is **nothing** in your **queue**")} {notif}'

        if url != 'next':
            if not mute_response:
                await ctx.reply(message)

        now_to_history(guild_id)
        return [False, message]

    video = guild[guild_id].queue[0]
    now_to_history(guild_id)

    if video.class_type not in ['Video', 'Probe', 'SoundCloud']:
        guild[guild_id].queue.pop(0)
        if video.class_type == 'Radio':
            await radio_def(ctx, video.title)
            return
        if video.class_type == 'Local':
            await ps_def(ctx, video.local_number)
            return

        message = tg(guild_id, "Unknown type")
        if not mute_response:
            await ctx.reply(message)
        return [False, message]

    if not force:
        guild[guild_id].options.stopped = False

    try:
        source = await GetSource.create_source(guild_id, video.url, source_type=video.class_type)
        voice.play(source, after=lambda e: asyncio.run_coroutine_threadsafe(play_def(ctx, 'next'), bot.loop))

        await volume_command_def(ctx, guild[guild_id].options.volume * 100, False, True)

        # Variables update
        guild[guild_id].options.stopped = False
        video.played_at = int(time())
        guild[guild_id].now_playing = video

        # Queue update
        if guild[guild_id].options.loop:
            guild[guild_id].queue.append(video)
        guild[guild_id].queue.pop(0)

        save_json()

        # Response
        options = guild[guild_id].options
        response_type = options.response_type

        message = f'{tg(guild_id, "Now playing")} [`{video.title}`](<{video.url}>) {notif}'
        view = PlayerControlView(ctx)

        if response_type == 'long':
            if not mute_response:
                embed = create_embed(video, "Now playing", guild_id)
                if options.buttons:
                    await ctx.reply(embed=embed, view=view)
                else:
                    await ctx.reply(embed=embed)
            return [True, message]

        elif response_type == 'short':
            if not mute_response:
                if options.buttons:
                    await ctx.reply(message, view=view)
                else:
                    await ctx.reply(message)
            return [True, message]

        else:
            return [True, message]


    except (discord.ext.commands.errors.CommandInvokeError, IndexError, TypeError, discord.errors.ClientException, discord.errors.NotFound):
        log(ctx, "------------------------------- play -------------------------")
        tb = traceback.format_exc()
        log(ctx, tb)
        log(ctx, "--------------------------------------------------------------")
        await ctx.reply(f'{tg(guild_id, "An **error** occurred while trying to play the song")}'
                        f' {bot.get_user(my_id).mention} ({sys.exc_info()[0]})')

async def radio_def(ctx,
                    favourite_radio: Literal['Rádio BLANÍK','Rádio BLANÍK CZ','Evropa 2','Fajn Radio','Hitrádio PopRock','Český rozhlas Pardubice','Radio Beat','Country Radio','Radio Kiss','Český rozhlas Vltava','Hitrádio Černá Hora'] = None,
                    radio_code: int = None,
                    ):
    log(ctx, 'radio_def', [favourite_radio, radio_code], log_type='function', author=ctx.author)
    is_ctx, guild_id, author_id, guild_object = ctx_check(ctx)
    radio_type = 'Rádio BLANÍK'

    # noinspection PyUnresolvedReferences
    if is_ctx:
        if not ctx.interaction.response.is_done():
            await ctx.defer()
    if favourite_radio and radio_code:
        message = tg(guild_id, "Only **one** argument possible!")
        await ctx.reply(message, ephemeral=True)
        return [False, message]

    if favourite_radio:
        radio_type = favourite_radio
    elif radio_code:
        radio_type = list(radio_dict.keys())[radio_code]

    if not guild_object.voice_client:
        response = await join_def(ctx, None, True)
        if not response[0]:
            return [False, response[1]]

    url = radio_dict[radio_type]['stream']
    # guild[guild_id].queue.clear()

    if guild_object.voice_client.is_playing():
        await stop_def(ctx, True)  # call the stop coroutine if something else is playing, pass True to not send response

    video = VideoClass('Radio', author_id, radio_name=radio_type, played_at=int(time()))
    guild[guild_id].now_playing = video

    guild[guild_id].options.is_radio = True

    embed = create_embed(video, 'Now playing', guild_id)

    source = discord.FFmpegPCMAudio(url, **FFMPEG_OPTIONS)

    guild_object.voice_client.play(source)

    await volume_command_def(ctx, guild[guild_id].options.volume*100, False, True)

    if guild[guild_id].options.buttons:
        view = PlayerControlView(ctx)
        await ctx.reply(embed=embed, view=view)
    else:
        await ctx.reply(embed=embed)  # view=view   f"**{text['Now playing']}** `{radio_type}`",

    save_json()

async def ps_def(ctx,
                 effect_number: app_commands.Range[int, 1, len(all_sound_effects)],
                 mute_response: bool = False
                 ):
    log(ctx, 'ps_def', [effect_number, mute_response], log_type='function', author=ctx.author)
    is_ctx, guild_id, author_id, guild_object = ctx_check(ctx)
    guild[guild_id].options.is_radio = False
    try:
        name = all_sound_effects[effect_number]
    except IndexError:
        if not mute_response:
            await ctx.reply(tg(guild_id, "Number **not in list** (use `/sound` to get all sound effects)"), ephemeral=True)
        return False

    filename = "sound_effects/" + name + ".mp3"
    if path.exists(filename):
        source = FFmpegPCMAudio(filename)
    else:
        filename = "sound_effects/" + name + ".wav"
        if path.exists(filename):
            source = FFmpegPCMAudio(filename)

        else:
            if not mute_response:
                await ctx.reply(tg(guild_id, "No such file/website supported"), ephemeral=True)
            return False

    video = VideoClass('Local', author_id, title=name, duration='Unknown', local_number=effect_number, played_at=int(time()))
    guild[guild_id].now_playing = video

    if not guild_object.voice_client:
        join_response = await join_def(ctx, None, True)
        if not join_response[0]:
            return [False, join_response[1]]

    voice = guild_object.voice_client

    await stop_def(ctx, True)
    voice.play(source)
    await volume_command_def(ctx, guild[guild_id].options.volume*100, False, True)
    if not mute_response:
        await ctx.reply(f"{tg(guild_id, 'Playing sound effect number')} `{effect_number}`", ephemeral=True)

    save_json()

    return True

async def now_def(ctx,
                  ephemeral: bool = False
                  ):
    log(ctx, 'now_def', [ephemeral], log_type='function', author=ctx.author)
    is_ctx, guild_id, author_id, guild_object = ctx_check(ctx)
    if not is_ctx:
        return [False, 'This command cant be used in WEB']

    if ctx.voice_client:
        if ctx.voice_client.is_playing():
            guild[guild_id].now_playing.renew()
            embed = create_embed(guild[guild_id].now_playing, "Now playing", guild_id)

            view = PlayerControlView(ctx)

            if guild[guild_id].options.buttons:
                await ctx.reply(embed=embed, view=view, ephemeral=ephemeral)
            else:
                await ctx.reply(embed=embed, ephemeral=ephemeral)

        if not ctx.voice_client.is_playing():
            if ctx.voice_client.is_paused():
                await ctx.reply(
                    f'{tg(guild_id, "There is no song playing right **now**, but there is one **paused:**")}'
                    f'  [`{guild[guild_id].now_playing.title}`](<{guild[guild_id].now_playing.url}>)', ephemeral=ephemeral)
            else:
                await ctx.reply(tg(guild_id, 'There is no song playing right **now**'), ephemeral=ephemeral)
    else:
        await ctx.reply(tg(guild_id, 'There is no song playing right **now**'), ephemeral=ephemeral)

    save_json()

async def last_def(ctx,
                   ephemeral: bool = False
                   ):
    log(ctx, 'last_def', [ephemeral], log_type='function', author=ctx.author)
    is_ctx, guild_id, author_id, guild_object = ctx_check(ctx)
    if not is_ctx:
        return [False, 'This command cant be used in WEB']

    embed = create_embed(guild[guild_id].history[-1], "Last played", guild_id)

    view = PlayerControlView(ctx)

    if guild[guild_id].options.buttons:
        await ctx.reply(embed=embed, view=view, ephemeral=ephemeral)
    else:
        await ctx.reply(embed=embed, ephemeral=ephemeral)

    save_json()

async def loop_command_def(ctx):
    log(ctx, 'loop_command_def', [], log_type='function', author=ctx.author)
    is_ctx, guild_id, author_id, guild_object = ctx_check(ctx)

    if guild[guild_id].options.loop:
        guild[guild_id].options.loop = False
        message = 'Loop mode: `False`'
        await ctx.reply(message, ephemeral=True)
        return [True, message]
    if not guild[guild_id].options.loop:
        guild[guild_id].options.loop = True
        message = 'Loop mode: `True`'
        await ctx.reply(message, ephemeral=True)
        return [True, message]

async def loop_this_def(ctx):
    log(ctx, 'loop_this_def', [], log_type='function', author=ctx.author)
    is_ctx, guild_id, author_id, guild_object = ctx_check(ctx)

    if guild[guild_id].now_playing and guild_object.voice_client.is_playing:
        guild[guild_id].queue.clear()
        guild[guild_id].queue.append(guild[guild_id].now_playing)
        guild[guild_id].options.loop = True

        message = f'{tg(guild_id, "Queue **cleared**, Player will now loop **currently** playing song:")} [`{guild[guild_id].now_playing.title}`](<{guild[guild_id].now_playing.url}>)'
        await ctx.reply(message)
        return [True, message]
    else:
        message = tg(guild_id, "Nothing is playing **right now**")
        await ctx.reply(message)
        return [False, message]

# --------------------------------------- VOICE --------------------------------------------------

async def stop_def(ctx,
                   mute_response: bool = False
                   ):
    log(ctx, 'stop_def', [mute_response], log_type='function', author=ctx.author)
    is_ctx, guild_id, author_id, guild_object = ctx_check(ctx)

    voice = discord.utils.get(bot.voice_clients, guild=guild_object)
    if voice:
        voice.stop()
    else:
        message = tg(guild_id, "Bot is not connected to a voice channel")
        if not mute_response:
            await ctx.reply(message, ephemeral=True)
        return [False, message]
    guild[guild_id].options.stopped = True
    guild[guild_id].options.loop = False

    message = tg(guild_id, "Player **stopped!**")
    if not mute_response:
        await ctx.reply(message, ephemeral=True)

    now_to_history(guild_id)
    save_json()
    return [True, message]

async def pause_def(ctx,
                    mute_response: bool = False
                    ):
    log(ctx, 'pause_def', [mute_response], log_type='function', author=ctx.author)
    is_ctx, guild_id, author_id, guild_object = ctx_check(ctx)
    voice = discord.utils.get(bot.voice_clients, guild=guild_object)

    if voice:
        if voice.is_playing():
            voice.pause()
            message = tg(guild_id, "Player **paused!**")
            resp = [True, message]
        elif voice.is_paused():
            message = tg(guild_id, "Player **already paused!**")
            resp = [False, message]
        else:
            message = tg(guild_id, 'No audio playing')
            resp = [False, message]
    else:
        message = tg(guild_id, "Bot is not connected to a voice channel")
        resp = [False, message]

    if not mute_response:
        await ctx.reply(message, ephemeral=True)

    save_json()

    return resp

async def resume_def(ctx,
                     mute_response: bool = False
                     ):
    log(ctx, 'resume_def', [mute_response], log_type='function', author=ctx.author)
    is_ctx, guild_id, author_id, guild_object = ctx_check(ctx)
    voice = discord.utils.get(bot.voice_clients, guild=guild_object)
    if voice:
        if voice.is_paused():
            voice.resume()
            message = tg(guild_id, "Player **resumed!**")
            resp = [True, message]
        elif voice.is_playing():
            message = tg(guild_id, "Player **already resumed!**")
            resp = [False, message]
        else:
            message = tg(guild_id, 'No audio playing')
            resp = [False, message]
    else:
        message = tg(guild_id, "Bot is not connected to a voice channel")
        resp = [False, message]

    if not mute_response:
        await ctx.reply(message, ephemeral=True)

    save_json()

    return resp

async def join_def(ctx,
                   channel_id=None,
                   mute_response: bool = False
                   ):
    log(ctx, 'join_def', [channel_id, mute_response], log_type='function', author=ctx.author)
    is_ctx, guild_id, author_id, guild_object = ctx_check(ctx)

    now_to_history(guild_id)

    if not channel_id:
        if not is_ctx:
            return [False, 'No channel_id provided']
        if ctx.author.voice:
            channel = ctx.message.author.voice.channel
            if ctx.voice_client:
                if ctx.voice_client.channel != channel:
                    await ctx.voice_client.disconnect(force=True)
                else:
                    message = tg(guild_id, "I'm already in this channel")
                    if not mute_response:
                        await ctx.reply(message, ephemeral=True)
                    return [True, message]
            await channel.connect()
            await ctx.guild.change_voice_state(channel=channel, self_deaf=True)

            message = f"{tg(guild_id, 'Joined voice channel:')}  `{channel.name}`"
            if not mute_response:
                await ctx.reply(message, ephemeral=True)
            return [True, message]

        message = tg(guild_id, "You are **not connected** to a voice channel")
        await ctx.reply(message, ephemeral=True)
        return [False, message]

    try:
        voice_channel = bot.get_channel(int(channel_id))
        if guild_object.voice_client:
            await guild_object.voice_client.disconnect(force=True)
        await voice_channel.connect()
        await guild_object.change_voice_state(channel=voice_channel, self_deaf=True)

        message = f"{tg(guild_id, 'Joined voice channel:')}  `{voice_channel.name}`"
        if not mute_response:
            await ctx.reply(message, ephemeral=True)
        return [True, message]

    except (discord.ext.commands.errors.CommandInvokeError, discord.errors.ClientException, AttributeError, ValueError, TypeError):

        log(ctx, "------------------------------- join -------------------------")
        tb = traceback.format_exc()
        log(ctx, tb)
        log(ctx, "--------------------------------------------------------------")

        message = tg(guild_id,"Channel **doesn't exist** or bot doesn't have **sufficient permission** to join")
        await ctx.reply(message, ephemeral=True)
        return [False, message]

async def disconnect_def(ctx,
                         mute_response: bool = False
                         ):
    log(ctx, 'disconnect_def', [mute_response], log_type='function', author=ctx.author)
    is_ctx, guild_id, author_id, guild_object = ctx_check(ctx)

    if guild_object.voice_client:
        await stop_def(ctx, True)
        guild[guild_id].queue.clear()
        channel = guild_object.voice_client.channel
        await guild_object.voice_client.disconnect(force=True)

        now_to_history(guild_id)
        save_json()

        message = f"{tg(guild_id, 'Left voice channel:')} `{channel}`"
        if not mute_response:
            await ctx.reply(message, ephemeral=True)
        return [True, message]
    else:
        now_to_history(guild_id)
        save_json()

        message = tg(guild_id, "Bot is **not** in a voice channel")
        if not mute_response:
            await ctx.reply(message, ephemeral=True)
        return [False, message]

async def volume_command_def(ctx,
                             volume = None,
                             ephemeral: bool = False,
                             mute_response: bool = False
                             ):
    log(ctx, 'volume_command_def', [volume, ephemeral, mute_response], log_type='function', author=ctx.author)
    is_ctx, guild_id, author_id, guild_object = ctx_check(ctx)

    if volume:
        new_volume = int(volume) / 100

        guild[guild_id].options.volume = new_volume
        voice = guild_object.voice_client
        if voice:
            try:
                if voice.source:
                    voice.source.volume = new_volume
                    voice.source = discord.PCMVolumeTransformer(voice.source, volume=new_volume)
            except AttributeError:
                pass

        message = f'{tg(guild_id, "Changed the volume for this server to:")} `{guild[guild_id].options.volume*100}%`'
    else:
        message = f'{tg(guild_id, "The volume for this server is:")} `{guild[guild_id].options.volume*100}%`'

    if not mute_response:
        await ctx.reply(message, ephemeral=ephemeral)

    save_json()

    return [True, message]

# --------------------------------------- GENERAL --------------------------------------------------

async def ping_def(ctx):
    log(ctx, 'ping_def', [], log_type='function', author=ctx.author)
    message = f'**Pong!** Latency: {round(bot.latency * 1000)}ms'
    await ctx.reply(message)
    save_json()
    return [True, message]

# noinspection PyTypeHints
async def language_command_def(ctx,
                               country_code: Literal[tuple(languages_dict.keys())]
                               ):
    log(ctx, 'language_command_def', [country_code], log_type='function', author=ctx.author)
    is_ctx, guild_id, author_id, guild_object = ctx_check(ctx)
    guild[guild_id].options.language = country_code
    message = f'{tg(guild_id, "Changed the language for this server to: ")} `{guild[guild_id].options.language}`'
    await ctx.reply(message)
    save_json()
    return [True, message]

async def sound_effects_def(ctx,
                            ephemeral: bool = True
                            ):
    log(ctx, 'sound_effects_def', [ephemeral], log_type='function', author=ctx.author)
    is_ctx, guild_id, author_id, guild_object = ctx_check(ctx)

    if not is_ctx:
        return [False, 'Command cannot be used in WEB']

    embed = discord.Embed(title="Sound Effects", colour=discord.Colour.from_rgb(241, 196, 15))
    message = ''
    for index, val in enumerate(all_sound_effects):
        add = f'**{index}** --> {val}\n'

        if len(message) + len(add) > 1023:
            embed.add_field(name="", value=message, inline=False)
            message = ''
        else:
            message = message + add

    embed.add_field(name="", value=message, inline=False)

    await ctx.send(embed=embed, ephemeral=ephemeral)

async def list_radios_def(ctx,
                          ephemeral: bool = True
                          ):
    log(ctx, 'list_radios_def', [ephemeral], log_type='function', author=ctx.author)
    is_ctx, guild_id, author_id, guild_object = ctx_check(ctx)

    if not is_ctx:
        return [False, 'Command cannot be used in WEB']

    embed = discord.Embed(title="Radio List")
    message = ''
    for index, (name, val) in enumerate(radio_dict.items()):
        add = f'**{index}** --> {name}\n'

        if len(message) + len(add) > 1023:
            embed.add_field(name="", value=message, inline=False)
            message = ''
        else:
            message = message + add

    embed.add_field(name="", value=message, inline=False)

    await ctx.send(embed=embed, ephemeral=ephemeral)

async def key_def(ctx: commands.Context):
    log(ctx, 'key_def', [], log_type='function', author=ctx.author)
    save_json()
    message = f'Key: `{guild[ctx.guild.id].data.key}` -> [Control Panel]({config.WEB_URL}/guild/{ctx.guild.id}&key={guild[ctx.guild.id].data.key})'
    await ctx.reply(message)
    save_json()
    return [True, message]

# ---------------------------------------- ADMIN --------------------------------------------------

async def announce_command_def(ctx: commands.Context,
                               message
                               ):
    log(ctx, 'announce_command_def', [message], log_type='function', author=ctx.author)
    for guild_object in bot.guilds:
        await guild_object.system_channel.send(message)

    await ctx.reply(f'Announced message to all servers: `{message}`')

async def rape_play_command_def(ctx: commands.Context,
                                effect_number: int = None,
                                channel_id = None,
                                ):
    log(ctx, 'rape_play_command_def', [effect_number, channel_id], log_type='function', author=ctx.author)

    if not effect_number and effect_number != 0:
        effect_number = 1

    if not channel_id:
        join_response = await join_def(ctx, None, True)
        if join_response[0]:
            pass
        else:
            await ctx.reply(f'You need to be in a voice channel to use this command', ephemeral=True)
            return
    else:
        join_response = await join_def(ctx, channel_id, True)
        if join_response[0]:
            pass
        else:
            await ctx.reply(f'An error occurred when connecting to the voice channel', ephemeral=True)
            return

    await ps_def(ctx, effect_number, True)
    await ear_rape_command_def(ctx)

    await ctx.reply(f'Playing effect `{effect_number}` with ear rape in `{channel_id if channel_id else "user channel"}` >>> effect can only be turned off by `/disconnect`', ephemeral=True)

async def ear_rape_command_def(ctx: commands.Context):
    log(ctx, 'ear_rape_command_def', [], log_type='function', author=ctx.author)
    guild_id = ctx.guild.id
    times = 10
    new_volume = 10000000000000

    guild[guild_id].options.volume = 1.0

    voice = ctx.voice_client
    if voice:
        try:
            if voice.source:
                for i in range(times):
                    voice.source.volume = new_volume
                    voice.source = discord.PCMVolumeTransformer(voice.source, volume=new_volume)
        except AttributeError:
            pass

        await ctx.reply(f'Haha get ear raped >>> effect can only be turned off by `/disconnect`', ephemeral=True)
    else:
        await ctx.reply(f'Ear Rape can only be activated if the bot is in a voice channel', ephemeral=True)

    save_json()

async def kys_def(ctx: commands.Context):
    log(ctx, 'kys_def', [], log_type='function', author=ctx.author)
    guild_id = ctx.guild.id
    await ctx.reply(tg(guild_id, "Committing seppuku..."))
    sys.exit(3)

async def config_command_def(ctx: commands.Context,
                             config_file: discord.Attachment,
                             config_type:  Literal['guilds', 'other', 'radio', 'languages'] = 'guilds',
                             ):
    log(ctx, 'config_command_def', [config_file, config_type], log_type='function', author=ctx.author)

    if config_file.filename != f'{config_type}.json':
        await ctx.reply(f'You need to upload a `{config_type}.json` file', ephemeral=True)
        return

    content = config_file.read()
    if not content:
        await ctx.reply(f"no content in file: `{config_type}`")
        return

    with open(f'src/{config_type}.json', 'wb') as f:
        f.write(content)

    if config_type == 'guilds':
        log(None, 'Loading guilds.json ...')
        with open('src/guilds.json', 'r') as f:
            globals()['guild'] = json_to_guilds(json.load(f))

        await ctx.reply("Loaded new `guilds.json`", ephemeral=True)
    else:
        await ctx.reply(f"Saved new `{config_type}.json`", ephemeral=True)

async def log_command_def(ctx: commands.Context,
                          log_type: Literal['log.txt', 'guilds.json', 'other.json', 'radio.json', 'languages.json', 'activity.log', 'data.txt'] = 'log.txt'
                          ):
    log(ctx, 'log_command_def', [log_type], log_type='function', author=ctx.author)
    save_json()
    if log_type == 'log.txt':
        file_to_send = discord.File('log/log.txt')
    elif log_type == 'data.txt':
        file_to_send = discord.File('log/data.txt')
    elif log_type == 'other.json':
        file_to_send = discord.File('src/other.json')
    elif log_type == 'radio.json':
        file_to_send = discord.File('src/radio.json')
    elif log_type == 'languages.json':
        file_to_send = discord.File('src/languages.json')
    elif log_type == 'guilds.json':
        file_to_send = discord.File('src/guilds.json')
    elif log_type == 'activity.log':
        try:
            file_to_send = discord.File('log/activity.log')
        except FileNotFoundError:
            await ctx.reply(f'`activity.log` does not exist', ephemeral=True)
            return
    else:
        file_to_send = discord.File('log/log.txt')
    await ctx.reply(file=file_to_send, ephemeral=True)

# noinspection PyTypeHints
async def change_options_def(ctx: commands.Context,
                            stopped: bool = None,
                            loop: bool = None,
                            is_radio: bool = None,
                            buttons: bool = None,
                            language: Literal[tuple(languages_dict.keys())] = None,
                            response_type: Literal['short', 'long'] = None,
                            buffer: int = None,
                            history_length: int = None,
                            volume = None,
                            server = None,
                            ):
    log(ctx, 'change_options_def', [stopped, loop, is_radio, buttons, language, response_type, buffer, history_length, volume, server], log_type='function', author=ctx.author)
    guild_id = ctx.guild.id

    save_json()

    guilds = []

    if not server:
        server = 'this'

    if server == 'all':
        for guild_id, guild_class in guild:
            guilds.append(guild_id)
    elif server == 'this':
        guilds.append(ctx.guild.id)
    else:
        try:
            if int(server) in bot.guilds:
                guilds.append(int(server))
            else:
                await ctx.reply(tg(guild_id, "That guild doesn't exist or the bot is not in it"), ephemeral=True)
                return
        except (ValueError, TypeError):
            await ctx.reply(tg(guild_id, "That is not a **guild id!**"), ephemeral=True)
            return

    for guild_id in guilds:
        if stopped:
            guild[guild_id].options.stopped = stopped
        if loop:
            guild[guild_id].options.loop = loop
        if is_radio:
            guild[guild_id].options.is_radio = is_radio
        if buttons:
            guild[guild_id].options.buttons = buttons
        if language:
            guild[guild_id].options.language = language
        if response_type:
            guild[guild_id].options.response_type = response_type
        if volume:
            guild[guild_id].options.volume = volume
        if buffer:
            guild[guild_id].options.buffer = buffer
        if history_length:
            guild[guild_id].options.history_length = history_length

        config_text = f'`stopped={guild[guild_id].options.stopped}`, `loop={guild[guild_id].options.loop}`,' \
                 f' `is_radio={guild[guild_id].options.is_radio}`, `buttons={guild[guild_id].options.buttons}`,' \
                 f' `language={guild[guild_id].options.language}`, `response_type={guild[guild_id].options.response_type}`,' \
                 f' `volume={guild[guild_id].options.volume}`, `buffer={guild[guild_id].options.buffer}`'

        save_json()

        await ctx.reply(f'**Config for guild `{guild_id}`**\n {config_text}', ephemeral=True)

# --------------------------------------------- HELP COMMAND -----------------------------------------------------------

bot.remove_command('help')
@bot.hybrid_command(name='help', with_app_command=True, description='Shows all available commands', help='Shows all available commands')
@app_commands.describe(general='General commands', player='Player commands', queue='Queue commands', voice='Voice commands')
async def help_command(ctx: commands.Context,
                       general: Literal['help', 'ping', 'language', 'sound_effects', 'list_radios'] = None,
                       player: Literal['play', 'radio', 'ps', 'skip', 'nowplaying', 'last', 'loop', 'loop_this'] = None,
                       queue: Literal['queue', 'remove', 'clear', 'shuffle', 'show', 'search'] = None,
                       voice: Literal['stop', 'pause', 'resume', 'join', 'disconnect', 'volume'] = None
                       ):
    log(ctx, 'help', [general, player, queue, voice], log_type='command', author=ctx.author)
    gi = ctx.guild.id

    if general:
        command = general
    elif player:
        command = player
    elif queue:
        command = queue
    elif voice:
        command = voice
    else:
        command = None

    embed = discord.Embed(title="Help", description=f"Use `/help <command>` to get help on a command | Prefix: `{prefix}`")
    embed.add_field(name="General", value=f"`/help` - {tg(gi, 'help')}\n"
                                          f"`/ping` - {tg(gi, 'ping')}\n"
                                          f"`/language` - {tg(gi, 'language')}\n"
                                          f"`/sound_ effects` - {tg(gi, 'sound')}\n"
                                          f"`/list_radios` - {tg(gi, 'list_radios')}\n"
                                          f"`/key` - {tg(gi, 'key')}\n"
                    , inline=False)
    embed.add_field(name="Player", value=f"`/play` - {tg(gi, 'play')}\n"
                                         f"`/radio` - {tg(gi, 'radio')}\n"
                                         f"`/ps` - {tg(gi, 'ps')}\n"
                                         f"`/skip` - {tg(gi, 'skip')}\n"
                                         f"`/nowplaying` - {tg(gi, 'nowplaying')}\n"
                                         f"`/last` - {tg(gi, 'last')}\n"
                                         f"`/loop` - {tg(gi, 'loop')}\n"
                                         f"`/loop_this` - {tg(gi, 'loop_this')}\n"
                    , inline=False)
    embed.add_field(name="Queue", value=f"`/queue` - {tg(gi, 'queue_add')}\n"
                                        f"`/remove` - {tg(gi, 'queue_remove')}\n"
                                        f"`/clear` - {tg(gi, 'clear')}\n"
                                        f"`/shuffle` - {tg(gi, 'shuffle')}\n"
                                        f"`/show` - {tg(gi, 'queue_show')}\n"
                                        f"`/search` - {tg(gi, 'search')}"
                    , inline=False)
    embed.add_field(name="Voice", value=f"`/stop` - {tg(gi, 'stop')}\n"
                                        f"`/pause` - {tg(gi, 'pause')}\n"
                                        f"`/resume` - {tg(gi, 'resume')}\n"
                                        f"`/join` - {tg(gi, 'join')}\n"
                                        f"`/disconnect` - {tg(gi, 'die')}\n"
                                        f"`/volume` - {tg(gi, 'volume')}"
                    , inline=False)
    embed.add_field(name="Context Menu", value=f"`Add to queue` - {tg(gi, 'queue_add')}\n"
                                               f"`Show Profile` - {tg(gi, 'profile')}\n"
                                               f"`Play now` - {tg(gi, 'play')}")

    embed.add_field(name="Admin Commands (only for bot owner)", value=f"`/zz_announce` - \n"
                                                 f"`/zz_rape` - \n"
                                                 f"`/zz_rape_play` - \n"
                                                 f"`/zz_kys` - \n"
                                                 f"`/zz_config` - \n"
                                                 f"`/zz_log` - \n"
                                                 f"`/zz_change_config` - \n"
                    , inline=False)

    if command == 'help':
        embed = discord.Embed(title="Help", description=f"`/help` - {tg(gi, 'help')}")
        embed.add_field(name=f"{tg(gi, 'Arguments')}", value=f"`general` - {tg(gi, 'The commands from')} General\n"
                                                f"`player` - {tg(gi, 'The commands from')} Player\n"
                                                f"`queue` - {tg(gi, 'The commands from')} Queue\n"
                                                f"`voice` - {tg(gi, 'The commands from')} Voice"
                        , inline=False)

    elif command == 'ping':
        embed = discord.Embed(title="Help", description=f"`/ping` - {tg(gi, 'ping')}")

    elif command == 'language':
        embed = discord.Embed(title="Help", description=f"`/language` - {tg(gi, 'language')}")
        embed.add_field(name=f"{tg(gi, 'Arguments')}", value=f"`country_code` - {tg(gi, 'country_code')}", inline=False)

    elif command == 'sound_effects':
        embed = discord.Embed(title="Help", description=f"`/sound_effects` - {tg(gi, 'sound')}")
        embed.add_field(name=f"{tg(gi, 'Arguments')}", value=f"`user_only` - {tg(gi, 'ephemeral')}", inline=False)

    elif command == 'list_radios':
        embed = discord.Embed(title="Help", description=f"`/list_radios` - {tg(gi, 'list_radios')}")
        embed.add_field(name=f"{tg(gi, 'Arguments')}", value=f"`user_only` - {tg(gi, 'ephemeral')}", inline=False)

    elif command == 'key':
        embed = discord.Embed(title="Help", description=f"`/key` - {tg(gi, 'key')}")

    elif command == 'play':
        embed = discord.Embed(title="Help", description=f"`/play` - {tg(gi, 'play')}")
        embed.add_field(name=f"{tg(gi, 'Arguments')}", value=f"`url` - {tg(gi, 'url')}", inline=False)
        embed.add_field(name="", value=f"`force` - {tg(gi, 'force')}", inline=False)

    elif command == 'radio':
        embed = discord.Embed(title="Help", description=f"`/radio` - {tg(gi, 'radio')}")
        embed.add_field(name=f"{tg(gi, 'Arguments')}", value=f"`favourite_radio` - {tg(gi, 'favourite_radio')}", inline=False)
        embed.add_field(name="", value=f"`radio_code` - {tg(gi, 'radio_code')}", inline=False)

    elif command == 'ps':
        embed = discord.Embed(title="Help", description=f"`/ps` - {tg(gi, 'ps')}")
        embed.add_field(name=f"{tg(gi, 'Arguments')}", value=f"`effect_number` - {tg(gi, 'effects_number')}", inline=False)

    elif command == 'skip':
        embed = discord.Embed(title="Help", description=f"`/skip` - {tg(gi, 'skip')}")

    elif command == 'nowplaying':
        embed = discord.Embed(title="Help", description=f"`/nowplaying` - {tg(gi, 'nowplaying')}")
        embed.add_field(name=f"{tg(gi, 'Arguments')}", value=f"`user_only` - {tg(gi, 'ephemeral')}", inline=False)

    elif command == 'last':
        embed = discord.Embed(title="Help", description=f"`/last` - {tg(gi, 'last')}")
        embed.add_field(name=f"{tg(gi, 'Arguments')}", value=f"`user_only` - {tg(gi, 'ephemeral')}", inline=False)

    elif command == 'loop':
        embed = discord.Embed(title="Help", description=f"`/loop` - {tg(gi, 'loop')}")

    elif command == 'loop_this':
        embed = discord.Embed(title="Help", description=f"`/loop_this` - {tg(gi, 'loop_this')}")

    elif command == 'queue':
        embed = discord.Embed(title="Help", description=f"`/queue` - {tg(gi, 'queue_add')}")
        embed.add_field(name=f"{tg(gi, 'Arguments')}", value=f"`url` - {tg(gi, 'url')}", inline=False)
        embed.add_field(name="", value=f"`position` - {tg(gi, 'pos')}", inline=False)
        embed.add_field(name="", value=f"`mute_response` - {tg(gi, 'mute_response')}", inline=False)
        embed.add_field(name="", value=f"`force` - {tg(gi, 'force')}", inline=False)

    elif command == 'next_up':
        embed = discord.Embed(title="Help", description=f"`/next_up` - {tg(gi, 'next_up')}")
        embed.add_field(name=f"{tg(gi, 'Arguments')}", value=f"`url` - {tg(gi, 'url')}", inline=False)
        embed.add_field(name="", value=f"`user_only` - {tg(gi, 'ephemeral')}", inline=False)

    elif command == 'remove':
        embed = discord.Embed(title="Help", description=f"`/remove` - {tg(gi, 'remove')}")
        embed.add_field(name=f"{tg(gi, 'Arguments')}", value=f"`number` - {tg(gi, 'number')}", inline=False)
        embed.add_field(name="", value=f"`user_only` - {tg(gi, 'ephemeral')}", inline=False)

    elif command == 'clear':
        embed = discord.Embed(title="Help", description=f"`/clear` - {tg(gi, 'clear')}")
        embed.add_field(name=f"{tg(gi, 'Arguments')}", value=f"`user_only` - {tg(gi, 'ephemeral')}", inline=False)

    elif command == 'shuffle':
        embed = discord.Embed(title="Help", description=f"`/shuffle` - {tg(gi, 'shuffle')}")
        embed.add_field(name=f"{tg(gi, 'Arguments')}", value=f"`user_only` - {tg(gi, 'ephemeral')}", inline=False)

    elif command == 'show':
        embed = discord.Embed(title="Help", description=f"`/show` - {tg(gi, 'show')}")
        embed.add_field(name=f"{tg(gi, 'Arguments')}", value=f"`display_type` - {tg(gi, 'display_type')}", inline=False)
        embed.add_field(name="", value=f"`user_only` - {tg(gi, 'ephemeral')}", inline=False)

    elif command == 'search':
        embed = discord.Embed(title="Help", description=f"`/search` - {tg(gi, 'search')}")
        embed.add_field(name=f"{tg(gi, 'Arguments')}", value=f"`search_query` - {tg(gi, 'search_query')}", inline=False)
        embed.add_field(name="", value=f"`user_only` - {tg(gi, 'ephemeral')}", inline=False)

    elif command == 'stop':
        embed = discord.Embed(title="Help", description=f"`/stop` - {tg(gi, 'stop')}")

    elif command == 'pause':
        embed = discord.Embed(title="Help", description=f"`/pause` - {tg(gi, 'pause')}")

    elif command == 'resume':
        embed = discord.Embed(title="Help", description=f"`/resume` - {tg(gi, 'resume')}")

    elif command == 'join':
        embed = discord.Embed(title="Help", description=f"`/join` - {tg(gi, 'join')}")
        embed.add_field(name=f"{tg(gi, 'Arguments')}", value=f"`channel_id` - {tg(gi, 'channel_id')}", inline=False)

    elif command == 'disconnect':
        embed = discord.Embed(title="Help", description=f"`/disconnect` - {tg(gi, 'die')}")

    elif command == 'volume':
        embed = discord.Embed(title="Help", description=f"`/volume` - {tg(gi, 'volume')}")
        embed.add_field(name=f"{tg(gi, 'Arguments')}", value=f"`volume` - {tg(gi, 'volume')}", inline=False)
        embed.add_field(name="", value=f"`user_only` - {tg(gi, 'ephemeral')}", inline=False)

    await ctx.reply(embed=embed, ephemeral=True)

# ---------------------------- WEB FUNCTIONS ---------------------------- #

async def move_def(ctx, org_number, destination_number, ephemeral=True):
    log(ctx, 'web_move', [org_number, destination_number], log_type='function', author=ctx.author)
    is_ctx, guild_id, author_id, guild_object = ctx_check(ctx)
    queue_length = len(guild[guild_id].queue)

    if queue_length == 0:
        log(ctx, "move_def -> No songs in queue")
        message = tg(guild_id, "No songs in queue")
        await ctx.reply(message, ephemeral=ephemeral)
        return [False, message]

    org_number = int(org_number)
    destination_number = int(destination_number)

    if queue_length-1 >= org_number >= 0:
        if queue_length-1 >= destination_number >= 0:
            video = guild[guild_id].queue.pop(org_number)
            guild[guild_id].queue.insert(destination_number, video)

            save_json()

            message = f"Moved #{org_number} to #{destination_number} : {video.title}"
            await ctx.reply(message, ephemeral=ephemeral)
            return [True, message]

        message = f'Destination number must be between 0 and {queue_length - 1}'
        log(guild_id, f"move_def -> {message}")
        await ctx.reply(message, ephemeral=ephemeral)
        return [False, message]

    message = f'Original number must be between 0 and {queue_length - 1}'
    log(guild_id, f"move_def -> {message}")
    await ctx.reply(message, ephemeral=ephemeral)
    return [False, message]

async def web_up(web_data, number):
    log(web_data, 'web_up', [number], log_type='function', author=web_data.author)
    guild_id = web_data.guild_id
    queue_length = len(guild[guild_id].queue)
    number = int(number)

    if queue_length == 0:
        log(guild_id, "web_up -> No songs in queue")
        return [False, 'No songs in queue']

    if number == 0:
        return await move_def(web_data, 0, queue_length-1)

    return await move_def(web_data, number, number-1)

async def web_down(web_data, number):
    log(web_data, 'web_down', [number], log_type='function', author=web_data.author)
    guild_id = web_data.guild_id
    queue_length = len(guild[guild_id].queue)
    number = int(number)

    if queue_length == 0:
        log(guild_id, "web_down -> No songs in queue")
        return [False, 'No songs in queue']

    if number == queue_length-1:
        return await move_def(web_data, number, 0)

    return await move_def(web_data, number, number+1)

async def web_top(web_data, number):
    log(web_data, 'web_top', [number], log_type='function', author=web_data.author)
    guild_id = web_data.guild_id
    queue_length = len(guild[guild_id].queue)
    number = int(number)

    if queue_length == 0:
        log(guild_id, "web_top -> No songs in queue")
        return [False, 'No songs in queue']

    if number == 0:
        log(guild_id, "web_top -> Already at the top")
        return [False, 'Already at the top']

    return await move_def(web_data, number, 0)

async def web_bottom(web_data, number):
    log(web_data, 'web_bottom', [number], log_type='function', author=web_data.author)
    guild_id = web_data.guild_id
    queue_length = len(guild[guild_id].queue)
    number = int(number)

    if queue_length == 0:
        log(guild_id, "web_bottom -> No songs in queue")
        return [False, 'No songs in queue']

    if number == queue_length-1:
        log(guild_id, "web_bottom -> Already at the bottom")
        return [False, 'Already at the bottom']

    return await move_def(web_data, number, queue_length-1)

async def web_queue(web_data, video_type, position=None):
    log(web_data, 'web_queue', [video_type, position], log_type='function', author=web_data.author)
    guild_id = web_data.guild_id

    if video_type == 'np':
        video = guild[guild_id].now_playing
    else:
        try:
            index = int(video_type[1:])
            video = guild[guild_id].history[index]
        except (TypeError, ValueError, IndexError):
            log(guild_id, "web_queue -> Invalid video type")
            return [False, 'Invalid video type (Internal web error -> contact developer)']

    if video.class_type == 'Radio':
        return await web_queue_from_radio(web_data, video.radio_name, position)

    try:
        await to_queue(guild_id, video, position)

        save_json()
        log(guild_id, "web_queue -> Queued")
        return [True, f'Queued {video.title}', video]

    except Exception as e:
        log(guild_id, f"web_queue -> Error while queuing: {e}")
        return [False, 'Error while queuing (Internal web error -> contact developer)']

async def web_queue_from_radio(web_data, radio_name, position=None):
    log(web_data, 'web_queue_from_radio', [radio_name, position], log_type='function', author=web_data.author)

    if radio_name in radio_dict.keys():
        video = VideoClass('Radio', web_data.author_id, radio_name=radio_name)

        if position == 'start':
            guild[web_data.guild_id].queue.insert(0, video)
        else:
            guild[web_data.guild_id].queue.append(video)

        message = f'`{video.title}` added to queue!'
        save_json()
        return [True, message, video]

    else:
        message = f'Radio station `{radio_name}` does not exist!'
        save_json()
        return [False, message]

async def web_join(web_data, form):
    log(web_data, 'web_join', [form], log_type='function', author=web_data.author)

    if form['join_btn'] == 'id':
        channel_id = form['channel_id']
    elif form['join_btn'] == 'name':
        channel_id = form['channel_name']
    else:
        return [False, 'Invalid channel id (Internal web error -> contact developer)']

    try:
        channel_id = int(channel_id)
    except ValueError:
        return [False, f'Invalid channel id: {channel_id}']

    task = asyncio.run_coroutine_threadsafe(join_def(web_data, channel_id), bot.loop)

    return task.result()

async def web_disconnect(web_data):
    log(web_data, 'web_disconnect', [], log_type='function', author=web_data.author)

    task = asyncio.run_coroutine_threadsafe(disconnect_def(web_data), bot.loop)

    return task.result()

async def web_edit(web_data, form):
    log(web_data, 'web_edit', [form], log_type='function', author=web_data.author)
    guild_id = web_data.guild_id
    index = form['edit_btn']
    is_queue = True
    is_np = False

    if index == 'np':
        is_np = True

    elif not index.isdigit():
        is_queue = False
        try:
            index = int(index[1:])
            if index < 0 or index >= len(guild[guild_id].history):
                return [False, 'Invalid index (out of range)']
        except (TypeError, ValueError, IndexError):
            return [False, 'Invalid index (not a number)']

    elif index.isdigit():
        is_queue = True
        index = int(index)
        if index < 0 or index >= len(guild[guild_id].queue):
            return [False, 'Invalid index (out of range)']

    else:
        return [False, 'Invalid index (not a number)']

    class_type = form['class_type']
    author = form['author']
    created_at = form['created_at']
    url = form['url']
    title = form['title']
    picture = form['picture']
    duration = form['duration']
    channel_name = form['channel_name']
    channel_link = form['channel_link']
    radio_name = form['radio_name']
    radio_website = form['radio_website']
    local_number = form['local_number']

    none_list = ['None', '']

    if author in none_list: author = None
    if url in none_list: url = None
    if title in none_list: title = None
    if picture in none_list: picture = None
    if duration in none_list: duration = None
    if channel_name in none_list: channel_name = None
    if channel_link in none_list: channel_link = None
    if radio_name in none_list: radio_name = None
    if radio_website in none_list: radio_website = None
    if local_number in none_list: local_number = None

    if class_type not in ['Video', 'Radio', 'Local', 'Probe', 'SoundCloud']:
        return [False, f'Invalid class type: {class_type}']

    if created_at:
        if not created_at.isdigit():
            return [False, f'Invalid struct time: {created_at}']
        created_at = int(created_at)

    if local_number:
        if not local_number.isdigit():
            return [False, f'Invalid local number: {local_number}']
        local_number = int(local_number)

    if author and author.isdigit():
        author = int(author)

    if duration and duration.isdigit():
        duration = int(duration)


    if is_np:
        guild[guild_id].now_playing = VideoClass(class_type, author, url, title, picture, duration, channel_name, channel_link, radio_name, radio_website, local_number, created_at)
    else:
        if is_queue:
            guild[guild_id].queue[index] = VideoClass(class_type, author, url, title, picture, duration, channel_name, channel_link, radio_name, radio_website, local_number, created_at)
        else:
            guild[guild_id].history[index] = VideoClass(class_type, author, url, title, picture, duration, channel_name, channel_link, radio_name, radio_website, local_number, created_at)

    save_json()

    return [True, f'Edited item {"h" if not is_queue else ""}{index} successfully!']

async def web_options_edit(web_data, form):
    log(web_data, 'web_options_edit', [form], log_type='function', author=web_data.author)
    try:
        guild_id = int(form['id'])
        options  = guild[guild_id].options
    except (TypeError, ValueError, KeyError):
        return [False, f'Invalid guild id: {form["id"]}']

    stopped = form['stopped']
    loop = form['loop']
    is_radio = form['is_radio']
    language = form['language']
    response_type = form['response_type']
    search_query = form['search_query']
    buttons = form['buttons']
    volume = form['volume']
    buffer = form['buffer']
    history_length = form['history_length']

    bool_list_t = ['True', 'true', '1']
    bool_list_f = ['False', 'false', '0']
    bool_list = bool_list_f + bool_list_t
    response_types = ['long', 'short']

    if stopped not in bool_list:
        return [False, f'stopped has to be: {bool_list} --> {stopped}']
    if loop not in bool_list:
        return [False, f'loop has to be: {bool_list} --> {loop}']
    if is_radio not in bool_list:
        return [False, f'is_radio has to be: {bool_list} --> {is_radio}']
    if buttons not in bool_list:
        return [False, f'buttons has to be: {bool_list} --> {buttons}']

    if response_type not in response_types:
        return [False, f'response_type has to be: {response_types} --> {response_type}']

    if language not in languages_dict:
        return [False, f'language has to be: {languages_dict}']


    if not is_float(volume):
        return [False, f'volume has to be a number: {volume}']
    if not buffer.isdigit():
        return [False, f'buffer has to be a number: {buffer}']
    if not history_length.isdigit():
        return [False, f'history_length has to be a number: {history_length}']

    options.stopped = to_bool(stopped)
    options.loop = to_bool(loop)
    options.is_radio = to_bool(is_radio)
    options.buttons = to_bool(buttons)

    options.language = language
    options.search_query = search_query
    options.response_type = response_type

    options.volume = float(volume)
    options.buffer = int(buffer)
    options.history_length = int(history_length)

    return [True, f'Edited options successfully!']

# --------------------------------------------- WEB SERVER --------------------------------------------- #

app = Flask(__name__)
app.config['SECRET_KEY'] = config.WEB_SECRET_KEY

@app.route('/')
async def index_page():
    log(request.remote_addr, '/index', log_type='ip')
    if 'discord_user' in session.keys(): user = session['discord_user']
    else: user = None

    return render_template('nav/index.html', user=user)

@app.route('/about')
async def about_page():
    log(request.remote_addr, '/about', log_type='ip')
    if 'discord_user' in session.keys():
        user = session['discord_user']
    else:
        user = None

    return render_template('nav/about.html', user=user)

@app.route('/guild')
async def guilds_page():
    log(request.remote_addr, '/guild', log_type='ip')
    if 'discord_user' in session.keys():
        user = session['discord_user']
        mutual_guild_ids = session['mutual_guild_ids']
    elif 'mutual_guild_ids' in session.keys():
        mutual_guild_ids = session['mutual_guild_ids']
        user = None
        if mutual_guild_ids is None:
            mutual_guild_ids = []
            session['mutual_guild_ids'] = []
    else:
        user = None
        mutual_guild_ids = []

    def sort_list(val_lst, key_lst):
        if not key_lst:
            return dict(val_lst)
        return dict(sorted(val_lst, key=lambda x: key_lst.index(x[0]) if x[0] in key_lst else len(key_lst)))

    return render_template('nav/guild_list.html', guild=sort_list(guild.items(), mutual_guild_ids).values(), len=len, user=user, errors=None, mutual_guild_ids=mutual_guild_ids)

@app.route('/guild/<guild_id>', methods=['GET', 'POST'])
async def guild_get_key_page(guild_id):
    log(request.remote_addr, f'/guild/{guild_id}', log_type='ip')
    if 'discord_user' in session.keys():
        user = session['discord_user']
        mutual_guild_ids = session['mutual_guild_ids']
    elif 'mutual_guild_ids' in session.keys():
        mutual_guild_ids = session['mutual_guild_ids']
        user = None
        if mutual_guild_ids is None:
            mutual_guild_ids = []
            session['mutual_guild_ids'] = []
    else:
        user = None
        mutual_guild_ids = []

    try:
        guild_object = guild[int(guild_id)]
    except (KeyError, ValueError, TypeError):
        return render_template('base/message.html', guild_id=guild_id, user=user, message="That Server doesn't exist or the bot is not in it", errors=None, title='Error')

    if guild_object.id in mutual_guild_ids:
        return redirect(f'/guild/{guild_id}&key={guild_object.data.key}')

    if request.method == 'POST':
        if 'key' in request.form.keys():
            if request.form['key'] == guild_object.data.key:
                if 'mutual_guild_ids' not in session.keys():
                    session['mutual_guild_ids'] = []

                session['mutual_guild_ids'] = session['mutual_guild_ids'] + [guild_object.id]
                # mutual_guild_ids = session['mutual_guild_ids']

                return redirect(f'/guild/{guild_id}&key={request.form["key"]}')

        return render_template('control/action/get_key.html', guild_id=guild_id, errors=[f'Invalid code: {request.form["key"]} -> do /key in the server'], url=Oauth.discord_login_url, user=user)

    return render_template('control/action/get_key.html', guild_id=guild_id, errors=None, url=Oauth.discord_login_url, user=user)

@app.route('/guild/<guild_id>&key=<key>', methods=['GET', 'POST'])
async def guild_page(guild_id, key):
    log(request.remote_addr, f'/guild/{guild_id}&key={key}', log_type='ip')
    admin = False
    user = None
    user_name, user_id = request.remote_addr, 'WEB Guest'
    errors = []
    messages = []
    scroll_position = 0

    if 'discord_user' in session.keys():
        user = session['discord_user']
        user_name, user_id = user['username'], int(user['id'])
        mutual_guild_ids = session['mutual_guild_ids']
    elif 'mutual_guild_ids' in session.keys():
        mutual_guild_ids = session['mutual_guild_ids']
    else:
        mutual_guild_ids = []

    if user_id == my_id or user_id == config.OWNER_ID:
        admin = True

    if request.method == 'POST':
        web_data = WebData(int(guild_id), user_name, user_id)
        response = None

        keys = request.form.keys()
        if 'del_btn' in keys:
            log(web_data, 'remove', [request.form['del_btn']], log_type='web', author=web_data.author)
            response = await remove_def(web_data, int(request.form['del_btn']))
        if 'up_btn' in keys:
            log(web_data, 'up', [request.form['up_btn']], log_type='web', author=web_data.author)
            response = await web_up(web_data, request.form['up_btn'])
        if 'down_btn' in keys:
            log(web_data, 'down', [request.form['down_btn']], log_type='web', author=web_data.author)
            response = await web_down(web_data, request.form['down_btn'])
        if 'top_btn' in keys:
            log(web_data, 'top', [request.form['top_btn']], log_type='web', author=web_data.author)
            response = await web_top(web_data, request.form['top_btn'])
        if 'bottom_btn' in keys:
            log(web_data, 'bottom', [request.form['bottom_btn']], log_type='web', author=web_data.author)
            response = await web_bottom(web_data, request.form['bottom_btn'])

        if 'play_btn' in keys:
            log(web_data, 'play', [], log_type='web', author=web_data.author)
            response = await play_def(web_data)
        if 'stop_btn' in keys:
            log(web_data, 'stop', [], log_type='web', author=web_data.author)
            response = await stop_def(web_data)
        if 'pause_btn' in keys:
            log(web_data, 'pause', [], log_type='web', author=web_data.author)
            response = await pause_def(web_data)
        if 'resume_btn' in keys:
            log(web_data, 'resume', [], log_type='web', author=web_data.author)
            response = await resume_def(web_data)

        if 'skip_btn' in keys:
            log(web_data, 'skip', [], log_type='web', author=web_data.author)
            response = await skip_def(web_data)
        if 'shuffle_btn' in keys:
            log(web_data, 'shuffle', [], log_type='web', author=web_data.author)
            response = await shuffle_def(web_data)
        if 'clear_btn' in keys:
            log(web_data, 'clear', [], log_type='web', author=web_data.author)
            response = await clear_def(web_data)

        if 'disconnect_btn' in keys:
            log(web_data, 'disconnect', [], log_type='web', author=web_data.author)
            response = await web_disconnect(web_data)
        if 'join_btn' in keys:
            log(web_data, 'join', [], log_type='web', author=web_data.author)
            response = await web_join(web_data, request.form)

        if 'queue_btn' in keys:
            log(web_data, 'queue', [request.form['queue_btn']], log_type='web', author=web_data.author)
            response = await web_queue(web_data, request.form['queue_btn'])
        if 'nextup_btn' in keys:
            log(web_data, 'nextup', [request.form['nextup_btn'], 0], log_type='web', author=web_data.author)
            response = await web_queue(web_data, request.form['nextup_btn'], 0)
        if 'hdel_btn' in keys:
            log(web_data, 'history remove', [request.form['hdel_btn']], log_type='web', author=web_data.author)
            response = await remove_def(web_data, int(request.form['hdel_btn'][1:]), list_type='history')

        if 'edit_btn' in keys:
            log(web_data, 'web_edit', [request.form['edit_btn']], log_type='web', author=web_data.author)
            response = await web_edit(web_data, request.form)

        if 'volume_btn' in keys:
            log(web_data, 'volume_command_def', [request.form['volumeRange'], request.form['volumeInput']], log_type='web', author=web_data.author)
            response = await volume_command_def(web_data, request.form['volumeRange'], request.form['volumeInput'])

        if 'ytURL' in keys:
            log(web_data, 'queue_command_def', [request.form['ytURL']], log_type='web', author=web_data.author)
            response = await queue_command_def(web_data, request.form['ytURL'])
        if 'radio-checkbox' in keys:
            log(web_data, 'web_queue_from_radio', [request.form['radio-checkbox']], log_type='web', author=web_data.author)
            response = await web_queue_from_radio(web_data, request.form['radio-checkbox'])

        if 'scroll' in keys:
            scroll_position = int(request.form['scroll'])

        if response:
            if not response[0]:
                errors = [response[1]]
            else:
                messages = [response[1]]

    try:
        guild_object = guild[int(guild_id)]
    except (KeyError, ValueError, TypeError):
        return render_template('base/message.html', guild_id=guild_id, user=user, message="That Server doesn't exist or the bot is not in it", errors=None, title='Error')

    if key != guild_object.data.key:
        if guild_object.id in mutual_guild_ids:
            return redirect(f'/guild/{guild_id}&key={guild_object.data.key}')

        return redirect(url_for('guild_get_key_page', guild_id=guild_id))

    mutual_guild_ids.append(guild_object.id)
    session['mutual_guild_ids'] = mutual_guild_ids

    return render_template('control/guild.html', guild=guild_object, struct_to_time=struct_to_time, convert_duration=convert_duration, get_username=get_username, errors=errors, messages=messages, user=user, admin=admin, volume=round(guild_object.options.volume * 100), radios=list(radio_dict.values()), scroll_position=scroll_position)

@app.route('/login')
async def login_page():
    log(request.remote_addr, '/login', log_type='web')
    admin = False
    if 'discord_user' in session.keys():
        user = Oauth.get_user(session['access_token'])
        collect_data(user)
        session['discord_user'] = user

        guilds = Oauth.get_user_guilds(session['access_token'])
        collect_data(f'{user["username"]} -> {guilds}')

        bot_guilds = Oauth.get_bot_guilds()
        mutual_guilds = [x for x in guilds if x['id'] in map(lambda i: i['id'], bot_guilds)]

        mutual_guild_ids = [int(guild_object['id']) for guild_object in mutual_guilds]
        session['mutual_guild_ids'] = mutual_guild_ids

        return render_template('base/message.html', message=f"Updated session for {user['username']}#{user['discriminator']}", errors=None, user=user, title='Update Success')

    code = request.args.get('code')
    if code is None:
        return redirect(Oauth.discord_login_url)

    response = Oauth.get_access_token(code)
    access_token = response['access_token']

    session['access_token'] = access_token

    user = Oauth.get_user(access_token)
    collect_data(user)
    session['discord_user'] = user

    guilds = Oauth.get_user_guilds(session['access_token'])
    collect_data(f'{user["username"]} -> {guilds}')

    bot_guilds = Oauth.get_bot_guilds()
    mutual_guilds = [x for x in guilds if x['id'] in map(lambda i:i['id'], bot_guilds)]

    mutual_guild_ids = [int(guild_object['id']) for guild_object in mutual_guilds]
    if int(user['id']) == my_id:
        mutual_guild_ids = [int(guild_object['id']) for guild_object in bot_guilds]
        admin = True
    session['mutual_guild_ids'] = mutual_guild_ids

    return render_template('base/message.html', message=f"Success, logged in as {user['username']}#{user['discriminator']}{' -> ADMIN' if admin else ''}", errors=None, user=user, title='Login Success')

@app.route('/logout')
async def logout_page():
    log(request.remote_addr, '/logout', log_type='ip')
    if 'discord_user' in session.keys():
        user = session['discord_user']
        username = user['username']
        discriminator = user['discriminator']
        session.clear()
        return render_template('base/message.html', message=f"Logged out as {username}#{discriminator}", errors=None, user=None, title='Logout Success')
    return redirect(url_for('index_page'))

@app.route('/reset')
async def reset_page():
    log(request.remote_addr, '/reset', log_type='ip')
    session.clear()
    return redirect(url_for('index_page'))

@app.route('/invite')
async def invite_page():
    log(request.remote_addr, '/invite', log_type='ip')
    return redirect(config.INVITE_URL)

@app.route('/admin', methods=['GET', 'POST'])
async def admin_page():
    log(request.remote_addr, '/admin', log_type='ip')
    if 'discord_user' in session.keys():
        user = session['discord_user']
        user_name = user['username']
        user_id = user['id']
    else:
        return render_template('base/message.html', message="You are not logged in or don't have permission", errors=None, user=None, title='Error')

    errors = []
    messages = []
    response = None

    if request.method == 'POST':
        guild_id = None
        web_data = WebData(guild_id, user_name, user_id)

        keys = request.form.keys()
        form = request.form
        try:
            if 'download_btn' in keys:
                file_name = request.form['download_file']
                log(web_data, 'download file', [file_name], log_type='web', author=web_data.author)
                try:
                    if file_name == 'log.txt' or file_name == 'data.txt' or file_name == 'activity.log':
                        return send_file(f'log/{file_name}', as_attachment=True)
                    else:
                        return send_file(f'src/{file_name}', as_attachment=True)
                except Exception as e:
                    return str(e)
            if 'upload_btn' in keys:
                f = request.files['file']
                file_name = request.form['download_file']
                log(web_data, 'upload file', [f.filename, file_name], log_type='web', author=web_data.author)
                if not f:
                    errors = ['No file']
                elif file_name != f.filename:
                    errors = ['File name does not match']
                else:
                    try:
                        if file_name == 'log.txt' or file_name == 'data.txt' or file_name == 'activity.log':
                            f.save(f"log/{f.filename}")
                            messages = ['File uploaded']
                        else:
                            f.save(f"src/{f.filename}")
                            messages = ['File uploaded']
                    except Exception as e:
                        return str(e)
            if 'edit_btn' in keys:
                log(web_data, 'edit options', [form], log_type='web', author=web_data.author)
                response = await web_options_edit(web_data, form)
        except Exception as e:
            errors = [str(e)]
            log(web_data, 'error', [str(e)], log_type='web', author=web_data.author)

        if response:
            if response[0]:
                messages = [response[1]]
            else:
                errors = [response[1]]

    if 'discord_user' in session.keys():
        user = session['discord_user']
        if int(user['id']) == my_id:
            return render_template('nav/admin.html', user=user, guild=guild.values(), languages_dict=languages_dict, errors=errors, messages=messages)
    return redirect(url_for('index_page'))

def application():
    web_thread = threading.Thread(target=app.run, kwargs={'debug': False, 'host': '0.0.0.0', 'port': int(os.environ.get('PORT', 5420))})
    bot_thread = threading.Thread(target=bot.run, kwargs={'token':config.BOT_TOKEN})

    web_thread.start()
    bot_thread.start()

    web_thread.join()
    bot_thread.join()

if __name__ == '__main__':
    application()
