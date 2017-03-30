import shutil
from random import Random
from .program import Program
from .judge import Judge
from .settings import RoundSettings
from .utils import *
from config import *


class Handler(object):

    def __init__(self, data):
        """
        :param data: including the following
        id: the id of the code, used in returned data
        code: just the code, should not be too long
        lang: language can now be c, cpp, java, python
        settings: should be an entire problem setting as demonstrated in RoundSettings
        judge: an indicator of judge used
        """
        # Handling a not complete data?
        # Therefore we are checking them first
        # If any of these failed, the exception will be caught outside.
        self.id = data['id']
        self.code = data['code']
        self.lang = data['lang']
        self.settings = RoundSettings(data['settings'])
        self.program = Program(self.code, self.lang, self.settings)
        self.judge = Judge(data['judge'], self.settings)

    def run(self):

        response = {'id': self.id, 'score': 0}
        compile_result = self.program.compile()
        if compile_result['code'] == COMPILE_ERROR:
            response['verdict'] = COMPILE_ERROR
            response['message'] = compile_result['message']
            shutil.rmtree(self.settings.round_dir)
            return response

        data_set = import_data(self.settings.data_dir)
        detail = []
        test_num, sum_time, sum_memory, sum_verdict, accept_case_num = 0, 0, 0, ACCEPTED, 0

        for key, val in sorted(data_set.items()):
            self.transfer_data(key, val)
            test_num += 1

            running_result = self.program.run()

            verdict = running_result['result']
            if verdict == 0:
                checker_exit_code = self.judge.run()
                if checker_exit_code != 0:
                    verdict = WRONG_ANSWER

            log_info = dict(
                count=test_num,
                time=running_result['cpu_time'],
                memory=running_result['memory'] // 1024,
                verdict=verdict
            )
            detail.append(log_info)

            sum_time += log_info['time']
            sum_memory = max(sum_memory, log_info['memory'])

            if verdict == ACCEPTED:
                accept_case_num += 1
            else:
                sum_verdict = max(verdict, sum_verdict) if verdict > 0 else verdict
            if sum_time > self.settings.max_sum_time:
                sum_verdict = SUM_TIME_LIMIT_EXCEEDED
                break

        shutil.rmtree(self.settings.round_dir)  # Clean up in case it blows the hard drive
        response.update({'verdict': sum_verdict, 'time': sum_time, 'memory': sum_memory, 'detail': detail})

        if len(data_set) > 0:
            response['score'] = int(accept_case_num / len(data_set) * 100)

        return response

    def transfer_data(self, input_file, ans_file):
        """
        :param input_file: filename, directory not included
        :param ans_file: filename
        :return: copy file to round directory and return nothing
        """
        shutil.copyfile(os.path.join(self.settings.data_dir, input_file), self.settings.input_path)
        shutil.copyfile(os.path.join(self.settings.data_dir, ans_file), self.settings.ans_path)
