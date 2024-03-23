from classes.data_classes import WebData, Guild, ReturnData
from classes.discord_classes import DiscordUser
from classes.typed_dictionaries import WebSearchResult

from commands.autocomplete import query_autocomplete_def

from utils.convert import convert_duration
from utils.log import log, collect_data
from utils.files import get_readable_byte_size, get_icon_class_for_filename, get_log_files
from utils.translate import txtf
from utils.video_time import video_time_from_start
from utils.checks import check_isdigit
from utils.web import *

from web_func.utils import *

import classes.data_classes

from flask import Flask, render_template, request, url_for, redirect, send_file, abort, send_from_directory
from flask import session as flask_session, jsonify
from werkzeug.utils import safe_join

from pathlib import Path
from typing import List
import json
import math
import asyncio

from oauth import Oauth

import config

authorized_users = config.AUTHORIZED_USERS
my_id = config.OWNER_ID
bot_id = config.CLIENT_ID
prefix = config.PREFIX
vlc_logo = config.VLC_LOGO
default_discord_avatar = config.DEFAULT_DISCORD_AVATAR
d_id = 349164237605568513

# -------------------------------------------- Database -------------------------------------------- #

from database.guild import *
from database.main import *

# --------------------------------------------- LOAD DATA --------------------------------------------- #

from utils.global_vars import radio_dict, languages_dict, sound_effects
authorized_users += [my_id, 349164237605568513]

# --------------------------------------------- FUNCTIONS --------------------------------------------- #

def check_admin(session_data, _db) -> list:
    if session_data is None:
        raise ValueError('Session data is None')

    if 'discord_user' not in session_data.keys():
        if 'allowed_guilds' not in session_data.keys():
            return []
        return session_data['allowed_guilds']

    user_id = int(session_data['discord_user']['id'])
    if user_id in authorized_users:
        with app.app_context():
            return [_tuple[0] for _tuple in _db.session.query(classes.data_classes.Guild).with_entities(classes.data_classes.Guild.id).all()]

    return session_data['allowed_guilds']

def is_admin(user) -> bool:
    if user is None:
        return False

    user_id = user.get('id', None)
    if user_id is None:
        return False

    try:
        user_id = int(user_id)
    except ValueError:
        return False

    if user_id in authorized_users:
        return True

    return False

async def simulate():
    try:
        await asyncio.sleep(float(os.environ.get('SIMULATE', 0)))
    except (ValueError, TypeError):
        pass

# Global vars
badge_dict_new = {
            'active_developer': '/static/discord/svg/active_developer.svg',
            'bot_http_interactions': '/static/discord/svg/bot_http_interactions.svg',
            'bug_hunter': '/static/discord/svg/bug_hunter.svg',
            'bug_hunter_level_2': '/static/discord/svg/bug_hunter_level_2.svg',
            'discord_certified_moderator': '/static/discord/svg/discord_certified_moderator.svg',
            'early_supporter': '/static/discord/svg/early_supporter.svg',
            'hypesquad': '/static/discord/svg/hypesquad.svg',
            'hypesquad_balance': '/static/discord/svg/hypesquad_balance.svg',
            'hypesquad_bravery': '/static/discord/svg/hypesquad_bravery.svg',
            'hypesquad_brilliance': '/static/discord/svg/hypesquad_brilliance.svg',
            'partner': '/static/discord/svg/partner.svg',
            'spammer': '/static/discord/svg/spammer.svg',
            'staff': '/static/discord/svg/staff.svg',
            'system': '/static/discord/svg/system.svg',
            'team_user': '/static/discord/svg/team_user.svg',
            'value': '/static/discord/svg/value.svg',
            'verified_bot': '/static/discord/svg/verified_bot.svg',
            'verified_bot_developer': '/static/discord/svg/verified_bot_developer.svg'
        }

# --------------------------------------------- WEB SERVER -------------------------------------------------------------

app = Flask(__name__)
app.config['SECRET_KEY'] = config.WEB_SECRET_KEY

file_path = os.path.join(os.path.abspath(os.getcwd()), 'db', 'database.db')
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{file_path}'

from flask_sqlalchemy import SQLAlchemy
db = SQLAlchemy(app, model_class=Base)

with app.app_context():
    for guild_obj in db.session.query(Guild).all():
        guild_obj.keep_alive = False
    db.session.commit()

@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'), 'favicon/favicon.ico', mimetype='image/vnd.microsoft.icon')

@app.context_processor
def inject_data():
    return dict(lang='en',
                auth=authorized_users,
                int=int,
                range=range,
                len=len,
                vars=vars,
                dict=dict,
                enumerate=enumerate,
                txt=txtf,
                get_username=get_username,
                struct_to_time=struct_to_time,
                convert_duration=convert_duration,
                video_time_from_start=video_time_from_start,
                check_isdigit=check_isdigit,
                ceil=math.ceil
                )

@app.before_request
def make_session_permanent():
    flask_session.permanent = True

# @app.teardown_appcontext
# def shutdown_session(exception=None):
#     ses.remove()

# -------------------------------------------------- Index page --------------------------------------------------------

@app.route('/')
async def index_page():
    log(request.remote_addr, request.full_path, log_type='ip')
    await simulate()
    user = flask_session.get('discord_user', {})

    try:
        return render_template('nav/index.html', user=user)
    except Exception as e:
        return f'index = {str(e)}'

@app.route('/about')
async def about_page():
    log(request.remote_addr, '/about', log_type='ip')
    await simulate()
    user = flask_session.get('discord_user', {})

    return render_template('nav/about.html', user=user)

# -------------------------------------------------- Guild pages -------------------------------------------------------

@app.route('/guild')
async def guilds_page():
    log(request.remote_addr, request.full_path, log_type='ip')
    await simulate()
    user = flask_session.get('discord_user', {})
    allowed_guilds = check_admin(flask_session, db)

    _guilds = sort_guilds(db.session.query(classes.data_classes.Guild).all(), allowed_guilds)

    return render_template('nav/guild_list.html', guilds=_guilds, allowed_guilds=allowed_guilds, user=user)

