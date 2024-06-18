from typing import TypedDict, Optional, Union, Literal

class DiscordChannelInfo(TypedDict):
    id: int
    name: str

class VideoChapter(TypedDict):
    start_time: float
    title: str
    end_time: float

class LastUpdated(TypedDict):
    queue: int
    now: int
    history: int
    saves: int
    options: int
    data: int
    slowed: int

class VideoAuthor(TypedDict):
    name: Union[str, int, None]
    id: Union[str, int, None]

# ------------------------------------------------ STATS ---------------------------------------------------------------

class DBData(TypedDict):
    bot_boot_time: int
    count_bot_boot: int
    time_in_vc: int
    time_paused: int
    time_playing: int
    count_guild_joined: int
    count_guild_left: int
    count_command: int
    count_songs_played: int
    count_skipped: int
    count_error: int

# ---------------------------------------------- Web Search ------------------------------------------------------------

class WebSearchResult(TypedDict):
    title: str
    value: str
    source: str
    picture: Optional[str]

# ---------------------------------------------- Commands --------------------------------------------------------------

class DiscordCommandDictAttribute(TypedDict):
    name: str
    description: str
    required: bool
    default: Union[str, int, float, bool, None]
    type: str

class DiscordCommandDict(TypedDict):
    name: str
    description: str
    category: str
    attributes: list[DiscordCommandDictAttribute]

# ------------------------------------------------- Radio --------------------------------------------------------------

class RadioInfoDict(TypedDict):
    type: str  # Literal['radia_cz', 'garden', 'tunein']

    id: str  # ID of the station (radia.cz ID | radio.garden ID | tunein ID)

    station_name: str  # Name of the station
    station_picture: Optional[str]  # URL of the station picture
    station_website: Optional[str]  # Website of the station

    now_title: Optional[str]  # Current song title
    now_artist: Optional[str]  # Current song artist
    now_picture: Optional[str]  # URL of the current song picture

    url: str  # radia.cz nowplay xml | radio.garden URL | tunein URL
    stream: Optional[str]  # Stream URL

    last_update: Optional[int]  # Timestamp of last update of now_playing

# ------------------------------------------------- played_duration ----------------------------------------------------

class TimeSegmentInner(TypedDict):
    epoch: Union[None, int]
    time_stamp: Union[None, int]

class TimeSegment(TypedDict):
    start: TimeSegmentInner
    end: TimeSegmentInner

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

# example_rgc_response = {
#   "apiVersion": 1,
#   "version": "9bd5454",
#   "data": {
#     "id": "vbFsCngB",
#     "title": "KUTX FM 98.9",
#     "url": "/listen/kutx-98-9/vbFsCngB",
#     "website": "http://www.kutx.org",
#     "secure": True,
#     "place": {
#       "id": "Aq7xeIiB",
#       "title": "Austin TX"
#     },
#     "country": {
#       "id": "GhDXw4EW",
#       "title": "United States"
#     }
#   }
# }

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

