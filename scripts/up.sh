#!/bin/bash

profiles=""
for arg in "$@"; do
  profiles+="--profile $arg "
done

NC='\033[0m' # No Color
CYAN='\033[1;36m'
GREEN='\033[0;32m'

source .env
source override.env

if [[ "${USE_LOCAL_DEV}" == "true" ]]; then
  compose_with_dev="-f docker-compose.dev.yaml"
  echo -e "Launching ${CYAN}with${NC} local changes."
else
  compose_with_dev=""
  echo -e "Launching ${GREEN}without${NC} local changes."
fi

command="docker compose --env-file=.env --env-file=override.env -f docker-compose.yaml ${compose_with_dev} ${profiles} up -d"
echo "${command}"
eval "${command}"