@app.route('/guild/<int:guild_id>', methods=['GET', 'POST'])
async def guild_page(guild_id):
    log(request.remote_addr, request.full_path, log_type='ip')
    await simulate()

    # Get data from session
    user = flask_session.get('discord_user', {})
    user_name = user.get('username', 'WEB Guest')
    user_id = user.get('id', 'Remote Address')
    key = request.args.get('key')
    admin = is_admin(user)
    allowed_guilds = check_admin(flask_session, db)

    guild_object = guild(db, int(guild_id))
    if guild_object is None:
        return render_template('base/message.html', guild_id=guild_id, user=user,
                               message="That Server doesn't exist or the bot is not in it", errors=None, title='Error')

    if key != guild_object.data.key:
        if guild_object.id in allowed_guilds:
            return redirect(f'/guild/{guild_id}?key={guild_object.data.key}')

        if user:
            if int(user['id']) in authorized_users:
                return redirect(f'/guild/{guild_id}?key={guild_object.data.key}')

        if request.method == 'POST':
            key = request.form['key'] if 'key' in request.form.keys() else None
            if key == guild_object.data.key:
                if 'allowed_guilds' not in flask_session.keys():
                    flask_session['allowed_guilds'] = []

                flask_session['allowed_guilds'] = flask_session['allowed_guilds'] + [guild_object.id]
                # mutual_guild_ids = flask_session['mutual_guild_ids']

                return redirect(f'/guild/{guild_id}?key={guild_object.data.key}')

            return render_template('main/get_key.html', guild_id=guild_id,
                                   errors=[f'Invalid code: {request.form["key"]} -> do /key in the server'],
                                   url=Oauth.discord_login_url, user=user)

        return render_template('main/get_key.html', guild_id=guild_id, errors=None, url=Oauth.discord_login_url, user=user)

    if guild_object.id not in allowed_guilds:
        allowed_guilds.append(guild_object.id)
        flask_session['allowed_guilds'] = allowed_guilds

    flask_session['guild_id'] = guild_id

    errors = []
    messages = []
    if request.method == 'POST':
        web_data = WebData(int(guild_id), {'id': user_id, 'name': user_name})
        response = None

        keys = request.form.keys()
        if 'play_btn' in keys:
            log(web_data, 'play', {}, log_type='web', author=web_data.author)
            response = execute_function('play_def', web_data=web_data)
        if 'stop_btn' in keys:
            log(web_data, 'stop', {}, log_type='web', author=web_data.author)
            response = execute_function('stop_def', web_data=web_data)
        if 'pause_btn' in keys:
            log(web_data, 'pause', {}, log_type='web', author=web_data.author)
            response = execute_function('pause_def', web_data=web_data)

        if 'skip_btn' in keys:
            log(web_data, 'skip', {}, log_type='web', author=web_data.author)
            response = execute_function('skip_def', web_data=web_data)

        if 'disconnect_btn' in keys:
            log(web_data, 'disconnect', {}, log_type='web', author=web_data.author)
            response = execute_function('web_disconnect', web_data=web_data)
        if 'join_btn' in keys:
            log(web_data, 'join', {}, log_type='web', author=web_data.author)
            response = execute_function('web_join', web_data=web_data, form=request.form)

        if 'edit_btn' in keys:
            log(web_data, 'web_video_edit', {'form': request.form}, log_type='web', author=web_data.author)
            response = execute_function('web_video_edit', web_data=web_data, form=request.form)
        if 'options_btn' in keys:
            log(web_data, 'web_options', {'form': request.form}, log_type='web', author=web_data.author)
            response = execute_function('web_user_options_edit', web_data=web_data, form=request.form)

        if 'volume_btn' in keys:
            log(web_data, 'volume_command_def', {'form': request.form}, log_type='web', author=web_data.author)
            response = execute_function('volume_command_def', web_data=web_data, volume=int(request.form['volumeRange']))
        if 'jump_btn' in keys:
            log(web_data, 'set_video_time', {'form': request.form}, log_type='web', author=web_data.author)
            response = execute_function('set_video_time', web_data=web_data, time_stamp=request.form['jump_btn'])
        if 'time_btn' in keys:
            log(web_data, 'set_video_time', {'form': request.form}, log_type='web', author=web_data.author)
            response = execute_function('set_video_time', web_data=web_data, time_stamp=request.form['timeInput'])

        # if 'ytURL' in keys:
        #     log(web_data, 'queue_command_def', {'form': request.form}, log_type='web', author=web_data.author)
        #     response = execute_function('queue_command_def', web_data=web_data, url=request.form['ytURL'])
        # if 'radio-checkbox' in keys:
        #     log(web_data, 'web_queue_from_radio', {'form': request.form}, log_type='web', author=web_data.author)
        #     response = execute_function('web_queue_from_radio', web_data=web_data, radio_name=request.form['radio-checkbox'])

        if response:
            if not response.response:
                errors = [response.message]
            # else:
            #     messages = [response.message]

    # pd = played_duration, npd = now_playing.duration
    pd = guild_object.now_playing.played_duration if guild_object.now_playing else [{'start': None, 'end': None}]
    npd = (guild_object.now_playing.duration if check_isdigit(guild_object.now_playing.duration) else 'null') if guild_object.now_playing else 'null'

    if guild_object.now_playing:
        await guild_object.now_playing.renew(None)

    return render_template('main/guild.html',
                           guild=guild(db, guild_id),
                           gi=int(guild_id),
                           key=key,
                           user=user,
                           errors=errors,
                           messages=messages,
                           volume=round(guild_object.options.volume * 100),
                           saves=guild_save_names(db, guild_object.id),
                           pd=json.dumps(pd),
                           npd=npd,
                           bot_status=get_guild_bot_status(int(guild_id)),
                           last_updated=int(guild_object.last_updated['queue']),
                           # radios=sort_radios(radio_dict),
                           admin=admin
                           )

# ---------------------------------------------------- HTMX ------------------------------------------------------------

