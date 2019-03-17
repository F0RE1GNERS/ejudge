#!/bin/sh
if [ `id -u` -ne 0 ]; then
    echo "Please re-run ${this_file} as root."
    exit 1
fi

core=$(grep --count ^processor /proc/cpuinfo)
n=$(($core*2))

echo "username:" $USERNAME > config/token.yaml
echo "password:" $PASSWORD >> config/token.yaml
./nsjail/setup.sh
chown compiler -R /sys/fs/cgroup/memory/NSJAIL /sys/fs/cgroup/cpu/NSJAIL /sys/fs/cgroup/pids/NSJAIL
chgrp compiler -R /sys/fs/cgroup/memory/NSJAIL /sys/fs/cgroup/cpu/NSJAIL /sys/fs/cgroup/pids/NSJAIL
chown compiler:compiler run/log run/tmp run/sub run/spj
gunicorn flask_server:flask_app --workers $n --worker-connections 1000 --error-logfile /ejudge/run/log/gunicorn.log \
    --timeout 600 --log-level warning -u compiler -g compiler --bind 0.0.0.0:5000
