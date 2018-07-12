import string
import random
import signal
from os import fdopen


def try_to_open_file(*args):
    """ try to open multiple files
    *args: pass (path / file object, mode) tuple, and return file-like objects list
    """
    lst = []
    appear = {}
    for foo, mode in args:
        if isinstance(foo, str):
            file = appear.get((foo, mode))
            if file is None:
                file = open(foo, mode)
                appear[(foo, mode)] = file
            lst.append(file)
        else:
            lst.append(foo)
    return lst


def format(s, as_list=False, **kwargs):
    if isinstance(s, list):
        a = []
        for t in s:
            a.extend(format(t, as_list=True, **kwargs))
        return a
    if not as_list:
        return s.format(**kwargs)
    else:
        v = []
        for token in s.split(' '):
            if token.startswith("{") and token.endswith("}") and token[1:-1] in kwargs:
                v.extend(kwargs[token[1:-1]])
            else:
                v.append(token.format(**kwargs))
        return list(filter(lambda x: x, v)) # filter out empty strings


def random_string(length=32):
    return ''.join(list(random.choice(string.ascii_letters) for i in range(length)))


def get_signal_name(signal_num):
    try:
        return signal.Signals(signal_num).name
    except:
        return 'SIG%03d' % signal_num


def serialize_sandbox_result(result):
    'Can be also used for TrustedSubmission.Result'
    d = result.__dict__.copy()
    d['verdict'] = d['verdict'].value
    return d