# example_rgp_response = {
#   "apiVersion": 1,
#   "version": "9bd5454",
#   "data": {
#     "title": "Austin TX",
#     "subtitle": "All Stations",
#     "url": "/visit/austin-tx/Aq7xeIiB/channels",
#     "map": "Aq7xeIiB",
#     "count": 21,
#     "utcOffset": -360,
#     "content": [
#       {
#         "title": "Selected Stations",
#         "type": "list",
#         "itemsType": "channel",
#         "items": [
#           {
#             "title": "KUTX FM 98.9",
#             "href": "/listen/kutx-98-9/vbFsCngB"
#           },
#           {
#             "title": "View all 21 stations",
#             "type": "more",
#             "rightAccessory": "chevron-right",
#             "page": {
#               "title": "Austin TX",
#               "subtitle": "All Stations",
#               "url": "/visit/austin-tx/Aq7xeIiB/channels",
#               "map": "Aq7xeIiB",
#               "count": 21,
#               "utcOffset": -360
#             }
#           }
#         ]
#       },
#       {
#         "actionPage": {
#           "title": "Austin TX",
#           "subtitle": "All Stations",
#           "url": "/visit/austin-tx/Aq7xeIiB/channels",
#           "map": "Aq7xeIiB",
#           "count": 21,
#           "utcOffset": -360
#         },
#         "actionText": "See all",
#         "title": "Popular in Austin TX",
#         "type": "list",
#         "itemsType": "channel",
#         "items": [
#           {
#             "title": "KUTX FM 98.9",
#             "href": "/listen/kutx-98-9/vbFsCngB"
#           }
#         ]
#       },
#       {
#         "title": "Picks from the area",
#         "type": "list",
#         "itemsType": "channel",
#         "items": [
#           {
#             "title": "KUTX FM 98.9",
#             "href": "/listen/kutx-98-9/vbFsCngB",
#             "subtitle": "Georgetown TX",
#             "map": "BQP3R6jj"
#           }
#         ]
#       },
#       {
#         "title": "Popular in United States",
#         "type": "list",
#         "itemsType": "channel",
#         "items": [
#           {
#             "title": "KUTX FM 98.9",
#             "href": "/listen/kutx-98-9/vbFsCngB",
#             "subtitle": "Georgetown TX",
#             "map": "BQP3R6jj"
#           },
#           {
#             "title": "View all 21 stations",
#             "type": "more",
#             "rightAccessory": "chevron-right",
#             "page": {
#               "title": "Austin TX",
#               "subtitle": "All Stations",
#               "url": "/visit/austin-tx/Aq7xeIiB/channels",
#               "map": "Aq7xeIiB",
#               "count": 21,
#               "utcOffset": -360
#             }
#           }
#         ]
#       },
#       {
#         "title": "Nearby Austin TX",
#         "type": "list",
#         "rightAccessory": "chevron-right",
#         "items": [
#           {
#             "title": "Georgetown TX",
#             "rightDetail": "41 km",
#             "page": {
#               "title": "Austin TX",
#               "subtitle": "All Stations",
#               "url": "/visit/austin-tx/Aq7xeIiB/channels",
#               "map": "Aq7xeIiB",
#               "count": 21,
#               "utcOffset": -360
#             }
#           }
#         ]
#       },
#       {
#         "title": "Cities in United States",
#         "type": "list",
#         "rightAccessory": "chevron-right",
#         "items": [
#           {
#             "title": "New York NY",
#             "leftAccessory": "count",
#             "leftAccessoryCount": 219,
#             "page": {
#               "title": "Austin TX",
#               "subtitle": "All Stations",
#               "url": "/visit/austin-tx/Aq7xeIiB/channels",
#               "map": "Aq7xeIiB",
#               "count": 21,
#               "utcOffset": -360
#             }
#           }
#         ]
#       }
#     ]
#   }
# }
#



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

# ----------------------------------------------- Radio Garden Search --------------------------------------------------

# rgs_example = {
#     "took": 2,
#     "hits": {
#         "hits": [
#             {
#                 "_id": "102998",
#                 "_score": 209.08212,
#                 "_source": {
#                     "code": "CZ",
#                     "stream": "streamtheworld.com",
#                     "subtitle": "Prague, Czechia",
#                     "type": "channel",
#                     "title": "Evropa2",
#                     "secure": true,
#                     "url": "/listen/evropa2/EwiN37X4"
#                 }
#             },
#             {
#                 "_id": "107518",
#                 "_score": 81.22767,
#                 "_source": {
#                     "code": "DE",
#                     "stream": "ndr.de",
#                     "subtitle": "Hamburg, Germany",
#                     "type": "channel",
#                     "title": "NDR 2",
#                     "secure": true,
#                     "url": "/listen/ndr2/Cz1WM7QF"
#                 }
#             },
#             {
#                 "_id": "118717",
#                 "_score": 81.22767,
#                 "_source": {
#                     "code": "EE",
#                     "stream": "err.ee",
#                     "subtitle": "Tallinn, Estonia",
#                     "type": "channel",
#                     "title": "Raadio 2",
#                     "secure": true,
#                     "url": "/listen/r2/HbcUYurM"
#                 }
#             },
#             {
#                 "_id": "122371",
#                 "_score": 81.22767,
#                 "_source": {
#                     "code": "SK",
#                     "stream": "bauermedia.sk",
#                     "subtitle": "Bratislava, Slovakia",
#                     "type": "channel",
#                     "title": "Europa 2",
#                     "secure": true,
#                     "url": "/listen/europa2/WBKeRMWM"
#                 }
#             },
#             {
#                 "_id": "130191",
#                 "_score": 81.22767,
#                 "_source": {
#                     "code": "DE",
#                     "stream": "ndr.de",
#                     "subtitle": "Hanover, Germany",
#                     "type": "channel",
#                     "title": "NDR 2",
#                     "secure": true,
#                     "url": "/listen/ndr-2/b3b3JIsM"
#                 }
#             }
#         ]
#     },
#     "query": "evropa 2",
#     "version": "d711c66",
#     "apiVersion": 0
# }

