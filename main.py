from classes.data_classes import WebData, Guild
from classes.typed_dictionaries import LastUpdated
from classes.video_class import History, NowPlaying, SaveVideo

from commands.autocomplete import *

from utils.discord import get_content_of_message
from utils.log import send_to_admin
from utils.json import *
from utils.save import update_db_commands

from ipc.server import ipc_run

from commands.admin import *
from commands.chat_export import *
from commands.general import *
from commands.player import *
from commands.queue import *
from commands.radio import *
from commands.voice import *

from sclib import SoundcloudAPI
from spotipy.oauth2 import SpotifyClientCredentials
from discord.ext import commands as dc_commands
from discord import app_commands

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
            await fix_guilds()
            update_db_commands(glob)
            log(None, "Updated database commands")
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
        await download_guild(WebData(guild_object.id, {'id': bot.user.id, 'name': bot.user.name}), glob, guild_object.id,
                             mute_response=True, ephemeral=True)

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
            await now_to_history(glob, guild_id)

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
                    log(guild_id,
                        f"-->> Disconnecting after {guild(glob, guild_id).options.buffer} seconds of no play <<--")

                    # save history
                    await now_to_history(glob, guild_id)

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
            await ctx.send(txt(ctx.guild.id, glob, "The command failed because I don't have the required permissions.\n Please give me the required permissions and try again."))

        elif isinstance(error, dc_commands.CheckFailure):
            err_msg = f'Error for ({ctx.author}) -> ({ctx.command}) with error ({error})'
            log(ctx, err_msg, log_type='error', author=ctx.author)
            await send_to_admin(glob, err_msg, file=True)
            await ctx.reply(f"（ ͡° ͜ʖ ͡°)つ━☆・。\n"
                            f"⊂　　 ノ 　　　・゜+.\n"
                            f"　しーＪ　　　°。+ ´¨)\n"
                            f"　　　　　　　　　.· ´¸.·´¨) ¸.·*¨)\n"
                            f"　　　　　　　　　　(¸.·´ (¸.·' ☆ **Fuck off**\n"
                            f"*{txt(ctx.guild.id, glob, 'You dont have permission to use this command')}*")

        elif isinstance(error, dc_commands.MissingPermissions):
            err_msg = f'Error for ({ctx.author}) -> ({ctx.command}) with error ({error})'
            log(ctx, err_msg, log_type='error', author=ctx.author)
            await ctx.reply(txt(ctx.guild.id, glob, 'Bot does not have permissions to execute this command correctly') + f" - {error}")

        # error.__cause__.__cause__ = HybridCommandError -> CommandInvokeError -> {Exception}
        elif isinstance(error.__cause__.__cause__, PendingRollbackError):
            err_msg = f'Error for ({ctx.author}) -> ({ctx.command}) with error ({error})'
            log(ctx, err_msg, log_type='error', author=ctx.author)
            err_msg += "\n" + "-" * 50

            try:
                glob.ses.rollback()  # Rollback the session
                err_msg += "\nRollback Successful"
            except Exception as rollback_error:
                rollback_traceback = traceback.format_exception(type(rollback_error), rollback_error,
                                                                rollback_error.__traceback__)
                rollback_traceback = ''.join(rollback_traceback)

                err_msg = f'\nFailed Rollback with error ({rollback_error})({rollback_traceback})'
                log(ctx, err_msg, log_type='error', author=ctx.author)

            err_msg += "\n" + "-" * 50 + "\nOriginal Traceback" + f"\n{error_traceback}"
            await send_to_admin(glob, err_msg, file=True)

            await ctx.reply(
                f"Database error -> Attempted rollback (try again one time - if it doesn't work tell developer to restart bot)")

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
                log(None, 'Timeout Forbidden',
                    {'author_id': message.author.id, 'author_name': message.author.name, 'guild_id': message.guild.id,
                     'guild_name': message.guild.name}, log_type='error')
                pass

        await bot.process_commands(message)

# ---------------------------------------------- LOAD ------------------------------------------------------------------

log(None, "--------------------------------------- NEW / REBOOTED ----------------------------------------")

build_new_guilds = False
build_old_guilds = False

