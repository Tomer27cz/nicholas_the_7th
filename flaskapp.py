import socket
import struct
import pickle
import json
import os
from time import gmtime, strftime, time

from io import BytesIO
from pathlib import Path

from flask import Flask, render_template, request, url_for, redirect, session, send_file, abort
from werkzeug.utils import safe_join

import config
from oauth import Oauth

# --------------------------------------------- LOAD DATA --------------------------------------------- #

with open(f'{config.PARENT_DIR}src/radio.json', 'r', encoding='utf-8') as file:
    radio_dict = json.load(file)

with open(f'{config.PARENT_DIR}src/languages.json', 'r', encoding='utf-8') as file:
    languages_dict = json.load(file)
    text = languages_dict['en']

with open(f'{config.PARENT_DIR}src/other.json', 'r', encoding='utf-8') as file:
    other = json.load(file)
    react_dict = other['reactions']
    prefix = other['prefix']
    my_id = other['my_id']
    bot_id = other['bot_id']
    vlc_logo = other['logo']
    authorized_users = other['authorized'] + [my_id, 349164237605568513]

guild = {}

# --------------------------------------------- CLASSES --------------------------------------------- #

class ReturnData:
    """
    Data class for returning data from functions

    :type response: bool
    :type message: str
    :type video: VideoClass

    :param successful: True if successful, False if not
    :param message: Message to be returned
    :param video: VideoClass object to be returned if needed
    """

    def __init__(self, successful: bool, message: str, video=None):
        self.response = successful
        self.message = message
        self.video = video

class WebData:
    """
    Replaces commands.Context when there can be none
    """

    def __init__(self, guild_id, author, author_id):
        self.guild_id = guild_id
        self.author = author
        self.author_id = author_id

    async def reply(self, content=None, **kwargs):
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
        self.buffer = 600  # how many seconds of nothing before it disconnects | 600 = 10min
        self.history_length = 10
        self.update = False

class GuildData:
    """
    Stores and updates the data for each guild
    """

    def __init__(self, guild_id):
        self.name = None
        self.id = guild_id
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
        self.history = []
        self.data = GuildData(guild_id)

    def renew(self):
        self.data = GuildData(self.id)

class VideoClass:
    """
    Stores all the data for each video
    Can do, YouTube, SoundCloud, Czech Radios, Url Probes, Local Files and Fake Spotify

    Raises ValueError: If URL is not provided or is incorrect for class_type
    """

    def __init__(self):
        self.class_type = None
        self.author = None
        self.created_at = None
        self.played_at = None
        self.stopped_at = None
        self.url = None
        self.title = None
        self.picture = None
        self.duration = None
        self.channel_name = None
        self.channel_link = None
        self.radio_name = None
        self.radio_website = None
        self.local_number = None

    def renew(self):
        if self.class_type == 'Radio':
            response = get_renew(self.radio_website, self.url)
            if response is not None:
                self.picture = response[0]
                self.channel_name = response[1]
                self.title = response[2]
                self.duration = response[3]

class DiscordUser:
    def __init__(self):
        self.name = None
        self.id = None
        self.discriminator = None
        self.avatar = None
        self.bot = None
        self.created_at = None
        self.display_name = None
        self.status = None

class DiscordMember:
    def __init__(self):
        self.name = None
        self.id = None
        self.discriminator = None
        self.avatar = None
        self.bot = None
        self.created_at = None
        self.status = None
        self.joined_at = None

class DiscordChannel:
    def __init__(self):
        self.id = None
        self.name = None
        self.created_at = None
        self.members = []

class DiscordRole:
    def __init__(self):
        self.id = None
        self.name = None
        self.created_at = None
        self.color = None
        self.permissions = None
        self.members = []

class DiscordInvite:
    def __init__(self):
            self.id = None
            self.url = None
            self.code = None
            self.inviter = None
            self.created_at = None
            self.expires_at = None
            self.temporary = None
            self.approximate_member_count = None
            self.approximate_presence_count = None
            self.max_age = None
            self.max_uses = None
            self.uses = None
            self.revoked = None

# --------------------------------------------- SOCKET --------------------------------------------- #

HOST = '127.0.0.1'  # The server's hostname or IP address
PORT = 5421  # The port used by the server

# --------------------------------------------- OTHER FUNCTIONS --------------------------------------------- #

class CustomUnpickler(pickle.Unpickler):
    def find_class(self, module, name):
        if name == 'ReturnData':
            return ReturnData
        if name == 'WebData':
            return WebData
        if name == 'Options':
            return Options
        if name == 'GuildData':
            return GuildData
        if name == 'Guild':
            return Guild
        if name == 'VideoClass':
            return VideoClass
        return super().find_class(module, name)

def unpickle(data):
    return CustomUnpickler(BytesIO(data)).load()

