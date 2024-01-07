import datetime
import threading

import discord.ext.commands
import spotipy
from sclib import SoundcloudAPI
from spotipy.oauth2 import SpotifyClientCredentials

from classes.data_classes import WebData

from utils.discord import get_content_of_message
from utils.log import send_to_admin
from utils.save import update_guilds
from utils.json import *

from commands.admin import *
from commands.chat_export import *
from commands.general import *
from commands.player import *
from commands.queue import *
from commands.voice import *

from ipc.server import ipc_run
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

        update_guilds(glob)

        save_json(glob)

    async def on_guild_join(self, guild_object):
        # log
        log_msg = f"Joined guild ({guild_object.name})({guild_object.id}) with {guild_object.member_count} members and {len(guild_object.voice_channels)} voice channels"
        log(None, log_msg)

        # send log to admin
        await send_to_admin(glob, log_msg)

        # create guild object
        create_guild(glob, guild_object.id)
        save_json(glob)

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
        save_json(glob)

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
            log(ctx, 'error.Forbidden', [error], log_type='error', author=ctx.author)
            await ctx.send(tg(ctx.guild.id, "The command failed because I don't have the required permissions.\n Please give me the required permissions and try again."))

        elif isinstance(error, dc_commands.CheckFailure):
            err_msg = f'Error for ({ctx.author}) -> ({ctx.command}) with error ({error})'
            log(ctx, err_msg, log_type='error', author=ctx.author)
            await send_to_admin(glob, err_msg)
            await ctx.reply(f"（ ͡° ͜ʖ ͡°)つ━☆・。\n"
                            f"⊂　　 ノ 　　　・゜+.\n"
                            f"　しーＪ　　　°。+ ´¨)\n"
                            f"　　　　　　　　　.· ´¸.·´¨) ¸.·*¨)\n"
                            f"　　　　　　　　　　(¸.·´ (¸.·' ☆ **Fuck off**\n"
                            f"*{tg(ctx.guild.id, 'You dont have permission to use this command')}*")

        elif isinstance(error, dc_commands.MissingPermissions):
            err_msg = f'Error for ({ctx.author}) -> ({ctx.command}) with error ({error})'
            log(ctx, err_msg, log_type='error', author=ctx.author)
            await ctx.reply(tg(ctx.guild.id, 'Bot does not have permissions to execute this command correctly') + f" - {error}")

        elif isinstance(error, PendingRollbackError):
            err_msg = f'Error for ({ctx.author}) -> ({ctx.command}) with error ({error})'
            log(ctx, err_msg, log_type='error', author=ctx.author)
            await send_to_admin(glob, err_msg)

            try:
                glob.ses.rollback()  # Rollback the session
            except Exception as rollback_error:
                error_traceback = traceback.format_exception(type(error), error, error.__traceback__)
                error_traceback = ''.join(error_traceback)

                err_msg = f'Error for ({ctx.author}) -> Failed Rollback ({ctx.command}) with error ({rollback_error})({error_traceback})'
                log(ctx, err_msg, log_type='error', author=ctx.author)
                await send_to_admin(glob, err_msg)

            await ctx.reply(f"Database error -> Attempted rollback (try again one time - if it doesn't work tell developer to restart bot)")
        else:
            message = f"Error for ({ctx.author}) -> ({ctx.command}) with error ({error})\n{error_traceback}"

            # log
            log(ctx, message, log_type='error', author=ctx.author)

            # send log to admin
            await send_to_admin(glob, message)

            # send to user
            await ctx.reply(f"{error}   {bot.get_user(config.DEVELOPER_ID).mention}", ephemeral=True)

    async def on_message(self, message):
        # on every message
        if message.author == bot.user:
            return

        # check if message is a DM
        if not message.guild:
            try:
                # respond to DM
                await message.channel.send(
                    f"I'm sorry, but I only work in servers.\n\n"
                    f""
                    f"If you want me to join your server, you can invite me with this link: {config.INVITE_URL}\n\n"
                    f""
                    f"If you have any questions, you can DM my developer <@!{config.DEVELOPER_ID}>#4272")

                # send DM to ADMIN
                await send_to_admin(glob, f"<@!{message.author.id}> tied to DM me with this message `{message.content}`")
                return

            except discord.errors.Forbidden:
                return

        is_slowed, slowed_for = is_user_slowed(glob, message.author.id, message.guild.id)
        if is_slowed:
            try:
                await message.author.timeout(datetime.timedelta(seconds=slowed_for))
            except discord.Forbidden:
                log(None, 'Timeout Forbidden', [message.author.id, message.author.name, message.guild.id, message.guild.name], log_type='error')
                pass

        await bot.process_commands(message)

