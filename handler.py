import base64
import time
import traceback
from os import path

import redis
from celery import Celery
from flask import Flask

from config.config import Verdict, TRACEBACK_LIMIT, SECRET_KEY, MAX_WORKER_NUMBER, MAX_TASKS_PER_CHILD, OUTPUT_LIMIT
from core.case import Case
from core.exception import CompileError
from core.judge import Checker, Interactor, Generator, Validator
from core.runner import CaseRunner, InteractiveRunner, RunnerResultType
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

redis_db = redis.StrictRedis(host='localhost', port=6379, db=1)


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
        response = reject_with_traceback()
    finally:
        try:
            submission.clean()
        except NameError:
            pass
    return response


@celery.task
def judge_handler_one(sub_dict, max_time, max_memory, case_input_b64, case_output_b64=None,
                      target='result', checker_dict=None, interactor_dict=None, multiple=False):
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
            max_memory = -1  # no-restrict on memory for running output
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

        try:
            if multiple:
                result_list = []
                result_output_size = 0
                for ind, input_binary in enumerate(case_input_b64):
                    try:
                        case = Case(random_string())
                        case.write_input_binary(base64.b64decode(input_binary))
                        try:
                            output_binary = base64.b64decode(case_output_b64[ind])
                        except:
                            output_binary = b''
                        case.write_output_binary(output_binary)
                        result = case_runner.run(case, result_type=target)
                        if result.get('verdict'):
                            result['verdict'] = result['verdict'].value
                        result_list.append(result)
                        if target == RunnerResultType.OUTPUT:
                            result_output_size += len(result['output'])
                        if result_output_size > OUTPUT_LIMIT * 1024576:
                            raise RuntimeError("Output limit exceeded")
                    finally:
                        case.clean()
                result = {'status': 'received', 'result': result_list}
            else:
                case = Case(random_string())
                case.write_input_binary(base64.b64decode(case_input_b64))
                case.write_output_binary(base64.b64decode(case_output_b64) if case_output_b64 else b'')
                result = case_runner.run(case, result_type=target)
                result.update(status='received')
                if result.get('verdict'):
                    result['verdict'] = result['verdict'].value
        except CompileError as ce:
            if target == RunnerResultType.FINAL:
                result = {'status': 'received', 'verdict': Verdict.COMPILE_ERROR.value, 'message': ce.detail}
            else:
                raise
    except:
        result = reject_with_traceback()
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
def generate_handler(gen_fingerprint, gen_code, gen_lang, max_time, max_memory, command_line_args, multiple=False):
    def get_b64_from_file(file_path):
        with open(file_path, 'rb') as fs:
            return base64.b64encode(fs.read()).decode()

    try:
        generator = Generator(gen_fingerprint, gen_code, gen_lang)
        tmp_output = generator.make_a_file_to_write()
        # If multiple is True, command line args is a list of list, then a list of output will be produced
        if multiple:
            output_list = []
            output_size = 0
            for args in command_line_args:
                running_result = generator.generate(tmp_output, max_time, max_memory, args)
                if running_result.verdict != Verdict.ACCEPTED:
                    raise RuntimeError("Generator failed to complete")
                output_size += path.getsize(tmp_output)
                if output_size > OUTPUT_LIMIT * 1024576:
                    raise RuntimeError("Output limit exceeded")
                output_list.append(get_b64_from_file(tmp_output))
            result = {'status': 'received', 'output': output_list}
        else:
            running_result = generator.generate(tmp_output, max_time, max_memory, command_line_args)
            if running_result.verdict != Verdict.ACCEPTED:
                raise RuntimeError("Generator failed to complete")
            result = {'status': 'received', 'output': get_b64_from_file(tmp_output)}
    except:
        result = reject_with_traceback()
    finally:
        try:
            generator.clean()
        except NameError:
            pass
    return result


@celery.task
def validate_handler(val_fingerprint, val_code, val_lang, max_time, max_memory, case_input_b64, multiple=False):
    try:
        validator = Validator(val_fingerprint, val_code, val_lang)
        tmp_input = validator.make_a_file_to_write()
        if multiple:
            result_list = []
            for case in case_input_b64:
                with open(tmp_input, 'wb') as fs:
                    fs.write(base64.b64decode(case))
                val_result = validator.validate(tmp_input, max_time, max_memory)
                result_list.append({'verdict': val_result.verdict.value, 'message': val_result.message})
            result = {'status': 'received', 'result': result_list}
        else:
            with open(tmp_input, 'wb') as fs:
                fs.write(base64.b64decode(case_input_b64))
            val_result = validator.validate(tmp_input, max_time, max_memory)
            result = {'status': 'received', 'verdict': val_result.verdict.value, 'message': val_result.message}
    except:
        result = reject_with_traceback()
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
                fs.write(base64.b64decode(case_runner1.run(case, result_type=RunnerResultType.OUTPUT)['output']))
            case.check_validity()
            result = case_runner2.run(case)
            if result['verdict'] != Verdict.ACCEPTED:
                report.append(base64.b64encode(open(case.input_file, 'rb').read()).decode())
                max_generate -= 1
            case.clean()
            args_idx = (args_idx + 1) % len(command_line_args_list)

        result = {'status': 'received', 'output': report}
    except:
        result = reject_with_traceback()
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