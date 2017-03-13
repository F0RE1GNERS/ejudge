import os, re
from .program import Program
from config import *
from .utils import read_partial_data_from_file


# This class is meant to deal with IO for judges
# No further explanations...
class Judge(Program):
    def __init__(self, submission, config, round_id):
        super().__init__(submission, config, round_id)

        self.input_path = self.output_path
        self.output_path = os.path.join(self.round_dir, 'judge_result')
        self.judge_ans_path = os.path.join(self.round_dir, 'judge_ans')
        self.judge_in_path = os.path.join(self.round_dir, 'in')
        self.judge_new_input_path = os.path.join(self.round_dir, 'judge_new_input')
        self.seccomp_rule_name = None
        self.base_run_cmd = self.run_cmd

    def generate_default_run_cmd(self):
        self.run_cmd = self.base_run_cmd
        self.run_cmd.append(self.judge_in_path)
        self.run_cmd.append(self.judge_ans_path)
        self.run_cmd.append(self.judge_new_input_path)

    def generate_new_file_for_judge(self, path):
        if not os.path.exists(path):
            open(path, "w").close()
        os.chmod(path, mode=0o666)

    def run(self):
        self.generate_default_run_cmd()
        self.generate_new_file_for_judge(self.judge_in_path)
        self.generate_new_file_for_judge(self.judge_ans_path)
        self.generate_new_file_for_judge(self.judge_new_input_path)
        res = super().run()
        if res['result'] > 0:
            print('Judge Debug: ' + read_partial_data_from_file(self.log_path))
        return self._judge_text_processing()

    # Returning a dict of all the things to do
    def _judge_text_processing(self):
        result = dict()

        result['continue'] = False
        result['score'] = 0
        result['message'] = 0
        result['data'] = ''

        with open(self.output_path, "r") as f:
            result['data'] = f.read()
            raw_text = re.sub(r"'.*?'", ' ', result['data'])
            raw_text = re.split(r'[^A-Za-z0-9]', raw_text)
            text = []
            for t in raw_text:
                if t != '':
                    text.append(t)
            text = ' '.join(text)
            text = text.lower()

            if re.search(r'\bcontinue\b', text) is not None:
                result['continue'] = True

            if re.search(r'\bstop\b', text) is not None:
                result['continue'] = False

            if re.search(r'\b(ok|yes|right|correct)\b', text) is not None:
                result['score'] = 100
                result['message'] = CORRECT

            if re.search(r'\b(no|wrong)\b', text) is not None:
                result['score'] = 0
                result['message'] = WRONG_ANSWER

            pattern = re.search(r'(score|point)[ds]? \d+', text)
            if pattern is not None:
                num = int(re.search(r'\d+', pattern.group()).group())
                num = min(max(num, 0), 100)
                result['score'] = num
                result['message'] = OK

            if re.search(r'idleness limit exceeded', text) is not None:
                result['score'] = 0
                result['continue'] = False
                result['message'] = IDLENESS_LIMIT_EXCEEDED

        return result