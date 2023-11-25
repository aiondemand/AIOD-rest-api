PIPELINE_SQL_RM_FILE_TEMPLATE = """SELECT {{entity_name}}.identifier
FROM aiod.{{entity_name}}
WHERE aiod.{{entity_name}}.date_deleted IS NOT NULL
AND aiod.{{entity_name}}.date_deleted > :sql_last_value
"""
