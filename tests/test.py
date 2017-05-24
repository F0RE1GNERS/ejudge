from os import path
import requests
import time
import json

TOKEN = 'naive'
URL = 'http://127.0.0.1:4999/'
BASE_DIR = path.dirname(path.abspath(__file__))

PROBLEM_ID = 1
UPLOAD_URL = URL + 'upload/%d' % PROBLEM_ID
JUDGE_URL = URL + 'judge'
LANG_SET = [
    ('.c', 'c'),
    ('.cpp', 'cpp'),
    ('.java', 'java'),
    ('.py', 'python')
]


def judge(data_name, source_name, max_time=1000, max_sum_time=10000, max_memory=256, judge='ncmp'):
    data_name = path.join(BASE_DIR, 'test_data/' + data_name + '.zip')
    source_name = path.join(BASE_DIR, 'test_src/' + source_name)
    lang = None
    for ext, name in LANG_SET:
        if source_name.endswith(ext):
            lang = name
            break
    if not lang:
        raise TypeError('Unrecognized language.')
    with open(source_name) as f:
        code = f.read()

    with open(data_name, 'rb') as f:
        result = requests.post(UPLOAD_URL, data=f.read(), auth=('token', TOKEN)).json()
        print('Uploading result:', result)
        if not result['status'] == 'received':
            raise ConnectionError('Remote server reject the request')
    start_time = time.time()
    data = {
        "id": 1,
        "lang": lang,
        "code": code,
        "settings": {
            "max_time": max_time,
            "max_sum_time": max_sum_time,
            "max_memory": max_memory,
            "problem_id": str(PROBLEM_ID),
        },
        "judge": judge,
    }
    result = requests.post(JUDGE_URL, json=data, auth=('token', TOKEN)).json()
    print('Judge result:', result)
    end_time = time.time()
    print('Time elapsed:', end_time - start_time)
    return result

if __name__ == '__main__':
    # judge('string', 'string_fast.cpp', max_time=3000, max_sum_time=0)
    # judge('a+b', 'a+b_wa.cpp', max_time=3000, max_sum_time=0)
    # judge('a+b', 'a+b_ce.cpp', max_time=3000, max_sum_time=0)
    # judge('a+b', 'a+b.java', max_time=1000)
    res1 = judge('string', 'string_slow.cpp', max_time=3000, max_sum_time=0)
    res2 = judge('string2', 'string_slow.cpp', max_time=3000, max_sum_time=0)
    print(list(filter(lambda x: x.get('count') == 13, res1['detail']))[0], res2['detail'][0])
    # judge('string', 'string_hash.cpp', max_time=6000, max_sum_time=0)
