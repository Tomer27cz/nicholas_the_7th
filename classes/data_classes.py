from classes.typed_dictionaries import LastUpdated, VideoAuthor

from database.main import *

from utils.global_vars import GlobalVars
from utils.voice_log import VoiceLog

from time import time
from typing import List
import random
import json

class Guild(Base):
    """
    Data class for storing data about guilds
    :param glob: GlobalVars object
    :param guild_id: ID of the guild
    :param json_data: Data from json file
    """
    __tablename__ = 'guilds'

    id = Column(Integer, primary_key=True)
    options = relationship('Options', uselist=False, backref='guilds', lazy=True)
    saves = relationship('Save', backref='guilds', order_by='Save.position', collection_class=ordering_list('position'), lazy=True)
    queue = relationship('Queue', backref='guilds', order_by='Queue.position', collection_class=ordering_list('position'), lazy=True)
    now_playing = relationship('NowPlaying', uselist=False, backref='guilds', lazy=True)
    history = relationship('History', backref='guilds', order_by='History.position', collection_class=ordering_list('position'), lazy=True)
    data = relationship('GuildData', uselist=False, backref='guilds', lazy=True)
    slowed_users = relationship('SlowedUser', backref='guilds', lazy=True)
    connected = Column(Boolean, default=True)
    last_updated = Column(JSON, default={key: int(time()) for key in LastUpdated.__annotations__.keys()})
    keep_alive = Column(Boolean, default=False)

    def __init__(self, glob: GlobalVars or None, guild_id, json_data: dict, last_updated: LastUpdated = None, **kw: any):
        super().__init__(**kw)
        self.id = guild_id
        self.last_updated = last_updated if last_updated else {key: int(time()) for key in LastUpdated.__annotations__.keys()}

        glob.ses.add(Options(self.id, json_data=json_data.get('options', {})))
        glob.ses.add(GuildData(glob, self.id, json_data=json_data.get('data', {})))
        glob.ses.commit()

class ReturnData:
    """
    Data class for returning data from functions

    :type response: bool
    :type message: str
    :type video: VideoClass child

    :param response: True if successful, False if not
    :param message: Message to be returned
    :param video: VideoClass child object to be returned if needed
    """
    def __init__(self, response: bool, message: str, video=None, terminate=False):
        self.response = response
        self.message = message
        self.video = video
        self.terminate = terminate

class WebData:
    """
    Replaces commands.Context when there can be none

    :type guild_id: int
    :type author: VideoAuthor

    :param guild_id: ID of the guild
    :param author: Name of the author
    :param author: VideoAuthor object
    """
    def __init__(self, guild_id: int, author: VideoAuthor):
        self.guild_id = guild_id
        self.author: VideoAuthor = author

    async def reply(self, content=None, **kwargs):
        pass

    async def send(self, content=None, **kwargs):
        pass

class Options(Base):
    """
    Data class for storing options for each guild
    :type guild_id: int
    :param guild_id: ID of the guild
    """
    __tablename__ = 'options'

    id = Column(Integer, ForeignKey('guilds.id'), primary_key=True)

    stopped = Column(Boolean, default=False)
    loop = Column(Boolean, default=False)
    is_radio = Column(Boolean, default=False)
    language = Column(String(2), default='en')
    response_type = Column(String(5), default='short')
    search_query = Column(String, default='Never gonna give you up')
    buttons = Column(Boolean, default=False)
    volume = Column(Float, default=1.0)
    buffer = Column(Integer, default=600)
    history_length = Column(Integer, default=20)
    player_id = Column(Integer, default=0)
    subtitles = Column(String, default='False')

    def __init__(self, guild_id: int, json_data: dict, **kw: any):
        super().__init__(**kw)
        self.id: int = guild_id  # id of the guild

        self.stopped: bool = json_data.get('stopped', False)  # if the player is stopped
        self.loop: bool = json_data.get('loop', False)  # if the player is looping
        self.is_radio: bool = json_data.get('is_radio', False)  # if the current media is a radio
        self.language: str = json_data.get('language', 'en')  # language of the bot
        self.response_type: str = json_data.get('response_type', 'short')  # long or short
        self.search_query: str = json_data.get('search_query', 'Never gonna give you up')  # last search query
        self.buttons: bool = json_data.get('buttons', False)  # if single are enabled
        self.volume: float = json_data.get('volume', 1.0)  # volume of the player
        self.buffer: int = json_data.get('buffer', 600)  # how many seconds of nothing playing before bot disconnects | 600 = 10min
        self.history_length: int = json_data.get('history_length', 20)  # how many songs are stored in the history
        self.player_id: int = json_data.get('player_id', 0)  # ID of the player
        self.subtitles: str = json_data.get('subtitles', 'False')  # if subtitles are enabled

