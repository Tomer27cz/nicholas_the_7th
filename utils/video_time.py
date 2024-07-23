from __future__ import annotations
from typing import TYPE_CHECKING, Union
if TYPE_CHECKING:
    from classes.typed_dictionaries import TimeSegment, TimeSegmentInner, VideoChapter, VideoHeatMap
    from utils.global_vars import GlobalVars

import classes.video_class as video_class
import database.guild as db
from utils.save import update, push_update

from time import time

def set_stopped(glob: GlobalVars, video):
    """
    Sets the time when the video was stopped
    :param glob: GlobalVars
    :param video: Video object
    """
    last_segment: TimeSegment = video.played_duration[-1]
    start = last_segment['start']
    end = last_segment['end']

    end['epoch'] = int(time())

    video.played_duration[-1]['end']['time_stamp'] = (end['epoch'] - start['epoch']) + start['time_stamp']
    pd = video.played_duration

    if video.__class__.__name__ == 'NowPlaying':
        # for some reason this needs to be done like this
        glob.ses.commit()
        if db.guild(glob, guild_id=video.guild_id).now_playing is not None:
            db.guild(glob, guild_id=video.guild_id).now_playing.played_duration = pd
        glob.ses.commit()

    update(glob)

async def set_started(glob: GlobalVars, video, guild_object, chapters: list[VideoChapter]=None, heatmap: list[VideoHeatMap]=None, subtitles=None, captions=None, no_push: bool=False):
    """
    Sets the time when the video was started
    :param glob: GlobalVars
    :param video: Video object
    :param guild_object: Guild object
    :param chapters: list[VideoChapter] - list of chapters
    :param heatmap: list[VideoHeatMap] - list of heatmaps
    :param subtitles: dict - list of subtitles
    :param captions: dict - list of captions
    :param no_push: bool - if True, does not push the update to the guild
    """
    if len(video.played_duration) == 0:
        assert video.played_duration == []
        video.played_duration += [
            {'start': {'epoch': None, 'time_stamp': None}, 'end': {'epoch': None, 'time_stamp': None}}]

    video.played_duration[-1]['start']['epoch'] = int(time())
    video.played_duration[-1]['start']['time_stamp'] = 0.0

    if chapters:
        video.chapters = chapters

    if heatmap:
        video.heatmap = heatmap

    if subtitles:
        video.subtitles = subtitles

    if captions:
        video.captions = captions

    try:
        video.discord_channel = {"id": guild_object.voice_client.channel.id,
                                 "name": guild_object.voice_client.channel.name}
    except AttributeError:
        pass

    guild_id = guild_object.id
    db.guild(glob, guild_id).now_playing = await video_class.to_now_playing_class(glob, video)
    glob.ses.commit()

    if not no_push:
        await push_update(glob, guild_id, ['queue', 'now'])

    update(glob)

def set_resumed(glob: GlobalVars, video):
    """
    Sets the time when the video was resumed
    :param glob: GlobalVars
    :param video: Video object
    """
    start_dict = {'epoch': int(time()), 'time_stamp': video.played_duration[-1]['end']['time_stamp']}
    end_dict = {'epoch': None, 'time_stamp': None}

    video.played_duration += [{'start': start_dict, 'end': end_dict}]
    pd = video.played_duration

    # for some reason this needs to be done like this
    glob.ses.commit()
    db.guild(glob, guild_id=video.guild_id).now_playing.played_duration = pd
    glob.ses.commit()

    update(glob)

def set_new_time(glob: GlobalVars, video, time_stamp: int):
    """
    Sets the time when the video was started
    :param glob: GlobalVars
    :param video: Video object
    :param time_stamp: int - new time stamp
    """
    if video.played_duration[-1]['end']['epoch'] is None:
        set_stopped(glob, video)

    start_dict = {'epoch': int(time()), 'time_stamp': time_stamp}
    end_dict = {'epoch': None, 'time_stamp': None}

    video.played_duration += [{'start': start_dict, 'end': end_dict}]
    pd = video.played_duration

    # for some reason this needs to be done like this
    glob.ses.commit()
    db.guild(glob, guild_id=video.guild_id).now_playing.played_duration = pd
    glob.ses.commit()

    update(glob)

def video_time_from_start(video) -> float:
    """
    Returns the time from the start of the video
    @param video: Video object
    @return: float - time from the start of the video
    """
    if len(video.played_duration) == 0:
        return 0.0

    segment: TimeSegment = video.played_duration[-1]
    start: TimeSegmentInner = segment['start']
    end: TimeSegmentInner = segment['end']

    if end['epoch'] is not None:
        return end['time_stamp']

    # edge case
    if start['epoch'] is None:
        return 0.0

    # time_stamp case - when the video was paused --///--
    return (int(time()) - start['epoch']) + start['time_stamp']
