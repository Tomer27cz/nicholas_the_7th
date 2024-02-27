from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from classes.data_classes import ReturnData
    from utils.global_vars import GlobalVars
    from classes.typed_dictionaries import VideoInfo

from database.guild import guild

from utils.save import update
from utils.translate import txt
from utils.discord import get_voice_client
from utils.url import get_playlist_from_url

import commands.player
import commands.queue

from discord.ui import View
from discord.ext import commands as dc_commands
import discord

react_dict = {
    "ABCD": "\ud83d\udd20",
    "abcd": "\ud83d\udd21",
    "1234": "\ud83d\udd22",
    "0": "0\ufe0f\u20e3",
    "1": "1\ufe0f\u20e3",
    "2": "2\ufe0f\u20e3",
    "3": "3\ufe0f\u20e3",
    "4": "4\ufe0f\u20e3",
    "5": "5\ufe0f\u20e3",
    "6": "6\ufe0f\u20e3",
    "7": "7\ufe0f\u20e3",
    "8": "8\ufe0f\u20e3",
    "9": "9\ufe0f\u20e3",
    "10": "\ud83d\udd1f",
    "stop": "\u23f9",
    "play": "\u25b6",
    "pause": "\u23f8",
    "false": "\u274c",
    "true": "\u2705",
    "up": "\u2b06\ufe0f",
    "down": "\u2b07\ufe0f",
    "left": "\u2b05\ufe0f",
    "right": "\u27a1\ufe0f"
}

class PlayerControlView(View):
    def __init__(self, ctx, glob: GlobalVars):
        super().__init__(timeout=7200)
        if isinstance(ctx, dc_commands.Context):
            self.guild = ctx.guild
            self.guild_id = ctx.guild.id
            self.glob = glob
            self.message = None

    async def on_timeout(self) -> None:
        for item in self.children:
            item.disabled = True

        if self.message:
            await self.message.edit(view=self, content=self.message.content+"\n**Controls Timed Out**")

    @discord.ui.button(emoji=react_dict['play'], style=discord.ButtonStyle.blurple, custom_id='play')
    async def callback(self, interaction, button):
        voice: discord.voice_client.VoiceClient = get_voice_client(self.glob.bot.voice_clients, guild=self.guild)
        if voice:
            if voice.is_paused():
                voice.resume()
                # noinspection PyUnresolvedReferences
                pause_button = [x for x in self.children if x.custom_id == 'pause'][0]
                pause_button.style = discord.ButtonStyle.blurple
                button.style = discord.ButtonStyle.grey
                await interaction.response.edit_message(view=self)
            elif voice.is_playing():
                await interaction.response.send_message(txt(self.guild_id, self.glob, "Player **already resumed!**"),
                                                        ephemeral=True)
            else:
                await interaction.response.send_message(txt(self.guild_id, self.glob, "No audio playing"), ephemeral=True)
        else:
            await interaction.response.send_message(txt(self.guild_id, self.glob, "No audio"), ephemeral=True)

    @discord.ui.button(emoji=react_dict['pause'], style=discord.ButtonStyle.blurple, custom_id='pause')
    async def pause_callback(self, interaction, button):
        voice: discord.voice_client.VoiceClient = get_voice_client(self.glob.bot.voice_clients, guild=self.guild)
        if voice:
            if voice.is_playing():
                voice.pause()
                # noinspection PyUnresolvedReferences
                play_button = [x for x in self.children if x.custom_id == 'play'][0]
                play_button.style = discord.ButtonStyle.blurple
                button.style = discord.ButtonStyle.grey
                await interaction.response.edit_message(view=self)
            elif voice.is_paused():
                await interaction.response.send_message(txt(self.guild_id, self.glob, "Player **already paused!**"),
                                                        ephemeral=True)
            else:
                await interaction.response.send_message(txt(self.guild_id, self.glob, "No audio playing"), ephemeral=True)
        else:
            await interaction.response.send_message(txt(self.guild_id, self.glob, "No audio"), ephemeral=True)

    # noinspection PyUnusedLocal
    @discord.ui.button(emoji=react_dict['stop'], style=discord.ButtonStyle.red, custom_id='stop')
    async def stop_callback(self, interaction, button):
        voice: discord.voice_client.VoiceClient = get_voice_client(self.glob.bot.voice_clients, guild=self.guild)
        if voice:
            if voice.is_playing() or voice.is_paused():
                voice.stop()
                guild(self.glob, interaction.guild_id).options.stopped = True
                self.glob.ses.commit()
                await interaction.response.edit_message(view=None)
            else:
                await interaction.response.send_message(txt(self.guild_id, self.glob, "No audio playing"), ephemeral=True)
        else:
            await interaction.response.send_message(txt(self.guild_id, self.glob, "No audio"), ephemeral=True)

