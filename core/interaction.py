import os
import pickle
import shutil
from os import pipe, fork, close, fdopen, _exit, path
from threading import Thread

from config.config import Verdict
from core.runner import CaseRunner
from core.submission import Submission
from core.util import random_string


def stream_proxy_run(record_file_name, input_fd, output_fd):
  with open(record_file_name, "wb") as stream:
    buffer_size = 65536
    while True:
      buffer = os.read(input_fd, buffer_size)
      if not buffer:
        break
      stream.write(buffer)
      os.write(output_fd, buffer)
  os.close(input_fd)
  os.close(output_fd)


class InteractiveRunner(CaseRunner):

  def __init__(self, submission, interactor, checker, max_time, max_memory, report_file=None):
    super().__init__(submission, checker, max_time, max_memory, report_file=report_file)
    self.interactor = interactor

  def initiate_case(self, case):
    super().initiate_case(case)
    self.case_input_name = "copy_" + random_string()
    self.case_output_name = "copy_" + random_string()
    shutil.copyfile(self.case.input_file, path.join(self.trusted_workspace, self.case_input_name))
    shutil.copyfile(self.case.output_file, path.join(self.trusted_workspace, self.case_output_name))

  def run(self, case):
    self.initiate_case(case)

    running_output = self.make_a_file_to_write()
    running_stderr = self.make_a_file_to_write()
    interactor_result_file = self.make_a_file_to_write()
    record_in = self.make_a_file_to_write()
    record_out = self.make_a_file_to_write()

    proxy1_rd, sub_wr = pipe()
    int_rd, proxy1_wr = pipe()
    proxy2_rd, int_wr = pipe()
    sub_rd, proxy2_wr = pipe()
    results = [None, None]

    def run_submission_helper():
      results[0] = self.submission.run(max_time=self.max_time, max_memory=self.max_memory,
                          stdin_file="/dev/fd/%d" % sub_rd, stdout_file="/dev/fd/%d" % sub_wr,
                          stderr_file=running_stderr, working_directory=self.workspace)

    def run_interaction_helper():
      results[1] = self.interactor.run(
        stdin_file="/dev/fd/%d" % sub_rd, stdout_file="/dev/fd/%d" % sub_wr, stderr_file="/dev/null",
        max_time=self.max_time, max_memory=self.max_memory, working_directory=self.trusted_workspace,
        extra_files=[(self.case.input_file, "in", "R"), (running_output, "out", "R"),
                     (self.case.output_file, "ans", "R"), (interactor_result_file, "result", "B")],
        extra_arguments=["in", "out", "ans", "result"]
      )

    process1 = Thread(target=run_submission_helper)
    process2 = Thread(target=run_interaction_helper)
    proxy1 = Thread(target=stream_proxy_run, args=(record_out, proxy1_rd, proxy1_wr))
    proxy2 = Thread(target=stream_proxy_run, args=(record_in, proxy2_rd, proxy2_wr))

    process1.start()
    process2.start()
    proxy1.start()
    proxy2.start()

    process1.join()
    process2.join()
    proxy1.join()
    proxy2.join()

    running_result, interactor_result = results
    if running_result.verdict != Verdict.ACCEPTED:
      result = self.running_fail_result(running_result)
      checker_message = result.get('message', '')
    elif interactor_result.verdict != Verdict.ACCEPTED:
      result = {'verdict': interactor_result.verdict}
      checker_message = self.get_message_from_file(interactor_result_file)
    else:
      result = self.do_check(running_output, running_result)
      checker_message = result.pop('message', '')
    if self.report_file:
      self.write_report(running_output, running_stderr, running_result, result, checker_message,
                        interacts=[record_in, record_out])
    return result
