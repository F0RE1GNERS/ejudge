"""
    Runner is what comes in when running
    When runner is run, a Multiprocessing pool is recommended.

    Runner returns result as a dict.
    - Only when the result is ACCEPTED or WRONG_ANSWER, will the dict contains "time"
    - The dict will contain "message" when it feels necessary
    - When submission fails to compile, a CompileError is raised;
      when trusted submission fails to compile, JUDGE_ERROR is returned.

"""
import shutil
from os import path, chown
import base64

from config import Verdict, USUAL_READ_SIZE, COMPILER_USER_UID, COMPILER_GROUP_GID, LIB_BASE
from core.util import get_signal_name, random_string, make_temp_dir


class CaseRunner(object):

  def __init__(self, submission, checker, max_time, max_memory, report_file=None):
    self.submission = submission
    self.checker = checker
    self.max_time = max_time
    self.max_memory = max_memory
    self.report_file = report_file
    self.trusted_workspace = make_temp_dir()
    self.workspace = make_temp_dir()

  def clean(self):
    shutil.rmtree(self.workspace)
    shutil.rmtree(self.trusted_workspace)

  def initiate_case(self, case):
    self.case = case
    self.case.check_validity()

  def make_a_file_to_write(self):
    mpath = path.join(self.trusted_workspace, "tmpfile_" + random_string())
    open(mpath, 'w').close()
    chown(mpath, COMPILER_USER_UID, COMPILER_GROUP_GID)
    return mpath

  def run(self, case):
    self.initiate_case(case)

    running_output = self.make_a_file_to_write()
    running_stderr = self.make_a_file_to_write()
    running_result = self.submission.run(max_time=self.max_time, max_memory=self.max_memory,
                                         stdin_file=self.case.input_file, stdout_file=running_output,
                                         stderr_file=running_stderr, working_directory=self.workspace)

    if running_result.verdict != Verdict.ACCEPTED:
      # If sub fails to run, the result is final
      result = self.running_fail_result(running_result)
      checker_message = result.get('message', '')  # message is kept
    else:
      result = self.do_check(running_output, running_result)
      checker_message = result.pop('message', '')  # message is popped
    if self.report_file:
      self.write_report(running_output, running_stderr, running_result, result, checker_message)
    return result

  def read_output_as_b64(self, file):
    try:
      with open(file, 'r') as handler:
        txt = handler.read(USUAL_READ_SIZE)
        if handler.read(1):
          txt += '...'
    except:
      txt = '...'
    return self.encode_as_b64(txt)

  def encode_as_b64(self, txt):
    return base64.b64encode(txt.encode()).decode()

  def running_fail_result(self, running_result):
    assert running_result.verdict != Verdict.ACCEPTED
    result = dict()
    result["verdict"] = running_result.verdict
    result["time"] = running_result.time
    result["memory"] = running_result.memory
    if running_result.verdict == Verdict.RUNTIME_ERROR:
      result["message"] = get_signal_name(running_result.signal)
    return result

  def do_check(self, running_output, running_result):
    result = dict()
    result_file = self.make_a_file_to_write()
    with open(running_output) as f:
      print('Running output:', f.read())
    if self.checker.exe_file.startswith(LIB_BASE):
      # trusted checker in LIB_BASE
      # not using sandbox to accelerate
      checker_result = self.checker.run_unsafe_for_binary(
        max_time=self.max_time,
        working_directory=self.trusted_workspace,
        extra_arguments=[self.case.input_file, running_output, self.case.output_file, result_file]
      )
    else:
      stdout_file = self.make_a_file_to_write()
      stderr_file = self.make_a_file_to_write()
      checker_result = self.checker.run(
        stdin_file="/dev/null", stdout_file=stdout_file, stderr_file=stderr_file,
        max_time=self.max_time, max_memory=self.max_memory, working_directory=self.trusted_workspace,
        extra_files=[(self.case.input_file, "in", "R"), (running_output, "out", "R"),
                     (self.case.output_file, "ans", "R"), (result_file, "result", "B")],
        extra_arguments=["in", "out", "ans", "result"]
      )
      with open(stdout_file) as f:
        print("Stdout:", f.read())
      with open(stderr_file) as f:
        print("Stderr:", f.read())
    result["message"] = self.checker.get_message_from_file(result_file, cleanup=True)
    result["verdict"] = self.checker.get_verdict_from_test_result(checker_result)
    if result["verdict"] == Verdict.POINT:
      try:
        result["point"] = float(result["message"].lstrip().split(maxsplit=1)[0])
      except:
        result["point"] = 0.0
    result["time"] = running_result.time
    result["memory"] = running_result.memory
    print(checker_result)
    print(result)
    return result

  def write_report(self, running_output, running_stderr, running_result, final_result, checker_message,
                   interacts=None):
    input_b64 = self.read_output_as_b64(self.case.input_file)
    output_b64 = self.read_output_as_b64(running_output)
    err_b64 = self.read_output_as_b64(running_stderr)
    answer_b64 = self.read_output_as_b64(self.case.output_file)
    checker_b64 = self.encode_as_b64(checker_message)
    s = 'time: %.3fs, memory: %.3f MB, exit code: %d, verdict: %s|%s|%s|%s|%s|%s' % (
      running_result.time, running_result.memory, running_result.exit_code, final_result['verdict'].name,
      input_b64, output_b64, err_b64, answer_b64, checker_b64
    )
    if interacts:
      for file in interacts:
        s += "|%s" % self.read_output_as_b64(file)
    self.report_file.write(s + "\n")
