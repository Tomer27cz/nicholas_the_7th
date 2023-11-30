from typing import TypedDict, Optional, Union

class TimeSegmentInner(TypedDict):
    epoch: Union[None, int]
    time_stamp: Union[None, int]

class TimeSegment(TypedDict):
    start: TimeSegmentInner
    end: TimeSegmentInner

class RadioInfoDict(TypedDict):
    name: str
    website: Optional[str]
    picture: Optional[str]
    channel_name: Optional[str]
    title: Optional[str]

class DiscordChannelInfo(TypedDict):
    id: int
    name: str

class VideoChapter(TypedDict):
    start_time: float
    title: str
    end_time: float
