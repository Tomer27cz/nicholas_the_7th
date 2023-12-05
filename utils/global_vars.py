import json
from os import listdir

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

with open('db/radio.json', 'r', encoding='utf-8') as file:
    radio_dict = json.load(file)

with open('db/languages.json', 'r', encoding='utf-8') as file:
    languages_dict = json.load(file)

def load_sound_effects():
    """
    Loads all sound effects from the sound_effects folder
    to the global variable sound_effects
    """
    sound_effects = ["No sound effects found"]
    try:
        sound_effects = listdir('sound_effects')
        for file_index, file_val in enumerate(sound_effects):
            sound_effects[file_index] = sound_effects[file_index][:len(file_val) - 4]
    except FileNotFoundError:
        return ["No sound effects found"]
    return sound_effects
sound_effects = load_sound_effects()

