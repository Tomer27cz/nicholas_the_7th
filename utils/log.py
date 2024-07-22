from __future__ import annotations
from typing import TYPE_CHECKING, Union
if TYPE_CHECKING:
    from classes.data_classes import WebData
    from utils.global_vars import GlobalVars

from utils.convert import struct_to_time

import classes.data_classes as data_classes

from time import time
from io import BytesIO
from typing import Literal
from discord.ext import commands as dc_commands
import discord
import logging
import sys
import os

from config import OWNER_ID

# ---------------- Create Loggers ------------

# Check if inside docker
inside_docker = True if os.environ.get('INSIDE_DOCKER', False) in ['True', 'true'] else False

# Formatters
formatter = logging.Formatter('%(asctime)s.%(msecs)03d | %(name)s | %(message)s', datefmt='%d/%m/%Y %H:%M:%S')

# Print handler
print_handler = logging.StreamHandler(sys.stdout)
print_handler.setLevel(logging.INFO)
print_handler.setFormatter(formatter)

# File handlers
file_handler = logging.FileHandler('logs/bot_logger.log', encoding='utf-8')
file_handler.setLevel(logging.INFO)
file_handler.setFormatter(formatter)
web_handler = logging.FileHandler('logs/web_logger.log', encoding='utf-8')
web_handler.setLevel(logging.INFO)
web_handler.setFormatter(formatter)

# Main logger
main_logger = logging.getLogger('main')
main_logger.setLevel(logging.INFO)
main_logger.addHandler(print_handler)
if not inside_docker:
    main_logger.addHandler(file_handler)

# Web logger
web_logger = logging.getLogger('web')
web_logger.setLevel(logging.INFO)
web_logger.addHandler(print_handler)
if not inside_docker:
    web_logger.addHandler(web_handler)

# logging.basicConfig(filename='logs/log.log', level=logging.INFO, format='%(asctime)s | %(levelname)s | %(message)s')

def log(ctx: Union[dc_commands.Context, WebData, None, int], text_data, options: dict=None, log_type: Literal['command', 'function', 'web', 'text', 'ip', 'error', 'warning']='text', author=None) -> None:
    """
    Logs data to the console and to the log file
    :param ctx: dc_commands.Context or WebData or guild_id
    :param text_data: The data to be logged
    :param options: dict - options to be logged from command
    :param log_type: ('command', 'function', 'web', 'text', 'ip') - type of log
    :param author: Author of the command
    :return: None
    """
    def readable_dict(_dict: dict) -> str:
        if not _dict:
            return ''
        ignored_keys = ['ctx', 'glob', 'web_data']

        out_str = ''
        for _key, _value in _dict.items():
            if _key in ignored_keys:
                continue

            if isinstance(_value, str):
                out_str += f"{_key}='{_value}', "
                continue

            out_str += f"{_key}={_value}, "

        return out_str[:-2]

    if isinstance(ctx, dc_commands.Context):
        if ctx.guild is None:
            guild_id = 'Other'
        else:
            guild_id = ctx.guild.id
    elif ctx.__class__.__name__ == 'WebData':
        guild_id = f'WD{ctx.guild_id}'
    else:
        guild_id = ctx

    match log_type:
        case 'command':
            message = f"CMD  {guild_id} | {text_data} by ({author}) -> {readable_dict(options)}"
            logging.getLogger('main').info(message)
            return
        case 'function':
            message = f"FUNC {guild_id} | {text_data} -> {readable_dict(options)}"
            logging.getLogger('main').info(message)
            return
        case 'web':
            message = f"WEB  {guild_id} | Command ({text_data}) was requested by ({author}) -> {readable_dict(options)}"
            logging.getLogger('web').info(message)
            return
        case 'text':
            message = f"TXT  {guild_id} | {text_data}"
            logging.getLogger('main').info(message)
            return
        case 'ip':
            message = f"IP   {guild_id} | Requested: {text_data}"
            logging.getLogger('web').info(message)
            return
        case 'error':
            message = f"ERR  {guild_id} | {text_data} -> {options}"
            logging.getLogger('main').error(message)
            return
        case 'warning':
            message = f"WRN  {guild_id} | {text_data} -> {options}"
            logging.getLogger('main').warning(message)
            return
        case _:
            raise ValueError('Wrong log_type')

def tl(glob: GlobalVars, log_type: int, guild_id: int=None, channel_id: int=None) -> None:
    """
    Logs the time of the event

    |BOT|
    0 = bot started,

    |VC|
    1 = joined VC,
    2 = left VC,

    |PLAY|
    3 = started playing,
    4 = un-paused,
    5 = bot stopped playing,
    6 = paused,

    |GUILD|
    7 = guild joined,
    8 = guild left,

    |COUNT|
    9 = command,
    10 = song played,
    11 = skipped,
    12 = error,

    :param glob: GlobalVars object
    :param log_type: int - type of log
    :param guild_id: int - guild_id (optional)
    :param channel_id: int - channel_id (optional)
    """
    glob.ses.add(data_classes.TimeLog(log_type=log_type, guild_id=guild_id, channel_id=channel_id))
    glob.ses.commit()

def collect_data(data) -> None:
    """
    Collects data to the data.log file
    :param data: data to be collected
    :return: None
    """
    now_time_str = struct_to_time(time())
    message = f"{now_time_str} | {data}\n"

    with open(f'logs/data.log', "a", encoding="utf-8") as f:
        f.write(message)

async def send_to_admin(glob: GlobalVars, data, file=False) -> None:
    """
    Sends data to admin
    :param glob: GlobalVars object
    :param data: str - data to send
    :param file: bool - if data should be sent as a file
    :return: None
    """
    admin = glob.bot.get_user(OWNER_ID)
    developer = glob.bot.get_user(349164237605568513)

    # if length of data is more than 2000 symbols send a file
    if len(data) > 2000 or file:
        file_to_send = discord.File(BytesIO(data.encode()), filename='data.txt')
        if admin is not None:
            await admin.send(file=file_to_send)

        # send to developer if OWNER_ID is not developer
        if OWNER_ID != 349164237605568513:
            file_to_send = discord.File(BytesIO(data.encode()), filename='data.txt')
            await developer.send(file=file_to_send)
        return

    # send to developer if OWNER_ID is not developer
    if OWNER_ID != 349164237605568513:
        await developer.send(data)

    if admin is not None:
        await admin.send(data)