def struct_to_time(struct_time, first='date') -> str:
    """
    Converts struct_time to time string
    :param struct_time: int == struct_time
    :param first: ('date', 'time') == (01/01/1970 00:00:00, 00:00:00 01/01/1970)
    :return: str
    """
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

def convert_duration(duration) -> str or None:
    """
    Converts duration(in sec) to HH:MM:SS format
    or returns 'Stream' if duration is None or 0
    if can't convert returns duration as str
    :param duration: duration in sec
    :return: str - duration in HH:MM:SS format
    """
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
        return str(duration)

def tg(guild_id: int, content: str) -> str:
    """
    Translates text to guild language
    Selects language from guild options
    Gets text from languages.json
    :param guild_id: int - id of guild
    :param content: str - translation key
    :return: str - translated text
    """
    global guild
    # lang = guild[guild_id].options.language
    lang = 'en'
    try:
        to_return = languages_dict[lang][content]
    except KeyError:
        to_return = content
    return to_return

# --------------------------------------------- FILE FUNCTIONS --------------------------------------------- #

def getReadableByteSize(num, suffix='B') -> str:
    for unit in ['', 'K', 'M', 'G', 'T', 'P', 'E', 'Z']:
        if abs(num) < 1024.0:
            return "%3.1f%s%s" % (num, unit, suffix)
        num /= 1024.0
    return "%.1f%s%s" % (num, 'Y', suffix)

def getIconClassForFilename(fName):
    fileExt = Path(fName).suffix
    fileExt = fileExt[1:] if fileExt.startswith(".") else fileExt
    fileTypes = ["aac", "ai", "bmp", "cs", "css", "csv", "doc", "docx", "exe", "gif", "heic", "html", "java", "jpg",
                 "js", "json", "jsx", "key", "m4p", "md", "mdx", "mov", "mp3",
                 "mp4", "otf", "pdf", "php", "png", "pptx", "psd", "py", "raw", "rb", "sass", "scss", "sh", "sql",
                 "svg", "tiff", "tsx", "ttf", "txt", "wav", "woff", "xlsx", "xml", "yml"]
    fileIconClass = f"bi bi-filetype-{fileExt}" if fileExt in fileTypes else "bi bi-file-earmark"
    return fileIconClass

# --------------------------------------------- LOG --------------------------------------------- #

def log(ctx, text_data, options=None, log_type='text', author=None) -> None:
    """
    Logs data to the console and to the log file
    :param ctx: commands.Context or WebData or guild_id
    :param text_data: The data to be logged
    :param options: list - options to be logged from command
    :param log_type: ('command', 'function', 'web', 'text', 'ip') - type of log
    :param author: Author of the command
    :return: None
    """

    now_time_str = struct_to_time(time())

    if type(ctx) == WebData:
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

    with open(f'{config.PARENT_DIR}log/log.log', "a", encoding="utf-8") as f:
        f.write(message + "\n")

def collect_data(data) -> None:
    """
    Collects data to the data.log file
    :param data: data to be collected
    :return: None
    """
    now_time_str = struct_to_time(time())
    message = f"{now_time_str} | {data}\n"

    with open(f'{config.PARENT_DIR}log/data.log', "a", encoding="utf-8") as f:
        f.write(message)

    return None

# --------------------------------------------- WEB FUNCTIONS --------------------------------------------- #

def send_msg(sock, msg: bytes):
    """
    Send a message to the socket prefixed with the length
    :param sock: socket to send to
    :param msg: message

    :type msg: bytes
    """
    # Prefix each message with a 4-byte length (network byte order)
    msg = struct.pack('>I', len(msg)) + msg
    sock.sendall(msg)

def send_arg(arg_dict: dict, get_response: bool = True):
    """
    Send an argument dictionary to the socket and return the response
    :param arg_dict: dictionary to send
    :param get_response: whether to wait for a response
    :return: response dictionary or None
    """
    # Create socket
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((HOST, PORT))

    # serialize and send
    msg = pickle.dumps(arg_dict)
    send_msg(s, msg)

    if get_response:
        response = recv_msg(s)

        if response is None:
            return None

        return unpickle(response)

def recv_msg(sock) -> bytes or None:
    """
    Receive a message prefixed with the message length
    :param sock: socket
    :return: bytes
    """
    raw_msg_len = recv_all(sock, 4)

    if not raw_msg_len:
        return None
    msg_len = struct.unpack('>I', raw_msg_len)[0]

    return recv_all(sock, msg_len)

def recv_all(sock, n) -> bytes or None:
    """
    Recieve all
    :param sock: socket
    :param n: length to read
    :return: bytes or None
    """
    # Helper function to recv n bytes or return None if EOF is hit
    data = bytearray()
    while len(data) < n:
        packet = sock.recv(int(n - len(data)))
        if not packet:
            return None
        data.extend(packet)
    return data

# Socket connection

