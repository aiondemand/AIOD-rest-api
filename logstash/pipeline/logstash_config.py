#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os

# PATH MACROS
# =============================================================================

# Repository base path
REPO_PATH = os.path.join("..", "..")

# Working path
WORKING_PATH = os.path.join(".")

# MACROS FOR THE DOCUMENTS GENERATION FUNCTIONS
# =============================================================================

INIT_INPUT_BASE = """  jdbc {{
    jdbc_driver_library => "/usr/share/logstash/mysql-connector-java-8.0.22.jar"
    jdbc_driver_class => "com.mysql.jdbc.Driver"
    jdbc_connection_string => "jdbc:mysql://sqlserver:3306/aiod"
    jdbc_user => "{0}"
    jdbc_password => "{1}"
    clean_run => true
    record_last_run => false
    statement_filepath => "/usr/share/logstash/sql/init_{2}.sql"
    type => "{2}"
  }}
"""

SYNC_INPUT_BASE = """  jdbc {{
    jdbc_driver_library => "/usr/share/logstash/mysql-connector-java-8.0.22.jar"
    jdbc_driver_class => "com.mysql.jdbc.Driver"
    jdbc_connection_string => "jdbc:mysql://sqlserver:3306/aiod"
    jdbc_user => "{0}"
    jdbc_password => "{1}"
    use_column_value => true
    tracking_column => "date_modified"
    tracking_column_type => "timestamp"
    schedule => "*/5 * * * * *"
    statement_filepath => "/usr/share/logstash/sql/sync_{2}.sql"
    type => "{2}"
  }}
  jdbc {{
    jdbc_driver_library => "/usr/share/logstash/mysql-connector-java-8.0.22.jar"
    jdbc_driver_class => "com.mysql.jdbc.Driver"
    jdbc_connection_string => "jdbc:mysql://sqlserver:3306/aiod"
    jdbc_user => "{0}"
    jdbc_password => "{1}"
    use_column_value => true
    tracking_column => "date_deleted"
    tracking_column_type => "timestamp"
    schedule => "*/5 * * * * *"
    statement_filepath => "/usr/share/logstash/sql/rm_{2}.sql"
    type => "rm_{2}"
  }}
"""

FILTER_BASE = """filter {{
  if ![application_area] {{
    mutate {{
      replace => {{"application_area" => ""}}
    }}
  }}
  mutate {{
    # remove_field => ["@version", "@timestamp"]
    split => {{"application_area" => ","}}
  }}{0}
}}
"""

DATE_FILTER = """
  if [type] == "organisation" {0}{{
      ruby {{
        code => '
            t = Time.at(event.get("date_founded").to_f)
            event.set("date_founded", t.strftime("%Y-%m-%d"))
        '
      }}
  }}
"""

SYNC_DATE_FILTER_ADDON = """or [type] == "rm_organisation" """

INIT_OUTPUT_BASE = """  if [type] == "{2}" {{
    elasticsearch {{
        hosts => "elasticsearch:9200"
        user => "{0}"
        password => "{1}"
        ecs_compatibility => disabled
        index => "{2}"
        document_id => "{2}_%{{identifier}}"
    }}
  }}
"""

#TODO: TEST DELETE WITHOUT protocol => "transport"
SYNC_OUTPUT_BASE = """  if [type] == "{2}" {{
    elasticsearch {{
        hosts => "elasticsearch:9200"
        user => "{0}"
        password => "{1}"
        ecs_compatibility => disabled
        index => "{2}"
        document_id => "{2}_%{{identifier}}"
    }}
  }}
  if [type] == "rm_{2}" {{
    elasticsearch {{
        action => "delete"
        hosts => "elasticsearch:9200"
        user => "{0}"
        password => "{1}"
        ecs_compatibility => disabled
        index => "{2}"
        document_id => "{2}_%{{identifier}}"
    }}
  }}
"""

SQL_BASE = """SELECT
    -- Concept
    {0}.identifier,
    {0}.platform,
    {0}.platform_identifier,
    -- Concept.aiod_entry
    status.name AS `status`,
    aiod_entry.date_modified,
    aiod_entry.date_created,
    -- Resource
    {0}.ai_resource_id AS `resource_identifier`,
    {0}.name,
    {0}.description,
    {0}.same_as{1}{2}{3}{4}{5}{6}{7},
    -- Application Area
    GROUP_CONCAT(application_area.name) AS `application_area`
FROM aiod.{0}
INNER JOIN aiod.aiod_entry ON aiod.{0}.aiod_entry_identifier=aiod.aiod_entry.identifier
INNER JOIN aiod.status ON aiod.aiod_entry.status_identifier=aiod.status.identifier{8}
LEFT JOIN aiod.{0}_application_area_link ON aiod.{0}_application_area_link.from_identifier=aiod.{0}.identifier
LEFT JOIN aiod.application_area ON aiod.{0}_application_area_link.linked_identifier=aiod.application_area.identifier{9}
GROUP BY aiod.{0}.identifier
ORDER BY aiod.{0}.identifier
"""