# ---------------------------------------------- LOAD ------------------------------------------------------------------

log(None, "--------------------------------------- NEW / REBOOTED ----------------------------------------")

build_new_guilds = False
build_old_guilds = False

# with open(f'{config.PARENT_DIR}db/radio.json', 'r', encoding='utf-8') as file:
#     radio_dict = json.load(file)

for radio_name in radio_dict:
    radio_info_class = ses.query(video_class.RadioInfo).filter(video_class.RadioInfo.name == radio_name).first()
    if not radio_info_class:
        radio_info_class = video_class.RadioInfo(radio_dict[radio_name]['id'])
        ses.add(radio_info_class)
        ses.commit()
        log(None, f'Added {radio_name} to database')
log(None, 'Loaded radio.json')

# with open(f'{config.PARENT_DIR}db/languages.json', 'r', encoding='utf-8') as file:
#     languages_dict = json.load(file)

text = languages_dict['en']
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

@bot.hybrid_command(name='queue', with_app_command=True, description=text['queue_add'], help=text['queue_add'])
@app_commands.describe(url=text['url'], position=text['pos'])
async def queue_command(ctx: dc_commands.Context, url, position: int = None):
    log(ctx, 'queue', [url, position], log_type='command', author=ctx.author)
    await queue_command_def(ctx, glob, url, position=position)

# @bot.hybrid_command(name='queue_export', with_app_command=True, description=text['queue_export'], help=text['queue_export'])
# @app_commands.describe(guild_id=text['guild_id'], ephemeral=text['ephemeral'])
# async def export_queue_command(ctx: dc_commands.Context, guild_id=None, ephemeral: bool=True):
#     log(ctx, 'export_queue', [guild_id, ephemeral], log_type='command', author=ctx.author)
#     await export_queue(ctx, glob, guild_id, ephemeral=ephemeral)
#
# @bot.hybrid_command(name='queue_import', with_app_command=True, description=text['queue_import'], help=text['queue_import'])
# @app_commands.describe(queue_string=text['queue_string'], guild_id=text['guild_id'], ephemeral=text['ephemeral'])
# async def import_queue_command(ctx: dc_commands.Context, queue_string: str, guild_id=None, ephemeral: bool=True):
#     log(ctx, 'import_queue', [queue_string, guild_id, ephemeral], log_type='command', author=ctx.author)
#     await import_queue(ctx, glob, queue_string, guild_id, ephemeral=ephemeral)

@bot.hybrid_command(name='next_up', with_app_command=True, description=text['next_up'], help=text['next_up'])
@app_commands.describe(url=text['url'], user_only=text['ephemeral'])
async def next_up(ctx: dc_commands.Context, url, user_only: bool = False):
    log(ctx, 'next_up', [url, user_only], log_type='command', author=ctx.author)
    await next_up_def(ctx, glob, url, user_only)

@bot.hybrid_command(name='skip', with_app_command=True, description=text['skip'], help=text['skip'])
async def skip(ctx: dc_commands.Context):
    log(ctx, 'skip', [], log_type='command', author=ctx.author)
    await skip_def(ctx, glob)

@bot.hybrid_command(name='remove', with_app_command=True, description=text['queue_remove'], help=text['queue_remove'])
@app_commands.describe(number=text['number'], user_only=text['ephemeral'])
async def remove(ctx: dc_commands.Context, number: int, user_only: bool = False):
    log(ctx, 'remove', [number, user_only], log_type='command', author=ctx.author)
    await remove_def(ctx, glob, number, ephemeral=user_only)

@bot.hybrid_command(name='clear', with_app_command=True, description=text['clear'], help=text['clear'])
@app_commands.describe(user_only=text['ephemeral'])
async def clear(ctx: dc_commands.Context, user_only: bool = False):
    log(ctx, 'clear', [user_only], log_type='command', author=ctx.author)
    await clear_def(ctx, glob, user_only)

@bot.hybrid_command(name='shuffle', with_app_command=True, description=text['shuffle'], help=text['shuffle'])
@app_commands.describe(user_only=text['ephemeral'])
async def shuffle(ctx: dc_commands.Context, user_only: bool = False):
    log(ctx, 'shuffle', [user_only], log_type='command', author=ctx.author)
    await shuffle_def(ctx, glob, user_only)

