import multiprocessing
import os
import signal
import unittest
import logging

from config.config import Verdict
from sandbox.sandbox import Sandbox
from tests.test_base import TestBase


class SandboxTest(TestBase):

    def setUp(self):
        logging.basicConfig(level=logging.INFO)
        self.workspace = "/tmp/sandbox"
        self.config = {"max_time": 1.0,
                       "max_memory": 128,
                       "max_process_number": 10,
                       "execute_file": "/bin/ls",
                       "execute_args": [],
                       "env": {"env": "judger_test", "test": "judger"},
                       "stdin": "/dev/null",
                       "stdout": "/dev/null",
                       "stderr": "/dev/null"}
        super(SandboxTest, self).setUp()

    def test_normal(self):
        config = self.config
        config["execute_file"] = self.compile_c("normal.c")
        config["stdin"] = self.make_input("sandbox_test")
        config["stdout"] = config["stderr"] = self.output_path()
        result = Sandbox(**config).run()
        output = "sandbox_test\nHello world"
        self.assertEqual(result.verdict, Verdict.ACCEPTED)
        self.assertEqual(output, self.output_content(config["stdout"]))

        config["execute_file"] = self.compile_c("math.c")
        config["stdin"] = "/dev/null"
        config["stdout"] = config["stderr"] = self.output_path()
        result = Sandbox(**config).run()
        self.assertEqual(result.verdict, Verdict.ACCEPTED)
        self.assertEqual("abs 1024", self.output_content(config["stdout"]))

    def test_normal_with_seccomp(self):
        config = self.config
        config["execute_file"] = self.compile_c("normal.c")
        config["stdin"] = self.make_input("sandbox_test")
        config["stdout"] = config["stderr"] = self.output_path()
        config["seccomp_rule"] = "general"
        result = Sandbox(**config).run()
        output = "sandbox_test\nHello world"
        self.assertEqual(result.verdict, Verdict.ACCEPTED)
        self.assertEqual(output, self.output_content(config["stdout"]))

    def test_args(self):
        config = self.config
        config["execute_file"] = self.compile_c("args.c")
        config["execute_args"] = ["test", "hehe", "000"]
        config["stdout"] = config["stderr"] = self.output_path()
        result = Sandbox(**config).run()
        output = "argv[0]: /tmp/sandbox/args\nargv[1]: test\nargv[2]: hehe\nargv[3]: 000\n"
        self.assertEqual(result.verdict, Verdict.ACCEPTED)
        self.assertEqual(output, self.output_content(config["stdout"]))

    def test_env(self):
        config = self.config
        config["execute_file"] = self.compile_c("env.c")
        config["stdout"] = config["stderr"] = self.output_path()
        result = Sandbox(**config).run()
        output = "judger_test\njudger\n"
        self.assertEqual(result.verdict, Verdict.ACCEPTED)
        self.assertEqual(output, self.output_content(config["stdout"]))

    def test_real_time(self):
        config = self.config
        config["execute_file"] = self.compile_c("sleep.c")
        result = Sandbox(**config).run()
        self.assertEqual(result.verdict, Verdict.IDLENESS_LIMIT_EXCEEDED)
        self.assertEqual(result.signal, signal.SIGKILL)

    def test_cpu_time(self):
        config = self.config
        config["execute_file"] = self.compile_c("while1.c")
        result = Sandbox(**config).run()
        self.assertEqual(result.verdict, Verdict.TIME_LIMIT_EXCEEDED)
        self.assertEqual(result.signal, signal.SIGKILL)
        self.assertTrue(result.time >= config["max_time"])

    def test_memory1(self):
        config = self.config
        config["max_memory"] = 64
        config["execute_file"] = self.compile_c("memory1.c")
        result = Sandbox(**config).run()
        # malloc succeeded
        self.assertEqual(result.verdict, Verdict.MEMORY_LIMIT_EXCEEDED)
        self.assertTrue(result.memory > 80)
        config["max_memory"] = 30
        result = Sandbox(**config).run()
        # too little memory, malloc failed
        self.assertEqual(result.verdict, Verdict.RUNTIME_ERROR)

    def test_memory2(self):
        config = self.config
        config["max_memory"] = 64
        config["execute_file"] = self.compile_c("memory2.c")
        result = Sandbox(**config).run()
        # malloc failed, return 1
        self.assertEqual(result.exit_code, 1)
        # malloc failed, so it should use a little memory
        self.assertTrue(result.memory < 20)
        self.assertEqual(result.verdict, Verdict.RUNTIME_ERROR)

    def test_memory3(self):
        config = self.config
        config["max_memory"] = 512
        config["execute_file"] = self.compile_c("memory3.c")
        result = Sandbox(**config).run()
        self.assertEqual(result.verdict, Verdict.ACCEPTED)
        self.assertTrue(result.memory >= 102400000 * 4 / 1024 / 1024)

    def test_re1(self):
        config = self.config
        config["execute_file"] = self.compile_c("re1.c")
        result = Sandbox(**config).run()
        # re1.c return 25
        self.assertEqual(result.exit_code, 25)

    def test_re2(self):
        config = self.config
        config["execute_file"] = self.compile_c("re2.c")
        result = Sandbox(**config).run()
        self.assertEqual(result.verdict, Verdict.RUNTIME_ERROR)
        self.assertEqual(result.signal, signal.SIGSEGV)

    def test_child_proc_cpu_time_limit(self):
        config = self.config
        config["execute_file"] = self.compile_c("child_proc_cpu_time_limit.c")
        result = Sandbox(**config).run()
        self.assertEqual(result.verdict, Verdict.IDLENESS_LIMIT_EXCEEDED)

    def test_child_proc_real_time_limit(self):
        config = self.config
        config["execute_file"] = self.compile_c("child_proc_real_time_limit.c")
        result = Sandbox(**config).run()
        self.assertEqual(result.verdict, Verdict.IDLENESS_LIMIT_EXCEEDED)
        self.assertEqual(result.signal, signal.SIGKILL)

    def test_stdout_and_stderr(self):
        config = self.config
        config["execute_file"] = self.compile_c("stdout_stderr.c")
        config["stdout"] = config["stderr"] = self.output_path()
        result = Sandbox(**config).run()
        self.assertEqual(result.verdict, Verdict.ACCEPTED)
        output = "stderr\n+++++++++++++++\n--------------\nstdout\n"
        self.assertEqual(output, self.output_content(config["stdout"]))

    def test_uid_and_gid(self):
        config = self.config
        config["execute_file"] = self.compile_c("uid_gid.c")
        config["stdout"] = config["stderr"] = self.output_path()
        config["uid"] = 65534
        config["gid"] = 65534
        result = Sandbox(**config).run()
        self.assertEqual(result.verdict, Verdict.ACCEPTED)
        output = "uid=65534(nobody) gid=65534(nogroup) groups=65534(nogroup),0(root)\nuid 65534\ngid 65534\n"
        self.assertEqual(output, self.output_content(config["stdout"]))

    def test_gcc_random(self):
        config = self.config
        config["execute_file"] = "/usr/bin/gcc"
        config["execute_args"] = ["./sandbox/gcc_random.c",
                          "-o", os.path.join(self.workspace, "gcc_random")]
        result = Sandbox(**config).run()
        self.assertEqual(result.verdict, Verdict.IDLENESS_LIMIT_EXCEEDED)

    def test_cpp_meta(self):
        config = self.config
        config["execute_file"] = "/usr/bin/g++"
        config["max_memory"] = 1024
        config["execute_args"] = ["./sandbox/cpp_meta.cpp",
                          "-o", os.path.join(self.workspace, "cpp_meta")]
        result = Sandbox(**config).run()
        self.assertEqual(result.verdict, Verdict.IDLENESS_LIMIT_EXCEEDED)

    def test_output_size(self):
        config = self.config
        config["execute_file"] = self.compile_c("output_size.c")
        config["max_output_size"] = 1
        result = Sandbox(**config).run()
        self.assertEqual(result.exit_code, 2)

    def test_stack_size(self):
        config = self.config
        config["max_memory"] = 256
        config["execute_file"] = self.compile_c("stack.c")
        config["stdout"] = config["stderr"] = self.output_path()
        result = Sandbox(**config).run()
        self.assertEqual(result.verdict, Verdict.ACCEPTED)
        self.assertEqual("big stack", self.output_content(config["stdout"]))

    def test_fork(self):
        config = self.config
        config["max_memory"] = 1024
        config["execute_file"] = self.compile_c("fork.c")
        config["stdout"] = config["stderr"] = self.output_path()
        result = Sandbox(**config).run()

        # without seccomp
        self.assertEqual(result.verdict, Verdict.ACCEPTED)

        # with general seccomp
        config["seccomp_rule"] = "general"
        result = Sandbox(**config).run()
        self.assertEqual(result.verdict, Verdict.RUNTIME_ERROR)
        self.assertEqual(result.signal, 31)

    def test_double_fork_allowed(self):
        # This test is to deal with possible un-clarified problem encountered in setgroups
        config = self.config
        config["max_memory"] = 30
        config["execute_file"] = self.compile_c("fork.c")
        config["stdout"] = config["stderr"] = self.output_path()
        result = Sandbox(**config).run()
        self.assertEqual(result.verdict, Verdict.ACCEPTED)
        result = Sandbox(**config).run()
        self.assertEqual(result.verdict, Verdict.ACCEPTED)

    def test_execve(self):
        config = self.config
        config["max_memory"] = 1024
        config["execute_file"] = self.compile_c("execve.c")
        config["stdout"] = config["stderr"] = self.output_path()
        result = Sandbox(**config).run()
        # without seccomp
        self.assertEqual(result.verdict, Verdict.ACCEPTED)
        self.assertEqual("Helloworld\n", self.output_content(config["stdout"]))

        # with general seccomp
        config["seccomp_rule"] = "general"
        result = Sandbox(**config).run()
        self.assertEqual(result.verdict, Verdict.RUNTIME_ERROR)
        self.assertEqual(result.signal, 31)

    def test_write_file(self):
        config = self.config
        config["max_memory"] = 1024
        config["execute_file"] = self.compile_c("write_file.c")
        config["stdout"] = config["stderr"] = self.output_path()
        result = Sandbox(**config).run()
        # without seccomp
        self.assertEqual(result.verdict, Verdict.ACCEPTED)
        self.assertEqual("test", self.output_content("/tmp/fffffffffffffile.txt"))

        # with general seccomp
        config["seccomp_rule"] = "general"
        result = Sandbox(**config).run()
        self.assertEqual(result.verdict, Verdict.RUNTIME_ERROR)
        self.assertEqual(result.signal, 31)

    def test_multiprocessing(self):
        config = self.config
        config["execute_file"] = self.compile_c("normal.c")
        config["stdin"] = self.make_input("sandbox_test")
        config["stdout"] = config["stderr"] = self.output_path()
        sandbox = Sandbox(**config)
        p = multiprocessing.Process(target=sandbox.run)
        p.start()
        p.join()

    def test_python(self):
        config = self.config
        config["execute_file"] = "/usr/bin/python3"
        config["execute_args"] = ["./sandbox/python_test.py"]
        config["stdout"] = config["stderr"] = self.output_path()
        result = Sandbox(**config).run()
        self.assertEqual(result.verdict, Verdict.ACCEPTED)
        self.assertEqual("hello\n", self.output_content(config["stdout"]))

    def test_pass_filelike_object(self):
        config = self.config
        config["execute_file"] = "/usr/bin/python3"
        config["execute_args"] = ["./sandbox/python_test.py"]
        output_file = self.output_path()
        config["stdout"] = config["stderr"] = open(output_file, 'w')
        result = Sandbox(**config).run()
        self.assertEqual(result.verdict, Verdict.ACCEPTED)
        self.assertEqual("hello\n", self.output_content(output_file))


if __name__ == '__main__':
    unittest.main()