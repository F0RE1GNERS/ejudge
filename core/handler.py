import shutil
from random import Random
from .program import Program
from .judge import Judge
from .settings import RoundSettings
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
        self.settings = RoundSettings(data['config'])
        self.program = Program(self.code, self.lang, self.settings)
        self.judge = Judge(data['judge'], self.settings)

    def run(self):

        compile_result = self.program.compile()
        if compile_result['code'] == COMPILE_ERROR:
            return compile_result

        data_set = import_data(self.settings.data_dir)
        details = []
        test_num = 0
        sum_time = 0

        for key in sorted(data_set.keys()):
            self.transfer_data(key, data_set[key])
            test_num += 1

            running_result = self.program.run()
            sum_time += running_result['cpu_time']
            log_info = dict(
                count=test_num,
                time=running_result['cpu_time'],
                memory=running_result['memory'] // 1024,
                exit_code=running_result['exit_code'],
                result=running_result['result'],
            )
            if sum_time > self.settings.max_sum_time:
                pass
        #
        #     while True:
        #         running_result = self.submissions[cnt].run()
        #
        #         # Save data
        #         _log_info = dict(
        #             cnt=run_count,
        #             program=self.submissions[cnt].submission_id,
        #             time=running_result['cpu_time'],
        #             memory=running_result['memory'] // 1024,
        #             exit_code=running_result['exit_code'],
        #             score=0,
        #             result=running_result['result']
        #         )
        #         in_data = read_partial_data_from_file(self.input_path)
        #         out_data = read_partial_data_from_file(self.output_path)
        #         ans_data = ''
        #         judge_data = 'none'
        #
        #         _continue = False
        #
        #         # Handle Errors
        #         if running_result['result'] == 0:
        #             # Cope with Judge
        #             judge_result = self.judge.run()
        #             _continue = judge_result['continue']
        #             _log_info['score'] = judge_result['score']
        #             _log_info['result'] = judge_result['message']
        #             judge_data = judge_result['data']
        #             ans_data = read_partial_data_from_file(self.ans_path)
        #
        #             # New input
        #             if os.path.exists(self.input_path):
        #                 os.remove(self.input_path)
        #             shutil.copyfile(self.judge.judge_new_input_path, self.input_path)
        #
        #         elif running_result['result'] == RUNTIME_ERROR:
        #             judge_data = read_partial_data_from_file(self.judge.log_path)
        #
        #         # Write Log
        #         _log_info['result'] = ERROR_CODE[_log_info['result']]
        #         self.round_log.write('##### Run #{cnt} (submission #{program})\n'
        #                              '**time: {time}ms., memory: {memory}KB, '
        #                              'exit code: {exit_code}, verdict: {result}, raw score: {score}.**\n'
        #                              .format(**_log_info))
        #         # DEBUG
        #         # print('Run #{cnt}: submission: #{program}, time: {time}ms., memory: {memory}KB, '
        #         #       'exit code: {exit_code}, running result: {result}, score: {score}. '
        #         #       .format(**log_info))
        #         self.round_log.write('input:\n```%s```\n' % format_code_for_markdown(in_data))
        #         self.round_log.write('output:\n```%s```\n' % format_code_for_markdown(out_data))
        #         if len(ans_data) > 0:
        #             self.round_log.write('answer:\n```%s```\n' % format_code_for_markdown(ans_data))
        #         self.round_log.write('judge:\n```%s```\n' % format_code_for_markdown(judge_data))
        #
        #         # Deal with the game
        #         self.submissions[cnt].score += _log_info['score']
        #         if not _continue:
        #             break
        #
        #         cnt = (cnt + 1) % len(self.submissions)
        #         run_count += 1
        #
        #     # Round complete
        #     self.submissions.sort(key=lambda x: x.submission_id)
        #     if run_count > 1:
        #         self.round_log.write('##### Judge has called an end to this round.\n')
        #         for submission in self.submissions:
        #             self.round_log.write('#%d time: %dms., memory: %dKB, score: %d.\n\n' % (
        #                 submission.submission_id, submission.sum_time, submission.sum_memory // 1024, submission.score))
        #     for i in range(len(self.submissions)):
        #         self.submissions[i].sum_score += int(self.submissions[i].score / 100 * weight)
        #
        # # CLEAN UP
        # json_result = dict()
        # json_result['code'] = FINISHED
        # json_result['score'] = dict()
        #
        # self.round_log.write('##### Conclusion:\n')
        # for submission in self.submissions:
        #     self.round_log.write('#%d has a total score of %d.\n\n' % (submission.submission_id, submission.sum_score))
        #     json_result['score'][submission.submission_id] = submission.sum_score
        # for file in os.listdir(self.round_dir):
        #     if file != 'round.log':
        #         os.remove(os.path.join(self.round_dir, file))
        #
        # self.round_log.close()
        # json_result['message'] = open(self.round_log_path, "r").read()
        # return json_result


    def transfer_data(self, input_file, ans_file):
        """
        :param input_file: filename, directory not included
        :param ans_file: filename
        :return: copy file to round directory and return nothing
        """
        shutil.copyfile(os.path.join(self.settings.data_dir, input_file), self.settings.input_path)
        shutil.copyfile(os.path.join(self.settings.data_dir, ans_file), self.settings.ans_path)
