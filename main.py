from classes.data_classes import WebData

from commands.autocomplete import *

from utils.discord import get_content_of_message
from utils.log import send_to_admin
from utils.json import *

from ipc.server import ipc_run

from commands.admin import *
from commands.chat_export import *
from commands.general import *
from commands.player import *
from commands.queue import *
from commands.voice import *

from sclib import SoundcloudAPI
from spotipy.oauth2 import SpotifyClientCredentials
from discord.ext import commands as dc_commands

import discord.ext.commands
import spotipy
import datetime
import threading

import config

authorized_users = config.AUTHORIZED_USERS
my_id = config.OWNER_ID
bot_id = config.CLIENT_ID
prefix = config.PREFIX
vlc_logo = config.VLC_LOGO
default_discord_avatar = config.DEFAULT_DISCORD_AVATAR
d_id = 349164237605568513

# ---------------- Connect to database ------------

from database.main import *
from database.guild import *
ses = connect_to_db(first_time=True)

# ---------------- Bot class ------------

class Bot(dc_commands.Bot):
    """
    Bot class

    This class is used to create the bot instance.
    """
    def __init__(self):
        intents = discord.Intents.all()
        super().__init__(command_prefix=prefix, intents=intents)
        self.synced = False

    async def on_ready(self):
        await self.wait_until_ready()
        if not self.synced:
            log(None, "Trying to sync commands")
            await self.tree.sync()
            log(None, f"Synced slash commands for {self.user}")
        await bot.change_presence(activity=discord.Game(name=f"/help"))
        log(None, f'Logged in as:\n{bot.user.name}\n{bot.user.id}')

        update(glob)

    async def on_guild_join(self, guild_object):
        # log
        log_msg = f"Joined guild ({guild_object.name})({guild_object.id}) with {guild_object.member_count} members and {len(guild_object.voice_channels)} voice channels"
        log(None, log_msg)

        # send log to admin
        await send_to_admin(glob, log_msg)

        # create guild object
        create_guild(glob, guild_object.id)
        update(glob)

        # get text channels
        text_channels = guild_object.text_channels
        sys_channel = guild_object.system_channel

        # send welcome message in system channel or first text channel
        message = f"Hello **`{guild_object.name}`**! I am `{self.user.display_name}`. Thank you for inviting me.\n\nTo see what commands I have available type `/help`\n\nIf you have any questions, you can DM my developer <@!{config.DEVELOPER_ID}>#4272"
        if sys_channel is not None:
            if sys_channel.permissions_for(guild_object.me).send_messages:
                await sys_channel.send(message)
        else:
            await text_channels[0].send(message)

        # download all channels
        await download_guild(WebData(guild_object.id, bot.user.name, bot.user.id), glob, guild_object.id, mute_response=True, ephemeral=True)

    @staticmethod
    async def on_guild_remove(guild_object):
        # log
        log_msg = f"Left guild ({guild_object.name})({guild_object.id}) with {guild_object.member_count} members and {len(guild_object.voice_channels)} voice channels"
        log(None, log_msg)

        # send log to admin
        await send_to_admin(glob, log_msg)

        # update guilds
        update(glob)

    async def on_voice_state_update(self, member, before, after):
        # set voice state
        voice_state = member.guild.voice_client

        # set guild_id
        guild_id = member.guild.id

        # check if bot is alone in voice channel
        if voice_state is not None and len(voice_state.channel.members) == 1:
            # stop playing and disconnect
            voice_state.stop()
            await voice_state.disconnect()

            # set stopped to true
            guild(glob, guild_id).options.stopped = True
            ses.commit()

            # log
            log(guild_id, "-->> Disconnecting when last person left -> Queue Cleared <<--")

            # save history
            now_to_history(glob, guild_id)

            # clear queue when last person leaves
            clear_queue(glob, guild_id)

        if not member.id == self.user.id:
            return

        # if bot joins a voice channel
        elif before.channel is None:
            # get voice client
            voice = after.channel.guild.voice_client

            # initialize loop
            time_var = 0
            while True:
                # check every second
                await asyncio.sleep(5)

                # increase time_var
                time_var += 5

                # check if bot is playing and not paused
                if voice.is_playing() and not voice.is_paused():
                    time_var = 0  # reset time_var

                # check if time_var is greater than buffer
                if time_var >= guild(glob, guild_id).options.buffer:
                    # stop playing and disconnect
                    voice.stop()
                    await voice.disconnect()

                    # set stopped to true
                    guild(glob, guild_id).options.stopped = True
                    ses.commit()

                    # log
                    log(guild_id, f"-->> Disconnecting after {guild(glob, guild_id).options.buffer} seconds of no play <<--")

                    # save history
                    now_to_history(glob, guild_id)

                # check if bot is disconnected
                if not voice.is_connected():
                    break  # break loop

        # if bot leaves a voice channel
        elif after.channel is None:
            # clear queue when bot leaves
            clear_queue(glob, guild_id)
            # log
            log(guild_id, f"-->> Cleared Queue after bot Disconnected <<--")

    async def on_command_error(self, ctx, error):
        # get error traceback
        error_traceback = traceback.format_exception(type(error), error, error.__traceback__)
        error_traceback = ''.join(error_traceback)

        if isinstance(error, discord.errors.Forbidden):
            log(ctx, 'error.Forbidden', {'error': error}, log_type='error', author=ctx.author)
            await ctx.send(text(ctx.guild.id, glob, "The command failed because I don't have the required permissions.\n Please give me the required permissions and try again."))

        elif isinstance(error, dc_commands.CheckFailure):
            err_msg = f'Error for ({ctx.author}) -> ({ctx.command}) with error ({error})'
            log(ctx, err_msg, log_type='error', author=ctx.author)
            await send_to_admin(glob, err_msg, file=True)
            await ctx.reply(f"（ ͡° ͜ʖ ͡°)つ━☆・。\n"
                            f"⊂　　 ノ 　　　・゜+.\n"
                            f"　しーＪ　　　°。+ ´¨)\n"
                            f"　　　　　　　　　.· ´¸.·´¨) ¸.·*¨)\n"
                            f"　　　　　　　　　　(¸.·´ (¸.·' ☆ **Fuck off**\n"
                            f"*{text(ctx.guild.id, glob, 'You dont have permission to use this command')}*")

        elif isinstance(error, dc_commands.MissingPermissions):
            err_msg = f'Error for ({ctx.author}) -> ({ctx.command}) with error ({error})'
            log(ctx, err_msg, log_type='error', author=ctx.author)
            await ctx.reply(text(ctx.guild.id, glob, 'Bot does not have permissions to execute this command correctly') + f" - {error}")

        # error.__cause__.__cause__ = HybridCommandError -> CommandInvokeError -> {Exception}
        elif isinstance(error.__cause__.__cause__, PendingRollbackError):
            err_msg = f'Error for ({ctx.author}) -> ({ctx.command}) with error ({error})'
            log(ctx, err_msg, log_type='error', author=ctx.author)
            err_msg += "\n" + "-"*50

            try:
                glob.ses.rollback()  # Rollback the session
                err_msg += "\nRollback Successful"
            except Exception as rollback_error:
                rollback_traceback = traceback.format_exception(type(rollback_error), rollback_error, rollback_error.__traceback__)
                rollback_traceback = ''.join(rollback_traceback)

                err_msg = f'\nFailed Rollback with error ({rollback_error})({rollback_traceback})'
                log(ctx, err_msg, log_type='error', author=ctx.author)

            err_msg += "\n" + "-"*50 + "\nOriginal Traceback" + f"\n{error_traceback}"
            await send_to_admin(glob, err_msg, file=True)

            await ctx.reply(f"Database error -> Attempted rollback (try again one time - if it doesn't work tell developer to restart bot)")

        else:
            message = f"Error for ({ctx.author}) -> ({ctx.command}) with error ({error})\n{error_traceback}"
            log(ctx, message, log_type='error', author=ctx.author)

            await send_to_admin(glob, message, file=True)
            await ctx.reply(f"{error}   {bot.get_user(config.DEVELOPER_ID).mention}", ephemeral=True)

    async def on_message(self, message):
        # on every message
        if message.author == bot.user:
            return

        # check if message is a DM
        if not message.guild:
            # send DM to ADMIN
            await send_to_admin(glob, f"<@!{message.author.id}> tied to DM me with this message `{message.content}`")
            try:
                # respond to DM
                await message.channel.send(
                    f"I'm sorry, but I only work in servers.\n\n"
                    f""
                    f"If you want me to join your server, you can invite me with this link: {config.INVITE_URL}\n\n"
                    f""
                    f"If you have any questions, you can DM my developer <@!{config.DEVELOPER_ID}>#4272")
                return

            except discord.errors.Forbidden:
                return

        is_slowed, slowed_for = is_user_slowed(glob, message.author.id, message.guild.id)
        if is_slowed:
            try:
                await message.author.timeout(datetime.timedelta(seconds=slowed_for))
            except discord.Forbidden:
                log(None, 'Timeout Forbidden', {'author_id': message.author.id, 'author_name': message.author.name, 'guild_id': message.guild.id, 'guild_name': message.guild.name}, log_type='error')
                pass

        await bot.process_commands(message)