@app.route('/guild/<int:guild_id>/queue')
async def htmx_queue(guild_id):
    await simulate()

    user = flask_session.get('discord_user', {})
    user_name = user.get('username', 'WEB Guest')
    user_id = user.get('id', 'Remote Address')
    admin = is_admin(user)
    response = ReturnData(True, 'No action')

    # await asyncio.sleep(5)

    # Queue API for HTMX
    # 
    # attributes:
    #   key: guild key - used to verify user
    #   render: json, html, none
    #   act: action - actions (below)
    #   var: variable - usually a number
    #   resp: (true, false, only) - if true renders response in html,
    #                               only renders response in html, false does not render response

    key = request.args.get('key')
    render = request.args.get('render')
    act = request.args.get('act')
    var = request.args.get('var')
    resp = request.args.get('resp')
    
    guild_object = guild(db, guild_id)
    if guild_object is None:
        return {'success': False, 'message': 'Guild not found'}, 404, {'ContentType': 'application/json'}

    if key != guild_object.data.key:
        return {'success': False, 'message': 'Invalid key'}, 403, {'ContentType': 'application/json'}

    if render and render not in ['json', 'html', 'none']:
        render = 'html'

    if resp not in ['true', 'false', 'only']:
        resp = 'false'

    if act:
        web_data = WebData(int(guild_id), {'id': user_id, 'name': user_name})
        if 'now_video' == act:
            track = guild_object.now_playing
            if not track:
                return {'success': False, 'message': 'No video playing'}, 404, {'ContentType': 'application/json'}

            if render == 'json':
                return jsonify(guild_object.now_playing.to_json())

            return render_template('main/htmx/now_playing.html', gi=int(guild_id), guild=guild_object, key=key, admin=admin)

        if 'queue_video' == act:
            if not var.isdigit() or int(var) >= len(guild_object.queue):
                return {'success': False, 'message': 'Invalid var'}, 400, {'ContentType': 'application/json'}

            track = guild_object.queue[int(var)]
            await track.renew(None)

            if render == 'json':
                _return = {
                    'success': True,
                    'message': 'Video found',
                    'video': track.to_json()
                }
                return _return, 200, {'ContentType': 'application/json'}

            return render_template('main/htmx/queue_video.html', gi=int(guild_id), guild=guild_object,
                                   struct_to_time=struct_to_time, convert_duration=convert_duration,
                                   get_username=get_username, key=key, admin=admin, track=track)

        if 'del_btn' == act:
            log(web_data, 'remove', {'var': var}, log_type='web', author=web_data.author)
            response = execute_function('remove_def', web_data=web_data, number=int(var), list_type='queue')
        if 'up_btn' == act:
            log(web_data, 'up', {'var': var}, log_type='web', author=web_data.author)
            response = execute_function('web_up', web_data=web_data, number=int(var))
        if 'down_btn' == act:
            log(web_data, 'down', {'var': var}, log_type='web', author=web_data.author)
            response = execute_function('web_down', web_data=web_data, number=int(var))
        if 'top_btn' == act:
            log(web_data, 'top', {'var': var}, log_type='web', author=web_data.author)
            response = execute_function('web_top', web_data=web_data, number=int(var))
        if 'bottom_btn' == act:
            log(web_data, 'bottom', {'var': var}, log_type='web', author=web_data.author)
            response = execute_function('web_bottom', web_data=web_data, number=int(var))
        if 'duplicate_btn' == act:
            log(web_data, 'duplicate', {'var': var}, log_type='web', author=web_data.author)
            response = execute_function('web_duplicate', web_data=web_data, number=int(var))

        # Buttons
        if 'loop_btn' == act:
            log(web_data, 'loop', {}, log_type='web', author=web_data.author)
            execute_function('loop_command_def', web_data=web_data)
            return render_template('main/htmx/single/loop.html', gi=guild_id, guild=guild_object, key=key)
        if 'shuffle_btn' == act:
            log(web_data, 'shuffle', {}, log_type='web', author=web_data.author)
            response = execute_function('shuffle_def', web_data=web_data)
        if 'clear_btn' == act:
            log(web_data, 'clear', {}, log_type='web', author=web_data.author)
            response = execute_function('clear_def', web_data=web_data)

        # History Video
        if 'queue_btn' == act:
            log(web_data, 'queue', {'var': var}, log_type='web', author=web_data.author)
            response = execute_function('web_queue', web_data=web_data, video_type=var, position=None)
        if 'nextup_btn' == act:
            log(web_data, 'nextup', {'var': var, 'position': 0}, log_type='web', author=web_data.author)
            response = execute_function('web_queue', web_data=web_data, video_type=var, position=0)

        # Admin
        # if 'edit_btn' == act:
        #     log(web_data, 'web_video_edit', [request.form['edit_btn']], log_type='web', author=web_data.author)
        #     response = execute_function('web_video_edit', web_data=web_data, form=request.form)
        # if 'options_btn' == act:
        #     log(web_data, 'web_options', [request.form], log_type='web', author=web_data.author)
        #     response = execute_function('web_user_options_edit', web_data=web_data, form=request.form)

        if 'add' == act:
            log(web_data, 'queue_command_def', {'var': var}, log_type='web', author=web_data.author)
            response = execute_function('queue_command_def', web_data=web_data, url=var)

        # Save
        if 'loadName' == act:
            log(web_data, 'web_load_queue', {'load_name': var}, log_type='web', author=web_data.author)
            response = execute_function('load_queue_save', web_data=web_data, save_name=var)
        if 'saveName' == act:
            log(web_data, 'web_save_queue', {'save_name': var}, log_type='web', author=web_data.author)
            response = execute_function('new_queue_save', web_data=web_data, save_name=var, author={'id': user_id, 'name': user_name})

    if response is None:
        return {'success': False, 'message': 'Unknown error'}, 500, {'ContentType': 'application/json'}

    if render == 'json':
        _return = {
            'success': response.response,
            'message': response.message,
            'queue': [],
        }

        if resp == 'only':
            return jsonify(_return)

        for video in guild_object.queue:
            await video.renew(None)
            _return['queue'].append(video.to_json())

        return jsonify(_return)

    if resp == 'only':
        return render_template('main/htmx/single/response.html', response=response)

    guild_object = guild(db, guild_id)
    for video in guild_object.queue:
        await video.renew(None)

    return render_template('main/htmx/queue.html', gi=int(guild_id), guild=guild_object, key=key,
                           admin=admin, response=response, resp=resp)

@app.route('/guild/<int:guild_id>/history')
async def htmx_history(guild_id):
    await simulate()

    user = flask_session.get('discord_user', {})
    user_name = user.get('username', 'WEB Guest')
    user_id = user.get('id', 'Remote Address')
    admin = is_admin(user)

    guild_object = guild(db, guild_id)
    if guild_object is None:
        return abort(404)

    key = request.args.get('key')
    if key != guild_object.data.key:
        return abort(403)


    act = request.args.get('act')
    if act:
        if not admin:
            return abort(403)

        web_data = WebData(int(guild_id), {'id': user_id, 'name': user_name})
        if 'hdel_btn' == act:
            var = request.args.get('var')
            log(web_data, 'history remove', {'var': var}, log_type='web', author=web_data.author)
            execute_function('remove_def', web_data=web_data, number=int(var), list_type='history')

    return render_template('main/htmx/history.html', gi=int(guild_id), guild=guild_object,
                           struct_to_time=struct_to_time, convert_duration=convert_duration, get_username=get_username,
                           key=key, admin=admin)