def execute_function(function_name: str, web_data: WebData, **kwargs) -> ReturnData:
    # create argument dictionary
    arg_dict = {
        'type': 'function',
        'function_name': function_name,
        'web_data': web_data,
        'args': kwargs
    }
    response = send_arg(arg_dict)

    if response is None:
        return ReturnData(False, 'An unexpected error occurred')

    return response

# admin

def check_admin(session_data):
    global guild
    if session_data is None:
        raise ValueError('Session data is None')

    user_id = int(session_data['discord_user']['id'])
    if user_id in authorized_users:
        if guild is None:
            guild = get_guilds()
        return list(guild.keys())

    return session_data['mutual_guild_ids']

# --------------------------------------------- DATABASE FUNCTIONS --------------------------------------------- #

def get_guild(guild_id: int):
    """
    Get a guild from the database
    :param guild_id: guild id
    :return: guild object
    """
    # create argument dictionary
    arg_dict = {
        'type': 'get_data',
        'data_type': 'guild',
        'guild_id': guild_id
    }
    # send argument dictionary
    return send_arg(arg_dict)

def get_guilds():
    """
    Get the guilds list from database
    :return: list - list of guild objects
    """
    global guild
    arg_dict = {
        'type': 'get_data',
        'data_type': 'guilds'
    }
    # send argument dictionary
    guild = send_arg(arg_dict)
    return guild

def get_bot_guilds():
    """
    Get the guilds list from bot instance
    :return: list - list of guild objects
    """
    arg_dict = {
        'type': 'get_data',
        'data_type': 'bot_guilds'
    }
    # send argument dictionary
    bot_guilds = send_arg(arg_dict)
    return bot_guilds

# guild specific data

def get_guild_channels(guild_id: int):
    """
    Get the guild channels list from database
    :param guild_id: guild id
    :return: list - list of channel objects
    """
    # create argument dictionary
    arg_dict = {
        'type': 'get_data',
        'data_type': 'guild_channels',
        'guild_id': guild_id
    }
    # send argument dictionary
    return send_arg(arg_dict)

def get_guild_text_channels(guild_id: int):
    """
    Get the guild text channels list from database
    :param guild_id: guild id
    :return: list - list of channel objects
    """
    # create argument dictionary
    arg_dict = {
        'type': 'get_data',
        'data_type': 'guild_text_channels',
        'guild_id': guild_id
    }
    # send argument dictionary
    return send_arg(arg_dict)

def get_guild_members(guild_id: int):
    """
    Get the members of a guild
    :param guild_id: guild id
    :return: list - list of members
    """
    # create argument dictionary
    arg_dict = {
        'type': 'get_data',
        'data_type': 'guild_members',
        'guild_id': guild_id
    }
    # send argument dictionary
    return send_arg(arg_dict)

def get_guild_roles(guild_id: int):
    """
    Get the roles of a guild
    :param guild_id: guild id
    :return: list - list of roles
    """
    # create argument dictionary
    arg_dict = {
        'type': 'get_data',
        'data_type': 'guild_roles',
        'guild_id': guild_id
    }
    # send argument dictionary
    return send_arg(arg_dict)

def get_guild_invites(guild_id: int):
    """
    Get the invites of a guild
    :param guild_id: guild id
    :return: list - list of invites
    """
    # create argument dictionary
    arg_dict = {
        'type': 'get_data',
        'data_type': 'guild_invites',
        'guild_id': guild_id
    }
    # send argument dictionary
    return send_arg(arg_dict)

def get_update(guild_id: int):
    """
    Get update variable state from the database
    :param guild_id: guild id
    :return: bool - update variable state
    """
    # create argument dictionary
    arg_dict = {
        'type': 'get_data',
        'data_type': 'update',
        'guild_id': guild_id
    }
    # send argument dictionary
    return send_arg(arg_dict)

def get_language(guild_id: int):
    """
    Get language from the database
    :param guild_id: guild id
    :return: language
    """
    # create argument dictionary
    arg_dict = {
        'type': 'get_data',
        'data_type': 'language',
        'guild_id': guild_id
    }
    # send argument dictionary
    return send_arg(arg_dict)

# user specific data

def get_username(user_id: int):
    """
    Get a user from the database
    :param user_id: user id
    :return: user object
    """
    # create argument dictionary
    arg_dict = {
        'type': 'get_data',
        'data_type': 'user_name',
        'user_id': user_id
    }
    # send argument dictionary
    return send_arg(arg_dict)

def get_user_data(user_id: int):
    """
    Get a user from the database
    :param user_id: user id
    :return: user object
    """
    # create argument dictionary
    arg_dict = {
        'type': 'get_data',
        'data_type': 'user_data',
        'user_id': user_id
    }
    # send argument dictionary
    return send_arg(arg_dict)

def get_renew(radio_website, url):
    """
    Get a renew from the database
    :param radio_website: radio website
    :param url: url
    :return: renew object
    """
    # create argument dictionary
    arg_dict = {
        'type': 'get_data',
        'data_type': 'renew',
        'radio_website': radio_website,
        'url': url
    }
    # send argument dictionary
    return send_arg(arg_dict)

