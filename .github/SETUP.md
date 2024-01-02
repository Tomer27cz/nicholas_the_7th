# Nicholas the 7th - New Instance

This is a setup guide for `Linux (Ubuntu)`. It is not meant to be used by anyone else, but if you want to use it, feel free to do so.

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
mkdir /var/www/
```
```bash
cd /var/www/
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
chmod -R 777 /var/www/bot
```

### Config setup

If you have a config file, you can just copy it to the main directory. If not, you can create one.

- ``nano config.py`` - Create a config file
- Copy the config from ``README.md`` and fill it out

### Copy database

**Skip this step** - if you don't want to use a database from a previous instance or if you are setting up the bot for **the first time.**

If you have an existing database from a previous instance, you can just copy it to the main directory. 

- ``cd /var/www`` - Move to parent directory
- ``ls`` - List all files
- It should look something like this ``bot bot_old html``
- ``cp -r bot_old/db bot`` - Copy the database to the new instance

# Two ways to run the bot

The bot can be run two ways. 

- [Docker](#docker-setup) (I am currently using this method)) 
- [Apache2](#apache2-setup) (I had some problems with wsgi using the wrong python version)

# Docker setup

### [Install docker](DOCKER.md)

### ~~Build Docker~~ 
##### deprecated in newer versions (after 3.2.3)

~~Build a new folder with all the required files. This will create a new folder called `FOLDERNAME_docker` with all the required files.
`python3 build_docker.py`
`cd /var/www/bot_docker`~~

### Docker compose

```bash
cd /var/www/bot
```

Build the containers - this will take a while
```bash
docker-compose build
```
Run the containers - you can use `-d` to run in the background
```bash
docker-compose up -d
```

### Check if it works

Check if the containers are running
```bash
docker compose ps
```
It should look something like this:
```
NAME      IMAGE              COMMAND                                                     SERVICE   CREATED        STATUS        PORTS
bot       bot-bot     "/bin/sh -c 'python main.py >> db/log/activity.log 2>&1'"   bot       19 hours ago   Up 18 hours   5420-5422/tcp
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
    ServerAdmin tomer19cz@gmial.com
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
    ServerAdmin tomer19cz@gmial.com
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
    ErrorLog /var/www/bot/db/log/apache_error.log
    LogLevel warn
    CustomLog /var/www/bot/db/log/apache_access.log combined
</VirtualHost>
```

- ``a2ensite bot`` - Enable the site
- ``a2dissite 000-default`` - Disable the default site
- ``systemctl reload apache2`` - Reload apache2

### Run the bot

- ``cd /var/www/bot`` - Move to main directory

```
nohup python3 -u main.py &>> db/log/activity.log &
```
- ``service apache2 restart`` - Restart apache2

Now you can go to your website and see if it works.
If not... check the logs and good luck.
