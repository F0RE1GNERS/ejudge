class CompileError(Exception):

  def __init__(self, detail):
    self.detail = detail

  def __repr__(self):
    return 'CompileError: %s' % self.detail
