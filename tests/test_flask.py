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

from config.config import Verdict, SPJ_BASE
from core.case import Case
from tests.test_base import TestBase
from config.config import SUB_BASE
from handler import trace_group_dependencies

URL_BASE = 'http://localhost:5000'


class FlaskTest(TestBase):

  def setUp(self):
    self.workspace = '/tmp/flask'
    self.url_base = URL_BASE
    self.token = ('ejudge', 'naive')  # Token has to be reset to do this test
    super().setUp()

  def test_analyze_dependencies(self):
    self.assertEqual({2: {1, 2}, 3: {1, 2, 3}}, trace_group_dependencies([(1, 2), (1, 3), (2, 3)]))
    self.assertEqual({1: {1, 2}}, trace_group_dependencies([(2, 1)]))
    self.assertEqual({3: {1, 3, 4, 5, 6, 7}, 4: {1, 4, 5, 6, 7}, 5: {1, 5, 6, 7}, 6: {1, 6, 7}, 7: {1, 7}},
                     trace_group_dependencies([(1, 7), (7, 6), (6, 5), (5, 4), (4, 3)]))
    self.assertEqual({1: {1, 3}, 2: {2, 3}}, trace_group_dependencies([(3, 1), (3, 2)]))
    self.assertEqual({1: {1, 2, 3, 4}, 2: {2, 4}, 3: {3, 4}},
                     trace_group_dependencies([(2, 1), (3, 1), (4, 2), (4, 3)]))

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

  def test_upload_checker_fail(self):
    fingerprint = 'test_%s' % self.rand_str()
    json_data = {'fingerprint': fingerprint, 'code': 'code', 'lang': 'cpp'}
    result = requests.post(self.url_base + '/upload/spj', json=json_data,
                           auth=self.token).json()
    self.assertEqual('reject', result['status'])
    self.assertIn("CompileError", result['message'])

  def test_upload_interactor(self):
    fingerprint = self.rand_str()
    json_data = {'fingerprint': fingerprint, 'code': self.read_content('./interact/interactor-a-plus-b.cpp', 'r'),
                 'lang': 'cpp'}
    result = requests.post(self.url_base + '/upload/spj', json=json_data, auth=self.token).json()
    self.assertEqual('received', result['status'])
    self.assertIn(fingerprint + ".bin11", os.listdir(SPJ_BASE))

  def test_list_spj(self):
    result = requests.get(self.url_base + '/list/spj', auth=self.token).json()
    self.assertEqual('received', result['status'])
    self.assertGreater(len(result["spj"]), 0)

  def judge_aplusb(self, code, lang, hold=True):
    checker_fingerprint = self.rand_str(True)
    case_fingerprints = [self.rand_str(True) for _ in range(31)]
    checker_dict = dict(fingerprint=checker_fingerprint, lang='cpp', code=self.read_content('./submission/ncmp.cpp'))
    response = requests.post(self.url_base + "/upload/spj",
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
      report = requests.get(self.url_base + '/query/report', json={'fingerprint': judge_upload['fingerprint']},
                            auth=self.token).text
      logging.warning(report)
    else:
      result = requests.post(self.url_base + '/judge', json=judge_upload,
                             auth=self.token).json()
    logging.warning(result)
    return result['verdict']

  def judge_aplusb_group(self, code, lang, group_graph):
    checker_fingerprint = self.rand_str(True)
    case_fingerprints = [self.rand_str(True) for _ in range(31)]
    checker_dict = dict(fingerprint=checker_fingerprint, lang='cpp', code=self.read_content('./submission/ncmp.cpp'))
    response = requests.post(self.url_base + "/upload/spj",
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
                        hold=False, group_list=[1] * 10 + [2] * 10 + [3] * (len(case_fingerprints) - 20),
                        group_dependencies=group_graph)

    response = requests.post(self.url_base + '/judge', json=judge_upload, auth=self.token).json()
    self.assertEqual('received', response['status'])
    time.sleep(10)
    result = requests.get(self.url_base + '/query', json={'fingerprint': judge_upload['fingerprint']},
                          auth=self.token).json()
    logging.warning(result)
    return result['verdict']

  def test_aplusb_judge(self):
    self.assertEqual(self.judge_aplusb(self.read_content('./submission/aplusb.cpp'), 'cpp'), Verdict.ACCEPTED.value)
    self.assertEqual(self.judge_aplusb(self.read_content('./submission/aplusb.cpp'), 'cpp', False),
                     Verdict.ACCEPTED.value)
    self.assertEqual(self.judge_aplusb(self.read_content('./submission/aplusb2.cpp'), 'cpp', False),
                     Verdict.ACCEPTED.value)

  def test_aplusb_judge_traceback(self):
    judge_upload = dict(fingerprint=self.rand_str(True), lang='cpp', code='int main() { return 0; }',
                        cases=[], max_time=1, max_memory=128, checker='ttt', hold=False)
    response = requests.post(self.url_base + '/judge', json=judge_upload, auth=self.token).json()
    self.assertEqual('received', response['status'], response)
    time.sleep(3)
    response = requests.get(self.url_base + '/query', json={'fingerprint': judge_upload['fingerprint']},
                            auth=self.token).json()
    print(response)
    self.assertEqual('reject', response['status'])
    self.assertIn('message', response)

  def test_aplusb_judge_ce(self):
    self.assertEqual(self.judge_aplusb(self.read_content('./submission/aplusb-ce.c'), 'c'),
                     Verdict.COMPILE_ERROR.value)
    self.assertEqual(self.judge_aplusb(self.read_content('./submission/aplusb-ce.c'), 'c', False),
                     Verdict.COMPILE_ERROR.value)

  def test_aplusb_judge_wa(self):
    self.assertEqual(self.judge_aplusb(self.read_content('./submission/aplusb-wrong.py'), 'python'),
                     Verdict.WRONG_ANSWER.value)
    self.assertEqual(self.judge_aplusb(self.read_content('./submission/aplusb-wrong.py'), 'python', False),
                     Verdict.WRONG_ANSWER.value)

  def test_aplusb_judge_group_wa(self):
    self.assertEqual(self.judge_aplusb_group(self.read_content('./submission/aplusb-wrong.py'), 'python', [(2, 1)]),
                     Verdict.WRONG_ANSWER.value)

  def test_aplusb_judge_group_ac(self):
    self.assertEqual(self.judge_aplusb_group(self.read_content('./submission/aplusb.cpp'), 'cpp', [(2, 1)]),
                     Verdict.ACCEPTED.value)

  def test_judge_interactive_ile(self):
    checker_fingerprint = self.rand_str(True)
    interactor_fingerprint = self.rand_str(True)
    case_fingerprints = [self.rand_str(True)]

    response = requests.post(self.url_base + '/upload/case/%s/input' % case_fingerprints[0],
                             data=self.read_content('./interact/guess-input.txt', 'rb'),
                             auth=self.token)
    self.assertEqual(response.json()['status'], 'received')
    response = requests.post(self.url_base + '/upload/case/%s/output' % case_fingerprints[0],
                             data=self.read_content('./interact/guess-output.txt', 'rb'),
                             auth=self.token)
    self.assertEqual(response.json()['status'], 'received')

    checker_dict = dict(fingerprint=checker_fingerprint, lang='cpp',
                        code=self.read_content('./interact/guess-checker.cpp'))
    response = requests.post(self.url_base + "/upload/spj",
                             json=checker_dict, auth=self.token)
    self.assertEqual(response.json()['status'], 'received')

    interactor_dict = dict(fingerprint=interactor_fingerprint, lang='cpp',
                           code=self.read_content('./interact/guess-interactor.cpp'))
    response = requests.post(self.url_base + "/upload/spj",
                             json=interactor_dict, auth=self.token)
    self.assertEqual(response.json()['status'], 'received')

    judge_upload = dict(fingerprint=self.rand_str(True), lang='cpp',
                        code=self.read_content('./interact/guess-bad.cpp'),
                        cases=case_fingerprints, max_time=1, max_memory=128, checker=checker_fingerprint,
                        interactor=interactor_fingerprint
                        )

    result = requests.post(self.url_base + '/judge', json=judge_upload,
                           auth=self.token).json()
    logging.warning(result)
    return result['verdict']


if __name__ == '__main__':
  unittest.main()
