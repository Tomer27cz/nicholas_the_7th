import json
from time import time
from pathlib import Path

from flask import Flask, render_template, request, url_for, redirect, session, send_file, abort
from werkzeug.utils import safe_join

from classes.data_classes import WebData
from classes.discord_classes import DiscordUser

from utils.convert import struct_to_time, convert_duration
from utils.log import log, collect_data
from utils.files import getReadableByteSize, getIconClassForFilename
from utils.translate import ftg
from utils.video_time import video_time_from_start
from utils.checks import check_isdigit
from utils.web import *

import config
from oauth import Oauth

authorized_users = config.AUTHORIZED_USERS
my_id = config.OWNER_ID
bot_id = config.CLIENT_ID
prefix = config.PREFIX
vlc_logo = config.VLC_LOGO
default_discord_avatar = config.DEFAULT_DISCORD_AVATAR
d_id = 349164237605568513

# --------------------------------------------- LOAD DATA --------------------------------------------- #

with open(f'{config.PARENT_DIR}db/radio.json', 'r', encoding='utf-8') as file:
    radio_dict = json.load(file)

with open(f'{config.PARENT_DIR}db/languages.json', 'r', encoding='utf-8') as file:
    languages_dict = json.load(file)
    text = languages_dict['en']
    authorized_users += [my_id, 349164237605568513]

guild = {}

# --------------------------------------------- FUNCTIONS --------------------------------------------- #
def check_admin(session_data):
    global guild
    if session_data is None:
        raise ValueError('Session data is None')

    user_id = int(session_data['discord_user']['id'])
    if user_id in authorized_users:
        if guild is None:
            guild = get_guilds()
        return list(guild.keys())

    return session_data['mutual_guild_ids']

# --------------------------------------------- WEB SERVER --------------------------------------------- #

app = Flask(__name__)
app.config['SECRET_KEY'] = config.WEB_SECRET_KEY

@app.route('/')
async def index_page():
    log(request.remote_addr, '/index', log_type='ip')
    if 'discord_user' in session.keys():
        user = session['discord_user']
    else:
        user = None

    return render_template('nav/index.html', user=user)

@app.route('/about')
async def about_page():
    log(request.remote_addr, '/about', log_type='ip')
    if 'discord_user' in session.keys():
        user = session['discord_user']
    else:
        user = None

    return render_template('nav/about.html', user=user)

# Guild pages
@app.route('/guild')
async def guilds_page():
    global guild
    log(request.remote_addr, '/guild', log_type='ip')
    if 'discord_user' in session.keys():
        user = session['discord_user']
        mutual_guild_ids = check_admin(session)
    elif 'mutual_guild_ids' in session.keys():
        mutual_guild_ids = session['mutual_guild_ids']
        user = None
        if mutual_guild_ids is None:
            mutual_guild_ids = []
            session['mutual_guild_ids'] = []
    else:
        user = None
        mutual_guild_ids = []

    def sort_list(val_lst, key_lst):
        if not key_lst:
            return dict(val_lst)
        return dict(sorted(val_lst, key=lambda x: key_lst.index(x[0]) if x[0] in key_lst else len(key_lst)))

    guild = get_guilds()

    return render_template('nav/guild_list.html', guild=sort_list(guild.items(), mutual_guild_ids).values(), len=len,
                           user=user, errors=None, mutual_guild_ids=mutual_guild_ids)

@app.route('/guild/<int:guild_id>', methods=['GET', 'POST'])
async def guild_get_key_page(guild_id):
    global guild
    log(request.remote_addr, f'/guild/{guild_id}', log_type='ip')
    if 'discord_user' in session.keys():
        user = session['discord_user']
        mutual_guild_ids = check_admin(session)
    elif 'mutual_guild_ids' in session.keys():
        mutual_guild_ids = session['mutual_guild_ids']
        user = None
        if mutual_guild_ids is None:
            mutual_guild_ids = []
            session['mutual_guild_ids'] = []
    else:
        user = None
        mutual_guild_ids = []

    guild_object = get_guild(int(guild_id))

    if guild_object is None:
        return render_template('base/message.html', guild_id=guild_id, user=user,
                               message="That Server doesn't exist or the bot is not in it", errors=None, title='Error')

    if guild_object.id in mutual_guild_ids:
        return redirect(f'/guild/{guild_id}&key={guild_object.data.key}')

    if user is not None:
        if int(user['id']) in authorized_users:
            return redirect(f'/guild/{guild_id}&key={guild_object.data.key}')

    if request.method == 'POST':
        if 'key' in request.form.keys():
            if request.form['key'] == guild_object.data.key:
                if 'mutual_guild_ids' not in session.keys():
                    session['mutual_guild_ids'] = []

                session['mutual_guild_ids'] = session['mutual_guild_ids'] + [guild_object.id]
                # mutual_guild_ids = session['mutual_guild_ids']

                return redirect(f'/guild/{guild_id}&key={request.form["key"]}')

        return render_template('control/action/get_key.html', guild_id=guild_id,
                               errors=[f'Invalid code: {request.form["key"]} -> do /key in the server'],
                               url=Oauth.discord_login_url, user=user)

    return render_template('control/action/get_key.html', guild_id=guild_id, errors=None, url=Oauth.discord_login_url, user=user)