# for radio_name_ in radio_dict:
#     radio_info_class = ses.query(video_class.RadioInfo).filter(video_class.RadioInfo.name == radio_name_).first()
#     if not radio_info_class:
#         radio_info_class = video_class.RadioInfo(radio_dict[radio_name_]['id'])
#         ses.add(radio_info_class)
#         ses.commit()
#         log(None, f'Added {radio_name_} to database')
log(None, 'Loaded radio.json')

authorized_users += [my_id, d_id, config.DEVELOPER_ID, 349164237605568513]
log(None, 'Loaded languages.json')

# ---------------------------------------------- BOT -------------------------------------------------------------------

bot = Bot()

log(None, 'Discord API initialized')

# ---------------------------------------------- SPOTIPY ---------------------------------------------------------------

try:
    credentials = SpotifyClientCredentials(client_id=config.SPOTIFY_CLIENT_ID,
                                           client_secret=config.SPOTIFY_CLIENT_SECRET)
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

# ---------------- set last_updated and keep_alive ------------

async def fix_guilds():
    for guild_obj in glob.ses.query(Guild).all():
        guild_obj.last_updated = {key: int(time()) for key in LastUpdated.__annotations__.keys()}
        guild_obj.keep_alive = True
    glob.ses.commit()

    for vid in glob.ses.query(Queue).all():
        if vid.author is None:
            vid.author = {'id': 0, 'name': 'Unknown'}
    glob.ses.commit()

    for hist in glob.ses.query(History).all():
        if hist.author is None:
            hist.author = {'id': 0, 'name': 'Unknown'}
    glob.ses.commit()

    for np in glob.ses.query(NowPlaying).all():
        if np.author is None:
            np.author = {'id': 0, 'name': 'Unknown'}
    glob.ses.commit()

    for sv in glob.ses.query(SaveVideo).all():
        if sv.author is None:
            sv.author = {'id': 0, 'name': 'Unknown'}
    glob.ses.commit()

    ___tasks = []
    for guild_obj in bot.guilds:
        ___tasks.append(now_to_history(glob, guild_obj.id))
    await asyncio.gather(*___tasks)

    log(None, 'Set attributes for new start')

# --------------------------------------- QUEUE --------------------------------------------------

@bot.hybrid_command(name='queue', with_app_command=True, description=txt(0, glob, 'command_queue'),
                    help=txt(0, glob, 'command_queue'), extras={'category': 'queue'})
@app_commands.describe(query=txt(0, glob, 'query'), position=txt(0, glob, 'attr_queue_position'))
async def queue_command(ctx: dc_commands.Context, query, position: int = None):
    log(ctx, 'queue', options=locals(), log_type='command', author=ctx.author)
    await queue_command_def(ctx, glob, query, position=position)

@bot.hybrid_command(name='nextup', with_app_command=True, description=txt(0, glob, 'command_nextup'),
                    help=txt(0, glob, 'command_nextup'), extras={'category': 'queue'})
@app_commands.describe(query=txt(0, glob, 'query'), user_only=txt(0, glob, 'ephemeral'))
async def nextup(ctx: dc_commands.Context, query, user_only: bool = False):
    log(ctx, 'nextup', options=locals(), log_type='command', author=ctx.author)
    await nextup_def(ctx, glob, query, user_only)

@bot.hybrid_command(name='skip', with_app_command=True, description=txt(0, glob, 'command_skip'), help=txt(0, glob, 'command_skip'), extras={'category': 'queue'})
async def skip(ctx: dc_commands.Context):
    log(ctx, 'skip', options=locals(), log_type='command', author=ctx.author)
    await skip_def(ctx, glob)

@bot.hybrid_command(name='remove', with_app_command=True, description=txt(0, glob, 'command_remove'),
                    help=txt(0, glob, 'command_remove'), extras={'category': 'queue'})
@app_commands.describe(song=txt(0, glob, 'attr_remove_song'), user_only=txt(0, glob, 'ephemeral'))
async def remove(ctx: dc_commands.Context, song, user_only: bool = False):
    log(ctx, 'remove', options=locals(), log_type='command', author=ctx.author)
    await remove_def(ctx, glob, song, ephemeral=user_only)

@bot.hybrid_command(name='clear', with_app_command=True, description=txt(0, glob, 'command_clear'),
                    help=txt(0, glob, 'command_clear'), extras={'category': 'queue'})
