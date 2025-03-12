#!/bin/bash

mkdir -p /opt/connectors/data/ai4europe_cms/organisation
mkdir -p /opt/connectors/data/ai4europe_cms/event

/usr/sbin/cron -f -l 4
