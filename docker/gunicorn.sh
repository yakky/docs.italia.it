#!/usr/bin/env sh

set -e

docker/dirs.sh
if [ "$1" = "collect" ]; then
  cp -a media /home/documents/
  /virtualenv/bin/python manage.py collectstatic --no-input -c
fi
/virtualenv/bin/gunicorn --error-logfile="-"  readthedocs.wsgi:application $*