@app_commands.describe(user_only=txt(0, glob, 'ephemeral'))
async def clear(ctx: dc_commands.Context, user_only: bool = False):
    log(ctx, 'clear', options=locals(), log_type='command', author=ctx.author)
    await clear_def(ctx, glob, user_only)

@bot.hybrid_command(name='shuffle', with_app_command=True, description=txt(0, glob, 'command_shuffle'),
                    help=txt(0, glob, 'command_shuffle'), extras={'category': 'queue'})
@app_commands.describe(user_only=txt(0, glob, 'ephemeral'))
async def shuffle(ctx: dc_commands.Context, user_only: bool = False):
    log(ctx, 'shuffle', options=locals(), log_type='command', author=ctx.author)
    await shuffle_def(ctx, glob, user_only)

# @bot.hybrid_command(name='show', with_app_command=True, description=txt(0, glob, 'command_show'),
#                     help=txt(0, glob, 'command_show'), extras={'category': 'queue'})
# @app_commands.describe(display_type=txt(0, glob, 'attr_show_display_type'), user_only=txt(0, glob, 'ephemeral'))
# async def show(ctx: dc_commands.Context, display_type: Literal['short', 'medium', 'long'] = None,
#                list_type: Literal['queue', 'history'] = 'queue', user_only: bool = False):
#     log(ctx, 'show', options=locals(), log_type='command', author=ctx.author)
#     await show_def(ctx, glob, display_type, list_type, user_only)

@bot.hybrid_command(name='search', with_app_command=True, description=txt(0, glob, 'command_search'),
                    help=txt(0, glob, 'command_search'), extras={'category': 'queue'})
@app_commands.describe(query=txt(0, glob, 'query'), display_type=txt(0, glob, 'attr_search_display_type'),
                       force=txt(0, glob, 'attr_search_force'), user_only=txt(0, glob, 'ephemeral'))
async def search_command(ctx: dc_commands.Context, query, display_type: Literal['short', 'long'] = None,
                         force: bool = False, user_only: bool = False):
    log(ctx, 'search', options=locals(), log_type='command', author=ctx.author)
    await search_command_def(ctx, glob, query, display_type, force, user_only)

# --------------------------------------- PLAYER --------------------------------------------------

@bot.hybrid_command(name='play', with_app_command=True, description=txt(0, glob, 'command_play'), help=txt(0, glob, 'command_play'), extras={'category': 'player'})
@app_commands.describe(query=txt(0, glob, 'query'), force=txt(0, glob, 'attr_play_force'))
async def play(ctx: dc_commands.Context, query=None, force=False):
    log(ctx, 'play', options=locals(), log_type='command', author=ctx.author)
    await play_def(ctx, glob, query, force)

@bot.hybrid_command(name='ps', with_app_command=True, description=txt(0, glob, 'command_ps'), help=txt(0, glob, 'command_ps'), extras={'category': 'player'})
@app_commands.describe(effect=txt(0, glob, 'attr_ps_effect'))
async def ps(ctx: dc_commands.Context, effect: str):
    log(ctx, 'ps', options=locals(), log_type='command', author=ctx.author)
    await local_def(ctx, glob, effect)

@bot.hybrid_command(name='nowplaying', with_app_command=True, description=txt(0, glob, 'command_nowplaying'),
                    help=txt(0, glob, 'command_nowplaying'), extras={'category': 'player'})
@app_commands.describe(user_only=txt(0, glob, 'ephemeral'))
async def nowplaying(ctx: dc_commands.Context, user_only: bool = False):
    log(ctx, 'nowplaying', options=locals(), log_type='command', author=ctx.author)
    await now_def(ctx, glob, user_only)

@bot.hybrid_command(name='last', with_app_command=True, description=txt(0, glob, 'command_last'), help=txt(0, glob, 'command_last'), extras={'category': 'player'})
@app_commands.describe(user_only=txt(0, glob, 'ephemeral'))
async def last(ctx: dc_commands.Context, user_only: bool = False):
    log(ctx, 'last', options=locals(), log_type='command', author=ctx.author)
    await last_def(ctx, glob, user_only)

@bot.hybrid_command(name='loop', with_app_command=True, description=txt(0, glob, 'command_loop'), help=txt(0, glob, 'command_loop'), extras={'category': 'player'})
async def loop_command(ctx: dc_commands.Context):
    log(ctx, 'loop', options=locals(), log_type='command', author=ctx.author)
    await loop_command_def(ctx, glob)

