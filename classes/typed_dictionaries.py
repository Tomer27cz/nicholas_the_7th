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

# ----------------------------------------------- youtubesearchpython --------------------------------------------------

class v_viewCount(TypedDict):
    text: str
    short: str

class v_thumbnails(TypedDict):
    url: str
    width: int
    height: int

class v_richThumbnail(TypedDict):
    url: str
    width: int
    height: int

class v_descriptionSnippet(TypedDict):
    text: str

class v_channel(TypedDict):
    name: str
    id: str
    thumbnails: list[v_thumbnails]
    link: str

class v_accessibility(TypedDict):
    title: str
    duration: str

class VideoInfo(TypedDict):
    type: str
    id: str
    title: str
    publishedTime: str
    duration: str
    viewCount: v_viewCount
    thumbnails: list[v_thumbnails]
    richThumbnail: v_richThumbnail
    descriptionSnippet: list[v_descriptionSnippet]
    channel: v_channel
    accessibility: v_accessibility
    link: str
    shelfTitle: Optional[str]