@app.route('/guild/<int:guild_id>&key=<key>', methods=['GET', 'POST'])
async def guild_page(guild_id, key):
    global guild
    log(request.remote_addr, f'/guild/{guild_id}&key={key}', log_type='ip')
    errors = []
    messages = []
    scroll_position = 0
    admin = False

    if 'discord_user' in session.keys():
        user = session['discord_user']
        user_name, user_id = user['username'], int(user['id'])
        mutual_guild_ids = check_admin(session)
        if user_id in authorized_users:
            admin = True
    elif 'mutual_guild_ids' in session.keys():
        mutual_guild_ids = session['mutual_guild_ids']
        user = None
        user_name, user_id = request.remote_addr, 'WEB Guest'
        admin = False
    else:
        mutual_guild_ids = []
        user = None
        user_name, user_id = request.remote_addr, 'WEB Guest'
        admin = False

    if request.method == 'POST':
        web_data = WebData(int(guild_id), user_name, user_id)
        response = None

        keys = request.form.keys()
        if 'del_btn' in keys:
            log(web_data, 'remove', [request.form['del_btn']], log_type='web', author=web_data.author)
            response = execute_function('remove_def', web_data=web_data, number=int(request.form['del_btn']),
                                        list_type='queue')
        if 'up_btn' in keys:
            log(web_data, 'up', [request.form['up_btn']], log_type='web', author=web_data.author)
            response = execute_function('web_up', web_data=web_data, number=request.form['up_btn'])
        if 'down_btn' in keys:
            log(web_data, 'down', [request.form['down_btn']], log_type='web', author=web_data.author)
            response = execute_function('web_down', web_data=web_data, number=request.form['down_btn'])
        if 'top_btn' in keys:
            log(web_data, 'top', [request.form['top_btn']], log_type='web', author=web_data.author)
            response = execute_function('web_top', web_data=web_data, number=request.form['top_btn'])
        if 'bottom_btn' in keys:
            log(web_data, 'bottom', [request.form['bottom_btn']], log_type='web', author=web_data.author)
            response = execute_function('web_bottom', web_data=web_data, number=request.form['bottom_btn'])
        if 'duplicate_btn' in keys:
            log(web_data, 'duplicate', [request.form['duplicate_btn']], log_type='web', author=web_data.author)
            response = execute_function('web_duplicate', web_data=web_data, number=request.form['duplicate_btn'])

        if 'play_btn' in keys:
            log(web_data, 'play', [], log_type='web', author=web_data.author)
            response = execute_function('play_def', web_data=web_data)
        if 'stop_btn' in keys:
            log(web_data, 'stop', [], log_type='web', author=web_data.author)
            response = execute_function('stop_def', web_data=web_data)
        if 'pause_btn' in keys:
            log(web_data, 'pause', [], log_type='web', author=web_data.author)
            response = execute_function('pause_def', web_data=web_data)
        if 'skip_btn' in keys:
            log(web_data, 'skip', [], log_type='web', author=web_data.author)
            response = execute_function('skip_def', web_data=web_data)

        if 'loop_btn' in keys:
            log(web_data, 'loop', [], log_type='web', author=web_data.author)
            response = execute_function('loop_command_def', web_data=web_data)
        if 'shuffle_btn' in keys:
            log(web_data, 'shuffle', [], log_type='web', author=web_data.author)
            response = execute_function('shuffle_def', web_data=web_data)
        if 'clear_btn' in keys:
            log(web_data, 'clear', [], log_type='web', author=web_data.author)
            response = execute_function('clear_def', web_data=web_data)

        if 'disconnect_btn' in keys:
            log(web_data, 'disconnect', [], log_type='web', author=web_data.author)
            response = execute_function('web_disconnect', web_data=web_data)
        if 'join_btn' in keys:
            log(web_data, 'join', [], log_type='web', author=web_data.author)
            response = execute_function('web_join', web_data=web_data, form=request.form)

        if 'queue_btn' in keys:
            log(web_data, 'queue', [request.form['queue_btn']], log_type='web', author=web_data.author)
            response = execute_function('web_queue', web_data=web_data, video_type=request.form['queue_btn'],
                                        position=None)
        if 'nextup_btn' in keys:
            log(web_data, 'nextup', [request.form['nextup_btn'], 0], log_type='web', author=web_data.author)
            response = execute_function('web_queue', web_data=web_data, video_type=request.form['nextup_btn'],
                                        position=0)
        if 'hdel_btn' in keys:
            log(web_data, 'history remove', [request.form['hdel_btn']], log_type='web', author=web_data.author)
            response = execute_function('remove_def', web_data=web_data, number=int(request.form['hdel_btn'][1:]),
                                        list_type='history')

        if 'edit_btn' in keys:
            log(web_data, 'web_video_edit', [request.form['edit_btn']], log_type='web', author=web_data.author)
            response = execute_function('web_video_edit', web_data=web_data, form=request.form)
        if 'options_btn' in keys:
            log(web_data, 'web_options', [request.form], log_type='web', author=web_data.author)
            response = execute_function('web_user_options_edit', web_data=web_data, form=request.form)

        if 'volume_btn' in keys:
            log(web_data, 'volume_command_def', [request.form['volumeRange'], request.form['volumeInput']],
                log_type='web', author=web_data.author)
            response = execute_function('volume_command_def', web_data=web_data, volume=int(request.form['volumeRange']))
        if 'jump_btn' in keys:
            log(web_data, 'set_video_time', [request.form['jump_btn']], log_type='web', author=web_data.author)
            response = execute_function('set_video_time', web_data=web_data, time_stamp=request.form['jump_btn'])
        if 'time_btn' in keys:
            log(web_data, 'set_video_time', [request.form['timeInput']], log_type='web', author=web_data.author)
            response = execute_function('set_video_time', web_data=web_data, time_stamp=request.form['timeInput'])

        if 'ytURL' in keys:
            log(web_data, 'queue_command_def', [request.form['ytURL']], log_type='web', author=web_data.author)
            response = execute_function('queue_command_def', web_data=web_data, url=request.form['ytURL'])
        if 'radio-checkbox' in keys:
            log(web_data, 'web_queue_from_radio', [request.form['radio-checkbox']], log_type='web',
                author=web_data.author)
            response = execute_function('web_queue_from_radio', web_data=web_data,
                                        radio_name=request.form['radio-checkbox'])

        if 'saveName' in keys:
            log(web_data, 'web_save_queue', [request.form['saveName']], log_type='web', author=web_data.author)
            response = execute_function('new_queue_save', web_data=web_data, save_name=request.form['saveName'])
        if 'loadName' in keys:
            log(web_data, 'web_load_queue', [request.form['loadName']], log_type='web', author=web_data.author)
            response = execute_function('load_queue_save', web_data=web_data, save_name=request.form['loadName'])

        if 'scroll' in keys:
            try:
                scroll_position = int(request.form['scroll'])
            except ValueError:
                try:
                    scroll_position = int(float(request.form['scroll']))
                except ValueError:
                    scroll_position = 0

        if response:
            if not response.response:
                errors = [response.message]
            else:
                messages = [response.message]

    guild_object = get_guild(int(guild_id))

    if guild_object is None:
        return render_template('base/message.html', guild_id=guild_id, user=user,
                               message="That Server doesn't exist or the bot is not in it", errors=None, title='Error')

    if key != guild_object.data.key:
        if guild_object.id in mutual_guild_ids:
            return redirect(f'/guild/{guild_id}&key={guild_object.data.key}')
        return redirect(url_for('guild_get_key_page', guild_id=guild_id))

    mutual_guild_ids.append(guild_object.id)
    session['mutual_guild_ids'] = mutual_guild_ids

    if guild_object.now_playing:
        await get_renew(guild_object.id, 'now_playing', 0)
        pd = guild_object.now_playing.played_duration
    else:
        pd = [{'start': None, 'end': None}]

    if guild_object.queue:
        for i, video in enumerate(guild_object.queue):
            await get_renew(guild_object.id, 'queue', i)

    guild_object = get_guild(int(guild_id))
    if guild_object is None:
        return render_template('base/message.html', guild_id=guild_id, user=user,
                               message="That Server doesn't exist or the bot is not in it", errors=None, title='Error')

    with open(f'{config.PARENT_DIR}db/saves.json', 'r', encoding='utf-8') as f:
        saves = json.load(f)
        if str(guild_object.id) in saves.keys():
            saves = saves[str(guild_object.id)]
        else:
            saves = None

    return render_template('control/guild.html', guild=guild_object, struct_to_time=struct_to_time,
                           convert_duration=convert_duration, get_username=get_username, errors=errors,
                           messages=messages, user=user, admin=admin, volume=round(guild_object.options.volume * 100),
                           radios=list(radio_dict.values()), scroll_position=scroll_position,
                           languages_dict=languages_dict, tg=ftg, gi=int(guild_id), time=time, int=int,
                           video_time_played=video_time_from_start, pd=json.dumps(pd), check_isdigit=check_isdigit,
                           saves=saves)

