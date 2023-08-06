import __main__

def get_bot():
    bot = __main__.bot
    if not bot:
        raise Exception("Bot instance not found")
    return bot

def get_guild_dict():
    guild = __main__.guild
    if not guild:
        raise Exception("Guild dict instance not found")
    return guild

def get_languages_dict():
    languages = __main__.languages_dict
    if not languages:
        raise Exception("Languages dict instance not found")
    return languages

def get_sc():
    sc = __main__.sc
    if not sc:
        raise Exception("SoundCloud instance not found")
    return sc

def get_radio_dict():
    radio_dict = __main__.radio_dict
    if not radio_dict:
        raise Exception("Radio dict not found")
    return radio_dict

def get_sp():
    sp = __main__.sp
    if not sp:
        raise Exception("Spotify instance not found")
    return sp

def get_all_sound_effects():
    sound_effects = __main__.sound_effects
    if not sound_effects:
        raise Exception("Sound effects dict not found")
    return sound_effects