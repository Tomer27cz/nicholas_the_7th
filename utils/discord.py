from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from classes.data_classes import ReturnData
    from utils.global_vars import GlobalVars

from classes.video_class import *
from classes.data_classes import *

from utils.convert import struct_to_time
from utils.translate import tg
from utils.video_time import set_stopped
from utils.save import save_json, push_update
from database.guild import guild, get_radio_info

import discord
from time import time

from config import WEB_URL


def get_voice_client(iterable, **attrs) -> discord.VoiceClient:
    """
    Gets voice_client from voice_clients list
    :param iterable: list
    :return: discord.VoiceClient
    """
    from operator import attrgetter

    # noinspection PyShadowingNames
    def _get(iterable, /, **attrs):
        # global -> local
        _all = all
        attrget = attrgetter

        # Special case the single element call
        if len(attrs) == 1:
            k, v = attrs.popitem()
            pred = attrget(k.replace('__', '.'))
            return next((elem for elem in iterable if pred(elem) == v), None)

        converted = [(attrget(attr.replace('__', '.')), value) for attr, value in attrs.items()]
        for elem in iterable:
            if _all(pred(elem) == value for pred, value in converted):
                return elem
        return None

    # noinspection PyShadowingNames
    async def _aget(iterable, /, **attrs):
        # global -> local
        _all = all
        attrget = attrgetter

        # Special case the single element call
        if len(attrs) == 1:
            k, v = attrs.popitem()
            pred = attrget(k.replace('__', '.'))
            async for elem in iterable:
                if pred(elem) == v:
                    return elem
            return None

        converted = [(attrget(attr.replace('__', '.')), value) for attr, value in attrs.items()]

        async for elem in iterable:
            if _all(pred(elem) == value for pred, value in converted):
                return elem
        return None


    return (
        _aget(iterable, **attrs)  # type: ignore
        if hasattr(iterable, '__aiter__')  # isinstance(iterable, collections.abc.AsyncIterable) is too slow
        else _get(iterable, **attrs)  # type: ignore
    )

def create_embed(glob: GlobalVars, video, name: str, guild_id: int, embed_colour: (int, int, int) = (88, 101, 242)) -> discord.Embed:
    """
    Creates embed with video info
    :param video: VideoClass child
    :param glob: GlobalVars object
    :param name: str - title of embed
    :param guild_id: id of guild the embed is created for
    :param embed_colour: (int, int, int) - rgb colour of embed default: (88, 101, 242) -> #5865F2 == discord.Color.blurple()
    :return: discord.Embed
    """
    try:
        requested_by = glob.bot.get_user(video.author).mention
    except AttributeError:
        requested_by = video.author
    # set variables
    title = video.title
    time_played = video.time(glob)
    author = f'[{video.channel_name}]({video.channel_link})'
    current_chapter = video.current_chapter(glob)
    url = video.url
    thumbnail = video.picture

    if video.radio_info is not None:
        radio_info_class = get_radio_info(glob, video.radio_info['name'])
        title = radio_info_class.title
        author = f'[{radio_info_class.channel_name}]({video.channel_link})'
        thumbnail = radio_info_class.picture

    started_at = struct_to_time(video.played_duration[0]["start"]["epoch"], "time")
    requested_at = struct_to_time(video.created_at, "time")

    # Create embed
    embed = (discord.Embed(title=name, description=f'```\n{title}\n```', color=discord.Color.from_rgb(*embed_colour)))

    embed.add_field(name=tg(guild_id, 'Duration'), value=time_played)
    embed.add_field(name=tg(guild_id, 'Requested by'), value=f"<@{requested_by}>")
    embed.add_field(name=tg(guild_id, 'Author'), value=author)

    if current_chapter is not None:
        embed.add_field(name=tg(guild_id, 'Chapter'), value=current_chapter)

    embed.add_field(name=tg(guild_id, 'URL'), value=url, inline=False)

    embed.set_thumbnail(url=thumbnail)
    embed.set_footer(text=f'{tg(guild_id, "Requested at")} {requested_at} | {tg(guild_id, "Started playing at")} {started_at}')

    return embed

