from utils.log import log
from utils.global_vars import languages_dict
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

    return content

    try:
        lang = guild(glob, guild_id).options.language
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
    # return content
    # # for now until i figure out how to get this working in apache2

    return content

    try:
        languages_dict = languages_dict()
        lang = guild(glob, guild_id).options.language
    except Exception as e:
        return content

    try:
        to_return = languages_dict[lang][content]
    except KeyError:
        log(None, f'KeyError: {content} in {lang}')
        to_return = content
    return to_return
