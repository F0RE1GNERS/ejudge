"""

    Basically, the programs submitted are called submissions.

    There are certain "submissions", which are submitted by judges, such as generators, checkers, interactors...
    These submissions are trusted and of certain usage.
    This file implements certain judge "submissions" and the way of running them.

    The args are same as the famous testlib.h, which is the following:

    Check, using testlib running format:
      check.exe <Input_File> <Output_File> <Answer_File> [<Result_File>],
    If result file is specified it will contain results.

    Validator, using testlib running format:
      validator.exe < input.txt,
    It will return non-zero exit code and writes message to standard output.

    Generator, using testlib running format:
      gen.exe [parameter-1] [parameter-2] [... paramerter-n]
    You can write generated test(s) into standard output or into the file(s).

    Interactor, using testlib running format:
      interactor.exe <Input_File> <Output_File> [<Answer_File> [<Result_File>]],
    Reads test from inf (mapped to args[1]), writes result to tout (mapped to argv[2],
    can be judged by checker later), reads program output from ouf (mapped to stdin),
    writes output to program via stdout (use cout, printf, etc).

    Note that in both checker and interactor, our implementation does not support variable-length args after Result_File.

    Just like submissions return Sandbox.Result directly, trusted submissions return TrustedSubmission.Result.
    The result contains two arguments, namely:
    - verdict: directly defined in config.config, can be used as the final verdict
    - message: compile error message and, most importantly, result file content (first 512 bytes)

"""

from core.submission import Submission
from core.exception import CompileError
from config.config import LIB_BASE, Verdict, DEVNULL, COMPILE_TIME_FACTOR, REAL_TIME_FACTOR


class TrustedSubmission(Submission):

    class Result:

        def __init__(self, verdict, message):
            self.verdict = verdict
            self.message = message

        def __repr__(self):
            return "TrustedSubmission.Result object: " + str(self.__dict__)

    def run(self, stdin, stdout, stderr, max_time, max_memory, **kwargs):
        kwargs.pop('trusted', None)
        return super().run(stdin, stdout, stderr, max_time, max_memory, trusted=True, **kwargs)

    def get_verdict_from_test_result(self, checker_result):
        """
        :param checker_result: a Sandbox.Result directly returned from checker running
        :return: an integer, one of the verdict
        """
        if checker_result.verdict != Verdict.ACCEPTED:
            # The following follows testlib's convention
            if checker_result.exit_code == 3:
                return Verdict.JUDGE_ERROR
            if checker_result.exit_code == 7:
                return Verdict.POINT
            if checker_result.verdict != Verdict.RUNTIME_ERROR:
                return checker_result.verdict
            return Verdict.WRONG_ANSWER
        return Verdict.ACCEPTED


class Checker(TrustedSubmission):

    def check(self, input_file, output_file, answer_file, max_time, max_memory):
        result_file = self.make_a_file_to_write()
        try:
            checker_result = self.run(DEVNULL, DEVNULL, DEVNULL, max_time, max_memory,
                                      command_line_args=[input_file, output_file, answer_file, result_file])
            message = self.get_message_from_file(result_file, cleanup=True)
            verdict = self.get_verdict_from_test_result(checker_result)
            return Checker.Result(verdict, message)
        except CompileError as e:
            return Checker.Result(Verdict.JUDGE_ERROR, e.detail)


class Interactor(TrustedSubmission):

    def interact(self, pipe_for_stdin, pipe_for_stdout, input_file, output_file, answer_file, max_time, max_memory, queue=None):
        """

        :param queue: queue is for putting the result of function since interactor and submission need to be run simultaneously
        :return:
        """
        result_file = self.make_a_file_to_write()
        try:
            interactor_result = self.run(pipe_for_stdin, pipe_for_stdout, DEVNULL, max_time, max_memory,
                                         command_line_args=[input_file, output_file, answer_file, result_file])
            message = self.get_message_from_file(result_file, cleanup=True)
            verdict = self.get_verdict_from_test_result(interactor_result)
            return_val = Interactor.Result(verdict, message)
        except CompileError as e:
            return_val = Verdict.JUDGE_ERROR, e.detail
        if queue:
            queue.put(return_val)
        return return_val


class Generator(TrustedSubmission):

    def generate(self, output_file, max_time, max_memory, command_line_args):
        try:
            generator_result = self.run(DEVNULL, output_file, DEVNULL, max_time, max_memory,
                                        command_line_args=command_line_args)
            verdict = self.get_verdict_from_test_result(generator_result)
            return Generator.Result(verdict, '')
        except CompileError as e:
            return Generator.Result(Verdict.JUDGE_ERROR, e.detail)


class Validator(TrustedSubmission):

    def validate(self, validate_input, max_time, max_memory):
        result_file = self.make_a_file_to_write()
        try:
            validate_result = self.run(validate_input, result_file, DEVNULL, max_time, max_memory)
            message = self.get_message_from_file(result_file, cleanup=True)
            verdict = self.get_verdict_from_test_result(validate_result)
            return Validator.Result(verdict, message)
        except CompileError as e:
            return Validator.Result(Verdict.JUDGE_ERROR, e.detail)