def now_to_history(glob: GlobalVars, guild_id: int):
    """
    Adds now_playing to history
    Removes first element of history if history length is more than options.history_length

    :param glob: GlobalVars object
    :param guild_id: int - id of guild
    :return: None
    """

    guild_object = guild(glob, guild_id)

    if guild_object.now_playing is not None:
        # trim history
        if len(guild_object.history) >= guild_object.options.history_length:
            while len(guild_object.history) >= guild_object.options.history_length:
                guild_object.history.pop(0)

        np_video = guild_object.now_playing

        # if loop is enabled and video is Radio class, add video to queue
        if guild_object.options.loop:
            to_queue(glob, guild_id, np_video, position=None, copy_video=True)

        # to history class (before delete - bug fix)
        h_video = to_history_class(glob, np_video)

        # set now_playing to None
        glob.ses.query(NowPlaying).filter(NowPlaying.guild_id == guild_id).delete()
        glob.ses.commit()

        # strip not needed data
        set_stopped(glob, h_video)
        h_video.chapters = None

        # add video to history
        guild_object.history.append(to_history_class(glob, h_video))

        # save json and push update
        save_json(glob)
        push_update(glob, guild_id)

def to_queue(glob: GlobalVars, guild_id: int, video, position: int = None, copy_video: bool=True, no_push: bool=False) -> ReturnData or None:
    """
    Adds video to queue

    if return_message is True returns: [bool, str, VideoClass child]

    :param glob: GlobalVars object
    :param guild_id: id of guild: int
    :param video: VideoClass child
    :param position: int - position in queue to add video
    :param copy_video: bool - if True copies video
    :param no_push: bool - if True doesn't push update
    :return: ReturnData or None
    """
    guild_object = guild(glob, guild_id)

    if copy_video:
        video = to_queue_class(glob, video)

    # strip video of time data
    video.played_duration = [{'start': {'epoch': None, 'time_stamp': None}, 'end': {'epoch': None, 'time_stamp': None}}]
    # strip video of discord channel data
    video.discord_channel = {"id": None, "name": None}
    # strip video of stream url
    video.stream_url = None
    # set new creation date
    video.created_at = int(time())

    if position is None:
        guild_object.queue.append(to_queue_class(glob, video))
    else:
        guild_object.queue.insert(position, to_queue_class(glob, video))

    if not no_push:
        push_update(glob, guild_id)
    save_json(glob)

    return f'[`{video.title}`](<{video.url}>) {tg(guild_id, "added to queue!")} -> [Control Panel]({WEB_URL}/guild/{guild_id}&key={guild_object.data.key})'

def get_content_of_message(glob: GlobalVars, message: discord.Message) -> (str, list or None):
    """
    Returns content of message

    if message has attachments returns url of first attachment and list with filename, author and link of message

    if message has embeds returns str representation of first embed without thumbnail and None

    if message has embeds and content returns content of message and None

    :param glob: GlobalVars object
    :param message: message: discord.Message
    :return: content: str, probe_data: list or None
    """
    if message.attachments:
        url = message.attachments[0].url
        filename = message.attachments[0].filename
        message_author = f"Message by {get_username(glob, message.author.id)}"
        message_link = message.jump_url
        probe_data = [filename, message_author, message_link]
    elif message.embeds:
        if message.content:
            url = message.content
            probe_data = None
        else:
            embed = message.embeds[0]
            embed_dict = embed.to_dict()
            embed_dict.pop('thumbnail')
            embed_str = str(embed_dict)
            url = embed_str
            probe_data = None
    else:
        url = message.content
        probe_data = None

    return url, probe_data

def get_username(glob: GlobalVars, user_id: int) -> str:
    """
    Returns username of user_id with bot.get_user

    if can't find user returns str(user_id)

    :param glob: GlobalVars object
    :param user_id: id of user
    :return: str - username of user_id or str(user_id)
    """
    # noinspection PyBroadException
    try:
        return glob.bot.get_user(int(user_id)).name
    except:
        return str(user_id)