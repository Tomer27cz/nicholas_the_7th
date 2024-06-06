import os
import json
from dotenv import load_dotenv

load_dotenv()

for key, value in os.environ.items():
    globals()[key] = value

CLIENT_ID = os.getenv('CLIENT_ID')
OWNER_ID = os.getenv('OWNER_ID')
BOT_TOKEN = os.getenv('BOT_TOKEN')
CLIENT_SECRET = os.getenv('CLIENT_SECRET')
PREFIX = os.getenv('PREFIX')

WEB_SECRET_KEY = os.getenv('WEB_SECRET_KEY')
WEB_URL = os.getenv('WEB_URL')
REDIRECT_URI = os.getenv('REDIRECT_URI')
DISCORD_LOGIN_URL = os.getenv('DISCORD_LOGIN_URL')
DISCORD_API_ENDPOINT = os.getenv('DISCORD_API_ENDPOINT')
SPOTIFY_CLIENT_ID = os.getenv('SPOTIFY_CLIENT_ID')
SPOTIFY_CLIENT_SECRET = os.getenv('SPOTIFY_CLIENT_SECRET')
SPOTIFY_REDIRECT_URI = os.getenv('SPOTIFY_REDIRECT_URI')
SOUNDCLOUD_CLIENT_ID = os.getenv('SOUNDCLOUD_CLIENT_ID')
PARENT_DIR = os.getenv('PARENT_DIR')
DEFAULT_DISCORD_AVATAR = os.getenv('DEFAULT_DISCORD_AVATAR')
VLC_LOGO = os.getenv('VLC_LOGO')
DEVELOPER_ID = os.getenv('DEVELOPER_ID')
PERMISSIONS = os.getenv('PERMISSIONS')
INVITE_URL = os.getenv('INVITE_URL')

ENABLE_WEB = True if os.getenv('COMPOSE_PROFILES') == 'web' else False

try:
    AUTHORIZED_USERS = json.loads(os.environ.get('AUTHORIZED_USERS', '[]'))
    AUTHORIZED_USERS = [int(user) for user in AUTHORIZED_USERS]
except json.JSONDecodeError:
    AUTHORIZED_USERS = []
except ValueError:
    pass
