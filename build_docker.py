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



# get the current folder name and path
current_folder_path = os.path.dirname(os.getcwd())
current_folder_name = os.path.basename(os.getcwd())

# create the new folder with the name of the current folder + _docker
new_folder_name = current_folder_path+ "\\" + current_folder_name + "_docker"

print("Current folder path: " + current_folder_path)
print("Current folder name: " + current_folder_name)
print("New folder name: " + new_folder_name)

# create the new folder
print("Creating new folder " + new_folder_name + "...")
os.mkdir(new_folder_name)
print("Done creating new folder " + new_folder_name)

# create the sub-folders
print("Creating sub-folders...")
print("Creating \\bot...")
os.mkdir(new_folder_name + "\\bot")
print("Creating \\web...")
os.mkdir(new_folder_name + "\\web")

# list of folders and files to copy to \\bot
bot_folders_and_files = ["chat_exporter", "classes", "commands", "dce", "ipc", "sound_effects", "utils", "web_func", "config.py", "main.py", "requirements.txt"]

# copy the folders and files to \\bot
for folder_or_file in bot_folders_and_files:
    print("Copying " + folder_or_file + " to \\bot...")
    copy_anything(folder_or_file, new_folder_name + f"\\bot\\{folder_or_file}")

# list of folders and files to copy to \\web
web_folders_and_files = ["chat_exporter", "classes", "commands", "ipc", "utils", "static", "templates", "config.py", "flaskapp.py", "oauth.py", "requirements.txt"]

# copy the folders and files to \\web
for folder_or_file in web_folders_and_files:
    print("Copying " + folder_or_file + " to \\web...")
    copy_anything(folder_or_file, new_folder_name + f"\\web\\{folder_or_file}")

# copy folder to \\nginx
print("Copying nginx to \\nginx...")
copy_anything("docker_build\\nginx", new_folder_name + "\\nginx")

# copy folder to \\db
print("Copying db to \\db...")
copy_anything("db", new_folder_name + "\\db")

# copy docker-compose.yml to new folder
print("Copying docker-compose.yml to \\...")
copy_anything("docker_build\\docker-compose.yml", new_folder_name + "\\docker-compose.yml")

# list of folders and files to copy to \\bot from docker_build
bot_folders_and_files = ["bot\\Dockerfile"]

# copy the folders and files to \\bot
for folder_or_file in bot_folders_and_files:
    print("Copying " + folder_or_file + " to \\bot...")
    copy_anything("docker_build\\" + folder_or_file, new_folder_name + f"\\{folder_or_file}")

# list of folders and files to copy to \\web from docker_build
web_folders_and_files = ["web\\Dockerfile", "web\\server.py", "web\\app.ini"]

# copy the folders and files to \\web
for folder_or_file in web_folders_and_files:
    print("Copying " + folder_or_file + " to \\web...")
    copy_anything("docker_build\\" + folder_or_file, new_folder_name + f"\\{folder_or_file}")

# copy .dockerignore to \\bot and \\web
print("Copying .dockerignore to \\bot...")
copy_anything(".dockerignore", new_folder_name + "\\bot\\.dockerignore")
print("Copying .dockerignore to \\web...")
copy_anything(".dockerignore", new_folder_name + "\\web\\.dockerignore")

# list of folders and files to copy to the new folder
folders_and_files = ["README.md", "LICENSE", ".dockerignore"]

# copy the folders and files to the new folder
for folder_or_file in folders_and_files:
    print("Copying " + folder_or_file + " to \\...")
    copy_anything(folder_or_file, new_folder_name + f"\\{folder_or_file}")

# wipe the log.log and data.log files
print("Wiping log.log...")
open(f"{new_folder_name}\\db\\log\\log.log", "w").close()
print("Wiping data.log...")
open(f"{new_folder_name}\\db\\log\\data.log", "w").close()

print("----------------------------------------")
print("\nDone!")
