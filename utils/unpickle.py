import classes.video_class
import classes.data_classes
import classes.discord_classes

import pickle
from io import BytesIO

class CustomUnpickler(pickle.Unpickler):
    def find_class(self, module, name):
        if name == 'ReturnData':
            return classes.data_classes.ReturnData
        if name == 'WebData':
            return classes.data_classes.WebData
        if name == 'Options':
            return classes.data_classes.Options
        if name == 'GuildData':
            return classes.data_classes.GuildData
        if name == 'Guild':
            return classes.data_classes.Guild
        if name == 'VideoClass':
            return classes.video_class.VideoClass
        if name == 'SearchList':
            return classes.video_class.SearchList
        if name == 'Queue':
            return classes.video_class.Queue
        if name == 'NowPlaying':
            return classes.video_class.NowPlaying
        if name == 'History':
            return classes.video_class.History
        if name == 'Save':
            return classes.data_classes.Save
        if name == 'SaveVideo':
            return classes.video_class.SaveVideo
        if name == 'DiscordUser':
            return classes.discord_classes.DiscordUser
        if name == 'DiscordMember':
            return classes.discord_classes.DiscordMember
        if name == 'DiscordChannel':
            return classes.discord_classes.DiscordChannel
        if name == 'DiscordRole':
            return classes.discord_classes.DiscordRole
        if name == 'DiscordInvite':
            return classes.discord_classes.DiscordInvite
        return super().find_class(module, name)

def unpickle(data):
    # if having a problem with unpickling, make sure that you have all the classes in CustomUnpickler
    return CustomUnpickler(BytesIO(data)).load()