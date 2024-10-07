TEMPLATE_SQL_RM = """SELECT
    {{entity_name}}.identifier,
    {{entity_name}}.date_deleted
FROM aiod.{{entity_name}}
WHERE aiod.{{entity_name}}.date_deleted IS NOT NULL
AND aiod.{{entity_name}}.date_deleted > :sql_last_value
"""
