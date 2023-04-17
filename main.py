import os
import random

import discord
import asyncio
from discord import FFmpegPCMAudio, app_commands
from discord.ext import commands
from discord.ui import View

from flask import Flask, render_template, request, url_for, redirect, session, send_file
import threading

import yt_dlp
import youtubesearchpython
from bs4 import BeautifulSoup
import requests
import json
import re

from os import path, listdir
import sys
from typing import Literal
import traceback
import datetime

from oauth import Oauth
import config

import functools

# ---------------- Bot class ------------

class Bot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.all()
        super().__init__(command_prefix=prefix, intents=intents)
        self.synced = False

    async def on_ready(self):
        await self.wait_until_ready()
        if not self.synced:
            log('no guild', "Trying to sync commands")
            await self.tree.sync()
            log('no guild', f"Synced slash commands for {self.user}")
        await bot.change_presence(activity=discord.Game(name=f"/help"))
        log('no guild', 'Logged in as:\n{0.user.name}\n{0.user.id}'.format(bot))

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
            now_to_last(member.guild.id)
        if not member.id == self.user.id:
            return
        elif before.channel is None:
            voice = after.channel.guild.voice_client
            time = 0
            while True:
                await asyncio.sleep(1)
                time +=  1
                if voice.is_playing() and not voice.is_paused():
                    time = 0
                if time >= guild[member.guild.id].options.buffer:  # how many seconds of inactivity to disconnect | 300 = 5min | 600 = 10min
                    guild[member.guild.id].options.stopped = True
                    voice.stop()
                    await voice.disconnect()
                    log(member.guild.id, f"-->> Disconnecting after {guild[member.guild.id].options.buffer} seconds of nothing playing <<--")
                    now_to_last(member.guild.id)
                if not voice.is_connected():
                    break

    async def on_command_error(self, ctx, error):
        if isinstance(error, commands.CheckFailure):
            log(ctx.guild.id, f'Error for ({ctx.author}) -> ({ctx.command}) with error ({error})')
            await ctx.reply("（ ͡° ͜ʖ ͡°)つ━☆・。\n"
                            "⊂　　 ノ 　　　・゜+.\n"
                            "　しーＪ　　　°。+ ´¨)\n"
                            "　　　　　　　　　.· ´¸.·´¨) ¸.·*¨)\n"
                            "　　　　　　　　　　(¸.·´ (¸.·' ☆ **Fuck off**\n"
                            "*You don't have permission to use this command*")
        else:
            log(ctx.guild.id, f"{error}")
            await ctx.reply(f"{error}   {bot.get_user(my_id).mention}", ephemeral=True)

    async def on_message(self, message):
        if message.author == bot.user:
            return
        if not message.guild:
            try:
                await message.channel.send(f"I'm sorry, but I only work in servers.\n\nIf you want me to join your server, you can invite me with this link: https://discord.com/api/oauth2/authorize?client_id=1007004463933952120&permissions=3198017&scope=bot\n\nIf you have any questions, you can DM my developer <@!{my_id}>#4272")
            except discord.errors.Forbidden:
                pass
        else:
            pass

# ---------------- Data Classes ------------

class WebData:
    def __init__(self, guild_id, author, author_id):
        self.guild_id = guild_id
        self.author = author
        self.author_id = author_id


class Options:
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


class GuildData:
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


# ----------------- Video Classes ----------------

# noinspection PyTypeChecker
class Video:
    def __init__(self, url, author, title=None, picture=None, duration=None, channel_name=None, channel_link=None):
        self.url = url
        self.author = author

        video = None

        if title is None and picture is None and duration is None and channel_name is None and channel_link is None:
            try:
                video = youtubesearchpython.Video.getInfo(url)  # mode=ResultMode.json
            except Exception as e:
                raise ValueError(f"Not a youtube link: {e}")

        self.title = title
        self.picture = picture
        self.duration = duration
        self.channel_name = channel_name
        self.channel_link = channel_link
        self.type = 'Video'

        if video:
            self.title = video['title']
            self.picture = 'https://img.youtube.com/vi/' + video['id'] + '/default.jpg'
            self.duration = video['duration']['secondsText']
            self.channel_name = video['channel']['name']
            self.channel_link = video['channel']['link']

    def renew(self):
        pass


class Radio:
    def __init__(self, name, author, radio_name):
        self.author = author
        self.url = radio_dict[radio_name]['url']

        self.picture = radio_dict[radio_name]['thumbnail']
        self.channel_name = radio_dict[radio_name]['type']
        self.channel_link = self.url
        self.title = name
        self.duration = 'Stream'
        self.radio_website = radio_dict[radio_name]['type']
        self.type = 'Radio'
        self.radio_name = radio_name

    def renew(self):
        if self.radio_website == 'radia_cz':
            html = requests.get(self.url).text
            soup = BeautifulSoup(html, features="lxml")
            data1 = soup.find('div', attrs={'class': 'interpret-image'})
            data2 = soup.find('div', attrs={'class': 'interpret-info'})

            self.picture = data1.find('img')['src']
            self.channel_name = data2.find('div', attrs={'class': 'nazev'}).text.lstrip().rstrip()
            self.title = data2.find('div', attrs={'class': 'song'}).text.lstrip().rstrip()
            self.duration = 'Stream'
        if self.radio_website == 'actve':
            r = requests.get(self.url).json()
            self.picture = r['coverBase']
            self.channel_name = r['artist']
            self.title = r['title']
            self.duration = 'Stream'


class LocalFile:
    def __init__(self, title, duration, author, number):
        self.url = None
        self.author = author
        self.title = title
        self.picture = vlc_logo
        self.duration = duration
        self.channel_name = 'Local file'
        self.channel_link = 'Local file'
        self.number = number
        self.type = 'LocalFile'

    def renew(self):
        pass


class FromProbe:
    def __init__(self, url, title, duration, author, channel_name, channel_link):
        self.url = url
        self.author = author
        self.title = title
        self.picture = vlc_logo
        self.duration = duration
        self.channel_name = channel_name
        self.channel_link = channel_link
        self.type = 'FromProbe'

    def renew(self):
        pass
    
# ------------ Guild ------------

class Guild:
    def __init__(self, guild_id):
        self.id = guild_id
        self.options = Options(guild_id)
        self.queue = []
        self.search_list = []
        self.now_playing = None
        self.last_played = Video(url='https://www.youtube.com/watch?v=dQw4w9WgXcQ',
                                 author=my_id,
                                 title='Never gonna give you up',
                                 picture='https://img.youtube.com/vi/dQw4w9WgXcQ/default.jpg',
                                 duration='3:33',
                                 channel_name='Rick Astley',
                                 channel_link='https://www.youtube.com/channel/UCuAXFkgsw1L7xaCfnd5JJOw')
        self.data = GuildData(guild_id)

    def renew(self):
        self.data = GuildData(self.id)

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
    log('no guild', 'Loaded sound_effects folder')

# ------------ PRINT --------------------

def log(guild_id, text_data, options=None, log_type='text', author=None):
    now_time = datetime.datetime.now(datetime.timezone(datetime.timedelta(seconds=3600), 'CET'))
    now_time_str = now_time.strftime('(CET) %d/%m/%Y %X')
    
    if log_type == 'command':
        message = f"{now_time_str} | C {guild_id} | Command ({text_data}) was requested by ({author}) -> {options}"
    elif log_type == 'function':
        message = f"{now_time_str} | F {guild_id} | {text_data} -> {options}"
    elif log_type == 'web':
        message = f"{now_time_str} | W {guild_id} | Command ({text_data}) was requested by ({author}) -> {options}"
    elif log_type == 'text':
        message = f"{now_time_str} | T {guild_id} | {text_data}"
    else:
        raise ValueError('Wrong log_type')
    
    print(message)

    with open("log.txt", "a", encoding="utf-8") as f:
        f.write(message + "\n")


def collect_data(data):
    now_time = datetime.datetime.now(datetime.timezone(datetime.timedelta(seconds=3600), 'CET'))
    message = f"{now_time.strftime('(CET) %d/%m/%Y %X')} | {data}\n"

    with open("data.txt", "a", encoding="utf-8") as f:
        f.write(message)


# ---------------------------------------------- GUILD TO JSON ---------------------------------------------------------


def guild_to_json(guild_object):
    guild_dict = {}
    search_dict = {}
    queue_dict = {}
    if guild_object.search_list:
        for index, video in enumerate(guild_object.search_list):
            search_dict[index] = video.__dict__

    if guild_object.queue:
        for index, video in enumerate(guild_object.queue):
            queue_dict[index] = video.__dict__

    guild_dict['id'] = guild_object.id
    guild_dict['options'] = guild_object.options.__dict__
    guild_dict['data'] = GuildData(guild_object.id).__dict__
    guild_dict['queue'] = queue_dict
    guild_dict['search_list'] = search_dict
    if guild_object.now_playing:
        guild_dict['now_playing'] = guild_object.now_playing.__dict__
    else:
        guild_dict['now_playing'] = {}
    if guild_object.last_played:
        guild_dict['last_played'] = guild_object.last_played.__dict__
    else:
        guild_dict['last_played'] = {}

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

    video = None

    if video_dict['type'] == 'Video':
        video = Video(url=video_dict['url'],
                      author=video_dict['author'],
                      title=video_dict['title'],
                      picture=video_dict['picture'],
                      duration=video_dict['duration'],
                      channel_name=video_dict['channel_name'],
                      channel_link=video_dict['channel_link'])

    if video_dict['type'] == 'Radio':
        video = Radio(author=video_dict['author'],
                      name=video_dict['title'],
                      radio_name=video_dict['radio_name'])

    if video_dict['type'] == 'LocalFile':
        video = LocalFile(author=video_dict['author'],
                          title=video_dict['title'],
                          duration=video_dict['duration'],
                          number=video_dict['number'])

    if video_dict['type'] == 'FromProbe':
        video = FromProbe(url=video_dict['url'],
                      author=video_dict['author'],
                      title=video_dict['title'],
                      duration=video_dict['duration'],
                      channel_name=video_dict['channel_name'],
                      channel_link=video_dict['channel_link'])

    return video


def json_to_guild(guild_dict):
    guild_object = Guild(guild_dict['id'])
    guild_object.options.__dict__ = guild_dict['options']
    guild_object.data.__dict__ = guild_dict['data']
    guild_object.queue = [json_to_video(video_dict) for video_dict in guild_dict['queue'].values()]
    guild_object.search_list = [json_to_video(video_dict) for video_dict in guild_dict['search_list'].values()]
    guild_object.now_playing = json_to_video(guild_dict['now_playing'])
    guild_object.last_played = json_to_video(guild_dict['last_played'])

    return guild_object


def json_to_guilds(guilds_dict):
    guilds_object = {}
    for guild_id, guild_dict in guilds_dict.items():
        guilds_object[int(guild_id)] = json_to_guild(guild_dict)

    return guilds_object

# ---------------------------------------------- LOAD -------------------------------------------------------------
log('no guild', "--------------------------------------- NEW / REBOOTED ----------------------------------------")


build_new_guilds = False

with open('src/radio.json', 'r') as file:
    radio_dict = json.load(file)
log('no guild', 'Loaded radio.json')


with open('src/languages.json', 'r') as file:
    languages_dict = json.load(file)
    text = languages_dict['en']
