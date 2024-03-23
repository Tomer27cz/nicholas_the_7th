from flask import Flask, request, abort
from flask_socketio import SocketIO, join_room
import json
from time import time
import os

app = Flask(__name__)

socketio = SocketIO(app, async_mode='eventlet', cors_allowed_origins='*')

@app.route('/push')
def send_message():
    guild_id = request.args.get('id')
    if guild_id is None:
        return abort(403)

    socketio.emit('update', int(time()), to=guild_id)

    return json.dumps({'success': True}), 200, {'ContentType': 'application/json'}

@socketio.on('getUpdates')
def handle_get_updates(data):
    join_room(data)

if __name__ == '__main__':
    # get_guilds()
    # app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 5420)))
    print('Running')

    debug = os.environ.get('DEBUG', True)
    debug = True if debug == 'true' or debug is True else False
    port = int(os.environ.get('PORT', 5001))
    host = os.environ.get('HOST', '127.0.0.1')

    print('DEBUG:', debug)
    print('type DEBUG:', type(debug))
    print('PORT:', port)
    print('type PORT:', type(port))
    print('HOST:', host)
    print('type HOST:', type(host))

    socketio.run(app=app,
                 log_output=True,
                 use_reloader=debug,
                 debug=debug,
                 port=port,
                 host=host)
