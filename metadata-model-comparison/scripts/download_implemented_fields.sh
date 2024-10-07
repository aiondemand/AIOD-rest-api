#!/bin/bash

ROOT_DIR=$(dirname -- $(dirname $(readlink -f "$0")))
DATA_DIR=$ROOT_DIR/data

wget https://api.aiod.eu/openapi.json -O $DATA_DIR/implemented.json