@bot.hybrid_command(name='loop-this', with_app_command=True, description=txt(0, glob, 'command_loop_this'),
                    help=txt(0, glob, 'command_loop_this'), extras={'category': 'player'})
async def loop_this(ctx: dc_commands.Context):
    log(ctx, 'loop_this', options=locals(), log_type='command', author=ctx.author)
    await loop_command_def(ctx, glob, clear_queue_opt=True)

@bot.hybrid_command(name='earrape', with_app_command=True, description=txt(0, glob, 'command_earrape'),
                    help=txt(0, glob, 'command_earrape'), extras={'category': 'player'})
async def earrape_command(ctx: dc_commands.Context):
    log(ctx, 'earrape', options=locals(), log_type='command', author=ctx.author)
    await earrape_command_def(ctx, glob)

# --------------------------------------- RADIO --------------------------------------------------

@bot.hybrid_command(name='radio-cz', with_app_command=True, description=txt(0, glob, 'command_radio_cz'), help=txt(0, glob, 'command_radio_cz'), extras={'category': 'radio'})
@app_commands.describe(radio=txt(0, glob, 'attr_radio_cz_radio'))
async def radio_cz_command(ctx: dc_commands.Context, radio: str):
    log(ctx, 'radio_cz', options=locals(), log_type='command', author=ctx.author)
    await radio_cz_def(ctx, glob, radio)

@bot.hybrid_command(name='radio-garden', with_app_command=True, description=txt(0, glob, 'command_radio_garden'), help=txt(0, glob, 'command_radio_garden'), extras={'category': 'radio'})
@app_commands.describe(radio=txt(0, glob, 'attr_radio_garden_radio'))
async def radio_garden_command(ctx: dc_commands.Context, radio: str):
    log(ctx, 'radio_garden', options=locals(), log_type='command', author=ctx.author)
    await radio_garden_def(ctx, glob, radio)

@bot.hybrid_command(name='radio-tunein', with_app_command=True, description=txt(0, glob, 'command_radio_tunein'), help=txt(0, glob, 'command_radio_tunein'), extras={'category': 'radio'})
@app_commands.describe(radio=txt(0, glob, 'attr_radio_tunein_radio'))
async def radio_tunein_command(ctx: dc_commands.Context, radio: str):
    log(ctx, 'radio_tunein', options=locals(), log_type='command', author=ctx.author)
    await radio_tunein_def(ctx, glob, radio)

# --------------------------------------- VOICE --------------------------------------------------

@bot.hybrid_command(name='stop', with_app_command=True, description=txt(0, glob, 'command_stop'), help=txt(0, glob, 'command_stop'), extras={'category': 'voice'})
async def stop(ctx: dc_commands.Context):
    log(ctx, 'stop', options=locals(), log_type='command', author=ctx.author)
    await stop_def(ctx, glob)

@bot.hybrid_command(name='pause', with_app_command=True, description=txt(0, glob, 'command_pause'), help=txt(0, glob, 'command_pause'), extras={'category': 'voice'})
async def pause(ctx: dc_commands.Context):
    log(ctx, 'pause', options=locals(), log_type='command', author=ctx.author)
    await pause_def(ctx, glob)

@bot.hybrid_command(name='resume', with_app_command=True, description=txt(0, glob, 'command_resume'), help=txt(0, glob, 'command_resume'), extras={'category': 'voice'})
async def resume(ctx: dc_commands.Context):
    log(ctx, 'resume', options=locals(), log_type='command', author=ctx.author)
    await resume_def(ctx, glob)

@bot.hybrid_command(name='join', with_app_command=True, description=txt(0, glob, 'command_join'), help=txt(0, glob, 'command_join'), extras={'category': 'voice'})
@app_commands.describe(channel=txt(0, glob, 'attr_join_channel'))
async def join(ctx: dc_commands.Context, channel: discord.VoiceChannel = None):
    log(ctx, 'join', options=locals(), log_type='command', author=ctx.author)
    await join_def(ctx, glob, channel_id=channel.id if channel else None)

