# coding=utf-8
import shutil
from os import sys, path
import requests
import json
from requests.auth import HTTPBasicAuth
import unittest
import zipfile

sys.path.append(path.dirname(path.dirname(path.abspath(__file__))))

JSON_BASE_DICT = {"headers": {"Content-Type": "application/json",
                              'User-Agent': 'Mozilla/5.0 (Windows NT 6.0; WOW64; rv:24.0) Gecko/20100101 Firefox/24.0'}}
SIMPLE_HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.0; WOW64; rv:24.0) Gecko/20100101 Firefox/24.0'}
LOCAL_URL = 'http://127.0.0.1:4999'
URL = LOCAL_URL
TOKEN = 'naive'


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

    def test_judge_a_plus_b(self):
        data = self.formatSubmissionJSON(300, 'cpp', 'a_plus_b/a_plus_b_c_ok')
        data.update({'settings': dict(max_time=1000, max_sum_time=10000, max_memory=256, problem_id=1000),
                     'judge': 'ncmp'})
        res = self.send_judge(data)
        print(res)


    # A * B Problem Test

    # def test_judge_a_mul_b_cpp(self):
    #     data = dict(
    #         submissions=[
    #             self.formatSubmissionJSON(100, 'cpp', 'a_mul_b/a_mul_b_c_int'),
    #             self.formatSubmissionJSON(101, 'cpp', 'a_mul_b/a_mul_b_c_long')
    #         ],
    #         judge=self.formatSubmissionJSON(200, 'cpp', 'a_mul_b/a_mul_b_c_judge'),
    #         config={'problem_id': 1001}
    #     )
    #     res = self.send_judge(data)
    #     self.assertEqual(res['code'], FINISHED, 'Judge Failed for REASON: %s; JSON: %s'
    #                      % (ERROR_CODE[res['code']], json.dumps(res)))
    #
    # def test_judge_a_mul_b_python(self):
    #     data = dict(
    #         submissions=[
    #             self.formatSubmissionJSON(100, 'cpp', 'a_mul_b/a_mul_b_c_int'),
    #             self.formatSubmissionJSON(101, 'cpp', 'a_mul_b/a_mul_b_c_long')
    #         ],
    #         judge=self.formatSubmissionJSON(201, 'python', 'a_mul_b/a_mul_b_p_judge'),
    #         config={'problem_id': 1001}
    #     )
    #     res = self.send_judge(data)
    #     self.assertEqual(res['code'], FINISHED, 'Judge Failed for REASON: %s; JSON: %s'
    #                      % (ERROR_CODE[res['code']], json.dumps(res)))
    #
    # def test_pretest_a_mul_b(self):
    #     data = dict(
    #         submission=self.formatSubmissionJSON(100, 'cpp', 'a_mul_b/a_mul_b_c_int'),
    #         judge=self.formatSubmissionJSON(201, 'python', 'a_mul_b/a_mul_b_p_judge'),
    #         config={'problem_id': 1001}
    #     )
    #     res = self.send_pretest(data)
    #     self.assertEqual(res['code'], PRETEST_PASSED, 'Pretest Failed for REASON: %s; JSON: %s'
    #                      % (ERROR_CODE[res['code']], json.dumps(res)))
    #
    # # Language Test
    #
    # def test_language_cpp(self):
    #     data = dict(
    #         submission={'id': 2000, 'lang': 'cpp', 'code': open('test_src/language/c.cpp').read()},
    #         config={'problem_id': 1001}
    #     )
    #     res = self.send_pretest(data)
    #     self.assertEqual(res['code'], PRETEST_PASSED, 'Pretest Failed for REASON: %s; JSON: %s'
    #                      % (ERROR_CODE[res['code']], json.dumps(res)))
    #
    # def test_language_java(self):
    #     data = dict(
    #         submission={'id': 2001, 'lang': 'java', 'code': open('test_src/language/Main.java').read()},
    #         config={'problem_id': 1001}
    #     )
    #     res = self.send_pretest(data)
    #     self.assertEqual(res['code'], PRETEST_PASSED, 'Pretest Failed for REASON: %s; JSON: %s'
    #                      % (ERROR_CODE[res['code']], json.dumps(res)))
    #
    # def test_language_python(self):
    #     data = dict(
    #         submission={'id': 2002, 'lang': 'python', 'code': open('test_src/language/p.py').read()},
    #         config={'problem_id': 1001}
    #     )
    #     res = self.send_pretest(data)
    #     self.assertEqual(res['code'], PRETEST_PASSED, 'Pretest Failed for REASON: %s; JSON: %s'
    #                      % (ERROR_CODE[res['code']], json.dumps(res)))
    #
    # # A + B Problem Test
    #
    # def test_judge_a_plus_b_ac(self):
    #     data = dict(
    #         submissions=[
    #             self.formatSubmissionJSON(300, 'cpp', 'a_plus_b/a_plus_b_c_ok')
    #         ],
    #         judge=dict(lang='builtin', code='testlib/checker/int_ocmp.py'),
    #         config={'problem_id': 1000}
    #     )
    #     res = self.send_judge(data)
    #     self.assertEqual(res['code'], FINISHED, 'Judge Failed for REASON: %s; JSON: %s'
    #                      % (ERROR_CODE[res['code']], json.dumps(res)))
    #
    # def test_judge_a_plus_b_wa(self):
    #     data = dict(
    #         submissions=[
    #             self.formatSubmissionJSON(301, 'cpp', 'a_plus_b/a_plus_b_c_wa')
    #         ],
    #         pretest_judge=dict(lang='builtin', code='testlib/checker/int_ocmp.py'),
    #         judge=dict(lang='builtin', code='testlib/checker/int_ocmp.py'),
    #         config={'problem_id': 1000}
    #     )
    #     res = self.send_judge(data)
    #     self.assertEqual(res['code'], PRETEST_FAILED, 'Judge Failed for REASON: %s; JSON: %s'
    #                      % (ERROR_CODE[res['code']], json.dumps(res)))


if __name__ == '__main__':
    unittest.main()
