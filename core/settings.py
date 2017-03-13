import os
from config import DATA_DIR, ROUND_DIR
from .judge import Judge
from .utils import randomize_round_id

class RoundSettings:

    def __init__(self, data):
        self.max_time = data['max_time']
        self.max_sum_time = data['max_sum_time']
        self.max_memory = data['max_memory']
        self.judge = Judge(data['judge'])
        self.problem_id = data['problem_id']
        self.round_id = randomize_round_id()
        self.data_dir = os.path.join(DATA_DIR, str(self.problem_id))
        self.round_dir = os.path.join(ROUND_DIR, str(self.round_id))
