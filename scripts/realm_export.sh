#!/bin/bash

SCRIPT_PATH="$(readlink -f "$0")"
SCRIPT_DIR="$(dirname "$SCRIPT_PATH")"

cd $SCRIPT_DIR/..

source .env
DATA_PATH=$(realpath "$DATA_PATH")
LOCAL_BACKUP_PATH="$DATA_PATH"/keycloak_realm

docker exec -i keycloak /bin/bash -c "/opt/keycloak/bin/kc.sh export --file /tmp/aiod.json --realm aiod --users realm_file"

if [ ! -d "$LOCAL_BACKUP_PATH" ]; then
    mkdir "$LOCAL_BACKUP_PATH"
fi

docker cp keycloak:/tmp/aiod.json "$LOCAL_BACKUP_PATH"/aiod.json
docker exec -i keycloak /bin/bash -c "rm /tmp/aiod.json"