log('no guild', 'Loaded languages.json')


with open('src/other.json', 'r') as file:
    other = json.load(file)
    react_dict = other['reactions']
    prefix = other['prefix']
    my_id = other['my_id']
    bot_id = other['bot_id']
    vlc_logo = other['logo']
    authorized_users = other['authorized']
log('no guild', 'Loaded other.json')


# ---------------------------------------------- BOT -------------------------------------------------------------------

bot = Bot()

log('no guild', 'Bot class initialized')

# ----------------------------------------------------------------------------------------------------------------------


if build_new_guilds:
    log('no guild', 'Building new guilds.json ...')
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
log('no guild', 'Loaded guilds.json')


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
    return languages_dict[lang][content]

# --------- video_info / url --------

def get_playlist_from_url(url: str):
    try:
        code = url[url.index('&list=')+1:url.index('&index=')]
    except ValueError:
        code = url[url.index('&list=')+1:]
    playlist_url = 'https://www.youtube.com/playlist?' + code
    return playlist_url

def extract_yt_id(url_string: str):
    magic_regex = "^(?:https?://|//)?(?:www\.|m\.|.+\.)?(?:youtu\.be/|youtube\.com/(?:embed/|v/|shorts/|feeds/api/videos/|watch\?v=|watch\?.+&v=))([\w-]{11})(?![\w-])"
    regex = re.compile(magic_regex)
    results = regex.search(url_string)

    if results is None:
        return None
    return results.group(1)

# -------------- convert / get -----------

def get_username(user_id: int):
    try:
        name = bot.get_user(int(user_id)).name
        return name
    except Exception as e:
        print(f"get_username failed for ({user_id}) : {e}")
        return user_id


def now_to_last(guild_id: int):
    if guild[guild_id].now_playing is not None:
        guild[guild_id].last_played = guild[guild_id].now_playing
        guild[guild_id].now_playing = None
        save_json()


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

# ---------------EMBED--------------

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

    return embed

# ------------- Youtube DL classes -----------


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


class YTDLError(Exception):
    pass


class YTDLSource(discord.PCMVolumeTransformer):
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

    ytdl = yt_dlp.YoutubeDL(YTDL_OPTIONS)

    def __init__(self, ctx: commands.Context, source: discord.FFmpegPCMAudio, *, data: dict):
        super().__init__(source, guild[ctx.guild.id].options.volume)

        self.requester = ctx.author
        self.channel = ctx.channel
        self.data = data

        self.uploader = data.get('uploader')
        self.uploader_url = data.get('uploader_url')
        date = data.get('upload_date')
        self.upload_date = date[6:8] + '.' + date[4:6] + '.' + date[0:4]
        self.title = data.get('title')
        self.thumbnail = data.get('thumbnail')
        self.description = data.get('description')
        self.tags = data.get('tags')
        self.url = data.get('webpage_url')
        self.views = data.get('view_count')
        self.likes = data.get('like_count')
        self.dislikes = data.get('dislike_count')
        self.stream_url = data.get('url')

    def __str__(self):
        return '**{0.title}** by **{0.uploader}**'.format(self)

    @classmethod
    async def create_source(cls, ctx: commands.Context, cr_search: str, *, cr_loop: asyncio.BaseEventLoop = None):
        cr_loop = cr_loop or asyncio.get_event_loop()

        partial = functools.partial(cls.ytdl.extract_info, cr_search, download=False, process=False)
        data = await cr_loop.run_in_executor(None, partial)

        if data is None:
            raise YTDLError('Couldn\'t find anything that matches `{}`'.format(cr_search))

        if 'entries' not in data:
            process_info = data
        else:
            process_info = None
            for entry in data['entries']:
                if entry:
                    process_info = entry
                    break

            if process_info is None:
                raise YTDLError('Couldn\'t find anything that matches `{}`'.format(cr_search))

        webpage_url = process_info['webpage_url']
        partial = functools.partial(cls.ytdl.extract_info, webpage_url, download=False)
        processed_info = await cr_loop.run_in_executor(None, partial)

        if processed_info is None:
            raise YTDLError('Couldn\'t fetch `{}`'.format(webpage_url))

        if 'entries' not in processed_info:
            info = processed_info
        else:
            info = None
            while info is None:
                try:
                    info = processed_info['entries'].pop(0)
                except IndexError:
                    raise YTDLError('Couldn\'t retrieve any matches for `{}`'.format(webpage_url))

        return cls(ctx, discord.FFmpegPCMAudio(info['url'], **cls.FFMPEG_OPTIONS), data=info)

    @staticmethod
    def parse_duration(duration: int):
        minutes, seconds = divmod(duration, 60)
        hours, minutes = divmod(minutes, 60)
        days, hours = divmod(hours, 24)

        duration = []
        if days > 0:
            duration.append('{} days'.format(days))
        if hours > 0:
            duration.append('{} hours'.format(hours))
        if minutes > 0:
            duration.append('{} minutes'.format(minutes))
        if seconds > 0:
            duration.append('{} seconds'.format(seconds))

        return ', '.join(duration)


# ------------------------------------ View Classes --------------------------------------------------------------------


class PlayerControlView(View):

    def __init__(self, ctx):
        super().__init__(timeout=7200)
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
        await interaction.response.edit_message(content=f'[`{video.title}`](<{video.url}>) '
                                                        f'{tg(self.guild_id, "added to queue!")}', view=None)
        if self.from_play:
            await play_def(self.ctx)


class PlaylistOptionView(View):

    def __init__(self, ctx, url, force=False, from_play=False):
        super().__init__(timeout=180)
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
            response = await queue_command_def(self.ctx, playlist_url, 0, True, self.force)
        else:
            response = await queue_command_def(self.ctx, playlist_url, None, True, self.force)

        msg = await interaction.original_response()
        await msg.edit(content=response[1])

        if self.from_play:
            await play_def(self.ctx)

    # noinspection PyUnusedLocal
    @discord.ui.button(label='No, just this', style=discord.ButtonStyle.blurple)
    async def callback_2(self, interaction, button):
        pure_url = self.url[:self.url.index('&list=')]
        if self.force:
            response = await queue_command_def(self.ctx, pure_url, 0, True, self.force)
        else:
            response = await queue_command_def(self.ctx, pure_url, None, True, self.force)
        await interaction.response.edit_message(content=response[1], view=None)
        if self.from_play:
            await play_def(self.ctx)


# --------------------------------------- QUEUE --------------------------------------------------


@bot.hybrid_command(name='queue', with_app_command=True, description=text['queue_add'], help=text['queue_add'])
@app_commands.describe(url=text['url'], position=text['pos'])
async def queue_command(ctx: commands.Context,
                        url,
                        position: int = None,
                        ):
    log(ctx.guild.id, 'queue', [url, position], log_type='command', author=ctx.author)

    await queue_command_def(ctx, url, position)


@bot.hybrid_command(name='next_up', with_app_command=True, description=text['next_up'], help=text['next_up'])
@app_commands.describe(url=text['url'], user_only=text['ephemeral'])
async def next_up(ctx: commands.Context,
                 url,
                 user_only: bool = False
                 ):
    log(ctx.guild.id, 'next_up', [url, user_only], log_type='command', author=ctx.author)

    await next_up_def(ctx, url, user_only)


@bot.hybrid_command(name='skip', with_app_command=True, description=text['skip'], help=text['skip'])
async def skip(ctx: commands.Context):
    log(ctx.guild.id, 'skip', [], log_type='command', author=ctx.author)

    await skip_def(ctx)


@bot.hybrid_command(name='remove', with_app_command=True, description=text['queue_remove'], help=text['queue_remove'])
@app_commands.describe(number=text['number'], user_only=text['ephemeral'])
async def remove(ctx: commands.Context,
                 number: int,
                 user_only: bool = False
                 ):
    log(ctx.guild.id, 'remove', [number, user_only], log_type='command', author=ctx.author)

    await remove_def(ctx, number, ephemeral=user_only)


@bot.hybrid_command(name='clear', with_app_command=True, description=text['clear'], help=text['clear'])
@app_commands.describe(user_only=text['ephemeral'])
async def clear(ctx: commands.Context,
                 user_only: bool = False
                 ):
    log(ctx.guild.id, 'clear', [user_only], log_type='command', author=ctx.author)

    await clear_def(ctx, user_only)


@bot.hybrid_command(name='shuffle', with_app_command=True, description=text['shuffle'], help=text['shuffle'])
@app_commands.describe(user_only=text['ephemeral'])
async def shuffle(ctx: commands.Context,
                 user_only: bool = False
                 ):
    log(ctx.guild.id, 'shuffle', [user_only], log_type='command', author=ctx.author)

    await shuffle_def(ctx, user_only)


@bot.hybrid_command(name='show', with_app_command=True, description=text['queue_show'], help=text['queue_show'])
@app_commands.describe(display_type=text['display_type'], user_only=text['ephemeral'])
async def show(ctx: commands.Context,
               display_type: Literal['short', 'medium', 'long'] = None,
               user_only: bool = False
               ):
    log(ctx.guild.id, 'show', [display_type, user_only], log_type='command', author=ctx.author)

    await show_def(ctx, display_type, user_only)


@bot.hybrid_command(name='search', with_app_command=True, description=text['search'],  help=text['search'])
@app_commands.describe(search_query=text['search_query'])
async def search_command(ctx: commands.Context,
                         search_query,
                         ):
    log(ctx.guild.id, 'search', [search_query], log_type='command', author=ctx.author)

    await search_command_def(ctx, search_query)

# --------------------------------------- PLAYER --------------------------------------------------


@bot.hybrid_command(name='play', with_app_command=True, description=text['play'], help=text['play'])
@app_commands.describe(url=text['play'], force=text['force'])
async def play(ctx: commands.Context,
               url=None,
               force=False
               ):
    log(ctx.guild.id, 'play', [url, force], log_type='command', author=ctx.author)

    await play_def(ctx, url, force)


@bot.hybrid_command(name='radio', with_app_command=True, description=text['radio'], help=text['radio'])
@app_commands.describe(favourite_radio=text['favourite_radio'], radio_code=text['radio_code'])
async def radio(ctx: commands.Context,
                favourite_radio: Literal['Rádio BLANÍK','Rádio BLANÍK CZ','Evropa 2','Fajn Radio','Hitrádio PopRock','Český rozhlas Pardubice','Radio Beat','Country Radio','Radio Kiss','Český rozhlas Vltava','Hitrádio Černá Hora'] = None,
                radio_code: int = None,
                ):
    log(ctx.guild.id, 'radio', [favourite_radio, radio_code], log_type='command', author=ctx.author)

    await radio_def(ctx, favourite_radio, radio_code)


@bot.hybrid_command(name='ps', with_app_command=True, description=text['ps'], help=text['ps'])
@app_commands.describe(effect_number=text['effects_number'])
async def ps(ctx: commands.Context,
             effect_number: app_commands.Range[int, 1, len(all_sound_effects)]
             ):
    log(ctx.guild.id, 'ps', [effect_number], log_type='command', author=ctx.author)

    await ps_def(ctx, effect_number)


