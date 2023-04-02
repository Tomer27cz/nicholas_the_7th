# discord_bot_stanley_the_7th

## About

This is a discord bot that I made for my friends and I to use in our discord server. It is a work in progress and I will be adding more features as I go along.

It is not meant to be used by anyone else, but if you want to use it, feel free to do so.

## Installation

- Clone the repository 
- Install the requirements
```
pip install -r requirements.txt
```
- Create a file called `config.py` in the root directory
```python
CLIENT_ID = 'YOUR_CLIENT_ID' # This is your bots id
OWNER_ID = 'YOUR_USER_ID' # This is your user id
BOT_TOKEN = 'YOUR_BOT_TOKEN' # This is the token for the bot
CLIENT_SECRET = "YOUR_CLIENT_SECRET" # This is the client secret for the bot
REDIRECT_URI = "https://YOUR_WEBSITE/login" # http://127.0.0.1:5000/login is the default redirect uri for the flask server
DISCORD_LOGIN_URL = "YOUR_DISCORD_LOGIN_URL" # identify guilds email - scopes are required for the bot to work
DISCORD_API_ENDPOINT = 'https://discord.com/api/v10' # This is the discord api endpoint (more recent version may be available)
```
- Run the bot
```
python main.py
```