# ---------------------------------------------- LOAD ------------------------------------------------------------------

log(None, "--------------------------------------- NEW / REBOOTED ----------------------------------------")

build_new_guilds = False
build_old_guilds = False

# with open(f'{config.PARENT_DIR}db/radio.json', 'r', encoding='utf-8') as file:
#     radio_dict = json.load(file)

for radio_name_ in radio_dict:
    radio_info_class = ses.query(video_class.RadioInfo).filter(video_class.RadioInfo.name == radio_name_).first()
    if not radio_info_class:
        radio_info_class = video_class.RadioInfo(radio_dict[radio_name_]['id'])
        ses.add(radio_info_class)
        ses.commit()
        log(None, f'Added {radio_name_} to database')
log(None, 'Loaded radio.json')

# with open(f'{config.PARENT_DIR}db/languages.json', 'r', encoding='utf-8') as file:
#     languages_dict = json.load(file)

# text = languages_dict['en']
authorized_users += [my_id, d_id, config.DEVELOPER_ID, 349164237605568513]
log(None, 'Loaded languages.json')

# ---------------------------------------------- BOT -------------------------------------------------------------------

bot = Bot()

log(None, 'Discord API initialized')

# ---------------------------------------------- SPOTIPY ---------------------------------------------------------------

try:
    credentials = SpotifyClientCredentials(client_id=config.SPOTIFY_CLIENT_ID, client_secret=config.SPOTIFY_CLIENT_SECRET)
    spotify_api = spotipy.Spotify(client_credentials_manager=credentials)
    log(None, 'Spotify API initialized')
except spotipy.oauth2.SpotifyOauthError:
    spotify_api = None
    log(None, 'Failed to initialize Spotify API')

# --------------------------------------------- SOUNDCLOUD -------------------------------------------------------------

try:
    soundcloud_api = SoundcloudAPI(client_id=config.SOUNDCLOUD_CLIENT_ID)
    log(None, 'SoundCloud API initialized')
except Exception as e:
    log(None, f'Failed to initialize SoundCloud API : {e}')
    soundcloud_api = None

# --------------------------------------------- Global Variables --------------------------------------------------------

glob = GlobalVars(bot, ses, spotify_api, soundcloud_api)

# ---------------- Load old guilds ------------

if build_old_guilds:
    with open('db/guilds.json', 'r', encoding='utf-8') as file:
        load_json_to_database(glob, json.load(file))
        log(None, 'Loaded old guilds.json')

# --------------------------------------- QUEUE --------------------------------------------------

@bot.hybrid_command(name='queue', with_app_command=True, description=text(0, glob, 'queue_add'), help=text(0, glob, 'queue_add'))
@app_commands.describe(query=text(0, glob, 'query'), position=text(0, glob, 'pos'))
async def queue_command(ctx: dc_commands.Context, query, position: int = None):
    log(ctx, 'queue', options=locals(), log_type='command', author=ctx.author)
    await queue_command_def(ctx, glob, query, position=position)

