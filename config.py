import os
import json
from dotenv import load_dotenv

load_dotenv()

# for key, value in os.environ.items():
#     print(f'{key}={value} | {type(value)}')
#     globals()[key] = value

def get_env(_key: str, var_type: type=str, default=None):
    _value = os.getenv(_key)
    if _value is None:
        return default

    try:
        return var_type(_value)
    except ValueError:
        return _value

CLIENT_ID = get_env('CLIENT_ID', int)
OWNER_ID = get_env('OWNER_ID', int, 349164237605568513)
BOT_TOKEN = get_env('BOT_TOKEN')
CLIENT_SECRET = get_env('CLIENT_SECRET')
PREFIX = get_env('PREFIX')
WEB_SECRET_KEY = get_env('WEB_SECRET_KEY')
WEB_URL = get_env('WEB_URL')
REDIRECT_URI = get_env('REDIRECT_URI')
DISCORD_LOGIN_URL = get_env('DISCORD_LOGIN_URL')
DISCORD_API_ENDPOINT = get_env('DISCORD_API_ENDPOINT')
SPOTIFY_CLIENT_ID = get_env('SPOTIFY_CLIENT_ID')
SPOTIFY_CLIENT_SECRET = get_env('SPOTIFY_CLIENT_SECRET')
SPOTIFY_REDIRECT_URI = get_env('SPOTIFY_REDIRECT_URI')
SOUNDCLOUD_CLIENT_ID = get_env('SOUNDCLOUD_CLIENT_ID')
PARENT_DIR = get_env('PARENT_DIR')
DEFAULT_DISCORD_AVATAR = get_env('DEFAULT_DISCORD_AVATAR')
VLC_LOGO = get_env('VLC_LOGO')
DEVELOPER_ID = get_env('DEVELOPER_ID', int, 349164237605568513)
PERMISSIONS = get_env('PERMISSIONS')
INVITE_URL = get_env('INVITE_URL')

ENABLE_WEB = True if os.getenv('COMPOSE_PROFILES') == 'web' else False

try:
    AUTHORIZED_USERS = json.loads(os.environ.get('AUTHORIZED_USERS', '[]'))
    AUTHORIZED_USERS = [int(user) for user in AUTHORIZED_USERS]
except json.JSONDecodeError:
    AUTHORIZED_USERS = []
except ValueError:
    pass