class rgs_hit_source(TypedDict):
    code: str
    stream: str
    subtitle: str
    type: str
    title: str
    secure: bool
    url: str

class rgs_hit(TypedDict):
    _id: str
    _score: float
    _source: rgs_hit_source

class rgs_hits(TypedDict):
    hits: list[rgs_hit]

class RadioGardenSearch(TypedDict):
    took: int
    hits: rgs_hits
    query: str
    version: str
    apiVersion: int

# ----------------------------------------------- Radio TuneIn ---------------------------------------------------------

# describe_example = {
#             "element": "station",
#             "guide_id": "s15666",
#             "preset_id": "s15666",
#             "name": "Evropa 2",
#             "call_sign": "Evropa 2",
#             "slogan": "Maxximum Muziky",
#             "frequency": "88.2",
#             "band": "FM",
#             "url": "http://www.evropa2.cz/",
#             "report_url": "",
#             "detail_url": "http://tun.in/senaK",
#             "is_preset": false,
#             "is_available": true,
#             "is_music": true,
#             "has_song": true,
#             "has_schedule": true,
#             "has_topics": false,
#             "twitter_id": "Evropa2",
#             "logo": "https://cdn-radiotime-logos.tunein.com/s15666q.png",
#             "location": "Praha",
#             "current_song": "Legends Never Die",
#             "current_artist": "Bad Wolves",
#             "current_artist_id": "m1414270",
#             "current_album": "Die About It",
#             "current_artist_art": null,
#             "current_album_art": null,
#             "description": "R\u00e1dio Evropa 2 nab\u00edz\u00ed nejlep\u0161\u00ed hudebn\u00ed mix poskl\u00e1dan\u00fd z t\u011bch nejaktu\u00e1ln\u011bj\u0161\u00edch hit\u016f sv\u011btov\u00fdch i dom\u00e1c\u00edch hitpar\u00e1d a novinek. Evropa 2 je modern\u00ed r\u00e1dio (nejen) pro mlad\u00e9 a dynamick\u00e9 lidi, kte\u0159\u00ed maj\u00ed r\u00e1di muziku, sport, filmy, m\u00f3du\u2026 Zkr\u00e1tka v\u0161e, co souvis\u00ed a modern\u00edm a aktivn\u00edm \u017eivotn\u00edm stylem.",
#             "email": "info@evropa2.cz",
#             "phone": "+420257400888",
#             "mailing_address": "Wenzigova 4\r\n120 00 Praha 2",
#             "language": "Czech",
#             "genre_id": "g3",
#             "genre_name": "Adult Hits",
#             "region_id": "r100725",
#             "country_region_id": 101232,
#             "latlon": null,
#             "tz": "GMT + 1 (Budapest)",
#             "tz_offset": "60",
#             "publish_song": null,
#             "publish_song_url": null,
#             "publish_song_rejection_reason": null,
#             "now_playing_url": null,
#             "external_key": null,
#             "ad_eligible": true,
#             "preroll_ad_eligible": true,
#             "companion_ad_eligible": false,
#             "video_preroll_ad_eligible": false,
#             "fb_share": true,
#             "twitter_share": true,
#             "song_share": true,
#             "donation_eligible": null,
#             "donation_url": null,
#             "donation_text": null,
#             "donation_icon": null,
#             "song_buy_eligible": null,
#             "tunein_url": "http://tunein.com/station/?stationId=15666",
#             "is_family_content": false,
#             "is_mature_content": false,
#             "is_event": false,
#             "content_classification": "music",
#             "echoed_count": null,
#             "favorited_count": null,
#             "is_favorited": null,
#             "is_favoritable": null,
#             "has_profile": "true",
#             "can_cast": true,
#             "nielsen_eligible": false,
#             "nielsen_provider": null,
#             "nielsen_asset_id": null,
#             "nowplaying_channel": null,
#             "why_ads_text": null,
#             "use_native_player": false,
#             "live_seek_stream": false,
#             "seek_disabled": false
#         }
#
# tunein_search_example = {
#             "element": "outline",
#             "type": "audio",
#             "text": "Evropa 2",
#             "URL": "http://opml.radiotime.com/Tune.ashx?id=s15666",
#             "bitrate": "128",
#             "reliability": "99",
#             "guide_id": "s15666",
#             "subtext": "Jagwar Twin - Bad Feeling (Oompa Loompa)",
#             "genre_id": "g3",
#             "formats": "mp3",
#             "playing": "Jagwar Twin - Bad Feeling (Oompa Loompa)",
#             "playing_image": "http://cdn-albums.tunein.com/gn/JNTVDVZKTDq.jpg",
#             "show_id": "p684187",
#             "item": "station",
#             "image": "http://cdn-radiotime-logos.tunein.com/s15666q.png",
#             "current_track": "MaXXimum muziky",
#             "now_playing_id": "s15666",
#             "preset_id": "s15666"
#         }
#


