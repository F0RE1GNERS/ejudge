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
import base64

from config.config import DEVNULL, Verdict, COMPILE_TIME_FACTOR, REAL_TIME_FACTOR, USUAL_READ_SIZE
from core.util import get_signal_name, serialize_sandbox_result
from sandbox.sandbox import Sandbox


class CaseRunner(object):

    def __init__(self, submission, checker, max_time, max_memory, report_file=None):
        self.submission = submission
        self.checker = checker
        self.max_time = max_time
        self.max_memory = max_memory
        self.report_file = report_file

    def initiate_case(self, case):
        self.case = case
        self.case.check_validity()

    def run(self, case):
        self.initiate_case(case)

        running_output = self.submission.make_a_file_to_write()
        running_stderr = self.submission.make_a_file_to_write()
        running_result = self.submission.run(self.case.input_file, running_output, running_stderr,
                                             self.max_time, self.max_memory)

        if running_result.verdict != Verdict.ACCEPTED:
            # If sub fails to run, the result is final
            result = self.running_fail_result(running_result)
            checker_message = result.get('message', '')  # message is kept
        else:
            result = self.do_check(running_output, running_result)
            checker_message = result.pop('message', '')  # message is popped
        if self.report_file:
            self.write_report(running_output, running_stderr, running_result, result, checker_message)
        return result

    def read_output_as_b64(self, file):
        try:
            with open(file, 'r') as handler:
                txt = handler.read(USUAL_READ_SIZE)
                if handler.read(1):
                    txt += '...'
        except:
            txt = '...'
        return self.encode_as_b64(txt)

    def encode_as_b64(self, txt):
        return base64.b64encode(txt.encode()).decode()

    def running_fail_result(self, running_result):
        assert running_result.verdict != Verdict.ACCEPTED
        result = dict()
        result['verdict'] = running_result.verdict
        result['time'] = running_result.time
        if running_result.verdict == Verdict.RUNTIME_ERROR:
            result['message'] = get_signal_name(running_result.signal)
        return result

    def do_check(self, running_output, running_result):
        result = dict()
        checker_result = self.checker.check(self.case.input_file, running_output, self.case.output_file,
                                            self.max_time, self.max_memory)
        result['verdict'] = checker_result.verdict
        result['message'] = checker_result.message
        result['time'] = running_result.time
        return result

    def write_report(self, running_output, running_stderr, running_result, final_result, checker_message):
        input_b64 = self.read_output_as_b64(self.case.input_file)
        output_b64 = self.read_output_as_b64(running_output)
        err_b64 = self.read_output_as_b64(running_stderr)
        answer_b64 = self.read_output_as_b64(self.case.output_file)
        checker_b64 = self.encode_as_b64(checker_message)
        self.report_file.write('time: %.3fs, estimate memory: %.3f MB, exit code: %d, verdict: %s|%s|%s|%s|%s|%s\n' % (
            running_result.time, running_result.memory, running_result.exit_code, final_result['verdict'].name,
            input_b64, output_b64, err_b64, answer_b64, checker_b64
        ))


class InteractiveRunner(CaseRunner):

    def __init__(self, submission, interactor, checker, max_time, max_memory, report_file=None):
        super().__init__(submission, checker, max_time, max_memory, report_file=report_file)
        self.interactor = interactor

    def run(self, case):
        self.initiate_case(case)

        # prevent compile waiting time
        if self.interactor.to_compile:
            self.interactor.compile(self.interactor.compilation_time_limit)
        if self.submission.to_compile:
            self.submission.compile(self.submission.compilation_time_limit)

        running_output = self.submission.make_a_file_to_write()
        running_stderr = self.submission.make_a_file_to_write()

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
        running_result = self.submission.run(r, w, running_stderr, self.max_time, self.max_memory)
        interactor_result = pickle.load(r_report)
        r.close()
        w.close()
        r_report.close()

        checker_message = ''
        if running_result.verdict != Verdict.ACCEPTED:
            result = self.running_fail_result(running_result)
            checker_message = result.get('message', '')
        elif interactor_result.verdict != Verdict.ACCEPTED:
            result = {'verdict': interactor_result.verdict}
        else:
            result =  self.do_check(running_output, running_result)
            checker_message = result.pop('message', '')
        if self.report_file:
            self.write_report(running_output, running_stderr, running_result, result, checker_message)
        return result