@bot.hybrid_command(name='next_up', with_app_command=True, description=text(0, glob, 'next_up'), help=text(0, glob, 'next_up'))
@app_commands.describe(query=text(0, glob, 'query'), user_only=text(0, glob, 'ephemeral'))
async def next_up(ctx: dc_commands.Context, query, user_only: bool = False):
    log(ctx, 'next_up', options=locals(), log_type='command', author=ctx.author)
    await next_up_def(ctx, glob, query, user_only)

@bot.hybrid_command(name='skip', with_app_command=True, description=text(0, glob, 'skip'), help=text(0, glob, 'skip'))
async def skip(ctx: dc_commands.Context):
    log(ctx, 'skip', options=locals(), log_type='command', author=ctx.author)
    await skip_def(ctx, glob)

@bot.hybrid_command(name='remove', with_app_command=True, description=text(0, glob, 'queue_remove'), help=text(0, glob, 'queue_remove'))
@app_commands.describe(song=text(0, glob, 'remove_song'), user_only=text(0, glob, 'ephemeral'))
async def remove(ctx: dc_commands.Context, song, user_only: bool = False):
    log(ctx, 'remove', options=locals(), log_type='command', author=ctx.author)
    await remove_def(ctx, glob, song, ephemeral=user_only)

@bot.hybrid_command(name='clear', with_app_command=True, description=text(0, glob, 'clear'), help=text(0, glob, 'clear'))
@app_commands.describe(user_only=text(0, glob, 'ephemeral'))
async def clear(ctx: dc_commands.Context, user_only: bool = False):
    log(ctx, 'clear', options=locals(), log_type='command', author=ctx.author)
    await clear_def(ctx, glob, user_only)

@bot.hybrid_command(name='shuffle', with_app_command=True, description=text(0, glob, 'shuffle'), help=text(0, glob, 'shuffle'))
@app_commands.describe(user_only=text(0, glob, 'ephemeral'))
async def shuffle(ctx: dc_commands.Context, user_only: bool = False):
    log(ctx, 'shuffle', options=locals(), log_type='command', author=ctx.author)
    await shuffle_def(ctx, glob, user_only)

@bot.hybrid_command(name='show', with_app_command=True, description=text(0, glob, 'queue_show'), help=text(0, glob, 'queue_show'))
@app_commands.describe(display_type=text(0, glob, 'display_type'), user_only=text(0, glob, 'ephemeral'))
async def show(ctx: dc_commands.Context, display_type: Literal['short', 'medium', 'long'] = None,
               list_type: Literal['queue', 'history'] = 'queue', user_only: bool = False):
    log(ctx, 'show', options=locals(), log_type='command', author=ctx.author)
    await show_def(ctx, glob, display_type, list_type, user_only)

@bot.hybrid_command(name='search', with_app_command=True, description=text(0, glob, 'search'), help=text(0, glob, 'search'))
@app_commands.describe(query=text(0, glob, 'search_query'), display_type=text(0, glob, 'display_type'), force=text(0, glob, 'force'), user_only=text(0, glob, 'ephemeral'))
async def search_command(ctx: dc_commands.Context, query, display_type: Literal['short', 'long'] = None, force: bool = False, user_only: bool = False):
    log(ctx, 'search', options=locals(), log_type='command', author=ctx.author)
    await search_command_def(ctx, glob, query, display_type, force, user_only)

# --------------------------------------- PLAYER --------------------------------------------------

@bot.hybrid_command(name='play', with_app_command=True, description=text(0, glob, 'play'), help=text(0, glob, 'play'))
@app_commands.describe(query=text(0, glob, 'query'), force=text(0, glob, 'force'))
async def play(ctx: dc_commands.Context, query=None, force=False):
    log(ctx, 'play', options=locals(), log_type='command', author=ctx.author)
    await play_def(ctx, glob, query, force)

@bot.hybrid_command(name='radio', with_app_command=True, description=text(0, glob, 'radio'), help=text(0, glob, 'radio'))
@app_commands.describe(radio_name=text(0, glob, 'radio_name'))
async def radio(ctx: dc_commands.Context, radio_name: str):
    log(ctx, 'radio', options=locals(), log_type='command', author=ctx.author)
    await radio_def(ctx, glob, radio_name)

@bot.hybrid_command(name='ps', with_app_command=True, description=text(0, glob, 'ps'), help=text(0, glob, 'ps'))
@app_commands.describe(effect_number=text(0, glob, 'effects_number'))
async def ps(ctx: dc_commands.Context, effect_number: app_commands.Range[int, 1, len(sound_effects)]):
    log(ctx, 'ps', options=locals(), log_type='command', author=ctx.author)
    await ps_def(ctx, glob, effect_number)

@bot.hybrid_command(name='nowplaying', with_app_command=True, description=text(0, glob, 'nowplaying'), help=text(0, glob, 'nowplaying'))
@app_commands.describe(user_only=text(0, glob, 'ephemeral'))
async def nowplaying(ctx: dc_commands.Context, user_only: bool = False):
    log(ctx, 'nowplaying', options=locals(), log_type='command', author=ctx.author)
    await now_def(ctx, glob, user_only)

@bot.hybrid_command(name='last', with_app_command=True, description=text(0, glob, 'last'), help=text(0, glob, 'last'))
@app_commands.describe(user_only=text(0, glob, 'ephemeral'))
async def last(ctx: dc_commands.Context, user_only: bool = False):
    log(ctx, 'last', options=locals(), log_type='command', author=ctx.author)
    await last_def(ctx, glob, user_only)

@bot.hybrid_command(name='loop', with_app_command=True, description=text(0, glob, 'loop'), help=text(0, glob, 'loop'))
async def loop_command(ctx: dc_commands.Context):
    log(ctx, 'loop', options=locals(), log_type='command', author=ctx.author)
    await loop_command_def(ctx, glob)

@bot.hybrid_command(name='loop_this', with_app_command=True, description=text(0, glob, 'loop_this'), help=text(0, glob, 'loop_this'))
async def loop_this(ctx: dc_commands.Context):
    log(ctx, 'loop_this', options=locals(), log_type='command', author=ctx.author)
    await loop_command_def(ctx, glob, clear_queue_opt=True)

