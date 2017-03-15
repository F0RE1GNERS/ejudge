#!/bin/sh
# Run this file for installation!

if [ `id -u` -ne 0 ]; then
    echo "Please re-run ${this_file} as root."
    exit 1
fi

docker build -f docker/judge/Dockerfile -t ejudge/judge:v1 --no-cache=true .