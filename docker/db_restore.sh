#!/usr/bin/env sh

set -e

DB_CONTAINER=db
DB_NAME=rtd
DB_USER=docs

if [ $# != 1 ]; then
  echo "Destination dump file required"
  exit 1
fi

echo "Restoring database from '$1'"
docker-compose up -d "${DB_CONTAINER}"
sleep 10
docker-compose exec -T "${DB_CONTAINER}" dropdb -U postgres "${DB_NAME}" --if-exists
docker-compose exec -T "${DB_CONTAINER}" dropuser -U postgres "${DB_USER}" --if-exists
docker-compose exec -T "${DB_CONTAINER}" createuser -U postgres "${DB_USER}"
docker-compose exec -T "${DB_CONTAINER}" createdb -U postgres -O "${DB_USER}" "${DB_NAME}"
docker-compose exec -T "${DB_CONTAINER}"  psql -U "${DB_USER}" -d "${DB_NAME}" < "${1}"
