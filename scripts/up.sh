#!/bin/bash

profiles=""
for arg in "$@"; do
  profiles+="--profile $arg "
done

source .env
source override.env
compose_with_dev=""
if [[ -n "${AIOD_MOUNT}" ]]; then
  compose_with_dev="-f docker-compose.dev.yaml"
fi

command="docker compose --env-file=.env --env-file=override.env -f docker-compose.yaml ${compose_with_dev} ${profiles} up -d"
echo "${command}"
eval "${command}"