@bot.hybrid_command(name='nowplaying', with_app_command=True, description=text['nowplaying'], help=text['nowplaying'])
@app_commands.describe(user_only=text['ephemeral'])
async def nowplaying(ctx: commands.Context,
              user_only: bool = False
              ):
    log(ctx.guild.id, 'nowplaying', [user_only], log_type='command', author=ctx.author)

    await now_def(ctx, user_only)


@bot.hybrid_command(name='last', with_app_command=True, description=text['last'], help=text['last'])
@app_commands.describe(user_only=text['ephemeral'])
async def last(ctx: commands.Context,
              user_only: bool = False
              ):
    log(ctx.guild.id, 'last', [user_only], log_type='command', author=ctx.author)

    await last_def(ctx, user_only)

@bot.hybrid_command(name='loop', with_app_command=True, description=text['loop'], help=text['loop'])
async def loop_command(ctx: commands.Context):
    log(ctx.guild.id, 'loop', [], log_type='command', author=ctx.author)

    await loop_command_def(ctx)


@bot.hybrid_command(name='loop_this', with_app_command=True, description=text['loop_this'], help=text['loop_this'])
async def loop_this(ctx: commands.Context):
    log(ctx.guild.id, 'loop_this', [], log_type='command', author=ctx.author)

    await loop_this_def(ctx)


# --------------------------------------- VOICE --------------------------------------------------


@bot.hybrid_command(name='stop', with_app_command=True, description=f'Stop the player')
async def stop(ctx: commands.Context):
    log(ctx.guild.id, 'stop', [], log_type='command', author=ctx.author)

    await stop_def(ctx)


@bot.hybrid_command(name='pause', with_app_command=True, description=f'Pause the player')
async def pause(ctx: commands.Context):
    log(ctx.guild.id, 'pause', [], log_type='command', author=ctx.author)

    await pause_def(ctx)


@bot.hybrid_command(name='resume', with_app_command=True, description=f'Resume the player')
async def resume(ctx: commands.Context):
    log(ctx.guild.id, 'resume', [], log_type='command', author=ctx.author)

    await resume_def(ctx)


@bot.hybrid_command(name='join', with_app_command=True, description=text['join'], help=text['join'])
@app_commands.describe(channel_id=text['channel_id'])
async def join(ctx: commands.Context,
               channel_id=None
               ):
    log(ctx.guild.id, 'join', [channel_id], log_type='command', author=ctx.author)

    await join_def(ctx, channel_id)

@bot.hybrid_command(name='disconnect', with_app_command=True, description=text['die'], help=text['die'])
async def disconnect(ctx: commands.Context):
    log(ctx.guild.id, 'disconnect', [], log_type='command', author=ctx.author)

    await disconnect_def(ctx)


@bot.hybrid_command(name='volume', with_app_command=True, description=text['volume'], help=text['volume'])
@app_commands.describe(volume=text['volume'], user_only=text['ephemeral'])
async def volume_command(ctx: commands.Context,
                         volume = None,
                         user_only: bool = False
                         ):
    log(ctx.guild.id, 'volume', [volume, user_only], log_type='command', author=ctx.author)

    await volume_command_def(ctx, volume, user_only)


# --------------------------------------- MENU --------------------------------------------------


@bot.tree.context_menu(name='Add to queue')
async def add_to_queue(inter, message: discord.Message):
    ctx = await bot.get_context(inter)
    log(ctx.guild.id, 'add_to_queue', [message.content], log_type='command', author=ctx.author)
    response = await queue_command_def(ctx, message.content, None, True)
    if not inter.response.is_done():
        await inter.response.send_message(content=response[1], ephemeral=True)


@bot.tree.context_menu(name='Show Profile')
async def show_profile(inter, member: discord.Member):
    ctx = await bot.get_context(inter)
    log(ctx.guild.id, 'show_profile', [member.name], log_type='command', author=ctx.author)
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
    log(ctx.guild.id, 'ping', [], log_type='command', author=ctx.author)

    await ping_def(ctx)


# noinspection PyTypeHints
@bot.hybrid_command(name='language', with_app_command=True, description=text['language'], help=text['language'])
@app_commands.describe(country_code=text['country_code'])
async def language_command(ctx: commands.Context,
                   country_code: Literal[tuple(languages_dict.keys())]
                   ):
    log(ctx.guild.id, 'language', [country_code], log_type='command', author=ctx.author)

    await language_command_def(ctx, country_code)


@bot.hybrid_command(name='sound_effects', with_app_command=True, description=text['sound'], help=text['sound'])
@app_commands.describe(user_only=text['ephemeral'])
async def sound_effects(ctx: commands.Context,
                user_only: bool = True
                ):
    log(ctx.guild.id, 'sound_effects', [user_only], log_type='command', author=ctx.author)

    await sound_effects_def(ctx, user_only)


@bot.hybrid_command(name='list_radios', with_app_command=True, description=text['list_radios'], help=text['list_radios'])
@app_commands.describe(user_only=text['ephemeral'])
async def list_radios(ctx: commands.Context,
                      user_only: bool = True
                      ):
    log(ctx.guild.id, 'list_radios', [user_only], log_type='command', author=ctx.author)

    await list_radios_def(ctx, user_only)


@bot.hybrid_command(name='key', with_app_command=True, description=text['key'], help=text['key'])
async def key_command(ctx: commands.Context):
    log(ctx.guild.id, 'key', [], log_type='command', author=ctx.author)

    await key_def(ctx)

# ---------------------------------------- ADMIN --------------------------------------------------


async def is_authorised(ctx):
    if ctx.author.id in authorized_users or ctx.author.id == 349164237605568513:
        return True


@bot.hybrid_command(name='zz_announce', with_app_command=True)
@commands.check(is_authorised)
async def announce_command(ctx: commands.Context,
                      message
                      ):
    log(ctx.guild.id, 'announce', [message], log_type='command', author=ctx.author)

    await announce_command_def(ctx, message)


@bot.hybrid_command(name='zz_earrape_play', with_app_command=True)
@commands.check(is_authorised)
async def earrape_play_command(ctx: commands.Context,
                      effect_number: int = None,
                      channel_id = None,
                      ):
    log(ctx.guild.id, 'zz_ear_rape_play', [effect_number, channel_id], log_type='command', author=ctx.author)

    await rape_play_command_def(ctx, effect_number, channel_id)

@bot.hybrid_command(name='zz_earrape', with_app_command=True)
@commands.check(is_authorised)
async def earrape_command(ctx: commands.Context):
    log(ctx.guild.id, 'earrape', [], log_type='command', author=ctx.author)

    await ear_rape_command_def(ctx)


@bot.hybrid_command(name='zz_kys', with_app_command=True)
@commands.check(is_authorised)
async def kys(ctx: commands.Context):
    log(ctx.guild.id, 'kys', [], log_type='command', author=ctx.author)

    await kys_def(ctx)


@bot.hybrid_command(name='zz_config', with_app_command=True)
@commands.check(is_authorised)
async def config_command(ctx: commands.Context,
                         config_file: discord.Attachment,
                         config_type:  Literal['guilds', 'other', 'radio', 'languages'] = 'guilds',
                         ):
    log(ctx.guild.id, 'config', [config_file, config_type], log_type='command', author=ctx.author)

    await config_command_def(ctx, config_file, config_type)


@bot.hybrid_command(name='zz_log', with_app_command=True)
@commands.check(is_authorised)
async def log_command(ctx: commands.Context,
                      log_type: Literal['log.txt', 'guilds.json', 'other.json', 'radio.json', 'languages.json', 'activity.log', 'data.txt'] = 'log.txt'
                      ):
    log(ctx.guild.id, 'log', [log_type], log_type='command', author=ctx.author)

    await log_command_def(ctx, log_type)


# noinspection PyTypeHints
@bot.hybrid_command(name='zz_change_config', with_app_command=True)
@app_commands.describe(server='all, this, {guild_id}', volume='No division', buffer='In seconds', language='Language code', response_type='short, long', buttons='True, False', is_radio='True, False', loop='True, False', stopped='True, False')
@commands.check(is_authorised)
async def change_config(ctx: commands.Context,
                        stopped: bool = None,
                        loop: bool = None,
                        is_radio: bool = None,
                        buttons: bool = None,
                        language: Literal[tuple(languages_dict.keys())] = None,
                        response_type: Literal['short', 'long'] = None,
                        buffer: int = None,
                        volume = None,
                        server = None,
                        ):
    log(ctx.guild.id, 'zz_change_config', [stopped, loop, is_radio, buttons, language, response_type, buffer, volume, server], log_type='command', author=ctx.author)

    await change_config_def(ctx, stopped, loop, is_radio, buttons, language, response_type, buffer, volume, server)


@bot.hybrid_command(name='zz_probe', with_app_command=True)
@commands.check(is_authorised)
async def probe_command(ctx: commands.Context,
                        url = None,
                        user_only: bool = False
                        ):
    log(ctx.guild.id, 'probe', [url, user_only], log_type='command', author=ctx.author)

    await probe_command_def(ctx, url, user_only)


# --------------------------------------------- COMMAND FUNCTIONS ------------------------------------------------------


# --------------------------------------- QUEUE --------------------------------------------------

async def queue_command_def(ctx: commands.Context,
                        url=None,
                        position: int = None,
                        mute_response: bool = False,
                        force: bool = False,
                        from_play: bool = False,
                        ):
    log(ctx.guild.id, 'queue_command_def', [url, position, mute_response, force, from_play], log_type='function', author=ctx.author)
    guild_id = ctx.guild.id
    author = ctx.author

    if not url:
        message = tg(guild_id, "`url` is **required**")
        if not mute_response:
            await ctx.reply(message, ephemeral=True)
        return [False, message]


    elif url[0:33] == "https://www.youtube.com/playlist?":
        try:
            # noinspection PyUnresolvedReferences
            if not ctx.interaction.response.is_done():
                await ctx.defer()
            playlist_videos = youtubesearchpython.Playlist.getVideos(url)
        except KeyError:
            log(guild_id, "------------------------------- playlist -------------------------")
            tb = traceback.format_exc()
            log(guild_id, tb)
            log(guild_id, "--------------------------------------------------------------")

            message = f'This playlist is unviewable: `{url}`'
            if not mute_response:
                await ctx.reply(message)
            return [False, message]

        playlist_songs = 0
        playlist_videos = playlist_videos['videos']

        if position or position == 0:
            playlist_videos = list(reversed(playlist_videos))

        for index, val in enumerate(playlist_videos):
            playlist_songs += 1
            # noinspection PyTypeChecker
            url = f"https://www.youtube.com/watch?v={playlist_videos[index]['id']}"
            video = Video(url, author.id)

            if position or position == 0: guild[guild_id].queue.insert(position, video)
            else: guild[guild_id].queue.append(video)

        message = f"`{playlist_songs}` {tg(guild_id, 'songs from playlist added to queue!')} -> [Control Panel](http://nicholasthe7th.duckdns.org:5420/guild/{ctx.guild.id}&key={guild[ctx.guild.id].data.key})"
        if not mute_response:
            await ctx.reply(message)

        save_json()
        return [True, message, None]

    elif url:
        if 'index=' in url or 'list=' in url:
            view = PlaylistOptionView(ctx, url, force, from_play)

            message = tg(guild_id, 'This video is from a **playlist**, do you want to add the playlist to **queue?**')
            await ctx.reply(message, view=view)
            return [False, message]

        video_id = extract_yt_id(url)

        if video_id is None:
            await search_command_def(ctx, url, 'short', force, from_play)
            message = f'[`{url}`](<{url}>) {tg(guild_id, "is not supported!")} -> [Control Panel](http://nicholasthe7th.duckdns.org:5420/guild/{ctx.guild.id}&key={guild[ctx.guild.id].data.key})'
            save_json()
            return [False, message]

        url = f"https://www.youtube.com/watch?v={video_id}"
        video = Video(url, author.id)

        if position or position == 0: guild[guild_id].queue.insert(position, video)
        else: guild[guild_id].queue.append(video)

        message = f'[`{video.title}`](<{video.url}>) {tg(guild_id, "added to queue!")} -> [Control Panel](http://nicholasthe7th.duckdns.org:5420/guild/{ctx.guild.id}&key={guild[ctx.guild.id].data.key})'

        if not mute_response:
            await ctx.reply(message)

        save_json()
        return [True, message, None]


