import string
import random
import signal
from os import fdopen, path, makedirs

from config.config import TMP_BASE


def try_to_open_file(*args):
  """ try to open multiple files
  *args: pass (path / file object, mode) tuple, and return file-like objects list
  """
  lst = []
  appear = {}
  for foo, mode in args:
    if isinstance(foo, str):
      file = appear.get((foo, mode))
      if file is None:
        file = open(foo, mode)
        appear[(foo, mode)] = file
      lst.append(file)
    else:
      lst.append(foo)
  return lst


def random_string(length=32):
  return ''.join(list(random.choice("0123456789abcdef") for i in range(length)))


def get_signal_name(signal_num):
  try:
    return signal.Signals(signal_num).name
  except:
    return 'SIG%03d' % signal_num


def serialize_sandbox_result(result):
  'Can be also used for SpecialJudge.Result'
  d = result.__dict__.copy()
  d['verdict'] = d['verdict'].value
  return d


def make_temp_dir():
  while True:
    directory = path.join(TMP_BASE, random_string())
    try:
      makedirs(directory)
      return directory
    except FileExistsError:
      pass