@app.route('/guild/<int:guild_id>/modals')
async def htmx_modal(guild_id):
    await simulate()

    user = flask_session.get('discord_user', {})
    # user_name = user.get('username', 'WEB Guest')
    # user_id = user.get('id', 'Remote Address')
    admin = is_admin(user)

    guild_object = guild(db, int(guild_id))
    if guild_object is None:
        return abort(404)

    key = request.args.get('key')
    if key != guild_object.data.key:
        return abort(403)

    modal_type = request.args.get('type')
    if modal_type == 'queue1Modal':
        return render_template('main/htmx/modals/queue/queue1Modal.html', gi=int(guild_id), key=key)
    if modal_type == 'queue2Modal':
        return render_template('main/htmx/modals/queue/queue2Modal.html', gi=int(guild_id), key=key)
    if modal_type == 'queue3Modal':
        return render_template('main/htmx/modals/queue/queue3Modal.html', gi=int(guild_id), key=key)
    if modal_type == 'queue4Modal':  # local radio
        return render_template('main/htmx/modals/queue/queue4Modal.html', gi=int(guild_id), key=key, radios=sort_radios(radio_dict))
    if modal_type == 'queue5Modal':  # local files
        return render_template('main/htmx/modals/queue/queue5Modal.html', gi=int(guild_id), key=key, files=sound_effects, logo=vlc_logo)

    if modal_type == 'joinModal':
        return render_template('main/htmx/modals/joinModal.html', gi=int(guild_id), guild=guild_object, key=key)
    if modal_type == 'loadModal':
        return render_template('main/htmx/modals/loadModal.html', gi=int(guild_id), saves=guild_saves(db, guild_object.id), key=key)
    if modal_type == 'optionsModal':
        return render_template('main/htmx/modals/optionsModal.html', gi=int(guild_id), guild=guild_object, languages_dict=languages_dict, int=int, key=key)
    if modal_type == 'saveModal':
        return render_template('main/htmx/modals/saveModal.html', gi=int(guild_id), key=key)
    if modal_type == 'timeModal':
        return render_template('main/htmx/modals/timeModal.html', gi=int(guild_id), guild=guild_object, key=key)

    if modal_type == 'queue':
        track_id = request.args.get('var')
        track = guild_object.queue[int(track_id)]
        return render_template('main/htmx/modals/video/queue.html', gi=int(guild_id), guild=guild_object, track=track, key=key)
    if modal_type == 'history':
        track_id = request.args.get('var')
        track = guild_object.history[int(track_id)]
        return render_template('main/htmx/modals/video/history.html', gi=int(guild_id), guild=guild_object, track=track, key=key)
    if modal_type == 'now_playing':
        return render_template('main/htmx/modals/video/now_playing.html', gi=int(guild_id), guild=guild_object, key=key)
    if modal_type == 'queue_edit' and admin:
        track_id = request.args.get('var')
        track = guild_object.queue[int(track_id)]
        return render_template('main/htmx/modals/video/queue_edit.html', gi=int(guild_id), guild=guild_object, track=track, key=key)
    if modal_type == 'history_edit' and admin:
        track_id = request.args.get('var')
        track = guild_object.history[int(track_id)]
        return render_template('main/htmx/modals/video/history_edit.html', gi=int(guild_id), guild=guild_object, track=track, key=key)
    if modal_type == 'now_playing_edit' and admin:
        return render_template('main/htmx/modals/video/now_playing_edit.html', gi=int(guild_id), guild=guild_object, key=key)

    return abort(404)

@app.route('/guild/<int:guild_id>/search')
async def htmx_search(guild_id):
    await simulate()

    db_key = guild_data_key(db, guild_id)
    key = request.args.get('key')
    if key != db_key:
        return abort(403)

    act = request.args.get('act')
    if act == 'youtube':
        results: List[WebSearchResult] = await query_autocomplete_def(None, query=request.args.get('var'), include_youtube=True, raw=True)
    elif act == 'tunein':
        results: List[WebSearchResult] = await query_autocomplete_def(None, query=request.args.get('var'), include_tunein=True, raw=True)
    elif act == 'radio':
        results: List[WebSearchResult] = await query_autocomplete_def(None, query=request.args.get('var'), include_radio=True, raw=True)
    elif act == 'garden':
        results: List[WebSearchResult] = await query_autocomplete_def(None, query=request.args.get('var'), include_garden=True, raw=True)
    elif act == 'local':
        results: List[WebSearchResult] = await query_autocomplete_def(None, query=request.args.get('var'), include_local=True, raw=True)
    else:
        return abort(404)

    return render_template('main/htmx/search.html', gi=int(guild_id), key=key, results=results)

@app.route('/guild/<int:guild_id>/action')
async def htmx_action(guild_id):
    await simulate()

    user = flask_session.get('discord_user', {})
    user_name = user.get('username', 'WEB Guest')
    user_id = user.get('id', 'Remote Address')

    key = request.args.get('key')
    act = request.args.get('act')
    var = request.args.get('var')
    resp = request.args.get('resp')
    refresh = request.args.get('refresh')

    guild_object = guild(db, guild_id)
    if guild_object is None:
        return {'success': False, 'message': 'Guild not found'}, 404, {'ContentType': 'application/json'}

    if key != guild_object.data.key:
        return {'success': False, 'message': 'Invalid key'}, 403, {'ContentType': 'application/json'}

    if resp not in ['true', 'false']:
        resp = 'false'

    if refresh not in ['true', 'false']:
        refresh = 'true'

    if not act:
        return {'success': False, 'message': 'No action'}, 400, {'ContentType': 'application/json'}

    web_data = WebData(int(guild_id), {'id': user_id, 'name': user_name})

    if 'play' == act:
        log(web_data, 'play', {}, log_type='web', author=web_data.author)
        response = execute_function('play_def', web_data=web_data)
    elif 'skip' == act:
        log(web_data, 'skip', {}, log_type='web', author=web_data.author)
        response = execute_function('skip_def', web_data=web_data)
    elif 'stop' == act:
        log(web_data, 'stop', {}, log_type='web', author=web_data.author)
        response = execute_function('stop_def', web_data=web_data)
    elif 'pause' == act:
        log(web_data, 'pause', {}, log_type='web', author=web_data.author)
        response = execute_function('pause_def', web_data=web_data)

    elif 'join' == act:
        log(web_data, 'join', {'var': var}, log_type='web', author=web_data.author)
        response = execute_function('web_join', web_data=web_data, channel_id=var)
    elif 'disconnect' == act:
        log(web_data, 'disconnect', {}, log_type='web', author=web_data.author)
        response = execute_function('web_disconnect', web_data=web_data)

    elif 'jump' == act:
        log(web_data, 'set_video_time', {'var': var}, log_type='web', author=web_data.author)
        response = execute_function('set_video_time', web_data=web_data, time_stamp=var)

    elif 'time' == act:
        log(web_data, 'set_video_time', {'var': var}, log_type='web', author=web_data.author)
        response = execute_function('set_video_time', web_data=web_data, time_stamp=var)
    elif 'volume' == act:
        log(web_data, 'volume_command_def', {'var': var}, log_type='web', author=web_data.author)
        response = execute_function('volume_command_def', web_data=web_data, volume=var)

    elif 'edit' == act:
        log(web_data, 'web_video_edit', {}, log_type='web', author=web_data.author)
        response = execute_function('web_video_edit', web_data=web_data, form=request.form)  # TODO
    elif 'options' == act:
        log(web_data, 'web_options', {}, log_type='web', author=web_data.author)
        response = execute_function('web_user_options_edit', web_data=web_data, form=request.form)  # TODO

    elif 'loop' == act:
        log(web_data, 'loop', {}, log_type='web', author=web_data.author)
        execute_function('loop_command_def', web_data=web_data)
        return render_template('main/htmx/single/loop.html', gi=guild_id, guild=guild_object, key=key)

    else:
        return {'success': False, 'message': 'Unknown action'}, 400, {'ContentType': 'application/json'}

    if response is None:
        return {'success': False, 'message': 'No response'}, 500, {'ContentType': 'application/json'}

    if resp == 'false' and refresh == 'false':
        return {'success': response.response, 'message': response.message, 'refresh': refresh}, 200, {'ContentType': 'application/json'}

    return render_template('main/htmx/single/response.html', response=response, refresh=refresh, resp=resp)

# -------------------------------------------------- SocketIO ----------------------------------------------------------