# Set Data

def set_update(guild_id: int, update: bool):
    """
    Set update variable state in the database
    :param guild_id: guild id
    :param update: update variable state
    :return: None
    """
    # create argument dictionary
    arg_dict = {
        'type': 'set_data',
        'data_type': 'update',
        'guild_id': guild_id,
        'update': update
    }
    # send argument dictionary
    return send_arg(arg_dict, get_response=False)

# --------------------------------------------- WEB SERVER --------------------------------------------- #

app = Flask(__name__)
app.config['SECRET_KEY'] = config.WEB_SECRET_KEY

@app.route('/')
async def index_page():
    log(request.remote_addr, '/index', log_type='ip')
    if 'discord_user' in session.keys():
        user = session['discord_user']
    else:
        user = None

    return render_template('nav/index.html', user=user)

@app.route('/about')
async def about_page():
    log(request.remote_addr, '/about', log_type='ip')
    if 'discord_user' in session.keys():
        user = session['discord_user']
    else:
        user = None

    return render_template('nav/about.html', user=user)

# Guild pages
@app.route('/guild')
async def guilds_page():
    global guild
    log(request.remote_addr, '/guild', log_type='ip')
    if 'discord_user' in session.keys():
        user = session['discord_user']
        mutual_guild_ids = check_admin(session)
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

    guild = get_guilds()

    return render_template('nav/guild_list.html', guild=sort_list(guild.items(), mutual_guild_ids).values(), len=len,
                           user=user, errors=None, mutual_guild_ids=mutual_guild_ids)

@app.route('/guild/<int:guild_id>', methods=['GET', 'POST'])
async def guild_get_key_page(guild_id):
    global guild
    log(request.remote_addr, f'/guild/{guild_id}', log_type='ip')
    if 'discord_user' in session.keys():
        user = session['discord_user']
        mutual_guild_ids = check_admin(session)
    elif 'mutual_guild_ids' in session.keys():
        mutual_guild_ids = session['mutual_guild_ids']
        user = None
        if mutual_guild_ids is None:
            mutual_guild_ids = []
            session['mutual_guild_ids'] = []
    else:
        user = None
        mutual_guild_ids = []

    guild_object = get_guild(int(guild_id))

    if guild_object is None:
        return render_template('base/message.html', guild_id=guild_id, user=user,
                               message="That Server doesn't exist or the bot is not in it", errors=None, title='Error')

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

        return render_template('control/action/get_key.html', guild_id=guild_id,
                               errors=[f'Invalid code: {request.form["key"]} -> do /key in the server'],
                               url=Oauth.discord_login_url, user=user)

    return render_template('control/action/get_key.html', guild_id=guild_id, errors=None, url=Oauth.discord_login_url,
                           user=user)

