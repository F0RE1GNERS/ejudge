_DEFAULT_ENV = ["LANG=en_US.UTF-8", "LANGUAGE=en_US:en", "LC_ALL=en_US.UTF-8"]
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
        "exe_cmd": "/usr/bin/java -cp {exe_dir} -Xss1M -XX:MaxPermSize=16M -XX:PermSize=8M -Xms16M -Xmx{max_memory}M "
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
        "compile_cmd": "/usr/bin/gcc -DONLINE_JUDGE -O2 {src_path} -lm -o {exe_path} `gnustep-config --objc-flags` "
                       "`gnustep-config --base-libs`",
        "exe_cmd": "{exe_path}",
        "seccomp_rule": "general",
        "env": [] + _DEFAULT_ENV
    },

    # Haskell
    'haskell': {
        "src_name": "main.hs",
        "exe_name": "main",
        "max_memory": MAX_MEMORY,
        "compile_cmd": "/usr/bin/ghc --make -O {src_path}",
        "exe_cmd": "{exe_path}",
        "seccomp_rule": "general",
        "env": [] + _DEFAULT_ENV
    },

    # Scala TODO: might be unusable
    'scala': {
        "src_name": "Main.scala",
        "exe_name": "Main",
        "max_memory": MAX_MEMORY,
        "compile_cmd": "/usr/bin/scalac {src_path}",
        "exe_cmd": "/usr/bin/scala {exe_path}",
        "seccomp_rule": "general",
        "env": [] + _DEFAULT_ENV
    },

    # Lua
    'lua': {
        "src_name": "main.lua",
        "exe_name": "main.lua",
        "max_memory": MAX_MEMORY,
        "compile_cmd": "/usr/bin/lua5.3 {src_path}",
        "exe_cmd": "/usr/bin/lua5.3 {exe_path}",
        "seccomp_rule": "general",
        "env": [] + _DEFAULT_ENV
    },

    'lisp': {
        "src_name": "main.lisp",
        "exe_name": "main.lisp",
        "max_memory": MAX_MEMORY,
        "compile_cmd": "/usr/bin/clisp --version",
        "exe_cmd": "/usr/bin/clisp {exe_path}",
        "seccomp_rule": "general",
        "env": [] + _DEFAULT_ENV
    }


}