@bot.hybrid_command(name='show', with_app_command=True, description=text['queue_show'], help=text['queue_show'])
@app_commands.describe(display_type=text['display_type'], user_only=text['ephemeral'])
async def show(ctx: dc_commands.Context, display_type: Literal['short', 'medium', 'long'] = None,
               list_type: Literal['queue', 'history'] = 'queue', user_only: bool = False):
    log(ctx, 'show', [display_type, user_only], log_type='command', author=ctx.author)
    await show_def(ctx, glob, display_type, list_type, user_only)

@bot.hybrid_command(name='search', with_app_command=True, description=text['search'], help=text['search'])
@app_commands.describe(search_query=text['search_query'])
async def search_command(ctx: dc_commands.Context, search_query):
    log(ctx, 'search', [search_query], log_type='command', author=ctx.author)
    await search_command_def(ctx, glob, search_query)

# --------------------------------------- PLAYER --------------------------------------------------

@bot.hybrid_command(name='play', with_app_command=True, description=text['play'], help=text['play'])
@app_commands.describe(url=text['play'], force=text['force'])
async def play(ctx: dc_commands.Context, url=None, force=False):
    log(ctx, 'play', [url, force], log_type='command', author=ctx.author)
    await play_def(ctx, glob, url, force)

@bot.hybrid_command(name='radio', with_app_command=True, description=text['radio'], help=text['radio'])
@app_commands.describe(favourite_radio=text['favourite_radio'], radio_code=text['radio_code'])
async def radio(ctx: dc_commands.Context, favourite_radio: Literal[
    'Rádio BLANÍK', 'Rádio BLANÍK CZ', 'Evropa 2', 'Fajn Radio', 'Hitrádio PopRock', 'Český rozhlas Pardubice', 'Radio Beat', 'Country Radio', 'Radio Kiss', 'Český rozhlas Vltava', 'Hitrádio Černá Hora'] = None,
                radio_code: int = None):
    log(ctx, 'radio', [favourite_radio, radio_code], log_type='command', author=ctx.author)
    await radio_def(ctx, glob, favourite_radio, radio_code)

@bot.hybrid_command(name='ps', with_app_command=True, description=text['ps'], help=text['ps'])
@app_commands.describe(effect_number=text['effects_number'])
async def ps(ctx: dc_commands.Context, effect_number: app_commands.Range[int, 1, len(sound_effects)]):
    log(ctx, 'ps', [effect_number], log_type='command', author=ctx.author)
    await ps_def(ctx, glob, effect_number)

@bot.hybrid_command(name='nowplaying', with_app_command=True, description=text['nowplaying'], help=text['nowplaying'])
@app_commands.describe(user_only=text['ephemeral'])
async def nowplaying(ctx: dc_commands.Context, user_only: bool = False):
    log(ctx, 'nowplaying', [user_only], log_type='command', author=ctx.author)
    await now_def(ctx, glob, user_only)

@bot.hybrid_command(name='last', with_app_command=True, description=text['last'], help=text['last'])
@app_commands.describe(user_only=text['ephemeral'])
async def last(ctx: dc_commands.Context, user_only: bool = False):
    log(ctx, 'last', [user_only], log_type='command', author=ctx.author)
    await last_def(ctx, glob, user_only)

@bot.hybrid_command(name='loop', with_app_command=True, description=text['loop'], help=text['loop'])
async def loop_command(ctx: dc_commands.Context):
    log(ctx, 'loop', [], log_type='command', author=ctx.author)
    await loop_command_def(ctx, glob)

@bot.hybrid_command(name='loop_this', with_app_command=True, description=text['loop_this'], help=text['loop_this'])
async def loop_this(ctx: dc_commands.Context):
    log(ctx, 'loop_this', [], log_type='command', author=ctx.author)
    await loop_command_def(ctx, glob, clear_queue_opt=True)

@bot.hybrid_command(name='earrape', with_app_command=True)
async def earrape_command(ctx: dc_commands.Context):
    log(ctx, 'earrape', [], log_type='command', author=ctx.author)
    await earrape_command_def(ctx, glob)

# --------------------------------------- VOICE --------------------------------------------------

@bot.hybrid_command(name='stop', with_app_command=True, description=f'Stop the player')
async def stop(ctx: dc_commands.Context):
    log(ctx, 'stop', [], log_type='command', author=ctx.author)
    await stop_def(ctx, glob)

