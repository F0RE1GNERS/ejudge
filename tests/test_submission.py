import unittest
import logging
from unittest import TestCase
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.config import Verdict
from core.submission import Submission
from sandbox.sandbox import Sandbox
from tests.test_base import TestBase


class APlusBTest(TestBase):

    def setUp(self):
        logging.basicConfig(level=logging.INFO)
        self.workspace = '/tmp/submission'
        super(APlusBTest, self).setUp()

        self.running_config = {
            'stdin': self.make_input('1\n2\n'),
            'stdout': self.output_path(),
            'stderr': self.output_path(),
            'max_time': 3,
            'max_memory': 128,
        }

        lang = self._testMethodName[5:]
        code = self.read_content('./submission/aplusb.%s' % lang)
        fingerprint = self.rand_str()

        self.submission = Submission(fingerprint, code, lang)
        self.result = self.submission.run(**self.running_config)
        self.assertEqual(self.result.verdict, Verdict.ACCEPTED)
        self.assertEqual('3', self.output_content(self.running_config['stdout']).strip())

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

    def test_cs(self):
        pass

    def test_hs(self):
        pass

    def test_java(self):
        pass

    def test_js(self):
        pass

    def test_pas(self):
        pass

    def test_php(self):
        pass

    def test_py2(self):
        pass

    def test_python(self):
        pass

    def test_pypy(self):
        pass

    def test_perl(self):
        pass

    def test_ocaml(self):
        pass

    def test_rs(self):
        pass

    def test_scala(self):
        pass

    def test_text(self):
        pass


class TrustedSubmissionTest(TestBase):

    def setUp(self):
        logging.basicConfig(level=logging.INFO)
        self.workspace = '/tmp/trusted'
        super(TrustedSubmissionTest, self).setUp()

    def test_java_unsafe(self):
        with open("/tmp/unsafe.txt", "w") as f:
            f.write('unsafe\n')
        self.running_config = {
            'stdin': '/dev/null',
            'stdout': self.output_path(),
            'stderr': self.output_path(),
            'max_time': 3,
            'max_memory': 128,
            'trusted': True,
        }

        lang = 'java'
        code = self.read_content('./submission/java_unsafe.java')
        fingerprint = self.rand_str()

        self.submission = Submission(fingerprint, code, lang)
        self.result = self.submission.run(**self.running_config)
        self.assertEqual(self.result.verdict, Verdict.ACCEPTED)
        self.assertEqual('unsafe', self.output_content(self.running_config['stdout']).strip())

    def test_cpp_library(self):
        self.running_config = {
            'stdin': '/dev/null',
            'stdout': self.output_path(),
            'stderr': self.output_path(),
            'max_time': 3,
            'max_memory': 128,
        }

        code = self.read_content('./submission/testlib-test.cpp')
        fingerprint = self.rand_str()

        self.submission = Submission(fingerprint, code, 'cpp')
        self.result = self.submission.run(**self.running_config)
        self.assertEqual(self.result.verdict, Verdict.ACCEPTED)
        print(self.output_content(self.running_config['stdout']))
        self.submission.clean()

    # TODO: python library limitations break
    # def test_python_library(self):
    #     self.running_config = {
    #         'stdin': '/dev/null',
    #         'stdout': self.output_path(),
    #         'stderr': self.output_path(),
    #         'max_time': 3,
    #         'max_memory': 512,
    #     }
    #
    #     code = self.read_content('./submission/numpy-test.py')
    #     fingerprint = self.rand_str()
    #
    #     self.submission = Submission(fingerprint, code, 'python')
    #     self.result = self.submission.run(**self.running_config)
    #     logging.info(self.output_content(self.running_config['stderr']))
    #     logging.info(self.output_content(self.running_config['stdout']))
    #     self.assertEqual(self.result.verdict, Verdict.ACCEPTED)
    #     self.submission.clean()


if __name__ == '__main__':
    unittest.main()