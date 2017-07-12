from core.case import Case
from core.runner import CaseRunner, InteractiveRunner
from core.submission import Submission
from core.judge import Checker, Interactor
from core.exception import CompileError
from config.config import Verdict
from tests.test_base import TestBase
import logging

logging.basicConfig(level=logging.INFO)


class RunnerTest(TestBase):

    def setUp(self):
        self.workspace = '/tmp/runner'
        super(RunnerTest, self).setUp()

    def test_aplusb(self):
        code = open('./submission/aplusb.cpp').read()
        checker_code = open('./submission/ncmp.cpp').read()
        case = Case(self.rand_str(True))
        case.write_input_binary(b"1\n2\n")
        case.write_output_binary(b"3\n")
        checker = Checker(self.rand_str(True), checker_code, 'cpp')
        submission = Submission(self.rand_str(True), code, 'cpp')
        case_runner = CaseRunner(submission, checker, 1, 128)
        result = case_runner.run(case)
        self.assertEqual(result['verdict'], Verdict.ACCEPTED)

    def test_aplub_wrong(self):
        code = open('./submission/aplusb.cpp').read()
        checker_code = open('./submission/ncmp.cpp').read()
        case = Case(self.rand_str(True))
        case.write_input_binary(b"1\n2\n")
        case.write_output_binary(b"4\n")
        checker = Checker(self.rand_str(True), checker_code, 'cpp')
        submission = Submission(self.rand_str(True), code, 'cpp')
        case_runner = CaseRunner(submission, checker, 1, 128)
        result = case_runner.run(case)
        self.assertEqual(result['verdict'], Verdict.WRONG_ANSWER)

    def test_aplusb_judge_fail(self):
        code = open('./submission/aplusb.cpp').read()
        checker_code = open('./submission/ncmp.cpp').read()
        case = Case(self.rand_str(True))
        case.write_input_binary(b"1\n2\n")
        case.write_output_binary(b"4\n")
        checker = Checker(self.rand_str(True), checker_code, 'c')
        submission = Submission(self.rand_str(True), code, 'cpp')
        case_runner = CaseRunner(submission, checker, 1, 128)
        result = case_runner.run(case)
        self.assertEqual(result['verdict'], Verdict.JUDGE_ERROR)

    def test_aplusb_compile_error(self):
        with self.assertRaises(CompileError):
            code = open('./submission/aplusb.cpp').read()
            checker_code = open('./submission/ncmp.cpp').read()
            case = Case(self.rand_str(True))
            case.write_input_binary(b"1\n2\n")
            case.write_output_binary(b"4\n")
            checker = Checker(self.rand_str(True), checker_code, 'c')
            submission = Submission(self.rand_str(True), code, 'c')
            case_runner = CaseRunner(submission, checker, 1, 128)
            case_runner.run(case)

    def test_interactive_normal(self):
        code = open('./interact/a-plus-b.py').read()
        checker_code = open('./submission/ncmp.cpp').read()
        interacter_code = open('./interact/interactor-a-plus-b.cpp').read()
        case = Case(self.rand_str(True))
        case.write_input_binary(open('./interact/a-plus-b-input.txt', 'rb').read())
        case.write_output_binary(open('./interact/a-plus-b-output.txt', 'rb').read())
        checker = Checker(self.rand_str(True), checker_code, 'cpp')
        interactor = Interactor(self.rand_str(True), interacter_code, 'cpp')
        submission = Submission(self.rand_str(True), code, 'python')
        case_runner = InteractiveRunner(submission, interactor, checker, 1, 128)
        result = case_runner.run(case)
        self.assertEqual(result['verdict'], Verdict.ACCEPTED)

    def test_interactive_wrong_answer(self):
        code = open('./interact/a-plus-b.py').read()
        checker_code = open('./submission/ncmp.cpp').read()
        interacter_code = open('./interact/interactor-a-plus-b.cpp').read()
        case = Case(self.rand_str(True))
        case.write_input_binary(open('./interact/a-plus-b-input.txt', 'rb').read())
        case.write_output_binary(open('./interact/a-plus-b-output-wrong.txt', 'rb').read())
        checker = Checker(self.rand_str(True), checker_code, 'cpp')
        interactor = Interactor(self.rand_str(True), interacter_code, 'cpp')
        submission = Submission(self.rand_str(True), code, 'python')
        case_runner = InteractiveRunner(submission, interactor, checker, 1, 128)
        result = case_runner.run(case)
        self.assertEqual(result['verdict'], Verdict.WRONG_ANSWER)

    def test_interactive_bad_submission(self):
        code = open('./interact/a-plus-b-nonstop.py').read()
        checker_code = open('./submission/ncmp.cpp').read()
        interacter_code = open('./interact/interactor-a-plus-b.cpp').read()
        case = Case(self.rand_str(True))
        case.write_input_binary(open('./interact/a-plus-b-input.txt', 'rb').read())
        case.write_output_binary(open('./interact/a-plus-b-output.txt', 'rb').read())
        checker = Checker(self.rand_str(True), checker_code, 'cpp')
        interactor = Interactor(self.rand_str(True), interacter_code, 'cpp')
        submission = Submission(self.rand_str(True), code, 'python')
        case_runner = InteractiveRunner(submission, interactor, checker, 1, 128)
        result = case_runner.run(case)
        self.assertEqual(result['verdict'], Verdict.RUNTIME_ERROR)

    def test_interactive_bad_interactor(self):
        code = open('./interact/a-plus-b.py').read()
        checker_code = open('./submission/ncmp.cpp').read()
        interacter_code = open('./interact/interactor-a-plus-b-nonstop.cpp').read()
        case = Case(self.rand_str(True))
        case.write_input_binary(open('./interact/a-plus-b-input.txt', 'rb').read())
        case.write_output_binary(open('./interact/a-plus-b-output-wrong.txt', 'rb').read())
        checker = Checker(self.rand_str(True), checker_code, 'cpp')
        interactor = Interactor(self.rand_str(True), interacter_code, 'cpp')
        submission = Submission(self.rand_str(True), code, 'python')
        case_runner = InteractiveRunner(submission, interactor, checker, 1, 128)
        result = case_runner.run(case)
        self.assertIn(result['verdict'], {Verdict.JUDGE_ERROR, Verdict.IDLENESS_LIMIT_EXCEEDED})

