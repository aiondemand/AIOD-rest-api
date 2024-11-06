#!/bin/bash
docker compose --env-file=.env --env-file=override.env up -d
