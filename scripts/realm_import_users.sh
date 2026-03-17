#!/bin/bash
# script to import users into keycloak without breaking the realm config
# fixes issue #304

set -euo pipefail # stop on errors

# set variables or use defaults
KEYCLOAK_CONTAINER="${KEYCLOAK_CONTAINER:-keycloak}"
KEYCLOAK_REALM="${KEYCLOAK_REALM:-aiod}"
EXPORT_DIR="${EXPORT_DIR:-./keycloak-exports}"

# get file from args or use default
USERS_FILE="${1:-${EXPORT_DIR}/aiod-users.json}"
CONTAINER_TMP="/tmp/keycloak-import"

# check if backup file actually exists
if [[ ! -f "${USERS_FILE}" ]]; then
    echo "error: can't find the users file at ${USERS_FILE}" >&2
    echo "run the export script first or pass the exact path" >&2
    exit 1
fi

# check if docker container is running
if ! docker inspect --format '{{.State.Running}}' "${KEYCLOAK_CONTAINER}" 2>/dev/null | grep -q "^true$"; then
    echo "error: keycloak container isn't running right now" >&2
    exit 1
fi

echo "importing users from ${USERS_FILE}..."

# make temp dir inside container
docker exec "${KEYCLOAK_CONTAINER}" mkdir -p "${CONTAINER_TMP}"

# copy backup file into the container
docker cp "${USERS_FILE}" "${KEYCLOAK_CONTAINER}:${CONTAINER_TMP}/aiod-users.json"

# run the import
# using --override false so we don't accidentally overwrite existing users
docker exec "${KEYCLOAK_CONTAINER}" \
    /opt/keycloak/bin/kc.sh import \
    --dir "${CONTAINER_TMP}" \
    --realm "${KEYCLOAK_REALM}" \
    --override false

# clean up temp files
docker exec "${KEYCLOAK_CONTAINER}" rm -rf "${CONTAINER_TMP}"

echo "done! users imported safely."