class SearchOptionView(View):
    def __init__(self, ctx, glob: GlobalVars, search_data: list[VideoInfo], force=False, from_play=False):
        super().__init__(timeout=180)

        if isinstance(ctx, dc_commands.Context):
            self.ctx = ctx
            self.guild = ctx.guild
            self.guild_id = ctx.guild.id
            self.force = force
            self.from_play = from_play
            self.glob = glob
            self.data = search_data
            self.message = None

    async def on_timeout(self) -> None:
        for item in self.children:
            item.disabled = True

        if self.message:
            await self.message.edit(view=self, content=self.message.content+"\n**Search Timed Out**")

    # noinspection PyUnusedLocal
    async def do_callback(self, interaction, button, num):
        if self.force:
            ret: ReturnData = await commands.queue.queue_command_def(self.ctx, self.glob, self.data[num-1]['link'], position=0, force=True, mute_response=True, no_search=True)
        else:
            ret: ReturnData = await commands.queue.queue_command_def(self.ctx, self.glob, self.data[num-1]['link'], mute_response=True, no_search=True)

        update(self.glob)
        await interaction.response.edit_message(content=ret.message, view=None)

        if self.from_play:
            await commands.player.play_def(self.ctx, self.glob)

    # noinspection PyUnusedLocal
    @discord.ui.button(emoji=react_dict['1'], style=discord.ButtonStyle.blurple, custom_id='1')
    async def callback_1(self, interaction, button):
        await self.do_callback(interaction, button, 1)

    # noinspection PyUnusedLocal
    @discord.ui.button(emoji=react_dict['2'], style=discord.ButtonStyle.blurple, custom_id='2')
    async def callback_2(self, interaction, button):
        await self.do_callback(interaction, button, 2)

    # noinspection PyUnusedLocal
    @discord.ui.button(emoji=react_dict['3'], style=discord.ButtonStyle.blurple, custom_id='3')
    async def callback_3(self, interaction, button):
        await self.do_callback(interaction, button, 3)

    # noinspection PyUnusedLocal
    @discord.ui.button(emoji=react_dict['4'], style=discord.ButtonStyle.blurple, custom_id='4')
    async def callback_4(self, interaction, button):
        await self.do_callback(interaction, button, 4)

    # noinspection PyUnusedLocal
    @discord.ui.button(emoji=react_dict['5'], style=discord.ButtonStyle.blurple, custom_id='5')
    async def callback_5(self, interaction, button):
        await self.do_callback(interaction, button, 5)

class PlaylistOptionView(View):
    def __init__(self, ctx, glob: GlobalVars, url, force=False, from_play=False):
        super().__init__(timeout=180)

        if isinstance(ctx, dc_commands.Context):
            self.ctx = ctx
            self.url = url
            self.guild = ctx.guild
            self.guild_id = ctx.guild.id
            self.force = force
            self.from_play = from_play
            self.glob = glob
            self.message = None

    async def on_timeout(self) -> None:
        for item in self.children:
            item.disabled = True

        if self.message:
            await self.message.edit(view=self, content=self.message.content+"\n**Interaction Timed Out**")

    # noinspection PyUnusedLocal
    @discord.ui.button(label='Yes', style=discord.ButtonStyle.blurple)
    async def callback_1(self, interaction, button):
        playlist_url = get_playlist_from_url(self.url)
        await interaction.response.edit_message(content=txt(self.guild_id, self.glob, "Adding playlist to queue..."), view=None)

        position = 0 if self.force else None
        response: ReturnData = await commands.queue.queue_command_def(self.ctx, self.glob, playlist_url,
                                                                      position=position, mute_response=True,
                                                                      force=self.force)

        # await interaction.response.edit_message(content=response.message, view=None)
        await interaction.followup.edit_message(content=response.message, view=None, message_id=interaction.message.id)

        if self.from_play:
            await commands.player.play_def(self.ctx, self.glob)

    # noinspection PyUnusedLocal
    @discord.ui.button(label='No', style=discord.ButtonStyle.blurple)
    async def callback_2(self, interaction, button):
        pure_url = self.url[:self.url.index('&list=')]

        position = 0 if self.force else None
        response: ReturnData = await commands.queue.queue_command_def(self.ctx, self.glob, pure_url, position=position,
                                                                      mute_response=True, force=self.force)

        await interaction.response.edit_message(content=response.message, view=None)

        if self.from_play:
            await commands.player.play_def(self.ctx, self.glob)
