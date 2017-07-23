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
LIB_BASE = path.abspath(path.join(_RUN_BASE, '../lib'))
TOKEN_FILE = path.join(_CONFIG_BASE, 'token.yaml')

with open(path.join(_CONFIG_BASE, 'lang.yaml')) as language_config:
    LANGUAGE_CONFIG = yaml.load(language_config.read())

RUN_USER_UID = getpwnam("nobody").pw_uid
RUN_GROUP_GID = getgrnam("nogroup").gr_gid

COMPILER_USER_UID = getpwnam("compiler").pw_uid
COMPILER_GROUP_GID = getgrnam("compiler").gr_gid

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
    JUDGE_ERROR = 11


USUAL_READ_SIZE = 512
TRACEBACK_LIMIT = 5
COMPILE_MAX_TIME_FOR_TRUSTED = 30
COMPILE_TIME_FACTOR = 10  # compile time limit is 10 times max time limit
REAL_TIME_FACTOR = 3  # real time limit is 2 times max time limit
MAX_WORKER_NUMBER = max(cpu_count() // 4, 1)
MAX_TASKS_PER_CHILD = 10
OUTPUT_LIMIT = 256
SECRET_KEY = 'secret!'


with open(path.join(_CONFIG_BASE, 'custom.yaml')) as config_file:
    custom_config = yaml.load(config_file.read())
    for key, val in custom_config.items():
        if val and key in globals().keys():  # if not empty
            globals()[key] = val