@app.route('/guild/<int:guild_id>&key=<key>', methods=['GET', 'POST'])
async def guild_page(guild_id, key):
    global guild
    log(request.remote_addr, f'/guild/{guild_id}&key={key}', log_type='ip')
    errors = []
    messages = []
    scroll_position = 0
    admin = False

    if 'discord_user' in session.keys():
        user = session['discord_user']
        user_name, user_id = user['username'], int(user['id'])
        mutual_guild_ids = check_admin(session)
        if user_id in authorized_users:
            admin = True
    elif 'mutual_guild_ids' in session.keys():
        mutual_guild_ids = session['mutual_guild_ids']
        user = None
        user_name, user_id = request.remote_addr, 'WEB Guest'
        admin = False
    else:
        mutual_guild_ids = []
        user = None
        user_name, user_id = request.remote_addr, 'WEB Guest'
        admin = False

    if request.method == 'POST':
        web_data = WebData(int(guild_id), user_name, user_id)
        response = None

        keys = request.form.keys()
        if 'del_btn' in keys:
            log(web_data, 'remove', [request.form['del_btn']], log_type='web', author=web_data.author)
            response = execute_function('remove_def', web_data=web_data, number=int(request.form['del_btn']),
                                        list_type='queue')
        if 'up_btn' in keys:
            log(web_data, 'up', [request.form['up_btn']], log_type='web', author=web_data.author)
            response = execute_function('web_up', web_data=web_data, number=request.form['up_btn'])
        if 'down_btn' in keys:
            log(web_data, 'down', [request.form['down_btn']], log_type='web', author=web_data.author)
            response = execute_function('web_down', web_data=web_data, number=request.form['down_btn'])
        if 'top_btn' in keys:
            log(web_data, 'top', [request.form['top_btn']], log_type='web', author=web_data.author)
            response = execute_function('web_top', web_data=web_data, number=request.form['top_btn'])
        if 'bottom_btn' in keys:
            log(web_data, 'bottom', [request.form['bottom_btn']], log_type='web', author=web_data.author)
            response = execute_function('web_bottom', web_data=web_data, number=request.form['bottom_btn'])

        if 'play_btn' in keys:
            log(web_data, 'play', [], log_type='web', author=web_data.author)
            response = execute_function('play_def', web_data=web_data)
        if 'stop_btn' in keys:
            log(web_data, 'stop', [], log_type='web', author=web_data.author)
            response = execute_function('stop_def', web_data=web_data)
        if 'pause_btn' in keys:
            log(web_data, 'pause', [], log_type='web', author=web_data.author)
            response = execute_function('pause_def', web_data=web_data)
        if 'skip_btn' in keys:
            log(web_data, 'skip', [], log_type='web', author=web_data.author)
            response = execute_function('skip_def', web_data=web_data)

        if 'loop_btn' in keys:
            log(web_data, 'loop', [], log_type='web', author=web_data.author)
            response = execute_function('loop_command_def', web_data=web_data)
        if 'shuffle_btn' in keys:
            log(web_data, 'shuffle', [], log_type='web', author=web_data.author)
            response = execute_function('shuffle_def', web_data=web_data)
        if 'clear_btn' in keys:
            log(web_data, 'clear', [], log_type='web', author=web_data.author)
            response = execute_function('clear_def', web_data=web_data)

        if 'disconnect_btn' in keys:
            log(web_data, 'disconnect', [], log_type='web', author=web_data.author)
            response = execute_function('web_disconnect', web_data=web_data)
        if 'join_btn' in keys:
            log(web_data, 'join', [], log_type='web', author=web_data.author)
            response = execute_function('web_join', web_data=web_data, form=request.form)

        if 'queue_btn' in keys:
            log(web_data, 'queue', [request.form['queue_btn']], log_type='web', author=web_data.author)
            response = execute_function('web_queue', web_data=web_data, video_type=request.form['queue_btn'],
                                        position=None)
        if 'nextup_btn' in keys:
            log(web_data, 'nextup', [request.form['nextup_btn'], 0], log_type='web', author=web_data.author)
            response = execute_function('web_queue', web_data=web_data, video_type=request.form['nextup_btn'],
                                        position=0)
        if 'hdel_btn' in keys:
            log(web_data, 'history remove', [request.form['hdel_btn']], log_type='web', author=web_data.author)
            response = execute_function('remove_def', web_data=web_data, number=int(request.form['hdel_btn'][1:]),
                                        list_type='history')

        if 'edit_btn' in keys:
            log(web_data, 'web_video_edit', [request.form['edit_btn']], log_type='web', author=web_data.author)
            response = execute_function('web_video_edit', web_data=web_data, form=request.form)
        if 'options_btn' in keys:
            log(web_data, 'web_options', [request.form], log_type='web', author=web_data.author)
            response = execute_function('web_user_options_edit', web_data=web_data, form=request.form)

        if 'volume_btn' in keys:
            log(web_data, 'volume_command_def', [request.form['volumeRange'], request.form['volumeInput']],
                log_type='web', author=web_data.author)
            response = execute_function('volume_command_def', web_data=web_data, volume=request.form['volumeRange'])

        if 'ytURL' in keys:
            log(web_data, 'queue_command_def', [request.form['ytURL']], log_type='web', author=web_data.author)
            response = execute_function('queue_command_def', web_data=web_data, url=request.form['ytURL'])
        if 'radio-checkbox' in keys:
            log(web_data, 'web_queue_from_radio', [request.form['radio-checkbox']], log_type='web',
                author=web_data.author)
            response = execute_function('web_queue_from_radio', web_data=web_data,
                                        radio_name=request.form['radio-checkbox'])

        if 'scroll' in keys:
            scroll_position = int(request.form['scroll'])

        if response:
            if not response.response:
                errors = [response.message]
            else:
                messages = [response.message]

    guild_object = get_guild(int(guild_id))

    if guild_object is None:
        return render_template('base/message.html', guild_id=guild_id, user=user,
                               message="That Server doesn't exist or the bot is not in it", errors=None, title='Error')

    if key != guild_object.data.key:
        if guild_object.id in mutual_guild_ids:
            return redirect(f'/guild/{guild_id}&key={guild_object.data.key}')
        return redirect(url_for('guild_get_key_page', guild_id=guild_id))

    mutual_guild_ids.append(guild_object.id)
    session['mutual_guild_ids'] = mutual_guild_ids

    return render_template('control/guild.html', guild=guild_object, struct_to_time=struct_to_time,
                           convert_duration=convert_duration, get_username=get_username, errors=errors,
                           messages=messages, user=user, admin=admin, volume=round(guild_object.options.volume * 100),
                           radios=list(radio_dict.values()), scroll_position=scroll_position,
                           languages_dict=languages_dict, tg=tg, gi=int(guild_id))

