_DEFAULT_ENV = ["LANG=en_US.UTF-8", "LANGUAGE=en_US:en", "LC_ALL=en_US.UTF-8"]

LANGUAGE_SETTINGS = {

    # C/C++
    'c': {
        "src_name": "main.c",
        "exe_name": "main",
        "max_memory": 128 * 1024 * 1024,
        "compile_cmd": "/usr/bin/gcc -DONLINE_JUDGE -O2 -w -std=c99 {src_path} -lm -o {exe_path}",
        "exe_cmd": "{exe_path}",
        "seccomp_rule": "c_cpp",
        "env": [] + _DEFAULT_ENV
    },
    'c11': {
        "src_name": "main.c",
        "exe_name": "main",
        "max_memory": 128 * 1024 * 1024,
        "compile_cmd": "/usr/bin/gcc -DONLINE_JUDGE -O2 -w -std=c11 {src_path} -lm -o {exe_path}",
        "exe_cmd": "{exe_path}",
        "seccomp_rule": "c_cpp",
        "env": [] + _DEFAULT_ENV
    },
    'cpp98': {
        "src_name": "main.cpp",
        "exe_name": "main",
        "max_memory": 128 * 1024 * 1024,
        "compile_cmd": "/usr/bin/g++ -DONLINE_JUDGE -O2 -w -fmax-errors=3 -std=c++98 {src_path} -lm -o {exe_path}",
        "exe_cmd": "{exe_path}",
        "seccomp_rule": "c_cpp",
        "env": [] + _DEFAULT_ENV
    },
    'cpp': {
        "src_name": "main.cpp",
        "exe_name": "main",
        "max_memory": 128 * 1024 * 1024,
        "compile_cmd": "/usr/bin/g++ -DONLINE_JUDGE -O2 -w -fmax-errors=3 -std=c++11 {src_path} -lm -o {exe_path}",
        "exe_cmd": "{exe_path}",
        "seccomp_rule": "c_cpp",
        "env": [] + _DEFAULT_ENV
    },
    'cpp14': {
        "src_name": "main.cpp",
        "exe_name": "main",
        "max_memory": 128 * 1024 * 1024,
        "compile_cmd": "/usr/bin/g++ -DONLINE_JUDGE -O2 -w -fmax-errors=3 -std=c++14 {src_path} -lm -o {exe_path}",
        "exe_cmd": "{exe_path}",
        "seccomp_rule": "c_cpp",
        "env": [] + _DEFAULT_ENV
    },

    # C#
    'csharp': {
        "src_name": "main.cs",
        "exe_name": "main.exe",
        "max_memory": 128 * 1024 * 1024,
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
        "max_memory": 128 * 1024 * 1024,
        "compile_cmd": "/usr/bin/python3 -m py_compile {src_path}",
        "exe_cmd": "/usr/bin/python3 {exe_path}",
        "seccomp_rule": "general",
        "env": [] + _DEFAULT_ENV
    },
    'python2': {
        "src_name": "solution.py",
        "exe_name": "solution.pyc",
        "max_memory": 128 * 1024 * 1024,
        "compile_cmd": "/usr/bin/python -m py_compile {src_path}",
        "exe_cmd": "/usr/bin/python {exe_path}",
        "seccomp_rule": "general",
        "env": ["PYTHONIOENCODING=UTF-8"] + _DEFAULT_ENV
    },

    # PHP
    'php': {
        "src_name": "solution.php",
        "exe_name": "solution.php",
        "max_memory": 128 * 1024 * 1024,
        "compile_cmd": "/usr/bin/php -v",
        "exe_cmd": "/usr/bin/php {exe_path}",
        "seccomp_rule": "general",
        "env": _DEFAULT_ENV
    },


}
