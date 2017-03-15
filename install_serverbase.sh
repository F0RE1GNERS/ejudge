#!/bin/sh
# Run this file for installation!

if [ `id -u` -ne 0 ]; then
    echo "Please re-run ${this_file} as root."
    exit 1
fi

docker build -f docker/serverbase/Dockerfile -t ejudge/serverbase:v2 --no-cache=true .