@app.route('/guild/<int:guild_id>/update')
async def update_page(guild_id):
    try:
        guild_id = int(guild_id)
    except (ValueError, TypeError):
        await abort(404)

    response = get_update(guild_id)

    if response:
        return response
    return None

# User Login
@app.route('/login')
async def login_page():
    log(request.remote_addr, '/login', log_type='web')
    admin = False
    update = False
    if 'discord_user' in session.keys():
        access_token = session['access_token']
        update = True
    else:
        code = request.args.get('code')
        if code is None:
            return redirect(Oauth.discord_login_url)

        response = Oauth.get_access_token(code)
        access_token = response['access_token']
        session['access_token'] = access_token

        log(request.remote_addr, 'Got access token', log_type='text')


    user = Oauth.get_user(access_token)

    collect_data(user)
    session['discord_user'] = user

    guilds = Oauth.get_user_guilds(session['access_token'])
    collect_data(f'{user["username"]} -> {guilds}')

    bot_guilds = Oauth.get_bot_guilds()
    mutual_guilds = [x for x in guilds if x['id'] in map(lambda i: i['id'], bot_guilds)]

    mutual_guild_ids = [int(guild_object['id']) for guild_object in mutual_guilds]
    if int(user['id']) in authorized_users:
        mutual_guild_ids = [int(guild_object['id']) for guild_object in bot_guilds]
        admin = True
    session['mutual_guild_ids'] = mutual_guild_ids

    if update:
        return render_template('base/message.html',
                               message=f"Updated session for {user['username']}#{user['discriminator']}", errors=None,
                               user=user, title='Update Success')

    return render_template('base/message.html',
                           message=f"Success, logged in as {user['username']}#{user['discriminator']}{' -> ADMIN' if admin else ''}",
                           errors=None, user=user, title='Login Success')

