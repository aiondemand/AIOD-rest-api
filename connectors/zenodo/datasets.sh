#!/bin/bash

WORK_DIR=/opt/connectors/data/zenodo/dataset
CONNECTOR=connectors.zenodo.zenodo_dataset_connector.ZenodoDatasetConnector

another_instance()
{
    echo $(date -u) "This script is already running in a different thread."
    exit 1
}
exec 9< "$0"
flock -n -x 9 || another_instance

echo $(date -u) "Starting synchronization..."
PYTHONPATH=/app /usr/local/bin/python3 /app/connectors/synchronization.py \
      -c $CONNECTOR \
      -w $WORK_DIR \
      --from-date "2023-08-01" \
      --save-every 100 >> ${WORK_DIR}/connector.log 2>&1
echo $(date -u) "Synchronization Done."
