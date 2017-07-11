from core.case import Case
from core.judge import Checker, Interactor, Generator, Validator
from core.submission import Submission
from core.runner import CaseRunner, InteractiveRunner, RunnerResultType
from core.exception import CompileError
from core.util import random_string, serialize_sandbox_result
from config.config import Verdict, TRACEBACK_LIMIT

from flask import Flask
from celery import Celery
from flask_socketio import SocketIO
import base64
import traceback
import time


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
                  sub_fingerprint, sub_code, sub_lang,
                  case_list, max_time, max_memory,
                  checker_fingerprint,
                  interactor_fingerprint=None,
                  run_until_complete=False):
    try:
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
        sum_verdict_value = Verdict.ACCEPTED.value
        time_verdict = -1
        try:
            for case_fingerprint in case_list:
                case = Case(case_fingerprint)
                case_result = case_runner.run(case)
                case_result['verdict'] = case_result['verdict'].value
                detail.append(case_result)
                self.update_state(state="PROGRESS", meta=response)
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
        submission.clean()
    except:
        response = {'status': 'reject', 'message': traceback.format_exc(TRACEBACK_LIMIT)}
    finally:
        try:
            submission.clean()
        except NameError:
            pass
    return response


@celery.task
def judge_handler_one(sub_dict, max_time, max_memory, case_input_b64, case_output_b64=None,
                      target='result', checker_dict=None, interactor_dict=None):
    """
    This function is built for admins to check problem status in multiple ways

    target:
    - result: running for final result
    - output: running for the output of std
    - sandbox: return the sandbox result of submission
    - checker/interactor: return the output in result file

    However, setting target does not guarantee you the corresponding result. If you, for example, set the target
    to be checker, but you fail to notify the checker_tuple, then something unexpected will return, without warnings.
    """
    try:
        if target not in ['result', 'output', 'sandbox', 'checker', 'interactor']:
            raise ValueError('Target must be result, output, sandbox, checker or interactor.')
        if target == 'result':
            target = RunnerResultType.FINAL
        elif target == 'output':
            target = RunnerResultType.OUTPUT
        elif target == 'sandbox':
            target = RunnerResultType.SUB_SANDBOX_RESULT
        elif target == 'checker':
            target = RunnerResultType.CHECKER_RESULT
        elif target == 'interactor':
            target = RunnerResultType.INTERACTOR_RESULT

        submission = Submission(sub_dict['fingerprint'], sub_dict['code'], sub_dict['lang'])
        checker = Checker(checker_dict['fingerprint'], checker_dict['code'], checker_dict['lang']) if checker_dict else None
        if interactor_dict:
            interactor = Interactor(interactor_dict['fingerprint'], interactor_dict['code'], interactor_dict['lang'])
            case_runner = InteractiveRunner(submission, interactor, checker, max_time, max_memory)
        else:
            interactor = None
            case_runner = CaseRunner(submission, checker, max_time, max_memory)

        case = Case(random_string())
        case.write_input_binary(base64.b64decode(case_input_b64))
        case.write_output_binary(base64.b64decode(case_output_b64) if case_output_b64 else b'')
        try:
            result = case_runner.run(case, result_type=target)
            result.update(status='received')
            result['verdict'] = result['verdict'].value
        except CompileError as ce:
            result = {'status': 'received', 'verdict': Verdict.COMPILE_ERROR.value, 'message': ce.detail}
    except:
        result = {'status': 'reject', 'message': traceback.format_exc(TRACEBACK_LIMIT)}
    finally:
        try:
            submission.clean()
            if checker:
                checker.clean()
            if interactor:
                interactor.clean()
            case.clean()
        except NameError:
            pass
    return result


@celery.task
def generate_handler(gen_fingerprint, gen_code, gen_lang, max_time, max_memory, command_line_args):
    try:
        generator = Generator(gen_fingerprint, gen_code, gen_lang)
        tmp_output = generator.make_a_file_to_write()
        generator.generate(tmp_output, max_time, max_memory, command_line_args)
        result = {'status': 'received', 'output': base64.b64encode(open(tmp_output, 'rb').read()).decode()}
    except:
        result = {'status': 'reject', 'message': traceback.format_exc(TRACEBACK_LIMIT)}
    finally:
        try:
            generator.clean()
        except NameError:
            pass
    return result


@celery.task
def validate_handler(val_fingerprint, val_code, val_lang, max_time, max_memory, case_input_b64):
    try:
        validator = Validator(val_fingerprint, val_code, val_lang)
        tmp_input = validator.make_a_file_to_write()
        with open(tmp_input, 'r') as fs:
            fs.write(base64.b64decode(case_input_b64))
        val_result = validator.validate(tmp_input, max_time, max_memory)
        result = {'status': 'received', 'verdict': val_result.verdict, 'message': val_result.message}
    except:
        result = {'status': 'reject', 'message': traceback.format_exc(TRACEBACK_LIMIT)}
    finally:
        try:
            validator.clean()
        except NameError:
            pass
    return result


@celery.task
def stress_handler(sub1, sub2, gen, command_line_args_list, max_time, max_memory, max_sum_time,
                   checker_dict, interactor_dict=None, max_generate=5):
    try:
        submission1 = Submission(sub1['fingerprint'], sub1['code'], sub1['lang'])
        submission2 = Submission(sub2['fingerprint'], sub2['code'], sub2['lang'])
        generator = Generator(gen['fingerprint'], gen['code'], gen['lang'])
        checker = Checker(checker_dict['fingerprint'], checker_dict['code'],
                          checker_dict['lang']) if checker_dict else None
        if interactor_dict:
            interactor = Interactor(interactor_dict['fingerprint'], interactor_dict['code'], interactor_dict['lang'])
            case_runner1 = InteractiveRunner(submission1, interactor, checker, max_time, max_memory)
            case_runner2 = InteractiveRunner(submission2, interactor, checker, max_time, max_memory)
        else:
            interactor = None
            case_runner1 = CaseRunner(submission1, checker, max_time, max_memory)
            case_runner2 = CaseRunner(submission2, checker, max_time, max_memory)

        args_idx, report = 0, []
        start_time = time.time()
        while max_generate > 0 and time.time() - start_time < max_sum_time:
            case = Case(random_string())
            generator.generate(case.input_file, max_time, max_memory, command_line_args_list[args_idx])
            with open(case.output_file, 'wb') as fs:
                fs.write(base64.b64decode(case_runner1.run(case, result_type=RunnerResultType.OUTPUT)))
            result = case_runner2.run(case)
            if result['verdict'] != Verdict.ACCEPTED:
                report.append(base64.b64encode(open(case.input_file, 'rb').read()))
                max_generate -= 1
            case.clean()
            args_idx = (args_idx + 1) % len(command_line_args_list)

    except:
        result = {'status': 'reject', 'message': traceback.format_exc(TRACEBACK_LIMIT)}
    finally:
        try:
            submission1.clean()
            submission2.clean()
            generator.clean()
            if checker:
                checker.clean()
            if interactor:
                interactor.clean()
        except NameError:
            pass
    return result