@bot.hybrid_command(name='pause', with_app_command=True, description=f'Pause the player')
async def pause(ctx: dc_commands.Context):
    log(ctx, 'pause', [], log_type='command', author=ctx.author)
    await pause_def(ctx, glob)

@bot.hybrid_command(name='resume', with_app_command=True, description=f'Resume the player')
async def resume(ctx: dc_commands.Context):
    log(ctx, 'resume', [], log_type='command', author=ctx.author)
    await resume_def(ctx, glob)

@bot.hybrid_command(name='join', with_app_command=True, description=text['join'], help=text['join'])
@app_commands.describe(channel_id=text['channel_id'])
async def join(ctx: dc_commands.Context, channel_id=None):
    log(ctx, 'join', [channel_id], log_type='command', author=ctx.author)
    await join_def(ctx, glob, channel_id)

@bot.hybrid_command(name='disconnect', with_app_command=True, description=text['die'], help=text['die'])
async def disconnect(ctx: dc_commands.Context):
    log(ctx, 'disconnect', [], log_type='command', author=ctx.author)
    await disconnect_def(ctx, glob)

@bot.hybrid_command(name='volume', with_app_command=True, description=text['volume'], help=text['volume'])
@app_commands.describe(volume=text['volume'], user_only=text['ephemeral'])
async def volume_command(ctx: dc_commands.Context, volume=None, user_only: bool = False):
    log(ctx, 'volume', [volume, user_only], log_type='command', author=ctx.author)
    await volume_command_def(ctx, glob, volume, user_only)

# --------------------------------------- MENU --------------------------------------------------