@app.route('/logout')
async def logout_page():
    log(request.remote_addr, '/logout', log_type='ip')
    if 'discord_user' in session.keys():
        user = session['discord_user']
        username = user['username']
        discriminator = user['discriminator']
        session.clear()
        return render_template('base/message.html', message=f"Logged out as {username}#{discriminator}", errors=None,
                               user=None, title='Logout Success')
    return redirect(url_for('index_page'))

# Session
@app.route('/reset')
async def reset_page():
    log(request.remote_addr, '/reset', log_type='ip')
    session.clear()
    return redirect(url_for('index_page'))

# Invite
@app.route('/invite')
async def invite_page():
    log(request.remote_addr, '/invite', log_type='ip')
    return redirect(config.INVITE_URL)

# Admin
@app.route('/admin', methods=['GET', 'POST'])
async def admin_page():
    global guild
    log(request.remote_addr, '/admin', log_type='ip')
    if 'discord_user' in session.keys():
        user = session['discord_user']
        user_name = user['username']
        user_id = user['id']
    else:
        return render_template('base/message.html', message="403 Forbidden", message4='You have to be logged in.',
                               errors=None, user=None, title='403 Forbidden'), 403

    if int(user['id']) not in authorized_users:
        return abort(403)

    errors = []
    messages = []
    response = None

    if request.method == 'POST':
        guild_id = 0
        web_data = WebData(guild_id, user_name, user_id)

        keys = request.form.keys()
        form = request.form
        try:
            if 'download_btn' in keys:
                file_name = request.form['download_file']
                log(web_data, 'download file', [file_name], log_type='web', author=web_data.author)
                try:
                    if file_name in ['log.log', 'data.log', 'activity.log', 'apache_error.log', 'apache_activity.log']:
                        return send_file(f'{config.PARENT_DIR}db/log/{file_name}', as_attachment=True)
                    else:
                        return send_file(f'{config.PARENT_DIR}db/{file_name}', as_attachment=True)
                except Exception as e:
                    return str(e)
            if 'upload_btn' in keys:
                f = request.files['file']
                file_name = request.form['download_file']
                log(web_data, 'upload file', [f.filename, file_name], log_type='web', author=web_data.author)
                if not f:
                    errors = ['No file']
                elif file_name != f.filename:
                    errors = ['File name does not match the one in the input field']
                else:
                    try:
                        if file_name in ['log.log', 'data.log', 'activity.log', 'apache_error.log',
                                         'apache_activity.log']:
                            f.save(f"{config.PARENT_DIR}db/log/{f.filename}")
                            messages = ['File uploaded']
                        else:
                            f.save(f"{config.PARENT_DIR}db/{f.filename}")
                            messages = ['File uploaded']
                    except Exception as e:
                        return str(e)
            if 'edit_btn' in keys:
                log(web_data, 'edit options', [form], log_type='web', author=web_data.author)
                response = execute_function('web_options_edit', web_data, form=form)
        except Exception as e:
            errors = [str(e)]
            log(web_data, 'error', [str(e)], log_type='web', author=web_data.author)

        if response:
            if response.response:
                messages = [response.message]
            else:
                errors = [response.message]

    guild = get_guilds()
    return render_template('nav/admin.html', user=user, guild=guild.values(), languages_dict=languages_dict,
                           errors=errors, messages=messages)

