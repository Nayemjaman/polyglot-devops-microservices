#!/usr/bin/env sh
set -eu

cd "$(dirname "$0")"

COMPOSE_FILES="-f docker-compose.yml -f docker-compose.ec2.yml"

docker compose $COMPOSE_FILES pull
docker compose $COMPOSE_FILES up -d --no-build
docker compose $COMPOSE_FILES ps
