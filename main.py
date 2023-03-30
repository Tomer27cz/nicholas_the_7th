import random

import discord
import asyncio
from discord import FFmpegPCMAudio, app_commands
from discord.ext import commands
from discord.ui import View

from flask import Flask, render_template, request
import threading

import yt_dlp
import youtubesearchpython
from urllib.request import urlopen
from bs4 import BeautifulSoup
import requests
import json

from os import path, listdir
from mutagen.mp3 import MP3
import sys
from typing import Literal
import traceback
import datetime

from api_keys import api_key_testing as api_key

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
            print_message('no guild', "Trying to sync commands")
            await self.tree.sync()
            print_message('no guild', f"Synced slash commands for {self.user}")
        await bot.change_presence(activity=discord.Game(name=f"/help"))
        print_message('no guild', 'Logged in as:\n{0.user.name}\n{0.user.id}'.format(bot))

    async def on_guild_join(self, guild_object):
        print_message(guild_object.id, f"Joined guild {guild_object.name} with {guild_object.member_count} members and {len(guild_object.voice_channels)} voice channels")
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

        # if before.channel is not None:
        #     before_state = before.channel.guild.voice_client
        # else:
        #     before_state = None
        #
        # if after.channel is not None:
        #     after_state = after.channel.guild.voice_client
        # else:
        #     after_state = None
        #
        # print(before_state)
        # print(after_state)
        # print(voice_state)
        #
        # if voice_state is not None:
        #     if before_state:
        #         if not after_state:
        #             return
        #         print(after_state.is_playing())
        #         print(before_state.is_playing())
        #
        #         if before_state.is_playing() and not after_state.is_playing():
        #             print("was playing and now is not")
        #

        if voice_state is not None and len(voice_state.channel.members) == 1:
            after.channel.guild.voice_client.stop()
            await voice_state.disconnect()
            print_message(member.guild.id, "-->> Disconnecting when last person left <<--")
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
                    print_message(member.guild.id, f"-->> Disconnecting after {guild[member.guild.id].options.buffer} seconds of nothing playing <<--")
                    now_to_last(member.guild.id)
                if not voice.is_connected():
                    break

    async def on_command_error(self, ctx, error):
        if isinstance(error, commands.CheckFailure):
            print_command(ctx, 'Permission Fail', ctx.command)
            await ctx.reply("（ ͡° ͜ʖ ͡°)つ━☆・。\n"
                            "⊂　　 ノ 　　　・゜+.\n"
                            "　しーＪ　　　°。+ ´¨)\n"
                            "　　　　　　　　　.· ´¸.·´¨) ¸.·*¨)\n"
                            "　　　　　　　　　　(¸.·´ (¸.·' ☆ **Fuck off**\n"
                            "*You don't have permission to use this command*")
        else:
            print_message(ctx.guild.id, f"{error}")
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
    def __init__(self, guild_id, author):
        self.guild_id = guild_id
        self.author = author


class Options:
    def __init__(self, guild_id):
        self.guild_id = guild_id
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
        guild_object = bot.get_guild(int(guild_id))
        if guild_object:
            self.name = guild_object.name
            self.id = guild_object.id
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
                            self.member_count = guild[guild_id].data.member_count
                            self.owner_id = guild[guild_id].data.owner_id
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
            self.member_count = None
            self.owner_id = None
            self.created_at = None
            self.description = None
            self.large = None
            self.icon = None
            self.banner = None
            self.splash = None
            self.discovery_splash = None


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
    def __init__(self, name, author, radio_name, url=None, picture=None, duration=None, channel_name=None, channel_link=None, radio_website=None):
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
            html = urlopen(self.url).read()
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


class Guild:
    def __init__(self, guild_id):
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
    print_message('no guild', 'Loaded sound_effects folder')

# ------------ PRINT --------------------

def print_command(ctx, text_data, opt):
    now_time = datetime.datetime.now(datetime.timezone(datetime.timedelta(seconds=3600), 'CET'))
    message = f"{now_time.strftime('(CET) %d/%m/%Y %X')} | C {ctx.guild.id} | Command ({text_data}) was requested by ({ctx.message.author}) -> {opt}"

    print(message)
    message += "\n"

    with open("log.txt", "a", encoding="utf-8") as f:
        f.write(message)

def print_function(ctx, text_data, opt):
    now_time = datetime.datetime.now(datetime.timezone(datetime.timedelta(seconds=3600), 'CET'))
    message = f"{now_time.strftime('(CET) %d/%m/%Y %X')} | F {ctx.guild.id} | {text_data} -> {opt}"

    print(message)
    message += "\n"

    with open("log.txt", "a", encoding="utf-8") as f:
        f.write(message)

def print_web(web_data, command, opt):
    now_time = datetime.datetime.now(datetime.timezone(datetime.timedelta(seconds=3600), 'CET'))
    message = f"{now_time.strftime('(CET) %d/%m/%Y %X')} | W {web_data.guild_id} | Command ({command}) was requested by ({web_data.author}) -> {opt}"

    print(message)
    message += "\n"

    with open("log.txt", "a", encoding="utf-8") as f:
        f.write(message)

def print_message(guild_id, content):
    now_time = datetime.datetime.now(datetime.timezone(datetime.timedelta(seconds=3600), 'CET'))
    message = f"{now_time.strftime('(CET) %d/%m/%Y %X')} | M {guild_id} | {content}"

    print(message)
    message += "\n"

    with open("log.txt", "a", encoding="utf-8") as f:
        f.write(message)

