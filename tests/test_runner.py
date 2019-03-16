import os
import sys
import logging
import unittest

logging.basicConfig(level=logging.INFO)

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.case import Case
from core.runner import CaseRunner
from core.interaction import InteractiveRunner
from core.submission import Submission
from core.judge import Checker, Interactor
from core.exception import CompileError
from config.config import Verdict
from tests.test_base import TestBase


class RunnerTest(TestBase):

    def setUp(self):
        self.workspace = '/tmp/runner'
        super(RunnerTest, self).setUp()

    def test_aplusb(self):
        code = self.read_content('./submission/aplusb.cpp')
        checker_code = self.read_content('./submission/ncmp.cpp')
        case = Case(self.rand_str(True))
        case.write_input_binary(b"1\n2\n")
        case.write_output_binary(b"3\n")
        checker = Checker(self.rand_str(True), checker_code, 'cpp')
        submission = Submission(self.rand_str(True), code, 'cpp')
        case_runner = CaseRunner(submission, checker, 1, 128)
        result = case_runner.run(case)
        self.assertEqual(result['verdict'], Verdict.ACCEPTED)

    def test_aplusb_defaultspj(self):
        code = self.read_content('./submission/aplusb.cpp')
        case = Case(self.rand_str(True))
        case.write_input_binary(b"1\n2\n")
        case.write_output_binary(b"3\n")
        checker = Checker.fromExistingFingerprint('defaultspj')
        submission = Submission(self.rand_str(True), code, 'cpp')
        case_runner = CaseRunner(submission, checker, 1, 128)
        result = case_runner.run(case)
        self.assertEqual(result['verdict'], Verdict.ACCEPTED)

    def test_aplub_wrong(self):
        code = self.read_content('./submission/aplusb.cpp')
        case = Case(self.rand_str(True))
        case.write_input_binary(b"1\n2\n")
        case.write_output_binary(b"4\n")
        checker = Checker.fromExistingFingerprint('defaultspj')
        submission = Submission(self.rand_str(True), code, 'cpp')
        case_runner = CaseRunner(submission, checker, 1, 128)
        result = case_runner.run(case)
        self.assertEqual(result['verdict'], Verdict.WRONG_ANSWER)

    def test_aplusb_judge_fail(self):
        code = self.read_content('./submission/aplusb.cpp')
        checker_code = self.read_content('./submission/ncmp.cpp')
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
            code = self.read_content('./submission/aplusb.cpp')
            checker_code = self.read_content('./submission/ncmp.cpp')
            case = Case(self.rand_str(True))
            case.write_input_binary(b"1\n2\n")
            case.write_output_binary(b"4\n")
            checker = Checker(self.rand_str(True), checker_code, 'c')
            submission = Submission(self.rand_str(True), code, 'c')
            case_runner = CaseRunner(submission, checker, 1, 128)
            case_runner.run(case)

    def test_interactive_normal(self):
        code = self.read_content('./interact/a-plus-b.py')
        interacter_code = self.read_content('./interact/interactor-a-plus-b.cpp')
        case = Case(self.rand_str(True))
        case.write_input_binary(self.read_content('./interact/a-plus-b-input.txt', 'rb'))
        case.write_output_binary(self.read_content('./interact/a-plus-b-output.txt', 'rb'))
        checker = Checker.fromExistingFingerprint('defaultspj')
        interactor = Interactor(self.rand_str(True), interacter_code, 'cpp')
        submission = Submission(self.rand_str(True), code, 'python')
        case_runner = InteractiveRunner(submission, interactor, checker, 1, 128)
        result = case_runner.run(case)
        self.assertEqual(result['verdict'], Verdict.ACCEPTED)

    def test_interactive_wrong_answer(self):
        code = self.read_content('./interact/a-plus-b.py')
        interacter_code = self.read_content('./interact/interactor-a-plus-b.cpp')
        case = Case(self.rand_str(True))
        case.write_input_binary(self.read_content('./interact/a-plus-b-input.txt', 'rb'))
        case.write_output_binary(self.read_content('./interact/a-plus-b-output-wrong.txt', 'rb'))
        checker = Checker.fromExistingFingerprint('defaultspj')
        interactor = Interactor(self.rand_str(True), interacter_code, 'cpp')
        submission = Submission(self.rand_str(True), code, 'python')
        case_runner = InteractiveRunner(submission, interactor, checker, 1, 128)
        result = case_runner.run(case)
        self.assertEqual(result['verdict'], Verdict.WRONG_ANSWER)

    def test_aplusb_points(self):
        code = self.read_content('./submission/aplusb.cpp')
        checker_code = self.read_content('./submission/ncmp_points.cpp')
        case = Case(self.rand_str(True))
        case.write_input_binary(b"1\n2\n")
        case.write_output_binary(b"3\n")
        checker = Checker(self.rand_str(True), checker_code, 'cc14')
        submission = Submission(self.rand_str(True), code, 'cc14')
        case_runner = CaseRunner(submission, checker, 1, 128)
        result = case_runner.run(case)
        self.assertEqual(result['verdict'], Verdict.POINT)
        self.assertIn('point', result)
        self.assertNotEqual(result['point'], 0.0)
        print(result)

    def test_interactive_bad_submission(self):
        code = self.read_content('./interact/a-plus-b-nonstop.py')
        checker_code = self.read_content('./submission/ncmp.cpp')
        interacter_code = self.read_content('./interact/interactor-a-plus-b.cpp')
        case = Case(self.rand_str(True))
        case.write_input_binary(self.read_content('./interact/a-plus-b-input.txt', 'rb'))
        case.write_output_binary(self.read_content('./interact/a-plus-b-output.txt', 'rb'))
        checker = Checker(self.rand_str(True), checker_code, 'cpp')
        interactor = Interactor(self.rand_str(True), interacter_code, 'cpp')
        submission = Submission(self.rand_str(True), code, 'python')
        case_runner = InteractiveRunner(submission, interactor, checker, 1, 128)
        result = case_runner.run(case)
        self.assertEqual(result['verdict'], Verdict.RUNTIME_ERROR)

    def test_interactive_bad_interactor(self):
        code = self.read_content('./interact/a-plus-b.py')
        checker_code = self.read_content('./submission/ncmp.cpp')
        interacter_code = self.read_content('./interact/interactor-a-plus-b-nonstop.cpp')
        case = Case(self.rand_str(True))
        case.write_input_binary(self.read_content('./interact/a-plus-b-input.txt', 'rb'))
        case.write_output_binary(self.read_content('./interact/a-plus-b-output-wrong.txt', 'rb'))
        checker = Checker(self.rand_str(True), checker_code, 'cpp')
        interactor = Interactor(self.rand_str(True), interacter_code, 'cpp')
        submission = Submission(self.rand_str(True), code, 'python')
        case_runner = InteractiveRunner(submission, interactor, checker, 1, 128)
        result = case_runner.run(case)
        self.assertIn(result['verdict'], {Verdict.JUDGE_ERROR, Verdict.IDLENESS_LIMIT_EXCEEDED})

if __name__ == '__main__':
    unittest.main()
