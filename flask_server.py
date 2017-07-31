#!/usr/bin/env python3

import logging
from functools import wraps
from os import path

import yaml
from flask import request, Response, jsonify, copy_current_request_context
from flask_socketio import emit

from config.config import COMPILE_MAX_TIME_FOR_TRUSTED, TOKEN_FILE, CUSTOM_FILE
from core.case import Case
from core.judge import TrustedSubmission
from handler import flask_app, socketio, judge_handler, judge_handler_one, generate_handler, validate_handler
from handler import reject_with_traceback, stress_handler


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


def response_ok():
    return jsonify({'status': 'received'})


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


@flask_app.route('/generate', methods=['POST'])
@auth_required
@with_traceback_on_err
def generate():
    data = request.get_json()
    p = generate_handler.apply_async((data['fingerprint'], data['code'], data['lang'],
                                      data['max_time'], data['max_memory'], data['command_line_args']),
                                     {'multiple': data.get("multiple", False)})
    return jsonify(p.get())


@flask_app.route('/validate', methods=['POST'])
@auth_required
@with_traceback_on_err
def validate():
    data = request.get_json()
    p = validate_handler.apply_async((data['fingerprint'], data['code'], data['lang'],
                                      data['max_time'], data['max_memory'], data['input']),
                                     {'multiple': data.get("multiple", False)})
    return jsonify(p.get())


@flask_app.route('/stress', methods=['POST'])
@auth_required
@with_traceback_on_err
def stress():
    data = request.get_json()
    if len(data['command_line_args_list']) < 1:
        raise ValueError("Must have at least one command line argument")
    args = (data.pop('std'), data.pop('submission'), data.pop('generator'), data.pop('command_line_args_list'),
            data.pop('max_time'), data.pop('max_memory'), data.pop('max_sum_time'), data.pop('checker'))
    if data.get('interactor'):
        data['interactor_dict'] = data.pop('interactor')
    p = stress_handler.apply_async(args, data)
    return jsonify(p.get())


@flask_app.route('/judge/<target>', methods=['POST'])
@auth_required
@with_traceback_on_err
def judge_one(target):
    data = request.get_json()
    args = (data.pop('submission'), data.pop('max_time'), data.pop('max_memory'), data.pop('input'))
    data['target'] = target
    if data.get('output'):
        data['case_output_b64'] = data.pop('output')
    if data.get('checker'):
        data['checker_dict'] = data.pop('checker')
    if data.get('interactor'):
        data['interactor_dict'] = data.pop('interactor')
    p = judge_handler_one.apply_async(args, data)
    return jsonify(p.get())


@flask_app.route('/judge', methods=['POST'])
@auth_required
@with_traceback_on_err
def judge():
    """This is the http version of judge, used in retry"""
    def on_raw_message(body):
        logging.info(body)

    data = request.get_json()
    p = judge_handler.apply_async((data['fingerprint'], data['code'], data['lang'], data['cases'],
                                   data['max_time'], data['max_memory'], data['checker']),
                                  {'interactor_fingerprint': data.get('interactor'),
                                   'run_until_complete': data.get('run_until_complete', False), })
    return jsonify(p.get(on_message=on_raw_message))


@socketio.on('judge')
def handle_message(data):

    @copy_current_request_context
    def on_raw_message(body):
        emit('judge_reply', body['result'])

    if not check_auth(data.get('username'), data.get('password')):
        return authorization_failed()
    p = judge_handler.apply_async((data['fingerprint'], data['code'], data['lang'], data['cases'],
                                   data['max_time'], data['max_memory'], data['checker']),
                                  {'interactor_fingerprint': data.get('interactor'),
                                   'run_until_complete': data.get('run_until_complete', False), })
    return jsonify(p.get(on_message=on_raw_message))


if __name__ == '__main__':
    socketio.run(flask_app, host='0.0.0.0', port=5000)
