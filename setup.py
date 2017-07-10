from distutils.core import setup
from distutils.extension import Extension
from Cython.Build import cythonize

extensions = [
    Extension("sandbox.seccomp", ["sandbox/seccomp.pyx"], libraries=["seccomp"])
]

setup(
    name = 'sandbox',
    ext_modules = cythonize(extensions),
)