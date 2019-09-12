#!/usr/bin/env sh

set -e

docker/dirs.sh
if [ "$1" = "collect" ]; then
  cp -a media /home/documents/
  /virtualenv/bin/python manage.py collectstatic --no-input -c
fi
sleep 10
/virtualenv/bin/python manage.py provision_elasticsearch --ensure-no-index
/virtualenv/bin/gunicorn --error-logfile="-"  readthedocs.wsgi:application $*
