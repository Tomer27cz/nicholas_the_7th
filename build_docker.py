import os
import shutil, errno

# this script creates a new folder at the same level as the current folder
# with the name of the current folder + _docker
# it then copies the contents of the current folder into the new folder
# according to the pre-defined rules
# then it copies Dockerfiles for each of the sub-folders
# and copies a docker-compose.yml file to the new folder

# the new folder will have the following structure:
# - CURRENT-FOLDER-NAME_docker
#   - docker-compose.yml
#   - bot
#     - Dockerfile
#     - ...
#   - web
#     - Dockerfile
#     - ...
#   - nginx
#     - Dockerfile
#     - nginx.conf
#   - db
#     - ...

def copy_anything(src, dst):
    try:
        shutil.copytree(src, dst)
    except OSError as exc: # python >2.5
        if exc.errno in (errno.ENOTDIR, errno.EINVAL):
            shutil.copy(src, dst)
        else: raise


# get environment
sp = "/"
windows = False
if os.name == 'nt':
    sp = "\\"
    windows = True


# get the current folder name and path
current_folder_path = os.path.dirname(os.getcwd())
current_folder_name = os.path.basename(os.getcwd())

# create the new folder with the name of the current folder + _docker
new_folder_name = current_folder_path + sp + current_folder_name + "_docker"

print("Current folder path: " + current_folder_path)
print("Current folder name: " + current_folder_name)
print("New folder name: " + new_folder_name)

# create the new folder
print("Creating new folder " + new_folder_name + "...")
os.mkdir(new_folder_name)
print("Done creating new folder " + new_folder_name)

# create the sub-folders
print("Creating sub-folders...")
print(f"Creating {sp}bot...")
os.mkdir(new_folder_name + sp + "bot")
print(f"Creating {sp}web...")
os.mkdir(new_folder_name + sp + "web")

# list of folders and files to copy to \\bot
bot_folders_and_files = ["chat_exporter", "classes", "commands", "dce", "ipc", "sound_effects", "utils", "web_func", "config.py", "main.py", "requirements.txt"]

# copy the folders and files to \\bot
for folder_or_file in bot_folders_and_files:
    print("Copying " + folder_or_file + f" to {sp}bot...")
    copy_anything(folder_or_file, new_folder_name + f"{sp}bot{sp}{folder_or_file}")

# list of folders and files to copy to \\web
web_folders_and_files = ["chat_exporter", "classes", "commands", "ipc", "utils", "static", "templates", "config.py", "flaskapp.py", "oauth.py", "requirements.txt"]

# copy the folders and files to \\web
for folder_or_file in web_folders_and_files:
    print("Copying " + folder_or_file + f" to {sp}web...")
    copy_anything(folder_or_file, new_folder_name + f"{sp}web{sp}{folder_or_file}")

# copy folder to \\nginx
print(f"Copying nginx to {sp}nginx...")
copy_anything(f"docker_build{sp}nginx", new_folder_name + f"{sp}nginx")

# copy folder to \\db
print(f"Copying db to {sp}db...")
copy_anything("db", new_folder_name + f"{sp}db")

# copy docker-compose.yml to new folder
print(f"Copying docker-compose.yml to {sp}...")
copy_anything(f"docker_build{sp}docker-compose.yml", new_folder_name + f"{sp}docker-compose.yml")

# list of folders and files to copy to \\bot from docker_build
bot_folders_and_files = [f"bot{sp}Dockerfile"]

# copy the folders and files to \\bot
for folder_or_file in bot_folders_and_files:
    print("Copying " + folder_or_file + f" to {sp}bot...")
    copy_anything(f"docker_build{sp}" + folder_or_file, new_folder_name + f"{sp}{folder_or_file}")

# list of folders and files to copy to \\web from docker_build
web_folders_and_files = [f"web{sp}Dockerfile", f"web{sp}server.py", f"web{sp}app.ini"]

# copy the folders and files to \\web
for folder_or_file in web_folders_and_files:
    print(f"Copying " + folder_or_file + f" to {sp}web...")
    copy_anything(f"docker_build{sp}" + folder_or_file, new_folder_name + f"{sp}{folder_or_file}")

# copy .dockerignore to \\bot and \\web
print(f"Copying .dockerignore to {sp}bot...")
copy_anything(".dockerignore", new_folder_name + f"{sp}bot{sp}.dockerignore")
print(f"Copying .dockerignore to {sp}web...")
copy_anything(".dockerignore", new_folder_name + f"{sp}web{sp}.dockerignore")

# list of folders and files to copy to the new folder
folders_and_files = ["README.md", "LICENSE", ".dockerignore"]

# copy the folders and files to the new folder
for folder_or_file in folders_and_files:
    print("Copying " + folder_or_file + f" to {sp}...")
    copy_anything(folder_or_file, new_folder_name + f"{sp}{folder_or_file}")

# wipe the log.log and data.log files
print("Wiping log.log...")
open(f"{new_folder_name}{sp}db{sp}log{sp}log.log", "w").close()
print("Wiping data.log...")
open(f"{new_folder_name}{sp}db{sp}log{sp}data.log", "w").close()

print("----------------------------------------")
print("\nDone!")
