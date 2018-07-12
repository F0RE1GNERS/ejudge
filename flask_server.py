#!/usr/bin/env python3

import logging
import json
import time
import threading
from functools import wraps
from os import path

import yaml
from flask import request, Response, jsonify

from config.config import COMPILE_MAX_TIME_FOR_TRUSTED, TOKEN_FILE, CUSTOM_FILE, Verdict
from core.case import Case
from core.judge import TrustedSubmission
from handler import flask_app, judge_handler
from handler import reject_with_traceback, cache


@flask_app.route('/ping')
def ping():
    return Response("pong")


def check_auth(username, password):
    with open(TOKEN_FILE) as token_fs:
        tokens = yaml.load(token_fs.read())
    return username == tokens['username'] and password == tokens['password']


def authorization_failed():
    return jsonify({'status': 'reject', 'message': 'authorization failed'})


def auth_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or not check_auth(auth.username, auth.password):
            return authorization_failed()
        return f(*args, **kwargs)
    return decorated


def response_ok(**kwargs):
    kwargs.update(status='received')
    return jsonify(kwargs)


def with_traceback_on_err(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except:
            return jsonify(reject_with_traceback())

    return decorated


@flask_app.route('/config/token', methods=['POST'])
@auth_required
@with_traceback_on_err
def update_token():
    data = request.get_json()
    with open(TOKEN_FILE) as token_fs:
        tokens = yaml.load(token_fs.read())
    tokens['password'] = data['token']
    with open(TOKEN_FILE, 'w') as token_fs:
        yaml.dump(tokens, token_fs, default_flow_style=False)
    return response_ok()


@flask_app.route('/config/custom', methods=['GET', 'POST'])
@auth_required
@with_traceback_on_err
def trace_custom_config():
    if request.method == 'GET':
        with open(CUSTOM_FILE) as fs:
            return fs.read()
    else:
        with open(CUSTOM_FILE, 'wb') as fs:
            fs.write(request.data)
        return response_ok()


@flask_app.route('/exist/case/<fid>')
def case_exist(fid):
    case = Case(fid)
    return jsonify({'exist': path.exists(case.input_file) and path.exists(case.output_file)})


@flask_app.route('/upload/case/<fid>/<io>', methods=['POST'])
@auth_required
@with_traceback_on_err
def upload_case(fid, io):
    """
    You need to do something like /upload/case/f3758/input and bind binary data to request.data
    """
    case = Case(fid)
    if io == 'input':
        case.write_input_binary(request.data)
    elif io == 'output':
        case.write_output_binary(request.data)
    return response_ok()



@flask_app.route('/upload/checker', methods=['POST'])
@flask_app.route('/upload/interactor', methods=['POST'])
@flask_app.route('/upload/generator', methods=['POST'])
@flask_app.route('/upload/validator', methods=['POST'])
@auth_required
@with_traceback_on_err
def upload_trusted_submission():
    data = request.get_json()
    program = TrustedSubmission(data['fingerprint'], data['code'], data['lang'], permanent=True)
    if data.get('force') or program.to_compile:
        program.compile(COMPILE_MAX_TIME_FOR_TRUSTED)
    return response_ok()


@flask_app.route('/delete/case/<fid>', methods=['DELETE'])
@auth_required
@with_traceback_on_err
def delete_case(fid):
    case = Case(fid)
    case.clean()
    return response_ok()


@flask_app.route('/delete/checker/<fid>', methods=['DELETE'])
@flask_app.route('/delete/interactor/<fid>', methods=['DELETE'])
@flask_app.route('/delete/generator/<fid>', methods=['DELETE'])
@flask_app.route('/delete/validator/<fid>', methods=['DELETE'])
@auth_required
@with_traceback_on_err
def delete_trusted_submission(fid):
    """This api is not recommended to use"""
    program = TrustedSubmission.fromExistingFingerprint(fid)
    program.clean(True)
    return response_ok()


@flask_app.route('/judge', methods=['POST'])
@auth_required
@with_traceback_on_err
def judge():
    data = request.get_json()
    hold = data.get('hold', True)
    fingerprint = data['fingerprint']

    cache.set(fingerprint, {'verdict': Verdict.WAITING.value}, timeout=3600)
    p = judge_handler(fingerprint, data['code'], data['lang'], data['cases'],
                      data['max_time'], data['max_memory'],
                      checker_fingerprint=data.get('checker', ''),
                      interactor_fingerprint=data.get('interactor'),
                      run_until_complete=data.get('run_until_complete', False),
                      group_list=data.get('group_list'),
                      group_dependencies=data.get('group_dependencies'))
    if hold:
        return jsonify(p.get())
    else:
        threading.Thread(target=p.get).start()
        return response_ok()


@flask_app.route('/query', methods=['GET'])
@auth_required
@with_traceback_on_err
def query():
    data = request.get_json()
    fingerprint = data['fingerprint']
    status = cache.get(fingerprint)
    status.setdefault('status', 'received')
    return jsonify(status)


@flask_app.route('/query/report', methods=['GET'])
@auth_required
@with_traceback_on_err
def query_result():
    data = request.get_json()
    fingerprint = data.get('fingerprint', '')
    status = cache.get('report_%s' % fingerprint)
    if status is None:
        status = ''
    return status


if __name__ == '__main__':
    flask_app.run(host='0.0.0.0', port=5000)