@bot.hybrid_command(name='disconnect', with_app_command=True, description=txt(0, glob, 'command_disconnect'),
                    help=txt(0, glob, 'command_disconnect'), extras={'category': 'voice'})
async def disconnect(ctx: dc_commands.Context):
    log(ctx, 'disconnect', options=locals(), log_type='command', author=ctx.author)
    await disconnect_def(ctx, glob)

@bot.hybrid_command(name='volume', with_app_command=True, description=txt(0, glob, 'command_volume'),
                    help=txt(0, glob, 'command_volume'), extras={'category': 'voice'})
@app_commands.describe(volume=txt(0, glob, 'attr_volume_volume'), user_only=txt(0, glob, 'ephemeral'))
async def volume_command(ctx: dc_commands.Context, volume: int = None, user_only: bool = False):
    log(ctx, 'volume', options=locals(), log_type='command', author=ctx.author)
    await volume_command_def(ctx, glob, volume, user_only)

# --------------------------------------- MENU --------------------------------------------------

@bot.tree.context_menu(name='Play now')
async def play_now(inter, message: discord.Message):
    ctx = await bot.get_context(inter)
    log(ctx, 'play_now', options=locals(), log_type='command', author=ctx.author)

    if ctx.author.voice is None:
        await inter.response.send_message(
            content=txt(ctx.guild.id, glob, 'You are **not connected** to a voice channel'),
            ephemeral=True)
        return

    url, probe_data = get_content_of_message(glob, message)

    response: ReturnData = await queue_command_def(ctx, glob, url, mute_response=True, probe_data=probe_data,
                                                   ephemeral=True,
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

    response: ReturnData = await queue_command_def(ctx, glob, url, mute_response=True, probe_data=probe_data,
                                                   ephemeral=True)
    if not inter.response.is_done():
        await inter.response.send_message(content=response.message, ephemeral=True)

# --------------------------------------- GENERAL --------------------------------------------------

@bot.hybrid_command(name='ping', with_app_command=True, description=txt(0, glob, 'command_ping'), help=txt(0, glob, 'command_ping'), extras={'category': 'general'})
async def ping_command(ctx: dc_commands.Context):
    log(ctx, 'ping', options=locals(), log_type='command', author=ctx.author)
    await ping_def(ctx, glob)

# noinspection PyTypeHints
@bot.hybrid_command(name='language', with_app_command=True, description=txt(0, glob, 'command_language'),
                    help=txt(0, glob, 'command_language'), extras={'category': 'general'})
@app_commands.describe(country_code=txt(0, glob, 'attr_language_country_code'))
async def language_command(ctx: dc_commands.Context, country_code: Literal[tuple(languages_dict.keys())]):
    log(ctx, 'language', options=locals(), log_type='command', author=ctx.author)

    await language_command_def(ctx, glob, country_code)

@bot.hybrid_command(name='list', with_app_command=True, description=txt(0, glob, 'command_list'), help=txt(0, glob, 'command_list'), extras={'category': 'general'})
@app_commands.describe(list_type=txt(0, glob, 'attr_list_list_type'), display_type=txt(0, glob, 'attr_list_display_type'), user_only=txt(0, glob, 'ephemeral'))
async def list_command(ctx: dc_commands.Context, list_type: Literal['queue', 'history', 'radios', 'effects']='queue', display_type: Literal['short', 'medium', 'long']=None, user_only: bool = False):
    log(ctx, 'list', options=locals(), log_type='command', author=ctx.author)

    await list_command_def(ctx, glob, list_type, display_type, user_only)

# @bot.hybrid_command(name='sound-effects', with_app_command=True, description=txt(0, glob, 'command_sound_effects'),
#                     help=txt(0, glob, 'command_sound_effects'), extras={'category': 'general'})
# @app_commands.describe(user_only=txt(0, glob, 'ephemeral'))
# async def sound_effects(ctx: dc_commands.Context, user_only: bool = True):
#     log(ctx, 'sound_effects', options=locals(), log_type='command', author=ctx.author)
#
#     await sound_effects_def(ctx, glob, user_only)
#
# @bot.hybrid_command(name='list-radios', with_app_command=True, description=txt(0, glob, 'command_list_radios'),
#                     help=txt(0, glob, 'command_list_radios'), extras={'category': 'general'})
# @app_commands.describe(user_only=txt(0, glob, 'ephemeral'))
# async def list_radios(ctx: dc_commands.Context, user_only: bool = True):
#     log(ctx, 'list_radios', options=locals(), log_type='command', author=ctx.author)
#
#     await list_radios_def(ctx, glob, user_only)

@bot.hybrid_command(name='key', with_app_command=True, description=txt(0, glob, 'command_key'), help=txt(0, glob, 'command_key'), extras={'category': 'general'})
async def key_command(ctx: dc_commands.Context):
    log(ctx, 'key', options=locals(), log_type='command', author=ctx.author)

    await key_def(ctx, glob)

# noinspection PyTypeHints
@bot.hybrid_command(name='options', with_app_command=True, description=txt(0, glob, 'command_options'),
                    help=txt(0, glob, 'command_options'), extras={'category': 'general'})
@app_commands.describe(volume=txt(0, glob, 'attr_options_volume'),
                       buffer=txt(0, glob, 'attr_options_buffer'),
                       language=txt(0, glob, 'attr_options_language'),
                       response_type=txt(0, glob, 'attr_options_response_type'),
                       buttons=txt(0, glob, 'attr_options_buttons'),
                       loop=txt(0, glob, 'attr_options_loop'),
                       history_length=txt(0, glob, 'attr_options_history_length'))
async def options_command(ctx: dc_commands.Context,
                          loop: bool = None,
                          language: Literal[tuple(languages_dict.keys())] = None,
                          response_type: Literal['short', 'long'] = None,
                          buttons: bool = None,
                          volume: discord.ext.commands.Range[int, 0, 200] = None,
                          buffer: discord.ext.commands.Range[int, 5, 3600] = None,
                          history_length: discord.ext.commands.Range[int, 1, 100] = None):
    log(ctx, 'options', options=locals(), log_type='command', author=ctx.author)

    await options_command_def(ctx, glob, loop=loop, language=language, response_type=response_type, buttons=buttons,
                              volume=volume, buffer=buffer, history_length=history_length)

# ---------------------------------------- ADMIN --------------------------------------------------

async def is_authorised(ctx):
    if ctx.author.id in authorized_users or ctx.author.id == d_id or ctx.author.id == 349164237605568513 or ctx.author.id == config.DEVELOPER_ID:
        return True

@bot.hybrid_command(name='zz_announce', with_app_command=True, hidden=True)
@dc_commands.check(is_authorised)
async def announce_command(ctx: dc_commands.Context, message):
    log(ctx, 'announce', options=locals(), log_type='command', author=ctx.author)
    await announce_command_def(ctx, glob, message)

@bot.hybrid_command(name='zz_kys', with_app_command=True, hidden=True)
@dc_commands.check(is_authorised)
async def kys(ctx: dc_commands.Context):
    log(ctx, 'kys', options=locals(), log_type='command', author=ctx.author)
    await kys_def(ctx, glob)

# noinspection PyTypeHints
@bot.hybrid_command(name='zz_options', with_app_command=True, hidden=True)
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
                         server: discord.ext.commands.GuildConverter = None,
                         stopped: bool = None,
                         loop: bool = None,
                         is_radio: bool = None,
                         buttons: bool = None,
                         language: Literal[tuple(languages_dict.keys())] = None,
                         response_type: Literal['short', 'long'] = None,
                         buffer: int = None,
                         history_length: int = None,
                         volume: int = None,
                         search_query: str = None):
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
                      search_query=str(search_query))

