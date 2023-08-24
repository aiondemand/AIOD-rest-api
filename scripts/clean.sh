#!/bin/bash

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
ROOT=$(dirname $SCRIPT_DIR)
DATA=${ROOT}/data


sudo rm -rf ${DATA}/*
echo "Deleted everything from $DATA"
mkdir -p ${DATA}/mysql ${DATA}/connectors ${DATA}/elasticsearch