@bot.hybrid_command(name='earrape', with_app_command=True)
async def earrape_command(ctx: dc_commands.Context):
    log(ctx, 'earrape', options=locals(), log_type='command', author=ctx.author)
    await earrape_command_def(ctx, glob)

# --------------------------------------- VOICE --------------------------------------------------

@bot.hybrid_command(name='stop', with_app_command=True, description=f'Stop the player')
async def stop(ctx: dc_commands.Context):
    log(ctx, 'stop', options=locals(), log_type='command', author=ctx.author)
    await stop_def(ctx, glob)

@bot.hybrid_command(name='pause', with_app_command=True, description=f'Pause the player')
async def pause(ctx: dc_commands.Context):
    log(ctx, 'pause', options=locals(), log_type='command', author=ctx.author)
    await pause_def(ctx, glob)

@bot.hybrid_command(name='resume', with_app_command=True, description=f'Resume the player')
async def resume(ctx: dc_commands.Context):
    log(ctx, 'resume', options=locals(), log_type='command', author=ctx.author)
    await resume_def(ctx, glob)

@bot.hybrid_command(name='join', with_app_command=True, description=text(0, glob, 'join'), help=text(0, glob, 'join'))
@app_commands.describe(channel=text(0, glob, 'channel'))
async def join(ctx: dc_commands.Context, channel: discord.VoiceChannel=None):
    log(ctx, 'join', options=locals(), log_type='command', author=ctx.author)
    await join_def(ctx, glob, channel_id=channel.id if channel else None)

@bot.hybrid_command(name='disconnect', with_app_command=True, description=text(0, glob, 'die'), help=text(0, glob, 'die'))
async def disconnect(ctx: dc_commands.Context):
    log(ctx, 'disconnect', options=locals(), log_type='command', author=ctx.author)
    await disconnect_def(ctx, glob)

@bot.hybrid_command(name='volume', with_app_command=True, description=text(0, glob, 'volume'), help=text(0, glob, 'volume'))
@app_commands.describe(volume=text(0, glob, 'volume'), user_only=text(0, glob, 'ephemeral'))
async def volume_command(ctx: dc_commands.Context, volume: int=None, user_only: bool = False):
    log(ctx, 'volume', options=locals(), log_type='command', author=ctx.author)
    await volume_command_def(ctx, glob, volume, user_only)

# --------------------------------------- MENU --------------------------------------------------

@bot.tree.context_menu(name='Play now')
async def play_now(inter, message: discord.Message):
    ctx = await bot.get_context(inter)
    log(ctx, 'play_now', options=locals(), log_type='command', author=ctx.author)

    if ctx.author.voice is None:
        await inter.response.send_message(content=text(ctx.guild.id, glob, 'You are **not connected** to a voice channel'),
                                          ephemeral=True)
        return

    url, probe_data = get_content_of_message(glob, message)

    response: ReturnData = await queue_command_def(ctx, glob, url, mute_response=True, probe_data=probe_data, ephemeral=True,
                                                   position=0, from_play=True)
    if response:
        if response.response:
            await play_def(ctx, glob, force=True)
        else:
            if not inter.response.is_done():
                await inter.response.send_message(content=response.message, ephemeral=True)

@bot.tree.context_menu(name='Add to queue')
async def add_to_queue(inter, message: discord.Message):
    ctx = await bot.get_context(inter)
    log(ctx, 'add_to_queue', options=locals(), log_type='command', author=ctx.author)

    url, probe_data = get_content_of_message(glob, message)

    response: ReturnData = await queue_command_def(ctx, glob, url, mute_response=True, probe_data=probe_data, ephemeral=True)
    if not inter.response.is_done():
        await inter.response.send_message(content=response.message, ephemeral=True)

# @bot.tree.context_menu(name='Show Profile')
# async def show_profile(inter, member: discord.Member):
#     ctx = await bot.get_context(0, glob, inter)
#     log(ctx, 'show_profile', [member), log_type='command', author=ctx.author)
#
#     embed = discord.Embed(title=f"{member.name}#{member.discriminator}",
#                           description=f"ID: `{member.id}` | Name: `{member.display_name}` | Nickname: `{member.nick}`")
#     embed.add_field(name="Created at", value=member.created_at.strftime("%d/%m/%Y %H:%M:%S"), inline=True)
#     embed.add_field(name="Joined at", value=member.joined_at.strftime("%d/%m/%Y %H:%M:%S"), inline=True)
#
#     embed.add_field(name="Roles", value=", ".join([role.mention for role in member.roles[1:))), inline=False)
#
#     embed.add_field(name='Top Role', value=f'{member.top_role.mention}', inline=True)
#
#     # noinspection PyUnresolvedReferences
#     embed.add_field(name='Badges', value=', '.join([badge.name for badge in member.public_flags.all())), inline=False)
#
#     embed.add_field(name='Avatar',
#                     value=f'[Default Avatar)({member.avatar}) | [Display Avatar)({member.display_avatar})',
#                     inline=False)
#
#     embed.add_field(name='Activity', value=f'`{member.activity}`', inline=False)
#
#     embed.add_field(name='Activities', value=f'`{member.activities}`', inline=True)
#     embed.add_field(name='Status', value=f'`{member.status}`', inline=True)
#     embed.add_field(name='Web Status', value=f'`{member.web_status}`', inline=True)
#
#     embed.add_field(name='Raw Status', value=f'`{member.raw_status}`', inline=True)
#     embed.add_field(name='Desktop Status', value=f'`{member.desktop_status}`', inline=True)
#     embed.add_field(name='Mobile Status', value=f'`{member.mobile_status}`', inline=True)
#
#     embed.add_field(name='Voice', value=f'`{member.voice}`', inline=False)
#
#     embed.add_field(name='Premium Since', value=f'`{member.premium_since}`', inline=False)
#
#     embed.add_field(name='Accent Color', value=f'`{member.accent_color}`', inline=True)
#     embed.add_field(name='Color', value=f'`{member.color}`', inline=True)
#     embed.add_field(name='Banner', value=f'`{member.banner}`', inline=True)
#
#     embed.add_field(name='System', value=f'`{member.system}`', inline=True)
#     embed.add_field(name='Pending', value=f'`{member.pending}`', inline=True)
#     embed.add_field(name='Bot', value=f'`{member.bot}`', inline=True)
#
#     embed.set_thumbnail(url=member.avatar)
#     await inter.response.send_message(embed=embed, ephemeral=True)

