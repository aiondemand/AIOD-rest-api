#!/bin/bash
# convenience script to revert back to a clean state.

DIR_SCRIPT=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
DIR_ROOT=$( dirname $DIR_SCRIPT )
DIR_DATA=$DIR_ROOT/data

DIR_MYSQL=$DIR_DATA/mysql
DIR_CONNECTORS=$DIR_DATA/connectors
DIR_DELETION=$DIR_DATA/deletion
DIR_ELASTIC=$DIR_DATA/elasticsearch
DIR_KEYCLOAK=$DIR_DATA/keycloak

find $DIR_CONNECTORS -type f ! -name .gitkeep -delete
find $DIR_DELETION -type f ! -name .gitkeep -delete
rm -rf $DIR_MYSQL/*
touch $DIR_MYSQL/.gitkeep
rm -rf $DIR_ELASTIC/*
rm -rf $DIR_KEYCLOAK/data/tmp
rm -rf $DIR_KEYCLOAK/data/h2
rm -rf $DIR_KEYCLOAK/data/transaction-logs
touch $DIR_ELASTIC/.gitkeep