@bot.hybrid_command(name='zz_download_guild', with_app_command=True, hidden=True)
@dc_commands.check(is_authorised)
async def download_guild_command(ctx: dc_commands.Context, guild_id, ephemeral: bool = True):
    log(ctx, 'download_guild', options=locals(), log_type='command', author=ctx.author)
    await download_guild(ctx, glob, guild_id, ephemeral=ephemeral)

@bot.hybrid_command(name='zz_download_guild_channel', with_app_command=True, hidden=True)
@dc_commands.check(is_authorised)
async def download_guild_channel_command(ctx: dc_commands.Context, channel_id, ephemeral: bool = True):
    log(ctx, 'download_guild_channel', options=locals(), log_type='command', author=ctx.author)
    await download_guild_channel(ctx, glob, channel_id, ephemeral=ephemeral)

@bot.hybrid_command(name='zz_get_guild', with_app_command=True, hidden=True)
@dc_commands.check(is_authorised)
async def get_guild_command(ctx: dc_commands.Context, guild_id, ephemeral: bool = True):
    log(ctx, 'get_guild', options=locals(), log_type='command', author=ctx.author)
    await get_guild(ctx, glob, guild_id, ephemeral=ephemeral)

@bot.hybrid_command(name='zz_get_guild_channel', with_app_command=True, hidden=True)
@dc_commands.check(is_authorised)
async def get_guild_channel_command(ctx: dc_commands.Context, channel_id, ephemeral: bool = True):
    log(ctx, 'get_guild_channel', options=locals(), log_type='command', author=ctx.author)
    await get_guild_channel(ctx, glob, channel_id, ephemeral=ephemeral)

