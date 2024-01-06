from __future__ import annotations
from typing import TYPE_CHECKING, Union
if TYPE_CHECKING:
    from classes.data_classes import WebData
    from utils.global_vars import GlobalVars

from utils.convert import struct_to_time
from config import PARENT_DIR, OWNER_ID

from time import time
from io import BytesIO
from typing import Literal
import sys

import discord
from discord.ext import commands as dc_commands

def log(ctx: Union[dc_commands.Context, WebData, None, int], text_data, options=None, log_type: Literal['command', 'function', 'web', 'text', 'ip', 'error']='text', author=None) -> None:
    """
    Logs data to the console and to the log file
    :param ctx: dc_commands.Context or WebData or guild_id
    :param text_data: The data to be logged
    :param options: list - options to be logged from command
    :param log_type: ('command', 'function', 'web', 'text', 'ip') - type of log
    :param author: Author of the command
    :return: None
    """
    now_time_str = struct_to_time(time())

    try:
        guild_id = ctx.guild.id
    except AttributeError:
        try:
            guild_id = ctx.guild_id
        except AttributeError:
            guild_id = ctx

    if log_type == 'command':
        message = f"{now_time_str} | C {guild_id} | Command ({text_data}) was requested by ({author}) -> {options}"
    elif log_type == 'function':
        message = f"{now_time_str} | F {guild_id} | {text_data} -> {options}"
    elif log_type == 'web':
        message = f"{now_time_str} | W {guild_id} | Command ({text_data}) was requested by ({author}) -> {options}"
    elif log_type == 'text':
        message = f"{now_time_str} | T {guild_id} | {text_data}"
    elif log_type == 'ip':
        message = f"{now_time_str} | I {guild_id} | Requested: {text_data}"
    elif log_type == 'error':
        message = f"{now_time_str} | E {guild_id} | {text_data} -> {options}"
    else:
        raise ValueError('Wrong log_type')

    if log_type == 'error':
        print(message, file=sys.stderr, flush=True)
    else:
        print(message, flush=True)

    with open(f"{PARENT_DIR}db/log/log.log", "a", encoding="utf-8") as f:
        f.write(message + "\n")

def collect_data(data) -> None:
    """
    Collects data to the data.log file
    :param data: data to be collected
    :return: None
    """
    now_time_str = struct_to_time(time())
    message = f"{now_time_str} | {data}\n"

    with open(f'{PARENT_DIR}db/log/data.log', "a", encoding="utf-8") as f:
        f.write(message)

async def send_to_admin(glob: GlobalVars, data):
    """
    Sends data to admin
    :param glob: GlobalVars object
    :param data: str - data to send
    :return: None
    """
    admin = glob.bot.get_user(OWNER_ID)
    developer = glob.bot.get_user(349164237605568513)

    # if length of data is more than 2000 symbols send a file
    if len(data) > 2000:
        file_to_send = discord.File(BytesIO(data.encode()), filename='data.txt')
        await admin.send(file=file_to_send)

        # send to developer if OWNER_ID is not developer
        if OWNER_ID != 349164237605568513:
            file_to_send = discord.File(BytesIO(data.encode()), filename='data.txt')
            await developer.send(file=file_to_send)
        return

    # send to developer if OWNER_ID is not developer
    if OWNER_ID != 349164237605568513:
        await developer.send(data)

    await admin.send(data)
