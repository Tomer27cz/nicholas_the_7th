from __future__ import annotations
from typing import TYPE_CHECKING, Union
if TYPE_CHECKING:
    from classes.video_class import VideoClass
    from classes.typed_dictionaries import TimeSegment, TimeSegmentInner, VideoChapter

import classes.video_class as video_class
import database.guild as db
from utils.save import save_json
from utils.globals import get_session

from time import time

def set_stopped(video: VideoClass):
    last_segment: TimeSegment = video.played_duration[-1]
    start = last_segment['start']
    end = last_segment['end']

    end['epoch'] = int(time())

    video.played_duration[-1]['end']['time_stamp'] = (end['epoch'] - start['epoch']) + start['time_stamp']
    pd = video.played_duration

    # for some reason this needs to be done like this
    get_session().commit()
    if db.guild(guild_id=video.guild_id).now_playing is not None:
        db.guild(guild_id=video.guild_id).now_playing.played_duration = pd
    get_session().commit()

    save_json()

def set_started(video: VideoClass, guild_object, chapters: Union[list[VideoChapter], None]= None):
    if len(video.played_duration) == 0:
        assert video.played_duration == []
        video.played_duration += [
            {'start': {'epoch': None, 'time_stamp': None}, 'end': {'epoch': None, 'time_stamp': None}}]

    video.played_duration[-1]['start']['epoch'] = int(time())
    video.played_duration[-1]['start']['time_stamp'] = 0.0

    if chapters:
        video.chapters = chapters

    try:
        video.discord_channel = {"id": guild_object.voice_client.channel.id,
                                 "name": guild_object.voice_client.channel.name}
    except AttributeError:
        pass

    guild_id = guild_object.id
    db.guild(guild_id).now_playing = video_class.to_now_playing_class(video)
    get_session().commit()

    save_json()

def set_resumed(video: VideoClass):
    start_dict = {'epoch': int(time()), 'time_stamp': video.played_duration[-1]['end']['time_stamp']}
    end_dict = {'epoch': None, 'time_stamp': None}

    video.played_duration += [{'start': start_dict, 'end': end_dict}]
    pd = video.played_duration

    # for some reason this needs to be done like this
    get_session().commit()
    db.guild(guild_id=video.guild_id).now_playing.played_duration = pd
    get_session().commit()

    save_json()

def set_new_time(video: VideoClass, time_stamp: int):
    if video.played_duration[-1]['end']['epoch'] is None:
        set_stopped(video)

    start_dict = {'epoch': int(time()), 'time_stamp': time_stamp}
    end_dict = {'epoch': None, 'time_stamp': None}

    video.played_duration += [{'start': start_dict, 'end': end_dict}]
    pd = video.played_duration

    # for some reason this needs to be done like this
    get_session().commit()
    db.guild(guild_id=video.guild_id).now_playing.played_duration = pd
    get_session().commit()

    save_json()

def video_time_from_start(video) -> float:
    len_played_duration = len(video.played_duration)
    if len_played_duration == 0:
        return 0.0

    if len_played_duration == 1:
        segment: TimeSegment = video.played_duration[0]
        start: Union[None, int] = segment['start']['epoch']
        end: Union[None, int] = segment['end']['epoch']

        if start is None:
            return 0.0

        if end is None:
            return int(time()) - start

        return segment['end']['time_stamp']

    segment: TimeSegment = video.played_duration[-1]
    start: TimeSegmentInner = segment['start']
    end: TimeSegmentInner = segment['end']

    if end['epoch'] is not None:
        return end['time_stamp']

    return (int(time()) - start['epoch']) + start['time_stamp']