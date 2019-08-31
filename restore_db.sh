#/bin/sh

set -e

DB_CONTAINER=db
DB_NAME=rtd
DB_USER=docs

docker-compose up -d "${DB_CONTAINER}"
sleep 20
docker-compose exec -T "${DB_CONTAINER}" dropdb -U postgres "${DB_NAME}" --if-exists
docker-compose exec -T "${DB_CONTAINER}" createuser -U postgres "${DB_USER}" -P
docker-compose exec -T "${DB_CONTAINER}" createdb -U postgres -O "${DB_USER}" "${DB_NAME}"
docker-compose exec -T "${DB_CONTAINER}"  psql -U "${DB_USER}" -d "${DB_NAME}" < "${1}"
docker-compose stop "${DB_CONTAINER}"
