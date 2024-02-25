from utils.global_vars import GlobalVars

import classes.discord_classes

from pathlib import Path
import os
import json

from config import PARENT_DIR

def get_readable_byte_size(num, suffix='B', rel_path=None) -> str:
    if num is None or num == 0:
        try:
            num = get_folder_size(rel_path)
        except (FileNotFoundError, TypeError, PermissionError):
            pass

    for unit in ['', 'K', 'M', 'G', 'T', 'P', 'E', 'Z']:
        if abs(num) < 1024.0:
            return "%3.1f%s%s" % (num, unit, suffix)
        num /= 1024.0
    return "%.1f%s%s" % (num, 'Y', suffix)

def get_icon_class_for_filename(f_name) -> str:
    file_ext = Path(f_name).suffix
    file_ext = file_ext[1:] if file_ext.startswith(".") else file_ext
    file_types = ["aac", "ai", "bmp", "cs", "css", "csv", "doc", "docx", "exe", "gif", "heic", "html", "java", "jpg",
                  "js", "json", "jsx", "key", "m4p", "md", "mdx", "mov", "mp3",
                  "mp4", "otf", "pdf", "php", "png", "pptx", "psd", "py", "raw", "rb", "sass", "scss", "sh", "sql",
                  "svg", "tiff", "tsx", "ttf", "txt", "wav", "woff", "xlsx", "xml", "yml"]
    file_icon_class = f"bi bi-filetype-{file_ext}" if file_ext in file_types else "bi bi-file-earmark"
    return file_icon_class

def get_folder_size(rel_path) -> int:
    total_size = 0
    for dirpath, dirnames, filenames in os.walk(rel_path):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            total_size += os.path.getsize(fp)
    return total_size

def get_guild_text_channels_file(glob: GlobalVars, guild_id: int):
    path = f'{PARENT_DIR}db/guilds/{guild_id}/channels.json'
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        if data:
            channel_list = []
            for channel_id, channel_data in data.items():
                channel_class = classes.discord_classes.DiscordChannel(glob, 0, json_data=channel_data)
                channel_list.append(channel_class)
            return channel_list
    return None

def get_log_files():
    log_files = []
    for file in os.listdir(f"{PARENT_DIR}db/log"):
        log_files.append(file)
    return log_files
