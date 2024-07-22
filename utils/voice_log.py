import time
# Description: VoiceLog class to log voice session of the bot
class VoiceLog:
    # VoiceLog - Voice Session
    # ----
    # guild_id: int
    # channel_id: int
    # connected_at: int
    # disconnected_at: int
    # list: list[dict]
    # ----
    # list
    # ('time', 'playing', 'paused') : (int, bool, bool) - not dict for memory efficiency
    # ----
    # time_in_vc: int
    # time_playing: int
    # time_paused: int
    # ----

    def __init__(self, guild_id: int, channel_id: int):
        self.guild_id = guild_id
        self.channel_id = channel_id
        self.connected_at = int(time.time())
        self.disconnected_at = None

        self.time_in_vc = 0
        self.time_playing = 0
        self.time_paused = 0

        self._list = [(self.connected_at, False, False)]
        self._active = True

    def playing(self):
        """
        Add a record to the list that the bot is playing if the last record is not playing
        """
        if not self._list[-1][1]:
            self._list.append((int(time.time()), True, False))

    def paused(self):
        """
        Add a record to the list that the bot is paused if the last record is not paused
        """
        if not self._list[-1][2]:
            self._list.append((int(time.time()), False, True))

    def in_vc(self):
        """
        Add a record to the list that the bot is in the voice channel if the last record is not in the voice channel
        """
        if self._list[-1][1] or self._list[-1][2]:
            self._list.append((int(time.time()), False, False))

    def calculate(self):
        """
        Should be called when the bot leaves the voice channel,
        Calculates the time spent in the voice channel, playing and paused
        """
        self._active = False
        self.disconnected_at = int(time.time())

        self.time_in_vc = self.disconnected_at - self.connected_at
        for i in range(1, len(self._list)):
            if self._list[i][1]:
                self.time_playing += self._list[i][0] - self._list[i-1][0]
            elif self._list[i][2]:
                self.time_paused += self._list[i][0] - self._list[i-1][0]

        self._list = None