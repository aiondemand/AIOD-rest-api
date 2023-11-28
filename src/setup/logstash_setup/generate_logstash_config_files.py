#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Generates the logstash configuration and pipelines files

This file generates the logstash configuration file in logstash/config, the
pipelines configuration files in logstash/pipelines/conf and the pipelines
sql sentences in logstash/pipelines/sql.

Launched by the es_logstash_setup container in the docker-compose file.
"""
import logging
import os
from pathlib import Path
from jinja2 import Template

from routers.search_routers import router_list
from setup.logstash_setup.templates.config import TEMPLATE_CONFIG
from setup.logstash_setup.templates.file_header import FILE_IS_GENERATED_COMMENT
from setup.logstash_setup.templates.init_table import TEMPLATE_INIT_TABLE
from setup.logstash_setup.templates.sql_init import TEMPLATE_SQL_INIT
from setup.logstash_setup.templates.sql_rm import TEMPLATE_SQL_RM
from setup.logstash_setup.templates.sql_sync import TEMPLATE_SQL_SYNC
from setup.logstash_setup.templates.sync_table import TEMPLATE_SYNC_TABLE
from setup_logger import setup_logger

PATH_BASE = Path("/logstash/config")
PATH_CONFIG = PATH_BASE / "config"
PATH_PIPELINE = PATH_BASE / "pipeline"
PATH_SQL = PATH_BASE / "sql"

DB_USER = "root"
DB_PASS = os.environ["MYSQL_ROOT_PASSWORD"]
ES_USER = os.environ["ES_USER"]
ES_PASS = os.environ["ES_PASSWORD"]

GLOBAL_FIELDS = {"name", "description_plain", "description_html"}


def generate_file(file_path, template, file_data):
    with open(file_path, "w") as f:
        f.write(Template(FILE_IS_GENERATED_COMMENT).render(file_data))
        f.write(Template(template).render(file_data))


def main():
    setup_logger()
    for path in (PATH_CONFIG, PATH_PIPELINE, PATH_SQL):
        path.mkdir(parents=True, exist_ok=True)
    entities = {
        router.es_index: list(router.indexed_fields ^ GLOBAL_FIELDS) for router in router_list
    }
    render_parameters = {
        "file": os.path.basename(__file__),
        "path": os.path.dirname(__file__).replace("/app", "src"),
        "comment_tag": "#",
        "es_user": ES_USER,
        "es_pass": ES_PASS,
        "db_user": DB_USER,
        "db_pass": DB_PASS,
        "entities": entities.keys(),
    }
    logging.info("Generating configuration files...")
    config_file = os.path.join(PATH_CONFIG, "logstash.yml")
    config_init_file = os.path.join(PATH_PIPELINE, "init_table.conf")
    config_sync_file = os.path.join(PATH_PIPELINE, "sync_table.conf")
    generate_file(config_file, TEMPLATE_CONFIG, render_parameters)
    generate_file(config_init_file, TEMPLATE_INIT_TABLE, render_parameters)
    generate_file(config_sync_file, TEMPLATE_SYNC_TABLE, render_parameters)

    render_parameters["comment_tag"] = "--"
    logging.info("Generating configuration files completed.")
    logging.info("Generating sql files...")
    for es_index, extra_fields in entities.items():
        render_parameters["entity_name"] = es_index
        render_parameters["extra_fields"] = (
            ",\n    " + ",\n    ".join(extra_fields) if extra_fields else ""
        )

        sql_init_file = os.path.join(PATH_SQL, f"init_{es_index}.sql")
        sql_sync_file = os.path.join(PATH_SQL, f"sync_{es_index}.sql")
        sql_rm_file = os.path.join(PATH_SQL, f"rm_{es_index}.sql")
        generate_file(sql_init_file, TEMPLATE_SQL_INIT, render_parameters)
        generate_file(sql_sync_file, TEMPLATE_SQL_SYNC, render_parameters)
        generate_file(sql_rm_file, TEMPLATE_SQL_RM, render_parameters)
    logging.info("Generating configuration files completed.")


if __name__ == "__main__":
    main()