AI_ASSET_BASE = """,
    -- AIAsset
    {0}.ai_asset_id AS `asset_identifier`,
    {0}.date_published,
    {0}.version,
    license.name AS `license`"""

ATTRIBUTES_BASE = """,
    -- Attributes
    """

TYPE_BASE = """,
    -- Type
    {0}_type.name AS `{0}_type`"""

MODE_BASE = """,
    -- Mode
    {0}_mode.name AS `mode`"""

STATUS_BASE = """,
    -- Status
    {0}_status.name AS `{0}_status`"""

AGENT_BASE = """,
    -- Agent
    agent.type AS `{0}`"""

ORGANISATION_BASE = """,
    -- Organisation
    organisation.name AS `{0}`"""

LEFT_LICENSE = """
LEFT JOIN aiod.license ON aiod.{0}.license_identifier=aiod.license.identifier"""

LEFT_TYPE = """
LEFT JOIN aiod.{0}_type ON aiod.{0}.type_identifier=aiod.{0}_type.identifier"""

LEFT_MODE = """
LEFT JOIN aiod.{0}_mode ON aiod.{0}.mode_identifier=aiod.{0}_mode.identifier"""

LEFT_STATUS = """
LEFT JOIN aiod.{0}_status ON aiod.{0}.status_identifier=aiod.{0}_status.identifier"""

LEFT_AGENT = """
LEFT JOIN aiod.agent ON aiod.{0}.{1}=aiod.agent.identifier"""

LEFT_ORGANISATION = """
LEFT JOIN aiod.organisation ON aiod.{0}.{1}=aiod.organisation.identifier"""

INIT_CLAUSE = """
WHERE aiod.{0}.date_deleted IS NULL"""

SYNC_CLAUSE = """
WHERE aiod.{0}.date_deleted IS NULL AND aiod.aiod_entry.date_modified > :sql_last_value"""

RM_CLAUSE = """
WHERE aiod.{0}.date_deleted IS NOT NULL AND aiod.{0}.date_deleted > :sql_last_value"""

# DOCUMENTS GENERATION FUNCTIONS
# =============================================================================

def generate_config_file(conf_path, db_user, db_pass, es_user, es_pass,
                         entities, sync=False):
    
    if not sync: # init file
        file_path = os.path.join(conf_path, "init_table.conf")
        input_base = INIT_INPUT_BASE
        date_filter = DATE_FILTER.format("")
        output_base = INIT_OUTPUT_BASE
    else: # sync file
        file_path = os.path.join(conf_path, "sync_table.conf")
        input_base = SYNC_INPUT_BASE
        date_filter = DATE_FILTER.format(SYNC_DATE_FILTER_ADDON)
        output_base = SYNC_OUTPUT_BASE
    
    # Generate configuration file
    with open(file_path, 'w') as f:
        
        # Input
        f.write("input {\n")
        for entity in entities:
            f.write(input_base.format(db_user, db_pass, entity))
        f.write("}\n")
        
        # Filters
        if "organisation" in entities:
            f.write(FILTER_BASE.format(date_filter))
        else:
            f.write(FILTER_BASE.format(""))
        
        # Output
        f.write("output {\n")
        for entity in entities:
            f.write(output_base.format(es_user, es_pass, entity))
        f.write("}\n")

