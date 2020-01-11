import app_secrets
from flask import Flask, render_template, redirect, url_for, request, jsonify, g, session
from flask_bootstrap import Bootstrap
from flask_socketio import SocketIO
import yaml
import json
import os
import time
import logging
import subprocess
from datetime import datetime
from logging.handlers import RotatingFileHandler
from zipfile import ZipFile
from pprint import pprint
import secrets

from flask_github import GitHub
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.ext.declarative import declarative_base

import requests
import sqlite3
from flask_login import (
    LoginManager,
    current_user,
    login_required,
    login_user,
    logout_user,
)

# Needed for SocketIO to work
import eventlet
eventlet.monkey_patch()

# Gather secrets
github_secret = secrets.token_urlsafe(40)
flask_secret = secrets.token_urlsafe(40)

# Build the app
app = Flask(__name__)
app.config['secret'] = flask_secret
app.config['GITHUB_CLIENT_ID'] = app_secrets.GITHUB_CLIENT_ID
app.config['GITHUB_CLIENT_SECRET'] = app_secrets.GITHUB_CLIENT_SECRET
app.config['SECRET_KEY'] = github_secret
bootstrap = Bootstrap(app)
github = GitHub(app)
socketio = SocketIO(app)

# Configure logging
if not os.path.exists('logs'):
    os.mkdir('logs')
file_handler = RotatingFileHandler(
    'logs/event.log',
    maxBytes=10240,
    backupCount=10)
file_handler.setFormatter(logging.Formatter(
    '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'))
file_handler.setLevel(logging.INFO)
app.logger.addHandler(file_handler)
app.logger.setLevel(logging.INFO)
app.logger.info('Startup...')

# setup sqlalchemy
engine = create_engine('sqlite:////tmp/github-flask.db')
db_session = scoped_session(sessionmaker(autocommit=False,
                                         autoflush=False,
                                         bind=engine))
Base = declarative_base()
Base.query = db_session.query_property()


def init_db():
    print('creating DB...')
    Base.metadata.create_all(bind=engine)


class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    github_access_token = Column(String(255))
    github_id = Column(Integer)
    github_login = Column(String(255))

    def __init__(self, github_access_token):
        self.github_access_token = github_access_token


# Custom functions for the app
def current_time():
    current_time = str(datetime.now().time())
    no_sec = current_time.split('.')
    time = no_sec.pop(0)
    return time


def get_nebulas():
    nebulas = []
    for root, dirs, files in os.walk(r'certs/ca'):
        for file in files:
            if file.endswith('.crt'):
                split = file.split(".")
                file = split.pop(0)
                nebulas.append(f'{file}')
    print(nebulas)
    return nebulas

def get_nebula_endpoints():
    nebulas = []
    for root, dirs, files in os.walk(r'certs/ca'):
        for file in files:
            if file.endswith('.crt'):
                split = file.split(".")
                file = split.pop(0)
                nebulas.append(f'{file}')
    print(nebulas)
    return nebulas

# Decorators
@app.before_request
def before_request():
    g.user = None
    if 'user_id' in session:
        g.user = User.query.get(session['user_id'])


@app.after_request
def after_request(response):
    db_session.remove()
    return response


@github.access_token_getter
def token_getter():
    user = g.user
    if user is not None:
        return user.github_access_token


# App routes
@app.route('/github-callback')
@github.authorized_handler
def authorized(access_token):
    print(request)
    next_url = request.args.get('next') or url_for('index')
    if access_token is None:
        return redirect(next_url)

    user = User.query.filter_by(github_access_token=access_token).first()
    if user is None:
        user = User(access_token)
        db_session.add(user)

    user.github_access_token = access_token

    # Not necessary to get these details here
    # but it helps humans to identify users easily.
    g.user = user
    github_user = github.get('/user')
    user.github_id = github_user['id']
    user.github_login = github_user['login']

    db_session.commit()

    session['user_id'] = user.id
    return redirect(next_url)


@app.route('/login')
def login():
    if session.get('user_id', None) is None:
        return github.authorize()
    else:
        print(session['user_id'])
        return redirect(url_for('index'))


@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('index'))


def GitHubAuthRequired(func):
    def authwrapper(*args, **kwargs):
        print(session)
        if g.user:
            print(g.user.github_login)
            return func(*args, **kwargs)
        else:
            print('PLEASE AUTH')
            return github.authorize()
    authwrapper.__name__ = func.__name__
    return authwrapper


@app.route('/user')
@GitHubAuthRequired
def user():
    '''
    Auth Example
    '''
    return jsonify(github.get('/user'))


@app.route('/repo')
@GitHubAuthRequired
def repo():
    '''
    Auth Example
    '''
    return jsonify(github.get('/repos/natemellendorf/pillars'))


@app.route('/', methods=['GET', 'POST'])
@app.route('/index', methods=['GET', 'POST'])
# @login_required
def index():
    return redirect(url_for('create'))


