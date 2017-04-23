#!/bin/sh
# Running now

if [ `id -u` -ne 0 ]; then
    echo "Please re-run ${this_file} as root."
    exit 1
fi

core=$(grep --count ^processor /proc/cpuinfo)
n=$(($core*4))
redis-server &
celery worker -A config.celery &
gunicorn server:app --workers $n --worker-connections 200 --error-logfile /var/log/gunicorn.log --timeout 3600 --graceful-timeout 3600 --worker-class gevent --bind 0.0.0.0:4999