@app.route('/guild/<int:guild_id>/update')
async def update_page(guild_id):
    try:
        guild_id = int(guild_id)
    except (ValueError, TypeError):
        print('invalid url')
        return 'False'

    update = get_update(guild_id)

    if update is True:
        set_update(guild_id, False)
        return 'True'
    return 'False'

# User Login
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

        return render_template('base/message.html',
                               message=f"Updated session for {user['username']}#{user['discriminator']}", errors=None,
                               user=user, title='Update Success')

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
    mutual_guilds = [x for x in guilds if x['id'] in map(lambda i: i['id'], bot_guilds)]

    mutual_guild_ids = [int(guild_object['id']) for guild_object in mutual_guilds]
    if int(user['id']) in authorized_users:
        mutual_guild_ids = [int(guild_object['id']) for guild_object in bot_guilds]
        admin = True
    session['mutual_guild_ids'] = mutual_guild_ids

    return render_template('base/message.html',
                           message=f"Success, logged in as {user['username']}#{user['discriminator']}{' -> ADMIN' if admin else ''}",
                           errors=None, user=user, title='Login Success')

@app.route('/logout')
async def logout_page():
    log(request.remote_addr, '/logout', log_type='ip')
    if 'discord_user' in session.keys():
        user = session['discord_user']
        username = user['username']
        discriminator = user['discriminator']
        session.clear()
        return render_template('base/message.html', message=f"Logged out as {username}#{discriminator}", errors=None,
                               user=None, title='Logout Success')
    return redirect(url_for('index_page'))

# Session
@app.route('/reset')
async def reset_page():
    log(request.remote_addr, '/reset', log_type='ip')
    session.clear()
    return redirect(url_for('index_page'))

# Invite
@app.route('/invite')
async def invite_page():
    log(request.remote_addr, '/invite', log_type='ip')
    return redirect(config.INVITE_URL)

# Admin
@app.route('/admin', methods=['GET', 'POST'])
async def admin_page():
    global guild
    log(request.remote_addr, '/admin', log_type='ip')
    if 'discord_user' in session.keys():
        user = session['discord_user']
        user_name = user['username']
        user_id = user['id']
    else:
        return render_template('base/message.html', message="403 Forbidden", message4='You have to be logged in.',
                               errors=None, user=None, title='403 Forbidden'), 403

    if int(user['id']) not in authorized_users:
        return abort(403)

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
                    if file_name in ['log.log', 'data.log', 'activity.log', 'apache_error.log', 'apache_activity.log']:
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
                    errors = ['File name does not match the one in the input field']
                else:
                    try:
                        if file_name in ['log.log', 'data.log', 'activity.log', 'apache_error.log',
                                         'apache_activity.log']:
                            f.save(f"log/{f.filename}")
                            messages = ['File uploaded']
                        else:
                            f.save(f"src/{f.filename}")
                            messages = ['File uploaded']
                    except Exception as e:
                        return str(e)
            if 'edit_btn' in keys:
                log(web_data, 'edit options', [form], log_type='web', author=web_data.author)
                response = execute_function('web_options_edit', web_data, form=form)
        except Exception as e:
            errors = [str(e)]
            log(web_data, 'error', [str(e)], log_type='web', author=web_data.author)

        if response:
            if response.response:
                messages = [response.message]
            else:
                errors = [response.message]

    guild = get_guilds()
    return render_template('nav/admin.html', user=user, guild=guild.values(), languages_dict=languages_dict,
                           errors=errors, messages=messages)

# Admin data
@app.route('/admin/user/<int:user_id>', methods=['GET', 'POST'])
async def admin_user_page(user_id):
    log(request.remote_addr, f'/admin/user/{user_id}', log_type='ip')
    if 'discord_user' in session.keys():
        user = session['discord_user']
    else:
        return render_template('base/message.html', message="403 Forbidden", message4='You have to be logged in.',
                               errors=None, user=None, title='403 Forbidden'), 403

    if int(user['id']) not in authorized_users:
        return abort(403)

    data = get_user_data(user_id)

    return render_template('admin/data/user.html', user=user, data=data, title='User Info')

