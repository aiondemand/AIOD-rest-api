#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Generates the logstash configuration and pipelines files

This file generates the logstash configuration file in logstash/config, the
pipelines configuration files in logstash/pipelines/conf and the pipelines
sql sentences in logstash/pipelines/sql.

Launched by the es_logstash_setup container in the docker-compose file.
"""

import os

import definitions
from routers.search_routers import router_list

def generate_conf_file(conf_path, es_user, es_pass):

    file_path = os.path.join(conf_path, "logstash.yml")

    # Generate configuration file
    with open(file_path, "w") as f:

        # Info
        f.write(INFO.format("#"))

        # Configuration
        f.write(CONF_BASE.format(es_user, es_pass))


def generate_pipeline_conf_files(
    pipeline_conf_path, db_user, db_pass, es_user, es_pass, entities, sync=False
):

    if not sync:  # init file
        file_path = os.path.join(pipeline_conf_path, "init_table.conf")
        input_base = INIT_INPUT_BASE
        output_base = INIT_OUTPUT_BASE
    else:  # sync file
        file_path = os.path.join(pipeline_conf_path, "sync_table.conf")
        input_base = SYNC_INPUT_BASE
        output_base = SYNC_OUTPUT_BASE

    # Generate configuration file
    with open(file_path, "w") as f:

        # Info
        f.write(INFO.format("#"))

        # Input
        f.write("input {\n")
        for entity in entities:
            f.write(input_base.format(db_user, db_pass, entity))
        f.write("}\n")

        # Filters
        f.write(FILTER)

        # Output
        f.write("output {\n")
        for entity in entities:
            f.write(output_base.format(es_user, es_pass, entity))
        f.write("}\n")


def generate_pipeline_sql_files(pipeline_sql_path, entity, fields, sync=False):

    # Generate output file path
    if sync:
        file_path = os.path.join(pipeline_sql_path, f"sync_{entity}.sql")
    else:
        file_path = os.path.join(pipeline_sql_path, f"init_{entity}.sql")

    # Write the output file
    with open(file_path, "w") as f:

        # Info
        f.write(INFO.format("--"))

        # Where clause
        if sync:
            where_clause = SYNC_CLAUSE.format(entity)
        else:
            where_clause = INIT_CLAUSE.format(entity)

        # Generate field list
        field_list = ", ".join(fields).format(entity)

        f.write(SQL_BASE.format(entity, field_list, where_clause))


def generate_pipeline_sql_rm_files(pipeline_sql_path, entity):

    # Generate output file path
    file_path = os.path.join(pipeline_sql_path, f"rm_{entity}.sql")

    # Write the output file
    with open(file_path, "w") as f:

        # Info
        f.write(INFO.format("--"))

        # SQL query
        f.write(SQL_RM_BASE.format(entity))

def main():

    # Get configuration variables
    base_path = "/logstash"
    db_user = "root"
    db_pass = os.environ["MYSQL_ROOT_PASSWORD"]
    es_user = os.environ["ES_USER"]
    es_pass = os.environ["ES_PASSWORD"]

    # Search for entities and their extra fields
    global_fields = set(["name", "plain", "html"])
    entities = {}
    for router in router_list:
        extra_fields = list(router.match_fields ^ global_fields)
        entities[router.es_index] = BASE_FIELDS + extra_fields

    # Make configuration dir
    conf_path = os.path.join(base_path, "config")
    os.makedirs(conf_path, exist_ok=True)

    # Make pipeline configuration dirs
    pipeline_conf_path = os.path.join(base_path, "pipeline", "conf")
    os.makedirs(pipeline_conf_path, exist_ok=True)
    pipeline_sql_path = os.path.join(base_path, "pipeline", "sql")
    os.makedirs(pipeline_sql_path, exist_ok=True)

    # Generate logstash configuration file
    generate_conf_file(conf_path, es_user, es_pass)

    # Generate pipeline configuration init and sync files
    generate_pipeline_conf_files(
        pipeline_conf_path, db_user, db_pass, es_user, es_pass, entities.keys(), sync=False
    )
    generate_pipeline_conf_files(
        pipeline_conf_path, db_user, db_pass, es_user, es_pass, entities.keys(), sync=True
    )

    # Generate SQL init, sync and rm files
    for entity, fields in entities.items():
        generate_pipeline_sql_files(pipeline_sql_path, entity, fields, sync=False)
        generate_pipeline_sql_files(pipeline_sql_path, entity, fields, sync=True)
        generate_pipeline_sql_rm_files(pipeline_sql_path, entity)


if __name__ == "__main__":
    main()
