from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify


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


# class GuildData:
#     def __init__(self, guild_id):
#
#         guild_object = bot.get_guild(int(guild_id))
#         if guild_object:
#             self.name = guild_object.name
#             self.id = guild_object.id
#             self.member_count = guild_object.member_count
#             self.owner_id = guild_object.owner_id
#             self.owner_name = guild_object.owner.name
#             self.created_at = guild_object.created_at.strftime("%d/%m/%Y %H:%M:%S")
#             self.description = guild_object.description
#             self.large = guild_object.large
#
#             if guild_object.icon is not None: self.icon = guild_object.icon.url
#             else: self.icon = None
#
#             if guild_object.banner is not None: self.banner = guild_object.banner.url
#             else: self.banner = None
#
#             if guild_object.splash is not None: self.splash = guild_object.splash.url
#             else: self.splash = None
#
#             if guild_object.discovery_splash is not None: self.discovery_splash = guild_object.discovery_splash.url
#             else:self.discovery_splash = None
#
#         else:
#             self.name = None
#             self.id = None
#             self.member_count = None
#             self.owner_id = None
#             self.created_at = None
#             self.description = None
#             self.large = None
#             self.icon = None
#             self.banner = None
#             self.splash = None
#             self.discovery_splash = None
#

# noinspection PyTypeChecker
class Video:
    def __init__(self, url, author, title=None, picture=None, duration=None, channel_name=None, channel_link=None):
        self.url = url
        self.author = author
        self.title = title
        self.picture = picture
        self.duration = duration
        self.channel_name = channel_name
        self.channel_link = channel_link

    def renew(self):
        pass




class Guild:
    def __init__(self, guild_id):
        self.options = Options(guild_id)
        self.queue = []
        self.search_list = []
        self.now_playing = Video(url='https://www.youtube.com/watch?v=dQw4w9WgXcQ',
                                 author=69,
                                 title='Never gonna give you up',
                                 picture='https://img.youtube.com/vi/dQw4w9WgXcQ/default.jpg',
                                 duration='3:33',
                                 channel_name='Rick Astley',
                                 channel_link='https://www.youtube.com/channel/UCuAXFkgsw1L7xaCfnd5JJOw')
        # self.data = GuildData(guild_id)


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

def json_to_video(video_dict):

    video = Video(url=video_dict['url'],
                  author=69,
                  title=video_dict['title'],
                  picture=video_dict['picture'],
                  duration=video_dict['duration'],
                  channel_name=video_dict['channel_name'],
                  channel_link=video_dict['channel_link'])
    return video


def json_to_guild(guild_dict):
    guild_object = Guild(guild_dict['options']['guild_id'])
    # guild_object.options = Options(guild_dict['options']['guild_id'])
    # options_time = time.time() - start_time - guild_time
    guild_object.options.__dict__ = guild_dict['options']
    # guild_object.data.__dict__ = guild_dict['data']
    guild_object.queue = [json_to_video(video_dict) for video_dict in guild_dict['queue'].values()]
    guild_object.search_list = [json_to_video(video_dict) for video_dict in guild_dict['search_list'].values()]
    guild_object.now_playing = json_to_video(guild_dict['now_playing'])

    return guild_object


def json_to_guilds(guilds_dict):
    guilds_object = {}
    for guild_id, guild_dict in guilds_dict.items():
        guilds_object[int(guild_id)] = json_to_guild(guild_dict)

    return guilds_object

import json

with open('src/guilds.json', 'r') as f:
    guilds = json.load(f)
    guild = json_to_guilds(guilds)


# ----------------------------

app = Flask(__name__)

@app.route('/')
async def index_page():
    return render_template('index.html')

@app.route('/about')
async def about_page():
    return render_template('about.html')

@app.route('/guild/<guild_id>')
async def guild_page(guild_id):
    guild_object = guild[int(guild_id)]
    return render_template('guild.html', guild=guild_object, convert_duration=convert_duration)


app.run(debug=True)



