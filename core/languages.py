_DEFAULT_ENV = ["LANG=en_US.UTF-8", "LANGUAGE=en_US:en", "LC_ALL=en_US.UTF-8"]
_DEFAULT_ENV += ["PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"]
_DEFAULT_ENV += ["HOME=/root"]
MAX_MEMORY = 128 * 1024 * 1024


LANGUAGE_SETTINGS = {

    # C/C++
    'c': {
        "src_name": "main.c",
        "exe_name": "main",
        "max_memory": MAX_MEMORY,
        "compile_cmd": "/usr/bin/gcc -DONLINE_JUDGE -O2 -w -std=c99 {src_path} -lm -o {exe_path}",
        "exe_cmd": "{exe_path}",
        "seccomp_rule": "c_cpp",
        "env": [] + _DEFAULT_ENV
    },
    'c11': {
        "src_name": "main.c",
        "exe_name": "main",
        "max_memory": MAX_MEMORY,
        "compile_cmd": "/usr/bin/gcc -DONLINE_JUDGE -O2 -w -std=c11 {src_path} -lm -o {exe_path}",
        "exe_cmd": "{exe_path}",
        "seccomp_rule": "c_cpp",
        "env": [] + _DEFAULT_ENV
    },
    'cpp98': {
        "src_name": "main.cpp",
        "exe_name": "main",
        "max_memory": MAX_MEMORY,
        "compile_cmd": "/usr/bin/g++ -DONLINE_JUDGE -O2 -w -fmax-errors=3 -std=c++98 {src_path} -lm -o {exe_path}",
        "exe_cmd": "{exe_path}",
        "seccomp_rule": "c_cpp",
        "env": [] + _DEFAULT_ENV
    },
    'cpp': {
        "src_name": "main.cpp",
        "exe_name": "main",
        "max_memory": MAX_MEMORY,
        "compile_cmd": "/usr/bin/g++ -DONLINE_JUDGE -O2 -w -fmax-errors=3 -std=c++11 {src_path} -lm -o {exe_path}",
        "exe_cmd": "{exe_path}",
        "seccomp_rule": "c_cpp",
        "env": [] + _DEFAULT_ENV
    },
    'cpp14': {
        "src_name": "main.cpp",
        "exe_name": "main",
        "max_memory": MAX_MEMORY,
        "compile_cmd": "/usr/bin/g++ -DONLINE_JUDGE -O2 -w -fmax-errors=3 -std=c++14 {src_path} -lm -o {exe_path}",
        "exe_cmd": "{exe_path}",
        "seccomp_rule": "c_cpp",
        "env": [] + _DEFAULT_ENV
    },

    # C#
    'csharp': {
        "src_name": "main.cs",
        "exe_name": "main.exe",
        "max_memory": MAX_MEMORY,
        "compile_cmd": "/usr/bin/mcs -define:ONLINE_JUDGE -o+ -out:{exe_path} {src_path}",
        "exe_cmd": "/usr/bin/mono {exe_path}",
        "seccomp_rule": "general",
        "env": [] + _DEFAULT_ENV
    },

    # Java
    'java': {
        "src_name": "Main.java",
        "exe_name": "Main",
        "max_memory": -1,
        "compile_cmd": "/usr/bin/javac {src_path} -encoding UTF8",
        "exe_cmd": "/usr/bin/java -cp {exe_dir} -Xss1M -Xms16M -Xmx{max_memory}M "
                   "-Djava.security.manager -Dfile.encoding=UTF-8 -Djava.security.policy==/etc/java_policy "
                   "-Djava.awt.headless=true {exe_name}",
        "seccomp_rule": None,
        "env": ["MALLOC_ARENA_MAX=1"] + _DEFAULT_ENV
    },

    # Python
    'python': {
        "src_name": "solution.py",
        "exe_name": "__pycache__/solution.cpython-35.pyc",
        "max_memory": MAX_MEMORY,
        "compile_cmd": "/usr/bin/python3 -m py_compile {src_path}",
        "exe_cmd": "/usr/bin/python3 {exe_path}",
        "seccomp_rule": "general",
        "env": [] + _DEFAULT_ENV
    },
    'python2': {
        "src_name": "solution.py",
        "exe_name": "solution.pyc",
        "max_memory": MAX_MEMORY,
        "compile_cmd": "/usr/bin/python -m py_compile {src_path}",
        "exe_cmd": "/usr/bin/python {exe_path}",
        "seccomp_rule": "general",
        "env": ["PYTHONIOENCODING=UTF-8"] + _DEFAULT_ENV
    },

    # PHP
    'php': {
        "src_name": "solution.php",
        "exe_name": "solution.php",
        "max_memory": MAX_MEMORY,
        "compile_cmd": "/usr/bin/php -v",
        "exe_cmd": "/usr/bin/php {exe_path}",
        "seccomp_rule": "general",
        "env": _DEFAULT_ENV
    },

    # Fortran
    'fortran': {
        "src_name": "main.f",
        "exe_name": "main",
        "max_memory": MAX_MEMORY,
        "compile_cmd": "/usr/bin/gfortran -ffree-form {src_path} -o {exe_path}",
        "exe_cmd": "/usr/bin/php {exe_path}",
        "seccomp_rule": "general",
        "env": _DEFAULT_ENV
    },

    # Perl
    'perl': {
        "src_name": "solution.pl",
        "exe_name": "solution.pl",
        "max_memory": MAX_MEMORY,
        "compile_cmd": "/usr/bin/perl -c {src_path}",
        "exe_cmd": "/usr/bin/perl {exe_path}",
        "seccomp_rule": "general",
        "env": _DEFAULT_ENV
    },

    # Ruby
    'ruby': {
        "src_name": "solution.rb",
        "exe_name": "solution.rb",
        "max_memory": MAX_MEMORY,
        "compile_cmd": "/usr/bin/ruby -c {src_path}",
        "exe_cmd": "/usr/bin/ruby {exe_path}",
        "seccomp_rule": "general",
        "env": _DEFAULT_ENV
    },

    # Objective C
    'objc': {
        "src_name": "main.m",
        "exe_name": "main",
        "max_memory": MAX_MEMORY,
        "compile_cmd": "/usr/bin/gcc -DONLINE_JUDGE -O2 {src_path} -lm -o {exe_path} "
                       "-MMD -MP -DGNUSTEP -DGNUSTEP_BASE_LIBRARY=1 -DGNU_GUI_LIBRARY=1 -DGNU_RUNTIME=1 "
                       "-DGNUSTEP_BASE_LIBRARY=1 -fno-strict-aliasing -fexceptions -fobjc-exceptions "
                       "-D_NATIVE_OBJC_EXCEPTIONS -pthread -fPIC -Wall -DGSWARN -DGSDIAGNOSE -Wno-import "
                       "-fgnu-runtime -fconstant-string-class=NSConstantString -I. -I/usr/local/include/GNUstep "
                       "-I/usr/include/GNUstep -rdynamic -shared-libgcc -L/usr/local/lib -L/usr/lib -lgnustep-base -lobjc",
        "exe_cmd": "{exe_path}",
        "seccomp_rule": "general",
        "env": [] + _DEFAULT_ENV
    },

    # Haskell
    'haskell': {
        "src_name": "main.hs",
        "exe_name": "main",
        "compile_cmd": "/usr/bin/ghc --make -O {src_path}",
        "exe_cmd": "{exe_path}",
        "seccomp_rule": "general",
        "env": [] + _DEFAULT_ENV,
        "max_memory": MAX_MEMORY,
    },

    # Lua
    'lua': {
        "src_name": "main.lua",
        "exe_name": "main.lua",
        "max_memory": MAX_MEMORY,
        "compile_cmd": "/usr/bin/lua5.3 -v",
        "exe_cmd": "/usr/bin/lua5.3 {exe_path}",
        "seccomp_rule": "general",
        "env": [] + _DEFAULT_ENV
    },

    'lisp': {
        "src_name": "main.lisp",
        "exe_name": "main",
        "max_memory": MAX_MEMORY,
        "compile_cmd": "/usr/bin/clisp -c {src_path} -o {exe_path}",
        "exe_cmd": "{exe_path}",
        "seccomp_rule": "general",
        "env": [] + _DEFAULT_ENV
    },
    'r': {
        "src_name": "solution.R",
        "exe_name": "solution.R",
        "compile_cmd": "/usr/bin/R --version",
        "exe_cmd": "/usr/bin/Rscript {exe_path}",
        "env": [] + _DEFAULT_ENV,
        "max_memory": MAX_MEMORY,
        "seccomp_rule": "general",
    },
    'rust': {
        "src_name": "main.rs",
        "exe_name": "main",
        "compile_cmd": "/usr/bin/rustc -O {src_path} -o {exe_path}",
        "exe_cmd": "{exe_path}",
        "env": [] + _DEFAULT_ENV,
        "max_memory": MAX_MEMORY,
        "seccomp_rule": "general",
    },
    'pascal': {
        "src_name": "main.pas",
        "exe_name": "main",
        "compile_cmd": "/usr/bin/fpc -O2 -Sgic -dONLINE_JUDGE -Mdelphi {src_path} -o{exe_path}",
        "exe_cmd": "{exe_path}",
        "env": [] + _DEFAULT_ENV,
        "max_memory": MAX_MEMORY,
        "seccomp_rule": "general",
    },
    'swift': {
        "src_name": "main.swift",
        "exe_name": "main",
        "compile_cmd": "/usr/bin/swiftc -O {src_path} -o {exe_path}",
        "exe_cmd": "{exe_path}",
        "env": [] + _DEFAULT_ENV,
        "max_memory": MAX_MEMORY,
        "seccomp_rule": "general",
    },
    'pypy2': {
        "src_name": "solution.py",
        "exe_name": "__pycache__/solution.pypy-41.pyc",
        "compile_cmd": "/usr/bin/pypy -m py_compile {src_path}",
        "exe_cmd": "/usr/bin/pypy {exe_path}",
        "env": [] + _DEFAULT_ENV,
        "max_memory": MAX_MEMORY,
        "seccomp_rule": "general",
    },
    'fsharp': {
        "src_name": "main.fs",
        "exe_name": "main.exe",
        "compile_cmd": "/usr/bin/fsharpc -d ONLINE_JUDGE -O -o {exe_path} {src_path}",
        "exe_cmd": "/usr/bin/mono {exe_path}",
        "env": [] + _DEFAULT_ENV,
        "max_memory": MAX_MEMORY,
        "seccomp_rule": "general",
    },
    'ocaml': {
        "src_name": "main.ml",
        "exe_name": "main",
        "compile_cmd": "/usr/bin/ocamlc {src_path} -o {exe_path}",
        "exe_cmd": "{exe_path}",
        "env": [] + _DEFAULT_ENV,
        "max_memory": MAX_MEMORY,
        "seccomp_rule": "general",
    },
    'scala': {
        "src_name": "Main.scala",
        "exe_name": "Main",
        "max_memory": -1,
        "compile_cmd": "/usr/bin/scalac -d {exe_dir} -encoding UTF8 -target:jvm-1.8 -optimise {src_path}",
        "exe_cmd": "/usr/bin/scala -cp {exe_dir} -J-Xss1M -J-Xms16M -J-Xmx{max_memory}M {exe_name}",
        "env": [] + _DEFAULT_ENV,
        "seccomp_rule": "general",
    },
    'js': {
        "src_name": "solution.js",
        "exe_name": "solution.js",
        "compile_cmd": "/usr/bin/node -v",
        "exe_cmd": "/usr/bin/node {exe_path}",
        "env": [] + _DEFAULT_ENV,
        "max_memory": MAX_MEMORY,
        "seccomp_rule": "general",
    },
    'go': {
        "src_name": "main.go",
        "exe_name": "main",
        "compile_cmd": "usr/bin/go build -o {exe_path} {src_path}",
        "exe_cmd": "{exe_path}",
        "env": [] + _DEFAULT_ENV,
        "max_memory": MAX_MEMORY,
        "seccomp_rule": "general",
    },
}
