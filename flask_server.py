#!/usr/bin/env python3

from functools import wraps
from flask import Flask, render_template, request, Response, jsonify, copy_current_request_context
from flask_socketio import emit
import yaml
import json
import logging

from core.case import Case
from core.judge import TrustedSubmission
from config.config import COMPILE_MAX_TIME_FOR_TRUSTED, TOKEN_FILE, custom_config
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
    data = json.loads(request.get_json())
    program = TrustedSubmission(data['fingerprint'], data['code'], data['lang'], permanent=True)
    if program.to_compile:
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
    data = json.loads(request.get_json())
    p = generate_handler.apply_async((data['fingerprint'], data['code'], data['lang'],
                                      data['max_time'], data['max_memory'], data['command_line_args']),
                                     {'multiple': data.get("multiple", False)})
    return jsonify(p.get())


@flask_app.route('/validate', methods=['POST'])
@auth_required
@with_traceback_on_err
def validate():
    data = json.loads(request.get_json())
    p = validate_handler.apply_async((data['fingerprint'], data['code'], data['lang'],
                                      data['max_time'], data['max_memory'], data['input']),
                                     {'multiple': data.get("multiple", False)})
    return jsonify(p.get())


@flask_app.route('/stress', methods=['POST'])
@auth_required
@with_traceback_on_err
def stress():
    data = json.loads(request.get_json())
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
    data = json.loads(request.get_json())
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

    data = json.loads(request.get_json())
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
