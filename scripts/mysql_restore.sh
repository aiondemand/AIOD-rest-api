#!/bin/bash

SCRIPT_PATH="$(readlink -f "$0")"
SCRIPT_DIR="$(dirname "$SCRIPT_PATH")"

cd $SCRIPT_DIR/..
source .env

DATA_PATH=$(realpath "$DATA_PATH")

echo $(date -u) "Copying backup.sql to container..."
docker cp "${DATA_PATH}/mysql_dump/backup.sql" sqlserver:/tmp/backup.sql

echo $(date -u) "Restoring database..."
docker exec -i sqlserver /bin/bash -c "mysql -uroot -p${MYSQL_ROOT_PASSWORD} aiod < /tmp/backup.sql"
echo $(date -u) "Done!"

