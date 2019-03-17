import os
from os import path, getenv, cpu_count
import yaml
from pwd import getpwnam
from grp import getgrnam
from enum import Enum

_CONFIG_BASE = path.dirname(path.abspath(__file__))
PROJECT_BASE = path.dirname(_CONFIG_BASE)
_RUN_BASE = path.join(PROJECT_BASE, 'run')
DATA_BASE = path.join(_RUN_BASE, 'data')
SUB_BASE = path.join(_RUN_BASE, 'sub')
SPJ_BASE = path.join(_RUN_BASE, "spj")
TMP_BASE = path.join(_RUN_BASE, "tmp")
LIB_BASE = path.abspath(path.join(_RUN_BASE, '../lib'))
TOKEN_FILE = path.join(_CONFIG_BASE, 'token.yaml')
NSJAIL_PATH = path.join(PROJECT_BASE, "nsjail", "nsjail")

with open(path.join(_CONFIG_BASE, 'lang.yaml')) as language_config:
  LANGUAGE_CONFIG = yaml.safe_load(language_config.read())

RUN_USER_UID = getpwnam("nobody").pw_uid
RUN_GROUP_GID = getgrnam("nogroup").gr_gid

try:
  COMPILER_USER_UID = getpwnam("compiler").pw_uid
  COMPILER_GROUP_GID = getgrnam("compiler").gr_gid
except:
  COMPILER_USER_UID = 1000
  COMPILER_GROUP_GID = 1000

ENV = {
  "PATH": getenv("PATH", ""),
  "PYTHONPATH": getenv("PYTHONPATH", ""),
  "LANG": "en_US.UTF-8",
  "LANGUAGE": "en_US:en",
  "LC_ALL": "en_US.UTF-8",
}

DEVNULL = '/dev/null'


class Verdict(Enum):
  WAITING = -3
  JUDGING = -2
  WRONG_ANSWER = -1
  ACCEPTED = 0
  TIME_LIMIT_EXCEEDED = 1
  IDLENESS_LIMIT_EXCEEDED = 2
  MEMORY_LIMIT_EXCEEDED = 3
  RUNTIME_ERROR = 4
  SYSTEM_ERROR = 5
  COMPILE_ERROR = 6
  POINT = 7
  JUDGE_ERROR = 11


USUAL_READ_SIZE = int(os.environ.get("USUAL_READ_SIZE", 512))
TRACEBACK_LIMIT = int(os.environ.get("TRACEBACK_LIMIT", 5))
COMPILE_MAX_TIME_FOR_TRUSTED = int(os.environ.get("COMPILE_MAX_TIME_FOR_TRUSTED", 30))
OUTPUT_LIMIT = int(os.environ.get("OUTPUT_LIMIT", 256))
DEBUG = os.environ.get("DEBUG", 0)
