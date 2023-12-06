import os
import shutil, errno

def copy_anything(src, dst):
    try:
        shutil.copytree(src, dst)
    except OSError as exc: # python >2.5
        if exc.errno in (errno.ENOTDIR, errno.EINVAL):
            shutil.copy(src, dst)
        else: raise

# get environment
sp, windows = "/", False
if os.name == 'nt':
    sp, windows = "\\", True

# this script creates a new folder at the same level as the current folder
# with the name of the current folder + _docker
# it then copies the contents of the current folder into the new folder
# according to the pre-defined rules
# then it copies Dockerfiles for each of the sub-folders
# and copies a docker-compose.yml file to the new folder

# vars
line_length = 70
ignore_for_bot = ["uWSGI"]

bot_requirements = """
discord
dnspython
PyNaCl
async-timeout
youtube-search-python
asyncio
requests
beautifulsoup4
lxml
yt_dlp
asgiref
spotipy
soundcloud-lib
emoji
aiohttp
grapheme
pytz
SQLAlchemy
"""

web_requirements = """
discord
dnspython
PyNaCl
async-timeout
youtube-search-python
asyncio
requests
beautifulsoup4
lxml
yt_dlp
asgiref
flask
spotipy
soundcloud-lib
werkzeug
emoji
aiohttp
grapheme
pytz
uWSGI
SQLAlchemy
"""

# GET CURRENT FOLDER
current_folder_path = os.path.dirname(os.getcwd())
current_folder_name = os.path.basename(os.getcwd())

# create the new folder with the name of the current folder + _docker
folder = current_folder_path + sp + current_folder_name + "_docker"
fs = current_folder_name + "_docker"

print("------------------- Nicholas the 7th Docker build --------------------")
print("Current folder path: " + current_folder_path)
print("Current folder name: " + current_folder_name)
print("New folder path: " + folder)
print("New folder name: " + fs)
print("-"*line_length)

print("\nCREATING FOLDER STRUCTURE...\n")

# -------------------------------------------------- Folder structure --------------------------------------------------
# - CURRENT-FOLDER-NAME_docker
#   - bot
#     - chat_exporter
#     - classes
#     - commands
#     - database
#     - dce
#     - ipc
#     - sound_effects
#     - utils
#     - web_func
#     - config.py xxxxxxxxxxxxxxxxx
#     - main.py
#     - requirements.txt
#   - web
#     - chat_exporter
#     - classes
#     - commands
#     - database
#     - ipc
#     - utils
#     - static
#     - templates
#     - config.py xxxxxxxxxxxxxxxxx
#     - flaskapp.py
#     - oauth.py
#     - requirements.txt
#   - nginx
#     - nginx.conf
#   - db
#     - add => config_bot.py
#     - add => config_web.py
#     - database.db
#     - log
#       - log.log
#       - data.log
#   - docker-compose.yml
#   - .dockerignore
#   - README.md
#   - LICENSE

# create the new folder
print(f"Creating {folder}...")
os.mkdir(folder)

# create the sub-folders
print(f"Creating {fs}{sp}bot...")
os.mkdir(f"{folder}{sp}bot")
print(f"Creating {fs}{sp}web...")
os.mkdir(f"{folder}{sp}web")
# Don't create nginx and db folder, it will be copied later

# COPY FILES/FOLDERS TO BOT SUB-FOLDER ---------------------------------------------------------------------------------
print(f"\nCOPYING FILES TO {fs}{sp}bot...")
print("-"*line_length)

bot_folders_and_files = ["chat_exporter", "classes", "commands", "database", "dce", "ipc", "sound_effects", "utils", "web_func", "main.py"]
for folder_or_file in bot_folders_and_files:
    print(f"Copying {folder_or_file} to {fs}{sp}bot...")
    copy_anything(folder_or_file, f"{folder}{sp}bot{sp}{folder_or_file}")

print(f"Writing BOT requirements.txt to {fs}{sp}bot...")
with open(f"{folder}{sp}bot{sp}requirements.txt", "w") as f:
    f.write(bot_requirements)

print(f"Writing BOT config.py to {fs}{sp}bot...")
with open(f"{folder}{sp}bot{sp}config.py", "w") as f:
    f.write("from db.config_bot import *")

# COPY FILES/FOLDERS TO WEB SUB-FOLDER ---------------------------------------------------------------------------------
print(f"\nCOPYING FILES TO {fs}{sp}web...")
print("-"*line_length)

