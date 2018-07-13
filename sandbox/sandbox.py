from os import wait4, kill, killpg, dup2, setuid, setgid, setgroups, getuid, fork, execve, execv, setpgrp, _exit
from os import WSTOPPED, WTERMSIG, WIFSIGNALED, WEXITSTATUS
import resource
import sys
import logging
import threading
import time
import signal
import psutil
import traceback

from core.util import try_to_open_file
from config.config import REAL_TIME_FACTOR, Verdict
from sandbox.seccomp import seccomp_rule_general


class Sandbox:

    class Result:

        def __init__(self, time, memory, exit_code, signal, verdict=Verdict.ACCEPTED):
            self.time = time
            self.memory = memory
            self.exit_code = exit_code
            self.signal = signal
            self.verdict = verdict

        def __repr__(self):
            return "Sandbox.Result object: " + str(self.__dict__)

    def __init__(self, execute_file, execute_args,
                 stdin=sys.stdin, stdout=sys.stdout, stderr=sys.stderr,
                 max_time=-1, max_real_time=-1, max_memory=-1, max_output_size=256, max_process_number=-1,
                 seccomp_rule=None, uid=0, gid=0, env=None):
        """

        :param execute_file:
        :param execute_args:
        :param stdin: file-like object or a string-like path
        :param stdout: as stdin
        :param stderr: as stdout, can be same as stdout
        :param max_time: max time in seconds
        :param max_real_time: max real time in seconds (2 * max_time if not specified)
        :param max_memory: max memory in megabytes
        :param max_output_size: max output size in megabytes
        :param max_process_number:
        :param seccomp_rule:
        :param uid:
        :param gid:
        """
        self.seccomp_rule = str(seccomp_rule)
        self.execute_file = execute_file
        self.execute_args = list(execute_args)
        self.max_cpu_time = float(max_time)
        self.max_real_time = self.max_cpu_time * REAL_TIME_FACTOR if max_real_time < 0 else max_real_time
        self.max_memory = float(max_memory) * 1024 * 1024  # in bytes
        self.max_output_size = float(max_output_size) * 1024 * 1024  # in bytes
        self.max_process_number = int(max_process_number)

        self.stdin, self.stdout, self.stderr = try_to_open_file((stdin, 'r'), (stdout, 'w'), (stderr, 'w'))
        self.env = env if env else {}

        self.uid = int(uid)
        self.gid = int(gid)

    def __del__(self):
        self.stdin.close()
        self.stdout.close()
        self.stderr.close()

    def set_resource_limit(self):
        if self.max_cpu_time > 0:
            resource.setrlimit(resource.RLIMIT_CPU, (int(self.max_cpu_time + 1), int(self.max_cpu_time + 1)))
        if self.max_memory > 0:
            if self.seccomp_rule != "scipy":
                resource.setrlimit(resource.RLIMIT_AS, (int(self.max_memory * 2), int(self.max_memory * 2)))
            resource.setrlimit(resource.RLIMIT_STACK, (int(self.max_memory * 2), int(self.max_memory * 2)))
        if self.max_output_size > 0:
            resource.setrlimit(resource.RLIMIT_FSIZE, (int(self.max_output_size), int(self.max_output_size)))
        if self.max_process_number > 0:
            if self.seccomp_rule != "scipy":
                resource.setrlimit(resource.RLIMIT_NPROC, (self.max_process_number, self.max_process_number))

    def redirect_input_and_output(self):
        # use number instead of function to prevent errors in Celery
        dup2(self.stdin.fileno(), 0)  # sys.stdin.fileno()
        dup2(self.stdout.fileno(), 1)  # sys.stdout.fileno()
        dup2(self.stderr.fileno(), 2)  # sys.stderr.fileno()

    def set_user_identity(self):
        setgid(self.gid)
        # setgroups([self.gid])
        setuid(self.uid)

    def load_seccomp_rule(self):
        if self.seccomp_rule == "general":
            seccomp_rule_general(self.execute_file, ["socket", "clone", "fork", "vfork", "kill"], ["execve", "open"])
        elif self.seccomp_rule == "csharp":
            seccomp_rule_general(self.execute_file, ["fork", "vfork"], ["execve"])
        elif self.seccomp_rule == 'py':
            seccomp_rule_general(self.execute_file, ["clone", "fork", "vfork", "kill"], ["execve", "open"])
        elif self.seccomp_rule == 'js':
            seccomp_rule_general(self.execute_file, ["socket", "fork", "vfork", "kill"], ["execve", "open"])
        # No such thing for Java :)

    def run(self):
        if getuid() != 0:
            # is not running under root
            raise PermissionError("Please rerun as root.")
        child_pid = fork()

        if child_pid == 0:
            # in the child now
            try:
                setpgrp()
                self.set_resource_limit()
                self.redirect_input_and_output()
                self.set_user_identity()
                self.load_seccomp_rule()
                execve(self.execute_file, [self.execute_file] + self.execute_args, self.env)
            except:
                traceback.print_exc()
                _exit(-777)  # Magic number, indicates something wrong during execution
        else:
            # in the parent process
            # print(psutil.Process(child_pid).memory_full_info())
            killer = None
            if self.max_real_time > 0:
                killer = threading.Timer(self.max_real_time, killpg, (child_pid, signal.SIGKILL))
                killer.start()

            start_time = time.time()
            pid, status, rusage = wait4(child_pid, WSTOPPED)
            stop_time = time.time()
            real_time_consumed = stop_time - start_time

            if killer:
                killer.cancel()

            result = Sandbox.Result(rusage.ru_utime, rusage.ru_maxrss / 1024, WEXITSTATUS(status),
                                    WTERMSIG(status) if WIFSIGNALED(status) else 0)
            if result.exit_code != 0:
                result.verdict = Verdict.RUNTIME_ERROR
            if result.exit_code == -777:  # Magic number, see above
                result.verdict = Verdict.SYSTEM_ERROR
            elif result.memory * 1048576 > self.max_memory > 0:
                result.verdict = Verdict.MEMORY_LIMIT_EXCEEDED
            elif result.time > self.max_cpu_time > 0:
                result.verdict = Verdict.TIME_LIMIT_EXCEEDED
            elif real_time_consumed > self.max_real_time > 0:
                result.verdict = Verdict.IDLENESS_LIMIT_EXCEEDED
                # result.time = self.max_cpu_time
            elif result.signal != 0:
                if result.signal == signal.SIGUSR1:
                    result.verdict = Verdict.SYSTEM_ERROR
                else:
                    result.verdict = Verdict.RUNTIME_ERROR

            logging.info(result)
            return result
