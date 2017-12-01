import base64
import time
import traceback
from io import StringIO
from os import path

from celery import Celery
from flask import Flask
from werkzeug.contrib.cache import MemcachedCache

from config.config import Verdict, TRACEBACK_LIMIT, SECRET_KEY, MAX_WORKER_NUMBER, MAX_TASKS_PER_CHILD, OUTPUT_LIMIT
from core.case import Case
from core.exception import CompileError
from core.judge import Checker, Interactor, Generator, Validator
from core.runner import CaseRunner, InteractiveRunner
from core.submission import Submission
from core.util import random_string

flask_app = Flask(__name__)
flask_app.config['broker_url'] = 'redis://localhost:6379/0'
flask_app.config['result_backend'] = 'redis://localhost:6379/0'
flask_app.config['imports'] = ['handler']
flask_app.config['SECRET_KEY'] = SECRET_KEY
flask_app.config['worker_concurrency'] = MAX_WORKER_NUMBER
flask_app.config['worker_max_tasks_per_child'] = MAX_TASKS_PER_CHILD

celery = Celery(flask_app.name, broker=flask_app.config['broker_url'])
celery.conf.update(flask_app.config)

cache = MemcachedCache(['127.0.0.1:11211'])


def reject_with_traceback():
    return {'status': 'reject', 'message': traceback.format_exc(TRACEBACK_LIMIT)}


@celery.task(bind=True)
def judge_handler(self,
                  sub_fingerprint, sub_code, sub_lang,
                  case_list, max_time, max_memory,
                  checker_fingerprint,
                  interactor_fingerprint=None,
                  run_until_complete=False):
    try:
        submission = Submission(sub_fingerprint, sub_code, sub_lang)
        checker = Checker.fromExistingFingerprint(checker_fingerprint)
        report = StringIO()
        if interactor_fingerprint:
            interactor = Interactor.fromExistingFingerprint(interactor_fingerprint)
            case_runner = InteractiveRunner(submission, interactor, checker, max_time, max_memory, report_file=report)
        else:
            case_runner = CaseRunner(submission, checker, max_time, max_memory, report_file=report)

        detail = []
        # enum is converted into value manually for json serialization
        response = {'status': 'received', 'verdict': Verdict.JUDGING.value, 'detail': detail}
        sum_verdict_value = Verdict.ACCEPTED.value
        time_verdict = -1
        try:
            for case_fingerprint in case_list:
                case = Case(case_fingerprint)
                case_result = case_runner.run(case)
                case_result['verdict'] = case_result['verdict'].value
                detail.append(case_result)
                cache.set(sub_fingerprint, response, timeout=3600)
                if case_result.get('time'):
                    time_verdict = max(time_verdict, case_result['time'])
                if case_result['verdict'] != Verdict.ACCEPTED.value:
                    if sum_verdict_value == Verdict.ACCEPTED.value:
                        sum_verdict_value = case_result['verdict']
                    if not run_until_complete:
                        break
        except CompileError as ce:
            sum_verdict_value = Verdict.COMPILE_ERROR.value
            response.update(message=ce.detail)
        response.update(verdict=sum_verdict_value)
        if time_verdict >= 0:
            response.update(time=time_verdict)
        cache.set('report_%s' % sub_fingerprint, report.getvalue(), timeout=1800)
        submission.clean()
    except:
        response = reject_with_traceback()
    finally:
        cache.set(sub_fingerprint, response, timeout=3600)

        try:
            submission.clean()
        except NameError:
            pass
    return response