class GuildData(Base):
    """
    Data class for storing discord data about guilds
    :type guild_id: int
    :param guild_id: ID of the guild
    """
    __tablename__ = 'guild_data'

    id = Column(Integer, ForeignKey('guilds.id'), primary_key=True)

    name = Column(String)
    key = Column(CHAR(6))
    member_count = Column(Integer)
    text_channel_count = Column(Integer)
    voice_channel_count = Column(Integer)
    role_count = Column(Integer)
    owner_id = Column(Integer)
    owner_name = Column(String)
    created_at = Column(String)
    description = Column(String)
    large = Column(Boolean)
    icon = Column(String)
    banner = Column(String)
    splash = Column(String)
    discovery_splash = Column(String)
    voice_channels = Column(JSON)

    def __init__(self, glob: GlobalVars or None, guild_id, json_data: dict, **kw: any):
        super().__init__(**kw)
        self.id: int = guild_id

        self.name: str = json_data.get('name')
        self.key: str = json_data.get('key')
        self.member_count: int = json_data.get('member_count')
        self.text_channel_count: int = json_data.get('text_channel_count')
        self.voice_channel_count: int = json_data.get('voice_channel_count')
        self.role_count: int = json_data.get('role_count')
        self.owner_id: int = json_data.get('owner_id')
        self.owner_name: str = json_data.get('owner_name')
        self.created_at: str = json_data.get('created_at')
        self.description: str = json_data.get('description')
        self.large: bool = json_data.get('large')
        self.icon: str = json_data.get('icon')
        self.banner: str = json_data.get('banner')
        self.splash: str = json_data.get('splash')
        self.discovery_splash: str = json_data.get('discovery_splash')
        self.voice_channels: list = json_data.get('voice_channels')

        self.renew(glob)

    def renew(self, glob: GlobalVars or None = None):
        guild_object = glob.bot.get_guild(int(self.id)) if glob else None

        # generate random key from the ID
        random.seed(self.id)  # set seed to the guild ID
        self.key = ''.join(random.choice('abcdefghijklmnopqrstuvwxyz0123456789') for _ in range(6))

        if guild_object:
            self.name = guild_object.name

            # set random key for the guild from the ID
            random.seed(self.id)  # set seed to the guild ID
            self.key = ''.join(random.choice('abcdefghijklmnopqrstuvwxyz0123456789') for _ in range(6))

            self.member_count = guild_object.member_count
            self.text_channel_count = len(guild_object.text_channels)
            self.voice_channel_count = len(guild_object.voice_channels)
            self.role_count = len(guild_object.roles)

            self.owner_id = guild_object.owner_id

            # check if owner exists
            self.owner_name = guild_object.owner.name if guild_object.owner else None

            # created at time
            self.created_at = guild_object.created_at.strftime("%d/%m/%Y %H:%M:%S")
            self.description = guild_object.description
            self.large = guild_object.large

            # check if guild has attributes
            self.icon = guild_object.icon.url if guild_object.icon else None
            self.banner = guild_object.banner.url if guild_object.banner else None
            self.splash = guild_object.splash.url if guild_object.splash else None
            self.discovery_splash = guild_object.discovery_splash.url if guild_object.discovery_splash else None
            self.voice_channels = [{'name': channel.name, 'id': channel.id} for channel in
                                   guild_object.voice_channels] if guild_object.voice_channels else None

        guild = glob.ses.query(Guild).filter(Guild.id == self.id).first()
        if guild:
            guild.last_updated['data'] = int(time())
        glob.ses.commit()