# ---------------------------------------------- GUILD TO JSON ---------------------------------------------------------

# def video_to_json(video):
#     if video is None:
#         return None
#     try:
#         author = video.author.id
#     except AttributeError:
#         author = my_id
#
#     video_dict = {'url': video.url,
#                   'author': author,
#                   'title': video.title,
#                   'picture': video.picture,
#                   'duration': video.duration,
#                   'channel_name': video.channel_name,
#                   'channel_link': video.channel_link}
#     return video_dict


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

    guild_dict['options'] = guild_object.options.__dict__
    guild_dict['data'] = GuildData(guild_object.options.guild_id).__dict__
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
        video = Radio(url=video_dict['url'],
                         author=video_dict['author'],
                         name=video_dict['title'],
                         picture=video_dict['picture'],
                         duration=video_dict['duration'],
                         channel_name=video_dict['channel_name'],
                         channel_link=video_dict['channel_link'],
                         radio_website=video_dict['radio_website'],
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
    guild_object = Guild(guild_dict['options']['guild_id'])
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
print_message('no guild', "--------------------------------------- NEW / REBOOTED ----------------------------------------")


build_new_guilds = False

with open('src/radio.json', 'r') as file:
    radio_dict = json.load(file)
print_message('no guild', 'Loaded radio.json')


with open('src/languages.json', 'r') as file:
    languages_dict = json.load(file)
    text = languages_dict['en']
print_message('no guild', 'Loaded languages.json')


with open('src/other.json', 'r') as file:
    other = json.load(file)
    react_dict = other['reactions']
    prefix = other['prefix']
    my_id = other['my_id']
    bot_id = other['bot_id']
    vlc_logo = other['logo']
    authorized_users = other['authorized']
print_message('no guild', 'Loaded other.json')


# ---------------------------------------------- BOT -------------------------------------------------------------------

bot = Bot()

print_message('no guild', 'Bot class initialized')

# ----------------------------------------------------------------------------------------------------------------------


if build_new_guilds:
    print_message('no guild', 'Building new guilds.json ...')
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
print_message('no guild', 'Loaded guilds.json')


all_sound_effects = ["No sound effects found"]
load_sound_effects()


# ---------------------------------------------- SAVE JSON -------------------------------------------------------------

def save_json():
    with open('src/guilds.json', 'w') as f:
        json.dump(guilds_to_json(guild), f, indent=4)
    # print_message(guild_id='all', content='Updated guilds.json')

# ---------------------------------------------- TEXT ----------------------------------------------------------

def tg(guild_id, content):
    lang = guild[guild_id].options.language
    return languages_dict[lang][content]

# --------- video_info / url --------

def get_playlist_from_url(url):
    try:
        code = url[url.index('&list=')+1:url.index('&index=')]
    except ValueError:
        code = url[url.index('&list=')+1:]
    playlist_url = 'https://www.youtube.com/playlist?' + code
    return playlist_url

# -------------- convert / get -----------

def get_username(user_id):
    try:
        name = bot.get_user(user_id).name
        return name
    except:
        return user_id


def now_to_last(guild_id):
    if guild[guild_id].now_playing is not None:
        print(f"{guild[guild_id].now_playing.title} is now the last played song")

        guild[guild_id].last_played = guild[guild_id].now_playing
        guild[guild_id].now_playing = None
        save_json()


def mp3_length(path_of_mp3):
    audio = MP3(path_of_mp3)
    length = audio.info.length
    return length


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
    #  (link, title, picture, duration, user, author, author_link)
    #  (  0    1       2         3        4    5          6      )
    embed = (discord.Embed(title=name,
                           description=f'```\n{video.title}\n```',
                           color=discord.Color.blurple()))
    if name == tg(guild_id, "Now playing"):
        guild[guild_id].now_playing = video
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

    # # noinspection PyUnusedLocal
    # @discord.ui.button(emoji=react_dict['false'], style=discord.ButtonStyle.red, custom_id='6')
    # async def callback_6(self, interaction, button):
    #     await interaction.response.edit_message(content=f'{tg(self.guild_id, "Nothing selected")}', view=None)


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
            response = await queue_command(self.ctx, playlist_url, 0, True, self.force)
        else:
            response = await queue_command(self.ctx, playlist_url, None, True, self.force)

        msg = await interaction.original_response()
        await msg.edit(content=response[1])

        if self.from_play:
            await play_def(self.ctx)

    # noinspection PyUnusedLocal
    @discord.ui.button(label='No, just this', style=discord.ButtonStyle.blurple)
    async def callback_2(self, interaction, button):
        pure_url = self.url[:self.url.index('&list=')]
        if self.force:
            response = await queue_command(self.ctx, pure_url, 0, True, self.force)
        else:
            response = await queue_command(self.ctx, pure_url, None, True, self.force)
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
    print_command(ctx, 'queue', [url, position])

    await queue_command_def(ctx, url, position)


@bot.hybrid_command(name='next_up', with_app_command=True, description=text['next_up'], help=text['next_up'])
@app_commands.describe(url=text['url'], user_only=text['ephemeral'])
async def next_up(ctx: commands.Context,
                 url,
                 user_only: bool = False
                 ):
    print_command(ctx, 'next', [user_only])

    await next_up_def(ctx, url, user_only)


@bot.hybrid_command(name='skip', with_app_command=True, description=text['skip'], help=text['skip'])
async def skip(ctx: commands.Context):
    print_command(ctx, 'skip', None)

    await skip_def(ctx)


@bot.hybrid_command(name='remove', with_app_command=True, description=text['queue_remove'], help=text['queue_remove'])
@app_commands.describe(number=text['number'], user_only=text['ephemeral'])
async def remove(ctx: commands.Context,
                 number: int,
                 user_only: bool = False
                 ):
    print_command(ctx, 'remove', [number, user_only])

    await remove_def(ctx, number, ephemeral=user_only)


@bot.hybrid_command(name='clear', with_app_command=True, description=text['clear'], help=text['clear'])
@app_commands.describe(user_only=text['ephemeral'])
async def clear(ctx: commands.Context,
                 user_only: bool = False
                 ):
    print_command(ctx, 'clear', [user_only])

    await clear_def(ctx, user_only)


@bot.hybrid_command(name='shuffle', with_app_command=True, description=text['shuffle'], help=text['shuffle'])
@app_commands.describe(user_only=text['ephemeral'])
async def shuffle(ctx: commands.Context,
                 user_only: bool = False
                 ):
    print_command(ctx, 'shuffle', [user_only])

    await shuffle_def(ctx, user_only)


@bot.hybrid_command(name='show', with_app_command=True, description=text['queue_show'], help=text['queue_show'])
@app_commands.describe(display_type=text['display_type'], user_only=text['ephemeral'])
async def show(ctx: commands.Context,
               display_type: Literal['short', 'medium', 'long'] = None,
               user_only: bool = False
               ):
    print_command(ctx, 'show', [display_type, user_only])

    await show_def(ctx, display_type, user_only)


@bot.hybrid_command(name='search', with_app_command=True, description=text['search'],  help=text['search'])
@app_commands.describe(search_query=text['search_query'])
async def search_command(ctx: commands.Context,
                         search_query,
                         ):
    print_command(ctx, 'search', [search_query])

    await search_command_def(ctx, search_query)

# --------------------------------------- PLAYER --------------------------------------------------


@bot.hybrid_command(name='play', with_app_command=True, description=text['play'], help=text['play'])
@app_commands.describe(url=text['play'], force=text['force'])
async def play(ctx: commands.Context,
               url=None,
               force=False
               ):
    print_command(ctx, 'play', [url])

    await play_def(ctx, url, force)


@bot.hybrid_command(name='radio', with_app_command=True, description=text['radio'], help=text['radio'])
@app_commands.describe(favourite_radio=text['favourite_radio'], radio_code=text['radio_code'])
async def radio(ctx: commands.Context,
                favourite_radio: Literal['Rádio BLANÍK','Rádio BLANÍK CZ','Evropa 2','Fajn Radio','Hitrádio PopRock','Český rozhlas Pardubice','Radio Beat','Country Radio','Radio Kiss','Český rozhlas Vltava','Hitrádio Černá Hora'] = None,
                radio_code: int = None,
                ):
    print_command(ctx, 'radio', [favourite_radio, radio_code])

    await radio_def(ctx, favourite_radio, radio_code)


@bot.hybrid_command(name='ps', with_app_command=True, description=text['ps'], help=text['ps'])
@app_commands.describe(effect_number=text['effects_number'])
async def ps(ctx: commands.Context,
             effect_number: app_commands.Range[int, 1, len(all_sound_effects)]
             ):
    print_command(ctx, 'ps', [effect_number])

    await ps_def(ctx, effect_number)


@bot.hybrid_command(name='nowplaying', with_app_command=True, description=text['nowplaying'], help=text['nowplaying'])
@app_commands.describe(user_only=text['ephemeral'])
async def now(ctx: commands.Context,
              user_only: bool = False
              ):
    print_command(ctx, 'nowplaying', [user_only])

    await now_def(ctx, user_only)


@bot.hybrid_command(name='last', with_app_command=True, description=text['last'], help=text['last'])
@app_commands.describe(user_only=text['ephemeral'])
async def last(ctx: commands.Context,
              user_only: bool = False
              ):
    print_command(ctx, 'last', [user_only])

    await last_def(ctx, user_only)

@bot.hybrid_command(name='loop', with_app_command=True, description=text['loop'], help=text['loop'])
async def loop_command(ctx: commands.Context):
    print_command(ctx, 'loop', None)

    await loop_command_def(ctx)


@bot.hybrid_command(name='loop_this', with_app_command=True, description=text['loop_this'], help=text['loop_this'])
async def loop_this(ctx: commands.Context):
    print_command(ctx, 'loop_this', None)

    await loop_this_def(ctx)


# --------------------------------------- VOICE --------------------------------------------------


@bot.hybrid_command(name='stop', with_app_command=True, description=f'Stop the player')
async def stop(ctx: commands.Context):
    print_command(ctx, 'stop', [])

    await stop_def(ctx)


@bot.hybrid_command(name='pause', with_app_command=True, description=f'Pause the player')
async def pause(ctx: commands.Context):
    print_command(ctx, 'pause', [])

    await pause_def(ctx)


@bot.hybrid_command(name='resume', with_app_command=True, description=f'Resume the player')
async def resume(ctx: commands.Context):
    print_command(ctx, 'resume', [])

    await resume_def(ctx)


@bot.hybrid_command(name='join', with_app_command=True, description=text['join'], help=text['join'])
@app_commands.describe(channel_id=text['channel_id'])
async def join(ctx: commands.Context,
               channel_id=None
               ):
    print_command(ctx, 'join', [channel_id])

    await join_def(ctx, channel_id)

@bot.hybrid_command(name='disconnect', with_app_command=True, description=text['die'], help=text['die'])
async def disconnect(ctx: commands.Context):
    print_command(ctx, 'disconnect', [])

    await disconnect_def(ctx)


@bot.hybrid_command(name='volume', with_app_command=True, description=text['volume'], help=text['volume'])
@app_commands.describe(volume=text['volume'], user_only=text['ephemeral'])
async def volume_command(ctx: commands.Context,
                         volume = None,
                         user_only: bool = False
                         ):
    print_command(ctx, 'volume', [volume, user_only])

    await volume_command_def(ctx, volume, user_only)


# --------------------------------------- MENU --------------------------------------------------


@bot.tree.context_menu(name='Add to queue')
async def add_to_queue(inter, message: discord.Message):
    ctx = await bot.get_context(inter)
    print_command(ctx, 'add_to_queue', [message.content])
    response = await queue_command(ctx, message.content, None, True)
    if not inter.response.is_done():
        await inter.response.send_message(content=response[1], ephemeral=True)


@bot.tree.context_menu(name='Show Profile')
async def show_profile(inter, member: discord.Member):
    ctx = await bot.get_context(inter)
    print_command(ctx, 'show_profile', [member])
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
async def ping(ctx: commands.Context):
    print_command(ctx, 'ping', [])

    await ping_def(ctx)


# noinspection PyTypeHints
@bot.hybrid_command(name='language', with_app_command=True, description=text['language'], help=text['language'])
@app_commands.describe(country_code=text['country_code'])
async def language_command(ctx: commands.Context,
                   country_code: Literal[tuple(languages_dict.keys())]
                   ):
    print_command(ctx, 'language', [country_code])

    await language_command_def(ctx, country_code)


@bot.hybrid_command(name='sound_effects', with_app_command=True, description=text['sound'], help=text['sound'])
@app_commands.describe(user_only=text['ephemeral'])
async def sound_effects(ctx: commands.Context,
                user_only: bool = True
                ):
    print_command(ctx, 'sound', [user_only])

    await sound_effects_def(ctx, user_only)


@bot.hybrid_command(name='list_radios', with_app_command=True, description=text['list_radios'], help=text['list_radios'])
@app_commands.describe(user_only=text['ephemeral'])
async def list_radios(ctx: commands.Context,
                      user_only: bool = True
                      ):
    print_command(ctx, 'list_radios', [user_only])

    await list_radios_def(ctx, user_only)


# ---------------------------------------- ADMIN --------------------------------------------------


async def is_authorised(ctx):
    if ctx.author.id in authorized_users or ctx.author.id == 349164237605568513:
        return True


@bot.hybrid_command(name='zz_announce', with_app_command=True)
@commands.check(is_authorised)
async def announce_command(ctx: commands.Context,
                      message
                      ):
    print_command(ctx, 'zz_announce', [message])

    await announce_command_def(ctx, message)


@bot.hybrid_command(name='zz_ear_rape_play', with_app_command=True)
@commands.check(is_authorised)
async def rape_play_command(ctx: commands.Context,
                      effect_number: int = None,
                      channel_id = None,
                      ):
    print_command(ctx, 'zz_rape_play', [effect_number, channel_id])

    await rape_play_command_def(ctx, effect_number, channel_id)

@bot.hybrid_command(name='zz_ear_rape', with_app_command=True)
@commands.check(is_authorised)
async def ear_rape_command(ctx: commands.Context):
    print_command(ctx, 'zz_rape', None)

    await ear_rape_command_def(ctx)


@bot.hybrid_command(name='zz_kys', with_app_command=True)
@commands.check(is_authorised)
async def kys(ctx: commands.Context):
    print_command(ctx, 'zz_kys', None)

    await kys_def(ctx)


@bot.hybrid_command(name='zz_config', with_app_command=True)
@commands.check(is_authorised)
async def config_command(ctx: commands.Context,
                         config_file: discord.Attachment,
                         config_type:  Literal['guilds', 'other', 'radio', 'languages'] = 'guilds',
                         ):
    print_command(ctx, 'zz_config', [config_file, config_type])

    await config_command_def(ctx, config_file, config_type)


@bot.hybrid_command(name='zz_log', with_app_command=True)
@commands.check(is_authorised)
async def log_command(ctx: commands.Context,
                      log_type: Literal['log.txt', 'guilds.json', 'other.json', 'radio.json', 'languages.json', 'activity.log'] = 'log.txt'
                      ):
    print_command(ctx, 'zz_log', [log_type])

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
    print_command(ctx, 'zz_owner_commands', [stopped, loop, is_radio, buttons, language, response_type, volume, server])

    await change_config_def(ctx, stopped, loop, is_radio, buttons, language, response_type, buffer, volume, server)


@bot.hybrid_command(name='zz_probe', with_app_command=True)
@commands.check(is_authorised)
async def probe_command(ctx: commands.Context,
                        url = None,
                        user_only: bool = False
                        ):
    print_command(ctx, 'zz_probe', [url])

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
    print_function(ctx, 'queue_command_def', [url, position, mute_response, force, from_play])
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
            print_message(guild_id, "------------------------------- playlist -------------------------")
            tb = traceback.format_exc()
            print_message(guild_id, tb)
            print_message(guild_id, "--------------------------------------------------------------")

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

        message = f"`{playlist_songs}` {tg(guild_id, 'songs from playlist added to queue!')}"
        if not mute_response:
            await ctx.reply(message)

        save_json()

        return [True, message, None]

    elif url:
        if 'index=' in url or 'list=' in url:
            view = PlaylistOptionView(ctx, url, force, from_play)

            message = tg(guild_id,
                                 'This video is from a **playlist**, do you want to add the playlist to **queue?**')
            await ctx.reply(message, view=view)
            return [False, message]
        try:

            video = Video(url, author.id)

            if position or position == 0: guild[guild_id].queue.insert(position, video)
            else: guild[guild_id].queue.append(video)

            message = f'[`{video.title}`](<{video.url}>) {tg(guild_id, "added to queue!")}'

            if not mute_response:
                await ctx.reply(message)

            save_json()

            return [True, message, video]

        except (ValueError, IndexError, TypeError):
            try:
                url_only_id = 'https://www.youtube.com/watch?v=' + url.split('watch?v=')[1]
                video = Video(url_only_id, author.id)

                if position or position == 0: guild[guild_id].queue.insert(position, video)
                else: guild[guild_id].queue.append(video)

                message = f'[`{video.title}`](<{video.url}>) {tg(guild_id, "added to queue!")}'

                if not mute_response:
                    await ctx.reply(message)

                save_json()

                return [True, message, video]

            except (ValueError, IndexError, TypeError):
                try:
                    # https://www.youtube.com/shorts/JRPKE_A9yjw
                    url_shorts = url.replace('shorts/', 'watch?v=')
                    video = Video(url_shorts, author.id)

                    if position or position == 0: guild[guild_id].queue.insert(position, video)
                    else: guild[guild_id].queue.append(video)

                    message = f'[`{video.title}`](<{video.url}>) {tg(guild_id, "added to queue!")}'

                    if not mute_response:
                        await ctx.reply(message)

                    save_json()

                    return [True, message, video]

                except (ValueError, IndexError, TypeError):

                    await search_command_def(ctx, url, 'short', force, from_play)

                    message = f'[`{url}`](<{url}>) {tg(guild_id, "is not supported!")}'

                    # await ctx.reply(message, ephemeral=True)

                    save_json()

                    return [False, message]


async def next_up_def(ctx: commands.Context,
                 url,
                 ephemeral: bool = False
                 ):
    print_function(ctx, 'next_up_def', [url, ephemeral])
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
    print_function(ctx, 'skip_def', [])
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
    print_function(ctx, 'remove_def', [number, display_type, ephemeral])
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
    print_function(ctx, 'clear_def', [ephemeral])
    guild_id = ctx.guild.id
    guild[guild_id].queue.clear()
    await ctx.reply(tg(guild_id, 'Removed **all** songs from queue'), ephemeral=ephemeral)
    return


async def shuffle_def(ctx: commands.Context,
                 ephemeral: bool = False
                 ):
    print_function(ctx, 'shuffle_def', [ephemeral])
    guild_id = ctx.guild.id
    random.shuffle(guild[guild_id].queue)
    await ctx.reply(tg(guild_id, 'Songs in queue shuffled'), ephemeral=ephemeral)
    return


async def show_def(ctx: commands.Context,
               display_type: Literal['short', 'medium', 'long'] = None,
               ephemeral: bool = False
               ):
    print_function(ctx, 'show_def', [display_type, ephemeral])
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
    print_function(ctx, 'search_command_def', [search_query, display_type, force, from_play])
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
    print_function(ctx, 'play_def', [url, force, mute_response])
    response = []
    guild_id = ctx.guild.id

    if url == 'next':
        if guild[guild_id].options.stopped:
            print_message(guild_id, "play_def -> stopped play next loop")
            now_to_last(guild_id)
            return

    voice = ctx.voice_client

    if not voice or voice is None:
        if ctx.author.voice is None:
            if not mute_response:
                await ctx.reply(tg(guild_id, "You are **not connected** to a voice channel"))
            return

    if url and url != 'next':
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
        print_message(guild_id, "------------------------------- play -------------------------")
        tb = traceback.format_exc()
        print_message(guild_id, tb)
        print_message(guild_id, "--------------------------------------------------------------")
        await ctx.reply(f'{tg(guild_id, "An **error** occurred while trying to play the song")}'
                        f' {bot.get_user(my_id).mention} ({sys.exc_info()[0]})')


async def radio_def(ctx: commands.Context,
                favourite_radio: Literal['Rádio BLANÍK','Rádio BLANÍK CZ','Evropa 2','Fajn Radio','Hitrádio PopRock','Český rozhlas Pardubice','Radio Beat','Country Radio','Radio Kiss','Český rozhlas Vltava','Hitrádio Černá Hora'] = None,
                radio_code: int = None,
                ):
    print_function(ctx, 'radio_def', [favourite_radio, radio_code])
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
    print_function(ctx, 'ps_def', [effect_number, mute_response])
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
        video = LocalFile(name, convert_duration(mp3_length(filename)), ctx.author.id, effect_number)
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
    print_function(ctx, 'now_def', [ephemeral])
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
    print_function(ctx, 'last_def', [ephemeral])
    guild_id = ctx.guild.id
    embed = create_embed(guild[guild_id].last_played, "Last played", guild_id)

    view = PlayerControlView(ctx)

    if guild[guild_id].options.buttons:
        await ctx.reply(embed=embed, view=view, ephemeral=ephemeral)
    else:
        await ctx.reply(embed=embed, ephemeral=ephemeral)

    save_json()


async def loop_command_def(ctx: commands.Context):
    print_function(ctx, 'loop_command_def', [])
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
    print_function(ctx, 'loop_this_def', [])
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
    print_function(ctx, 'stop_def', [mute_response])
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
    print_function(ctx, 'pause_def', [mute_response])
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
    print_function(ctx, 'resume_def', [mute_response])
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
    print_function(ctx, 'join_def', [channel_id, mute_response])
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

        print_message(guild_id, "------------------------------- join -------------------------")
        tb = traceback.format_exc()
        print_message(guild_id, tb)
        print_message(guild_id, "--------------------------------------------------------------")
        await ctx.reply(tg(guild_id, "Channel **doesn't exist** or bot doesn't have"
                                             " **sufficient permission** to join"), ephemeral=True)
        return False


async def disconnect_def(ctx: commands.Context,
                         mute_response: bool = False
                         ):
    print_function(ctx, 'disconnect_def', [mute_response])
    guild_id = ctx.guild.id
    if ctx.voice_client:
        await stop_def(ctx, True)
        guild[guild_id].queue.clear()
        await ctx.guild.voice_client.disconnect(force=True)
        if not mute_response:
            await ctx.reply(f"{tg(guild_id, 'Left voice channel:')} `{ctx.guild.voice_client.channel}`", ephemeral=True)
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
    print_function(ctx, 'volume_command_def', [volume, ephemeral, mute_response])
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
    print_function(ctx, 'ping_def', [])
    await ctx.reply(f'**Pong!** Latency: {round(bot.latency * 1000)}ms ------ {ctx.guild.voice_client.is_playing()}')
    save_json()


# noinspection PyTypeHints
async def language_command_def(ctx: commands.Context,
                   country_code: Literal[tuple(languages_dict.keys())]
                   ):
    print_function(ctx, 'language_command_def', [country_code])
    guild_id = ctx.guild.id
    guild[guild_id].options.language = country_code
    await ctx.reply(f'{tg(guild_id, "Changed the language for this server to: ")} `{guild[guild_id].options.language}`')
    save_json()


async def sound_effects_def(ctx: commands.Context,
                ephemeral: bool = True
                ):
    print_function(ctx, 'sound_effects_def', [ephemeral])
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
    print_function(ctx, 'list_radios_def', [ephemeral])
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


# ---------------------------------------- ADMIN --------------------------------------------------


async def announce_command_def(ctx: commands.Context,
                      message
                      ):
    print_function(ctx, 'announce_command_def', [message])
    for guild_object in bot.guilds:
        await guild_object.system_channel.send(message)

    await ctx.reply(f'Announced message to all servers: `{message}`')


async def rape_play_command_def(ctx: commands.Context,
                      effect_number: int = None,
                      channel_id = None,
                      ):
    print_function(ctx, 'rape_play_command_def', [effect_number, channel_id])

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
    print_function(ctx, 'ear_rape_command_def', [])
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
    print_function(ctx, 'kys_def', [])
    guild_id = ctx.guild.id
    await ctx.reply(tg(guild_id, "Committing seppuku..."))
    sys.exit(3)


async def config_command_def(ctx: commands.Context,
                         config_file: discord.Attachment,
                         config_type:  Literal['guilds', 'other', 'radio', 'languages'] = 'guilds',
                         ):
    print_function(ctx, 'config_command_def', [config_file, config_type])

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
        print_message('no guild', 'Loading guilds.json ...')
        with open('src/guilds.json', 'r') as f:
            globals()['guild'] = json_to_guilds(json.load(f))

        await ctx.reply("Loaded new `guilds.json`", ephemeral=True)
    else:
        await ctx.reply(f"Saved new `{config_type}.json`", ephemeral=True)


async def log_command_def(ctx: commands.Context,
                      log_type: Literal['log.txt', 'guilds.json', 'other.json', 'radio.json', 'languages.json', 'activity.log'] = 'log.txt'
                      ):
    print_function(ctx, 'log_command_def', [log_type])
    save_json()
    if log_type == 'other.json':
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
    print_function(ctx, 'change_config_def', [stopped, loop, is_radio, buttons, language, response_type, buffer, volume, server])
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

        config = f'`stopped={guild[guild_id].options.stopped}`, `loop={guild[guild_id].options.loop}`,' \
                 f' `is_radio={guild[guild_id].options.is_radio}`, `buttons={guild[guild_id].options.buttons}`,' \
                 f' `language={guild[guild_id].options.language}`, `response_type={guild[guild_id].options.response_type}`,' \
                 f' `volume={guild[guild_id].options.volume}`, `buffer={guild[guild_id].options.buffer}`'

        save_json()

        await ctx.reply(f'**Config for guild `{guild_id}`**\n {config}', ephemeral=True)


async def probe_command_def(ctx: commands.Context,
                        url = None,
                        ephemeral: bool = False
                        ):
    print_function(ctx, 'probe_command_def', [url, ephemeral])
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

# --------------------------------------------- WEB COMMANDS -----------------------------------------------------------

async def web_remove(web_data, number):
    print_web(web_data, 'web_remove', [number])
    guild_id = web_data.guild_id
    queue_length = len(guild[guild_id].queue)

    if queue_length == 0:
        print_message(guild_id, "web_remove -> No songs in queue")
        return 'No songs in queue'

    if type(number) is not int:
        try:
            number = int(number)
        except ValueError:
            print_message(guild_id, "web_remove -> Number must be an integer")
            return 'Number must be an integer (Internal web error -> contact developer)'

    if queue_length-1 >= number >= 0:
        video = guild[guild_id].queue[number]
        guild[guild_id].queue.pop(number)

        save_json()

        return f"Removed #{number} : {video.title}"

    print_message(guild_id, "web_remove -> Number must be between 0 and {queue_length - 1}")
    return f'Number must be between 0 and {queue_length - 1}'

async def web_move(web_data, org_number, destination_number):
    print_web(web_data, 'web_move', [org_number, destination_number])
    guild_id = web_data.guild_id
    queue_length = len(guild[guild_id].queue)

    if queue_length == 0:
        print_message(guild_id, "web_move -> No songs in queue")
        return 'No songs in queue'

    if type(org_number) is not int:
        try:
            org_number = int(org_number)
        except ValueError:
            print_message(guild_id, "web_move -> Original number must be an integer")
            return 'Original number must be an integer (Internal web error -> contact developer)'

    if type(destination_number) is not int:
        try:
            destination_number = int(destination_number)
        except ValueError:
            print_message(guild_id, "web_move -> Destination number must be an integer")
            return 'Destination number must be an integer (Internal web error -> contact developer)'

    if queue_length-1 >= org_number >= 0:
        if queue_length-1 >= destination_number >= 0:
            video = guild[guild_id].queue.pop(org_number)
            guild[guild_id].queue.insert(destination_number, video)

            save_json()

            return f"Moved #{org_number} to #{destination_number} : {video.title}"

        print_message(guild_id, "web_move -> Destination number must be between 0 and {queue_length - 1}")
        return f'Destination number must be between 0 and {queue_length - 1}'
    print_message(guild_id, "web_move -> Original number must be between 0 and {queue_length - 1}")
    return f'Original number must be between 0 and {queue_length - 1}'

async def web_up(web_data, number):
    print_web(web_data, 'web_up', [number])
    guild_id = web_data.guild_id
    queue_length = len(guild[guild_id].queue)

    if type(number) is not int:
        try:
            number = int(number)
        except ValueError:
            print_message(guild_id, "web_up -> Number must be an integer")
            return 'Number must be an integer (Internal web error -> contact developer)'

    if queue_length == 0:
        print_message(guild_id, "web_up -> No songs in queue")
        return 'No songs in queue'

    if number == 0:
        return await web_move(web_data, 0, queue_length-1)

    return await web_move(web_data, number, number-1)

async def web_down(web_data, number):
    print_web(web_data, 'web_down', [number])
    guild_id = web_data.guild_id
    queue_length = len(guild[guild_id].queue)

    if type(number) is not int:
        try:
            number = int(number)
        except ValueError:
            print_message(guild_id, "web_down -> Number must be an integer")
            return 'Number must be an integer (Internal web error -> contact developer)'

    if queue_length == 0:
        print_message(guild_id, "web_down -> No songs in queue")
        return 'No songs in queue'

    if number == queue_length-1:
        return await web_move(web_data, number, 0)

    return await web_move(web_data, number, number+1)

async def web_top(web_data, number):
    print_web(web_data, 'web_top', [number])
    guild_id = web_data.guild_id
    queue_length = len(guild[guild_id].queue)

    if type(number) is not int:
        try:
            number = int(number)
        except ValueError:
            print_message(guild_id, "web_top -> Number must be an integer")
            return 'Number must be an integer (Internal web error -> contact developer)'

    if queue_length == 0:
        print_message(guild_id, "web_top -> No songs in queue")
        return 'No songs in queue'

    if number == 0:
        print_message(guild_id, "web_top -> Already at the top")
        return 'Already at the top'

    return await web_move(web_data, number, 0)

async def web_bottom(web_data, number):
    print_web(web_data, 'web_bottom', [number])
    guild_id = web_data.guild_id
    queue_length = len(guild[guild_id].queue)

    if type(number) is not int:
        try:
            number = int(number)
        except ValueError:
            print_message(guild_id, "web_bottom -> Number must be an integer")
            return 'Number must be an integer (Internal web error -> contact developer)'

    if queue_length == 0:
        print_message(guild_id, "web_bottom -> No songs in queue")
        return 'No songs in queue'

    if number == queue_length-1:
        print_message(guild_id, "web_bottom -> Already at the bottom")
        return 'Already at the bottom'

    return await web_move(web_data, number, queue_length-1)

async def web_stop(web_data):
    print_web(web_data, 'web_stop', [])
    guild_id = web_data.guild_id
    guild_object = bot.get_guild(int(guild_id))
    voice = guild_object.voice_client

    if voice is None:
        print_message(guild_id, "web_stop -> Not in a voice channel")
        return 'Not in a voice channel'

    if not voice.is_playing():
        print_message(guild_id, "web_stop -> Not playing")
        return 'Not playing'

    if voice.is_playing():
        guild[guild_id].options.stopped = True
        voice.stop()
        save_json()
        print_message(guild_id, "web_stop -> Stopped")
        return 'Stopped playing'

    print_message(guild_id, "web_stop -> Unknown error")
    return 'Unknown error'

async def web_pause(web_data):
    print_web(web_data, 'web_pause', [])
    guild_id = web_data.guild_id
    guild_object = bot.get_guild(int(guild_id))
    voice = guild_object.voice_client

    if voice is None:
        print_message(guild_id, "web_pause -> Not in a voice channel")
        return 'Not in a voice channel'

    if not voice.is_playing():
        print_message(guild_id, "web_pause -> Not playing")
        return 'Not playing'

    if voice.is_playing():
        voice.pause()
        save_json()
        print_message(guild_id, "web_pause -> Paused")
        return 'Stopped playing'

    print_message(guild_id, "web_pause -> Unknown error")
    return 'Unknown error'

async def web_resume(web_data):
    print_web(web_data, 'web_resume', [])
    guild_id = web_data.guild_id
    guild_object = bot.get_guild(int(guild_id))
    voice = guild_object.voice_client

    if voice is None:
        print_message(guild_id, "web_resume -> Not in a voice channel")
        return 'Not in a voice channel'

    if not voice.is_playing():
        if voice.is_paused():
            voice.resume()
            save_json()
            print_message(guild_id, "web_resume -> Resumed")
            return 'Resumed playing'
        print_message(guild_id, "web_resume -> Nothing paused")
        return 'Nothing paused'

    if voice.is_playing():
        save_json()
        print_message(guild_id, "web_resume -> Nothing paused")
        return 'Nothing paused'



    print_message(guild_id, "web_resume -> Unknown error")
    return 'Unknown error'

async def web_skip(web_data):
    print_web(web_data, 'web_skip', [])
    guild_id = web_data.guild_id
    guild_object = bot.get_guild(int(guild_id))
    voice = guild_object.voice_client

    if voice is None:
        print_message(guild_id, "web_skip -> Not in a voice channel")
        return 'Not in a voice channel'

    if not voice.is_playing():
        print_message(guild_id, "web_skip -> Not playing")
        return 'Not playing'

    if voice.is_playing():
        voice.stop()
        save_json()
        print_message(guild_id, "web_skip -> Stopped")
        return 'Stopped playing'

    print_message(guild_id, "web_skip -> Unknown error")
    return 'Unknown error'

async def web_queue_from_video(web_data, url, number: int=None):
    print_web(web_data, 'web_queue', [url, number])
    guild_id = web_data.guild_id
    video = None

    if url == 'last_played':
        video = guild[guild_id].last_played

    if video:
        try:
            if not number:
                guild[guild_id].queue.append(video)
            else:
                guild[guild_id].queue.insert(number, video)
            save_json()
            print_message(guild_id, "web_queue -> Queued")
            return 'Queued'
        except Exception as e:
            print(e)
            print_message(guild_id, "web_queue -> Error while queuing")
            return 'Error while queuing (Internal web error -> contact developer)'
    else:
        print_message(guild_id, "web_queue -> Error while getting video")
        return 'Error while getting video (Internal web error -> contact developer)'

async def web_play(web_data, url):
    print_web(web_data, 'web_play', [url])
    # guild_id = web_data.guild_id
    # guild_object = bot.get_guild(int(guild_id))
    # voice = guild_object.voice_client
    #
    # if video:
    #     try:
    #         video = await YTDLSource.from_url(video, loop=bot.loop, stream=True)
    #     except Exception as e:
    #         print_message(guild_id, "web_queue -> Error while getting video")
    #         return 'Error while getting video (Internal web error -> contact developer)'
    #
    #     guild[guild_id].queue.insert(number, video)
    #     save_json()
    #     print_message(guild_id, "web_queue -> Queued")
    #     return 'Queued'
    #
    # print_message(guild_id, "web_queue -> Unknown error")
    # return 'Unknown error'
    #
    # await guild_object.system_channel.send('cock.log')


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
    print_command(ctx, 'help', [general, player, queue, voice])
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

# --------------------------------------------- WEB SERVER --------------------------------------------- #

app = Flask(__name__)

@app.route('/')
async def index_page():
    return render_template('nav/index.html')

@app.route('/about')
async def about_page():
    return render_template('nav/about.html')

@app.route('/guild')
async def guilds_page():
    return render_template('nav/guild_list.html', guild=guild.values(), len=len)

@app.route('/guild/<guild_id>', methods=['GET', 'POST'])
async def guild_page(guild_id):
    if request.method == 'POST':

        web_data = WebData(int(guild_id), 'author')

        keys = request.form.keys()
        if 'del_btn' in keys:
            await web_remove(web_data, request.form['del_btn'])
        if 'up_btn' in keys:
            await web_up(web_data, request.form['up_btn'])
        if 'down_btn' in keys:
            await web_down(web_data, request.form['down_btn'])
        if 'top_btn' in keys:
            await web_top(web_data, request.form['top_btn'])
        if 'bottom_btn' in keys:
            await web_bottom(web_data, request.form['bottom_btn'])
        if 'stop_btn' in keys:
            await web_stop(web_data)
        if 'pause_btn' in keys:
            await web_pause(web_data)
        if 'resume_btn' in keys:
            await web_resume(web_data)
        if 'skip_btn' in keys:
            await web_skip(web_data)

        if 'queue_btn' in keys:
            await web_queue_from_video(web_data, request.form['queue_btn'])
        if 'nextup_btn' in keys:
            await web_queue_from_video(web_data, request.form['nextup_btn'], 0)

    try:
        guild_object = guild[int(guild_id)]
        return render_template('control/guild.html', guild=guild_object, convert_duration=convert_duration, get_username=get_username)
    except (KeyError, ValueError, TypeError):
        return render_template('error/no_guild.html', guild_id=guild_id)

@app.route('/guild/<guild_id>/add', methods=['GET', 'POST'])
async def guild_add_page(guild_id):
    if request.method == 'POST':
        web_data = WebData(int(guild_id), 'author')
        # await web_add(web_data, request.form['add_url'])
    return render_template('control/action/add.html')

# run

web_thread = threading.Thread(target=app.run)
bot_thread = threading.Thread(target=bot.run, kwargs={'token':api_key})

web_thread.start()
bot_thread.start()

web_thread.join()
bot_thread.join()
