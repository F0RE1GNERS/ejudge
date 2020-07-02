import logging
import os
import sys
import unittest

logging.basicConfig(level=logging.INFO)

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.case import Case
from core.runner import CaseRunner
from core.interaction import InteractiveRunner
from core.submission import Submission
from core.judge import SpecialJudge
from core.exception import CompileError
from config import Verdict
from tests.test_base import TestBase


class RunnerTest(TestBase):

  @classmethod
  def setUpClass(cls):
    cls.ncmp = cls.rand_str(True)
    checker_code = cls.read_content('./submission/ncmp.cpp')
    logging.info("compiling checker code")
    program = SpecialJudge('cpp', fingerprint=cls.ncmp)
    program.compile(checker_code, 30)

    cls.ncmp_points = cls.rand_str(True)
    checker_code = cls.read_content('./submission/ncmp_points.cpp')
    logging.info("compiling checker points")
    program = SpecialJudge('cpp', fingerprint=cls.ncmp_points)
    program.compile(checker_code, 30)

    cls.defaultspj = "defaultspj"

    cls.interactor = cls.rand_str(True)
    interacter_code = cls.read_content('./interact/interactor-a-plus-b.cpp')
    logging.info("compiling interactor")
    program = SpecialJudge('cpp', fingerprint=cls.interactor)
    program.compile(interacter_code, 30)

    cls.interactor_nonstop = cls.rand_str(True)
    interacter_code = cls.read_content('./interact/interactor-a-plus-b-nonstop.cpp')
    logging.info("compiling interactor nonstop")
    program = SpecialJudge('cpp', fingerprint=cls.interactor_nonstop)
    program.compile(interacter_code, 30)

  def setUp(self):
    self.workspace = '/tmp/runner'
    super(RunnerTest, self).setUp()

  def test_aplusb(self):
    code = self.read_content('./submission/aplusb.cpp')
    case = Case(self.rand_str(True))
    case.write_input_binary(b"1\n2\n")
    case.write_output_binary(b"3\n")
    checker = SpecialJudge.fromExistingFingerprint(self.ncmp)
    submission = Submission('cpp')
    submission.compile(code, 5)
    case_runner = CaseRunner(submission, checker, 1, 128)
    result = case_runner.run(case)
    self.assertEqual(result['verdict'], Verdict.ACCEPTED)

  def test_aplusb_defaultspj(self):
    code = self.read_content('./submission/aplusb.cpp')
    case = Case(self.rand_str(True))
    case.write_input_binary(b"1\n2\n")
    case.write_output_binary(b"3\n")
    checker = SpecialJudge.fromExistingFingerprint('defaultspj')
    submission = Submission('cpp')
    submission.compile(code, 5)
    case_runner = CaseRunner(submission, checker, 1, 128)
    result = case_runner.run(case)
    self.assertEqual(result['verdict'], Verdict.ACCEPTED)

  def test_aplub_wrong(self):
    code = self.read_content('./submission/aplusb.cpp')
    case = Case(self.rand_str(True))
    case.write_input_binary(b"1\n2\n")
    case.write_output_binary(b"4\n")
    checker = SpecialJudge.fromExistingFingerprint('defaultspj')
    submission = Submission('cpp')
    submission.compile(code, 5)
    case_runner = CaseRunner(submission, checker, 1, 128)
    result = case_runner.run(case)
    self.assertEqual(result['verdict'], Verdict.WRONG_ANSWER)

  def test_aplusb_compile_error(self):
    with self.assertRaises(CompileError):
      code = self.read_content('./submission/aplusb.cpp')
      case = Case(self.rand_str(True))
      case.write_input_binary(b"1\n2\n")
      case.write_output_binary(b"4\n")
      checker = SpecialJudge.fromExistingFingerprint('defaultspj')
      submission = Submission('c')
      submission.compile(code, 5)

  def test_interactive_normal(self):
    code = self.read_content('./interact/a-plus-b.py')
    case = Case(self.rand_str(True))
    case.write_input_binary(self.read_content('./interact/a-plus-b-input.txt', 'rb'))
    case.write_output_binary(self.read_content('./interact/a-plus-b-output.txt', 'rb'))
    checker = SpecialJudge.fromExistingFingerprint('defaultspj')
    interactor = SpecialJudge.fromExistingFingerprint(self.interactor)
    submission = Submission('python')
    submission.compile(code, 10)
    case_runner = InteractiveRunner(submission, interactor, checker, 1, 128)
    result = case_runner.run(case)
    self.assertEqual(result['verdict'], Verdict.ACCEPTED)

  def test_interactive_wrong_answer(self):
    code = self.read_content('./interact/a-plus-b.py')
    case = Case(self.rand_str(True))
    case.write_input_binary(self.read_content('./interact/a-plus-b-input.txt', 'rb'))
    case.write_output_binary(self.read_content('./interact/a-plus-b-output-wrong.txt', 'rb'))
    checker = SpecialJudge.fromExistingFingerprint('defaultspj')
    interactor = SpecialJudge.fromExistingFingerprint(self.interactor)
    submission = Submission('python')
    submission.compile(code, 10)
    case_runner = InteractiveRunner(submission, interactor, checker, 1, 128)
    result = case_runner.run(case)
    self.assertEqual(result['verdict'], Verdict.WRONG_ANSWER)

  def test_aplusb_points(self):
    code = self.read_content('./submission/aplusb.cpp')
    case = Case(self.rand_str(True))
    case.write_input_binary(b"1\n2\n")
    case.write_output_binary(b"3\n")
    checker = SpecialJudge.fromExistingFingerprint(self.ncmp_points)
    submission = Submission('cc14')
    submission.compile(code, 5)
    case_runner = CaseRunner(submission, checker, 1, 128)
    result = case_runner.run(case)
    self.assertEqual(result['verdict'], Verdict.POINT)
    self.assertIn('point', result)
    self.assertNotEqual(result['point'], 0.0)
    print(result)

  def test_interactive_bad_submission(self):
    code = self.read_content('./interact/a-plus-b-nonstop.py')
    case = Case(self.rand_str(True))
    case.write_input_binary(self.read_content('./interact/a-plus-b-input.txt', 'rb'))
    case.write_output_binary(self.read_content('./interact/a-plus-b-output.txt', 'rb'))
    checker = SpecialJudge.fromExistingFingerprint('defaultspj')
    interactor = SpecialJudge.fromExistingFingerprint(self.interactor)
    submission = Submission('python')
    submission.compile(code, 10)
    case_runner = InteractiveRunner(submission, interactor, checker, 1, 128)
    result = case_runner.run(case)
    self.assertEqual(result['verdict'], Verdict.RUNTIME_ERROR)

  def test_interactive_bad_interactor(self):
    code = self.read_content('./interact/a-plus-b.py')
    case = Case(self.rand_str(True))
    case.write_input_binary(self.read_content('./interact/a-plus-b-input.txt', 'rb'))
    case.write_output_binary(self.read_content('./interact/a-plus-b-output.txt', 'rb'))
    checker = SpecialJudge.fromExistingFingerprint('defaultspj')
    interactor = SpecialJudge.fromExistingFingerprint(self.interactor_nonstop)
    submission = Submission('python')
    submission.compile(code, 10)
    case_runner = InteractiveRunner(submission, interactor, checker, 1, 128)
    result = case_runner.run(case)
    self.assertIn(result['verdict'], {Verdict.JUDGE_ERROR, Verdict.IDLENESS_LIMIT_EXCEEDED})


if __name__ == '__main__':
  unittest.main()
