from flask import Flask, render_template, redirect, url_for, request, jsonify
import requests
from jinja2 import Environment, FileSystemLoader, meta
from flask_bootstrap import Bootstrap
import yaml, json
from datetime import datetime
from flask_socketio import SocketIO
import os
import redis
import time
import logging
import fnmatch
from logging.handlers import RotatingFileHandler
from zipfile import ZipFile
import subprocess
from flask_apscheduler import APScheduler

# Needed for SocketIO to actually work...
import eventlet
eventlet.monkey_patch()

app = Flask(__name__)
app.config['secret'] = 's;ldi3r#$R@lkjedf$'
app.config['slax_host'] = '10.0.0.204'
bootstrap = Bootstrap(app)
scheduler = APScheduler()
scheduler.init_app(app)
scheduler.start()
socketio = SocketIO(app)


if not os.path.exists('logs'):
    os.mkdir('logs')
file_handler = RotatingFileHandler('logs/event.log', maxBytes=10240, backupCount=10)
file_handler.setFormatter(logging.Formatter(
    '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'))
file_handler.setLevel(logging.INFO)
app.logger.addHandler(file_handler)
app.logger.setLevel(logging.INFO)
app.logger.info('Startup...')


REDIS_URI = os.environ.get('REDIS_URI')

if not REDIS_URI:
    REDIS_URI = '127.0.0.1'

r = redis.Redis(host=REDIS_URI, port=6379, db=0)

def current_time():
    current_time = str(datetime.now().time())
    no_sec = current_time.split('.')
    time = no_sec.pop(0)
    return time

@app.route('/pillar', methods=['GET', 'POST'])
def pillar():
    return render_template('pillar.html', title='Pillar')

@app.route('/', methods=['GET', 'POST'])
@app.route('/index', methods=['GET', 'POST'])
# @login_required
def index():
    return redirect(url_for('hub'))

@socketio.on('connect')
def connect():
    print('Client connected!')

@socketio.on('disconnect')
def disconnect():
    print('Client disconnected')

@socketio.on('nebula_create')
def socket_event(data):
    # print(f'Flask received: {data}')
    #stream = os.popen(f'./nebula/nebula-cert ca -name "{data["name"]}"')
    name = str(data["name"])
    command = f'.\cert.exe ca -name "{name}" -out-crt "certs\{name}.crt" -out-key "certs\{name}.key"'
    output = subprocess.run(command)

    if output.returncode == 1:
        data['error'] = 'ERROR'
        socketio.emit('return', data)
        return

    with open(f'certs\{name}.crt') as crt_f:
         data["crt"] = crt_f.read()

    with open(f'certs\{name}.key') as key_f:
         data["key"] = key_f.read()
    '''
    with ZipFile(f'{name}.zip', 'w') as myzip:
        myzip.write(f'{name}.crt')
        myzip.write(f'{name}.key')
    '''
    socketio.emit('return', data)

if __name__ == '__main__':
    socketio.run(app, host="0.0.0.0", port=80, debug=True)