# Admin file
@app.route('/admin/file/', defaults={'reqPath': ''})
@app.route('/admin/file/<path:reqPath>')
def getFiles(reqPath):
    log(request.remote_addr, f'/admin/file/{reqPath}', log_type='ip')
    if 'discord_user' in session.keys():
        user = session['discord_user']
    else:
        return render_template('base/message.html', message="403 Forbidden", message4='You have to be logged in.',
                               errors=None, user=None, title='403 Forbidden'), 403

    if int(user['id']) not in authorized_users:
        return abort(403)

    # Joining the base and the requested path
    absPath = safe_join(config.PARENT_DIR, reqPath)

    # Return 404 if path doesn't exist
    if not os.path.exists(absPath):
        return abort(404)

    # Check if path is a file and serve
    if os.path.isfile(absPath):
        return send_file(absPath)

    # Show directory contents
    def fObjFromScan(x):
        fileStat = x.stat()
        # return file information for rendering
        return {'name': x.name,
                'fIcon': "bi bi-folder-fill" if os.path.isdir(x.path) else getIconClassForFilename(x.name),
                'relPath': os.path.relpath(x.path, config.PARENT_DIR).replace("\\", "/"),
                'mTime': struct_to_time(fileStat.st_mtime),
                'size': getReadableByteSize(fileStat.st_size)}

    fileObjs = [fObjFromScan(x) for x in os.scandir(absPath)]

    # get parent directory url
    parentFolderPath = os.path.relpath(Path(absPath).parents[0], config.PARENT_DIR).replace("\\", "/")
    if parentFolderPath == '..':
        parentFolderPath = '.'

    return render_template('admin/files.html', data={'files': fileObjs, 'parentFolder': parentFolderPath}, title='Files', user=user)

# def getFiles(reqPath):
#     log(request.remote_addr, f'/admin/file/{reqPath}', log_type='ip')
#     if 'discord_user' in session.keys():
#         user = session['discord_user']
#     else:
#         return render_template('base/message.html', message="403 Forbidden", message4='You have to be logged in.',
#                                errors=None, user=None, title='403 Forbidden'), 403
#
#     if int(user['id']) not in authorized_users:
#         return abort(403)
#
#     # Return 404 if path doesn't exist
#     if not os.path.exists(reqPath):
#         return abort(404)
#
#     # Check if path is a file and serve
#     if os.path.isfile(reqPath):
#         return send_file(reqPath)
#
#     # Show directory contents
#     def fObjFromScan(x):
#         fileStat = x.stat()
#         # return file information for rendering
#         return {'name': x.name,
#                 'fIcon': "bi bi-folder-fill" if os.path.isdir(x.path) else getIconClassForFilename(x.name),
#                 'relPath': x.path,
#                 'mTime': struct_to_time(fileStat.st_mtime),
#                 'size': getReadableByteSize(fileStat.st_size)
#                 }
#
#     fileObjs = [fObjFromScan(x) for x in os.scandir(reqPath)]
#     # get parent directory url
#
#     try:
#         parentFolderPath = Path(reqPath).parents[0]
#     except IndexError:
#         parentFolderPath = reqPath
#
#     return render_template('admin/files.html', data={'files': fileObjs, 'parentFolder': parentFolderPath},
#                            title='Admin File', user=user, errors=None, messages=None)

# Admin guild
@app.route('/admin/guild', methods=['GET', 'POST'])
async def admin_guild_redirect():
    log(request.remote_addr, '/admin/guild', log_type='ip')
    return redirect('/admin')

@app.route('/admin/guild/<int:guild_id>', methods=['GET', 'POST'])
async def admin_guild(guild_id):
    global guild
    log(request.remote_addr, f'/admin/guild/{guild_id}', log_type='ip')
    if 'discord_user' in session.keys():
        user = session['discord_user']
        user_name = user['username']
        user_id = user['id']
    else:
        return render_template('base/message.html', message="403 Forbidden", message4='You have to be logged in.',
                               errors=None, user=None, title='403 Forbidden'), 403

    if int(user['id']) not in authorized_users:
        return abort(403)

    errors = []
    messages = []
    response = None

    if request.method == 'POST':
        web_data = WebData(guild_id, user_name, user_id)

        keys = request.form.keys()
        form = request.form
        try:
            if 'edit_btn' in keys:
                log(web_data, 'web_options_edit', [form], log_type='web', author=web_data.author)
                response = execute_function('web_options_edit', web_data, form=form)
            if 'delete_guild_btn' in keys:
                log(web_data, 'web_delete_guild', [guild_id], log_type='web', author=web_data.author)
                response = execute_function('web_delete_guild', web_data, guild_id=guild_id)
            if 'disconnect_guild_btn' in keys:
                log(web_data, 'web_disconnect_guild', [guild_id], log_type='web', author=web_data.author)
                response = execute_function('web_disconnect_guild', web_data, guild_id=guild_id)
            if 'invite_btn' in keys:
                log(web_data, 'web_create_invite', [guild_id], log_type='web', author=web_data.author)
                response = execute_function('web_create_invite', web_data, guild_id=guild_id)
        except Exception as e:
            errors = [str(e)]
            log(web_data, 'error', [str(e)], log_type='web', author=web_data.author)

        if response:
            if response.response:
                messages = [response.message]
            else:
                errors = [response.message]

    guild_object = get_guild(int(guild_id))
    if guild_object is None:
        return abort(404)
    return render_template('admin/guild.html', user=user, guild_object=guild_object, languages_dict=languages_dict,
                           errors=errors, messages=messages, title='Admin Guild Dashboard')

