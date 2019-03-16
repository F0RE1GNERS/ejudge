"""

    Basically, the programs submitted are called submissions.

    There are certain "submissions", which are submitted by judges, such as generators, checkers, interactors...
    These submissions are trusted and of certain usage.
    This file implements certain judge "submissions" and the way of running them.

    The args are same as the famous testlib.h, which is the following:

    Check, using testlib running format:
      check.exe <Input_File> <Output_File> <Answer_File> [<Result_File>],
    If result file is specified it will contain results.

    Validator, using testlib running format:
      validator.exe < input.txt,
    It will return non-zero exit code and writes message to standard output.

    Generator, using testlib running format:
      gen.exe [parameter-1] [parameter-2] [... paramerter-n]
    You can write generated test(s) into standard output or into the file(s).

    Interactor, using testlib running format:
      interactor.exe <Input_File> <Output_File> [<Answer_File> [<Result_File>]],
    Reads test from inf (mapped to args[1]), writes result to tout (mapped to argv[2],
    can be judged by checker later), reads program output from ouf (mapped to stdin),
    writes output to program via stdout (use cout, printf, etc).

    Note that in both checker and interactor, our implementation does not support variable-length args after Result_File.

    Just like submissions return Sandbox.Result directly, trusted submissions return SpecialJudge.Result.
    The result contains two arguments, namely:
    - verdict: directly defined in config.config, can be used as the final verdict
    - message: compile error message and, most importantly, result file content (first 512 bytes)

"""
from os import path, listdir

from config.config import Verdict, SPJ_BASE, LANGUAGE_CONFIG
from core.submission import Submission


class SpecialJudge(Submission):

  def __init__(self, lang, fingerprint=None, exe_file=None):
    if exe_file is not None:
      super().__init__(lang, exe_file=exe_file)
    elif fingerprint is not None:
      super().__init__(lang, exe_file=path.join(SPJ_BASE, fingerprint + "." + LANGUAGE_CONFIG[lang]["exe_ext"]))
    else:
      raise AssertionError

  def clean(self):
    pass   # do nothing

  @classmethod
  def fromExistingFingerprint(cls, fingerprint):
    exe_file, lang = None, None
    for file in listdir(SPJ_BASE):
      if file.startswith(fingerprint + "."):
        exe_file = path.join(SPJ_BASE, file)
        break
    if not exe_file:
      raise FileNotFoundError("SPJ fingerprint does not exist")
    file_ext = exe_file.split(".")[-1]
    for candidate_lang in LANGUAGE_CONFIG:
      if LANGUAGE_CONFIG[candidate_lang]["exe_ext"] == file_ext:
        lang = candidate_lang
    if not lang:
      raise FileNotFoundError("SPJ language not recognized")
    return cls(lang, exe_file=exe_file)

  def get_verdict_from_test_result(self, checker_result):
    """
    :param checker_result: a Sandbox.Result directly returned from checker running
    :return: an integer, one of the verdict
    """
    if checker_result.verdict != Verdict.ACCEPTED:
      # The following follows testlib's convention
      if checker_result.exit_code == 3:
        return Verdict.JUDGE_ERROR
      if checker_result.exit_code == 7:
        return Verdict.POINT
      if checker_result.verdict != Verdict.RUNTIME_ERROR:
        return checker_result.verdict
      return Verdict.WRONG_ANSWER
    return Verdict.ACCEPTED
