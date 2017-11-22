"""
    Runner is what comes in when running
    When runner is run, a Multiprocessing pool is recommended.

    Runner returns result as a dict.
    - Only when the result is ACCEPTED or WRONG_ANSWER, will the dict contains "time"
    - The dict will contain "message" when it feels necessary
    - When submission fails to compile, a CompileError is raised; when trusted submission fails to compile, JUDGE_ERROR is returned.

"""

import pickle
from os import fork, pipe, _exit, close, fdopen
from enum import Enum
import base64

from config.config import DEVNULL, Verdict, COMPILE_TIME_FACTOR, REAL_TIME_FACTOR, USUAL_READ_SIZE
from core.util import get_signal_name, serialize_sandbox_result
from sandbox.sandbox import Sandbox


class RunnerResultType(Enum):
    FINAL = 0
    OUTPUT = 1
    SUB_SANDBOX_RESULT = 2
    CHECKER_RESULT = 3
    INTERACTOR_RESULT = 4


class CaseRunner(object):

    def __init__(self, submission, checker, max_time, max_memory):
        self.submission = submission
        self.checker = checker
        self.max_time = max_time
        self.max_memory = max_memory

    def initiate_case(self, case):
        self.case = case
        self.case.check_validity()

    def run(self, case, result_type=RunnerResultType.FINAL):
        self.initiate_case(case)

        running_output = self.submission.make_a_file_to_write()
        running_result = self.submission.run(self.case.input_file, running_output, DEVNULL,
                                             self.max_time, self.max_memory)
        if result_type == RunnerResultType.OUTPUT:
            return {'output': self.read_output_as_b64(running_output)}
        elif result_type == RunnerResultType.SUB_SANDBOX_RESULT:
            return serialize_sandbox_result(running_result)

        if running_result.verdict != Verdict.ACCEPTED:
            # If sub fails to run, the result is final
            return self.running_fail_result(running_result)
        else:
            return self.do_check(running_output, running_result, result_type == RunnerResultType.CHECKER_RESULT)

    def read_output_as_b64(self, file):
        return base64.b64encode(open(file, 'rb').read()).decode()

    def running_fail_result(self, running_result):
        assert running_result.verdict != Verdict.ACCEPTED
        result = dict()
        result['verdict'] = running_result.verdict
        if running_result.verdict == Verdict.RUNTIME_ERROR:
            result['message'] = get_signal_name(running_result.signal)
        return result

    def do_check(self, running_output, running_result, get_message=False):
        result = dict()
        checker_result = self.checker.check(self.case.input_file, running_output, self.case.output_file,
                                            self.max_time, self.max_memory)
        result['verdict'] = checker_result.verdict
        if get_message:
            result['message'] = checker_result.message
        if checker_result.verdict == Verdict.ACCEPTED:
            result['time'] = running_result.time
        return result


class InteractiveRunner(CaseRunner):

    def __init__(self, submission, interactor, checker, max_time, max_memory):
        super().__init__(submission, checker, max_time, max_memory)
        self.interactor = interactor

    def run(self, case, result_type=RunnerResultType.FINAL):
        self.initiate_case(case)

        # prevent compile waiting time
        if self.interactor.to_compile:
            self.interactor.compile(min(self.max_time * COMPILE_TIME_FACTOR, 10))
        if self.submission.to_compile:
            self.submission.compile(min(self.max_time * COMPILE_TIME_FACTOR, 10))

        running_output = self.submission.make_a_file_to_write()

        r1, w1 = pipe()  # interactor read, submission write
        r2, w2 = pipe()  # submission read, interactor write
        r_report, w_report = pipe()  # main process read, interactor report

        interactor_pid = fork()
        if interactor_pid == 0:
            # This is the child process for interactor running usage
            close(w1)
            close(r2)
            close(r_report)
            r, w = fdopen(r1, 'r'), fdopen(w2, 'w')
            w_report = fdopen(w_report, 'wb')
            interactor_result = self.interactor.interact(r, w, self.case.input_file, running_output, self.case.output_file,
                                                         self.max_time, self.max_memory)
            pickle.dump(interactor_result, w_report)
            r.close()
            w.close()
            w_report.close()
            _exit(0)

        # This is the parent process for submission
        close(r1)
        close(w2)
        close(w_report)
        r, w = fdopen(r2, 'r'), fdopen(w1, 'w')
        r_report = fdopen(r_report, 'rb')
        running_result = self.submission.run(r, w, DEVNULL, self.max_time, self.max_memory)
        interactor_result = pickle.load(r_report)
        r.close()
        w.close()
        r_report.close()

        if result_type == RunnerResultType.OUTPUT:
            return {'output': self.read_output_as_b64(running_output)}
        elif result_type == RunnerResultType.SUB_SANDBOX_RESULT:
            return serialize_sandbox_result(running_result)
        elif result_type == RunnerResultType.INTERACTOR_RESULT:
            return {'verdict': interactor_result.verdict, 'message': interactor_result.message}

        if running_result.verdict != Verdict.ACCEPTED:
            return self.running_fail_result(running_result)
        elif interactor_result.verdict != Verdict.ACCEPTED:
            return {'verdict': interactor_result.verdict}
        else:
            return self.do_check(running_output, running_result, result_type == RunnerResultType.CHECKER_RESULT)