async def next_up_def(ctx: commands.Context,
                 url,
                 ephemeral: bool = False
                 ):
    log(ctx.guild.id, 'next_up_def', [url, ephemeral], log_type='function', author=ctx.author)
    response = await queue_command_def(ctx, url, 0, True, True)

    if response[0]:

        if ctx.voice_client:
            if not ctx.voice_client.is_playing():
                await play_def(ctx)
                return
        else:
            await play_def(ctx)
            return

        await ctx.reply(response[1], ephemeral=ephemeral)

    else:
        return

    save_json()


async def skip_def(ctx: commands.Context):
    log(ctx.guild.id, 'skip_def', [], log_type='function', author=ctx.author)
    guild_id = ctx.guild.id
    if not ctx.voice_client.is_playing():
        await ctx.reply(tg(guild_id, "There is **nothing to skip!**"), ephemeral=True)
    if ctx.voice_client.is_playing():
        await stop_def(ctx, True)
        await asyncio.sleep(0.5)
        await play_def(ctx)


async def remove_def(ctx: commands.Context,
                 number: int,
                 display_type: Literal['short', 'long'] = None,
                 ephemeral: bool = False
                 ):
    log(ctx.guild.id, 'remove_def', [number, display_type, ephemeral], log_type='function', author=ctx.author)
    guild_id = ctx.guild.id

    if not display_type:
        display_type = guild[guild_id].options.response_type

    if number or number == 0 or number == '0':
        if number > len(guild[guild_id].queue):
            if not guild[guild_id].queue:
                await ctx.reply(tg(guild_id, "Nothing to **remove**, queue is **empty!**"), ephemeral=True)
                return
            await ctx.reply(tg(guild_id, "Index out of range!"), ephemeral=True)
            return

        video = guild[guild_id].queue[number]

        if display_type == 'long':
            embed = create_embed(video, f'{tg(guild_id, "REMOVED #")}{number}', guild_id)
            await ctx.reply(embed=embed, ephemeral=ephemeral)
        if display_type == 'short':
            await ctx.reply(f'REMOVED #{number} : [`{video.title}`](<{video.url}>)', ephemeral=ephemeral)

        guild[guild_id].queue.pop(number)

    save_json()


async def clear_def(ctx: commands.Context,
                 ephemeral: bool = False
                 ):
    log(ctx.guild.id, 'clear_def', [ephemeral], log_type='function', author=ctx.author)
    guild_id = ctx.guild.id
    guild[guild_id].queue.clear()
    await ctx.reply(tg(guild_id, 'Removed **all** songs from queue'), ephemeral=ephemeral)
    return


async def shuffle_def(ctx: commands.Context,
                 ephemeral: bool = False
                 ):
    log(ctx.guild.id, 'shuffle_def', [ephemeral], log_type='function', author=ctx.author)
    guild_id = ctx.guild.id
    random.shuffle(guild[guild_id].queue)
    await ctx.reply(tg(guild_id, 'Songs in queue shuffled'), ephemeral=ephemeral)
    return


async def show_def(ctx: commands.Context,
               display_type: Literal['short', 'medium', 'long'] = None,
               ephemeral: bool = False
               ):
    log(ctx.guild.id, 'show_def', [display_type, ephemeral], log_type='function', author=ctx.author)
    guild_id = ctx.guild.id
    max_embed = 5
    if not guild[guild_id].queue:
        await ctx.reply(tg(guild_id, "Nothing to **show**, queue is **empty!**"), ephemeral=ephemeral)
        return

    if not display_type:
        if len(guild[guild_id].queue) <= max_embed:
            display_type = 'long'
        else:
            display_type = 'medium'

    if display_type == 'long':
        await ctx.send(f"**THE QUEUE**\n **Loop** mode  `{guild[guild_id].options.loop}`,  **Display** type `{display_type}`", ephemeral=ephemeral, mention_author=False)

        for index, val in enumerate(guild[guild_id].queue):
            embed = create_embed(val, f'{tg(guild_id, "Queue #")}{index}', guild_id)

            await ctx.send(embed=embed, ephemeral=ephemeral, mention_author=False)


    if display_type == 'medium':
        embed = discord.Embed(title="Song Queue", description=f'Loop: {guild[guild_id].options.loop} | Display type: {display_type}', color=0x00ff00)

        message = ''
        for index, val in enumerate(guild[guild_id].queue):
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
        send = f"**THE QUEUE**\n **Loop** mode  `{guild[guild_id].options.loop}`,  **Display** type `{display_type}`"
        # noinspection PyUnresolvedReferences
        if ctx.interaction.response.is_done(): await ctx.send(send, ephemeral=ephemeral, mention_author=False)
        else: await ctx.reply(send, ephemeral=ephemeral, mention_author=False)

        message = ''
        for index, val in enumerate(guild[guild_id].queue):
            add = f'**{tg(guild_id, "Queue #")}{index}**  `{convert_duration(val.duration)}`  [`{val.title}`](<{val.url}>) \n'
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


async def search_command_def(ctx: commands.Context,
                         search_query,
                         display_type: Literal['short', 'long'] = None,
                         force: bool = False,
                         from_play: bool = False
                         ):
    log(ctx.guild.id, 'search_command_def', [search_query, display_type, force, from_play], log_type='function', author=ctx.author)
    # noinspection PyUnresolvedReferences
    if not ctx.interaction.response.is_done():
        await ctx.defer()
    guild_id = ctx.guild.id

    guild[guild_id].options.search_query = search_query

    if display_type is None:
        display_type = guild[guild_id].options.response_type

    message = f'**Search query:** `{search_query}`\n'

    if display_type == 'long':
        await ctx.reply(tg(guild_id, 'Searching...'), ephemeral=True)

    custom_search = youtubesearchpython.VideosSearch(search_query, limit=5)
    guild[guild_id].search_list.clear()

    view = SearchOptionView(ctx, force, from_play)

    if not custom_search.result()['result']:
        await ctx.reply(tg(guild_id, 'No results found!'))
        return

    for i in range(5):
        # noinspection PyTypeChecker
        url = custom_search.result()['result'][i]['link']
        video = Video(url, ctx.author.id)
        guild[guild_id].search_list.append(video)

        if display_type == 'long':
            embed = create_embed(video, f'{tg(guild_id, "Result #")}{i + 1}', guild_id)
            await ctx.message.channel.send(embed=embed)
        if display_type == 'short':
            message += f'{tg(guild_id, "Result #")}{i+1} : [`{video.title}`](<{video.url}>)\n'
    if display_type == 'short':
        await ctx.reply(message, view=view)

    save_json()


# --------------------------------------- PLAYER --------------------------------------------------


async def play_def(ctx: commands.Context,
               url=None,
               force=False,
               mute_response=False
               ):
    log(ctx.guild.id, 'play_def', [url, force, mute_response], log_type='function', author=ctx.author)
    response = []
    guild_id = ctx.guild.id

    if url == 'next':
        if guild[guild_id].options.stopped:
            log(guild_id, "play_def -> stopped play next loop")
            now_to_last(guild_id)
            return

    voice = ctx.voice_client

    if not voice or voice is None:
        if ctx.author.voice is None:
            if not mute_response:
                await ctx.reply(tg(guild_id, "You are **not connected** to a voice channel"))
            return

    if url and url != 'next':
        if voice:
            if not voice.is_playing():
                force = True
        if force:
            response = await queue_command_def(ctx, url=url, position=0, mute_response=True, force=force, from_play=True)
        else:
            response = await queue_command_def(ctx, url=url, position=None, mute_response=True, force=force, from_play=True)
        if not response[0]:
            return

    voice = ctx.voice_client

    if not voice or voice is None:
        # noinspection PyUnresolvedReferences
        if not ctx.interaction.response.is_done():
            await ctx.defer()
        response = await join_def(ctx, None, True)
        voice = ctx.voice_client
        if not response:
            return

    if voice.is_playing():
        if not guild[guild_id].options.is_radio and not force:
            if url and not force:
                if response:
                    if not mute_response:
                        await ctx.reply(f'{tg(guild_id, "**Already playing**, added to queue")}: [`{response[2].title}`](<{response[2].url}>)')
                    return 'already playing, added to queue'
                if not mute_response:
                    await ctx.reply(f'{tg(guild_id, "**Already playing**, added to queue")}')
                return 'already playing, added to queue'
            if not mute_response:
                await ctx.reply(tg(guild_id, "**Already playing**"), ephemeral=True)
            return 'already playing'
        voice.stop()
        guild[guild_id].options.stopped = True
        guild[guild_id].options.is_radio = False

    if not guild[guild_id].queue:
        if url != 'next':
            if not mute_response:
                await ctx.reply(tg(guild_id, "There is **nothing** in your **queue**"))
        now_to_last(guild_id)
        return 'nothing in queue'

    video = guild[guild_id].queue[0]
    now_to_last(guild_id)

    if type(video) is not Video:
        guild[guild_id].queue.pop(0)
        if type(video) is Radio:
            await radio_def(ctx, video.title)
            return
        if type(video) is LocalFile:
            await ps_def(ctx, video.number)
            return
        if type(video) is FromProbe:
            await probe_command_def(ctx, video.url)
            return

        if not mute_response:
            await ctx.reply(tg(guild_id, "Unknown type"))
        return 'unknown type'

    if not force:
        guild[guild_id].options.stopped = False

    try:
        source = await YTDLSource.create_source(ctx, video.url)  # loop=bot.loop  va_list[0]
        voice.play(source, after=lambda e: asyncio.run_coroutine_threadsafe(play_def(ctx, 'next'), bot.loop))

        await volume_command_def(ctx, guild[guild_id].options.volume * 100, False, True)

        guild[guild_id].options.stopped = False
        guild[guild_id].now_playing = video

        if guild[guild_id].options.loop:
            guild[guild_id].queue.append(video)

        guild[guild_id].queue.pop(0)

        view = PlayerControlView(ctx)

        if guild[guild_id].options.response_type == 'long':
            embed = create_embed(video, "Now playing", guild_id)
            if guild[guild_id].options.buttons:
                if not mute_response:
                    await ctx.reply(embed=embed, view=view)
            else:
                if not mute_response:
                    await ctx.reply(embed=embed)

        if guild[guild_id].options.response_type == 'short':
            if guild[guild_id].options.buttons:
                if not mute_response:
                    await ctx.reply(f'{tg(guild_id, "Now playing")} [`{video.title}`](<{video.url}>)', view=view)
            else:
                if not mute_response:
                    await ctx.reply(f'{tg(guild_id, "Now playing")} [`{video.title}`](<{video.url}>)')

        save_json()

    except (discord.ext.commands.errors.CommandInvokeError, IndexError, TypeError, discord.errors.ClientException,
            YTDLError, discord.errors.NotFound):
        log(guild_id, "------------------------------- play -------------------------")
        tb = traceback.format_exc()
        log(guild_id, tb)
        log(guild_id, "--------------------------------------------------------------")
        await ctx.reply(f'{tg(guild_id, "An **error** occurred while trying to play the song")}'
                        f' {bot.get_user(my_id).mention} ({sys.exc_info()[0]})')


