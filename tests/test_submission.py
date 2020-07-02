import unittest
import logging
from unittest import TestCase
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import Verdict
from core.submission import Submission
from tests.test_base import TestBase


class APlusBTest(TestBase):

  def setUp(self):
    logging.basicConfig(level=logging.INFO)
    self.workspace = '/tmp/submission'
    super(APlusBTest, self).setUp()

    self.running_config = {
      'stdin_file': self.make_input('1\n2\n'),
      'stdout_file': self.output_path(),
      'stderr_file': self.output_path(),
      'max_time': 3,
      'max_memory': 128,
      'working_directory': self.workspace
    }

    lang = self._testMethodName[5:]
    code = self.read_content('./submission/aplusb.%s' % lang)
    self.submission = Submission(lang)
    self.submission.compile(code, 5)
    self.result = self.submission.run(**self.running_config)
    if self.result.verdict != Verdict.ACCEPTED:
      print(self.output_content(self.running_config['stderr_file']))
    self.assertEqual(self.result.verdict, Verdict.ACCEPTED)
    self.assertEqual('3', self.output_content(self.running_config['stdout_file']).strip())

  def tearDown(self):
    self.submission.clean()

  def test_c(self):
    pass

  def test_cpp(self):
    pass

  def test_cc14(self):
    pass

  def test_cc17(self):
    pass

  def test_java(self):
    pass

  def test_pas(self):
    pass

  def test_py2(self):
    pass

  def test_python(self):
    pass

  def test_pypy(self):
    pass

  def test_pypy3(self):
    pass

  def test_text(self):
    pass


class TrustedSubmissionTest(TestBase):

  def setUp(self):
    logging.basicConfig(level=logging.INFO)
    self.workspace = '/tmp/trusted'
    super(TrustedSubmissionTest, self).setUp()

  def test_cpp_library(self):
    self.running_config = {
      'stdin_file': '/dev/null',
      'stdout_file': self.output_path(),
      'stderr_file': self.output_path(),
      'max_time': 3,
      'max_memory': 128,
      'working_directory': self.workspace
    }

    code = self.read_content('./submission/testlib-test.cpp')

    self.submission = Submission('cpp')
    self.submission.compile(code, 10)
    self.result = self.submission.run(**self.running_config)
    self.assertEqual(self.result.verdict, Verdict.ACCEPTED)
    print(self.output_content(self.running_config['stdout_file']))
    self.submission.clean()

  def test_python_library(self):
    self.running_config = {
      'stdin_file': '/dev/null',
      'stdout_file': self.output_path(),
      'stderr_file': self.output_path(),
      'max_time': 3,
      'max_memory': 512,
      'working_directory': self.workspace
    }

    code = self.read_content('./submission/numpy-test.py')

    self.submission = Submission('python')
    self.submission.compile(code, 5)
    self.result = self.submission.run(**self.running_config)
    logging.info(self.output_content(self.running_config['stderr_file']))
    logging.info(self.output_content(self.running_config['stdout_file']))
    self.assertEqual(self.result.verdict, Verdict.ACCEPTED)
    self.submission.clean()


if __name__ == '__main__':
  unittest.main()
