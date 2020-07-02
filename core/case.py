from os import path, makedirs
from config import DATA_BASE


class Case(object):

  def __init__(self, fingerprint):
    self.fingerprint = fingerprint
    self.input_file = self._get_data_path("in", fingerprint)
    self.output_file = self._get_data_path("out", fingerprint)
    self.input_file_stream = self.output_file_stream = None

  def _get_data_path(self, category, hash):
    parts = [DATA_BASE, category]
    if len(hash) >= 2:
      parts.append(hash[:2])
    else:
      parts.append("??")
    if len(hash) >= 4:
      parts.append(hash[2:4])
    else:
      parts.append("??")
    directory = path.join(*parts)
    makedirs(directory, exist_ok=True)
    parts.append(hash)
    return path.join(*parts)

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

  def check_validity(self):
    assert path.exists(self.input_file)
    assert path.exists(self.output_file)