async def radio_def(ctx: commands.Context,
                favourite_radio: Literal['Rádio BLANÍK','Rádio BLANÍK CZ','Evropa 2','Fajn Radio','Hitrádio PopRock','Český rozhlas Pardubice','Radio Beat','Country Radio','Radio Kiss','Český rozhlas Vltava','Hitrádio Černá Hora'] = None,
                radio_code: int = None,
                ):
    log(ctx.guild.id, 'radio_def', [favourite_radio, radio_code], log_type='function', author=ctx.author)
    guild_id = ctx.guild.id
    radio_type = 'Rádio BLANÍK'

    # noinspection PyUnresolvedReferences
    if not ctx.interaction.response.is_done():
        await ctx.defer()
    if favourite_radio and radio_code:
        await ctx.reply(tg(guild_id, "Only **one** argument possible!"), ephemeral=True)
        return

    if favourite_radio:
        radio_type = favourite_radio
    elif radio_code:
        radio_type = list(radio_dict.keys())[radio_code]

    if not ctx.voice_client:
        response = await join_def(ctx, None, True)
        if not response:
            return

    url = radio_dict[radio_type]['stream']
    # guild[guild_id].queue.clear()

    if ctx.voice_client.is_playing():
        await stop_def(ctx, True)  # call the stop coroutine if something else is playing, pass True to not send response

    radio_class = Radio(radio_type, ctx.author.id, radio_type)
    guild[guild_id].now_playing = radio_class

    guild[guild_id].options.is_radio = True

    embed = create_embed(radio_class, 'Now playing', guild_id)

    source = discord.FFmpegPCMAudio(url, **FFMPEG_OPTIONS)

    ctx.voice_client.play(source)

    await volume_command_def(ctx, guild[guild_id].options.volume*100, False, True)

    if guild[guild_id].options.buttons:
        view = PlayerControlView(ctx)
        await ctx.reply(embed=embed, view=view)
    else:
        await ctx.reply(embed=embed)  # view=view   f"**{text['Now playing']}** `{radio_type}`",

    save_json()


async def ps_def(ctx: commands.Context,
             effect_number: app_commands.Range[int, 1, len(all_sound_effects)],
             mute_response: bool = False
             ):
    log(ctx.guild.id, 'ps_def', [effect_number, mute_response], log_type='function', author=ctx.author)
    guild_id = ctx.guild.id
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
        video = LocalFile(name, 'Unknown', ctx.author.id, effect_number)
        guild[guild_id].now_playing = video
    else:
        filename = "sound_effects/" + name + ".wav"
        if path.exists(filename):
            source = FFmpegPCMAudio(filename)

        else:
            if not mute_response:
                await ctx.reply(tg(guild_id, "No such file/website supported"), ephemeral=True)
            return False

    if not ctx.voice_client:
        await join_def(ctx, None, True)

    voice = ctx.voice_client

    await stop_def(ctx, True)
    voice.play(source)
    await volume_command_def(ctx, guild[guild_id].options.volume*100, False, True)
    if not mute_response:
        await ctx.reply(f"{tg(guild_id, 'Playing sound effect number')} `{effect_number}`", ephemeral=True)

    save_json()

    return True


async def now_def(ctx: commands.Context,
              ephemeral: bool = False
              ):
    log(ctx.guild.id, 'now_def', [ephemeral], log_type='function', author=ctx.author)
    guild_id = ctx.guild.id
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


async def last_def(ctx: commands.Context,
              ephemeral: bool = False
              ):
    log(ctx.guild.id, 'last_def', [ephemeral], log_type='function', author=ctx.author)
    guild_id = ctx.guild.id
    embed = create_embed(guild[guild_id].last_played, "Last played", guild_id)

    view = PlayerControlView(ctx)

    if guild[guild_id].options.buttons:
        await ctx.reply(embed=embed, view=view, ephemeral=ephemeral)
    else:
        await ctx.reply(embed=embed, ephemeral=ephemeral)

    save_json()


async def loop_command_def(ctx: commands.Context):
    log(ctx.guild.id, 'loop_command_def', [], log_type='function', author=ctx.author)
    guild_id = ctx.guild.id
    if guild[guild_id].options.loop:
        guild[guild_id].options.loop = False
        await ctx.reply("Loop mode: `False`", ephemeral=True)
        return
    if not guild[guild_id].options.loop:
        guild[guild_id].options.loop = True
        await ctx.reply("Loop mode: `True`", ephemeral=True)
        return


async def loop_this_def(ctx: commands.Context):
    log(ctx.guild.id, 'loop_this_def', [], log_type='function', author=ctx.author)
    guild_id = ctx.guild.id
    if guild[guild_id].now_playing and ctx.voice_client.is_playing:
        guild[guild_id].queue.clear()
        guild[guild_id].queue.append(guild[guild_id].now_playing)
        guild[guild_id].options.loop = True
        await ctx.reply(f'{tg(guild_id, "Queue **cleared**, Player will now loop **currently** playing song:")}'
                        f' [`{guild[guild_id].now_playing.title}`](<{guild[guild_id].now_playing.url}>)')
    else:
        await ctx.reply(tg(guild_id, "Nothing is playing **right now**"))


# --------------------------------------- VOICE --------------------------------------------------


async def stop_def(ctx: commands.Context,
               mute_response: bool = False
               ):
    log(ctx.guild.id, 'stop_def', [mute_response], log_type='function', author=ctx.author)
    guild_id = ctx.guild.id

    voice = discord.utils.get(bot.voice_clients, guild=ctx.guild)
    if voice:
        voice.stop()
    else:
        if not mute_response:
            await ctx.reply(tg(guild_id, "Bot is not connected to a voice channel"), ephemeral=True)
        return
    guild[guild_id].options.stopped = True
    guild[guild_id].options.loop = False

    if not mute_response:
        await ctx.reply(f"{tg(guild_id, 'Player **stopped!**')}", ephemeral=True)

    now_to_last(guild_id)
    save_json()


async def pause_def(ctx: commands.Context,
                mute_response: bool = False
                ):
    log(ctx.guild.id, 'pause_def', [mute_response], log_type='function', author=ctx.author)
    guild_id = ctx.guild.id
    voice = discord.utils.get(bot.voice_clients, guild=ctx.guild)

    if voice:
        if voice.is_playing():
            voice.pause()
            if not mute_response:
                await ctx.reply(f"{tg(guild_id, 'Player **paused!**')}", ephemeral=True)
        elif voice.is_paused():
            if not mute_response:
                await ctx.reply(f"{tg(guild_id, 'Player **already paused!**')}", ephemeral=True)
        else:
            if not mute_response:
                await ctx.reply(f"{tg(guild_id, 'No audio playing')}", ephemeral=True)
    else:
        if not mute_response:
            await ctx.reply(tg(ctx.guild.id, "Bot is not connected to a voice channel"), ephemeral=True)

    save_json()


async def resume_def(ctx: commands.Context,
                 mute_response: bool = False
                 ):
    log(ctx.guild.id, 'resume_def', [mute_response], log_type='function', author=ctx.author)
    guild_id = ctx.guild.id
    voice = discord.utils.get(bot.voice_clients, guild=ctx.guild)
    if voice:
        if voice.is_paused():
            voice.resume()
            if not mute_response:
                await ctx.reply(f"{tg(guild_id, 'Player **resumed!**')}", ephemeral=True)
        elif voice.is_playing():
            if not mute_response:
                await ctx.reply(f"{tg(guild_id, 'Player **already resumed!**')}", ephemeral=True)
        else:
            if not mute_response:
                await ctx.reply(f"{tg(guild_id, 'No audio playing')}", ephemeral=True)
    else:
        if not mute_response:
            await ctx.reply(tg(guild_id, "Bot is not connected to a voice channel"), ephemeral=True)

    save_json()


async def join_def(ctx: commands.Context,
               channel_id=None,
               mute_response: bool = False
               ):
    log(ctx.guild.id, 'join_def', [channel_id, mute_response], log_type='function', author=ctx.author)
    guild_id = ctx.guild.id

    now_to_last(guild_id)

    if not channel_id:
        if ctx.author.voice:
            channel = ctx.message.author.voice.channel
            if ctx.voice_client:
                if ctx.voice_client.channel != channel:
                    await ctx.voice_client.disconnect(force=True)
                else:
                    if not mute_response:
                        await ctx.reply(tg(guild_id, "I'm already in this channel"), ephemeral=True)
                    return True
            await channel.connect()
            await ctx.guild.change_voice_state(channel=channel, self_deaf=True)
            if not mute_response:
                await ctx.reply(f"{tg(guild_id, 'Joined voice channel:')}  `{channel.name}`", ephemeral=True)
            return True

        await ctx.reply(tg(guild_id, "You are **not connected** to a voice channel"), ephemeral=True)
        return False

    try:
        voice_channel = bot.get_channel(int(channel_id))
        if ctx.voice_client:
            await ctx.voice_client.disconnect(force=True)
        await voice_channel.connect()
        await ctx.guild.change_voice_state(channel=voice_channel, self_deaf=True)
        if not mute_response:
            await ctx.reply(f"{tg(guild_id, 'Joined voice channel:')}  `{voice_channel.name}`", ephemeral=True)
        return True
    except (discord.ext.commands.errors.CommandInvokeError, discord.errors.ClientException, AttributeError):

        log(guild_id, "------------------------------- join -------------------------")
        tb = traceback.format_exc()
        log(guild_id, tb)
        log(guild_id, "--------------------------------------------------------------")
        await ctx.reply(tg(guild_id, "Channel **doesn't exist** or bot doesn't have"
                                             " **sufficient permission** to join"), ephemeral=True)
        return False


async def disconnect_def(ctx: commands.Context,
                         mute_response: bool = False
                         ):
    log(ctx.guild.id, 'disconnect_def', [mute_response], log_type='function', author=ctx.author)
    guild_id = ctx.guild.id
    if ctx.voice_client:
        await stop_def(ctx, True)
        #guild[guild_id].queue.clear()
        channel = ctx.voice_client.channel
        await ctx.guild.voice_client.disconnect(force=True)
        if not mute_response:
            await ctx.reply(f"{tg(guild_id, 'Left voice channel:')} `{channel}`", ephemeral=True)
    else:
        if not mute_response:
            await ctx.reply(tg(guild_id, "Bot is **not** in a voice channel"), ephemeral=True, mention_author=False)

    now_to_last(guild_id)
    save_json()


