import _judger
import uuid
from config import *
from .languages import LANGUAGE_SETTINGS
from .utils import get_language


# For celery usage

@celery.task
def _celery_judger_run(args):
    # args is dict
    return _judger.run(**args)


# This class is meant to deal with all difficulties when it comes to programs.
# If initiated properly, you can simply use compile() and run() to run the program.

class Program(object):

    def __init__(self, submission, config, round_id):

        # About this program
        self.submission_id = submission.get('id', 0)
        self.lang = submission.get('lang', 'cpp')
        self.code = submission.get('code', '')
        if self.lang == 'builtin':  # built-in program
            self.lang = 'python'
            try:
                code_path = os.path.normpath(os.path.join(INCLUDE_DIR, self.code))
                self.lang = get_language(code_path)
                if not code_path.startswith(INCLUDE_DIR):
                    raise OSError
                self.code = open(code_path, 'r').read()
            except OSError:
                self.code = ''

        self.language_settings = LANGUAGE_SETTINGS[self.lang]
        self.score = 0
        self.sum_score = 0

        # Restrictive settings
        self.round_id = round_id
        self.problem_id = config.get('problem_id')
        self.max_time = config.get('max_time', 1000)
        self.max_memory = config.get('max_memory', 256)
        self.max_sum_time = config.get('max_sum_time', 10000)

        self.sum_time = 0
        # if you call it max, it is ok.
        self.sum_memory = 0

        # Deal with directories
        self.submission_dir = os.path.join(SUBMISSION_DIR, str(self.submission_id))
        self.round_dir = os.path.join(ROUND_DIR, str(self.round_id))
        if not os.path.exists(self.round_dir):
            os.mkdir(self.round_dir)
        if not os.path.exists(self.submission_dir):
            os.mkdir(self.submission_dir)
        os.chown(self.round_dir, COMPILER_USER_UID, COMPILER_GROUP_GID)
        os.chown(self.submission_dir, COMPILER_USER_UID, COMPILER_GROUP_GID)

        # Ready to make some files
        self.src_name = self.language_settings['src_name']
        self.exe_name = self.language_settings['exe_name']
        self.src_path = os.path.join(self.submission_dir, self.src_name)
        self.exe_path = os.path.join(self.submission_dir, self.exe_name)

        # Compilation related
        self.compile_out_path = os.path.join(self.submission_dir, 'compile.out')
        self.compile_log_path = os.path.join(self.submission_dir, 'compile.log')
        self.compile_cmd = self.language_settings['compile_cmd'].format(
            src_path=self.src_path,
            exe_path=self.exe_path,
        ).split(' ')

        # Running related
        self.input_path = os.path.join(self.round_dir, 'in')
        self.output_path = os.path.join(self.round_dir, 'out')
        self.log_path = os.path.join(self.round_dir, 'run.log')
        self.seccomp_rule_name = self.language_settings['seccomp_rule']
        self.run_cmd = self.language_settings['exe_cmd'].format(
            exe_path=self.exe_path,
            # The following is for Java
            exe_dir=self.submission_dir,
            exe_name=self.exe_name,
            max_memory=self.max_memory
        ).split(' ')

    def compile(self):
        with open(self.src_path, 'w') as f:
            f.write(self.code)
        result = self._compile()
        print("Compile Result of " + self.lang + ": " + str(result))
        if result["result"] != _judger.RESULT_SUCCESS:
            if not os.path.exists(self.compile_out_path):
                with open(self.compile_out_path, 'w') as f:
                    f.write("Error Code = " + result['error'])
            return False
        return True

    def run(self):
        # Prevent input errors
        if not os.path.exists(self.input_path):
            open(self.input_path, "w").close()
        result = self._run()

        # TODO: solve java memory problem, maybe a new sandbox?
        if self.lang == 'java':
            result['memory'] = 0

        # Sum time
        self.sum_time += result['cpu_time']
        self.sum_memory = max(self.sum_memory, result['memory'])
        if self.sum_time > self.max_sum_time > 0:
            result['result'] = SUM_TIME_LIMIT_EXCEEDED

        # A fake one
        if result['result'] == CPU_TIME_LIMIT_EXCEEDED or result['result'] == REAL_TIME_LIMIT_EXCEEDED:
            result['time'] = self.max_time
        if result['result'] == MEMORY_LIMIT_EXCEEDED:
            result['memory'] = self.max_memory

        print("Running Result of " + self.lang + ": " + str(result))
        return result

    def _compile(self):
        return _celery_judger_run.delay(self._compile_args()).get()

    def _run(self):
        return _celery_judger_run.delay(self._run_args()).get()

    def _compile_args(self):
        return dict(
            max_cpu_time=600 * 1000,
            max_real_time=3000 * 1000,
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
            max_cpu_time=self.max_time,
            max_real_time=self.max_time * 10,
            max_memory=self.max_memory * 1048576 if self.lang != 'java' else -1,
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
