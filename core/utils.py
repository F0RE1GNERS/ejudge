import uuid


def read_partial_data_from_file(filename, length=1024):
    with open(filename, "r") as f:
        result = f.read(length)
    if len(result) >= length - 1:
        result += '\n......'
    return result


def format_code_for_markdown(code):
    return '\n' + code.strip('\n') + '\n'


def randomize_round_id():
    return str(uuid.uuid1())


def get_language(path):
    if path.endswith('.cpp'):
        return 'cpp'
    elif path.endswith('.py'):
        return 'python'
    elif path.endswith('.java'):
        return 'java'
