from utils.globals import get_bot, get_session
from database.main import *

import random
from time import time

class Guild(Base):
    """
    Data class for storing data about guilds
    :type guild_id: int
    :param guild_id: ID of the guild
    """
    __tablename__ = 'guilds'

    id = Column(Integer, primary_key=True)
    options = relationship('Options', uselist=False, backref='guilds')
    saves = relationship('Save', backref='guilds', order_by='Save.position', collection_class=ordering_list('position'))
    queue = relationship('Queue', backref='guilds', order_by='Queue.position', collection_class=ordering_list('position'))
    search_list = relationship('SearchList', backref='guilds', order_by='SearchList.position', collection_class=ordering_list('position'))
    now_playing = relationship('NowPlaying', uselist=False, backref='guilds')
    history = relationship('History', backref='guilds', order_by='History.position', collection_class=ordering_list('position'))
    data = relationship('GuildData', uselist=False, backref='guilds')
    connected = Column(Boolean, default=True)

    def __init__(self, guild_id):
        self.id = guild_id

        get_session().add(Options(self.id))
        get_session().add(GuildData(self.id))
        get_session().commit()

class ReturnData:
    """
    Data class for returning data from functions

    :type response: bool
    :type message: str
    :type video: VideoClass

    :param response: True if successful, False if not
    :param message: Message to be returned
    :param video: VideoClass object to be returned if needed
    """
    def __init__(self, response: bool, message: str, video = None):
        self.response = response
        self.message = message
        self.video = video

class WebData:
    """
    Replaces commands.Context when there can be none

    :type guild_id: int
    :type author: str
    :type author_id: int

    :param guild_id: ID of the guild
    :param author: Name of the author
    :param author_id: ID of the author
    """
    def __init__(self, guild_id: int, author: str, author_id: int):
        self.guild_id = guild_id
        self.author = author
        self.author_id = author_id

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
    last_updated = Column(Integer, default=int(time()))

    def __init__(self, guild_id: int):
        self.id: int = guild_id # id of the guild
        self.stopped: bool = False # if the player is stopped
        self.loop: bool = False # if the player is looping
        self.is_radio: bool = False # if the current media is a radio
        self.language: str = 'en' # language of the bot
        self.response_type: str = 'short'  # long or short
        self.search_query: str = 'Never gonna give you up' # last search query
        self.buttons: bool = False # if buttons are enabled
        self.volume: float = 1.0 # volume of the player
        self.buffer: int = 600  # how many seconds of nothing playing before bot disconnects | 600 = 10min
        self.history_length: int = 20 # how many songs are stored in the history
        self.last_updated: int = int(time()) # when was the last time any of the guilds data was updated

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

    def __init__(self, guild_id):
        self.id: int = guild_id
        self.renew()

    def renew(self):
        guild_object = get_bot().get_guild(int(self.id))

        if guild_object:
            self.name = guild_object.name

            # set random key for the guild from the ID
            random.seed(self.id)  # set seed to the guild ID
            self.key = ''.join(random.choice('abcdefghijklmnopqrstuvwxyz0123456789') for _ in range(6))

            self.member_count = guild_object.member_count
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

        else:
            self.name = None

            # generate random key from the ID
            random.seed(self.id)  # set seed to the guild ID
            self.key = ''.join(random.choice('abcdefghijklmnopqrstuvwxyz0123456789') for _ in range(6))

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
    queue = relationship('SaveVideo', backref='saves', order_by='SaveVideo.position', collection_class=ordering_list('position'))

    def __init__(self, guild_id: int, name: str):
        self.id: int = guild_id
        self.name: str = name