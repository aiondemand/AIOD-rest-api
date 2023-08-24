#!/bin/bash

docker image rm ai4eu_server
docker image rm ai4eu_openml_connector
docker image rm ai4eu_zenodo_connector
echo "Deleted docker images, so that they will be rebuild on docker up."


SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
ROOT=$(dirname $SCRIPT_DIR)
DATA=${ROOT}/data

sudo rm -rf ${DATA}/mysql
sudo rm -rf ${DATA}/connectors
sudo rm -rf ${DATA}/elasticsearch
mkdir -p ${DATA}/mysql ${DATA}/connectors ${DATA}/elasticsearch
echo "Deleted everything from $DATA"
