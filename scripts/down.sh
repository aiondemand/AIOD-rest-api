#!/bin/bash

command='docker compose --profile "*" down'
echo "${command}"
eval "${command}"
