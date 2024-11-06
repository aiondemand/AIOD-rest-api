#!/bin/bash

profiles=""
for arg in "$@"; do
  profiles+="--profile $arg "
done

docker compose --env-file=.env --env-file=override.env ${profiles} up -d
