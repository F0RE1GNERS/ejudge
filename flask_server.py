#!/usr/bin/env python3
import os
import threading
from functools import wraps

import yaml
from flask import request, Response, jsonify, Flask

from config.config import TOKEN_FILE, Verdict, SPJ_BASE
from core.case import Case
from core.judge import SpecialJudge
from handler import judge_handler
from handler import reject_with_traceback, cache

flask_app = Flask(__name__)


@flask_app.route('/ping')
def ping():
  return Response("pong")


def check_auth(username, password):
  with open(TOKEN_FILE) as token_fs:
    tokens = yaml.safe_load(token_fs.read())
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


@flask_app.route('/upload/case/<fid>/<io>', methods=['POST'])
@auth_required
@with_traceback_on_err
def upload_case(fid, io):
  """
  This API is only used for testing purposes, and is likely to fail in production
  You need to do something like /upload/case/f3758/input and bind binary data to request.data
  """
  case = Case(fid)
  if io == 'input':
    case.write_input_binary(request.data)
  elif io == 'output':
    case.write_output_binary(request.data)
  return response_ok()


@flask_app.route('/upload/spj', methods=['POST'])
@auth_required
@with_traceback_on_err
def upload_spj():
  data = request.get_json()
  program = SpecialJudge(data['lang'], data['fingerprint'])
  program.compile(data['code'], 30)
  return response_ok()


@flask_app.route('/list/spj', methods=['GET'])
@auth_required
@with_traceback_on_err
def list_spj():
  return jsonify({
    "status": "received",
    "spj": list(os.listdir(SPJ_BASE))
  })


@flask_app.route('/judge', methods=['POST'])
@auth_required
@with_traceback_on_err
def judge():
  data = request.get_json()
  hold = data.get('hold', True)
  fingerprint = data['fingerprint']

  cache.set(fingerprint, {'verdict': Verdict.WAITING.value}, timeout=3600)
  args = (fingerprint, data['code'], data['lang'], data['cases'],
          data['max_time'], data['max_memory'],)
  kwargs = dict(checker_fingerprint=data.get('checker', ''),
                interactor_fingerprint=data.get('interactor'),
                run_until_complete=data.get('run_until_complete', False),
                group_list=data.get('group_list'),
                group_dependencies=data.get('group_dependencies'))
  if hold:
    return jsonify(judge_handler(*args, **kwargs))
  else:
    threading.Thread(target=judge_handler, args=args, kwargs=kwargs).start()
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
