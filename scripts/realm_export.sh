#!/bin/bash
set -euo pipefail

# Set defaults, but allow overrides via environment variables
KEYCLOAK_CONTAINER="${KEYCLOAK_CONTAINER:-keycloak}"
KEYCLOAK_REALM="${KEYCLOAK_REALM:-aiod}"
EXPORT_DIR="${EXPORT_DIR:-./keycloak-exports}"

REALM_FILE="aiod-realm.json"
USERS_FILE="aiod-users.json"
CONTAINER_TMP="/tmp/keycloak-export"

log() {
    echo "[realm_export] $1"
}

# Bail out early if the container isn't up
if ! docker inspect --format '{{.State.Running}}' "${KEYCLOAK_CONTAINER}" 2>/dev/null | grep -q "^true$"; then
    echo "Error: Container '${KEYCLOAK_CONTAINER}' doesn't seem to be running." >&2
    echo "Make sure Keycloak is up before running the backup script." >&2
    exit 1
fi

# Prep the local and container directories
mkdir -p "${EXPORT_DIR}"
docker exec "${KEYCLOAK_CONTAINER}" mkdir -p "${CONTAINER_TMP}"

# --- 1. Export the realm config (skipping users) ---
log "Exporting realm config to ${REALM_FILE}..."

docker exec "${KEYCLOAK_CONTAINER}" \
    /opt/keycloak/bin/kc.sh export \
    --dir "${CONTAINER_TMP}" \
    --realm "${KEYCLOAK_REALM}" \
    --users skip

# kc.sh generates the file as <realm>-realm.json, pull it out and rename it
docker cp "${KEYCLOAK_CONTAINER}:${CONTAINER_TMP}/${KEYCLOAK_REALM}-realm.json" "${EXPORT_DIR}/${REALM_FILE}"
log "✔ Realm config saved."

# --- 2. Export the user data ---
log "Exporting user data to ${USERS_FILE}..."

docker exec "${KEYCLOAK_CONTAINER}" \
    /opt/keycloak/bin/kc.sh export \
    --dir "${CONTAINER_TMP}" \
    --realm "${KEYCLOAK_REALM}" \
    --users realm_file

# Keycloak chunks user exports, giving it a '-0' suffix.
# Grab it and rename it to our clean target filename.
docker cp "${KEYCLOAK_CONTAINER}:${CONTAINER_TMP}/${KEYCLOAK_REALM}-users-0.json" "${EXPORT_DIR}/${USERS_FILE}"
log "✔ User data saved."

# Clean up the temp folder inside the container so we don'