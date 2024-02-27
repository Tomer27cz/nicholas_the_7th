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

# ------------------------------------------- Radio Garden Channel -----------------------------------------------------

example_rgc_response = {
  "apiVersion": 1,
  "version": "9bd5454",
  "data": {
    "id": "vbFsCngB",
    "title": "KUTX FM 98.9",
    "url": "/listen/kutx-98-9/vbFsCngB",
    "website": "http://www.kutx.org",
    "secure": True,
    "place": {
      "id": "Aq7xeIiB",
      "title": "Austin TX"
    },
    "country": {
      "id": "GhDXw4EW",
      "title": "United States"
    }
  }
}

class rgc_place(TypedDict):
    id: str
    title: str

class rgc_country(TypedDict):
    id: str
    title: str

class rgc_data(TypedDict):
    id: str
    title: str
    url: str
    website: str
    secure: bool
    place: rgc_place
    country: rgc_country

class RadioGardenChannel(TypedDict):
    apiVersion: int
    version: str
    data: rgc_data

# -------------------------------------------- Radio Garden Info -------------------------------------------------------

class RadioGardenInfo(TypedDict):
    id: str
    title: str
    url: str
    website: str
    stream: str
    place: rgc_place
    country: rgc_country

# ------------------------------------------- Radio Garden Place -------------------------------------------------------

example_rgp_response = {
  "apiVersion": 1,
  "version": "9bd5454",
  "data": {
    "title": "Austin TX",
    "subtitle": "All Stations",
    "url": "/visit/austin-tx/Aq7xeIiB/channels",
    "map": "Aq7xeIiB",
    "count": 21,
    "utcOffset": -360,
    "content": [
      {
        "title": "Selected Stations",
        "type": "list",
        "itemsType": "channel",
        "items": [
          {
            "title": "KUTX FM 98.9",
            "href": "/listen/kutx-98-9/vbFsCngB"
          },
          {
            "title": "View all 21 stations",
            "type": "more",
            "rightAccessory": "chevron-right",
            "page": {
              "title": "Austin TX",
              "subtitle": "All Stations",
              "url": "/visit/austin-tx/Aq7xeIiB/channels",
              "map": "Aq7xeIiB",
              "count": 21,
              "utcOffset": -360
            }
          }
        ]
      },
      {
        "actionPage": {
          "title": "Austin TX",
          "subtitle": "All Stations",
          "url": "/visit/austin-tx/Aq7xeIiB/channels",
          "map": "Aq7xeIiB",
          "count": 21,
          "utcOffset": -360
        },
        "actionText": "See all",
        "title": "Popular in Austin TX",
        "type": "list",
        "itemsType": "channel",
        "items": [
          {
            "title": "KUTX FM 98.9",
            "href": "/listen/kutx-98-9/vbFsCngB"
          }
        ]
      },
      {
        "title": "Picks from the area",
        "type": "list",
        "itemsType": "channel",
        "items": [
          {
            "title": "KUTX FM 98.9",
            "href": "/listen/kutx-98-9/vbFsCngB",
            "subtitle": "Georgetown TX",
            "map": "BQP3R6jj"
          }
        ]
      },
      {
        "title": "Popular in United States",
        "type": "list",
        "itemsType": "channel",
        "items": [
          {
            "title": "KUTX FM 98.9",
            "href": "/listen/kutx-98-9/vbFsCngB",
            "subtitle": "Georgetown TX",
            "map": "BQP3R6jj"
          },
          {
            "title": "View all 21 stations",
            "type": "more",
            "rightAccessory": "chevron-right",
            "page": {
              "title": "Austin TX",
              "subtitle": "All Stations",
              "url": "/visit/austin-tx/Aq7xeIiB/channels",
              "map": "Aq7xeIiB",
              "count": 21,
              "utcOffset": -360
            }
          }
        ]
      },
      {
        "title": "Nearby Austin TX",
        "type": "list",
        "rightAccessory": "chevron-right",
        "items": [
          {
            "title": "Georgetown TX",
            "rightDetail": "41 km",
            "page": {
              "title": "Austin TX",
              "subtitle": "All Stations",
              "url": "/visit/austin-tx/Aq7xeIiB/channels",
              "map": "Aq7xeIiB",
              "count": 21,
              "utcOffset": -360
            }
          }
        ]
      },
      {
        "title": "Cities in United States",
        "type": "list",
        "rightAccessory": "chevron-right",
        "items": [
          {
            "title": "New York NY",
            "leftAccessory": "count",
            "leftAccessoryCount": 219,
            "page": {
              "title": "Austin TX",
              "subtitle": "All Stations",
              "url": "/visit/austin-tx/Aq7xeIiB/channels",
              "map": "Aq7xeIiB",
              "count": 21,
              "utcOffset": -360
            }
          }
        ]
      }
    ]
  }
}

class rgp_content_items(TypedDict):
    title: str
    href: str

class rgp_content1(TypedDict):
    title: str
    type: str
    itemsType: str
    items: list[rgp_content_items]

class rgp_data(TypedDict):
    title: str
    subtitle: str
    url: str
    map: str
    count: int
    utcOffset: int
    content: list[rgp_content1]

class RadioGardenPlace(TypedDict):
    apiVersion: int
    version: str
    data: rgp_data