# @app.route('/push')
# def push_endpoint():
#     guild_id = request.args.get('id')
#     if guild_id:
#         socketio.emit('update', int(time()), to=str(guild_id))
#
#         return json.dumps({'success': True}), 200, {'ContentType': 'application/json'}
#
#     return abort(403)
#
# @socketio.on('connect')
# def connect():
#     if 'guild_id' in flask_session.keys():
#         join_room(flask_session['guild_id'])
#
# @socketio.on('disconnect')
# def disconnect():
#     if 'guild_id' in flask_session.keys():
#         leave_room(flask_session['guild_id'])
#
# @socketio.on('getUpdates')
# def get_update(guild_id):
#     join_room(guild_id)

# ------------------------------------------------- User Login ---------------------------------------------------------

@app.route('/login')
async def login_page():
    log(request.remote_addr, request.full_path, log_type='web')
    await simulate()

    update, admin = False, False
    if 'discord_user' not in flask_session.keys():
        code = request.args.get('code')
        if code is None:
            return redirect(Oauth.discord_login_url)

        response = Oauth.get_access_token(code)
        flask_session['access_token'] = response['access_token']

        log(request.remote_addr, 'Got access token', log_type='text')

    if 'discord_user' in flask_session.keys():
        update = True

    # Get API data
    user = Oauth.get_user(flask_session['access_token'])
    user_guilds = Oauth.get_user_guilds(flask_session['access_token'])

    # Collect data
    collect_data(user)
    collect_data(f'{user["username"]} -> {user_guilds}')

    # Store data in session
    flask_session['discord_user'] = user
    flask_session['discord_user_guilds'] = [int(u_guild['id']) for u_guild in user_guilds]

    # Set allowed guilds to user guilds
    allowed_guilds = user_guilds

    # Check if user is admin and set allowed guilds to user+bot guilds
    if int(user['id']) in authorized_users:
        bot_guilds = Oauth.get_bot_guilds()
        allowed_guilds = bot_guilds+user_guilds

    # Store allowed guilds in session as list of guild IDs
    flask_session['allowed_guilds'] = [int(g_dict['id']) for g_dict in allowed_guilds]

    # Customize message
    msg_type = "updated session for" if update else "logged in as"
    message = f"Success, {msg_type} {user['username']}#{user['discriminator']}{' -> ADMIN' if admin else ''}"

    return render_template('base/message.html', message=message, errors=None, user=user, title='Login Success')

@app.route('/logout')
async def logout_page():
    log(request.remote_addr, request.full_path, log_type='ip')
    await simulate()

    if 'discord_user' in flask_session.keys():
        user = flask_session['discord_user']
        username = user['username']
        discriminator = user['discriminator']
        flask_session.clear()
        return render_template('base/message.html', message=f"Logged out {username}#{discriminator}", errors=None,
                               user=None, title='Logout Success')
    return redirect(url_for('index_page'))

# ------------------------------------------------------- Session ------------------------------------------------------

@app.route('/reset')
async def reset_page():
    log(request.remote_addr, request.full_path, log_type='ip')
    await simulate()
    flask_session.clear()
    return redirect(url_for('index_page'))

# -------------------------------------------------------- Invite ------------------------------------------------------

@app.route('/invite')
async def invite_page():
    log(request.remote_addr, request.full_path, log_type='ip')
    await simulate()
    return redirect(config.INVITE_URL)

# -------------------------------------------------------- Admin -------------------------------------------------------

@app.route('/admin', methods=['GET', 'POST'])
async def admin_page():
    log(request.remote_addr, request.full_path, log_type='ip')
    await simulate()
    user = flask_session.get('discord_user', {})
    if user is None:
        return render_template('base/message.html', message="403 Forbidden", message4='You have to be logged in.',
                               errors=None, user=None, title='403 Forbidden'), 403

    if int(user.get('id', 0)) not in authorized_users:
        return abort(403)

    guild_list = sort_guilds(guilds(db), flask_session.get('discord_user_guilds', []))

    return render_template('admin/admin.html', user=user, guild=guild_list,
                           bot_status=get_guilds_bot_status(), last_played=guilds_last_played(db))

# Admin Files ---------------------------------------------------
@app.route('/admin/log')
async def admin_log_tree():
    log(request.remote_addr, request.full_path, log_type='ip')
    await simulate()
    user = flask_session.get('discord_user', {})
    if user is None:
        return render_template('base/message.html', message="403 Forbidden", message4='You have to be logged in.',
                               errors=None, user=None, title='403 Forbidden'), 403

    if not is_admin(user):
        return abort(403)

    log_files = get_log_files()

    return render_template('admin/text_file/txt_tree.html', user=user, title='Log', log_files=log_files)

# Files
@app.route('/admin/log/<path:file_name>')
async def admin_log_page(file_name):
    log(request.remote_addr, request.full_path, log_type='ip')
    await simulate()
    user = flask_session.get('discord_user', {})
    if user is None:
        return render_template('base/message.html', message="403 Forbidden", message4='You have to be logged in.',
                               errors=None, user=None, title='403 Forbidden'), 403

    if not is_admin(user):
        return abort(403)

    file_names = get_log_files()
    if file_name not in file_names:
        return abort(404)

    try:
        with open(f'db/log/{file_name}', 'r', encoding='utf-8') as f:
            lines = list(reversed([(value, index) for index, value in enumerate(f.readlines())]))
            chunks = math.ceil(len(lines) / 100)
    except Exception as e:
        log(request.remote_addr, [str(e)], log_type='error', author=user['username'])
        return abort(500)

    separate_lines = True if request.args.get('separate_lines') is not None else False

    return render_template('admin/text_file/iscroll.html', user=user, chunks=chunks, lines=lines, title='Log', log_type=file_name, separate_lines=separate_lines)

# @app.route('/admin/json/<path:file_name>')
# async def admin_json_page(file_name):
#     log(request.remote_addr, request.full_path, log_type='ip')
#     if 'discord_user' in flask_session.keys():
#         user = flask_session['discord_user']
#     else:
#         return render_template('base/message.html', message="403 Forbidden", message4='You have to be logged in.',
#                                errors=None, user=None, title='403 Forbidden'), 403
#
#     if int(user['id']) not in authorized_users:
#         return abort(403)
#
#     file_names = ['radio', 'languages']
#     if file_name not in file_names:
#         return abort(404)
#
#     try:
#         with open(f'{config.PARENT_DIR}db/{file_name}.json', 'r', encoding='utf-8') as f:
#             lines = list(reversed(f.readlines()))
#             chunks = math.ceil(len(lines) / 100)
#     except Exception as e:
#         log(request.remote_addr, [str(e)], log_type='error', author=user['username'])
#         return abort(500)
#
#     return render_template('admin/text_file/iscroll.html', user=user, chunks=chunks, lines=lines, title='Log', range=range, log_type=file_name)

# Admin Data Data
# @app.route('/admin/data', methods=['GET', 'POST'])
# async def admin_data_page():
#     log(request.remote_addr, request.full_path, log_type='ip')
#     if 'discord_user' in flask_session.keys():
#         user = flask_session['discord_user']
#     else:
#         return render_template('base/message.html', message="403 Forbidden", message4='You have to be logged in.',
#                                errors=None, user=None, title='403 Forbidden'), 403
#
#     if int(user['id']) not in authorized_users:
#         return abort(403)
#
#     with open(f'{config.PARENT_DIR}db/log/data.log', 'r', encoding='utf-8') as f:
#         data_data = f.readlines()
#
#     return render_template('admin/text_file/data.html', user=user, data_data=data_data, title='Log')

