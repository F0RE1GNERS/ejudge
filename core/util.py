import random
import signal
from os import path, makedirs

from config.config import TMP_BASE


def random_string(length=32):
  return ''.join(list(random.choice("0123456789abcdef") for _ in range(length)))


def get_signal_name(signal_num):
  try:
    return signal.Signals(signal_num).name
  except:
    return 'SIG%03d' % signal_num


def make_temp_dir():
  while True:
    directory = path.join(TMP_BASE, random_string())
    try:
      makedirs(directory)
      return directory
    except FileExistsError:
      pass
