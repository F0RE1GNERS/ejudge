from core.case import Case
from core.judge import Checker, Interactor
from core.submission import Submission
from core.runner import CaseRunner, InteractiveRunner
from config.config import Verdict

from flask import Flask
from celery import Celery
from flask_socketio import SocketIO


flask_app = Flask(__name__)
flask_app.config['broker_url'] = 'redis://localhost:6379/0'
flask_app.config['result_backend'] = 'redis://localhost:6379/0'
flask_app.config['imports'] = ['handler']
flask_app.config['SECRET_KEY'] = 'secret!'
# flask_app.config['worker_concurrency'] = max(os.cpu_count() // 2, 1)

celery = Celery(flask_app.name, broker=flask_app.config['broker_url'])
celery.conf.update(flask_app.config)

socketio = SocketIO(flask_app, async_mode='eventlet')


@celery.task(bind=True)
def judge_handler(self,
                  sub_fingerprint, sub_lang, sub_code,
                  case_list, max_time, max_memory,
                  checker_fingerprint,
                  interactor_fingerprint=None,
                  run_until_complete=False):
    submission = Submission(sub_fingerprint, sub_code, sub_lang)
    checker = Checker.fromExistingFingerprint(checker_fingerprint)
    if interactor_fingerprint:
        interactor = Interactor.fromExistingFingerprint(interactor_fingerprint)
        case_runner = InteractiveRunner(submission, interactor, checker, max_time, max_memory)
    else:
        case_runner = CaseRunner(submission, checker, max_time, max_memory)

    detail = []
    # enum is converted into value manually for json serialization
    response = {'status': 'received', 'verdict': Verdict.JUDGING.value, 'detail': detail}
    sum_verdict = Verdict.ACCEPTED
    time_verdict = -1
    for case_fingerprint in case_list:
        case = Case(case_fingerprint)
        case_result = case_runner.run(case)
        case_result['verdict'] = case_result['verdict'].value
        detail.append(case_result)
        self.update_state(state="PROGRESS", meta=response)
        if case_result.get('time'):
            time_verdict = max(time_verdict, case_result['time'])
        if case_result['verdict'] != Verdict.ACCEPTED.value:
            if sum_verdict == Verdict.ACCEPTED:
                sum_verdict = case_result['verdict']
            if not run_until_complete:
                break
    response.update(verdict=sum_verdict.value)
    if time_verdict >= 0:
        response.update(time=time_verdict)
    submission.clean()
    return response