# --------------------------------------- GENERAL --------------------------------------------------

@bot.hybrid_command(name='ping', with_app_command=True, description=text(0, glob, 'ping'), help=text(0, glob, 'ping'))
async def ping_command(ctx: dc_commands.Context):
    log(ctx, 'ping', options=locals(), log_type='command', author=ctx.author)
    await ping_def(ctx, glob)

# noinspection PyTypeHints
@bot.hybrid_command(name='language', with_app_command=True, description=text(0, glob, 'language'), help=text(0, glob, 'language'))
@app_commands.describe(country_code=text(0, glob, 'country_code'))
async def language_command(ctx: dc_commands.Context, country_code: Literal[tuple(languages_dict.keys())]):
    log(ctx, 'language', options=locals(), log_type='command', author=ctx.author)

    await language_command_def(ctx, glob, country_code)

@bot.hybrid_command(name='sound_effects', with_app_command=True, description=text(0, glob, 'sound'), help=text(0, glob, 'sound'))
@app_commands.describe(user_only=text(0, glob, 'ephemeral'))
async def sound_effects(ctx: dc_commands.Context, user_only: bool = True):
    log(ctx, 'sound_effects', options=locals(), log_type='command', author=ctx.author)

    await sound_effects_def(ctx, glob, user_only)

@bot.hybrid_command(name='list_radios', with_app_command=True, description=text(0, glob, 'list_radios'), help=text(0, glob, 'list_radios'))
@app_commands.describe(user_only=text(0, glob, 'ephemeral'))
async def list_radios(ctx: dc_commands.Context, user_only: bool = True):
    log(ctx, 'list_radios', options=locals(), log_type='command', author=ctx.author)

    await list_radios_def(ctx, glob, user_only)

@bot.hybrid_command(name='key', with_app_command=True, description=text(0, glob, 'key'), help=text(0, glob, 'key'))
async def key_command(ctx: dc_commands.Context):
    log(ctx, 'key', options=locals(), log_type='command', author=ctx.author)

    await key_def(ctx, glob)

# noinspection PyTypeHints
@bot.hybrid_command(name='options', with_app_command=True, description=text(0, glob, 'options'), help=text(0, glob, 'options'))
@app_commands.describe(volume='In percentage (200 max)',
                       buffer='In seconds (what time to wait after no music is playing to disconnect)',
                       language='Language code', response_type='short/long -> embeds/plain text',
                       buttons='Whether to show player control single on messages', loop='True, False',
                       history_length='Number of items in history (100 max)')
async def options_command(ctx: dc_commands.Context,
                          loop: bool = None,
                          language: Literal[tuple(languages_dict.keys())] = None,
                          response_type: Literal['short', 'long'] = None,
                          buttons: bool = None,
                          volume: discord.ext.commands.Range[int, 0, 200]=None,
                          buffer: discord.ext.commands.Range[int, 5, 3600] = None,
                          history_length: discord.ext.commands.Range[int, 1, 100] = None):
    log(ctx, 'options', options=locals(), log_type='command', author=ctx.author)

    await options_command_def(ctx, glob, loop=loop, language=language, response_type=response_type, buttons=buttons, volume=volume, buffer=buffer, history_length=history_length)

# ---------------------------------------------- AUTOCOMPLETE ----------------------------------------------------------

@radio.autocomplete('radio_name')
async def radio_autocomplete(ctx: discord.Interaction, current: str):
    return await radio_autocomplete_def(ctx, current)

@remove.autocomplete('song')
async def song_autocomplete(ctx: discord.Interaction, current: str):
    return await song_autocomplete_def(ctx, current, glob)

@queue_command.autocomplete('query')
@next_up.autocomplete('query')
@play.autocomplete('query')
async def query_autocomplete(ctx: discord.Interaction, query: str):
    return await query_autocomplete_def(ctx, query)



# ---------------------------------------- ADMIN --------------------------------------------------

async def is_authorised(ctx):
    if ctx.author.id in authorized_users or ctx.author.id == d_id or ctx.author.id == 349164237605568513 or ctx.author.id == config.DEVELOPER_ID:
        return True

@bot.hybrid_command(name='zz_announce', with_app_command=True)
@dc_commands.check(is_authorised)
async def announce_command(ctx: dc_commands.Context, message):
    log(ctx, 'announce', options=locals(), log_type='command', author=ctx.author)
    await announce_command_def(ctx, glob, message)

@bot.hybrid_command(name='zz_kys', with_app_command=True)
@dc_commands.check(is_authorised)
async def kys(ctx: dc_commands.Context):
    log(ctx, 'kys', options=locals(), log_type='command', author=ctx.author)
    await kys_def(ctx, glob)

# noinspection PyTypeHints
@bot.hybrid_command(name='zz_options', with_app_command=True)
@app_commands.describe(server='all, this, {guild_id}',
                       volume='No division',
                       buffer='In seconds',
                       language='Language code',
                       response_type='short, long',
                       buttons='True, False',
                       is_radio='True, False',
                       loop='True, False',
                       stopped='True, False',
                       history_length='Number of items in history (100 is probably a lot)')
@dc_commands.check(is_authorised)
async def change_options(ctx: dc_commands.Context,
                         server: discord.ext.commands.GuildConverter=None,
                         stopped: bool = None,
                         loop: bool = None,
                         is_radio: bool = None,
                         buttons: bool = None,
                         language: Literal[tuple(languages_dict.keys())] = None,
                         response_type: Literal['short', 'long'] = None,
                         buffer: int = None,
                         history_length: int = None,
                         volume: int = None,
                         search_query: str = None,
                         last_updated: int = None):
    log(ctx, 'zz_change_options', options=locals(), log_type='command', author=ctx.author)

    await options_def(ctx, glob,
                      server=str(server),
                      stopped=str(stopped),
                      loop=str(loop),
                      is_radio=str(is_radio),
                      buttons=str(buttons),
                      language=str(language),
                      response_type=str(response_type),
                      buffer=str(buffer),
                      history_length=str(history_length),
                      volume=str(volume),
                      search_query=str(search_query),
                      last_updated=str(last_updated))

