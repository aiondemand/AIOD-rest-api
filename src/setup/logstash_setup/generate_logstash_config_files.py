#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Generates the logstash configuration and pipelines files

This file generates the logstash configuration file in logstash/config, the
pipelines configuration files in logstash/pipelines/conf and the pipelines
sql sentences in logstash/pipelines/sql.

Launched by the es_logstash_setup container in the docker-compose file.
"""

import os
from pathlib import Path
from jinja2 import Template

from routers.search_routers import router_list
from templates.file_generated_comment import FILE_IS_GENERATED_COMMENT
from templates.config_file_template import CONFIG_FILE_TEMPLATE
from templates.pipeline_config_init_file_template import PIPELINE_CONFIG_INIT_FILE_TEMPLATE
from templates.pipeline_config_sync_file_template import PIPELINE_CONFIG_SYNC_FILE_TEMPLATE
from templates.pipeline_sql_init_file_template import PIPELINE_SQL_INIT_FILE_TEMPLATE
from templates.pipeline_sql_sync_file_template import PIPELINE_SQL_SYNC_FILE_TEMPLATE
from templates.pipeline_sql_rm_file_template import PIPELINE_SQL_RM_FILE_TEMPLATE


BASE_PATH = Path("/logstash")
CONFIG_PATH = BASE_PATH / "config"
PIPELINE_CONFIG_PATH = BASE_PATH / "pipeline" / "conf"
pipeline_sql_path = BASE_PATH / "pipeline" / "sql"
DB_USER = "root"
DB_PASS = os.environ["MYSQL_ROOT_PASSWORD"]
ES_USER = os.environ["ES_USER"]
ES_PASS = os.environ["ES_PASSWORD"]
GLOBAL_FIELDS = {"name", "plain", "html"}


def generate_file(file_path, template, file_data):
    with open(file_path, "w") as f:
        f.write(Template(FILE_IS_GENERATED_COMMENT).render(file_data))
        f.write(Template(template).render(file_data))


def main():
    for path in (CONFIG_PATH, PIPELINE_CONFIG_PATH, pipeline_sql_path):
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
    config_file = os.path.join(CONFIG_PATH, "logstash.yml")
    config_init_file = os.path.join(PIPELINE_CONFIG_PATH, "init_table.conf")
    config_sync_file = os.path.join(PIPELINE_CONFIG_PATH, "sync_table.conf")
    generate_file(config_file, CONFIG_FILE_TEMPLATE, render_parameters)
    generate_file(config_init_file, PIPELINE_CONFIG_INIT_FILE_TEMPLATE, render_parameters)
    generate_file(config_sync_file, PIPELINE_CONFIG_SYNC_FILE_TEMPLATE, render_parameters)
    render_parameters["comment_tag"] = "--"
    for entity, extra_fields in entities.items():
        render_parameters["entity_name"] = entity
        render_parameters["extra_fields"] = (
            ",\n    " + ",\n    ".join(extra_fields) if extra_fields else ""
        )
        sql_init_file = os.path.join(pipeline_sql_path, f"init_{entity}.sql")
        sql_sync_file = os.path.join(pipeline_sql_path, f"sync_{entity}.sql")
        sql_rm_file = os.path.join(pipeline_sql_path, f"rm_{entity}.sql")
        generate_file(sql_init_file, PIPELINE_SQL_INIT_FILE_TEMPLATE, render_parameters)
        generate_file(sql_sync_file, PIPELINE_SQL_SYNC_FILE_TEMPLATE, render_parameters)
        generate_file(sql_rm_file, PIPELINE_SQL_RM_FILE_TEMPLATE, render_parameters)


if __name__ == "__main__":
    main()
