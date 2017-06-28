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
        self.running_path = os.path.join(settings.round_dir, 'spj')
        self.time_limit = int(settings.max_time / 1000 * 10)

        if indicator == '':
            indicator = 'fcmp'
        search_path = [TESTLIB_BUILD_DIR, settings.data_dir]
        for path in search_path:
            if indicator in os.listdir(path):
                self.running_path = os.path.join(path, indicator)
                break
        if not os.path.exists(self.running_path):
            self.running_path = os.path.join(TESTLIB_BUILD_DIR, 'fcmp')

    def run(self, input_path, output_path, ans_path):
        """
        :return: checker exit code
        """
        return subprocess.call([self.running_path, input_path, output_path, ans_path],
                               stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT, timeout=self.time_limit)