@bot.hybrid_command(name='zz_download_guild', with_app_command=True)
@dc_commands.check(is_authorised)
async def download_guild_command(ctx: dc_commands.Context, guild_id, ephemeral: bool=True):
    log(ctx, 'download_guild', options=locals(), log_type='command', author=ctx.author)
    await download_guild(ctx, glob, guild_id, ephemeral=ephemeral)

@bot.hybrid_command(name='zz_download_guild_channel', with_app_command=True)
@dc_commands.check(is_authorised)
async def download_guild_channel_command(ctx: dc_commands.Context, channel_id, ephemeral: bool=True):
    log(ctx, 'download_guild_channel', options=locals(), log_type='command', author=ctx.author)
    await download_guild_channel(ctx, glob, channel_id, ephemeral=ephemeral)

@bot.hybrid_command(name='zz_get_guild', with_app_command=True)
@dc_commands.check(is_authorised)
async def get_guild_command(ctx: dc_commands.Context, guild_id, ephemeral: bool=True):
    log(ctx, 'get_guild', options=locals(), log_type='command', author=ctx.author)
    await get_guild(ctx, glob, guild_id, ephemeral=ephemeral)

@bot.hybrid_command(name='zz_get_guild_channel', with_app_command=True)
@dc_commands.check(is_authorised)
async def get_guild_channel_command(ctx: dc_commands.Context, channel_id, ephemeral: bool=True):
    log(ctx, 'get_guild_channel', options=locals(), log_type='command', author=ctx.author)
    await get_guild_channel(ctx, glob, channel_id, ephemeral=ephemeral)

@bot.hybrid_command(name='zz_set_time', with_app_command=True)
@dc_commands.check(is_authorised)
async def set_time_command(ctx: dc_commands.Context, time_stamp: int, ephemeral: bool=True, mute_response: bool=False):
    log(ctx, 'set_time', options=locals(), log_type='command', author=ctx.author)
    await set_video_time(ctx, glob, time_stamp, ephemeral=ephemeral, mute_response=mute_response)

# ------------------------------------------ ADMIN SLOWED USERS --------------------------------------------------------

@bot.hybrid_command(name='zz_slowed_users', with_app_command=True)
@dc_commands.check(is_authorised)
async def slowed_users_command(ctx: dc_commands.Context):
    log(ctx, 'slowed_users', options=locals(), log_type='command', author=ctx.author)
    await slowed_users_command_def(ctx, glob)

@bot.hybrid_command(name='zz_slowed_users_add', with_app_command=True)
@dc_commands.check(is_authorised)
async def slowed_users_add_command(ctx: dc_commands.Context, member: discord.Member, time: int):
    log(ctx, 'slowed_users_add', options=locals(), log_type='command', author=ctx.author)
    await slowed_users_add_command_def(ctx, glob, member, time)

@bot.hybrid_command(name='zz_slowed_users_add_all', with_app_command=True)
@dc_commands.check(is_authorised)
async def slowed_users_add_all_command(ctx: dc_commands.Context, guild_obj: discord.Guild, time: int):
    log(ctx, 'slowed_users_add_all', options=locals(), log_type='command', author=ctx.author)
    await slowed_users_add_all_command_def(ctx, glob, guild_obj, time)

@bot.hybrid_command(name='zz_slowed_users_remove', with_app_command=True)
@dc_commands.check(is_authorised)
async def slowed_users_remove_command(ctx: dc_commands.Context, member: discord.Member):
    log(ctx, 'slowed_users_remove', options=locals(), log_type='command', author=ctx.author)
    await slowed_users_remove_command_def(ctx, glob, member)

@bot.hybrid_command(name='zz_slowed_users_remove_all', with_app_command=True)
@dc_commands.check(is_authorised)
async def slowed_users_remove_all_command(ctx: dc_commands.Context, guild_obj: discord.Guild):
    log(ctx, 'slowed_users_remove_all', options=locals(), log_type='command', author=ctx.author)
    await slowed_users_remove_all_command_def(ctx, glob, guild_obj)

# ------------------------------------------ SPECIFIC USER TORTURE -----------------------------------------------------

@bot.hybrid_command(name='zz_voice_torture', with_app_command=True)
@dc_commands.check(is_authorised)
@dc_commands.has_guild_permissions(move_members=True)
async def voice_torture_command(ctx: dc_commands.Context, member: discord.Member, delay: int):
    log(ctx, 'voice_torture', options=locals(), log_type='command', author=ctx.author)
    await voice_torture_command_def(ctx, glob, member, delay)

@bot.hybrid_command(name='zz_voice_torture_stop', with_app_command=True)
@dc_commands.check(is_authorised)
async def voice_torture_stop_command(ctx: dc_commands.Context, member: discord.Member):
    log(ctx, 'voice_torture_stop', options=locals(), log_type='command', author=ctx.author)
    await voice_torture_stop_command_def(ctx, glob, member)

# --------------------------------------------- HELP COMMAND -----------------------------------------------------------

bot.remove_command('help')

