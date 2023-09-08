import os

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

# get the current folder name and path
current_folder_path = os.path.dirname(os.getcwd())
current_folder_name = os.path.basename(os.getcwd())

# create the new folder with the name of the current folder + _docker
new_folder_name = current_folder_path+ "\\" + current_folder_name + "_docker_test"

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
    os.system(f"powershell cp -r '{folder_or_file}' '{new_folder_name}\\bot'")
    print("Done copying " + folder_or_file + " to \\bot")

# list of folders and files to copy to \\web
web_folders_and_files = ["chat_exporter", "classes", "commands", "ipc", "utils", "static", "templates", "docker_build\\web\\app.ini", "config.py", "flaskapp.py", "oauth.py", "requirements.txt", "docker_build\\web\\server.py"]

# copy the folders and files to \\web
for folder_or_file in web_folders_and_files:
    print("Copying " + folder_or_file + " to \\web...")
    os.system(f"powershell cp -r '{folder_or_file}' '{new_folder_name}\\web'")
    print("Done copying " + folder_or_file + " to \\web")

# copy folder to \\nginx
print("Copying nginx to \\nginx...")
os.system("powershell cp -r docker_build\\nginx '" + new_folder_name + "'")
print("Done copying nginx to \\nginx")

# copy folder to \\db
print("Copying db to \\db...")
os.system("powershell cp -r db '" + new_folder_name + "'")
print("Done copying db to \\db")

# copy docker-compose.yml to new folder
print("Copying docker-compose.yml to \\...")
os.system("powershell cp docker_build\\docker-compose.yml '" + new_folder_name + "'")
print("Done copying docker-compose.yml to \\")

# copy Dockerfile to \\bot
print("Copying Dockerfile to \\bot...")
os.system("powershell cp docker_build\\bot\\Dockerfile '" + new_folder_name + "\\bot'")
print("Done copying Dockerfile to \\bot")

# copy Dockerfile to \\web
print("Copying Dockerfile to \\web...")
os.system("powershell cp docker_build\\web\\Dockerfile '" + new_folder_name + "\\web'")
print("Done copying Dockerfile to \\web")

# copy .dockerignore to \\bot and \\web
print("Copying .dockerignore to \\bot...")
os.system("powershell cp .dockerignore '" + new_folder_name + "\\bot'")
print("Done copying .dockerignore to '\\bot'")
print("Copying .dockerignore to \\web...")
os.system("powershell cp .dockerignore '" + new_folder_name + "\\web'")
print("Done copying .dockerignore to '\\web'")

# copy README.md, LICENSE, and .dockerignore to new folder
print("Copying README.md, LICENSE, and .dockerignore to \\...")
print("Copying README.md...")
os.system("powershell cp README.md '" + new_folder_name + "'")
print("Copying LICENSE...")
os.system("powershell cp LICENSE '" + new_folder_name + "'")
print("Copying .dockerignore...")
os.system("powershell cp .dockerignore '" + new_folder_name + "'")
print("Done copying README.md, LICENSE, and .dockerignore to " + new_folder_name)

# wipe the log.log and data.log files
print("Wiping log.log and data.log...")
print("Wiping log.log...")
open(f"{new_folder_name}\\db\\log\\log.log", "w").close()
print("Wiping data.log...")
open(f"{new_folder_name}\\db\\log\\data.log", "w").close()
print("Done wiping log.log and data.log")

print("----------------------------------------")
print("\nDone!")
