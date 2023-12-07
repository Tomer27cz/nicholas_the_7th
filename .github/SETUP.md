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

# Docker setup

### Install docker

I followed this [guide](https://www.cherryservers.com/blog/how-to-install-and-use-docker-compose-on-ubuntu-20-04) to install docker.

To begin, update your package list:
```bash
apt update -y
```

Next, you'll need these four packages to allow `apt` to work with HTTPS-based repositories:
- `ca-certificates` - A package that verifies SSL/TLS certificates.
- `curl` - A popular data transfer tool that supports multiple protocols including HTTPS.
- `gnupg` - An open source implementation of the Pretty Good Privacy (PGP) suite of cryptographic tools.
- `lsb-release` - A utility for reporting Linux Standard Base (LSB) versions.

Use this command to install those packages:
```bash
apt install ca-certificates curl gnupg lsb-release -y
```

Make a directory for Docker's GPG key:
```bash
mkdir /etc/apt/demokeyrings
```

Use `curl` to download Docker's keyring and pipe it into `gpg` to create a GPG file so `apt` trusts Docker's repo:
```bash
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/demokeyrings/demodocker.gpg
```

Add the Docker repo to your system with this command:
```bash
 echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/demokeyrings/demodocker.gpg] https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list
```

Now that you added Docker's repo, update your package lists again:
```bash
apt update -y
```

Next, install Docker-CE (Community Edition), the Docker-CE CLI, the containerd runtime, and Docker Compose with this command:
```bash
apt install docker-ce docker-ce-cli containerd.io docker-compose-plugin
```

You can verify Docker-CE, the Docker-CE CLI, containerd, and Docker Compose are installed by checking their versions with these commands:
```bash
docker --version; docker compose version;ctr version
```

It should look something like this:
```
Docker version 24.0.7, build afdd53b
Docker Compose version v2.21.0
Client:
  Version:  1.6.25
  Revision: d8f198a4ed8892c764191ef7b3b06d8a2eeb5c7f
  Go version: go1.20.10

Server:
  Version:  1.6.25
  Revision: d8f198a4ed8892c764191ef7b3b06d8a2eeb5c7f
  UUID: 234a5863-7cf4-4462-ac20-53b24bc001ef
```

### Build Docker

Build a new folder with all the required files. This will create a new folder called `FOLDERNAME_docker` with all the required files.
```bash
python3 build_docker.py
```
```bash
cd /var/www/bot_docker
```

### Docker compose

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
bot       bot_docker-bot     "/bin/sh -c 'python main.py >> db/log/activity.log 2>&1'"   bot       19 hours ago   Up 18 hours   5420-5422/tcp
nginx     bot_docker-nginx   "/docker-entrypoint.sh nginx -g 'daemon off;'"              nginx     18 hours ago   Up 18 hours   0.0.0.0:80->80/tcp, :::80->80/tcp, 0.0.0.0:443->443/tcp, :::443->443/tcp, 0.0.0.0:5420->5420/tcp, :::5420->5420/tcp
web       bot_docker-web     "/bin/sh -c 'uwsgi app.ini'"                                web       18 hours ago   Up 18 hours   5420-5422/tcp
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