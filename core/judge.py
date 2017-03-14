import os
import shutil
import subprocess
from config import *


class Judge:
    def __init__(self, indicator, settings):
        """
        initialize a checker
        :param indicator: the name of the checker (usually a filename)
        :param settings: related settings
        """
        if indicator == '':
            indicator = 'fcmp'
        search_path = [TESTLIB_BUILD_DIR, settings.data_dir]
        self.running_path = os.path.join(settings.round_dir, 'spj')
        self.input_path = settings.input_path
        self.output_path = settings.output_path
        self.ans_path = settings.ans_path
        for path in search_path:
            if indicator in os.listdir(path):
                assert os.path.exists(os.path.join(path, indicator))
                shutil.copyfile(os.path.join(path, indicator), self.running_path)
                assert os.path.exists(self.running_path)
                break
        if not os.path.exists(self.running_path):
            try:
                shutil.copyfile(os.path.join(TESTLIB_BUILD_DIR, 'fcmp'), self.running_path)
            except OSError:
                print('Judge seems to be not installed?')
                raise OSError

        # Don't forget to add permission to judge
        os.chmod(self.running_path, 0o755)

    def run(self):
        """
        :return: checker exit code
        """
        return subprocess.call([self.running_path, self.input_path, self.output_path, self.ans_path],
                               stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT, timeout=10)