def generate_sql_file(sql_path, entity, sync=False, rm=False):
    
    # Generate output file path
    if rm: # rm (regardless of the value of sync)
        file_path = os.path.join(sql_path, f"rm_{entity}.sql")
    elif sync: # sync and not rm
        file_path = os.path.join(sql_path, f"sync_{entity}.sql")
    else: # not sync and not rm
        file_path = os.path.join(sql_path, f"init_{entity}.sql")
    
    # Write the output file
    with open(file_path, 'w') as f:
            
            # Left joins
            left_joins = ""
            
            # For ai_asset entities
            ai_asset_attributes = ""
            if entity in ai_asset_entities:
                ai_asset_attributes = AI_ASSET_BASE.format(entity)
                left_joins += LEFT_LICENSE.format(entity)
            
            # Attributes
            entity_attributes = ""
            if entity in attributes.keys():
                entity_attributes = (ATTRIBUTES_BASE
                                     + f"{entity}.{attributes[entity][0]}")
                for attribute in attributes[entity][1:]:
                    entity_attributes += f",\n    {entity}.{attribute}"
            
            # For entities with a type relation
            type_attribute = ""
            if entity in type_entities:
                type_attribute = TYPE_BASE.format(entity)
                left_joins += LEFT_TYPE.format(entity)
            
            # For entities with a mode relation
            mode_attribute = ""
            if entity in mode_entities:
                mode_attribute = MODE_BASE.format(entity)
                left_joins += LEFT_MODE.format(entity)
            
            # For entities with a status relation
            status_attribute = ""
            if entity in status_entities:
                status_attribute = STATUS_BASE.format(entity)
                left_joins += LEFT_STATUS.format(entity)
            
            # For entities with an agent relation
            agent_attribute = ""
            if entity in agent_entities.keys():
                agent_attribute = AGENT_BASE.format(agent_entities[entity][1])
                left_joins += LEFT_AGENT.format(entity,
                                                agent_entities[entity][0])
            
            # For entities with an organisation relation
            organisation_attribute = ""
            if entity in organisation_entities.keys():
                organisation_attribute = ORGANISATION_BASE.format(
                                            organisation_entities[entity][1])
                left_joins += LEFT_ORGANISATION.format(entity,
                                organisation_entities[entity][0])
            
            # Where clause
            if rm: # rm (regardless of the value of sync)
                where_clause = RM_CLAUSE.format(entity)
            elif sync: # sync and not rm
                where_clause = SYNC_CLAUSE.format(entity)
            else: # not sync and not rm
                where_clause = INIT_CLAUSE.format(entity)
            
            f.write(SQL_BASE.format(entity, ai_asset_attributes,
                                    entity_attributes, type_attribute,
                                    mode_attribute, status_attribute,
                                    agent_attribute, organisation_attribute,
                                    left_joins, where_clause))

# MAIN FUNCTION
# =============================================================================

def main(base_path, db_user, db_pass, es_user, es_pass, entities,
         ai_asset_entities, attributes, type_entities, mode_entities,
         status_entities, agent_entities, organisation_entities):
    
    # Make configuration dirs
    conf_path = os.path.join(base_path, "conf")
    os.makedirs(conf_path, exist_ok=True)
    sql_path = os.path.join(base_path, "sql")
    os.makedirs(sql_path, exist_ok=True)
    
    # Configuration init file
    generate_config_file(conf_path, db_user, db_pass, es_user, es_pass,
                         entities, sync=False)
    
    # Configuration sync file
    generate_config_file(conf_path, db_user, db_pass, es_user, es_pass,
                         entities, sync=True)
    
    # Generate SQL init, sync and rm files
    for entity in entities:
        generate_sql_file(sql_path, entity, sync=False, rm=False) # init
        generate_sql_file(sql_path, entity, sync=True, rm=False) # sync
        generate_sql_file(sql_path, entity, rm=True) # rm

if __name__ == "__main__":
    
    # PATH MACROS
    # -------------------------------------------------------------------------
    
    # Repository base path
    repo_path = REPO_PATH
    
    # Configuration base path
    base_path = WORKING_PATH
    
    # -------------------------------------------------------------------------
    
    # Users and passwords
    db_user = "root"
    db_pass = ""
    es_user = ""
    es_pass = ""
    with open(os.path.join(repo_path, ".env"), "r") as f:
        for line in f:
            if "MYSQL_ROOT_PASSWORD" in line:
                db_pass = line.split("=")[1][:-1]
            if "ES_USER" in line:
                es_user = line.split("=")[1][:-1]
            if "ES_PASSWORD" in line:
                es_pass = line.split("=")[1][:-1]
    
    # Entities and attributes
    entities = ["dataset", "event", "experiment", "ml_model", "news",
                "organisation", "project", "publication", "service"]
    ai_asset_entities = ["dataset", "experiment", "ml_model", "publication"]
    attributes = {
        "dataset": ["issn", "measurement_technique", "temporal_coverage"],
        "event": ["start_date", "end_date", "schedule", "registration_link",
                  "organiser_identifier"],
        "experiment": ["experimental_workflow", "execution_settings",
                       "reproducibility_explanation"],
        "news": ["headline", "alternative_headline"],
        "organisation": ["date_founded", "legal_name"],
        "project": ["start_date", "end_date", "total_cost_euro",
                    "coordinator_identifier"],
        "publication": ["permanent_identifier", "isbn", "issn",
                        "knowledge_asset_id AS `knowledge_asset_identifier`"],
        "service": ["slogan", "terms_of_service"]
    }
    type_entities = ["ml_model", "organisation", "publication"]
    mode_entities = ["event"]
    status_entities = ["event"]
    agent_entities = {
        "event": ("organiser_identifier", "organiser_type"),
        "organisation": ("agent_id", "agent")
    }
    organisation_entities = {
        "project": ("coordinator_identifier", "coordinator_name")
    }
    
    # Main function
    main(base_path, db_user, db_pass, es_user, es_pass, entities,
         ai_asset_entities, attributes, type_entities, mode_entities,
         status_entities, agent_entities, organisation_entities)
