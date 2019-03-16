import glob
import os
import shutil
import signal
import stat
import sys
import traceback
from os import path, makedirs, chown, remove

from config.config import COMPILER_GROUP_GID, COMPILER_USER_UID, RUN_GROUP_GID, RUN_USER_UID, NSJAIL_PATH, OUTPUT_LIMIT
from config.config import LANGUAGE_CONFIG, SUB_BASE, USUAL_READ_SIZE, ENV, REAL_TIME_FACTOR
from config.config import Verdict
from core.exception import *
from core.util import format, random_string, make_temp_dir


class Result:

  def __init__(self, time, memory, exit_code, signal, verdict=Verdict.ACCEPTED):
    self.time = time
    self.memory = memory
    self.exit_code = exit_code
    self.signal = signal
    self.verdict = verdict

  def __repr__(self):
    return "Sandbox.Result object: " + str(self.__dict__)


class Submission(object):

  def __init__(self, fingerprint, lang, exe_file=None):
    self.workspace = path.join(SUB_BASE, fingerprint)
    self.lang = lang
    # Using [] instead of .get() to throw KeyError in case of bad configuration
    self.language_config = LANGUAGE_CONFIG[lang]
    if self.exe_file is not None:
      self.exe_file = exe_file
    else:
      self.exe_file = path.join(SUB_BASE, random_string() + "." + self.language_config["exe_ext"])

  def clean(self):
    """
    Remember to call clean when you leave!

    :param force: to clean whether it is permanent or not
    """
    remove(self.exe_file)

  def format_compile_command(self, command, exe_file):
    command = command.format(code_file=self.language_config["code_file"],
                             exe_file=exe_file)
    args_list = []
    for token in command.split():
      if "*" in token:
        args_list.extend(glob.glob(token))
      else:
        args_list.append(token)
    return args_list

  def compile(self, code, max_time):
    error_path = path.join(self.workspace, "compiler_output_%s" % random_string())
    tmp_compile_out = "compile.out"
    compile_dir = make_temp_dir()
    with open(path.join(compile_dir, self.language_config["code_file"]), "w") as fs:
      fs.write(code)
    for command in self.language_config["compile"]:
      args_list = self.format_compile_command(command, tmp_compile_out)
      result = self.run(max_time=max_time, max_memory=1024,
                        stdin_file="/dev/null", stdout_file=error_path, stderr_file=error_path,
                        working_directory=compile_dir, trusted=True,
                        exe_file=args_list[0], extra_arguments=args_list[1:])
      if result.verdict != Verdict.ACCEPTED:
        error_message = self.get_message_from_file(error_path, read_size=-1)
        shutil.rmtree(compile_dir)
        if not error_message:
          if result.verdict == Verdict.TIME_LIMIT_EXCEEDED:
            error_message = 'Time limit exceeded when compiling'
          elif result.verdict == Verdict.MEMORY_LIMIT_EXCEEDED:
            error_message = 'Memory limit exceeded when compiling'
          else:
            error_message = 'Something is wrong, but, em, nothing is reported'
        raise CompileError(error_message)
    shutil.copyfile(path.join(compile_dir, tmp_compile_out), self.exe_file)
    shutil.rmtree(compile_dir)

  def get_message_from_file(self, result_file, read_size=USUAL_READ_SIZE, cleanup=False):
    try:
      with open(result_file, 'r') as result_fs:
        if read_size > 0:
          message = result_fs.read(USUAL_READ_SIZE)
        else:
          message = result_fs.read()  # unlimited
      if cleanup and path.exists(result_file):
        remove(result_file)
      return message
    except:
      return ''

  def run(self, max_time, max_memory, stdin_file: str, stdout_file: str, stderr_file: str, working_directory: str,
          exe_file: str=None, trusted=False, extra_arguments: list=None, extra_files: list=None):
    if extra_files is None:
      extra_files = list()
    if extra_arguments is None:
      extra_arguments = list()
    root_dir = make_temp_dir()
    info_dir = make_temp_dir()
    error_path = path.join(info_dir, "err")
    real_time_limit = max_time * 2
    uid = COMPILER_USER_UID if trusted else RUN_USER_UID
    gid = COMPILER_GROUP_GID if trusted else RUN_GROUP_GID
    if exe_file is None:
      exe_file = path.basename(self.exe_file)
      args = self.format_compile_command(self.language_config["execute"], exe_file)
      exe_args = args + extra_arguments
    else:
      exe_args = [exe_file] + extra_arguments
    shutil.copyfile(exe_file, working_directory)
    extra_file_bindings = []
    for k, v, mode in extra_files.items():
      extra_file_bindings.append("-" + mode)
      extra_file_bindings.append(k + ":/app/" + v)
    nsjail_args = [
      NSJAIL_PATH, "-Mo", "--chroot", root_dir, "--user", str(uid), "--group", str(gid), "--log",
      path.join(info_dir, "log"), "--usage", path.join(info_dir, "usage"),
      "-R", "/bin", "-R", "/lib", "-R", "/lib64", "-R", "/usr", "-R", "/sbin", "-R", "/dev",
      "-R", "/etc", "-B", working_directory + ":/app"] + extra_file_bindings + [
      "-D", "/app",
      "--cgroup_pids_max", "64", "--cgroup_cpu_ms_per_sec", "1000",
      "--cgroup_mem_max", str(int(max_memory * 1024 * 1024)),
      "--time_limit", str(int(real_time_limit + 1)), "--rlimit_cpu", str(int((max_time + 1))),
      "--rlimit_as", "inf", "--rlimit_stack", str(int(max_memory)),
      "--rlimit_stack", str(max(int(max_memory), 256)), "--rlimit_fsize", str(int(OUTPUT_LIMIT)),
    ]
    for k, v in ENV.items():
      nsjail_args.append("-E")
      nsjail_args.append("%s=%s" % (k, v))
    nsjail_args.append("--")
    nsjail_args.append(exe_args)

    pid = os.fork()
    if pid == 0:
      try:
        stdin_fd = os.open(stdin_file, os.O_RDONLY, stat.S_IRUSR | stat.S_IRGRP)
        os.dup2(stdin_fd, sys.stdin.fileno())
        stdout_fd = os.open(stdout_file, os.O_WRONLY, stat.S_IRUSR | stat.S_IRGRP)
        os.dup2(stdout_fd, sys.stdout.fileno())
        stderr_fd = os.open(stderr_file, os.O_WRONLY, stat.S_IRUSR | stat.S_IRGRP)
        os.dup2(stderr_fd, sys.stderr.fileno())
        os.execve(NSJAIL_PATH, nsjail_args, dict())
      except:
        with open(error_path, "w") as p:
          traceback.print_exc(file=p)
      sys.exit(0)
    else:
      try:
        os.waitpid(pid, 0)
        if os.path.exists(error_path):
          with open(error_path) as p:
            raise RuntimeError(p.read())

        with open(path.join(info_dir, "usage")) as usage_file:
          usage = {}
          for line in usage_file:
            tag, num = line.strip().split()
            usage[tag] = num

        result = Result(usage["user"] / 1000, usage["memory"] / 1024, usage["exit"], usage["signal"])
        if result.exit_code != 0:
          result.verdict = Verdict.RUNTIME_ERROR
        elif result.memory * 1048576 > max_memory > 0:
          result.verdict = Verdict.MEMORY_LIMIT_EXCEEDED
        elif result.time > max_time > 0:
          result.verdict = Verdict.TIME_LIMIT_EXCEEDED
        elif usage["pass"] / 1000 > real_time_limit > 0:
          result.verdict = Verdict.IDLENESS_LIMIT_EXCEEDED
        elif result.signal != 0:
          result.verdict = Verdict.RUNTIME_ERROR
        return result
      except:
        raise RuntimeError(traceback.format_exc())
      finally:
        shutil.rmtree(info_dir)
        shutil.rmtree(root_dir)
