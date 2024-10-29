#!/bin/bash

SCRIPT_PATH="$(readlink -f "$0")"
SCRIPT_DIR="$(dirname "$SCRIPT_PATH")"

cd $SCRIPT_DIR/..
source .env

DATA_PATH=$(realpath "$DATA_PATH")
LOCAL_BACKUP_PATH="$DATA_PATH"/mysql_dump

docker exec -i sqlserver /bin/bash -c "
    mysqldump -uroot -p"$MYSQL_ROOT_PASSWORD" aiod > /tmp/backup.sql
"

if [ ! -d "$LOCAL_BACKUP_PATH" ]; then
    mkdir "$LOCAL_BACKUP_PATH"
fi

docker cp sqlserver:tmp/backup.sql "$LOCAL_BACKUP_PATH"/backup.sql

docker exec -i sqlserver /bin/bash -c "rm /tmp/backup.sql"
