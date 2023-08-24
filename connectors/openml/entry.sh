#!/bin/bash

# If this directory does not exist, the cron job cannot log (and cannot run)
mkdir -p /opt/connectors/data/openml/dataset

# Run once on startup
bash /opt/connectors/script/datasets.sh >> /opt/connectors/data/openml/dataset/cron.log 2>&1

# Run cron on the foreground with log level WARN
/usr/sbin/cron -f -l 4
