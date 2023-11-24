#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Generates the logstash configuration and pipelines files

This file generates the logstash configuration file in logstash/config, the
pipelines configuration files in logstash/pipelines/conf and the pipelines
sql sentences in logstash/pipelines/sql.

Launched by the es_logstash_setup container in the docker-compose file.
"""

import os
from jinja2 import Template

from routers.search_routers import router_list
from file_generated_comment import FILE_IS_GENERATED_COMMENT
from config_file_template import CONFIG_FILE_TEMPLATE
from pipeline_config_init_file_template import PIPELINE_CONFIG_INIT_FILE_TEMPLATE
from pipeline_config_sync_file_template import PIPELINE_CONFIG_SYNC_FILE_TEMPLATE
from pipeline_sql_init_file_template import PIPELINE_SQL_INIT_FILE_TEMPLATE
from pipeline_sql_sync_file_template import PIPELINE_SQL_SYNC_FILE_TEMPLATE
from pipeline_sql_rm_file_template import PIPELINE_SQL_RM_FILE_TEMPLATE


def generate_file(file_path, template, file_data):
    with open(file_path, "w") as f:
        f.write(Template(FILE_IS_GENERATED_COMMENT).render(file_data))
        f.write(Template(template).render(file_data))

def main():
    base_path = "/logstash"
    db_user = "root"
    db_pass = os.environ["MYSQL_ROOT_PASSWORD"]
    es_user = os.environ["ES_USER"]
    es_pass = os.environ["ES_PASSWORD"]
    global_fields = set(["name", "plain", "html"])
    entities = {}
    for router in router_list:
        entities[router.es_index] = list(router.match_fields ^ global_fields)
    config_path = os.path.join(base_path, "config")
    os.makedirs(config_path, exist_ok=True)
    pipeline_config_path = os.path.join(base_path, "pipeline", "conf")
    os.makedirs(pipeline_config_path, exist_ok=True)
    pipeline_sql_path = os.path.join(base_path, "pipeline", "sql")
    os.makedirs(pipeline_sql_path, exist_ok=True)
    config_file_data = {
        'comment_tag': "#",
        'es_user': es_user,
        'es_pass': es_pass
    }
    config_file_path = os.path.join(config_path, "logstash.yml")
    generate_file(config_file_path, CONFIG_FILE_TEMPLATE, config_file_data)
    pipeline_config_files_data = {
        'comment_tag': "#",
        'es_user': es_user,
        'es_pass': es_pass,
        'db_user': db_user,
        'db_pass': db_pass,
        'entities': entities.keys()
    }
    pipeline_config_init_file_path = os.path.join(pipeline_config_path, "init_table.conf")
    generate_file(pipeline_config_init_file_path, PIPELINE_CONFIG_INIT_FILE_TEMPLATE, pipeline_config_files_data)
    pipeline_config_sync_file_path = os.path.join(pipeline_config_path, "sync_table.conf")
    generate_file(pipeline_config_sync_file_path, PIPELINE_CONFIG_SYNC_FILE_TEMPLATE, pipeline_config_files_data)
    for entity, extra_fields in entities.items():
        pipeline_sql_files_data = {
            'comment_tag': "--",
            'entity_name': entity,
            'extra_fields': ", " + ", ".join(extra_fields) if extra_fields else ""
        }
        pipeline_sql_init_file_path = os.path.join(pipeline_sql_path, f"init_{entity}.sql")
        generate_file(pipeline_sql_init_file_path, PIPELINE_SQL_INIT_FILE_TEMPLATE, pipeline_sql_files_data)
        pipeline_sql_sync_file_path = os.path.join(pipeline_sql_path, f"sync_{entity}.sql")
        generate_file(pipeline_sql_sync_file_path, PIPELINE_SQL_SYNC_FILE_TEMPLATE, pipeline_sql_files_data)
        pipeline_sql_rm_file_path = os.path.join(pipeline_sql_path, f"rm_{entity}.sql")
        generate_file(pipeline_sql_rm_file_path, PIPELINE_SQL_RM_FILE_TEMPLATE, pipeline_sql_files_data)


if __name__ == "__main__":
    main()
