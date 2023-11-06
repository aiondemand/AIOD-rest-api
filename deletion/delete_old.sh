#!/bin/bash

WORK_DIR=/opt/deletion/data/

another_instance()
{
    echo $(date -u) "This script is already running in a different thread."
    exit 1
}
exec 9< "$0"
flock -n -x 9 || another_instance

echo $(date -u) "Starting deletion..."
PYTHONPATH=/app /usr/local/bin/python3 /app/database/deletion/hard_delete.py \
      --time-threshold-minutes 10080 > ${WORK_DIR}/deletion.log 2>&1
echo $(date -u) "Deletion Done."