# Admin Files HTMX ---------------------------------------------------
@app.route('/admin/inflog', methods=['GET'])
async def admin_inflog_page():
    await simulate()
    user = flask_session.get('discord_user', {})
    if user is None:
        return render_template('base/message.html', message="403 Forbidden", message4='You have to be logged in.',
                               errors=None, user=None, title='403 Forbidden'), 403

    if not is_admin(user):
        return abort(403)

    log_type = request.args.get('type')
    if log_type not in get_log_files():
        return abort(404)

    try:
        with open(f'db/log/{log_type}', 'r', encoding='utf-8') as f:
            lines = list(reversed([(value, index) for index, value in enumerate(f.readlines())]))
    except Exception as e:
        log(request.remote_addr, [str(e)], log_type='error', author=user['username'])
        return abort(500)

    index_num = request.args.get('index')
    if index_num:
        index_num = int(index_num)
    else:
        return abort(400)

    if index_num > math.ceil(len(lines)/100):
        return "<p>Index out of range</p>"

    if index_num == 0:
        lines = lines[:100]
    else:
        if index_num == math.ceil(len(lines)/100):
            lines = lines[index_num*100:]
        else:
            lines = lines[index_num*100:(index_num+1)*100]

    separate_lines = True if request.args.get('separate_lines') is not None else False

    return render_template('admin/text_file/chunk.html', lines=lines, separate_lines=separate_lines)

# Admin user data ----------------------------------------------------
@app.route('/admin/user/<int:user_id>', methods=['GET', 'POST'])
async def admin_user_page(user_id):
    log(request.remote_addr, request.full_path, log_type='ip')
    await simulate()
    user = flask_session.get('discord_user', {})
    if user is None:
        return render_template('base/message.html', message="403 Forbidden", message4='You have to be logged in.',
                               errors=None, user=None, title='403 Forbidden'), 403

    if int(user.get('id', 0)) not in authorized_users:
        return abort(403)

    data = get_user_data(user_id)

    return render_template('admin/data/user.html', user=user, data=data, title='User Info', badge_dict=badge_dict_new)

# Admin file ---------------------------------------------------------
@app.route('/admin/file/', defaults={'reqPath': ''})
@app.route('/admin/file/<path:req_path>')
async def get_files(req_path):
    log(request.remote_addr, request.full_path, log_type='ip')
    await simulate()
    user = flask_session.get('discord_user', {})
    if user is None:
        return render_template('base/message.html', message="403 Forbidden", message4='You have to be logged in.',
                               errors=None, user=None, title='403 Forbidden'), 403

    if int(user.get('id', 0)) not in authorized_users:
        return abort(403)

    # Joining the base and the requested path
    abs_path = safe_join(config.PARENT_DIR, req_path)

    # Return 404 if path doesn't exist
    if not os.path.exists(abs_path):
        return abort(404)

    # Check if path is a file and serve
    if os.path.isfile(abs_path):
        return send_file(abs_path)

    # Show directory contents
    def f_obj_from_scan(x):
        file_stat = x.stat()
        # return file information for rendering
        return {'name': x.name,
                'fIcon': "bi bi-folder-fill" if os.path.isdir(x.path) else get_icon_class_for_filename(x.name),
                'relPath': os.path.relpath(x.path, config.PARENT_DIR).replace("\\", "/"),
                'mTime': struct_to_time(file_stat.st_mtime),
                'size': get_readable_byte_size(num=file_stat.st_size, rel_path=os.path.relpath(x.path, config.PARENT_DIR).replace("\\", "/"))}

    file_objs = [f_obj_from_scan(x) for x in os.scandir(abs_path)]

    # get parent directory url
    parent_folder_path = os.path.relpath(Path(abs_path).parents[0], config.PARENT_DIR).replace("\\", "/")
    if parent_folder_path == '..':
        parent_folder_path = '.'

    return render_template('admin/files.html', data={'files': file_objs, 'parentFolder': parent_folder_path}, title='Files', user=user)

# Admin guild ----------------------------------------------------------------------------------------------------------
@app.route('/admin/guild', methods=['GET', 'POST'])
async def admin_guild_redirect():
    log(request.remote_addr, request.full_path, log_type='ip')
    await simulate()
    return redirect('/admin')

@app.route('/admin/guild/<int:guild_id>', methods=['GET', 'POST'])
async def admin_guild(guild_id):
    log(request.remote_addr, request.full_path, log_type='ip')
    await simulate()
    user = flask_session.get('discord_user', {})
    if user is None:
        return render_template('base/message.html', message="403 Forbidden", message4='You have to be logged in.',
                               errors=None, user=None, title='403 Forbidden'), 403

    if int(user.get('id', 0)) not in authorized_users:
        return abort(403)

    errors = []
    messages = []
    response = None

    if request.method == 'POST':
        web_data = WebData(guild_id, {'id': user['id'], 'name': user['username']})

        keys = request.form.keys()
        form = request.form
        try:
            if 'edit_btn' in keys:
                log(web_data, 'web_options_edit', {'form': form}, log_type='web', author=web_data.author)
                response = execute_function('web_options_edit', web_data, form=form)
            if 'delete_guild_btn' in keys:
                log(web_data, 'web_delete_guild', {'guild_id': guild_id}, log_type='web', author=web_data.author)
                response = execute_function('web_delete_guild', web_data, guild_id=guild_id)
            if 'disconnect_guild_btn' in keys:
                log(web_data, 'web_disconnect_guild', {'guild_id': guild_id}, log_type='web', author=web_data.author)
                response = execute_function('web_disconnect_guild', web_data, guild_id=guild_id)
            if 'invite_btn' in keys:
                log(web_data, 'web_create_invite', {'guild_id': guild_id}, log_type='web', author=web_data.author)
                response = execute_function('web_create_invite', web_data, guild_id=guild_id)
        except Exception as e:
            errors = [str(e)]
            log(web_data, 'error', {'error': str(e)}, log_type='web', author=web_data.author)

        if response:
            if response.response:
                messages = [response.message]
            else:
                errors = [response.message]

    guild_object = guild(db, int(guild_id))
    if guild_object is None:
        return abort(404)
    return render_template('admin/guild.html', user=user, guild_object=guild_object, languages_dict=languages_dict,
                           errors=errors, messages=messages, title='Admin Guild Dashboard', int=int)

# ----------------------------------------------- Admin guild data -----------------------------------------------------
@app.route('/admin/guild/<int:guild_id>/users', methods=['GET', 'POST'])
async def admin_guild_users(guild_id):
    log(request.remote_addr, request.full_path, log_type='ip')
    await simulate()
    user = flask_session.get('discord_user', {})
    if user is None:
        return render_template('base/message.html', message="403 Forbidden", message4='You have to be logged in.',
                               errors=None, user=None, title='403 Forbidden'), 403

    if int(user.get('id', 0)) not in authorized_users:
        return abort(403)

    if not guild_exists(db, int(guild_id)):
        return abort(404)

    return render_template('admin/data/guild_users.html', user=user, data=guild_data(db, guild_id), title='Users')