@bot.tree.context_menu(name='Play now')
async def play_now(inter, message: discord.Message):
    ctx = await bot.get_context(inter)
    log(ctx, 'play_now', [message], log_type='command', author=ctx.author)

    if ctx.author.voice is None:
        await inter.response.send_message(content=tg(ctx.guild.id, 'You are **not connected** to a voice channel'),
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
    log(ctx, 'add_to_queue', [message], log_type='command', author=ctx.author)

    url, probe_data = get_content_of_message(glob, message)

    response: ReturnData = await queue_command_def(ctx, glob, url, mute_response=True, probe_data=probe_data, ephemeral=True)
    if not inter.response.is_done():
        await inter.response.send_message(content=response.message, ephemeral=True)

# @bot.tree.context_menu(name='Show Profile')
# async def show_profile(inter, member: discord.Member):
#     ctx = await bot.get_context(inter)
#     log(ctx, 'show_profile', [member], log_type='command', author=ctx.author)
#
#     embed = discord.Embed(title=f"{member.name}#{member.discriminator}",
#                           description=f"ID: `{member.id}` | Name: `{member.display_name}` | Nickname: `{member.nick}`")
#     embed.add_field(name="Created at", value=member.created_at.strftime("%d/%m/%Y %H:%M:%S"), inline=True)
#     embed.add_field(name="Joined at", value=member.joined_at.strftime("%d/%m/%Y %H:%M:%S"), inline=True)
#
#     embed.add_field(name="Roles", value=", ".join([role.mention for role in member.roles[1:]]), inline=False)
#
#     embed.add_field(name='Top Role', value=f'{member.top_role.mention}', inline=True)
#
#     # noinspection PyUnresolvedReferences
#     embed.add_field(name='Badges', value=', '.join([badge.name for badge in member.public_flags.all()]), inline=False)
#
#     embed.add_field(name='Avatar',
#                     value=f'[Default Avatar]({member.avatar}) | [Display Avatar]({member.display_avatar})',
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

@bot.hybrid_command(name='ping', with_app_command=True, description=text['ping'], help=text['ping'])
async def ping_command(ctx: dc_commands.Context):
    log(ctx, 'ping', [], log_type='command', author=ctx.author)
    await ping_def(ctx, glob)

# noinspection PyTypeHints
@bot.hybrid_command(name='language', with_app_command=True, description=text['language'], help=text['language'])
@app_commands.describe(country_code=text['country_code'])
async def language_command(ctx: dc_commands.Context, country_code: Literal[tuple(languages_dict.keys())]):
    log(ctx, 'language', [country_code], log_type='command', author=ctx.author)

    await language_command_def(ctx, glob, country_code)

@bot.hybrid_command(name='sound_effects', with_app_command=True, description=text['sound'], help=text['sound'])
@app_commands.describe(user_only=text['ephemeral'])
async def sound_effects(ctx: dc_commands.Context, user_only: bool = True):
    log(ctx, 'sound_effects', [user_only], log_type='command', author=ctx.author)

    await sound_effects_def(ctx, glob, user_only)

@bot.hybrid_command(name='list_radios', with_app_command=True, description=text['list_radios'], help=text['list_radios'])
@app_commands.describe(user_only=text['ephemeral'])
async def list_radios(ctx: dc_commands.Context, user_only: bool = True):
    log(ctx, 'list_radios', [user_only], log_type='command', author=ctx.author)

    await list_radios_def(ctx, glob, user_only)

@bot.hybrid_command(name='key', with_app_command=True, description=text['key'], help=text['key'])
async def key_command(ctx: dc_commands.Context):
    log(ctx, 'key', [], log_type='command', author=ctx.author)

    await key_def(ctx, glob)

# noinspection PyTypeHints
@bot.hybrid_command(name='options', with_app_command=True, description=text['options'], help=text['options'])
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
    log(ctx, 'options', [loop, language, response_type, buttons, volume, buffer, history_length], log_type='command', author=ctx.author)

    await options_command_def(ctx, glob, loop=loop, language=language, response_type=response_type, buttons=buttons, volume=volume, buffer=buffer, history_length=history_length)

# ---------------------------------------- ADMIN --------------------------------------------------

async def is_authorised(ctx):
    if ctx.author.id in authorized_users or ctx.author.id == d_id or ctx.author.id == 349164237605568513 or ctx.author.id == config.DEVELOPER_ID:
        return True

@bot.hybrid_command(name='zz_announce', with_app_command=True)
@dc_commands.check(is_authorised)
async def announce_command(ctx: dc_commands.Context, message):
    log(ctx, 'announce', [message], log_type='command', author=ctx.author)
    await announce_command_def(ctx, glob, message)

@bot.hybrid_command(name='zz_kys', with_app_command=True)
@dc_commands.check(is_authorised)
async def kys(ctx: dc_commands.Context):
    log(ctx, 'kys', [], log_type='command', author=ctx.author)
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
    log(ctx, 'zz_change_options', [server, stopped, loop, is_radio, buttons, language, response_type, buffer, history_length, volume, search_query, last_updated], log_type='command', author=ctx.author)

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
    log(ctx, 'download_guild', [guild_id, ephemeral], log_type='command', author=ctx.author)
    await download_guild(ctx, glob, guild_id, ephemeral=ephemeral)

@bot.hybrid_command(name='zz_download_guild_channel', with_app_command=True)
@dc_commands.check(is_authorised)
async def download_guild_channel_command(ctx: dc_commands.Context, channel_id, ephemeral: bool=True):
    log(ctx, 'download_guild_channel', [channel_id, ephemeral], log_type='command', author=ctx.author)
    await download_guild_channel(ctx, glob, channel_id, ephemeral=ephemeral)

@bot.hybrid_command(name='zz_get_guild', with_app_command=True)
@dc_commands.check(is_authorised)
async def get_guild_command(ctx: dc_commands.Context, guild_id, ephemeral: bool=True):
    log(ctx, 'get_guild', [guild_id, ephemeral], log_type='command', author=ctx.author)
    await get_guild(ctx, glob, guild_id, ephemeral=ephemeral)

@bot.hybrid_command(name='zz_get_guild_channel', with_app_command=True)
@dc_commands.check(is_authorised)
async def get_guild_channel_command(ctx: dc_commands.Context, channel_id, ephemeral: bool=True):
    log(ctx, 'get_guild_channel', [channel_id, ephemeral], log_type='command', author=ctx.author)
    await get_guild_channel(ctx, glob, channel_id, ephemeral=ephemeral)

@bot.hybrid_command(name='zz_set_time', with_app_command=True)
@dc_commands.check(is_authorised)
async def set_time_command(ctx: dc_commands.Context, time_stamp: int, ephemeral: bool=True, mute_response: bool=False):
    log(ctx, 'set_time', [time_stamp, ephemeral, mute_response], log_type='command', author=ctx.author)
    await set_video_time(ctx, glob, time_stamp, ephemeral=ephemeral, mute_response=mute_response)

# ------------------------------------------ ADMIN SLOWED USERS --------------------------------------------------------

@bot.hybrid_command(name='zz_slowed_users', with_app_command=True)
@dc_commands.check(is_authorised)
async def slowed_users_command(ctx: dc_commands.Context):
    log(ctx, 'slowed_users', [], log_type='command', author=ctx.author)
    await slowed_users_command_def(ctx, glob)

@bot.hybrid_command(name='zz_slowed_users_add', with_app_command=True)
@dc_commands.check(is_authorised)
async def slowed_users_add_command(ctx: dc_commands.Context, member: discord.Member, time: int):
    log(ctx, 'slowed_users_add', [member.id, time], log_type='command', author=ctx.author)
    await slowed_users_add_command_def(ctx, glob, member, time)

@bot.hybrid_command(name='zz_slowed_users_add_all', with_app_command=True)
@dc_commands.check(is_authorised)
async def slowed_users_add_all_command(ctx: dc_commands.Context, guild_obj: discord.Guild, time: int):
    log(ctx, 'slowed_users_add_all', [guild_obj.id, time], log_type='command', author=ctx.author)
    await slowed_users_add_all_command_def(ctx, glob, guild_obj, time)

@bot.hybrid_command(name='zz_slowed_users_remove', with_app_command=True)
@dc_commands.check(is_authorised)
async def slowed_users_remove_command(ctx: dc_commands.Context, member: discord.Member):
    log(ctx, 'slowed_users_remove', [member.id], log_type='command', author=ctx.author)
    await slowed_users_remove_command_def(ctx, glob, member)

@bot.hybrid_command(name='zz_slowed_users_remove_all', with_app_command=True)
@dc_commands.check(is_authorised)
async def slowed_users_remove_all_command(ctx: dc_commands.Context, guild_obj: discord.Guild):
    log(ctx, 'slowed_users_remove_all', [guild_obj.id], log_type='command', author=ctx.author)
    await slowed_users_remove_all_command_def(ctx, glob, guild_obj)

# ------------------------------------------ SPECIFIC USER TORTURE -----------------------------------------------------

@bot.hybrid_command(name='zz_voice_torture', with_app_command=True)
@dc_commands.check(is_authorised)
@dc_commands.has_guild_permissions(move_members=True)
async def voice_torture_command(ctx: dc_commands.Context, member: discord.Member, delay: int):
    log(ctx, 'voice_torture', [member.id, delay], log_type='command', author=ctx.author)
    await voice_torture_command_def(ctx, glob, member, delay)

@bot.hybrid_command(name='zz_voice_torture_stop', with_app_command=True)
@dc_commands.check(is_authorised)
async def voice_torture_stop_command(ctx: dc_commands.Context, member: discord.Member):
    log(ctx, 'voice_torture_stop', [member.id], log_type='command', author=ctx.author)
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
    log(ctx, 'help', [general, player, queue, voice], log_type='command', author=ctx.author)
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
    embed.add_field(name="General", value=f"`/help` - {tg(gi, 'help')}\n"
                                          f"`/ping` - {tg(gi, 'ping')}\n"
                                          f"`/language` - {tg(gi, 'language')}\n"
                                          f"`/sound_ effects` - {tg(gi, 'sound')}\n"
                                          f"`/list_radios` - {tg(gi, 'list_radios')}\n"
                                          f"`/key` - {tg(gi, 'key')}\n",
                    inline=False)
    embed.add_field(name="Player", value=f"`/play` - {tg(gi, 'play')}\n"
                                         f"`/radio` - {tg(gi, 'radio')}\n"
                                         f"`/ps` - {tg(gi, 'ps')}\n"
                                         f"`/skip` - {tg(gi, 'skip')}\n"
                                         f"`/nowplaying` - {tg(gi, 'nowplaying')}\n"
                                         f"`/last` - {tg(gi, 'last')}\n"
                                         f"`/loop` - {tg(gi, 'loop')}\n"
                                         f"`/loop_this` - {tg(gi, 'loop_this')}\n",
                    inline=False)
    embed.add_field(name="Queue", value=f"`/queue` - {tg(gi, 'queue_add')}\n"
                                        # f"`/queue_import` - {tg(gi, 'queue_import')}\n"
                                        # f"`/queue_export` - {tg(gi, 'queue_export')}\n"
                                        f"`/remove` - {tg(gi, 'queue_remove')}\n"
                                        f"`/clear` - {tg(gi, 'clear')}\n"
                                        f"`/shuffle` - {tg(gi, 'shuffle')}\n"
                                        f"`/show` - {tg(gi, 'queue_show')}\n"
                                        f"`/search` - {tg(gi, 'search')}",
                    inline=False)
    embed.add_field(name="Voice", value=f"`/stop` - {tg(gi, 'stop')}\n"
                                        f"`/pause` - {tg(gi, 'pause')}\n"
                                        f"`/resume` - {tg(gi, 'resume')}\n"
                                        f"`/join` - {tg(gi, 'join')}\n"
                                        f"`/disconnect` - {tg(gi, 'die')}\n"
                                        f"`/volume` - {tg(gi, 'volume')}",
                    inline=False)
    embed.add_field(name="Context Menu", value=f"`Add to queue` - {tg(gi, 'queue_add')}\n"
                                               # f"`Show Profile` - {tg(gi, 'profile')}\n"
                                               f"`Play now` - {tg(gi, 'play')}")

    if command == 'help':
        embed = discord.Embed(title="Help", description=f"`/help` - {tg(gi, 'help')}")
        embed.add_field(name=f"{tg(gi, 'Arguments')}", value=f"`general` - {tg(gi, 'The commands from')} General\n"
                                                             f"`player` - {tg(gi, 'The commands from')} Player\n"
                                                             f"`queue` - {tg(gi, 'The commands from')} Queue\n"
                                                             f"`voice` - {tg(gi, 'The commands from')} Voice",
                        inline=False)

    elif command == 'ping':
        embed = discord.Embed(title="Help", description=f"`/ping` - {tg(gi, 'ping')}")

    elif command == 'language':
        embed = discord.Embed(title="Help", description=f"`/language` - {tg(gi, 'language')}")
        embed.add_field(name=f"{tg(gi, 'Arguments')}", value=f"`country_code` - {tg(gi, 'country_code')}", inline=False)

    elif command == 'sound_effects':
        embed = discord.Embed(title="Help", description=f"`/sound_effects` - {tg(gi, 'sound')}")
        embed.add_field(name=f"{tg(gi, 'Arguments')}", value=f"`user_only` - {tg(gi, 'ephemeral')}", inline=False)

    elif command == 'list_radios':
        embed = discord.Embed(title="Help", description=f"`/list_radios` - {tg(gi, 'list_radios')}")
        embed.add_field(name=f"{tg(gi, 'Arguments')}", value=f"`user_only` - {tg(gi, 'ephemeral')}", inline=False)

    elif command == 'key':
        embed = discord.Embed(title="Help", description=f"`/key` - {tg(gi, 'key')}")

    elif command == 'play':
        embed = discord.Embed(title="Help", description=f"`/play` - {tg(gi, 'play')}")
        embed.add_field(name=f"{tg(gi, 'Arguments')}", value=f"`url` - {tg(gi, 'url')}", inline=False)
        embed.add_field(name="", value=f"`force` - {tg(gi, 'force')}", inline=False)

    elif command == 'radio':
        embed = discord.Embed(title="Help", description=f"`/radio` - {tg(gi, 'radio')}")
        embed.add_field(name=f"{tg(gi, 'Arguments')}", value=f"`favourite_radio` - {tg(gi, 'favourite_radio')}",
                        inline=False)
        embed.add_field(name="", value=f"`radio_code` - {tg(gi, 'radio_code')}", inline=False)

    elif command == 'ps':
        embed = discord.Embed(title="Help", description=f"`/ps` - {tg(gi, 'ps')}")
        embed.add_field(name=f"{tg(gi, 'Arguments')}", value=f"`effect_number` - {tg(gi, 'effects_number')}",
                        inline=False)

    elif command == 'skip':
        embed = discord.Embed(title="Help", description=f"`/skip` - {tg(gi, 'skip')}")

    elif command == 'nowplaying':
        embed = discord.Embed(title="Help", description=f"`/nowplaying` - {tg(gi, 'nowplaying')}")
        embed.add_field(name=f"{tg(gi, 'Arguments')}", value=f"`user_only` - {tg(gi, 'ephemeral')}", inline=False)

    elif command == 'last':
        embed = discord.Embed(title="Help", description=f"`/last` - {tg(gi, 'last')}")
        embed.add_field(name=f"{tg(gi, 'Arguments')}", value=f"`user_only` - {tg(gi, 'ephemeral')}", inline=False)

    elif command == 'loop':
        embed = discord.Embed(title="Help", description=f"`/loop` - {tg(gi, 'loop')}")

    elif command == 'loop_this':
        embed = discord.Embed(title="Help", description=f"`/loop_this` - {tg(gi, 'loop_this')}")

    elif command == 'queue':
        embed = discord.Embed(title="Help", description=f"`/queue` - {tg(gi, 'queue_add')}")
        embed.add_field(name=f"{tg(gi, 'Arguments')}", value=f"`url` - {tg(gi, 'url')}", inline=False)
        embed.add_field(name="", value=f"`position` - {tg(gi, 'pos')}", inline=False)
        embed.add_field(name="", value=f"`mute_response` - {tg(gi, 'mute_response')}", inline=False)
        embed.add_field(name="", value=f"`force` - {tg(gi, 'force')}", inline=False)

    elif command == 'queue_import':
        embed = discord.Embed(title="Help", description=f"`/queue_import` - {tg(gi, 'queue_import')}")
        embed.add_field(name=f"{tg(gi, 'Arguments')}", value=f"`queue_string` - {tg(gi, 'queue_string')}", inline=False)
        embed.add_field(name="", value=f"`guild_id` - {tg(gi, 'guild_id')}", inline=False)
        embed.add_field(name="", value=f"`user_only` - {tg(gi, 'ephemeral')}", inline=False)

    elif command == 'queue_export':
        embed = discord.Embed(title="Help", description=f"`/queue_export` - {tg(gi, 'queue_export')}")
        embed.add_field(name=f"{tg(gi, 'Arguments')}", value=f"`guild_id` - {tg(gi, 'guild_id')}", inline=False)
        embed.add_field(name="", value=f"`user_only` - {tg(gi, 'ephemeral')}", inline=False)

    elif command == 'next_up':
        embed = discord.Embed(title="Help", description=f"`/next_up` - {tg(gi, 'next_up')}")
        embed.add_field(name=f"{tg(gi, 'Arguments')}", value=f"`url` - {tg(gi, 'url')}", inline=False)
        embed.add_field(name="", value=f"`user_only` - {tg(gi, 'ephemeral')}", inline=False)

    elif command == 'remove':
        embed = discord.Embed(title="Help", description=f"`/remove` - {tg(gi, 'remove')}")
        embed.add_field(name=f"{tg(gi, 'Arguments')}", value=f"`number` - {tg(gi, 'number')}", inline=False)
        embed.add_field(name="", value=f"`user_only` - {tg(gi, 'ephemeral')}", inline=False)

    elif command == 'clear':
        embed = discord.Embed(title="Help", description=f"`/clear` - {tg(gi, 'clear')}")
        embed.add_field(name=f"{tg(gi, 'Arguments')}", value=f"`user_only` - {tg(gi, 'ephemeral')}", inline=False)

    elif command == 'shuffle':
        embed = discord.Embed(title="Help", description=f"`/shuffle` - {tg(gi, 'shuffle')}")
        embed.add_field(name=f"{tg(gi, 'Arguments')}", value=f"`user_only` - {tg(gi, 'ephemeral')}", inline=False)

    elif command == 'show':
        embed = discord.Embed(title="Help", description=f"`/show` - {tg(gi, 'show')}")
        embed.add_field(name=f"{tg(gi, 'Arguments')}", value=f"`display_type` - {tg(gi, 'display_type')}", inline=False)
        embed.add_field(name="", value=f"`user_only` - {tg(gi, 'ephemeral')}", inline=False)

    elif command == 'search':
        embed = discord.Embed(title="Help", description=f"`/search` - {tg(gi, 'search')}")
        embed.add_field(name=f"{tg(gi, 'Arguments')}", value=f"`search_query` - {tg(gi, 'search_query')}", inline=False)
        embed.add_field(name="", value=f"`user_only` - {tg(gi, 'ephemeral')}", inline=False)

    elif command == 'stop':
        embed = discord.Embed(title="Help", description=f"`/stop` - {tg(gi, 'stop')}")

    elif command == 'pause':
        embed = discord.Embed(title="Help", description=f"`/pause` - {tg(gi, 'pause')}")

    elif command == 'resume':
        embed = discord.Embed(title="Help", description=f"`/resume` - {tg(gi, 'resume')}")

    elif command == 'join':
        embed = discord.Embed(title="Help", description=f"`/join` - {tg(gi, 'join')}")
        embed.add_field(name=f"{tg(gi, 'Arguments')}", value=f"`channel_id` - {tg(gi, 'channel_id')}", inline=False)

    elif command == 'disconnect':
        embed = discord.Embed(title="Help", description=f"`/disconnect` - {tg(gi, 'die')}")

    elif command == 'volume':
        embed = discord.Embed(title="Help", description=f"`/volume` - {tg(gi, 'volume')}")
        embed.add_field(name=f"{tg(gi, 'Arguments')}", value=f"`volume` - {tg(gi, 'volume')}", inline=False)
        embed.add_field(name="", value=f"`user_only` - {tg(gi, 'ephemeral')}", inline=False)

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