@bot.hybrid_command(name='help', with_app_command=True, description='List all available commands', help='List all available commands')
@app_commands.describe(general='General commands', player='Player commands', queue='Queue commands', voice='Voice commands')
async def help_command(ctx: dc_commands.Context,
                       general: Literal['help', 'ping', 'language', 'sound_effects', 'list_radios'] = None,
                       player: Literal['play', 'radio', 'ps', 'skip', 'nowplaying', 'last', 'loop', 'loop_this'] = None,
                       queue: Literal['queue', 'queue_import', 'queue_export', 'remove', 'clear', 'shuffle', 'show', 'search'] = None,
                       voice: Literal['stop', 'pause', 'resume', 'join', 'disconnect', 'volume'] = None
                       ):
    log(ctx, 'help', options=locals(), log_type='command', author=ctx.author)
    gi = ctx.guild.id

    if general:
        command = general
    elif player:
        command = player
    elif queue:
        command = queue
    elif voice:
        command = voice
    else:
        command = None

    embed = discord.Embed(title="Help",
                          description=f"Use `/help <command>` to get help on a command | Prefix: `{prefix}`")
    embed.add_field(name="General", value=f"`/help` - {text(gi, glob, 'help')}\n"
                                          f"`/ping` - {text(gi, glob, 'ping')}\n"
                                          f"`/language` - {text(gi, glob, 'language')}\n"
                                          f"`/sound_ effects` - {text(gi, glob, 'sound')}\n"
                                          f"`/list_radios` - {text(gi, glob, 'list_radios')}\n"
                                          f"`/key` - {text(gi, glob, 'key')}\n",
                    inline=False)
    embed.add_field(name="Player", value=f"`/play` - {text(gi, glob, 'play')}\n"
                                         f"`/radio` - {text(gi, glob, 'radio')}\n"
                                         f"`/ps` - {text(gi, glob, 'ps')}\n"
                                         f"`/skip` - {text(gi, glob, 'skip')}\n"
                                         f"`/nowplaying` - {text(gi, glob, 'nowplaying')}\n"
                                         f"`/last` - {text(gi, glob, 'last')}\n"
                                         f"`/loop` - {text(gi, glob, 'loop')}\n"
                                         f"`/loop_this` - {text(gi, glob, 'loop_this')}\n",
                    inline=False)
    embed.add_field(name="Queue", value=f"`/queue` - {text(gi, glob, 'queue_add')}\n"
                                        # f"`/queue_import` - {text(gi, glob, 'queue_import')}\n"
                                        # f"`/queue_export` - {text(gi, glob, 'queue_export')}\n"
                                        f"`/remove` - {text(gi, glob, 'queue_remove')}\n"
                                        f"`/clear` - {text(gi, glob, 'clear')}\n"
                                        f"`/shuffle` - {text(gi, glob, 'shuffle')}\n"
                                        f"`/show` - {text(gi, glob, 'queue_show')}\n"
                                        f"`/search` - {text(gi, glob, 'search')}",
                    inline=False)
    embed.add_field(name="Voice", value=f"`/stop` - {text(gi, glob, 'stop')}\n"
                                        f"`/pause` - {text(gi, glob, 'pause')}\n"
                                        f"`/resume` - {text(gi, glob, 'resume')}\n"
                                        f"`/join` - {text(gi, glob, 'join')}\n"
                                        f"`/disconnect` - {text(gi, glob, 'die')}\n"
                                        f"`/volume` - {text(gi, glob, 'volume')}",
                    inline=False)
    embed.add_field(name="Context Menu", value=f"`Add to queue` - {text(gi, glob, 'queue_add')}\n"
                                               # f"`Show Profile` - {text(gi, glob, 'profile')}\n"
                                               f"`Play now` - {text(gi, glob, 'play')}")

    if command == 'help':
        embed = discord.Embed(title="Help", description=f"`/help` - {text(gi, glob, 'help')}")
        embed.add_field(name=f"{text(gi, glob, 'Arguments')}", value=f"`general` - {text(gi, glob, 'The commands from')} General\n"
                                                                     f"`player` - {text(gi, glob, 'The commands from')} Player\n"
                                                                     f"`queue` - {text(gi, glob, 'The commands from')} Queue\n"
                                                                     f"`voice` - {text(gi, glob, 'The commands from')} Voice",
                        inline=False)

    elif command == 'ping':
        embed = discord.Embed(title="Help", description=f"`/ping` - {text(gi, glob, 'ping')}")

    elif command == 'language':
        embed = discord.Embed(title="Help", description=f"`/language` - {text(gi, glob, 'language')}")
        embed.add_field(name=f"{text(gi, glob, 'Arguments')}", value=f"`country_code` - {text(gi, glob, 'country_code')}", inline=False)

    elif command == 'sound_effects':
        embed = discord.Embed(title="Help", description=f"`/sound_effects` - {text(gi, glob, 'sound')}")
        embed.add_field(name=f"{text(gi, glob, 'Arguments')}", value=f"`user_only` - {text(gi, glob, 'ephemeral')}", inline=False)

    elif command == 'list_radios':
        embed = discord.Embed(title="Help", description=f"`/list_radios` - {text(gi, glob, 'list_radios')}")
        embed.add_field(name=f"{text(gi, glob, 'Arguments')}", value=f"`user_only` - {text(gi, glob, 'ephemeral')}", inline=False)

    elif command == 'key':
        embed = discord.Embed(title="Help", description=f"`/key` - {text(gi, glob, 'key')}")

    elif command == 'play':
        embed = discord.Embed(title="Help", description=f"`/play` - {text(gi, glob, 'play')}")
        embed.add_field(name=f"{text(gi, glob, 'Arguments')}", value=f"`url` - {text(gi, glob, 'url')}", inline=False)
        embed.add_field(name="", value=f"`force` - {text(gi, glob, 'force')}", inline=False)

    elif command == 'radio':
        embed = discord.Embed(title="Help", description=f"`/radio` - {text(gi, glob, 'radio')}")
        embed.add_field(name=f"{text(gi, glob, 'Arguments')}", value=f"`favourite_radio` - {text(gi, glob, 'favourite_radio')}",
                        inline=False)
        embed.add_field(name="", value=f"`radio_code` - {text(gi, glob, 'radio_code')}", inline=False)

    elif command == 'ps':
        embed = discord.Embed(title="Help", description=f"`/ps` - {text(gi, glob, 'ps')}")
        embed.add_field(name=f"{text(gi, glob, 'Arguments')}", value=f"`effect_number` - {text(gi, glob, 'effects_number')}",
                        inline=False)

    elif command == 'skip':
        embed = discord.Embed(title="Help", description=f"`/skip` - {text(gi, glob, 'skip')}")

    elif command == 'nowplaying':
        embed = discord.Embed(title="Help", description=f"`/nowplaying` - {text(gi, glob, 'nowplaying')}")
        embed.add_field(name=f"{text(gi, glob, 'Arguments')}", value=f"`user_only` - {text(gi, glob, 'ephemeral')}", inline=False)

    elif command == 'last':
        embed = discord.Embed(title="Help", description=f"`/last` - {text(gi, glob, 'last')}")
        embed.add_field(name=f"{text(gi, glob, 'Arguments')}", value=f"`user_only` - {text(gi, glob, 'ephemeral')}", inline=False)

    elif command == 'loop':
        embed = discord.Embed(title="Help", description=f"`/loop` - {text(gi, glob, 'loop')}")

    elif command == 'loop_this':
        embed = discord.Embed(title="Help", description=f"`/loop_this` - {text(gi, glob, 'loop_this')}")

    elif command == 'queue':
        embed = discord.Embed(title="Help", description=f"`/queue` - {text(gi, glob, 'queue_add')}")
        embed.add_field(name=f"{text(gi, glob, 'Arguments')}", value=f"`url` - {text(gi, glob, 'url')}", inline=False)
        embed.add_field(name="", value=f"`position` - {text(gi, glob, 'pos')}", inline=False)
        embed.add_field(name="", value=f"`mute_response` - {text(gi, glob, 'mute_response')}", inline=False)
        embed.add_field(name="", value=f"`force` - {text(gi, glob, 'force')}", inline=False)

    elif command == 'queue_import':
        embed = discord.Embed(title="Help", description=f"`/queue_import` - {text(gi, glob, 'queue_import')}")
        embed.add_field(name=f"{text(gi, glob, 'Arguments')}", value=f"`queue_string` - {text(gi, glob, 'queue_string')}", inline=False)
        embed.add_field(name="", value=f"`guild_id` - {text(gi, glob, 'guild_id')}", inline=False)
        embed.add_field(name="", value=f"`user_only` - {text(gi, glob, 'ephemeral')}", inline=False)

    elif command == 'queue_export':
        embed = discord.Embed(title="Help", description=f"`/queue_export` - {text(gi, glob, 'queue_export')}")
        embed.add_field(name=f"{text(gi, glob, 'Arguments')}", value=f"`guild_id` - {text(gi, glob, 'guild_id')}", inline=False)
        embed.add_field(name="", value=f"`user_only` - {text(gi, glob, 'ephemeral')}", inline=False)

    elif command == 'next_up':
        embed = discord.Embed(title="Help", description=f"`/next_up` - {text(gi, glob, 'next_up')}")
        embed.add_field(name=f"{text(gi, glob, 'Arguments')}", value=f"`url` - {text(gi, glob, 'url')}", inline=False)
        embed.add_field(name="", value=f"`user_only` - {text(gi, glob, 'ephemeral')}", inline=False)

    elif command == 'remove':
        embed = discord.Embed(title="Help", description=f"`/remove` - {text(gi, glob, 'remove')}")
        embed.add_field(name=f"{text(gi, glob, 'Arguments')}", value=f"`number` - {text(gi, glob, 'number')}", inline=False)
        embed.add_field(name="", value=f"`user_only` - {text(gi, glob, 'ephemeral')}", inline=False)

    elif command == 'clear':
        embed = discord.Embed(title="Help", description=f"`/clear` - {text(gi, glob, 'clear')}")
        embed.add_field(name=f"{text(gi, glob, 'Arguments')}", value=f"`user_only` - {text(gi, glob, 'ephemeral')}", inline=False)

    elif command == 'shuffle':
        embed = discord.Embed(title="Help", description=f"`/shuffle` - {text(gi, glob, 'shuffle')}")
        embed.add_field(name=f"{text(gi, glob, 'Arguments')}", value=f"`user_only` - {text(gi, glob, 'ephemeral')}", inline=False)

    elif command == 'show':
        embed = discord.Embed(title="Help", description=f"`/show` - {text(gi, glob, 'show')}")
        embed.add_field(name=f"{text(gi, glob, 'Arguments')}", value=f"`display_type` - {text(gi, glob, 'display_type')}", inline=False)
        embed.add_field(name="", value=f"`user_only` - {text(gi, glob, 'ephemeral')}", inline=False)

    elif command == 'search':
        embed = discord.Embed(title="Help", description=f"`/search` - {text(gi, glob, 'search')}")
        embed.add_field(name=f"{text(gi, glob, 'Arguments')}", value=f"`search_query` - {text(gi, glob, 'search_query')}", inline=False)
        embed.add_field(name="", value=f"`user_only` - {text(gi, glob, 'ephemeral')}", inline=False)

    elif command == 'stop':
        embed = discord.Embed(title="Help", description=f"`/stop` - {text(gi, glob, 'stop')}")

    elif command == 'pause':
        embed = discord.Embed(title="Help", description=f"`/pause` - {text(gi, glob, 'pause')}")

    elif command == 'resume':
        embed = discord.Embed(title="Help", description=f"`/resume` - {text(gi, glob, 'resume')}")

    elif command == 'join':
        embed = discord.Embed(title="Help", description=f"`/join` - {text(gi, glob, 'join')}")
        embed.add_field(name=f"{text(gi, glob, 'Arguments')}", value=f"`channel_id` - {text(gi, glob, 'channel_id')}", inline=False)

    elif command == 'disconnect':
        embed = discord.Embed(title="Help", description=f"`/disconnect` - {text(gi, glob, 'die')}")

    elif command == 'volume':
        embed = discord.Embed(title="Help", description=f"`/volume` - {text(gi, glob, 'volume')}")
        embed.add_field(name=f"{text(gi, glob, 'Arguments')}", value=f"`volume` - {text(gi, glob, 'volume')}", inline=False)
        embed.add_field(name="", value=f"`user_only` - {text(gi, glob, 'ephemeral')}", inline=False)

    await ctx.reply(embed=embed, ephemeral=True)

# --------------------------------------------------- APP --------------------------------------------------------------

def application():
    web_thread = threading.Thread(target=ipc_run, kwargs={'glob': glob})
    bot_thread = threading.Thread(target=bot.run, kwargs={'token': config.BOT_TOKEN})

    web_thread.start()
    bot_thread.start()

    web_thread.join()
    bot_thread.join()


if __name__ == '__main__':
    application()
