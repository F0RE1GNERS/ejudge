import shutil
from os import path, makedirs, chown, remove

from config.config import COMPILER_GROUP_GID, COMPILER_USER_UID, RUN_GROUP_GID, RUN_USER_UID
from config.config import LANGUAGE_CONFIG, SUB_BASE, USUAL_READ_SIZE, ENV, COMPILE_TIME_FACTOR, REAL_TIME_FACTOR
from config.config import Verdict
from core.exception import *
from core.util import format, random_string
from sandbox.sandbox import Sandbox


class Submission(object):

    def __init__(self, fingerprint, code, lang, permanent=False):
        self.workspace = path.join(SUB_BASE, fingerprint)
        self.lang = lang
        # Using [] instead of .get() to throw KeyError in case of bad configuration
        language_config = LANGUAGE_CONFIG[lang]
        self.code_file = path.join(self.workspace, language_config['code_file'])
        object_file_name = language_config.get('object_file', 'foo')
        path_config = {
            'exe_path': path.join(self.workspace, object_file_name),
            'code_path': self.code_file,
            'workspace': self.workspace,
            'max_memory': '{max_memory}'
        }

        old_submission = True
        if not path.exists(self.workspace):
            # This is a new submission
            makedirs(self.workspace)
            chown(self.workspace, COMPILER_USER_UID, COMPILER_GROUP_GID)
            with open(self.code_file, 'w') as fs:
                fs.write(code)
            with open(path.join(self.workspace, 'LANG'), 'w') as fs:
                fs.write(lang)
            old_submission = False

        if language_config['type'] == 'compiler' and not old_submission:
            self.to_compile = True
            self.compiler_file = format(language_config['compiler_file'], **path_config)
            self.compiler_args = format(language_config.get('compiler_args', ''), as_list=True, **path_config)
        else:
            self.to_compile = False
        self.execute_file = format(language_config['execute_file'], **path_config)
        self.execute_args = language_config.get('execute_args', '')
        self.execute_args_unsafe = language_config.get('execute_args_unsafe', self.execute_args)
        self.execute_args = format(self.execute_args, as_list=True, **path_config)
        self.execute_args_unsafe = format(self.execute_args_unsafe, as_list=True, **path_config)

        self.env = ENV.copy()
        self.env.update(language_config.get('env', {}))
        self.memory_flag = language_config.get('memory_flag', '') # when memory info shows up in the command or env...
        self.seccomp_rule = language_config.get('seccomp_rule', 'general')

        self.permanent = permanent

    def clean(self, force=False):
        """
        Remember to call clean when you leave!

        :param force: to clean whether it is permanent or not
        """
        if not self.permanent or force:
            shutil.rmtree(self.workspace, ignore_errors=True)

    @classmethod
    def fromExistingFingerprint(cls, fingerprint):
        workspace = path.join(SUB_BASE, fingerprint)
        if not path.exists(workspace):
            raise FileNotFoundError("Fingerprint does not exist")
        with open(path.join(workspace, 'LANG')) as fs:
            lang = fs.read()
        return cls(fingerprint, '', lang, True)

    def compile(self, max_time):
        error_path = path.join(self.workspace, "compiler_output_%s" % random_string())
        sandbox = Sandbox(self.compiler_file, self.compiler_args,
                          stdin=self.code_file,
                          stdout=error_path,
                          stderr=error_path,
                          max_time=max_time,
                          uid=COMPILER_USER_UID,
                          gid=COMPILER_GROUP_GID,
                          env=self.env,
                          )
        result = sandbox.run()
        if result.verdict != Verdict.ACCEPTED:
            error_message = self.get_message_from_file(error_path, read_size=-1)
            if not error_message:
                if result.verdict == Verdict.TIME_LIMIT_EXCEEDED:
                    error_message = 'Time limit exceeded when compiling'
                elif result.verdict == Verdict.MEMORY_LIMIT_EXCEEDED:
                    error_message = 'Memory limit exceeded when compiling'
                else:
                    error_message = 'Something is wrong, but, em, nothing is reported'
            raise CompileError(error_message)
        self.to_compile = False

    def get_message_from_file(self, result_file, read_size=USUAL_READ_SIZE, cleanup=False):
        try:
            with open(result_file, 'r') as result_fs:
                if read_size > 0:
                    message = result_fs.read(USUAL_READ_SIZE)
                else: message = result_fs.read()   # unlimited
            if cleanup and path.exists(result_file):
                remove(result_file)
            return message
        except:
            return ''

    def make_a_file_to_write(self):
        mpath = path.join(self.workspace, "output_" + random_string())
        open(mpath, 'w').close()
        chown(mpath, COMPILER_USER_UID, COMPILER_GROUP_GID)
        return mpath

    def run(self, stdin, stdout, stderr, max_time, max_memory, **kwargs):
        """
        A trusted program is usually an interactor or a checker.

        It's recommended to use multiprocessing to "run".

        :param stdin:
        :param stdout:
        :param stderr:
        :param max_time: in seconds
        :param max_memory: in megabytes
        :param max_real_time (optional): in seconds, default is max_time * 3
        :param max_output_size (optional): in megabytes, default is 256
        :param trusted: when program is trusted, it will run with root privilege and without seccomp rule
        :param command_line_args: additional args from command line
        :return:
        """
        max_real_time = kwargs.get('max_real_time', max_time * REAL_TIME_FACTOR)
        max_output_size = kwargs.get('max_output_size', 256)
        trusted = kwargs.get('trusted', False)
        command_line_args = kwargs.get('command_line_args', [])

        if trusted:
            uid, gid = COMPILER_USER_UID, COMPILER_GROUP_GID
            seccomp_rule = None
            execute_args = self.execute_args_unsafe.copy()
        else:
            uid, gid = RUN_USER_UID, RUN_GROUP_GID
            seccomp_rule = self.seccomp_rule  # general by default
            execute_args = self.execute_args.copy()

        execute_args.extend(command_line_args)

        if self.memory_flag == 'MB' and max_memory > 0:
            execute_args = format(execute_args, as_list=True, max_memory=int(max_memory))
            self.env["MONO_GC_PARAMS"] = 'max-heap-size=%dM' % int(max_memory)
            max_memory = -1

        if self.to_compile:
            self.compile(max(max_time * COMPILE_TIME_FACTOR, 10))
        sandbox = Sandbox(self.execute_file, execute_args,
                          stdin=stdin, stdout=stdout, stderr=stderr,
                          max_time=max_time, max_real_time=max_real_time, max_memory=max_memory,
                          max_output_size=max_output_size, uid=uid, gid=gid, seccomp_rule=seccomp_rule,
                          env=self.env)
        result = sandbox.run()
        return result
