"""
!!! IMPORTANT:
Before running this test, you need to run both flask server and celery
"""

import requests
import json
import logging
import base64
import os
import unittest
import shutil
import sys
import time

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.config import DATA_BASE, Verdict
from core.case import Case
from tests.test_base import TestBase
from config.config import SUB_BASE


class FlaskTest(TestBase):

    def setUp(self):
        self.workspace = '/tmp/flask'
        self.url_base = 'http://localhost:5000'
        self.token = ('ejudge', 'naive') # Token has to be reset to do this test
        super().setUp()

    def test_upload_success(self):
        fingerprint = 'test_%s' % self.rand_str()
        result = requests.post(self.url_base + '/upload/case/%s/input' % fingerprint, data=b'123123',
                               auth=self.token).json()
        self.assertEqual(result['status'], 'received')
        result = requests.post(self.url_base + '/upload/case/%s/output' % fingerprint, data=b'456456',
                               auth=self.token).json()
        self.assertEqual(result['status'], 'received')
        case = Case(fingerprint)
        case.check_validity()
        with open(case.input_file, 'r') as f1:
            self.assertEqual(f1.read(), '123123')
        with open(case.output_file, 'r') as f2:
            self.assertEqual(f2.read(), '456456')

    def test_upload_fail(self):
        fingerprint = 'test_%s' % self.rand_str()
        result = requests.post(self.url_base + '/upload/case/%s/input' % fingerprint, data=b'123123',
                               auth=('123', '345')).json()
        self.assertEqual(result['status'], 'reject')

    def test_delete_case(self):
        fingerprint = 'test_%s' % self.rand_str()
        result = requests.post(self.url_base + '/upload/case/%s/input' % fingerprint, data=b'123123',
                               auth=self.token).json()
        self.assertEqual(result['status'], 'received')
        result = requests.delete(self.url_base + '/delete/case/%s' % fingerprint, data=b'123123',
                                auth=self.token).json()
        self.assertEqual(result['status'], 'received')

    def test_upload_checker_fail(self):
        fingerprint = 'test_%s' % self.rand_str()
        json_data = {'fingerprint': fingerprint, 'code': 'code', 'lang': 'cpp'}
        result = requests.post(self.url_base + '/upload/checker', json=json_data,
                               auth=self.token).json()
        self.assertEqual('reject', result['status'])
        self.assertIn("CompileError", result['message'])

    def test_upload_interactor_with_delete(self):
        fingerprint = 'test_%s' % self.rand_str()
        json_data = {'fingerprint': fingerprint, 'code': self.read_content('./interact/interactor-a-plus-b.cpp', 'r'), 'lang': 'cpp'}
        result = requests.post(self.url_base + '/upload/checker', json=json_data,
                               auth=self.token).json()
        self.assertEqual('received', result['status'])
        self.assertIn(fingerprint, os.listdir(SUB_BASE))
        # without token
        result = requests.delete(self.url_base + '/delete/interactor/' + fingerprint).json()
        self.assertEqual('reject', result['status'])
        # wrong place
        result = requests.delete(self.url_base + '/delete/checker/' + fingerprint).json()
        self.assertEqual('reject', result['status'])
        result = requests.delete(self.url_base + '/delete/interactor/' + fingerprint, auth=self.token).json()
        self.assertEqual('received', result['status'])
        self.assertNotIn(fingerprint, os.listdir(SUB_BASE))

    def test_generate_with_validate(self):
        validator_code = self.read_content('./gen-and-val/bipartite-graph-validator.cpp')
        generator_code = self.read_content('./gen-and-val/gen-bipartite-graph.cpp')
        # 1 <= n, m <= 400, 0 <= k <= n * m
        fingerprint = 'test_%s' % self.rand_str()
        gen_data = {'fingerprint': fingerprint, 'lang': 'cpp', 'code': generator_code, 'max_time': 1, 'max_memory': 256,
                    'command_line_args': ["10", "10", "20"]}
        result = requests.post(self.url_base + '/generate', json=gen_data, auth=self.token).json()
        output_b64 = result['output']
        self.assertEqual(22, len(base64.b64decode(output_b64).decode().split('\n')))
        self.assertNotIn(fingerprint, os.listdir(SUB_BASE))

        val_data = {'fingerprint': fingerprint, 'lang': 'cpp', 'code': validator_code, 'max_time': 1, 'max_memory': 256,
                    'input': output_b64}
        result = requests.post(self.url_base + '/validate', json=val_data, auth=self.token).json()
        self.assertEqual(Verdict.ACCEPTED.value, result['verdict'])

        # multiple
        command_line_args = [["10", "10", "20"]] + [["400", "400", "8000"], ["40", "40", "1500"]]
        gen_data = {'fingerprint': fingerprint, 'lang': 'cpp', 'code': generator_code, 'max_time': 1, 'max_memory': 256,
                    'command_line_args': command_line_args, 'multiple': True}
        result = requests.post(self.url_base + '/generate', json=gen_data, auth=self.token).json()
        output_b64 = result['output']
        self.assertEqual(3, len(output_b64))
        val_data = {'fingerprint': fingerprint, 'lang': 'cpp', 'code': validator_code, 'max_time': 1, 'max_memory': 256,
                    'input': output_b64, 'multiple': True}
        result = requests.post(self.url_base + '/validate', json=val_data, auth=self.token).json()
        for res in result['result']:
            self.assertEqual(Verdict.ACCEPTED.value, res['verdict'])
        val_data = {'fingerprint': fingerprint, 'lang': 'cpp', 'code': validator_code, 'max_time': 1, 'max_memory': 256,
                    'input': output_b64}
        result = requests.post(self.url_base + '/validate', json=val_data, auth=self.token).json()
        self.assertEqual('reject', result['status'])

    def test_generate_fail(self):
        generator_code = self.read_content('./gen-and-val/gen-bipartite-graph.cpp')
        # 1 <= n, m <= 400, 0 <= k <= n * m
        fingerprint = 'test_%s' % self.rand_str()
        gen_data = {'fingerprint': fingerprint, 'lang': 'cpp', 'code': generator_code, 'max_time': 1, 'max_memory': 256,
                    'command_line_args': ["10", "10", "300"]}
        result = requests.post(self.url_base + '/generate', json=gen_data, auth=self.token).json()
        self.assertEqual("reject", result['status'])

    def test_validate_fail(self):
        fingerprint = 'test_%s' % self.rand_str()
        validator_code = self.read_content('./gen-and-val/bipartite-graph-validator.cpp')
        val_data = {'fingerprint': fingerprint, 'lang': 'cpp', 'code': validator_code, 'max_time': 1, 'max_memory': 256,
                    'input': base64.b64encode(b"1 2 3").decode()}
        result = requests.post(self.url_base + '/validate', json=val_data, auth=self.token).json()
        self.assertEqual(Verdict.WRONG_ANSWER.value, result['verdict'])

    def test_stress(self):
        checker_fingerprint, std_fingerprint, sub_fingerprint, gen_fingerprint = \
            self.rand_str(True), self.rand_str(True), self.rand_str(True), self.rand_str(True)
        checker_dict = dict(fingerprint=checker_fingerprint, lang='cpp', code=self.read_content('./submission/ncmp.cpp'))
        std_dict = dict(fingerprint=std_fingerprint, lang='cpp', code=self.read_content('./submission/aplusb.cpp'))
        sub_dict = dict(fingerprint=sub_fingerprint, lang='python', code=self.read_content('./gen-and-val/aplusb-sometimes-wrong.py'))
        gen_dict = dict(fingerprint=gen_fingerprint, lang='python', code=self.read_content('./gen-and-val/aplusb-gen.py'))

        stress_data = dict(std=std_dict, submission=sub_dict, generator=gen_dict, command_line_args_list=[[]],
                           max_time=1, max_memory=128, max_sum_time=20, checker=checker_dict)
        result = requests.post(self.url_base + '/stress', json=stress_data, auth=self.token).json()
        for out in result['output']:
            self.assertTrue(int(base64.b64decode(out).decode().split(' ')[0]) % 2 == 0)

        # correct sub
        sub_dict = dict(fingerprint=sub_fingerprint, lang='java', code=self.read_content('./submission/aplusb.java'))
        stress_data = dict(std=std_dict, submission=sub_dict, generator=gen_dict, command_line_args_list=[[]],
                           max_time=1, max_memory=128, max_sum_time=15, checker=checker_dict)
        result = requests.post(self.url_base + '/stress', json=stress_data, auth=self.token).json()
        self.assertFalse(result['output'])

    def test_stress_interactor(self):
        checker_fingerprint, std_fingerprint, sub_fingerprint, gen_fingerprint, interactor_fingerprint = \
            self.rand_str(True), self.rand_str(True), self.rand_str(True), self.rand_str(True), self.rand_str(True)
        checker_dict = dict(fingerprint=checker_fingerprint, lang='cpp', code=self.read_content('./submission/ncmp.cpp'))
        std_dict = dict(fingerprint=std_fingerprint, lang='cpp', code=self.read_content('./submission/aplusb.cpp'))
        sub_dict = dict(fingerprint=sub_fingerprint, lang='python',
                        code=self.read_content('./gen-and-val/aplusb-sometimes-wrong.py'))
        gen_dict = dict(fingerprint=gen_fingerprint, lang='python', code=self.read_content('./interact/aplusb-gen-one-with-count.py'))
        inter_dict = dict(fingerprint=interactor_fingerprint, lang='cpp',
                          code=self.read_content('./interact/interactor-a-plus-b.cpp'))

        stress_data = dict(std=std_dict, submission=sub_dict, generator=gen_dict, command_line_args_list=[[]],
                           max_time=1, max_memory=128, max_sum_time=20, checker=checker_dict, interactor=inter_dict,
                           max_generate=10)
        result = requests.post(self.url_base + '/stress', json=stress_data, auth=self.token).json()
        self.assertGreaterEqual(10, len(result['output']))

    def test_judge_one(self):
        checker_fingerprint, std_fingerprint = \
            self.rand_str(True), self.rand_str(True)
        input_b64 = base64.b64encode(b'1 2').decode()
        output_b64 = base64.b64encode(b'3').decode()
        sub_dict = dict(fingerprint=std_fingerprint, lang='cpp', code=self.read_content('./submission/aplusb.cpp'))
        checker_dict = dict(fingerprint=checker_fingerprint, lang='cpp', code=self.read_content('./submission/ncmp.cpp'))
        data = dict(submission=sub_dict, max_time=1, max_memory=128, input=input_b64)

        # output
        result = requests.post(self.url_base + '/judge/output', json=data, auth=self.token).json()
        self.assertEqual('3', base64.b64decode(result['output']).decode().strip())

        # sandbox
        result = requests.post(self.url_base + '/judge/sandbox', json=data, auth=self.token).json()
        self.assertEqual(0, result['verdict'])

        # checker
        data.update(checker=checker_dict, output=output_b64)
        result = requests.post(self.url_base + '/judge/checker', json=data, auth=self.token).json()
        self.assertEqual(Verdict.ACCEPTED.value, result['verdict'])
        self.assertEqual("1 number(s): \"3\"", result['message'])

        # result
        result = requests.post(self.url_base + '/judge/checker', json=data, auth=self.token).json()
        self.assertEqual(Verdict.ACCEPTED.value, result['verdict'])

    def test_judge_one_multiple(self):
        checker_fingerprint, std_fingerprint = \
            self.rand_str(True), self.rand_str(True)
        input_b64 = list(map(lambda x: base64.b64encode(x).decode(), [b'1 2', b'3 4']))
        output_b64 = list(map(lambda x: base64.b64encode(x).decode(), [b'3', b'7']))
        sub_dict = dict(fingerprint=std_fingerprint, lang='cpp', code=self.read_content('./submission/aplusb.cpp'))
        checker_dict = dict(fingerprint=checker_fingerprint, lang='cpp', code=self.read_content('./submission/ncmp.cpp'))
        data = dict(submission=sub_dict, max_time=1, max_memory=128, input=input_b64, multiple=True)
        shutil.rmtree(DATA_BASE)
        os.makedirs(DATA_BASE)

        # output
        result = requests.post(self.url_base + '/judge/output', json=data, auth=self.token).json()
        self.assertEqual('7', base64.b64decode(result['result'][1]['output']).decode().strip())

        # sandbox
        result = requests.post(self.url_base + '/judge/sandbox', json=data, auth=self.token).json()
        self.assertEqual(0, result['result'][0]['verdict'])

        # checker
        data.update(checker=checker_dict, output=output_b64)
        result = requests.post(self.url_base + '/judge/checker', json=data, auth=self.token).json()
        self.assertEqual(Verdict.ACCEPTED.value, result['result'][0]['verdict'])
        self.assertEqual("1 number(s): \"7\"", result['result'][1]['message'])

        # result
        result = requests.post(self.url_base + '/judge/checker', json=data, auth=self.token).json()
        self.assertEqual(Verdict.ACCEPTED.value, result['result'][1]['verdict'])

        # make sure it is clean
        self.assertEqual([], list(os.listdir(DATA_BASE)))

        # clean even when something went wrong
        sub_dict = dict(fingerprint=std_fingerprint, lang='cpp', code=self.read_content('./submission/aplusb-ce.c'))
        data = dict(submission=sub_dict, max_time=1, max_memory=128, input=input_b64, multiple=True)
        result = requests.post(self.url_base + '/judge/output', json=data, auth=self.token).json()
        self.assertEqual('reject', result['status'])
        self.assertEqual([], list(os.listdir(DATA_BASE)))

    def test_judge_one_interactor(self):
        checker_fingerprint, std_fingerprint, interactor_fingerprint = \
            self.rand_str(True), self.rand_str(True), self.rand_str(True)
        input_b64 = base64.b64encode(b'1\n1 2').decode()
        output_b64 = base64.b64encode(b'3').decode()
        sub_dict = dict(fingerprint=std_fingerprint, lang='python', code=self.read_content('./interact/a-plus-b.py'))
        checker_dict = dict(fingerprint=checker_fingerprint, lang='cpp', code=self.read_content('./submission/ncmp.cpp'))
        interactor_dict = dict(fingerprint=interactor_fingerprint, lang='cpp', code=self.read_content('./interact/interactor-a-plus-b.cpp'))
        data = dict(submission=sub_dict, max_time=1, max_memory=128, input=input_b64, interactor=interactor_dict)

        # interactor
        result = requests.post(self.url_base + '/judge/interactor', json=data, auth=self.token).json()
        self.assertEqual("1 queries processed", result['message'])

        # checker
        data.update(checker=checker_dict, output=output_b64)
        result = requests.post(self.url_base + '/judge/checker', json=data, auth=self.token).json()
        self.assertEqual(Verdict.ACCEPTED.value, result['verdict'])
        self.assertEqual("1 number(s): \"3\"", result['message'])

        # result
        result = requests.post(self.url_base + '/judge/checker', json=data, auth=self.token).json()
        self.assertEqual(Verdict.ACCEPTED.value, result['verdict'])

    def judge_aplusb(self, code, lang, hold=True):
        checker_fingerprint = self.rand_str(True)
        case_fingerprints = [self.rand_str(True) for _ in range(31)]
        checker_dict = dict(fingerprint=checker_fingerprint, lang='cpp', code=self.read_content('./submission/ncmp.cpp'))
        response = requests.post(self.url_base + "/upload/checker",
                                 json=checker_dict, auth=self.token).json()
        self.assertEqual(response['status'], 'received')

        for i, fingerprint in enumerate(case_fingerprints):
            response = requests.post(self.url_base + '/upload/case/%s/input' % fingerprint,
                                     data=self.read_content('./data/aplusb/ex_input%d.txt' % (i + 1), 'rb'),
                                     auth=self.token)
            self.assertEqual(response.json()['status'], 'received')
            requests.post(self.url_base + '/upload/case/%s/output' % fingerprint,
                          data=self.read_content('./data/aplusb/ex_output%d.txt' % (i + 1), 'rb'),
                          auth=self.token)
        judge_upload = dict(fingerprint=self.rand_str(True), lang=lang, code=code,
                            cases=case_fingerprints, max_time=1, max_memory=128, checker=checker_fingerprint,
                            )

        if not hold:
            judge_upload.update(hold=False)
            response = requests.post(self.url_base + '/judge', json=judge_upload, auth=self.token).json()
            self.assertEqual('received', response['status'])
            time.sleep(10)
            result = requests.get(self.url_base + '/query', json={'fingerprint': judge_upload['fingerprint']},
                                  auth=self.token).json()
        else:
            result = requests.post(self.url_base + '/judge', json=judge_upload,
                                   auth=self.token).json()
        logging.warning(result)
        return result['verdict']

    def test_aplusb_judge(self):
        self.assertEqual(self.judge_aplusb(self.read_content('./submission/aplusb.cpp'), 'cpp'), Verdict.ACCEPTED.value)
        self.assertEqual(self.judge_aplusb(self.read_content('./submission/aplusb.cpp'), 'cpp', False), Verdict.ACCEPTED.value)

    def test_aplusb_judge_ce(self):
        self.assertEqual(self.judge_aplusb(self.read_content('./submission/aplusb-ce.c'), 'c'), Verdict.COMPILE_ERROR.value)

    def test_aplusb_judge_wa(self):
        self.assertEqual(self.judge_aplusb(self.read_content('./submission/aplusb-wrong.py'), 'python'), Verdict.WRONG_ANSWER.value)

    def test_speed_val(self):
        start = time.time()
        result = requests.post(self.url_base + '/validate',
                               json=json.loads(self.read_content('./gen-and-val/speed-test.json')),
                               auth=self.token).json()
        print(result)
        end = time.time()
        self.assertLess(end - start, 10)
        self.assertEqual('received', result['status'])


if __name__ == '__main__':
    unittest.main()