# Admin Log
@app.route('/admin/log', methods=['GET', 'POST'])
async def admin_log_page():
    log(request.remote_addr, '/admin/log', log_type='ip')
    if 'discord_user' in session.keys():
        user = session['discord_user']
    else:
        return render_template('base/message.html', message="403 Forbidden", message4='You have to be logged in.',
                               errors=None, user=None, title='403 Forbidden'), 403

    if int(user['id']) not in authorized_users:
        return abort(403)

    with open(f'{config.PARENT_DIR}db/log/log.log', 'r', encoding='utf-8') as f:
        log_data = f.readlines()

    return render_template('admin/log.html', user=user, log_data=log_data, title='Log')

# Admin Data Data
@app.route('/admin/data', methods=['GET', 'POST'])
async def admin_data_page():
    log(request.remote_addr, '/admin/data', log_type='ip')
    if 'discord_user' in session.keys():
        user = session['discord_user']
    else:
        return render_template('base/message.html', message="403 Forbidden", message4='You have to be logged in.',
                               errors=None, user=None, title='403 Forbidden'), 403

    if int(user['id']) not in authorized_users:
        return abort(403)

    with open(f'{config.PARENT_DIR}db/log/data.log', 'r', encoding='utf-8') as f:
        data_data = f.readlines()

    return render_template('admin/data.html', user=user, data_data=data_data, title='Log')

# Admin data
@app.route('/admin/user/<int:user_id>', methods=['GET', 'POST'])
async def admin_user_page(user_id):
    log(request.remote_addr, f'/admin/user/{user_id}', log_type='ip')
    if 'discord_user' in session.keys():
        user = session['discord_user']
    else:
        return render_template('base/message.html', message="403 Forbidden", message4='You have to be logged in.',
                               errors=None, user=None, title='403 Forbidden'), 403

    if int(user['id']) not in authorized_users:
        return abort(403)

    data = get_user_data(user_id)

    return render_template('admin/data/user.html', user=user, data=data, title='User Info')

# Admin file
@app.route('/admin/file/', defaults={'reqPath': ''})
@app.route('/admin/file/<path:reqPath>')
def getFiles(reqPath):
    log(request.remote_addr, f'/admin/file/{reqPath}', log_type='ip')
    if 'discord_user' in session.keys():
        user = session['discord_user']
    else:
        return render_template('base/message.html', message="403 Forbidden", message4='You have to be logged in.',
                               errors=None, user=None, title='403 Forbidden'), 403

    if int(user['id']) not in authorized_users:
        return abort(403)

    # Joining the base and the requested path
    absPath = safe_join(config.PARENT_DIR, reqPath)

    # Return 404 if path doesn't exist
    if not os.path.exists(absPath):
        return abort(404)

    # Check if path is a file and serve
    if os.path.isfile(absPath):
        return send_file(absPath)

    # Show directory contents
    def fObjFromScan(x):
        fileStat = x.stat()
        # return file information for rendering
        return {'name': x.name,
                'fIcon': "bi bi-folder-fill" if os.path.isdir(x.path) else getIconClassForFilename(x.name),
                'relPath': os.path.relpath(x.path, config.PARENT_DIR).replace("\\", "/"),
                'mTime': struct_to_time(fileStat.st_mtime),
                'size': getReadableByteSize(num=fileStat.st_size, relPath=os.path.relpath(x.path, config.PARENT_DIR).replace("\\", "/"))}

    fileObjs = [fObjFromScan(x) for x in os.scandir(absPath)]

    # get parent directory url
    parentFolderPath = os.path.relpath(Path(absPath).parents[0], config.PARENT_DIR).replace("\\", "/")
    if parentFolderPath == '..':
        parentFolderPath = '.'

    return render_template('admin/files.html', data={'files': fileObjs, 'parentFolder': parentFolderPath}, title='Files', user=user)

