import shutil
import copy
from random import Random
from .program import Program
from .judge import Judge
from .utils import *
from config import *


class Handler(object):

    def __init__(self, data):
        # Handling a not complete data?
        # Therefore we are checking them first
        # If any of these failed, the exception will be caught outside.

        self.id = data['id']
        self.code = data['code']
        self.lang = data['lang']
        self.settings = ProblemSettings(data['config'])

        if data.get('judge') is None:
            data['judge'] = {'id': 0, 'lang': 'builtin', 'code': 'testlib/checker/file_cmp.py'}
        if data.get('pretest_judge') is None:
            data['pretest_judge'] = copy.deepcopy(data['judge'])

        submission_list = data.get('submissions')
        config = data.get('config', dict())
        judge = data.get('judge')
        pretest_judge = data.get('pretest_judge', judge)
        self.round_id = randomize_round_id()
        self.submissions = []

        # TEST
        try:
            self.test_result = Tester({'submission': judge, 'config': config}, do_not_run=True).test()
            if self.test_result['code'] != PRETEST_PASSED:
                raise Handler.TestFailedException
            self.judge = Judge(judge, config, self.round_id)

            self.test_result = Tester({'submission': pretest_judge, 'config': config}, do_not_run=True).test()
            if self.test_result['code'] != PRETEST_PASSED:
                raise Handler.TestFailedException
            self.pretest_judge = Judge(pretest_judge, config, self.round_id)

            for submission in submission_list:
                self.test_result = Tester({'submission': submission, 'judge': pretest_judge, 'config': config}).test()
                if self.test_result['code'] != PRETEST_PASSED:
                    raise Handler.TestFailedException
                self.submissions.append(Program(submission, config, self.round_id))

        except Handler.TestFailedException:
            pass

        else:
            self.problem_id = config['problem_id']
            self.data_dir = os.path.join(DATA_DIR, str(self.problem_id))
            self.round_dir = os.path.join(ROUND_DIR, str(self.round_id))
            self.input_path = os.path.join(self.round_dir, 'in')
            self.output_path = os.path.join(self.round_dir, 'out')
            self.ans_path = os.path.join(self.round_dir, 'judge_ans')
            self.round_log_path = os.path.join(self.round_dir, 'round.log')

            self.round_log = open(self.round_log_path, "w")
            self.dumped = False

    def run(self):
        if self.test_result['code'] != PRETEST_PASSED:
            return self.test_result

        if self.dumped:
            # WHAT THE HELL?
            return {'code': SYSTEM_ERROR}
        self.dumped = True

        # IMPORT DATA
        data_list = import_data(self.data_dir)

        # INIT
        for i in range(len(self.submissions)):
            self.submissions[i].sum_score = 0

        for data in data_list:
            input_file = data[0]
            ans_file = data[1]
            weight = data[2]

            # use copy instead of link to prevent chmod problems
            if os.path.exists(self.input_path):
                os.remove(self.input_path)
            shutil.copyfile(os.path.join(self.data_dir, input_file), self.input_path)

            if os.path.exists(self.ans_path):
                os.remove(self.ans_path)
            if ans_file is not None:
                shutil.copyfile(os.path.join(self.data_dir, ans_file), self.ans_path)

            self.round_log.write('#### Based on input data %s, data weight %d:\n\n' % (input_file, weight))

            # Start Running

            r = Random()
            r.shuffle(self.submissions)
            for i in range(len(self.submissions)):
                self.submissions[i].score = 0
                self.submissions[i].sum_time = 0
                self.submissions[i].sum_memory = 0
            cnt = 0
            run_count = 1

            while True:
                running_result = self.submissions[cnt].run()

                # Save data
                _log_info = dict(
                    cnt=run_count,
                    program=self.submissions[cnt].submission_id,
                    time=running_result['cpu_time'],
                    memory=running_result['memory'] // 1024,
                    exit_code=running_result['exit_code'],
                    score=0,
                    result=running_result['result']
                )
                in_data = read_partial_data_from_file(self.input_path)
                out_data = read_partial_data_from_file(self.output_path)
                ans_data = ''
                judge_data = 'none'

                _continue = False

                # Handle Errors
                if running_result['result'] == 0:
                    # Cope with Judge
                    judge_result = self.judge.run()
                    _continue = judge_result['continue']
                    _log_info['score'] = judge_result['score']
                    _log_info['result'] = judge_result['message']
                    judge_data = judge_result['data']
                    ans_data = read_partial_data_from_file(self.ans_path)

                    # New input
                    if os.path.exists(self.input_path):
                        os.remove(self.input_path)
                    shutil.copyfile(self.judge.judge_new_input_path, self.input_path)

                elif running_result['result'] == RUNTIME_ERROR:
                    judge_data = read_partial_data_from_file(self.judge.log_path)

                # Write Log
                _log_info['result'] = ERROR_CODE[_log_info['result']]
                self.round_log.write('##### Run #{cnt} (submission #{program})\n'
                                     '**time: {time}ms., memory: {memory}KB, '
                                     'exit code: {exit_code}, verdict: {result}, raw score: {score}.**\n'
                                     .format(**_log_info))
                # DEBUG
                # print('Run #{cnt}: submission: #{program}, time: {time}ms., memory: {memory}KB, '
                #       'exit code: {exit_code}, running result: {result}, score: {score}. '
                #       .format(**log_info))
                self.round_log.write('input:\n```%s```\n' % format_code_for_markdown(in_data))
                self.round_log.write('output:\n```%s```\n' % format_code_for_markdown(out_data))
                if len(ans_data) > 0:
                    self.round_log.write('answer:\n```%s```\n' % format_code_for_markdown(ans_data))
                self.round_log.write('judge:\n```%s```\n' % format_code_for_markdown(judge_data))

                # Deal with the game
                self.submissions[cnt].score += _log_info['score']
                if not _continue:
                    break

                cnt = (cnt + 1) % len(self.submissions)
                run_count += 1

            # Round complete
            self.submissions.sort(key=lambda x: x.submission_id)
            if run_count > 1:
                self.round_log.write('##### Judge has called an end to this round.\n')
                for submission in self.submissions:
                    self.round_log.write('#%d time: %dms., memory: %dKB, score: %d.\n\n' % (
                        submission.submission_id, submission.sum_time, submission.sum_memory // 1024, submission.score))
            for i in range(len(self.submissions)):
                self.submissions[i].sum_score += int(self.submissions[i].score / 100 * weight)

        # CLEAN UP
        json_result = dict()
        json_result['code'] = FINISHED
        json_result['score'] = dict()

        self.round_log.write('##### Conclusion:\n')
        for submission in self.submissions:
            self.round_log.write('#%d has a total score of %d.\n\n' % (submission.submission_id, submission.sum_score))
            json_result['score'][submission.submission_id] = submission.sum_score
        for file in os.listdir(self.round_dir):
            if file != 'round.log':
                os.remove(os.path.join(self.round_dir, file))

        self.round_log.close()
        json_result['message'] = open(self.round_log_path, "r").read()
        return json_result


