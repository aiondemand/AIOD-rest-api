#!/bin/bash

# Can be run after docker compose up (the sqlserver must be running)
docker exec -it sqlserver mysql -uroot -pok --database aiod
