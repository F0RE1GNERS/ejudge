import uuid
import zipfile
import platform
import shutil
from flask import request, jsonify
from config import *
from core.handler import Handler

try:
    from local_config import HOST, PORT, TOKEN, DEBUG
except ImportError:
    HOST = '127.0.0.1'
    PORT = 4999
    TOKEN = 'naive'
    DEBUG = True


def verify_token(data):
    try:
        if data.get('username') == 'token' and data.get('password') == TOKEN:
            return True
        return False
    except KeyError:
        return False


@app.route('/upload/<pid>', methods=['POST'])
def server_upload(pid):
    result = {'status': 'reject'}
    try:
        if verify_token(request.authorization):
            target_dir = os.path.join(DATA_DIR, pid)
            if os.path.exists(target_dir):
                shutil.rmtree(target_dir)
            os.mkdir(target_dir)
            source_path = os.path.join(TMP_DIR, str(uuid.uuid1()) + '.zip')
            with open(source_path, 'wb') as f:
                f.write(request.data)
            source_zip = zipfile.ZipFile(source_path)
            source_zip.extractall(target_dir)
            source_zip.close()
            result['status'] = 'received'
            os.remove(source_path)
    except Exception as e:
        print(e)
    return jsonify(result)


@app.route('/judge', methods=['POST'])
def server_judge():
    result = {'status': 'reject'}
    # TODO: return immediately
    if request.is_json:
        try:
            if verify_token(request.authorization):
                result.update(Handler(request.get_json()).run())
                result['status'] = 'received'
        except Exception as e:
            print(e)
    return jsonify(result)


@app.route('/info', methods=['GET'])
def server_info():
    result = {'status': 'received', 'error': 'not responding'}

    try:
        # System Information
        result['system'] = ', '.join(platform.uname())

        cpu_info = []
        with open('/proc/cpuinfo') as f:
            for line in f:
                if line.strip():
                    if line.rstrip('\n').startswith('model name'):
                        model_name = line.rstrip('\n').split(':')[1]
                        cpu_info.append(model_name.strip())
        result['cpu'] = ', '.join(cpu_info)

        mem_info = []
        with open('/proc/meminfo') as f:
            for line in f:
                if line.strip():
                    if line.rstrip('\n').startswith('MemTotal'):
                        mem_total = line.rstrip('\n').split(':')[1]
                        mem_info.append(mem_total.strip())
        result['memory'] = ', '.join(mem_info)

        result['cpp'] = os.popen('g++ --version').readline().strip()

        result['java'] = ''
        java_info_path = os.path.join(TMP_DIR, str(uuid.uuid1()))
        if os.system('java -version 2> ' + java_info_path) == 0:
            with open(java_info_path, 'r') as f:
                java_info = []
                for line in f:
                    if line.strip():
                        java_info.append(line.strip())
                result['java'] = ', '.join(java_info)

        result['python'] = os.popen('python3 --version').readline().strip()

        if len(os.popen('ps aux | grep redis | grep -v grep').readlines()) == 0:
            raise Exception('Redis is not running')
        if len(os.popen('ps aux | grep celery | grep -v grep').readlines()) == 0:
            raise Exception('Celery is not running')

        result['status'] = 'ok'
        result['error'] = ''
    except Exception as e:
        result['status'] = 'failure'
        result['error'] = str(e)
    return jsonify(result)


if __name__ == '__main__':
    app.run(host=HOST, port=PORT, debug=DEBUG)
