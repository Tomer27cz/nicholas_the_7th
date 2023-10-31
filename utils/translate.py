from utils.log import log
from utils.globals import get_languages_dict
from database.guild import guild

def tg(guild_id: int, content: str) -> str:
    """
    Translates text to guild language
    Selects language from guild options
    Gets text from languages.json
    :param guild_id: int - id of guild
    :param content: str - translation key
    :return: str - translated text
    """
    languages_dict = get_languages_dict()
    try:
        lang = guild(guild_id).options.language
    except KeyError:
        log(guild_id, f'KeyError: {guild_id} in guild')
        lang = 'en'
    except AttributeError:
        log(guild_id, f'AttributeError: {guild_id} in guild')
        lang = 'en'

    try:
        to_return = languages_dict[lang][content]
    except KeyError:
        log(None, f'KeyError: {content} in {lang}')
        to_return = content
    return to_return


def ftg(guild_id: int, content: str) -> str:
    """
    Translates text to guild language
    Selects language from guild options
    Gets text from languages.json
    :param guild_id: int - id of guild
    :param content: str - translation key
    :return: str - translated text
    """
    return content
    # for now until i figure out how to get this working in apache2


    try:
        guild = get_guild_dict()
        languages_dict = get_languages_dict()
    except Exception as e:
        return content

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