@bot.hybrid_command(name='zz_set_time', with_app_command=True, hidden=True)
@dc_commands.check(is_authorised)
async def set_time_command(ctx: dc_commands.Context, time_stamp: int, ephemeral: bool = True,
                           mute_response: bool = False):
    log(ctx, 'set_time', options=locals(), log_type='command', author=ctx.author)
    await set_video_time(ctx, glob, time_stamp, ephemeral=ephemeral, mute_response=mute_response)

# ------------------------------------------ ADMIN SLOWED USERS --------------------------------------------------------

@bot.hybrid_command(name='zz_slowed_users', with_app_command=True, hidden=True)
@dc_commands.check(is_authorised)
async def slowed_users_command(ctx: dc_commands.Context):
    log(ctx, 'slowed_users', options=locals(), log_type='command', author=ctx.author)
    await slowed_users_command_def(ctx, glob)

@bot.hybrid_command(name='zz_slowed_users_add', with_app_command=True, hidden=True)
@dc_commands.check(is_authorised)
async def slowed_users_add_command(ctx: dc_commands.Context, member: discord.Member, time: int):
    log(ctx, 'slowed_users_add', options=locals(), log_type='command', author=ctx.author)
    await slowed_users_add_command_def(ctx, glob, member, time)

@bot.hybrid_command(name='zz_slowed_users_add_all', with_app_command=True, hidden=True)
@dc_commands.check(is_authorised)
async def slowed_users_add_all_command(ctx: dc_commands.Context, guild_obj: discord.Guild, time: int):
    log(ctx, 'slowed_users_add_all', options=locals(), log_type='command', author=ctx.author)
    await slowed_users_add_all_command_def(ctx, glob, guild_obj, time)

@bot.hybrid_command(name='zz_slowed_users_remove', with_app_command=True, hidden=True)
@dc_commands.check(is_authorised)
async def slowed_users_remove_command(ctx: dc_commands.Context, member: discord.Member):
    log(ctx, 'slowed_users_remove', options=locals(), log_type='command', author=ctx.author)
    await slowed_users_remove_command_def(ctx, glob, member)

@bot.hybrid_command(name='zz_slowed_users_remove_all', with_app_command=True, hidden=True)
@dc_commands.check(is_authorised)
async def slowed_users_remove_all_command(ctx: dc_commands.Context, guild_obj: discord.Guild):
    log(ctx, 'slowed_users_remove_all', options=locals(), log_type='command', author=ctx.author)
    await slowed_users_remove_all_command_def(ctx, glob, guild_obj)

# ---------------------------------------------- DEVELOPMENT -----------------------------------------------------------

@bot.hybrid_command(name='zz_dev', with_app_command=True, hidden=True)
@dc_commands.check(is_authorised)
async def dev_command(ctx: dc_commands.Context, message):
    log(ctx, 'dev', options=locals(), log_type='command', author=ctx.author)

    await dev_command_def(ctx, glob, message)

    # await ctx.defer()
    #
    # resp = await query_autocomplete_def(None, 'song', include_youtube=True, include_tunein=True, include_radio=True)
    # # await ctx.send(resp)
    # #
    # # await dev_command_def(ctx, glob, message)

# ------------------------------------------ SPECIFIC USER TORTURE -----------------------------------------------------