async def volume_command_def(ctx: commands.Context,
                         volume = None,
                         ephemeral: bool = False,
                         mute_response: bool = False
                         ):
    log(ctx.guild.id, 'volume_command_def', [volume, ephemeral, mute_response], log_type='function', author=ctx.author)
    guild_id = ctx.guild.id

    if volume:
        new_volume = int(volume) / 100

        guild[guild_id].options.volume = new_volume
        voice = ctx.voice_client
        if voice:
            try:
                if voice.source:
                    voice.source.volume = new_volume
                    voice.source = discord.PCMVolumeTransformer(voice.source, volume=new_volume)
            except AttributeError:
                pass

        if not mute_response:
            await ctx.reply(f'{tg(guild_id, "Changed the volume for this server to:")} `{guild[guild_id].options.volume*100}%`', ephemeral=ephemeral)
    else:
        if not mute_response:
            await ctx.reply(f'{tg(guild_id, "The volume for this server is:")} `{guild[guild_id].options.volume*100}%`', ephemeral=ephemeral)

    save_json()


# --------------------------------------- GENERAL --------------------------------------------------


async def ping_def(ctx: commands.Context):
    log(ctx.guild.id, 'ping_def', [], log_type='function', author=ctx.author)
    await ctx.reply(f'**Pong!** Latency: {round(bot.latency * 1000)}ms')
    save_json()


# noinspection PyTypeHints
async def language_command_def(ctx: commands.Context,
                   country_code: Literal[tuple(languages_dict.keys())]
                   ):
    log(ctx.guild.id, 'language_command_def', [country_code], log_type='function', author=ctx.author)
    guild_id = ctx.guild.id
    guild[guild_id].options.language = country_code
    await ctx.reply(f'{tg(guild_id, "Changed the language for this server to: ")} `{guild[guild_id].options.language}`')
    save_json()


async def sound_effects_def(ctx: commands.Context,
                ephemeral: bool = True
                ):
    log(ctx.guild.id, 'sound_effects_def', [ephemeral], log_type='function', author=ctx.author)
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


async def list_radios_def(ctx: commands.Context,
                      ephemeral: bool = True
                      ):
    log(ctx.guild.id, 'list_radios_def', [ephemeral], log_type='function', author=ctx.author)
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
    log(ctx.guild.id, 'key_def', [], log_type='function', author=ctx.author)
    await ctx.reply(f'Key: `{guild[ctx.guild.id].data.key}` -> [Control Panel](http://nicholasthe7th.duckdns.org:5420/guild/{ctx.guild.id}&key={guild[ctx.guild.id].data.key})')
    save_json()

# ---------------------------------------- ADMIN --------------------------------------------------


async def announce_command_def(ctx: commands.Context,
                      message
                      ):
    log(ctx.guild.id, 'announce_command_def', [message], log_type='function', author=ctx.author)
    for guild_object in bot.guilds:
        await guild_object.system_channel.send(message)

    await ctx.reply(f'Announced message to all servers: `{message}`')


async def rape_play_command_def(ctx: commands.Context,
                      effect_number: int = None,
                      channel_id = None,
                      ):
    log(ctx.guild.id, 'rape_play_command_def', [effect_number, channel_id], log_type='function', author=ctx.author)

    if not effect_number and effect_number != 0:
        effect_number = 1

    if not channel_id:
        response = await join_def(ctx, None, True)
        if response:
            pass
        else:
            await ctx.reply(f'You need to be in a voice channel to use this command', ephemeral=True)
            return
    else:
        response = await join_def(ctx, channel_id, True)
        if response:
            pass
        else:
            await ctx.reply(f'An error occurred when connecting to the voice channel', ephemeral=True)
            return

    await ps_def(ctx, effect_number, True)
    await ear_rape_command_def(ctx)

    await ctx.reply(f'Playing effect `{effect_number}` with ear rape in `{channel_id if channel_id else "user channel"}` >>> effect can only be turned off by `/disconnect`', ephemeral=True)


async def ear_rape_command_def(ctx: commands.Context):
    log(ctx.guild.id, 'ear_rape_command_def', [], log_type='function', author=ctx.author)
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
    log(ctx.guild.id, 'kys_def', [], log_type='function', author=ctx.author)
    guild_id = ctx.guild.id
    await ctx.reply(tg(guild_id, "Committing seppuku..."))
    sys.exit(3)


async def config_command_def(ctx: commands.Context,
                         config_file: discord.Attachment,
                         config_type:  Literal['guilds', 'other', 'radio', 'languages'] = 'guilds',
                         ):
    log(ctx.guild.id, 'config_command_def', [config_file, config_type], log_type='function', author=ctx.author)

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
        log('no guild', 'Loading guilds.json ...')
        with open('src/guilds.json', 'r') as f:
            globals()['guild'] = json_to_guilds(json.load(f))

        await ctx.reply("Loaded new `guilds.json`", ephemeral=True)
    else:
        await ctx.reply(f"Saved new `{config_type}.json`", ephemeral=True)


async def log_command_def(ctx: commands.Context,
                      log_type: Literal['log.txt', 'guilds.json', 'other.json', 'radio.json', 'languages.json', 'activity.log', 'data.txt'] = 'log.txt'
                      ):
    log(ctx.guild.id, 'log_command_def', [log_type], log_type='function', author=ctx.author)
    save_json()
    if log_type == 'log.txt':
        file_to_send = discord.File('log.txt')
    elif log_type == 'data.txt':
        file_to_send = discord.File('data.txt')
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
            file_to_send = discord.File('activity.log')
        except FileNotFoundError:
            await ctx.reply(f'`activity.log` does not exist', ephemeral=True)
            return
    else:
        file_to_send = discord.File('log.txt')
    await ctx.reply(file=file_to_send, ephemeral=True)


# noinspection PyTypeHints
async def change_config_def(ctx: commands.Context,
                        stopped: bool = None,
                        loop: bool = None,
                        is_radio: bool = None,
                        buttons: bool = None,
                        language: Literal[tuple(languages_dict.keys())] = None,
                        response_type: Literal['short', 'long'] = None,
                        buffer: int = None,
                        volume = None,
                        server = None,
                        ):
    log(ctx.guild.id, 'change_config_def', [stopped, loop, is_radio, buttons, language, response_type, buffer, volume, server], log_type='function', author=ctx.author)
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

        config_text = f'`stopped={guild[guild_id].options.stopped}`, `loop={guild[guild_id].options.loop}`,' \
                 f' `is_radio={guild[guild_id].options.is_radio}`, `buttons={guild[guild_id].options.buttons}`,' \
                 f' `language={guild[guild_id].options.language}`, `response_type={guild[guild_id].options.response_type}`,' \
                 f' `volume={guild[guild_id].options.volume}`, `buffer={guild[guild_id].options.buffer}`'

        save_json()

        await ctx.reply(f'**Config for guild `{guild_id}`**\n {config_text}', ephemeral=True)


async def probe_command_def(ctx: commands.Context,
                        url = None,
                        ephemeral: bool = False
                        ):
    log(ctx.guild.id, 'probe_command_def', [url, ephemeral], log_type='function', author=ctx.author)
    guild_id = ctx.guild.id
    if url is None:
        await ctx.reply("Please provide a url", ephemeral=ephemeral)
        return

    codec, bitrate = await discord.FFmpegOpusAudio.probe(url)
    if codec is None and bitrate is None:
        await ctx.reply(f"`{url}` does not have `bitrate` and `codec` properties", ephemeral=ephemeral)
        return

    try:
        if not ctx.voice_client:
            response = await join_def(ctx, None, True)
            if not response:
                return

        if ctx.voice_client.is_playing():
            await stop_def(ctx, True)

        guild[guild_id].now_playing = FromProbe(url=url, author=ctx.author.id, title='URL Probe', duration=0, channel_link=url, channel_name='URL Probe')

        source = discord.FFmpegPCMAudio(url, **FFMPEG_OPTIONS)

        ctx.voice_client.play(source)

        await volume_command_def(ctx, guild[guild_id].options.volume * 100, False, True)

        await ctx.reply(f'{tg(guild_id, "Now playing")}: [`{url}`](<{url}>)', ephemeral=ephemeral)
    except Exception as e:
        await ctx.reply(f'Error: {e}', ephemeral=ephemeral)

    save_json()


# --------------------------------------------- HELP COMMAND -----------------------------------------------------------