# Admin guild data
@app.route('/admin/guild/<int:guild_id>/users', methods=['GET', 'POST'])
async def admin_guild_users(guild_id):
    log(request.remote_addr, f'/admin/guild/{guild_id}/users', log_type='ip')
    if 'discord_user' in session.keys():
        user = session['discord_user']
    else:
        return render_template('base/message.html', message="403 Forbidden", message4='You have to be logged in.',
                               errors=None, user=None, title='403 Forbidden'), 403

    if int(user['id']) not in authorized_users:
        return abort(403)

    guild_object = get_guild(int(guild_id))
    if guild_object is None:
        return abort(404)
    guild_members = get_guild_members(int(guild_id))
    return render_template('admin/data/guild_users.html', user=user, guild_object=guild_object, users=guild_members, title='Users')

@app.route('/admin/guild/<int:guild_id>/channels', methods=['GET', 'POST'])
async def admin_guild_channels(guild_id):
    log(request.remote_addr, f'/admin/guild/{guild_id}/channels', log_type='ip')
    if 'discord_user' in session.keys():
        user = session['discord_user']
    else:
        return render_template('base/message.html', message="403 Forbidden", message4='You have to be logged in.',
                               errors=None, user=None, title='403 Forbidden'), 403

    if int(user['id']) not in authorized_users:
        return abort(403)

    guild_object = get_guild(int(guild_id))
    guild_channels = get_guild_channels(int(guild_id))
    return render_template('admin/data/guild_channels.html', user=user, channels=guild_channels, len=len,
                           guild_object=guild_object, title='Voice Channels')

@app.route('/admin/guild/<int:guild_id>/textChannels', methods=['GET', 'POST'])
async def admin_guild_text_channels(guild_id):
    log(request.remote_addr, f'/admin/guild/{guild_id}/textChannels', log_type='ip')
    if 'discord_user' in session.keys():
        user = session['discord_user']
    else:
        return render_template('base/message.html', message="403 Forbidden", message4='You have to be logged in.',
                               errors=None, user=None, title='403 Forbidden'), 403

    if int(user['id']) not in authorized_users:
        return abort(403)

    guild_object = get_guild(int(guild_id))
    guild_text_channels = get_guild_text_channels(int(guild_id))
    return render_template('admin/data/guild_channels.html', user=user, channels=guild_text_channels, len=len,
                           guild_object=guild_object, title='Text Channels')

@app.route('/admin/guild/<int:guild_id>/roles', methods=['GET', 'POST'])
async def admin_guild_roles(guild_id):
    log(request.remote_addr, f'/admin/guild/{guild_id}/roles', log_type='ip')
    if 'discord_user' in session.keys():
        user = session['discord_user']
    else:
        return render_template('base/message.html', message="403 Forbidden", message4='You have to be logged in.',
                               errors=None, user=None, title='403 Forbidden'), 403

    if int(user['id']) not in authorized_users:
        return abort(403)

    guild_object = get_guild(int(guild_id))
    guild_roles = get_guild_roles(int(guild_id))
    return render_template('admin/data/guild_roles.html', user=user, roles=guild_roles, len=len, vars=vars, dict=dict,
                           guild_object=guild_object, title='Roles')

@app.route('/admin/guild/<int:guild_id>/invites', methods=['GET', 'POST'])
async def admin_guild_invites(guild_id):
    log(request.remote_addr, f'/admin/guild/{guild_id}/invites', log_type='ip')
    if 'discord_user' in session.keys():
        user = session['discord_user']
    else:
        return render_template('base/message.html', message="403 Forbidden", message4='You have to be logged in.',
                               errors=None, user=None, title='403 Forbidden'), 403

    if int(user['id']) not in authorized_users:
        return abort(403)

    guild_object = get_guild(int(guild_id))
    guild_invites = get_guild_invites(int(guild_id))
    return render_template('admin/data/guild_invites.html', user=user, invites=guild_invites,
                           guild_object=guild_object, title='Invites', type=type, DiscordUser=DiscordUser)


# Error Handling
@app.errorhandler(404)
async def page_not_found(_):
    log(request.remote_addr, f'{request.path} -> 404', log_type='ip')
    if 'discord_user' in session.keys():
        user = session['discord_user']
    else:
        user = None
    return render_template('base/message.html', message="404 Not Found",
                           message4='The requested URL was not found on the server. If you entered the URL manually please check your spelling and try again.',
                           errors=None, user=user, title='404 Not Found'), 404

@app.errorhandler(403)
async def page_forbidden(_):
    log(request.remote_addr, f'{request.path} -> 403', log_type='ip')
    if 'discord_user' in session.keys():
        user = session['discord_user']
    else:
        user = None
    return render_template('base/message.html', message="403 Forbidden", message4='You do not have permission.',
                           user=user, errors=None, title='403 Forbidden'), 403

def main():
    # get_guilds()
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 5420)))

if __name__ == '__main__':
    main()