# def getFiles(reqPath):
#     log(request.remote_addr, f'/admin/file/{reqPath}', log_type='ip')
#     if 'discord_user' in session.keys():
#         user = session['discord_user']
#     else:
#         return render_template('base/message.html', message="403 Forbidden", message4='You have to be logged in.',
#                                errors=None, user=None, title='403 Forbidden'), 403
#
#     if int(user['id']) not in authorized_users:
#         return abort(403)
#
#     # Return 404 if path doesn't exist
#     if not os.path.exists(reqPath):
#         return abort(404)
#
#     # Check if path is a file and serve
#     if os.path.isfile(reqPath):
#         return send_file(reqPath)
#
#     # Show directory contents
#     def fObjFromScan(x):
#         fileStat = x.stat()
#         # return file information for rendering
#         return {'name': x.name,
#                 'fIcon': "bi bi-folder-fill" if os.path.isdir(x.path) else getIconClassForFilename(x.name),
#                 'relPath': x.path,
#                 'mTime': struct_to_time(fileStat.st_mtime),
#                 'size': getReadableByteSize(fileStat.st_size)
#                 }
#
#     fileObjs = [fObjFromScan(x) for x in os.scandir(reqPath)]
#     # get parent directory url
#
#     try:
#         parentFolderPath = Path(reqPath).parents[0]
#     except IndexError:
#         parentFolderPath = reqPath
#
#     return render_template('admin/files.html', data={'files': fileObjs, 'parentFolder': parentFolderPath},
#                            title='Admin File', user=user, errors=None, messages=None)

# Admin guild
@app.route('/admin/guild', methods=['GET', 'POST'])
async def admin_guild_redirect():
    log(request.remote_addr, '/admin/guild', log_type='ip')
    return redirect('/admin')

@app.route('/admin/guild/<int:guild_id>', methods=['GET', 'POST'])
async def admin_guild(guild_id):
    global guild
    log(request.remote_addr, f'/admin/guild/{guild_id}', log_type='ip')
    if 'discord_user' in session.keys():
        user = session['discord_user']
        user_name = user['username']
        user_id = user['id']
    else:
        return render_template('base/message.html', message="403 Forbidden", message4='You have to be logged in.',
                               errors=None, user=None, title='403 Forbidden'), 403

    if int(user['id']) not in authorized_users:
        return abort(403)

    errors = []
    messages = []
    response = None

    if request.method == 'POST':
        web_data = WebData(guild_id, user_name, user_id)

        keys = request.form.keys()
        form = request.form
        try:
            if 'edit_btn' in keys:
                log(web_data, 'web_options_edit', [form], log_type='web', author=web_data.author)
                response = execute_function('web_options_edit', web_data, form=form)
            if 'delete_guild_btn' in keys:
                log(web_data, 'web_delete_guild', [guild_id], log_type='web', author=web_data.author)
                response = execute_function('web_delete_guild', web_data, guild_id=guild_id)
            if 'disconnect_guild_btn' in keys:
                log(web_data, 'web_disconnect_guild', [guild_id], log_type='web', author=web_data.author)
                response = execute_function('web_disconnect_guild', web_data, guild_id=guild_id)
            if 'invite_btn' in keys:
                log(web_data, 'web_create_invite', [guild_id], log_type='web', author=web_data.author)
                response = execute_function('web_create_invite', web_data, guild_id=guild_id)
        except Exception as e:
            errors = [str(e)]
            log(web_data, 'error', [str(e)], log_type='web', author=web_data.author)

        if response:
            if response.response:
                messages = [response.message]
            else:
                errors = [response.message]

    guild_object = get_guild(int(guild_id))
    if guild_object is None:
        return abort(404)
    return render_template('admin/guild.html', user=user, guild_object=guild_object, languages_dict=languages_dict,
                           errors=errors, messages=messages, title='Admin Guild Dashboard', int=int)

# Admin guild data
@app.route('/admin/guild/<int:guild_id>/users', methods=['GET', 'POST'])
async def admin_guild_users(guild_id):
    log(request.remote_addr, f'/admin/guild/{guild_id}/users', log_type='ip')
    if 'discord_user' in session.keys():
        user = session['discord_user']
    else:
        return render_template('base/message.html', message="403 Forbidden", message4='You have to be logged in.',
                               errors=None, user=None, title='403 Forbidden'), 403

    if int(user['id']) not in authorized_users:
        return abort(403)

    guild_object = get_guild(int(guild_id))
    if guild_object is None:
        return abort(404)
    guild_members = get_guild_members(int(guild_id))
    return render_template('admin/data/guild_users.html', user=user, guild_object=guild_object, users=guild_members, title='Users')

