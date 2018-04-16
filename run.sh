#!/bin/sh
if [ `id -u` -ne 0 ]; then
    echo "Please re-run ${this_file} as root."
    exit 1
fi

core=$(grep --count ^processor /proc/cpuinfo)
n=$(($core*2))

service memcached start
service redis-server start
# TODO: fix celery has to be restarted manually after restart the docker
celery multi start worker -A handler \
    --pidfile="/ejudge/run/log/celery-%n.pid" \
    --logfile="/ejudge/run/log/celery-%n%I.log"
gunicorn flask_server:flask_app --workers $n --worker-connections 1000 --error-logfile /ejudge/run/log/gunicorn.log \
    --timeout 600 --worker-class gevent --log-level warning --bind 0.0.0.0:5000
