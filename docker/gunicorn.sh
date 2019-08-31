#!/bin/sh

set -e

docker/dirs.sh
if [ "$1" = "collect" ]; then
  cp -a media /home/documents/
  /virtualenv/bin/python manage.py collectstatic -c --no-input
fi
/virtualenv/bin/gunicorn --error-logfile="-"  readthedocs.wsgi:application $*
