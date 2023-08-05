import classes.discord_classes

import os
from pathlib import Path
import json

from config import PARENT_DIR

def getReadableByteSize(num, suffix='B', relPath=None) -> str:
    if num is None or num == 0:
        try:
            num = getFolderSize(relPath)
        except (FileNotFoundError, TypeError, PermissionError):
            pass

    for unit in ['', 'K', 'M', 'G', 'T', 'P', 'E', 'Z']:
        if abs(num) < 1024.0:
            return "%3.1f%s%s" % (num, unit, suffix)
        num /= 1024.0
    return "%.1f%s%s" % (num, 'Y', suffix)

def getIconClassForFilename(fName) -> str:
    fileExt = Path(fName).suffix
    fileExt = fileExt[1:] if fileExt.startswith(".") else fileExt
    fileTypes = ["aac", "ai", "bmp", "cs", "css", "csv", "doc", "docx", "exe", "gif", "heic", "html", "java", "jpg",
                 "js", "json", "jsx", "key", "m4p", "md", "mdx", "mov", "mp3",
                 "mp4", "otf", "pdf", "php", "png", "pptx", "psd", "py", "raw", "rb", "sass", "scss", "sh", "sql",
                 "svg", "tiff", "tsx", "ttf", "txt", "wav", "woff", "xlsx", "xml", "yml"]
    fileIconClass = f"bi bi-filetype-{fileExt}" if fileExt in fileTypes else "bi bi-file-earmark"
    return fileIconClass

def getFolderSize(relPath) -> int:
    totalSize = 0
    for dirpath, dirnames, filenames in os.walk(relPath):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            totalSize += os.path.getsize(fp)
    return totalSize

def get_guild_text_channels_file(guild_id: int):
    path = f'{PARENT_DIR}db/guilds/{guild_id}/channels.json'
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        if data:
            channel_list = []
            for channel_id, channel_data in data.items():
                channel_class = classes.discord_classes.DiscordChannel(0)
                channel_class.__dict__ = channel_data
                channel_list.append(channel_class)
            return channel_list
    return None