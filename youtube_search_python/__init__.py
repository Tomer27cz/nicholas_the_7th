from .search import Search, VideosSearch, ChannelsSearch, PlaylistsSearch, CustomSearch, ChannelSearch
from .extras import Video, Playlist, Suggestions, Hashtag, Comments, Transcript, Channel
from .streamurlfetcher import StreamURLFetcher
from .core.constants import *
from .core.utils import *


__title__        = 'youtube-search-python'
__version__      = '1.6.2'
__author__       = 'alexmercerind'
__license__      = 'MIT'


''' Deprecated. Present for legacy support. '''
from .legacy import SearchVideos, SearchPlaylists
from .legacy import SearchVideos as searchYoutube
