import _judger
from config import *
from .languages import LANGUAGE_SETTINGS
from .utils import read_partial_data_from_file


# For celery usage

@celery.task
def _celery_judger_run(args):
    # args is dict
    return _judger.run(**args)


# This class is meant to deal with all difficulties when it comes to programs.
# If initiated properly, you can simply use compile() and run() to run the program.

class Program(object):

    def __init__(self, code, lang, settings):

        # About this program
        self.code = code
        self.lang = lang
        self.settings = settings

        self.language_settings = LANGUAGE_SETTINGS[self.lang]
        self.run_dir = self.settings.round_dir

        # Ready to make some files
        self.src_name = self.language_settings['src_name']
        self.exe_name = self.language_settings['exe_name']
        self.src_path = os.path.join(self.run_dir, self.src_name)
        self.exe_path = os.path.join(self.run_dir, self.exe_name)

        # Compilation related
        self.compile_out_path = os.path.join(self.run_dir, 'compile.out')
        self.compile_log_path = os.path.join(self.run_dir, 'compile.log')
        self.compile_cmd = self.language_settings['compile_cmd'].format(
            src_path=self.src_path,
            exe_path=self.exe_path,
        ).split(' ')

        # Running related
        self.input_path = os.path.join(self.run_dir, 'in')
        self.output_path = os.path.join(self.run_dir, 'out')
        self.log_path = os.path.join(self.run_dir, 'run.log')
        self.seccomp_rule_name = self.language_settings['seccomp_rule']
        self.run_cmd = self.language_settings['exe_cmd'].format(
            exe_path=self.exe_path,
            # The following is for Java
            exe_dir=self.run_dir,
            exe_name=self.exe_name,
            max_memory=self.settings.max_memory
        ).split(' ')

    def compile(self):
        with open(self.src_path, 'w', encoding='utf-8') as f:
            f.write(self.code)
        response = {"code": 0, "message": ""}
        try:
            result = self._compile()
            # print("Compile Result of " + self.lang + ": " + str(result))
            if result["result"] != _judger.RESULT_SUCCESS:
                response['code'] = COMPILE_ERROR
                if os.path.exists(self.compile_out_path):
                    response['message'] = read_partial_data_from_file(self.compile_out_path)
                if response['message'] == '' and os.path.exists(self.compile_log_path):
                    response['message'] = read_partial_data_from_file(self.compile_log_path)
                response['message'] = response['message'].replace(self.run_dir, '~')
        except:
            response['code'] = COMPILE_ERROR
            response['message'] = 'N/A'
        return response

    def run(self):
        # Prevent input errors
        if not os.path.exists(self.input_path):
            open(self.input_path, "w").close()
        result = self._run()

        # Case java: time -= 150, memory N/A (currently)
        if self.lang == 'java':
            result['memory'] = 0
            result['cpu_time'] = max(result['cpu_time'] - 150, 0)

        # A fake time limit / memory limit exceeded
        if result['cpu_time'] > self.settings.max_time or result['result'] == CPU_TIME_LIMIT_EXCEEDED \
                or result['result'] == REAL_TIME_LIMIT_EXCEEDED:
            result['cpu_time'] = self.settings.max_time
            result['result'] = CPU_TIME_LIMIT_EXCEEDED
        if result['result'] == MEMORY_LIMIT_EXCEEDED:
            result['memory'] = self.settings.max_memory

        # print("Running Result of " + self.lang + ": " + str(result))
        return result

    def _compile(self):
        # return _celery_judger_run(self._compile_args())
        return _celery_judger_run.delay(self._compile_args()).get()

    def _run(self):
        # return _celery_judger_run(self._run_args())
        return _celery_judger_run.delay(self._run_args()).get()

    def _compile_args(self):
        return dict(
            max_cpu_time=5000,
            max_real_time=10000,
            max_memory=-1,
            max_output_size=128 * 1024 * 1024,
            max_process_number=_judger.UNLIMITED,
            exe_path=self.compile_cmd[0],
            # /dev/null is best, but in some system, this will call ioctl system call
            input_path=self.src_path,
            output_path=self.compile_out_path,
            error_path=self.compile_out_path,
            args=self.compile_cmd[1:],
            env=[("PATH=" + os.getenv("PATH"))] + self.language_settings['env'],
            log_path=self.compile_log_path,
            seccomp_rule_name=None,
            uid=COMPILER_USER_UID,  # not safe?
            gid=COMPILER_GROUP_GID
        )

    def _run_args(self):
        return dict(
            max_cpu_time=self.settings.max_time,
            max_real_time=self.settings.max_time * 5,
            max_memory=self.settings.max_memory * 1048576 if self.lang != 'java' else -1,
            max_output_size=128 * 1024 * 1024,
            max_process_number=_judger.UNLIMITED,
            exe_path=self.run_cmd[0],
            input_path=self.input_path,
            output_path=self.output_path,
            error_path=self.log_path,
            args=self.run_cmd[1:],
            env=[("PATH=" + os.getenv("PATH"))] + self.language_settings['env'],
            log_path=self.log_path,
            seccomp_rule_name=self.seccomp_rule_name,
            uid=RUN_USER_UID,
            gid=RUN_GROUP_GID
        )