bot.remove_command('help')
@bot.hybrid_command(name='help', with_app_command=True, description='Shows all available commands', help='Shows all available commands')
@app_commands.describe(general='General commands', player='Player commands', queue='Queue commands', voice='Voice commands')
async def help_command(ctx: commands.Context,
                       general: Literal['help', 'ping', 'language', 'sound_effects', 'list_radios'] = None,
                       player: Literal['play', 'radio', 'ps', 'skip', 'nowplaying', 'last', 'loop', 'loop_this'] = None,
                       queue: Literal['queue', 'remove', 'clear', 'shuffle', 'show', 'search'] = None,
                       voice: Literal['stop', 'pause', 'resume', 'join', 'disconnect', 'volume'] = None,
               ):
    log(ctx.guild.id, 'help', [general, player, queue, voice], log_type='command', author=ctx.author)
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
                                               f"`Show Profile` - {tg(gi, 'profile')}\n")

    embed.add_field(name="Admin Commands (only for bot owner)", value=f"`/zz_announce` - \n"
                                                 f"`/zz_rape` - \n"
                                                 f"`/zz_rape_play` - \n"
                                                 f"`/zz_kys` - \n"
                                                 f"`/zz_config` - \n"
                                                 f"`/zz_log` - \n"
                                                 f"`/zz_change_config` - \n"
                                                 f"`/zz_probe` - "
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


# --------------------------------------------- WEB COMMANDS -----------------------------------------------------------


async def web_remove(web_data, number):
    log(web_data.guild_id, 'web_remove', [number], log_type='function', author=web_data.author)
    guild_id = web_data.guild_id
    queue_length = len(guild[guild_id].queue)

    if queue_length == 0:
        log(guild_id, "web_remove -> No songs in queue")
        return [False, 'No songs in queue']

    if type(number) is not int:
        try:
            number = int(number)
        except ValueError:
            log(guild_id, "web_remove -> Number must be an integer")
            return [False, 'Number must be an integer (Internal web error -> contact developer)']

    if queue_length-1 >= number >= 0:
        video = guild[guild_id].queue[number]
        guild[guild_id].queue.pop(number)

        save_json()

        return [True, f"Removed #{number} : {video.title}"]

    log(guild_id, "web_remove -> Number must be between 0 and {queue_length - 1}")
    return [False, f'Number must be between 0 and {queue_length - 1}']

async def web_move(web_data, org_number, destination_number):
    log(web_data.guild_id, 'web_move', [org_number, destination_number], log_type='function', author=web_data.author)
    guild_id = web_data.guild_id
    queue_length = len(guild[guild_id].queue)

    if queue_length == 0:
        log(guild_id, "web_move -> No songs in queue")
        return [False, 'No songs in queue']

    if type(org_number) is not int:
        try:
            org_number = int(org_number)
        except ValueError:
            log(guild_id, "web_move -> Original number must be an integer")
            return [False, 'Original number must be an integer (Internal web error -> contact developer)']

    if type(destination_number) is not int:
        try:
            destination_number = int(destination_number)
        except ValueError:
            log(guild_id, "web_move -> Destination number must be an integer")
            return [False, 'Destination number must be an integer (Internal web error -> contact developer)']

    if queue_length-1 >= org_number >= 0:
        if queue_length-1 >= destination_number >= 0:
            video = guild[guild_id].queue.pop(org_number)
            guild[guild_id].queue.insert(destination_number, video)

            save_json()

            return [True, f"Moved #{org_number} to #{destination_number} : {video.title}"]

        log(guild_id, "web_move -> Destination number must be between 0 and {queue_length - 1}")
        return [False, f'Destination number must be between 0 and {queue_length - 1}']
    log(guild_id, "web_move -> Original number must be between 0 and {queue_length - 1}")
    return [False, f'Original number must be between 0 and {queue_length - 1}']

async def web_up(web_data, number):
    log(web_data.guild_id, 'web_up', [number], log_type='function', author=web_data.author)
    guild_id = web_data.guild_id
    queue_length = len(guild[guild_id].queue)

    if type(number) is not int:
        try:
            number = int(number)
        except ValueError:
            log(guild_id, "web_up -> Number must be an integer")
            return [False, 'Number must be an integer (Internal web error -> contact developer)']

    if queue_length == 0:
        log(guild_id, "web_up -> No songs in queue")
        return [False, 'No songs in queue']

    if number == 0:
        return await web_move(web_data, 0, queue_length-1)

    return await web_move(web_data, number, number-1)

async def web_down(web_data, number):
    log(web_data.guild_id, 'web_down', [number], log_type='function', author=web_data.author)
    guild_id = web_data.guild_id
    queue_length = len(guild[guild_id].queue)

    if type(number) is not int:
        try:
            number = int(number)
        except ValueError:
            log(guild_id, "web_down -> Number must be an integer")
            return [False, 'Number must be an integer (Internal web error -> contact developer)']

    if queue_length == 0:
        log(guild_id, "web_down -> No songs in queue")
        return [False, 'No songs in queue']

    if number == queue_length-1:
        return await web_move(web_data, number, 0)

    return await web_move(web_data, number, number+1)

async def web_top(web_data, number):
    log(web_data.guild_id, 'web_top', [number], log_type='function', author=web_data.author)
    guild_id = web_data.guild_id
    queue_length = len(guild[guild_id].queue)

    if type(number) is not int:
        try:
            number = int(number)
        except ValueError:
            log(guild_id, "web_top -> Number must be an integer")
            return [False, 'Number must be an integer (Internal web error -> contact developer)']

    if queue_length == 0:
        log(guild_id, "web_top -> No songs in queue")
        return [False, 'No songs in queue']

    if number == 0:
        log(guild_id, "web_top -> Already at the top")
        return [False, 'Already at the top']

    return await web_move(web_data, number, 0)

async def web_bottom(web_data, number):
    log(web_data.guild_id, 'web_bottom', [number], log_type='function', author=web_data.author)
    guild_id = web_data.guild_id
    queue_length = len(guild[guild_id].queue)

    if type(number) is not int:
        try:
            number = int(number)
        except ValueError:
            log(guild_id, "web_bottom -> Number must be an integer")
            return [False, 'Number must be an integer (Internal web error -> contact developer)']

    if queue_length == 0:
        log(guild_id, "web_bottom -> No songs in queue")
        return [False, 'No songs in queue']

    if number == queue_length-1:
        log(guild_id, "web_bottom -> Already at the bottom")
        return [False, 'Already at the bottom']

    return await web_move(web_data, number, queue_length-1)

async def web_stop(web_data):
    log(web_data.guild_id, 'web_stop', [], log_type='function', author=web_data.author)
    guild_id = web_data.guild_id
    guild_object = bot.get_guild(int(guild_id))
    voice = guild_object.voice_client

    now_to_last(guild_id)

    if voice is None:
        log(guild_id, "web_stop -> Not in a voice channel")
        return [False, 'Not in a voice channel']

    if not voice.is_playing():
        log(guild_id, "web_stop -> Not playing")
        return [False, 'Not playing']

    if voice.is_playing():
        guild[guild_id].options.stopped = True
        voice.stop()
        save_json()
        log(guild_id, "web_stop -> Stopped")
        return [True, 'Stopped playing']

    log(guild_id, "web_stop -> Unknown error")
    return [False, 'Unknown error']

async def web_pause(web_data):
    log(web_data.guild_id, 'web_pause', [], log_type='function', author=web_data.author)
    guild_id = web_data.guild_id
    guild_object = bot.get_guild(int(guild_id))
    voice = guild_object.voice_client

    if voice is None:
        log(guild_id, "web_pause -> Not in a voice channel")
        return [False, 'Not in a voice channel']

    if not voice.is_playing():
        log(guild_id, "web_pause -> Not playing")
        return [False, 'Not playing']

    if voice.is_playing():
        voice.pause()
        save_json()
        log(guild_id, "web_pause -> Paused")
        return [True, 'Paused playing']

    log(guild_id, "web_pause -> Unknown error")
    return [False, 'Unknown error']

async def web_resume(web_data):
    log(web_data.guild_id, 'web_resume', [], log_type='function', author=web_data.author)
    guild_id = web_data.guild_id
    guild_object = bot.get_guild(int(guild_id))
    voice = guild_object.voice_client

    if voice is None:
        log(guild_id, "web_resume -> Not in a voice channel")
        return [False, 'Not in a voice channel']

    if not voice.is_playing():
        if voice.is_paused():
            voice.resume()
            save_json()
            log(guild_id, "web_resume -> Resumed")
            return [True, 'Resumed playing']
        log(guild_id, "web_resume -> Nothing paused")
        return [False, 'Nothing paused']

    if voice.is_playing():
        save_json()
        log(guild_id, "web_resume -> Nothing paused")
        return [False, 'Nothing paused']



    log(guild_id, "web_resume -> Unknown error")
    return [False, 'Unknown error']

async def web_skip(web_data):
    log(web_data.guild_id, 'web_skip', [], log_type='function', author=web_data.author)
    guild_id = web_data.guild_id
    guild_object = bot.get_guild(int(guild_id))
    voice = guild_object.voice_client

    now_to_last(guild_id)

    if voice is None:
        log(guild_id, "web_skip -> Not in a voice channel")
        return [False, 'Not in a voice channel']

    if not voice.is_playing():
        log(guild_id, "web_skip -> Not playing")
        return [False, 'Not playing']

    if voice.is_playing():
        voice.stop()
        save_json()
        log(guild_id, "web_skip -> Stopped")
        return [True, 'Stopped playing']

    log(guild_id, "web_skip -> Unknown error")
    return [False, 'Unknown error']

async def web_shuffle(web_data):
    log(web_data.guild_id, 'web_shuffle', [], log_type='function', author=web_data.author)
    guild_id = web_data.guild_id

    if len(guild[guild_id].queue) == 0:
        log(guild_id, "web_shuffle -> No songs in queue")
        return [False, 'No songs in queue']

    random.shuffle(guild[guild_id].queue)
    save_json()

    log(guild_id, "web_shuffle -> Shuffled queue")
    return [True, 'Shuffled queue']

async def web_clear(web_data):
    log(web_data.guild_id, 'web_clear', [], log_type='function', author=web_data.author)
    guild_id = web_data.guild_id

    if len(guild[guild_id].queue) == 0:
        log(guild_id, "web_clear -> No songs in queue")
        return [False, 'No songs in queue']

    guild[guild_id].queue.clear()
    save_json()
    log(guild_id, "web_clear -> Cleared queue")
    return [True, 'Cleared queue']

async def web_volume(web_data, vol_range, vol_input):
    log(web_data.guild_id, 'web_volume', [vol_range, vol_input], log_type='function', author=web_data.author)
    guild_id = web_data.guild_id
    guild_object = bot.get_guild(int(guild_id))
    voice = guild_object.voice_client

    if int(vol_range) != int(vol_input):
        log(guild_id, "web_volume -> Mismatched range and input")
        return [False, 'Mismatched range and input (Internal web error -> contact developer)']
    else:
        number = int(vol_input)

    if number:
        new_volume = int(number) / 100

        guild[guild_id].options.volume = new_volume
        if voice:
            try:
                if voice.source:
                    voice.source.volume = new_volume
                    voice.source = discord.PCMVolumeTransformer(voice.source, volume=new_volume)
            except AttributeError:
                pass

        save_json()

        log(guild_id, "web_volume -> Changed volume")
        return [True, f'Changed volume to {guild[guild_id].options.volume * 100}%']

    log(guild_id, "web_volume -> No number given")
    return [False, 'No number given (Internal web error -> contact developer)']

async def web_queue_from_video(web_data, url, number: int=None):
    log(web_data.guild_id, 'web_queue', [url, number], log_type='function', author=web_data.author)
    guild_id = web_data.guild_id
    video = None

    if url == 'last_played':
        video = guild[guild_id].last_played
    elif url == 'now_playing':
        video = guild[guild_id].now_playing

    if type(video) == Video:
        pass
    elif type(video) == Radio:
        video = Radio(name=video.radio_name, author=video.author, radio_name=video.radio_name)
    elif type(video) == FromProbe:
        video = FromProbe(url=video.url, title=video.title, duration=video.duration, author=video.author, channel_name=video.channel_name, channel_link=video.channel_link)
    elif type(video) == LocalFile:
        video = LocalFile(title=video.title, duration=video.duration, author=video.author, number=video.number)

    if video:
        try:
            if not number and number != 0 and number != '0':
                guild[guild_id].queue.append(video)
            else:
                guild[guild_id].queue.insert(number, video)
            save_json()
            log(guild_id, "web_queue -> Queued")
            return [True, f'Queued {video.title}', video]
        except Exception as e:
            print(e)
            log(guild_id, "web_queue -> Error while queuing")
            return [False, 'Error while queuing (Internal web error -> contact developer)']
    else:
        log(guild_id, "web_queue -> Error while getting video")
        return [False, 'Error while getting video (Internal web error -> contact developer)']

async def web_queue_from_url(web_data, url, position=None):
    if position:
        if position == "start":
            position = 0
        elif position == "end":
            position = None

    if url[0:33] == "https://www.youtube.com/playlist?":
        try:
            playlist_videos = youtubesearchpython.Playlist.getVideos(url)
        except KeyError:
            message = f'This playlist is unviewable: `{url}`'
            return [False, message]
        playlist_songs = 0

        playlist_videos = playlist_videos['videos']
        if position or position == 0:
            playlist_videos = list(reversed(playlist_videos))

        for index, val in enumerate(playlist_videos):
            playlist_songs += 1

            # noinspection PyTypeChecker
            url = f"https://www.youtube.com/watch?v={playlist_videos[index]['id']}"
            video = Video(url, web_data.id)

            if position or position == 0:
                guild[web_data.guild_id].queue.insert(position, video)
            else:
                guild[web_data.guild_id].queue.append(video)

        message = f"`{playlist_songs}` songs from playlist added to queue!"

        save_json()

        return [True, message, None]

    elif url:

        video_id = extract_yt_id(url)

        if video_id is None:
            message = f'Invalid URL: `{url}`'
            save_json()
            return [False, message]

        url = f"https://www.youtube.com/watch?v={video_id}"
        video = Video(url, web_data.author_id)

        if position or position == 0:
            guild[web_data.guild_id].queue.insert(position, video)
        else:
            guild[web_data.guild_id].queue.append(video)

        message = f'{video.title} added to queue!'

        save_json()
        return [True, message, None]

async def web_queue_from_radio(web_data, radio_name, position=None):
    if position:
        if position == "start":
            position = 0
        elif position == "end":
            position = None

    if radio_name in radio_dict.keys():

        video = Radio(radio_name, web_data.id, radio_name)

        if position or position == 0:
            guild[web_data.guild_id].queue.insert(position, video)
        else:
            guild[web_data.guild_id].queue.append(video)

        message = f'`{video.title}` added to queue!'

        save_json()

        return [True, message, video]

    else:
        message = f'Radio station `{radio_name}` does not exist!'

        save_json()

        return [False, message]

# --------------------------------------------- WEB SERVER --------------------------------------------- #

app = Flask(__name__)
app.config['SECRET_KEY'] = config.WEB_SECRET_KEY

@app.route('/')
async def index_page():
    if 'discord_user' in session.keys(): user = session['discord_user']
    else: user = None

    return render_template('nav/index.html', user=user)

@app.route('/about')
async def about_page():
    if 'discord_user' in session.keys():
        user = session['discord_user']
    else:
        user = None

    return render_template('nav/about.html', user=user)

@app.route('/guild')
async def guilds_page():
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
    if 'discord_user' in session.keys():
        user = session['discord_user']
        user_name, user_id = user['username'], int(user['id'])
        mutual_guild_ids = session['mutual_guild_ids']
    elif 'mutual_guild_ids' in session.keys():
        mutual_guild_ids = session['mutual_guild_ids']
        user = None
        user_name, user_id = "WEB", bot_id
    else:
        user = None
        user_name, user_id = "WEB", bot_id
        mutual_guild_ids = []

    errors = []
    messages = []

    if request.method == 'POST':

        web_data = WebData(int(guild_id), user_name, user_id)
        response = [True, '']

        keys = request.form.keys()
        if 'del_btn' in keys:
            log(web_data.guild_id, 'web_remove', [request.form['del_btn']], log_type='web', author=web_data.author)
            response = await web_remove(web_data, request.form['del_btn'])
        if 'up_btn' in keys:
            log(web_data.guild_id, 'web_up', [request.form['up_btn']], log_type='web', author=web_data.author)
            response = await web_up(web_data, request.form['up_btn'])
        if 'down_btn' in keys:
            log(web_data.guild_id, 'web_down', [request.form['down_btn']], log_type='web', author=web_data.author)
            response = await web_down(web_data, request.form['down_btn'])
        if 'top_btn' in keys:
            log(web_data.guild_id, 'web_top', [request.form['top_btn']], log_type='web', author=web_data.author)
            response = await web_top(web_data, request.form['top_btn'])
        if 'bottom_btn' in keys:
            log(web_data.guild_id, 'web_bottom', [request.form['bottom_btn']], log_type='web', author=web_data.author)
            response = await web_bottom(web_data, request.form['bottom_btn'])
        if 'stop_btn' in keys:
            log(web_data.guild_id, 'web_stop', [], log_type='web', author=web_data.author)
            response = await web_stop(web_data)
        if 'pause_btn' in keys:
            log(web_data.guild_id, 'web_pause', [], log_type='web', author=web_data.author)
            response = await web_pause(web_data)
        if 'resume_btn' in keys:
            log(web_data.guild_id, 'web_resume', [], log_type='web', author=web_data.author)
            response = await web_resume(web_data)

        if 'skip_btn' in keys:
            log(web_data.guild_id, 'web_skip', [], log_type='web', author=web_data.author)
            response = await web_skip(web_data)
        if 'shuffle_btn' in keys:
            log(web_data.guild_id, 'web_shuffle', [], log_type='web', author=web_data.author)
            response = await web_shuffle(web_data)
        if 'clear_btn' in keys:
            log(web_data.guild_id, 'web_clear', [], log_type='web', author=web_data.author)
            response = await web_clear(web_data)

        if 'queue_btn' in keys:
            log(web_data.guild_id, 'web_add_queue', [request.form['queue_btn']], log_type='web', author=web_data.author)
            response = await web_queue_from_video(web_data, request.form['queue_btn'])
        if 'nextup_btn' in keys:
            log(web_data.guild_id, 'web_nextup', [request.form['nextup_btn'], 0], log_type='web', author=web_data.author)
            response = await web_queue_from_video(web_data, request.form['nextup_btn'], 0)

        if 'volume_btn' in keys:
            log(web_data.guild_id, 'web_volume', [request.form['volumeRange'], request.form['volumeInput']], log_type='web', author=web_data.author)
            response = await web_volume(web_data, request.form['volumeRange'], request.form['volumeInput'])

        if 'ytURL' in keys:
            log(web_data.guild_id, 'web_add_queue', [request.form['ytURL'], request.form['addPosition']], log_type='web', author=web_data.author)
            response = await web_queue_from_url(web_data, request.form['ytURL'], request.form['addPosition'])
        if 'radio-checkbox' in keys:
            log(web_data.guild_id, 'web_add_queue', [request.form['radio-checkbox'], request.form['addPosition']], log_type='web', author=web_data.author)
            response = await web_queue_from_radio(web_data, request.form['radio-checkbox'], request.form['addPosition'])

        if not response[0]:
            errors = [response[1]]
        else:
            messages = [response[1]]

    try:
        guild_object = guild[int(guild_id)]

        if key != guild_object.data.key:
            if guild_object.id in mutual_guild_ids:
                return redirect(f'/guild/{guild_id}&key={guild_object.data.key}')
            return redirect(url_for('guild_get_key_page', guild_id=guild_id))

        return render_template('control/guild.html', guild=guild_object, convert_duration=convert_duration, get_username=get_username, errors=errors, messages=messages, user=user, volume=round(guild_object.options.volume * 100), radios=list(radio_dict.values()))
    except (KeyError, ValueError, TypeError):
        return render_template('base/message.html', guild_id=guild_id, user=user, message="That Server doesn't exist or the bot is not in it", errors=None, title='Error')


@app.route('/login')
async def login_page():
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
    if 'discord_user' in session.keys():
        user = session['discord_user']
        username = user['username']
        discriminator = user['discriminator']
        session.pop('access_token')
        session.pop('discord_user')
        session.pop('mutual_guild_ids')
        return render_template('base/message.html', message=f"Logged out as {username}#{discriminator}", errors=None, user=None, title='Logout Success')
    return redirect(url_for('index_page'))

@app.route('/reset')
async def reset_page():
    session.clear()
    return redirect(url_for('index_page'))

@app.route('/invite')
async def invite_page():
    return redirect(f"https://discord.com/api/oauth2/authorize?client_id={config.CLIENT_ID}&permissions={config.PERMISSIONS}&scope=bot")

@app.route('/admin', methods=['GET', 'POST'])
async def admin_page():
    if 'discord_user' in session.keys():
        user = session['discord_user']
        user_name = user['username']
        user_id = user['id']
    else:
        return render_template('base/message.html', message="You are not logged in or don't have permission", errors=None, user=None, title='Error')

    errors = []
    messages = []

    if request.method == 'POST':
        guild_id = int(request.form['guild_id_select'])

        web_data = WebData(guild_id, user_name, user_id)

        keys = request.form.keys()
        try:
            if 'download_btn' in keys:
                file_name = request.form['download_file']
                log(web_data.guild_id, 'download file', [file_name], log_type='web', author=web_data.author)
                try:
                    if file_name == 'log.txt' or file_name == 'data.txt' or file_name == 'activity.log':
                        return send_file(f'{file_name}', as_attachment=True)
                    else:
                        return send_file(f'src/{file_name}', as_attachment=True)
                except Exception as e:
                    return str(e)
            if 'upload_btn' in keys:
                f = request.files['file']
                file_name = request.form['download_file']
                log(web_data.guild_id, 'upload file', [f.filename, file_name], log_type='web', author=web_data.author)
                if not f:
                    errors = ['No file']
                elif file_name != f.filename:
                    errors = ['File name does not match']
                else:
                    try:
                        if file_name == 'log.txt' or file_name == 'data.txt' or file_name == 'activity.log':
                            f.save(f.filename)
                            messages = ['File uploaded']
                        else:
                            f.save(f"src/{f.filename}")
                            messages = ['File uploaded']
                    except Exception as e:
                        return str(e)
            if 'update_stopped_btn' in keys:
                guild[guild_id].options.stopped = bool(request.form['stoppedSelect'])
                messages = ['stopped updated']
                log(web_data.guild_id, 'update stopped', [guild[guild_id].options.stopped], log_type='web', author=web_data.author)
            if 'update_loop_btn' in keys:
                guild[guild_id].options.loop = bool(request.form['loopSelect'])
                messages = ['loop updated']
                log(web_data.guild_id, 'update loop', [guild[guild_id].options.loop], log_type='web', author=web_data.author)
            if 'update_is_radio_btn' in keys:
                guild[guild_id].options.is_radio = bool(request.form['is_radioSelect'])
                messages = ['is_radio updated']
                log(web_data.guild_id, 'update is_radio', [guild[guild_id].options.is_radio], log_type='web', author=web_data.author)
            if 'update_buttons_btn' in keys:
                guild[guild_id].options.buttons = bool(request.form['buttonsSelect'])
                messages = ['buttons updated']
                log(web_data.guild_id, 'update buttons', [guild[guild_id].options.buttons], log_type='web', author=web_data.author)
            if 'update_language_btn' in keys:
                guild[guild_id].options.language = request.form['languageSelect']
                messages = ['language updated']
                log(web_data.guild_id, 'update language', [guild[guild_id].options.language], log_type='web', author=web_data.author)
            if 'update_response_type_btn' in keys:
                guild[guild_id].options.response_type = request.form['response_typeSelect']
                messages = ['response_type updated']
                log(web_data.guild_id, 'update response_type', [guild[guild_id].options.response_type], log_type='web', author=web_data.author)
            if 'update_buffer_btn' in keys:
                guild[guild_id].options.buffer = int(request.form['bufferSelect'])
                messages = ['buffer updated']
                log(web_data.guild_id, 'update buffer', [guild[guild_id].options.buffer], log_type='web', author=web_data.author)
            if 'update_volume_btn' in keys:
                guild[guild_id].options.volume = int(request.form['volumeSelect'])
                messages = ['volume updated']
                log(web_data.guild_id, 'update volume', [guild[guild_id].options.volume], log_type='web', author=web_data.author)
        except Exception as e:
            errors = [str(e)]
            log(web_data.guild_id, 'error', [str(e)], log_type='web', author=web_data.author)

    if 'discord_user' in session.keys():
        user = session['discord_user']
        if int(user['id']) == my_id:
            return render_template('nav/admin.html', user=user, guild=guild.values(), languages_dict=languages_dict, errors=errors, messages=messages)
    return redirect(url_for('index_page'))


def application():
    web_thread = threading.Thread(target=app.run, kwargs={'debug': False, 'host': '0.0.0.0', 'port': int(os.environ.get('PORT', config.PORT))})
    bot_thread = threading.Thread(target=bot.run, kwargs={'token':config.BOT_TOKEN})

    web_thread.start()
    bot_thread.start()

    web_thread.join()
    bot_thread.join()

application()
