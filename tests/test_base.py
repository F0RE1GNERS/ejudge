import os
import random
import shutil
import string
import sys
from unittest import TestCase

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestBase(TestCase):
  workspace = '/tmp/abc'

  def setUp(self):
    shutil.rmtree(self.workspace, ignore_errors=True)
    os.makedirs(self.workspace)
    print("Running", self._testMethodName)

  @staticmethod
  def rand_str(test=True):
    gen = ''.join([random.choice(string.ascii_letters) for _ in range(32)])
    return ('test_' + gen) if test else gen

  def make_input(self, content):
    path = os.path.join(self.workspace, self.rand_str())
    with open(path, "w") as f:
      f.write(content)
    return path

  def output_path(self):
    return os.path.join(self.workspace, self.rand_str())

  @staticmethod
  def output_content(path):
    with open(path, "r") as f:
      return f.read()

  @staticmethod
  def read_content(path, mode='r'):
    with open(path, mode) as f:
      return f.read()
