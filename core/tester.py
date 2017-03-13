import shutil, uuid
from .program import Program
from .judge import Judge
from config import *
from .utils import *


# Tester: to test whether a submission is a valid submission
class Tester(object):

    def __init__(self, arg, do_not_run=False):
        submission_info = arg.get('submission')
        judge_info = arg.get('judge')
        config = arg.get('config', dict())

        self.do_not_run = do_not_run
        self.round_id = randomize_round_id()
        self.program = Program(submission_info, config, self.round_id)
        self.judge = Judge(judge_info, config, self.round_id) if judge_info is not None else None
        self.error = PRETEST_PASSED
        self.message = 'none'

        self.pretest_dir = os.path.join(PRETEST_DIR, str(self.program.problem_id))
        self.round_dir = os.path.join(ROUND_DIR, self.round_id)

        self.input_path = os.path.join(self.round_dir, 'in')
        self.ans_path = os.path.join(self.round_dir, 'judge_ans')

    def test(self):
        if self.test_compile():
            self.test_run()
        self.message = 'Submission #%d:\n' % self.program.submission_id + self.message
        return {'code': self.error, 'message': self.message}

    def test_compile(self):
        if not self.program.compile():
            self.error = COMPILE_ERROR
            self.message = read_partial_data_from_file(self.program.compile_out_path)
            if self.message == '':
                self.message = read_partial_data_from_file(self.program.compile_log_path)
            return False
        return True

    def test_run(self):

        if self.do_not_run:
            return True

        if self.judge is not None and not self.judge.compile():
            return False

        sum_score = 0
        if self.judge is None:
            sum_score = 100

        # IMPORT DATA
        data_list = import_data(self.pretest_dir)

        for data in data_list:
            input_file = data[0]
            ans_file = data[1]

            if os.path.exists(self.input_path):
                os.remove(self.input_path)
            shutil.copyfile(os.path.join(self.pretest_dir, input_file), self.input_path)

            if os.path.exists(self.ans_path):
                os.remove(self.ans_path)
            if ans_file is not None:
                shutil.copyfile(os.path.join(self.pretest_dir, ans_file), self.ans_path)

            running_result = self.program.run()

            if self.judge is not None:
                judge_result = self.judge.run()
                sum_score += judge_result['score']
                if judge_result['score'] == 0 and data[2] > 0:
                    self.error = PRETEST_FAILED
                    self.message = 'Bad Score'
                    break

            if running_result['result'] > 0:  # fatal error
                self.error = PRETEST_FAILED
                self.message = read_partial_data_from_file(self.program.log_path)
                break

        # CLEAN UP
        for file in os.listdir(self.round_dir):
            os.remove(os.path.join(self.round_dir, file))

        return False if self.error == PRETEST_FAILED else True
