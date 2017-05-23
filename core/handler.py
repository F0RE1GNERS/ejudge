import shutil
import os
import time
from .program import Program
from .judge import Judge
from .settings import RoundSettings
from .utils import *
from config import *
from celery import group
from .utils import random_string


@celery.task
def run_test(config_data, round_id, count, key, val):
    try:
        settings = RoundSettings(config_data['settings'], round_id)
        program = Program(config_data['code'], config_data['lang'], settings)
        judge = Judge(config_data['judge'], settings, initial=False)
        input_path = os.path.join(settings.data_dir, key)
        output_path = os.path.join(settings.round_dir, random_string(32))
        ans_path = os.path.join(settings.data_dir, val)
        log_path = os.path.join(settings.round_dir, random_string(32))

        running_result = program.run(input_path, output_path, log_path)

        verdict = running_result['result']
        if verdict == 0:
            checker_exit_code = judge.run(input_path, output_path, ans_path)
            if checker_exit_code != 0:
                verdict = WRONG_ANSWER

        return dict(
            count=count,
            time=running_result['cpu_time'],
            memory=running_result['memory'] // 1024,
            verdict=verdict
        )
    except Exception as e:
        print(repr(e))
        return dict(count=count, time=0, memory=0, verdict=SYSTEM_ERROR)


class Handler(object):

    def __init__(self, data, round_id):
        """
        :param data: including the following
        id: the id of the code, used in returned data
        code: just the code, should not be too long
        lang: language can now be c, cpp, java, python
        settings: should be an entire problem setting as demonstrated in RoundSettings
        judge: an indicator of judge used
        :param round_id: round dir name
        """
        # Handling a not complete data?
        # Therefore we are checking them first
        # If any of these failed, the exception will be caught outside.
        self.config_data = data
        self.id = data['id']
        self.code = data['code']
        self.lang = data['lang']
        self.settings = RoundSettings(data['settings'], round_id)
        self.program = Program(self.code, self.lang, self.settings)
        self.judge = Judge(data['judge'], self.settings)

    def run(self):

        response = {'id': self.id, 'score': 0}
        compile_result = self.program.compile()
        if compile_result['code'] == COMPILE_ERROR:
            response['verdict'] = COMPILE_ERROR
            response['message'] = compile_result['message']
            return response

        data_set = import_data(self.settings.data_dir)

        run_group = group(run_test.s(self.config_data, self.settings.round_id, idx, key, val)
                          for idx, (key, val) in enumerate(data_set, start=1))
        promise = run_group()
        detail = promise.get()
        detail = sorted(detail, key=lambda x: x.get('count'))

        sum_time = sum(x.get('time', 0) for x in detail)
        sum_memory = max(x.get('memory', 0) for x in detail)
        wrong_cases = list(filter(lambda x: x.get('verdict', WRONG_ANSWER) != ACCEPTED, detail))
        sum_verdict = ACCEPTED
        if wrong_cases:
            sum_verdict = max(x.get('verdict', WRONG_ANSWER) for x in wrong_cases)
        accept_case_num = len(detail) - len(wrong_cases)

        response.update({'verdict': sum_verdict, 'time': sum_time, 'memory': sum_memory, 'detail': detail})

        if len(detail) > 0:
            response['score'] = int(accept_case_num / len(detail) * 100)

        return response