web_folders_and_files = ["chat_exporter", "classes", "commands", "database", "ipc", "utils", "static", "templates", "flaskapp.py", "oauth.py"]
for folder_or_file in web_folders_and_files:
    print(f"Copying {folder_or_file} to {sp}web...")
    copy_anything(folder_or_file, f"{folder}{sp}web{sp}{folder_or_file}")

print(f"Writing WEB requirements.txt to {fs}{sp}web...")
with open(f"{folder}{sp}web{sp}requirements.txt", "w") as f:
    f.write(web_requirements)

print(f"Writing WEB config.py to {fs}{sp}web...")
with open(f"{folder}{sp}web{sp}config.py", "w") as f:
    f.write("from db.config_web import *")

# COPY FILES/FOLDERS TO NGINX SUB-FOLDER -------------------------------------------------------------------------------
print(f"\nCOPYING FILES TO {fs}{sp}nginx...")
print("-"*line_length)

print(f"Copying nginx to {fs}{sp}nginx...")
copy_anything(f"docker_build{sp}nginx", f"{folder}{sp}nginx")

# COPY FILES/FOLDERS TO DB SUB-FOLDER ---------------------------------------------------------------------------------
print(f"\nCOPYING FILES TO {fs}{sp}db...")
print("-"*line_length)

print(f"Copying db to {fs}{sp}db...")
copy_anything("db", f"{folder}{sp}db")

print("Creating __init__.py...")
open(f"{folder}{sp}db{sp}__init__.py", "w").close()

print("Creating config_bot.py...")
with open(f"{folder}{sp}db{sp}config_bot.py", "w") as f:
    with open("config.py", "r") as f2:
        for line in f2:
            if "PARENT_DIR" in line:
                f.write(f"PARENT_DIR = '/bot/'\n")
                continue
            f.write(line)

print("Creating config_web.py...")
with open(f"{folder}{sp}db{sp}config_web.py", "w") as f:
    with open("config.py", "r") as f2:
        for line in f2:
            if "PARENT_DIR" in line:
                f.write(f"PARENT_DIR = '/web/'\n")
                continue
            f.write(line)

# COPY FILES FROM docker_build -----------------------------------------------------------------------------------------
print(f"\nCOPYING FILES FROM docker_build...")
print("-"*line_length)

print(f"Copying docker-compose.yml to {fs}{sp}...")
copy_anything(f"docker_build{sp}docker-compose.yml", f"{folder}{sp}docker-compose.yml")

# COPY FILES FROM docker_build/bot
bot_folders_and_files = [f"bot{sp}Dockerfile"]
for folder_or_file in bot_folders_and_files:
    print(f"Copying {folder_or_file} to {sp}bot...")
    copy_anything(f"docker_build{sp}{folder_or_file}", f"{folder}{sp}{folder_or_file}")

# COPY FILES FROM docker_build/web
web_folders_and_files = [f"web{sp}Dockerfile", f"web{sp}server.py", f"web{sp}app.ini"]
for folder_or_file in web_folders_and_files:
    print(f"Copying {folder_or_file} to {sp}web...")
    copy_anything(f"docker_build{sp}{folder_or_file}", f"{folder}{sp}{folder_or_file}")

# COPY .dockerignore
print(f"Copying .dockerignore to {fs}{sp}bot...")
copy_anything(".dockerignore", f"{folder}{sp}bot{sp}.dockerignore")
print(f"Copying .dockerignore to {fs}{sp}web...")
copy_anything(".dockerignore", f"{folder}{sp}web{sp}.dockerignore")

# COPY FILES FROM CURRENT FOLDER ---------------------------------------------------------------------------------------
print(f"\nCOPYING FILES FROM CURRENT FOLDER...")
print("-"*line_length)

folders_and_files = ["README.md", "LICENSE", ".dockerignore"]
for folder_or_file in folders_and_files:
    print(f"Copying {folder_or_file} to {sp}...")
    copy_anything(folder_or_file, f"{folder}{sp}{folder_or_file}")

# WIPE LOG FILES -------------------------------------------------------------------------------------------------------
print(f"\nWIPE LOG FILES...")
print("-"*line_length)

print("Wiping log.log...")
open(f"{folder}{sp}db{sp}log{sp}log.log", "w").close()
print("Wiping data.log...")
open(f"{folder}{sp}db{sp}log{sp}data.log", "w").close()

# DONE -----------------------------------------------------------------------------------------------------------------
print("-"*line_length)
print("\nDone!")
