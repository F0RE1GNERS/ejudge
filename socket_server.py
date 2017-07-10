#!/usr/bin/env python3

import asyncio
import json
import traceback
from multiprocessing import Pool, Pipe
from os import path

import websockets
import yaml

from config.config import PROJECT_BASE, COMPILE_MAX_TIME_FOR_TRUSTED
from core.case import Case
from core.judge import TrustedSubmission
from handler import judge_handler

json.encoder.FLOAT_REPR = lambda o: format(o, '.3f')  # MONKEY PATCH


def check_auth(username, password):
    token_name = path.join(PROJECT_BASE, 'config/token.yaml')
    with open(token_name) as token_fs:
        tokens = yaml.load(token_fs.read())
    return username == tokens['username'] and password == tokens['password']


async def save_file(websocket, file_path, length):
    # NOTE: this function does not verify the reliability of the file
    accumulate = 0
    with open(file_path, 'wb') as f:
        while True:
            data = await websocket.recv()
            accumulate += len(data)
            f.write(data)
            if accumulate >= length:
                break


async def send_file(websocket, file_path):
    pass


def quick_json_response(received, message=''):
    assert isinstance(message, str)
    return json.dumps({'status': 'received' if received else 'reject', 'message': message})


async def router(websocket, routepath):

    try:

        username = websocket.request_headers.get('username')
        password = websocket.request_headers.get('password')
        if not check_auth(username, password):
            raise Exception('Authorization failed. Goodbye...')

        if routepath == '/upload/case':
            subcase = websocket.request_headers.get('subcase')
            fingerprint = websocket.request_headers.get('fingerprint')
            length = int(websocket.request_headers.get('length'))
            assert subcase == 'in' or subcase == 'out'
            assert isinstance(fingerprint, str)
            case = Case(fingerprint)
            if subcase == 'in':
                file_path = case.input_file
            else:
                file_path = case.output_file
            await save_file(websocket, file_path, length)
            if path.getsize(file_path) != length:
                raise Exception('File transfer fails.')
            await websocket.send(quick_json_response(True))

        elif routepath.startswith('/upload/') and routepath[8:] in ['generator', 'validator', 'interactor', 'checker']:
            data = await websocket.recv()
            data = json.loads(data)
            program = TrustedSubmission(data['fingerprint'], data['code'], data['lang'], permanent=True)
            program.compile(COMPILE_MAX_TIME_FOR_TRUSTED)

        elif routepath == '/judge':
            data = await websocket.recv()
            data = json.loads(data)
            print(data)
            receiver, sender = Pipe(False)

            p = pool.apply_async(judge_handler, args=(data['fingerprint'], data['lang'], data['code'], data['cases'],
                                                      data['max_time'], data['max_memory'], data['checker']),
                                 kwds=dict(interactor_fingerprint=data.get('interactor'),
                                           run_until_complete=data.get('run_until_complete', False),
                                           pipe=sender))
            sender.close()
            while True:
                try:
                    dict_msg = receiver.recv()
                    print(dict_msg)
                    await websocket.send(json.dumps(dict_msg))
                except EOFError:
                    print('EOF error captured')
                    break
            final_msg = p.get()
            await websocket.send(json.dumps(final_msg))
            # res = judge_handler(data['fingerprint'], data['lang'], data['code'], data['cases'],
            #                     data['max_time'], data['max_memory'], not data['checker'],
            #                     interactor_fingerprint=data.get('interactor'),
            #                     run_until_complete=data.get('run_until_complete', False),
            #                     )
            # await websocket.send(json.dumps(res))


        else:
            raise Exception('Authorization granted. Goodbye...')

    except Exception as e:
        traceback.print_exc()
        await websocket.send(quick_json_response(False, str(e)))


if __name__ == '__main__':
    pool = Pool(2)
    start_server = websockets.serve(router, '0.0.0.0', 5001)

    asyncio.get_event_loop().run_until_complete(start_server)
    asyncio.get_event_loop().run_forever()