class Save(Base):
    """
    Data class for storing saved videos
    :type guild_id: int
    """
    __tablename__ = 'saves'

    id = Column(Integer, primary_key=True)
    position = Column(Integer)
    guild_id = Column(Integer, ForeignKey('guilds.id'))
    name = Column(String)
    author = Column(JSON)
    created_at = Column(Integer)

    queue = relationship('SaveVideo', backref='saves', order_by='SaveVideo.position', collection_class=ordering_list('position'), lazy=True)

    def __init__(self, guild_id: int, name: str, author: VideoAuthor, **kw: any):
        super().__init__(**kw)
        self.guild_id: int = guild_id
        self.name: str = name
        self.created_at: int = int(time())
        self.author: VideoAuthor = author

class SlowedUser(Base):
    """
    Data class for storing slowed users
    :type guild_id: int
    :type user_id: int
    :type user_name: str
    :type slowed_for: int
    """
    __tablename__ = 'slowed_users'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer)
    user_name = Column(String)
    guild_id = Column(Integer, ForeignKey('guilds.id'))
    slowed_for = Column(Integer)

    def __init__(self, guild_id: int, user_id: int, user_name: str, slowed_for: int, **kw: any):
        super().__init__(**kw)
        self.guild_id: int = guild_id
        self.user_id: int = user_id
        self.user_name: str = user_name
        self.slowed_for: int = slowed_for

class TorturedUser(Base):
    """
    Data class for storing tortured users
    :type guild_id: int
    :type user_id: int
    :type torture_delay: int
    """
    __tablename__ = 'tortured_users'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer)
    guild_id = Column(Integer, ForeignKey('guilds.id'))
    torture_delay = Column(Integer)

    def __init__(self, guild_id: int, user_id: int, torture_delay: int, **kw: any):
        super().__init__(**kw)
        self.guild_id: int = guild_id
        self.user_id: int = user_id
        self.torture_delay: int = torture_delay

class DiscordCommand(Base):
    """
    Data class for storing discord commands
    :type name: str
    :type description: str
    :type category: str
    :type attributes: List[dict]
    """
    __tablename__ = 'discord_commands'

    id = Column(Integer, primary_key=True)
    name = Column(String)
    description = Column(String)
    category = Column(String)
    attributes = Column(JSON)

    def __init__(self, name: str, description: str, category: str, attributes: List[dict], **kw: any):
        super().__init__(**kw)
        self.name: str = name
        self.description: str = description
        self.category: str = category
        self.attributes: str = json.dumps(attributes)

class TimeLog(Base):
    """
    Data class for storing logs with a timestamp included

    :type log_type: int
    :type timestamp: int
    :type guild_id: int
    :type channel_id: int

    :param log_type: Type of the log (specified in the tl() function)
    :param guild_id: ID of the guild
    :param channel_id: ID of the channel
    """
    __tablename__ = 'time_logs'

    id = Column(Integer, primary_key=True)
    log_type = Column(Integer)
    timestamp = Column(Integer)
    guild_id = Column(Integer, ForeignKey('guilds.id'))
    channel_id = Column(Integer)

    def __init__(self, log_type: int, guild_id: int = None, channel_id: int = None, timestamp: int = None, **kw: any):
        super().__init__(**kw)
        self.log_type: int = log_type
        self.timestamp: int = int(time()) if not timestamp else timestamp
        self.guild_id: int = guild_id
        self.channel_id: int = channel_id

class VoiceLogDB(Base):
    """
    Data class for storing voice logs

    :type guild_id: int
    :type channel_id: int
    :type connected_at: int
    :type disconnected_at: int
    :type time_in_vc: int
    :type time_playing: int
    :type time_paused: int

    :param voice_log: VoiceLog object
    """
    __tablename__ = 'voice_logs'

    id = Column(Integer, primary_key=True)
    guild_id = Column(Integer, ForeignKey('guilds.id'))
    channel_id = Column(Integer)
    connected_at = Column(Integer)
    disconnected_at = Column(Integer)
    time_in_vc = Column(Integer)
    time_playing = Column(Integer)
    time_paused = Column(Integer)

    def __init__(self, voice_log: VoiceLog, **kw: any):
        super().__init__(**kw)

        self.guild_id: int = voice_log.guild_id
        self.channel_id: int = voice_log.channel_id
        self.connected_at: int = voice_log.connected_at
        self.disconnected_at: int = voice_log.disconnected_at
        self.time_in_vc: int = voice_log.time_in_vc
        self.time_playing: int = voice_log.time_playing
        self.time_paused: int = voice_log.time_paused