class TuneInSearch(TypedDict):
    element: str
    type: str
    text: str
    URL: str
    bitrate: str
    reliability: str
    guide_id: str
    subtext: str
    genre_id: str
    formats: str
    playing: str
    playing_image: str
    show_id: str
    item: str
    image: str
    current_track: str
    now_playing_id: str
    preset_id: str


class TuneInDescribe(TypedDict):
    element: str
    guide_id: str
    preset_id: str
    name: str
    call_sign: str
    slogan: str
    frequency: str
    band: str
    url: str
    report_url: str
    detail_url: str
    is_preset: bool
    is_available: bool
    is_music: bool
    has_song: bool
    has_schedule: bool
    has_topics: bool
    twitter_id: str
    logo: str
    location: str
    current_song: str
    current_artist: str
    current_artist_id: str
    current_album: str
    current_artist_art: Optional[str]
    current_album_art: Optional[str]
    description: str
    email: str
    phone: str
    mailing_address: str
    language: str
    genre_id: str
    genre_name: str
    region_id: str
    country_region_id: int
    latlon: Optional[str]
    tz: str
    tz_offset: str
    publish_song: Optional[str]
    publish_song_url: Optional[str]
    publish_song_rejection_reason: Optional[str]
    now_playing_url: Optional[str]
    external_key: Optional[str]
    ad_eligible: bool
    preroll_ad_eligible: bool
    companion_ad_eligible: bool
    video_preroll_ad_eligible: bool
    fb_share: bool
    twitter_share: bool
    song_share: bool
    donation_eligible: Optional[str]
    donation_url: Optional[str]
    donation_text: Optional[str]
    donation_icon: Optional[str]
    song_buy_eligible: Optional[str]
    tunein_url: str
    is_family_content: bool
    is_mature_content: bool
    is_event: bool
    content_classification: str
    echoed_count: Optional[str]
    favorited_count: Optional[str]
    is_favorited: Optional[str]
    is_favoritable: Optional[str]
    has_profile: str
    can_cast: bool
    nielsen_eligible: bool
    nielsen_provider: Optional[str]
    nielsen_asset_id: Optional[str]
    nowplaying_channel: Optional[str]
    why_ads_text: Optional[str]
    use_native_player: bool
    live_seek_stream: bool
    seek_disabled: bool

