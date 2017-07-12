from shutil import rmtree
from os import path, makedirs, chmod, chown
from config.config import DATA_BASE, COMPILER_GROUP_GID, COMPILER_USER_UID


class Case(object):

    def __init__(self, fingerprint):
        self.fingerprint = fingerprint
        self._workspace = path.join(DATA_BASE, fingerprint)
        makedirs(self._workspace, exist_ok=True)
        self.input_file_stream = self.output_file_stream = None

    def write_input_binary(self, buf):
        if not self.input_file_stream:
            self.input_file_stream = open(self.input_file, 'wb')
        self.input_file_stream.write(buf)
        self.input_file_stream.close()

    def write_output_binary(self, buf):
        if not self.output_file_stream:
            self.output_file_stream = open(self.output_file, 'wb')
        self.output_file_stream.write(buf)
        self.output_file_stream.close()

    @property
    def input_file(self):
        return path.join(self._workspace, 'input')

    @property
    def output_file(self):
        return path.join(self._workspace, 'output')

    def check_validity(self):
        assert path.exists(self.input_file)
        assert path.exists(self.output_file)
        chown(self.input_file, COMPILER_USER_UID, COMPILER_GROUP_GID)
        chown(self.output_file, COMPILER_USER_UID, COMPILER_GROUP_GID)
        chmod(self.input_file, 0o600)
        chmod(self.output_file, 0o600)

    def clean(self):
        rmtree(self._workspace, ignore_errors=True)