@app.route('/admin/guild/<int:guild_id>/channels', methods=['GET', 'POST'])
async def admin_guild_channels(guild_id):
    log(request.remote_addr, f'/admin/guild/{guild_id}/channels', log_type='ip')
    if 'discord_user' in session.keys():
        user = session['discord_user']
    else:
        return render_template('base/message.html', message="403 Forbidden", message4='You have to be logged in.',
                               errors=None, user=None, title='403 Forbidden'), 403

    if int(user['id']) not in authorized_users:
        return abort(403)

    guild_object = get_guild(int(guild_id))
    guild_channels = get_guild_channels(int(guild_id))
    return render_template('admin/data/guild_channels.html', user=user, channels=guild_channels, len=len,
                           guild_object=guild_object, title='Voice Channels')

@app.route('/admin/guild/<int:guild_id>/textChannels', methods=['GET', 'POST'])
async def admin_guild_text_channels(guild_id):
    log(request.remote_addr, f'/admin/guild/{guild_id}/textChannels', log_type='ip')
    if 'discord_user' in session.keys():
        user = session['discord_user']
    else:
        return render_template('base/message.html', message="403 Forbidden", message4='You have to be logged in.',
                               errors=None, user=None, title='403 Forbidden'), 403

    if int(user['id']) not in authorized_users:
        return abort(403)

    guild_object = get_guild(int(guild_id))
    guild_text_channels = get_guild_text_channels(int(guild_id))
    return render_template('admin/data/guild_channels.html', user=user, channels=guild_text_channels, len=len,
                           guild_object=guild_object, title='Text Channels')

@app.route('/admin/guild/<int:guild_id>/roles', methods=['GET', 'POST'])
async def admin_guild_roles(guild_id):
    log(request.remote_addr, f'/admin/guild/{guild_id}/roles', log_type='ip')
    if 'discord_user' in session.keys():
        user = session['discord_user']
    else:
        return render_template('base/message.html', message="403 Forbidden", message4='You have to be logged in.',
                               errors=None, user=None, title='403 Forbidden'), 403

    if int(user['id']) not in authorized_users:
        return abort(403)

    guild_object = get_guild(int(guild_id))
    guild_roles = get_guild_roles(int(guild_id))
    return render_template('admin/data/guild_roles.html', user=user, roles=guild_roles, len=len, vars=vars, dict=dict,
                           guild_object=guild_object, title='Roles')

@app.route('/admin/guild/<int:guild_id>/invites', methods=['GET', 'POST'])
async def admin_guild_invites(guild_id):
    log(request.remote_addr, f'/admin/guild/{guild_id}/invites', log_type='ip')
    if 'discord_user' in session.keys():
        user = session['discord_user']
    else:
        return render_template('base/message.html', message="403 Forbidden", message4='You have to be logged in.',
                               errors=None, user=None, title='403 Forbidden'), 403

    if int(user['id']) not in authorized_users:
        return abort(403)

    guild_object = get_guild(int(guild_id))
    guild_invites = get_guild_invites(int(guild_id))
    return render_template('admin/data/guild_invites.html', user=user, invites=guild_invites,
                           guild_object=guild_object, title='Invites', type=type, DiscordUser=DiscordUser)

@app.route('/admin/guild/<int:guild_id>/saves', methods=['GET', 'POST'])
async def admin_guild_saves(guild_id):
    log(request.remote_addr, f'/admin/guild/{guild_id}/saves', log_type='ip')
    if 'discord_user' in session.keys():
        user = session['discord_user']
        user_name, user_id = user['username'], int(user['id'])

    else:
        return render_template('base/message.html', message="403 Forbidden", message4='You have to be logged in.',
                               errors=None, user=None, title='403 Forbidden'), 403

    if int(user['id']) not in authorized_users:
        return abort(403)

    errors = []
    messages = []
    response = None

    if request.method == 'POST':
        web_data = WebData(guild_id, user_name, user_id)

        keys = request.form.keys()
        form = request.form
        try:
            if 'deleteSave' in keys:
                log(web_data, 'web_delete_save', [form['save_name']], log_type='web', author=web_data.author)
                response = execute_function('delete_queue_save', web_data, save_name=form['save_name'])
            if 'renameSave' in keys:
                log(web_data, 'web_rename_save', [form['old_name'], form['new_name']], log_type='web', author=web_data.author)
                response = execute_function('rename_queue_save', web_data, old_name=form['old_name'], new_name=form['new_name'])
        except Exception as e:
            errors = [str(e)]
            log(web_data, 'error', [str(e)], log_type='web', author=web_data.author)

        if response:
            if response.response:
                messages = [response.message]
            else:
                errors = [response.message]

    guild_object = get_guild(int(guild_id))

    with open(f"{config.PARENT_DIR}db/saves.json", "r", encoding='utf-8') as f:
        saves = json.load(f)

    guild_saves = None
    if str(guild_id) in saves.keys():
        guild_saves = saves[str(guild_id)]

    del saves

    return render_template('admin/saves.html', user=user, saves=guild_saves, len=len,
                           guild_object=guild_object, title='Saves', get_username=get_username,
                           struct_to_time=struct_to_time, convert_duration=convert_duration, tg=ftg, gi=int(guild_id),
                           errors=errors, messages=messages)

