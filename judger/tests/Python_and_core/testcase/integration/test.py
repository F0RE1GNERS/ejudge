# coding=utf-8
import _judger
import signal
import os

from .. import base


class IntegrationTest(base.BaseTestCase):
    def setUp(self):
        print("Running", self._testMethodName)
        self.config = {"max_cpu_time": 1000,
                       "max_real_time": 3000,
                       "max_memory": 1024 * 1024 * 128,
                       "max_process_number": 10,
                       "max_output_size": 1024 * 1024,
                       "exe_path": "/bin/ls",
                       "input_path": "/dev/null",
                       "output_path": "/dev/null",
                       "error_path": "/dev/null",
                       "args": [],
                       "env": ["env=judger_test", "test=judger"],
                       "log_path": "judger_test.log",
                       "seccomp_rule_name": None,
                       "uid": 0,
                       "gid": 0}
        self.workspace = self.init_workspace("integration")
        
    def _compile_c(self, src_name, extra_flags=None):
        return super(IntegrationTest, self)._compile_c("../../test_src/integration/" + src_name, extra_flags)

    def _compile_cpp(self, src_name):
        return super(IntegrationTest, self)._compile_cpp("integration/" + src_name)

    def test_args_validation(self):
        with self.assertRaisesRegex(ValueError, "Invalid args and kwargs"):
            _judger.run()
            _judger.run(a=1, c=3)

    def test_args_must_be_list(self):
        with self.assertRaisesRegex(ValueError, "args must be a list"):
            _judger.run(max_cpu_time=1000, max_real_time=2000, max_memory=1000000000,
                        max_process_number=200, max_output_size=10000, exe_path="1.out",
                        input_path="1.in", output_path="1.out", error_path="1.out",
                        args="12344", env=["a=b"], log_path="1.log",
                        seccomp_rule_name="1.so", uid=0, gid=0)

        with self.assertRaisesRegex(ValueError, "args must be a list"):
            _judger.run(max_cpu_time=1000, max_real_time=2000, max_memory=1000000000,
                        max_process_number=200, max_output_size=10000, exe_path="1.out",
                        input_path="1.in", output_path="1.out", error_path="1.out",
                        args={"k": "v"}, env=["a=b"], log_path="1.log",
                        seccomp_rule_name="1.so", uid=0, gid=0)

    def test_args_item_must_be_string(self):
        with self.assertRaisesRegex(ValueError, "arg item must be a string"):
            _judger.run(max_cpu_time=1000, max_real_time=2000, max_memory=1000000000,
                        max_process_number=200, max_output_size=10000, exe_path="1.out",
                        input_path="1.in", output_path="1.out", error_path="1.out",
                        args=["1234", 1234], env=["a=b"], log_path="1.log",
                        seccomp_rule_name="1.so", uid=0, gid=0)

        with self.assertRaisesRegex(ValueError, "arg item must be a string"):
            _judger.run(max_cpu_time=1000, max_real_time=2000, max_memory=1000000000,
                        max_process_number=200, max_output_size=10000, exe_path="1.out",
                        input_path="1.in", output_path="1.out", error_path="1.out",
                        args=["1234", None], env=["a=b"], log_path="1.log",
                        seccomp_rule_name="1.so", uid=0, gid=0)

    def test_env_must_be_list(self):
        with self.assertRaisesRegex(ValueError, "env must be a list"):
            _judger.run(max_cpu_time=1000, max_real_time=2000, max_memory=1000000000,
                        max_process_number=200, max_output_size=10000, exe_path="1.out",
                        input_path="1.in", output_path="1.out", error_path="1.out",
                        args=["1234"], env="1234", log_path="1.log",
                        seccomp_rule_name="1.so", uid=0, gid=0)

        with self.assertRaisesRegex(ValueError, "env must be a list"):
            _judger.run(max_cpu_time=1000, max_real_time=2000, max_memory=1000000000,
                        max_process_number=200, max_output_size=10000, exe_path="1.out",
                        input_path="1.in", output_path="1.out", error_path="1.out",
                        args=["1234"], env={"k": "v"}, log_path="1.log",
                        seccomp_rule_name="1.so", uid=0, gid=0)

    def test_env_item_must_be_string(self):
        with self.assertRaisesRegex(ValueError, "env item must be a string"):
            _judger.run(max_cpu_time=1000, max_real_time=2000, max_memory=1000000000,
                        max_process_number=200, max_output_size=10000, exe_path="1.out",
                        input_path="1.in", output_path="1.out", error_path="1.out",
                        args=["1234"], env=["1234", 1234], log_path="1.log",
                        seccomp_rule_name="1.so", uid=0, gid=0)

        with self.assertRaisesRegex(ValueError, "env item must be a string"):
            _judger.run(max_cpu_time=1000, max_real_time=2000, max_memory=1000000000,
                        max_process_number=200, max_output_size=10000, exe_path="1.out",
                        input_path="1.in", output_path="1.out", error_path="1.out",
                        args=["1234"], env=["a=b", None], log_path="1.log",
                        seccomp_rule_name="1.so", uid=0, gid=0)

    def test_seccomp_rule_can_be_none(self):
        _judger.run(max_cpu_time=1000, max_real_time=2000, max_memory=1000000000,
                    max_process_number=200, max_output_size=10000, exe_path="/bin/ls",
                    input_path="/dev/null", output_path="/dev/null", error_path="/dev/null",
                    args=["12344"], env=["a=b"], log_path="/dev/null",
                    seccomp_rule_name="c_cpp", uid=0, gid=0)

        _judger.run(max_cpu_time=1000, max_real_time=2000, max_memory=1000000000,
                    max_process_number=200, max_output_size=10000, exe_path="/bin/ls",
                    input_path="/dev/null", output_path="/dev/null", error_path="/dev/null",
                    args=["12344"], env=["a=b"], log_path="/dev/null",
                    seccomp_rule_name=None, uid=0, gid=0)

    def test_normal(self):
        config = self.config
        config["exe_path"] = self._compile_c("normal.c")
        config["input_path"] = self.make_input("judger_test")
        config["output_path"] = config["error_path"] = self.output_path()
        result = _judger.run(**config)
        output = "judger_test\nHello world"
        self.assertEqual(result["result"], _judger.RESULT_SUCCESS)
        self.assertEqual(output, self.output_content(config["output_path"]))

        config["exe_path"] = self._compile_c("math.c")
        config["input_path"] = "/dev/null"
        config["output_path"] = config["error_path"] = self.output_path()
        result = _judger.run(**config)
        self.assertEqual(result["result"], _judger.RESULT_SUCCESS)
        self.assertEqual("abs 1024", self.output_content(config["output_path"]))

    def test_args(self):
        config = self.config
        config["exe_path"] = self._compile_c("args.c")
        config["args"] = ["test", "hehe", "000"]
        config["output_path"] = config["error_path"] = self.output_path()
        result = _judger.run(**config)
        output = "argv[0]: /tmp/integration/args\nargv[1]: test\nargv[2]: hehe\nargv[3]: 000\n"
        self.assertEqual(result["result"], _judger.RESULT_SUCCESS)
        self.assertEqual(output, self.output_content(config["output_path"]))

    def test_env(self):
        config = self.config
        config["exe_path"] = self._compile_c("env.c")
        config["output_path"] = config["error_path"] = self.output_path()
        result = _judger.run(**config)
        output = "judger_test\njudger\n"
        self.assertEqual(result["result"], _judger.RESULT_SUCCESS)
        self.assertEqual(output, self.output_content(config["output_path"]))

    def test_real_time(self):
        config = self.config
        config["exe_path"] = self._compile_c("sleep.c")
        result = _judger.run(**config)
        self.assertEqual(result["result"], _judger.RESULT_REAL_TIME_LIMIT_EXCEEDED)
        self.assertEqual(result["signal"], signal.SIGKILL)
        self.assertTrue(result["real_time"] >= config["max_real_time"])

    def test_cpu_time(self):
        config = self.config
        config["exe_path"] = self._compile_c("while1.c")
        result = _judger.run(**config)
        self.assertEqual(result["result"], _judger.RESULT_CPU_TIME_LIMIT_EXCEEDED)
        self.assertEqual(result["signal"], signal.SIGKILL)
        self.assertTrue(result["cpu_time"] >= config["max_cpu_time"])

    def test_memory1(self):
        config = self.config
        config["max_memory"] = 64 * 1024 * 1024
        config["exe_path"] = self._compile_c("memory1.c")
        result = _judger.run(**config)
        # malloc succeeded
        self.assertTrue(result["memory"] > 80 * 1024 * 1024)
        self.assertEqual(result["result"], _judger.RESULT_MEMORY_LIMIT_EXCEEDED)

    def test_memory2(self):
        config = self.config
        config["max_memory"] = 64 * 1024 * 1024
        config["exe_path"] = self._compile_c("memory2.c")
        result = _judger.run(**config)
        # malloc failed, return 1
        self.assertEqual(result["exit_code"], 1)
        # malloc failed, so it should use a little memory
        self.assertTrue(result["memory"] < 12 * 1024 * 1024)
        self.assertEqual(result["result"], _judger.RESULT_RUNTIME_ERROR)

    def test_memory3(self):
        config = self.config
        config["max_memory"] = 512 * 1024 * 1024
        config["exe_path"] = self._compile_c("memory3.c")
        result = _judger.run(**config)
        self.assertEqual(result["result"], _judger.RESULT_SUCCESS)
        self.assertTrue(result["memory"] >= 102400000 * 4)

    def test_re1(self):
        config = self.config
        config["exe_path"] = self._compile_c("re1.c")
        result = _judger.run(**config)
        # re1.c return 25
        self.assertEqual(result["exit_code"], 25)

    def test_re2(self):
        config = self.config
        config["exe_path"] = self._compile_c("re2.c")
        result = _judger.run(**config)
        self.assertEqual(result["result"], _judger.RESULT_RUNTIME_ERROR)
        self.assertEqual(result["signal"], signal.SIGSEGV)

    def test_child_proc_cpu_time_limit(self):
        config = self.config
        config["exe_path"] = self._compile_c("child_proc_cpu_time_limit.c")
        result = _judger.run(**config)
        self.assertEqual(result["result"], _judger.RESULT_CPU_TIME_LIMIT_EXCEEDED)

    def test_child_proc_real_time_limit(self):
        config = self.config
        config["exe_path"] = self._compile_c("child_proc_real_time_limit.c")
        result = _judger.run(**config)
        self.assertEqual(result["result"], _judger.RESULT_REAL_TIME_LIMIT_EXCEEDED)
        self.assertEqual(result["signal"], signal.SIGKILL)

    def test_stdout_and_stderr(self):
        config = self.config
        config["exe_path"] = self._compile_c("stdout_stderr.c")
        config["output_path"] = config["error_path"] = self.output_path()
        result = _judger.run(**config)
        self.assertEqual(result["result"], _judger.RESULT_SUCCESS)
        output = "stderr\n+++++++++++++++\n--------------\nstdout\n"
        self.assertEqual(output, self.output_content(config["output_path"]))

    def test_uid_and_gid(self):
        config = self.config
        config["exe_path"] = self._compile_c("uid_gid.c")
        config["output_path"] = config["error_path"] = self.output_path()
        config["uid"] = 65534
        config["gid"] = 65534
        result = _judger.run(**config)
        self.assertEqual(result["result"], _judger.RESULT_SUCCESS)
        output = "uid=65534(nobody) gid=65534(nogroup) groups=65534(nogroup)\nuid 65534\ngid 65534\n"
        self.assertEqual(output, self.output_content(config["output_path"]))

    def test_gcc_random(self):
        config = self.config
        config["exe_path"] = "/usr/bin/gcc"
        config["args"] = ["../test_src/integration/gcc_random.c",
                          "-o", os.path.join(self.workspace, "gcc_random")]
        result = _judger.run(**config)
        self.assertEqual(result["result"], _judger.RESULT_CPU_TIME_LIMIT_EXCEEDED)
        self.assertTrue(result["cpu_time"] >= 1950)
        self.assertTrue(result["real_time"] >= 1950)

    def test_cpp_meta(self):
        config = self.config
        config["exe_path"] = "/usr/bin/g++"
        config["max_memory"] = 1024 * 1024 * 1024
        config["args"] = ["../test_src/integration/cpp_meta.cpp",
                          "-o", os.path.join(self.workspace, "cpp_meta")]
        result = _judger.run(**config)
        self.assertEqual(result["result"], _judger.RESULT_CPU_TIME_LIMIT_EXCEEDED)
        self.assertTrue(result["cpu_time"] >= 1950)
        self.assertTrue(result["real_time"] >= 1950)

    def test_output_size(self):
        config = self.config
        config["exe_path"] = self._compile_c("output_size.c")
        config["max_output_size"] = 1000 * 10
        result = _judger.run(**config)
        self.assertEqual(result["exit_code"], 2)
