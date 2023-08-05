from typing import TypedDict, Optional

class TimeSegmentInner(TypedDict):
    epoch: int | None
    time_stamp: float | None

class TimeSegment(TypedDict):
    start: TimeSegmentInner
    end: TimeSegmentInner

class RadioInfo(TypedDict):
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