@bot.hybrid_command(name='zz_voice_torture', with_app_command=True, hidden=True)
@dc_commands.check(is_authorised)
@dc_commands.has_guild_permissions(move_members=True)
async def voice_torture_command(ctx: dc_commands.Context, member: discord.Member, delay: int):
    log(ctx, 'voice_torture', options=locals(), log_type='command', author=ctx.author)
    await voice_torture_command_def(ctx, glob, member, delay)

@bot.hybrid_command(name='zz_voice_torture_stop', with_app_command=True, hidden=True)
@dc_commands.check(is_authorised)
async def voice_torture_stop_command(ctx: dc_commands.Context, member: discord.Member):
    log(ctx, 'voice_torture_stop', options=locals(), log_type='command', author=ctx.author)
    await voice_torture_stop_command_def(ctx, glob, member)

# --------------------------------------------- HELP COMMAND -----------------------------------------------------------

bot.remove_command('help')

@bot.hybrid_command(name='help', with_app_command=True, description=txt(0, glob, 'command_help'), help=txt(0, glob, 'command_help'), extras={'category': 'general'})
async def help_command(ctx: dc_commands.Context, command_name: str = None):
    log(ctx, 'help', options=locals(), log_type='command', author=ctx.author)
    gi = ctx.guild.id

    embed = discord.Embed(title=txt(gi, glob, "Commands"), description=f"{txt(gi, glob, 'Use `/help <command>` to get help on a command')} | Prefix: `{prefix}`")

    command_dict = {}
    command_name_dict = {}
    for command in bot.commands:
        if command.hidden:
            continue

        command_name_dict[command.name] = command

        category = command.extras.get('category', 'No category')
        if category not in command_dict:
            command_dict[category] = []

        command_dict[category].append(command)

    if not command_name:
        for category in command_dict.keys():
            message = ''

            for command in command_dict[category]:
                add = f'`{command.name}` - {txt(gi, glob, command.description)} \n'

                if len(message + add) > 1024:
                    embed.add_field(name=f"**{category.capitalize()}**", value=message, inline=False)
                    message = ''
                    continue

                message = message + add

            embed.add_field(name=f"**{category.capitalize()}**", value=message, inline=False)

        await ctx.send(embed=embed)
        return

    if command_name not in command_name_dict:
        await ctx.send(txt(gi, glob, 'Command not found'))
        return

    command = command_name_dict[command_name]

    embed = discord.Embed(title=command.name, description=txt(gi, glob, command.description))
    # noinspection PyProtectedMember
    for key, value in command.app_command._params.items():
        embed.add_field(name=f"`{key}` - {txt(gi, glob, value.description)}", value=f'{txt(gi, glob, "Required")}: `{value.required}` | {txt(gi, glob, "Default")}: `{value.default}` | {txt(gi, glob, "Type")}: `{value.type}`', inline=False)

    await ctx.send(embed=embed)

# ---------------------------------------------- AUTOCOMPLETE ----------------------------------------------------------

# Local autocomplete functions
@help_command.autocomplete('command_name')
async def help_autocomplete(ctx: discord.Interaction, current: str):
    return await help_autocomplete_def(ctx, current, glob)

@remove.autocomplete('song')
async def song_autocomplete(ctx: discord.Interaction, current: str):
    return await song_autocomplete_def(ctx, current, glob)

@radio_cz_command.autocomplete('radio')
async def radio_autocomplete(ctx: discord.Interaction, current: str):
    return await radio_autocomplete_def(ctx, current, limit=25)

@ps.autocomplete('effect')
async def effect_autocomplete(ctx: discord.Interaction, current: str):
    return await local_autocomplete_def(ctx, current, limit=25)

# API request autocomplete functions
@play.autocomplete('query')
async def play_autocomplete(ctx: discord.Interaction, current: str):
    return await query_autocomplete_def(ctx, current, include_youtube=True)

@radio_tunein_command.autocomplete('radio')
async def radio_tunein_autocomplete(ctx: discord.Interaction, current: str):
    return await tunein_autocomplete_def(ctx, current)

@radio_garden_command.autocomplete('radio')
async def radio_garden_autocomplete(ctx: discord.Interaction, current: str):
    return await garden_autocomplete_def(ctx, current)



# @queue_command.autocomplete('query')
# @next_up.autocomplete('query')
# @play.autocomplete('query')
# async def query_autocomplete(ctx: discord.Interaction, query: str):
#     return await query_autocomplete_def(ctx, query)


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
