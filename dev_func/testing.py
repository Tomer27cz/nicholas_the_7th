import time
import asyncio


import yt_dlp
import youtubesearchpython


YTDL_OPTIONS = {
        'format': 'bestaudio/best',
        'extractaudio': True,
        'audioformat': 'mp3',
        'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
        'restrictfilenames': True,
        'noplaylist': True,
        'nocheckcertificate': True,
        'ignoreerrors': False,
        'logtostderr': False,
        'quiet': True,
        'no_warnings': True,
        'default_search': 'auto',
        'source_address': '0.0.0.0',
    }
FFMPEG_OPTIONS = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
    'options': '-vn',
}
ytdl = yt_dlp.YoutubeDL(YTDL_OPTIONS)


url ='https://www.youtube.com/watch?v=5qap5aO4i9A'

start_time = time.time()
ytdl_result = asyncio.run(ytdl.extract_info(url, download=False, process=False))
end_time = time.time()

print(f"yt_dlp took {end_time - start_time} seconds to get info")

start_time = time.time()
ytsp = youtubesearchpython.VideosSearch(url, limit=1)
ytsp_result = ytsp.result()['result'][0]
end_time = time.time()

print(f"ytsp took {end_time - start_time} seconds to get info")


print("yt_dlp result:")
print(ytdl_result)
print("ytsp result:")
print(ytsp_result)



