[![Icon](https://raw.githubusercontent.com/Tomer27cz/discord_bot_stanley_the_7th/master/.github/icon.svg)](#readme)

## About

This is a discord bot that I made for a few discord servers. It is a work in progress, and I will be adding more features as I go along.

It is not meant to be used by anyone else, but if you want to use it, feel free to do so.

[![Dashboard](https://raw.githubusercontent.com/Tomer27cz/discord_bot_stanley_the_7th/master/.github/dashboard.png)](#readme)

## [Invite](https://discord.com/api/oauth2/authorize?client_id=1007004463933952120&permissions=3198017&scope=bot)

The bot is currently hosted by me. So if you want to, you can [Invite](https://discord.com/api/oauth2/authorize?client_id=1007004463933952120&permissions=3198017&scope=bot) him.

## [Setup Guide](.github/SETUP.md)

## Configuration - config.py

- Create a file called `config.py` in the main directory
```python
# Description: Configuration file for the bot
# Discord
CLIENT_ID = 'YOUR_CLIENT_ID' # This is your bots id
OWNER_ID = 'YOUR_USER_ID' # This is your user id
BOT_TOKEN = 'YOUR_BOT_TOKEN' # This is the token for the bot
CLIENT_SECRET = "YOUR_CLIENT_SECRET" # This is the client secret for the bot

# Prefix
PREFIX = "ncl." # This is the prefix for the bot

# Authorised Users
AUTHORIZED_USERS = [416254812339044365, 349164237605568513] # This is a list of authorised users (add your user id here - not required)

# Discord Invite
PERMISSIONS = 3198017 # This is the permissions for the bot
INVITE_URL = f"https://discord.com/api/oauth2/authorize?client_id={CLIENT_ID}&permissions={PERMISSIONS}&scope=bot" # a discord invite url

# Discord OAuth2
REDIRECT_URI = "https://YOUR_WEBSITE:5420/login" # http://127.0.0.1:5420/login is the default redirect uri for the flask server
DISCORD_LOGIN_URL = f"https://discord.com/api/oauth2/authorize?client_id={CLIENT_ID}&redirect_uri={REDIRECT_URI}&response_type=code&scope=identify%20guilds" # identify guilds - scopes are required for the bot to work
DISCORD_API_ENDPOINT = 'https://discord.com/api/v10' # This is the discord api endpoint (more recent version may be available)

# Web
WEB_SECRET_KEY = '!secret!' # This is the secret key for the flask server
WEB_URL = 'YOUR_WEB_URL' # This is the url for the flask server (http://127.0.0.1:5420 is the default url)

# Spotify
SPOTIFY_CLIENT_ID='YOUR_SPOTIFY_CLIENT_ID' # This is the client id for the spotify api
SPOTIFY_CLIENT_SECRET='YOUR_SPOTIFY_CLIENT_SECRET' # This is the client secret for the spotify api
SPOTIFY_REDIRECT_URI='https://localhost:8888/callback' # This is the redirect uri for the spotify api

# SoundCloud
SOUNDCLOUD_CLIENT_ID = 'YOUR_SOUNDCLOUD_ID' # SoundCloud ID (you can use your accounts id -> developer tools)

# Parent Directory
# For docker, set this to /app/
PARENT_DIR = r'' # Leave blank if running from root directory (has to be absolute path and have / at the end)

# Default Values
DEFAULT_DISCORD_AVATAR = "https://cdn.discordapp.com/embed/avatars/0.png"
VLC_LOGO = "https://cdn.discordapp.com/attachments/892403162315644931/1008054767379030096/vlc.png"
DEVELOPER_ID = 349164237605568513
```

## Credits

- [discord.py](https://github.com/Rapptz/discord.py) by Rapptz
- [flask](https://github.com/pallets/flask) by pallets
- [yt-dlp](https://github.com/yt-dlp/yt-dlp)
- [youtube-search-python](https://github.com/alexmercerind/youtube-search-python) by alexmercerind
- [requests](https://github.com/psf/requests) by psf
- [BeautifulSoup](https://www.crummy.com/software/BeautifulSoup/) by Leonard Richardson
- [spotipy](https://github.com/spotipy-dev/spotipy)
- [soundcloud-lib](https://github.com/3jackdaws/soundcloud-lib) by 3jackdaws
- [DiscordChatExporterPy](https://github.com/mahtoid/DiscordChatExporterPy) by mahtoid

## License

[MIT](https://choosealicense.com/licenses/mit/)

## Contributing

If you want to contribute to this project, feel free to do so. I am not very experienced with python, so I am sure there are many things that can be improved.
