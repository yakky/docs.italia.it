#!/bin/sh

set -e

docker/dirs.sh
/virtualenv/bin/celery worker $*