# Admin Chat
@app.route('/admin/guild/<int:guild_id>/chat/', defaults={'channel_id': 0}, methods=['GET', 'POST'])
@app.route('/admin/guild/<int:guild_id>/chat/<int:channel_id>', methods=['GET', 'POST'])
def admin_chat(guild_id, channel_id):
    log(request.remote_addr, f'/admin/guild/{guild_id}/chat/{channel_id}', log_type='ip')
    if 'discord_user' in session.keys():
        user = session['discord_user']
        user_name = user['username']
        user_id = user['id']
    else:
        return render_template('base/message.html', message="403 Forbidden", message4='You have to be logged in.',
                               errors=None, user=None, title='403 Forbidden'), 403

    if int(user['id']) not in authorized_users:
        return abort(403)

    guild_text_channels = get_guild_text_channels(int(guild_id))
    if guild_text_channels is None:
        return abort(404)

    errors = []
    messages = []
    response = None

    if request.method == 'POST':
        web_data = WebData(guild_id, user_name, user_id)

        keys = request.form.keys()
        form = request.form
        try:
            if 'download_btn' in keys:
                log(web_data, 'download_guild_channel', [form['download_btn']], log_type='web', author=web_data.author)
                response = execute_function('download_guild_channel', web_data, channel_id=form['download_btn'])
            if 'download_guild_btn' in keys:
                log(web_data, 'download_guild', [form['download_guild_btn']], log_type='web', author=web_data.author)
                response = execute_function('download_guild', web_data, guild_id=form['download_guild_btn'])
        except Exception as e:
            errors = [str(e)]
            log(web_data, 'error', [str(e)], log_type='web', author=web_data.author)

        if response:
            if response.response:
                messages = [response.message]
            else:
                errors = [response.message]


    if channel_id == 0:
        content = 0
    else:
        content = get_channel_content(int(guild_id), int(channel_id))

    return render_template('admin/data/chat.html', user=user, guild_id=guild_id, channel_id=channel_id,  channels=guild_text_channels, content=content, title='Chat', errors=errors, messages=messages)

@app.route('/admin/guild/<int:guild_id>/fastchat/', defaults={'channel_id': 0}, methods=['GET', 'POST'])
@app.route('/admin/guild/<int:guild_id>/fastchat/<int:channel_id>', methods=['GET', 'POST'])
def admin_fastchat(guild_id, channel_id):
    log(request.remote_addr, f'/admin/guild/{guild_id}/fastchat/{channel_id}', log_type='ip')
    if 'discord_user' in session.keys():
        user = session['discord_user']
    else:
        return render_template('base/message.html', message="403 Forbidden", message4='You have to be logged in.',
                               errors=None, user=None, title='403 Forbidden'), 403

    if int(user['id']) not in authorized_users:
        return abort(403)

    guild_text_channels = get_guild_text_channels(int(guild_id))
    if guild_text_channels is None:
        return abort(404)

    if channel_id == 0:
        content = 0
    else:
        content = get_fast_channel_content(int(channel_id))

    return render_template('admin/data/fastchat.html', user=user, guild_id=guild_id, channel_id=channel_id,  channels=guild_text_channels, content=content, title='Fast Chat')

# Error Handling
@app.errorhandler(404)
async def page_not_found(_):
    log(request.remote_addr, f'{request.path} -> 404', log_type='ip')
    if 'discord_user' in session.keys():
        user = session['discord_user']
    else:
        user = None
    return render_template('base/message.html', message="404 Not Found",
                           message4='The requested URL was not found on the server. If you entered the URL manually please check your spelling and try again.',
                           errors=None, user=user, title='404 Not Found'), 404

@app.errorhandler(403)
async def page_forbidden(_):
    log(request.remote_addr, f'{request.path} -> 403', log_type='ip')
    if 'discord_user' in session.keys():
        user = session['discord_user']
    else:
        user = None
    return render_template('base/message.html', message="403 Forbidden", message4='You do not have permission.',
                           user=user, errors=None, title='403 Forbidden'), 403

def main():
    # get_guilds()
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 5420)))

if __name__ == '__main__':
    main()
