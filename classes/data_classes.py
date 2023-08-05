from utils.globals import get_bot

import random
from time import time

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
    def __init__(self, successful: bool, message: str, video = None):
        self.response = successful
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

class Options:
    """
    Data class for storing options for each guild

    :type guild_id: int

    :param guild_id: ID of the guild
    """
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

class GuildData:
    """
    Data class for storing discord data about guilds

    :type guild_id: int
    :type old_data: GuildData

    :param guild_id: ID of the guild
    :param old_data: Old GuildData object to be used for updating
    """
    def __init__(self, guild_id, old_data=None):
        self.id: int = guild_id
        bot = get_bot()
        guild_object = bot.get_guild(int(guild_id))

        if guild_object:
            self.name = guild_object.name

            # set random key for the guild from the ID
            random.seed(self.id) # set seed to the guild ID
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
            self.voice_channels = [{'name': channel.name, 'id': channel.id} for channel in guild_object.voice_channels] if guild_object.voice_channels else None

        else:
            if old_data:
                self.name = old_data.name
                self.key = old_data.key
                self.member_count = old_data.member_count
                self.owner_id = old_data.owner_id
                self.owner_name = old_data.owner_name
                self.created_at = old_data.created_at
                self.description = old_data.description
                self.large = old_data.large
                self.icon = old_data.icon
                self.banner = old_data.banner
                self.splash = old_data.splash
                self.voice_channels = old_data.voice_channels

            # if there is no old data set everything to None except the key
            else:
                self.name = None

                # generate random key from the ID
                random.seed(self.id) # set seed to the guild ID
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

class Guild:
    """
    Data class for storing data about guilds

    :type guild_id: int

    :param guild_id: ID of the guild
    """

    def __init__(self, guild_id):
        self.id = guild_id
        self.options = Options(guild_id)
        self.saves = []
        self.queue = []
        self.search_list = []
        self.now_playing = None
        self.history = []
        self.data = GuildData(guild_id)
        self.connected = True

    def renew(self):
        self.data = GuildData(self.id, self.data)