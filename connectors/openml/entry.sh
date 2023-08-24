#!/bin/bash

# If this directory does not exist, the cron job cannot log (and cannot run)
mkdir -p /opt/connectors/data/openml/dataset

# Run cron on the foreground with log level WARN
/usr/sbin/cron -f -l 4