@app.route('/create', methods=['GET', 'POST'])
def create():
    nebulas = get_nebulas()
    return render_template(
        'create.html',
        title='Pillars - Create',
        nebulas=nebulas)

@app.route('/join', methods=['GET', 'POST'])
def join():
    nebulas = get_nebulas()
    return render_template(
        'join.html',
        title='Pillars - Join',
        nebulas=nebulas)

# SocketIO
@socketio.on('connect')
def connect():
    print('Client connected!')


@socketio.on('disconnect')
def disconnect():
    print('Client disconnected')


@socketio.on('nebula_refresh')
def nebula_refresh(data):
    nebulas = get_nebulas()
    socketio.emit('nebula_refresh', nebulas)


@socketio.on('nebula_create')
def socket_event(data):
    name = str(data["data"]["name"])
    command = f'./cert ca -name "{name}" -out-crt "certs/ca/{name}.crt" -out-key "certs/ca/{name}.key"'
    output = subprocess.run(command, capture_output=True, shell=True)

    if output.returncode != 0:
        data['error'] = str(output.stderr)
        socketio.emit('return', data)
        return

    # Read the certificates created - WIP
    # with open(f'certs\ca\{name}.crt') as crt_f:
        #data["crt"] = crt_f.read()

    # with open(f'certs\ca\{name}.key') as key_f:
        #data["key"] = key_f.read()

    socketio.emit('return', data)


@socketio.on('nebula_join')
def nebula_join(data):
    print(f'Flask received: {data}')
    nebula = str(data["data"]["nebula"])
    device_name = str(data["data"]["device_name"])
    device_ip = str(data["data"]["device_ip"])
    device_group = str(data["data"].get("device_group", ''))
    lh_location = str(data["data"].get("lh_location", ''))
    lh_port = str(data["data"].get("lh_port", ''))
    lh_ip = str(data["data"].get("lh_ip", ''))

    if lh_location and lh_port:
        lh = lh_location + ':' + lh_port

    device_ip_no_cidr = device_ip.split('/')
    device_ip_no_cidr = device_ip_no_cidr.pop(0)
    pprint(device_ip_no_cidr)

    # Create certificates for the endpoint
    command = f'./cert sign -name "{device_name}" -ip "{device_ip}" -ca-crt "certs/ca/{nebula}.crt" -ca-key "certs/ca/{nebula}.key" -out-crt "certs/{device_name}.crt" -out-key "certs/{device_name}.key"'
    output = subprocess.run(command, capture_output=True, shell=True)

    # If an error is returned, stop and return the error.
    if output.returncode != 0:
        data['error'] = str(output.stderr)
        print(output)
        socketio.emit('return', data)
        return

    # Read the certificates created - WIP
    # with open(f'certs\{device_name}.crt') as crt_f:
        #data["crt"] = crt_f.read()

    # with open(f'certs\{device_name}.key') as key_f:
        #data["key"] = key_f.read()

    # Create config file for endpoint
    config = 'config.yml'

    with open(config, 'r') as outfile:
        d = yaml.load(outfile, Loader=yaml.SafeLoader)

    # Lighthouse logic
    if lh_ip == device_ip_no_cidr:
        d['lighthouse']['am_lighthouse'] = True
        del d['lighthouse']['hosts']
        d['listen']['host'] = f'0.0.0.0'
        d['listen']['port'] = lh_port
    else:
        d['lighthouse']['am_lighthouse'] = False
        d['lighthouse']['hosts'][0] = f'{lh_ip}'
        d['listen']['host'] = '0.0.0.0'
        d['listen']['port'] = 0

    # Required:
    d['pki']['ca'] = f'{nebula}.crt'
    d['pki']['cert'] = f'{device_name}.crt'
    d['pki']['key'] = f'{device_name}.key'

    newlist = []

    if lh_ip:
        newlist.append(lh)
        d['static_host_map'] = dict()
        d['static_host_map'][f'{lh_ip}'] = ''
        d['static_host_map'][f'{lh_ip}'] = newlist
    else:
        del d['static_host_map']

    # Save the new endpoint config file
    with open(f'configs/{nebula}_{device_name}.yml', 'w') as outfile:
        yaml.dump(d, outfile, default_style='', default_flow_style=False)

    with ZipFile(f'static/zips/{nebula}_{device_name}.zip', 'w') as myzip:
        myzip.write(f'certs/ca/{nebula}.crt', f'{nebula}.crt')
        myzip.write(f'certs/{device_name}.crt', f'{device_name}.crt')
        myzip.write(f'certs/{device_name}.key', f'{device_name}.key')
        myzip.write(
            f'configs/{nebula}_{device_name}.yml',
            f'{nebula}_{device_name}.yml')

    data['zip_location'] = f'static/zips/{nebula}_{device_name}.zip'
    data['configFile'] = f'./nebula -config {nebula}_{device_name}.yml'
    socketio.emit('return', data)


# Start the app
if __name__ == '__main__':
    init_db()
    socketio.run(app, host="0.0.0.0", port=80, debug=True)
