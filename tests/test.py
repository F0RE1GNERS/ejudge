# coding=utf-8
import shutil
from os import sys, path
import requests
import json
from requests.auth import HTTPBasicAuth
import unittest
import zipfile
from config import *

sys.path.append(path.dirname(path.dirname(path.abspath(__file__))))

JSON_BASE_DICT = {"headers": {"Content-Type": "application/json",
                              'User-Agent': 'Mozilla/5.0 (Windows NT 6.0; WOW64; rv:24.0) Gecko/20100101 Firefox/24.0'}}
SIMPLE_HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.0; WOW64; rv:24.0) Gecko/20100101 Firefox/24.0'}
LOCAL_URL = 'http://127.0.0.1:4999'
URL = LOCAL_URL
TOKEN = 'elephant'


class WebserverTest(unittest.TestCase):

    @staticmethod
    def send_judge(data):
        kwargs = JSON_BASE_DICT.copy()
        kwargs["data"] = json.dumps(data)
        url = URL + '/judge'
        res = requests.post(url, json=data, auth=('token', TOKEN)).json()
        print(json.dumps(res))
        return res

    @staticmethod
    def formatSubmissionJSON(submission_id=0, lang='cpp', code_path=''):
        if '.' not in code_path:
            if lang == 'cpp':
                code_path += '.cpp'
            elif lang == 'python':
                code_path += '.py'
            elif lang == 'java':
                code_path += '.java'
        return {"id": submission_id, "lang": lang, "code": open('test_src/' + code_path, "r").read()}

    @staticmethod
    def add_listdir_to_file(source_dir, target_path):
        import zipfile
        f = zipfile.ZipFile(target_path, 'w', zipfile.ZIP_DEFLATED)
        for filename in os.listdir(source_dir):
            real_path = os.path.join(source_dir, filename)
            if os.path.isfile(real_path):
                f.write(real_path, arcname=filename)
        f.close()

    @staticmethod
    def upload(id):
        url = URL + '/upload/%d' % id
        WebserverTest.add_listdir_to_file('test_data/data/%d' % id, 'test_data/upload.zip')
        with open('test_data/upload.zip', 'rb') as f:
            res = requests.post(url, data=f.read(), auth=('token', TOKEN), headers=SIMPLE_HEADERS).json()
        print(json.dumps(res))

    def test_judge_a_plus_b(self):
        data = self.formatSubmissionJSON(300, 'cpp', 'a_plus_b/a_plus_b_c_ok')
        data.update({'settings': dict(max_time=1000, max_sum_time=10000, max_memory=256, problem_id=1000),
                     'judge': 'ncmp'})
        res = self.send_judge(data)
        self.assertEqual(res['verdict'], ACCEPTED)

    def test_judge_a_plus_b_wa(self):
        data = self.formatSubmissionJSON(301, 'cpp', 'a_plus_b/a_plus_b_c_wa')
        data.update({'settings': dict(max_time=1000, max_sum_time=10000, max_memory=256, problem_id=1000),
                     'judge': 'ncmp'})
        res = self.send_judge(data)
        self.assertEqual(res['verdict'], WRONG_ANSWER)

    def test_judge_a_plus_b_ce(self):
        data = self.formatSubmissionJSON(302, 'cpp', 'a_plus_b/a_plus_b_c_ce')
        data.update({'settings': dict(max_time=1000, max_sum_time=10000, max_memory=256, problem_id=1000),
                     'judge': 'ncmp'})
        res = self.send_judge(data)
        self.assertEqual(res['verdict'], COMPILE_ERROR)

    def test_judge_a_plus_b_java(self):
        data = self.formatSubmissionJSON(303, 'java', 'a_plus_b/a_plus_b')
        data.update({'settings': dict(max_time=1000, max_sum_time=10000, max_memory=256, problem_id=1000),
                     'judge': 'ncmp'})
        res = self.send_judge(data)
        self.assertEqual(res['verdict'], ACCEPTED)

    def test_judge_a_plus_b_py(self):
        data = self.formatSubmissionJSON(304, 'python', 'a_plus_b/a_plus_b')
        data.update({'settings': dict(max_time=1000, max_sum_time=10000, max_memory=256, problem_id='1000'),
                     'judge': 'ncmp'})
        res = self.send_judge(data)
        self.assertEqual(res['verdict'], ACCEPTED)

    def test_upload_data(self):
        self.upload(1001)
        self.upload(1002)

    def test_judge_nothing(self):
        data = self.formatSubmissionJSON(304, 'python', 'a_plus_b/a_plus_b')
        data.update({'settings': dict(max_time=1000, max_sum_time=10000, max_memory=256, problem_id='1000-aaa'),
                     'judge': 'ncmp'})
        res = self.send_judge(data)
        self.assertEqual(res['status'], "reject")

if __name__ == '__main__':
    unittest.main()
