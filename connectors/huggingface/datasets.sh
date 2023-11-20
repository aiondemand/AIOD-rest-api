#!/bin/bash

WORK_DIR=/opt/connectors/data/huggingface/dataset
mkdir -p $WORK_DIR

python3 connectors/synchronization.py \
  -c connectors.huggingface.huggingface_dataset_connector.HuggingFaceDatasetConnector \
  -w ${WORK_DIR} \
  --save-every 100 > ${WORK_DIR}/connector.log 2>&1
