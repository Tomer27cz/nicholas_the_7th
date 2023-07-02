[![Icon](https://raw.githubusercontent.com/Tomer27cz/discord_bot_stanley_the_7th/master/.github/icon.svg)](#readme)

## About

This is a discord bot that I made for a few discord servers. It is a work in progress, and I will be adding more features as I go along.

It is not meant to be used by anyone else, but if you want to use it, feel free to do so.

[![Dashboard](https://raw.githubusercontent.com/Tomer27cz/discord_bot_stanley_the_7th/master/.github/dashboard.png)](#readme)

## Invite

The bot is currently hosted by me. So if you want to, you can [Invite](https://discord.com/api/oauth2/authorize?client_id=1007004463933952120&permissions=3198017&scope=bot) him.

## Installation

- Clone the repository 
- Install the requirements
```
pip install -r requirements.txt
```
- Create a file called `config.py` in the root directory
```python
# Description: Configuration file for the bot
# Discord
CLIENT_ID = 'YOUR_CLIENT_ID' # This is your bots id
OWNER_ID = 'YOUR_USER_ID' # This is your user id
BOT_TOKEN = 'YOUR_BOT_TOKEN' # This is the token for the bot
CLIENT_SECRET = "YOUR_CLIENT_SECRET" # This is the client secret for the bot

# Discord Invite
PERMISSIONS = 3198017 # This is the permissions for the bot
INVITE_URL = f"https://discord.com/api/oauth2/authorize?client_id={CLIENT_ID}&permissions={PERMISSIONS}&scope=bot" # a discord invite url

# Discord OAuth2
REDIRECT_URI = "https://YOUR_WEBSITE:5420/login" # http://127.0.0.1:5420/login is the default redirect uri for the flask server
DISCORD_LOGIN_URL = "YOUR_DISCORD_LOGIN_URL" # identify guilds - scopes are required for the bot to work
DISCORD_API_ENDPOINT = 'https://discord.com/api/v10' # This is the discord api endpoint (more recent version may be available)

# Web
WEB_SECRET_KEY = '!secret!' # This is the secret key for the flask server
WEB_URL = 'YOUR_WEB_URL' # This is the url for the flask server (http://127.0.0.1:5420 is the default url)

# Spotify
SPOTIPY_CLIENT_ID='YOUR_SPOTIFY_CLIENT_ID' # This is the client id for the spotify api
SPOTIPY_CLIENT_SECRET='YOUR_SPOTIFY_CLIENT_SECRET' # This is the client secret for the spotify api
SPOTIPY_REDIRECT_URI='https://localhost:8888/callback' # This is the redirect uri for the spotify api

# SoundCloud
SOUNDCLOUD_CLIENT_ID = 'YOUR_SOUNDCLOUD_ID' # SoundCloud ID (you can use your accounts id -> developer tools)

# Parent Directory
PARENT_DIR = r'C:/Users/Tomer27cz/Desktop/Files/CODING/Discord Bot/Python/nicholas_the_7th/' # Leave blank if running from root directory (has to be absolute path and have / at the end)
```
more detailed guide will be added later (maby)
- Run the bot
```
python main.py
```
for Linux (recommended for continuous execution with log)
```
nohup python3 -u main.py &>> log/activity.log &
```


- Run `flaskapp.py` for Web Interface
```
python flaskapp.py
```
or [run with apache2](https://example.com)


## Credits

- [discord.py](https://github.com/Rapptz/discord.py) by Rapptz
- [flask](https://github.com/pallets/flask) by pallets
- [yt-dlp](https://github.com/yt-dlp/yt-dlp)
- [youtube-search-python](https://github.com/alexmercerind/youtube-search-python) by alexmercerind
- [requests](https://github.com/psf/requests) by psf
- [BeautifulSoup](https://www.crummy.com/software/BeautifulSoup/) by Leonard Richardson
- [spotipy](https://github.com/spotipy-dev/spotipy)
- [soundcloud-lib](https://github.com/3jackdaws/soundcloud-lib) by 3jackdaws

## License

[MIT](https://choosealicense.com/licenses/mit/)

## Contributing

If you want to contribute to this project, feel free to do so. I am not very experienced with python, so I am sure there are many things that can be improved.