# ----------------------------------------------- Radios JSON ----------------------------------------------------------

# radia_cz_example =  {
#         "@u": "2024-02-29 19:46:53",
#         "id": "94",
#         "name": "Hitr\u00e1dio Faktor",
#         "logoSvg": "https://radia.cz/data/station_logo_svg/0001/02/hitradio-faktor-svg-1635772227.svg",
#         "logo": "https://radia.cz/data/station_logo/0001/02/054abb50c9a795b4899f55cf933e5ce3101e0ea1.png",
#         "link": "https://radia.cz/radio-hitradio-faktor",
#         "nowplay": "https://cdb.radia.cz/content/nowplay/v2/hitradio-faktor.xml",
#         "playlist": "https://cdb.radia.cz/content/playlist/v2/hitradio-faktor.xml",
#         "program": None,
#         "streams": {
#             "stream": [
#                 {
#                     "id": "2630",
#                     "name": "Hitr\u00e1dio Faktor aac 64kb",
#                     "type": "aac",
#                     "bitrate": "64",
#                     "forAndroid": "1",
#                     "forApple": "1",
#                     "forBrowser": "1",
#                     "url": "https://playerservices.streamtheworld.com/api/livestream-redirect/HITRADIO_FAKTORAAC.aac",
#                     "defWifi": "0",
#                     "def3g": "1"
#                 },
#                 {
#                     "id": "2628",
#                     "name": "Hitr\u00e1dio Faktor mp3 128kb",
#                     "type": "mp3",
#                     "bitrate": "128",
#                     "forAndroid": "1",
#                     "forApple": "1",
#                     "forBrowser": "1",
#                     "url": "https://playerservices.streamtheworld.com/api/livestream-redirect/HITRADIO_FAKTOR_128.mp3",
#                     "defWifi": "1",
#                     "def3g": "0"
#                 },
#                 {
#                     "id": "2619",
#                     "name": "Hitr\u00e1dio Faktor aac 64kb",
#                     "type": "aac",
#                     "bitrate": "64",
#                     "forAndroid": "1",
#                     "forApple": "1",
#                     "forBrowser": "1",
#                     "url": "https://ice.radia.cz/faktor64.aac",
#                     "defWifi": "0",
#                     "def3g": "1"
#                 },
#                 {
#                     "id": "2617",
#                     "name": "Hitr\u00e1dio Faktor mp3 128kb",
#                     "type": "mp3",
#                     "bitrate": "128",
#                     "forAndroid": "1",
#                     "forApple": "1",
#                     "forBrowser": "1",
#                     "url": "https://ice.radia.cz/faktor128.mp3",
#                     "defWifi": "1",
#                     "def3g": "0"
#                 }
#             ]
#         }
#     },

class r_stream(TypedDict):
    id: str
    name: str
    type: str
    bitrate: str
    forAndroid: str
    forApple: str
    forBrowser: str
    url: str
    defWifi: str
    def3g: str

class r_streams(TypedDict):
    stream: Union[list[r_stream] or r_stream]

class RadiosJSON(TypedDict):
    id: str
    name: str
    logoSvg: str
    logo: str
    link: str
    nowplay: str
    playlist: str
    program: Optional[str]
    streams: r_streams

# ------------------------------------------------- RadiosCzNow --------------------------------------------------------

np_Image = TypedDict('np_Image', {'#text': str})

class np_Images(TypedDict):
    Image: Union[list[np_Image], np_Image]

class np_Item(TypedDict):
    Id: Optional[str]
    PlayedAt: Optional[str]
    Length: Optional[str]
    Artist: Optional[Union[str, dict[str, str]]]
    Song: Optional[Union[str, dict[str, str]]]
    Album: Optional[str]
    Year: Optional[str]
    Authors: Optional[str]
    Publisher: Optional[str]
    Lyrics: Optional[str]
    Images: Optional[np_Images]
    Audio: Optional[str]

class np_RadiosCzNow(TypedDict):
    Item: np_Item

class RadiosCzNow(TypedDict):
    NowPlay: np_RadiosCzNow
