# Nicholas the 7th - New Instance

This is a setup guide for `Linux (Ubuntu)`. This is just a guide for future me, but if you want to use it, feel free to do so. 

Main [README.md](../README.md)

## Initial Setup

- ``sudo su`` - Make yourself a super-user

- ``apt update && apt upgrade -y`` - Update your system

- ``apt install git -y`` - Install git

- ``apt install python3 -y`` - Install python3

- ``apt install python3-pip -y`` - Install pip3

- ``apt install ffmpeg -y`` - Install ffmpeg

### Folder setup

Create a folder for the bot (I am using `/var/www/` - the same as apache2)
```bash
mkdir /path_to_directory 
```
Clone the [nicholas_the_7th](https://github.com/Tomer27cz/nicholas_the_7th) repository
```bash
git clone https://github.com/Tomer27cz/nicholas_the_7th.git
```
Rename the folder
```bash
mv nicholas_the_7th bot
```
Move into the folder
```bash
cd bot
```
Give permissions to the folder
```bash
chmod -R 777 /path_to_directory
```

### Discord Developer Portal
- Go to the [Discord Developer Portal](https://discord.com/developers/applications)
- Create a new application

##### Bot tab
- Create a new bot
- Copy the `BOT_TOKEN`
- Check all the Privileged Gateway Intents

##### OAuth2 tab
- Copy the `CLIENT_ID` and `CLIENT_SECRET`
- Go to the OAuth2 tab and add the redirect uri ```http://YOUR_WEBSITE/login```

##### Optional
- Add a bot icon
- Add a bot description


- In the OAuth2 tab under Default Authorization Link, check `In-App Authorization` (this will show a button in the bot profile)
- Scopes: `bot` and `application.commands`
- Bot Permissions: `Administrator` or 
>`Create Instant Invide`, `Read Messages/View Channels`, `Send Messages`, `Send Messages in Threads`, `Embed Links`, `Attach Files`, `Read Message History`, `Add Reactions`, `Use Slash Commands`, `Connect`, `Speak`

### Config setup

#### Before version 4.0.4

In versions before 4.0.4, the config file was called `config.py`. This has been changed to `.env` in the newer versions. To use the new config file, replace "f strings" with `${}` in the string (also remove the f lol).

#### After version 4.0.4

These are the required environment variables for the bot.

- Create a file called `.env` in the main directory
```dotenv
# Description: Configuration file for the bot
# Discord
CLIENT_ID='YOUR_CLIENT_ID' # This is your bots id
OWNER_ID='YOUR_USER_ID' # This is your user id
BOT_TOKEN='YOUR_BOT_TOKEN' # This is the token for the bot
CLIENT_SECRET="YOUR_CLIENT_SECRET" # This is the client secret for the bot

# Prefix
PREFIX="ncl." # This is the prefix for the bot

# Authorised Users
AUTHORIZED_USERS='[416254812339044365, 349164237605568513]' # has to be this format | ='[1, 2, 3, ...]' | This is a list of authorised users (add your user id here - not required)

# Web
COMPOSE_PROFILES="bot" # "bot"- only start bot, "web"- start web and bot
WEB_SECRET_KEY='YOUR_SECRET_KEY' # This is the secret key for the flask server (you can generate one with os.urandom(24))
WEB_URL='YOUR_WEB_URL' # This is the url for the flask server (http://127.0.0.1:5420 is the default url)

# Discord OAuth2
REDIRECT_URI="https://YOUR_WEBSITE/login" # The address you added to the discord developer portal
DISCORD_LOGIN_URL="https://discord.com/api/oauth2/authorize?client_id=${CLIENT_ID}&redirect_uri=${REDIRECT_URI}&response_type=code&scope=identify%20guilds" # identify guilds - scopes are required for the bot to work
DISCORD_API_ENDPOINT='https://discord.com/api/v10' # This is the discord api endpoint (more recent version may be available)

# Spotify
SPOTIFY_CLIENT_ID='YOUR_SPOTIFY_CLIENT_ID' # This is the client id for the spotify api
SPOTIFY_CLIENT_SECRET='YOUR_SPOTIFY_CLIENT_SECRET' # This is the client secret for the spotify api
SPOTIFY_REDIRECT_URI='https://localhost:8888/callback' # This is the redirect uri for the spotify api

# SoundCloud
SOUNDCLOUD_CLIENT_ID='YOUR_SOUNDCLOUD_ID' # SoundCloud ID (you can use your accounts id -> developer tools)

# DEFAULT VALUES - DO NOT CHANGE UNLESS YOU KNOW WHAT YOU'RE DOING
DEFAULT_DISCORD_AVATAR="https://cdn.discordapp.com/embed/avatars/0.png"
VLC_LOGO="https://upload.wikimedia.org/wikipedia/commons/3/38/VLC_icon.png"
DEVELOPER_ID=349164237605568513
# Discord
PERMISSIONS=3198017
INVITE_URL="https://discord.com/api/oauth2/authorize?client_id=${CLIENT_ID}&permissions=${PERMISSIONS}&scope=bot"
```

### Copy database

**Skip this step** - if you don't want to use a database from a previous instance or if you are setting up the bot for **the first time.**

If you have an existing database from a previous instance, you can just copy it to the main directory. 

- ``cd /var/www`` - Move to parent directory
- ``ls`` - List all files
- It should look something like this ``bot bot_old html``
- ``cp -r bot_old/db bot`` - Copy the database to the new instance

# Two ways to run the bot

The bot can be run two ways. 

- [Docker](#docker-setup) (I am currently using this method)
- [Apache2](#apache2-setup) (I had some problems with wsgi using the wrong python version)

# Docker setup

### [Install docker](DOCKER.md)

### ~~Build Docker~~ 
##### deprecated in versions after 3.2.3

~~Build a new folder with all the required files. This will create a new folder called `FOLDERNAME_docker` with all the required files.
`python3 build_docker.py`
`cd /var/www/bot_docker`~~

### Docker compose

Build the containers - this will take a while
```bash
docker compose build
```
Run the containers - you can use `-d` to run in the background
```bash
docker compose up -d
```

### Check if it works

Check if the containers are running
```bash
docker compose ps
```
It should look something like this:
```
NAME      IMAGE              COMMAND                                                     SERVICE   CREATED        STATUS        PORTS
bot       bot-bot     "/bin/sh -c 'python main.py >> logs/bot.log 2>&1'"   bot       19 hours ago   Up 18 hours   5420-5422/tcp
nginx     bot-nginx   "/docker-entrypoint.sh nginx -g 'daemon off;'"              nginx     18 hours ago   Up 18 hours   0.0.0.0:80->80/tcp, :::80->80/tcp, 0.0.0.0:443->443/tcp, :::443->443/tcp, 0.0.0.0:5420->5420/tcp, :::5420->5420/tcp
web       bot-web     "/bin/sh -c 'uwsgi app.ini'"                                web       18 hours ago   Up 18 hours   5420-5422/tcp
```

### Troubleshooting

If one of the containers is not running (or is restarting), you can check the logs with this command:
```bash
docker logs CONTAINER_NAME
```

If you want to access the container, you can use this command:
```bash
docker exec -t -i CONTAINER_NAME /bin/bash
```

### General commands


If you want to stop the containers, you can use this command:
```bash
docker compose stop
```
or this command to stop and remove the containers:
```bash
docker compose down
```
If you want to start the containers again, you can use this command:
```bash
docker compose start
```

# Apache2 setup

- ``apt install apache2 apache2-utils apache2-dev -y`` - Install apache2

- ``apt install libapache2-mod-wsgi-py3 -y`` - Install mod_wsgi

- ``apt autoremove -y`` - Remove unnecessary packages

### Pip setup

- ``pip3 install --upgrade pip`` - Upgrade pip

- ``pip3 install mod-wsgi`` - Install mod_wsgi

- ``pip3 install -r requirements.txt`` - Install requirements

### Apache2 config

- ``cd /etc/apache2/sites-available`` - Move to apache2 sites-available directory
- ``nano bot.conf`` - Create a config file for apache2
- Copy the following code and fill it out

Idk witch one to use
```
<VirtualHost *>
    ServerAdmin example@email.com
    ServerName localhost
    ErrorLog /var/www/bot/log/apache_error.log
    CustomLog /var/www/bot/log/apache_access.log combined
    WSGIDaemonProcess www-data user=www-data group=root threads=5
    WSGIScriptAlias / /var/www/bot/server.wsgi
    <Directory /var/www/bot >
        WSGIScriptReloading On
        Require all granted
   </Directory>
</VirtualHost>
```
```
<VirtualHost *:80>
    ServerName ip
    ServerAdmin example@email.com
    WSGIScriptAlias / /var/www/bot/server.wsgi
    <Directory /var/www/bot/>
    	Order allow,deny
    	Allow from all
    </Directory>
    Alias /static /var/www/bot/static
    <Directory /var/www/bot/static/>
    	Order allow,deny
    	Allow from all
    </Directory>
    ErrorLog /var/www/bot/logs/apache_error.log
    LogLevel warn
    CustomLog /var/www/bot/logs/apache_access.log combined
</VirtualHost>
```

- ``a2ensite bot`` - Enable the site
- ``a2dissite 000-default`` - Disable the default site
- ``systemctl reload apache2`` - Reload apache2

### Run the bot

- ``cd /var/www/bot`` - Move to main directory

```
nohup python3 -u main.py &>> logs/bot.log &
```
- ``service apache2 restart`` - Restart apache2

Now you can go to your website and see if it works.
If not... check the logs and good luck.