@app.route('/admin/guild/<int:guild_id>/voice_channels', methods=['GET', 'POST'])
async def admin_guild_channels(guild_id):
    log(request.remote_addr, request.full_path, log_type='ip')
    await simulate()
    user = flask_session.get('discord_user', {})
    if user is None:
        return render_template('base/message.html', message="403 Forbidden", message4='You have to be logged in.',
                               errors=None, user=None, title='403 Forbidden'), 403

    if int(user.get('id', 0)) not in authorized_users:
        return abort(403)

    data = guild_data(db, int(guild_id))
    return render_template('admin/data/guild_channels.html', user=user, data=data, title='Voice Channels', channel_type='voice')

@app.route('/admin/guild/<int:guild_id>/text_channels', methods=['GET', 'POST'])
async def admin_guild_text_channels(guild_id):
    log(request.remote_addr, request.full_path, log_type='ip')
    await simulate()
    user = flask_session.get('discord_user', {})
    if user is None:
        return render_template('base/message.html', message="403 Forbidden", message4='You have to be logged in.',
                               errors=None, user=None, title='403 Forbidden'), 403

    if int(user.get('id', 0)) not in authorized_users:
        return abort(403)

    data = guild_data(db, int(guild_id))
    return render_template('admin/data/guild_channels.html', user=user, data=data, title='Text Channels', channel_type='text')

@app.route('/admin/guild/<int:guild_id>/roles', methods=['GET', 'POST'])
async def admin_guild_roles(guild_id):
    log(request.remote_addr, request.full_path, log_type='ip')
    await simulate()
    user = flask_session.get('discord_user', {})
    if user is None:
        return render_template('base/message.html', message="403 Forbidden", message4='You have to be logged in.',
                               errors=None, user=None, title='403 Forbidden'), 403

    if int(user.get('id', 0)) not in authorized_users:
        return abort(403)

    data = guild_data(db, int(guild_id))

    return render_template('admin/data/guild_roles.html', user=user, data=data, title='Roles')

@app.route('/admin/guild/<int:guild_id>/invites', methods=['GET', 'POST'])
async def admin_guild_invites(guild_id):
    log(request.remote_addr, request.full_path, log_type='ip')
    await simulate()
    user = flask_session.get('discord_user', {})
    if user is None:
        return render_template('base/message.html', message="403 Forbidden", message4='You have to be logged in.',
                               errors=None, user=None, title='403 Forbidden'), 403

    if int(user.get('id', 0)) not in authorized_users:
        return abort(403)

    guild_object = guild(db, int(guild_id))
    guild_invites = get_guild_invites(int(guild_id))
    return render_template('admin/data/guild_invites.html', user=user, invites=guild_invites,
                           guild_object=guild_object, title='Invites', type=type, DiscordUser=DiscordUser)

@app.route('/admin/guild/<int:guild_id>/saves', methods=['GET', 'POST'])
async def admin_guild_saves(guild_id):
    log(request.remote_addr, request.full_path, log_type='ip')
    await simulate()
    user = flask_session.get('discord_user', {})
    if user is None:
        return render_template('base/message.html', message="403 Forbidden", message4='You have to be logged in.',
                               errors=None, user=None, title='403 Forbidden'), 403

    if int(user['id']) not in authorized_users:
        return abort(403)

    if request.method == 'POST':
        web_data = WebData(guild_id, {'id': user['id'], 'name': user['username']})

        keys = request.form.keys()
        form = request.form
        try:
            if 'deleteSave' in keys:
                log(web_data, 'web_delete_save', {'form': form}, log_type='web', author=web_data.author)
                execute_function('delete_queue_save', web_data, save_name=form['save_name'])
            if 'renameSave' in keys:
                log(web_data, 'web_rename_save', {'form': form}, log_type='web', author=web_data.author)
                execute_function('rename_queue_save', web_data, old_name=form['old_name'], new_name=form['new_name'])
        except Exception as e:
            log(web_data, 'error', {'error': str(e)}, log_type='web', author=web_data.author)

    data = guild_data(db, int(guild_id))
    saves_count = guild_save_count(db, int(guild_id))
    return render_template('admin/data/guild_saves.html', user=user, data=data, saves_count=saves_count)

# -------------------------------------------- Admin guild data HTMX ---------------------------------------------------

@app.route('/admin/guild/<int:guild_id>/users/htmx', methods=['GET', 'POST'])
async def admin_guild_users_htmx(guild_id):
    await simulate()
    user = flask_session.get('discord_user', {})
    if user is None:
        return render_template('base/message.html', message="403 Forbidden", message4='You have to be logged in.',
                               errors=None, user=None, title='403 Forbidden')

    if int(user['id']) not in authorized_users:
        return abort(403)

    index = request.args.get('index')
    if index is not None:
        index = int(index)

        # users = get_guild(int(guild_id)).members[index*5:(index+1)*5]
        users = get_guild_members_index(int(guild_id), index*5, (index+1)*5)

        return render_template('admin/data/htmx/guild_users.html', users=users, badge_dict=badge_dict_new)

    return abort(400)

@app.route('/admin/guild/<int:guild_id>/channels/htmx', methods=['GET', 'POST'])
async def admin_guild_channels_htmx(guild_id):
    await simulate()
    user = flask_session.get('discord_user', {})
    if user is None:
        return render_template('base/message.html', message="403 Forbidden", message4='You have to be logged in.',
                               errors=None, user=None, title='403 Forbidden')

    if int(user['id']) not in authorized_users:
        return abort(403)

    index = request.args.get('index')
    type_of = request.args.get('type')
    channel_id = request.args.get('channel_id')

    if index is not None and type_of:
        if type_of not in ['text_channels', 'voice_channels', 'voice_members', 'text_members',]:
            return abort(400)

        if index is None:
            return abort(400)

        index = int(index)
        if type_of == 'voice_members':
            if not channel_id:
                return abort(400)
            channel_members = get_guild_channel_members(int(guild_id), int(channel_id))

            return render_template('admin/data/htmx/channels/guild_channels_members.html',
                                   channel_members=channel_members, channel_id=channel_id)

        if type_of == 'voice_channels':
            channels = get_guild_voice_channels_index(int(guild_id), index*5, (index+1)*5)

            return render_template('admin/data/htmx/channels/guild_channels.html',
                                   channels=channels, guild_id=guild_id, channel_type='voice')

        if type_of == 'text_members':
            if not channel_id:
                return abort(400)
            channel_members = get_guild_channel_members(int(guild_id), int(channel_id))

            return render_template('admin/data/htmx/channels/guild_channels_members.html',
                                   channel_members=channel_members, channel_id=channel_id)

        if type_of == 'text_channels':
            channels = get_guild_text_channels_index(int(guild_id), index*5, (index+1)*5)

            return render_template('admin/data/htmx/channels/guild_channels.html',
                                   channels=channels, guild_id=guild_id, channel_type='text')

    return abort(400)

