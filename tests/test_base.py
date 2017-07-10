from unittest import TestCase
import shutil
import os
import random
import string

class TestBase(TestCase):

    workspace = '/tmp/abc'

    def setUp(self):
        shutil.rmtree(self.workspace, ignore_errors=True)
        os.makedirs(self.workspace)
        print("Running", self._testMethodName)

    def rand_str(self, test=True):
        gen = ''.join([random.choice(string.ascii_letters) for _ in range(32)])
        return ('test_' + gen) if test else gen

    def compile_c(self, src_name):
        path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sandbox")
        execute_file = os.path.join(self.workspace, os.path.splitext(src_name)[0])
        cmd = "gcc {0} -g -O0 -o {1}".format(os.path.join(path, src_name), execute_file)
        if os.system(cmd):
            raise AssertionError("compile error, cmd: {0}".format(cmd))
        return execute_file

    def make_input(self, content):
        path = os.path.join(self.workspace, self.rand_str())
        with open(path, "w") as f:
            f.write(content)
        return path

    def output_path(self):
        return os.path.join(self.workspace, self.rand_str())

    def output_content(self, path):
        with open(path, "r") as f:
            return f.read()