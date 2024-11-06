#!/bin/bash

profiles=""
for arg in "$@"; do
  profiles+="--profile $arg "
done

docker compose --env-file=.env --env-file=override.env -f docker-compose.yaml -f docker-compose.dev.yaml ${profiles} up -d

