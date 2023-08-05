from utils.log import log
from utils.globals import get_guild_dict, get_languages_dict

def tg(guild_id: int, content: str) -> str:
    """
    Translates text to guild language
    Selects language from guild options
    Gets text from languages.json
    :param guild_id: int - id of guild
    :param content: str - translation key
    :return: str - translated text
    """
    guild = get_guild_dict()
    languages_dict = get_languages_dict()
    try:
        lang = guild[guild_id].options.language
    except KeyError:
        log(guild_id, f'KeyError: {guild_id} in guild')
        lang = 'en'

    try:
        to_return = languages_dict[lang][content]
    except KeyError:
        log(None, f'KeyError: {content} in {lang}')
        to_return = content
    return to_return
