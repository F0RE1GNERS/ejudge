import uuid
import os
import re


def import_data(path):

    result = {}
    if not os.path.exists(path):
        return result
    raw_file_list = os.listdir(path)
    file_set = set(raw_file_list)
    patterns = {'.in$': ['.out', '.ans'], 'input': ['output', 'answer']}

    for file in raw_file_list:
        for pattern_in, pattern_out in patterns.items():
            if re.search(pattern_in, file) is not None:
                for pattern in pattern_out:
                    try_str = re.sub(pattern_in, pattern, file)
                    if try_str in file_set:
                        file_set.remove(try_str)
                        file_set.remove(file)
                        result[file] = try_str
                        break

    return result


def read_partial_data_from_file(filename, length=4096):
    with open(filename, "r") as f:
        result = f.read(length)
    if len(result) >= length - 1:
        result += '\n......'
    return result


def randomize_round_id():
    return str(uuid.uuid1())
