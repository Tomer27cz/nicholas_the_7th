import json
from os import listdir

import config

class GlobalVars:
    def __init__(self, bot_var, ses_var, sp_var, sc_var):
        """
        Global variables class
        :param bot_var: Bot object
        :param ses_var: Session object
        :param sp_var: Spotipy object
        :param sc_var: SoundCloud object
        """
        self.bot = bot_var
        self.ses = ses_var
        self.sp = sp_var
        self.sc = sc_var


with open(f'{config.PARENT_DIR}db/radio.json', 'r', encoding='utf-8') as file:
    radio_dict = json.load(file)

with open(f'{config.PARENT_DIR}db/languages.json', 'r', encoding='utf-8') as file:
    languages_dict = json.load(file)

def load_sound_effects():
    """
    Loads all sound effects from the sound_effects folder
    to the global variable sound_effects
    """
    try:
        se = listdir(f'{config.PARENT_DIR}sound_effects')
        for file_index, file_val in enumerate(se):
            se[file_index] = se[file_index][:len(file_val) - 4]
    except FileNotFoundError:
        return ["No sound effects found"]
    return se


sound_effects = load_sound_effects()
