PIPELINE_SQL_SYNC_FILE_TEMPLATE = """SELECT {{entity_name}}.identifier, {{entity_name}}.name, text.plain as 'plain', text.html as 'html', aiod_entry.date_modified {{extra_fields}}
FROM aiod.{{entity_name}}
INNER JOIN aiod.aiod_entry ON aiod.{{entity_name}}.aiod_entry_identifier=aiod.aiod_entry.identifier
LEFT JOIN aiod.text ON aiod.{{entity_name}}.description_identifier=aiod.text.identifier
WHERE aiod.{{entity_name}}.date_deleted IS NULL AND aiod.aiod_entry.date_modified > :sql_last_value"""
