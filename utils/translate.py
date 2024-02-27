from database.guild import guild_options_language

from utils.log import log
from utils.global_vars import languages_dict, GlobalVars, languages_shortcuts_dict

import typing

# noinspection PyTypeHints
def txt(guild_id: int, glob: GlobalVars, content: str, lang: typing.Literal[tuple(languages_dict.keys())]=None) -> str:
    """
    Translates text to english
    Gets text from languages.json
    :param content: str - translation key
    :param glob: GlobalVars - global variables object (only when getting language from guild)
    :param guild_id: int - id of guild (default: 0 - no guild)
    :param lang: str - language to translate to (default: 'en')
    :return: str - translated text
    """
    if lang is None:
        lang = 'en'
        if guild_id != 0:
            lang = guild_options_language(glob, guild_id)

    if content in languages_shortcuts_dict.keys():
        content = str(languages_shortcuts_dict[content])

    if str(content) not in languages_dict[lang].keys():
        with open('db/missing.txt', 'a', encoding='utf-8') as file:
            # lines = file.readlines()
            # if content not in lines:
            file.write(f'{lang},{content}\n')
            log(None, f'KeyError: {content} in {lang} - added to missing.txt')
        return content

    try:
        return languages_dict[lang][str(content)]
    except KeyError:
        log(None, f'KeyError: {content} in {lang} - Should not happen!')
        return content

# def tg(guild_id: int, content: str) -> str:
#     """
#     Translates text to guild language
#     Selects language from guild options
#     Gets text from languages.json
#     :param guild_id: int - id of guild
#     :param content: str - translation key
#     :return: str - translated text
#     """
#
#     return content
#
#     try:
#         lang = guild(glob, guild_id).options.language
#     except KeyError:
#         log(guild_id, f'KeyError: {guild_id} in guild')
#         lang = 'en'
#     except AttributeError:
#         log(guild_id, f'AttributeError: {guild_id} in guild')
#         lang = 'en'
#
#     try:
#         to_return = languages_dict[lang][content]
#     except KeyError:
#         log(None, f'KeyError: {content} in {lang}')
#         to_return = content
#     return to_return
#
#
# def ftg(guild_id: int, content: str) -> str:
#     """
#     Translates text to guild language
#     Selects language from guild options
#     Gets text from languages.json
#     :param guild_id: int - id of guild
#     :param content: str - translation key
#     :return: str - translated text
#     """
#     # return content
#     # # for now until i figure out how to get this working in apache2
#
#     return content
#
#     try:
#         languages_dict = languages_dict()
#         lang = guild(glob, guild_id).options.language
#     except Exception as e:
#         return content
#
#     try:
#         to_return = languages_dict[lang][content]
#     except KeyError:
#         log(None, f'KeyError: {content} in {lang}')
#         to_return = content
#     return to_return