@app.route('/admin/guild/<int:guild_id>/roles/htmx', methods=['GET', 'POST'])
async def admin_guild_roles_htmx(guild_id):
    await simulate()
    user = flask_session.get('discord_user', {})
    if user is None:
        return render_template('base/message.html', message="403 Forbidden", message4='You have to be logged in.',
                               errors=None, user=None, title='403 Forbidden')

    if int(user['id']) not in authorized_users:
        return abort(403)

    index = request.args.get('index')
    role_id = request.args.get('role_id')
    type_of = request.args.get('type')
    if index is not None:
        index = int(index)

    if type_of == 'role':
        if index is None:
            return abort(400)

        roles = get_guild_roles_index(int(guild_id), index*5, (index+1)*5)
        return render_template('admin/data/htmx/roles/guild_roles.html', roles=roles, guild_id=guild_id)

    if type_of == 'members':
        if not role_id:
            return abort(400)

        members = get_guild_role_members(int(guild_id), int(role_id))
        return render_template('admin/data/htmx/roles/guild_roles_members.html', members=members, role_id=role_id)

    if type_of == 'permissions':
        if not role_id:
            return abort(400)

        permissions = get_guild_role_permissions(int(guild_id), int(role_id))
        return render_template('admin/data/htmx/roles/guild_roles_permissions.html', permissions=permissions, role_id=role_id)

    return abort(400)

@app.route('/admin/guild/<int:guild_id>/saves/htmx', methods=['GET', 'POST'])
async def admin_guild_saves_htmx(guild_id):
    await simulate()
    user = flask_session.get('discord_user', {})
    if user is None:
        return render_template('base/message.html', message="403 Forbidden", message4='You have to be logged in.',
                               errors=None, user=None, title='403 Forbidden')

    if int(user['id']) not in authorized_users:
        return abort(403)

    index = request.args.get('index')
    type_of = request.args.get('type')
    save_id = request.args.get('save_id')
    if type_of == 'saves':
        if index is not None:
            index = int(index)

            saves = guild(db, int(guild_id)).saves[index*5:(index+1)*5]
            return render_template('admin/data/htmx/saves/guild_saves.html', saves=saves, gi=int(guild_id),
                                   guild_save_queue_count=guild_save_queue_count, struct_to_time=struct_to_time)
    if type_of == 'save_queue':
        if save_id is not None:
            save_id = int(save_id)
            save_queue = guild_save(db, int(guild_id), save_id).queue
            return render_template('admin/data/htmx/saves/guild_saves_queue.html', queue=save_queue, save_id=save_id,
                                   get_username=get_username, struct_to_time=struct_to_time, convert_duration=convert_duration)

    return abort(400)


# -------------------------------------------------- Admin Chat --------------------------------------------------------
@app.route('/admin/guild/<int:guild_id>/chat/', defaults={'channel_id': 0}, methods=['GET', 'POST'])
@app.route('/admin/guild/<int:guild_id>/chat/<int:channel_id>', methods=['GET', 'POST'])
async def admin_chat(guild_id, channel_id):
    log(request.remote_addr, request.full_path, log_type='ip')
    await simulate()
    user = flask_session.get('discord_user', {})
    if user is None:
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
        web_data = WebData(guild_id, {'id': user['id'], 'name': user['username']})

        keys = request.form.keys()
        form = request.form
        try:
            if 'download_btn' in keys:
                log(web_data, 'download_guild_channel', {'form': form}, log_type='web', author=web_data.author)
                response = execute_function('download_guild_channel', web_data, channel_id=form['download_btn'])
            if 'download_guild_btn' in keys:
                log(web_data, 'download_guild', {'form': form}, log_type='web', author=web_data.author)
                response = execute_function('download_guild', web_data, guild_id=form['download_guild_btn'])
        except Exception as e:
            errors = [str(e)]
            log(web_data, 'error', {'error': str(e)}, log_type='web', author=web_data.author)

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
async def admin_fastchat(guild_id, channel_id):
    log(request.remote_addr, request.full_path, log_type='ip')
    await simulate()
    user = flask_session.get('discord_user', {})
    if user is None:
        return render_template('base/message.html', message="403 Forbidden", message4='You have to be logged in.',
                               errors=None, user=None, title='403 Forbidden'), 403

    if int(user.get('id', 0)) not in authorized_users:
        return abort(403)

    guild_text_channels = get_guild_text_channels(int(guild_id))
    if guild_text_channels is None:
        return abort(404)

    if channel_id == 0:
        content = 0
    else:
        content = get_fast_channel_content(int(channel_id))

    return render_template('admin/data/fastchat.html', user=user, guild_id=guild_id, channel_id=channel_id,  channels=guild_text_channels, content=content, title='Fast Chat')

# -------------------------------------------------- Error Handling ----------------------------------------------------
@app.errorhandler(404)
async def page_not_found(_):
    log(request.remote_addr, f'{request.full_path} -> 404', log_type='ip')
    await simulate()
    return render_template('base/error.html', title='404 Not Found', message="404 Not Found",
                           message4='The requested URL was not found on the server. If you entered the URL manually please check your spelling and try again.',
                           ), 404

@app.errorhandler(403)
async def page_forbidden(_):
    log(request.remote_addr, f'{request.full_path} -> 403', log_type='ip')
    await simulate()
    return render_template('base/error.html', message="403 Forbidden", message4='You do not have permission.',
                           title='403 Forbidden'), 403

@app.errorhandler(400)
async def bad_request(_):
    log(request.remote_addr, f'{request.full_path} -> 400', log_type='ip')
    await simulate()
    return render_template('base/error.html', message="400 Bad Request", title='400 Bad Request',
                           message4='The server could not understand the request due to invalid syntax.'
                           ), 400

@app.errorhandler(500)
async def internal_server_error(_):
    log(request.remote_addr, f'{request.full_path} -> 500', log_type='ip')
    await simulate()
    return render_template('base/error.html', message="500 Internal Server Error",
                           message4='The server encountered an internal error and was unable to complete your request.',
                           title='500 Internal Server Error'), 500

# -------------------------------------------------- Main --------------------------------------------------------------

def main():
    # get_guilds()
    # app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 5420)))
    print('Running')

    debug = os.environ.get('DEBUG', True)
    debug = True if debug == 'true' or debug is True else False
    port = int(os.environ.get('PORT', 5000))
    host = os.environ.get('HOST', '127.0.0.1')

    simulation = 0
    os.environ['SIMULATE'] = str(simulation)

    print('DEBUG:', debug)
    print('PORT:', port)
    print('HOST:', host)

    # print('type DEBUG:', type(debug))
    # print('type PORT:', type(port))
    # print('type HOST:', type(host))

    # socketio.run(app=app,
    #              log_output=True,
    #              use_reloader=debug,
    #              debug=debug,
    #              port=port,
    #              host=host,
    #              allow_unsafe_werkzeug=True,
    #              )

    app.run(debug=debug, host=host, port=port, use_reloader=debug)

if __name__ == '__main__':
    main()
