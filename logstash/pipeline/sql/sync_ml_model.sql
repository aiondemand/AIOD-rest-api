-- This file has been generated by `generate_logstash_config.py`
-- file, placed in `src/setup/logstash`
-- -------------------------------------------------------------
SELECT ml_model.identifier, ml_model.name, text.plain as 'plain', text.html as 'html', aiod_entry.date_modified
FROM aiod.ml_model
INNER JOIN aiod.aiod_entry ON aiod.ml_model.aiod_entry_identifier=aiod.aiod_entry.identifier
LEFT JOIN aiod.text ON aiod.ml_model.description_identifier=aiod.text.identifier
WHERE aiod.ml_model.date_deleted IS NULL AND aiod.aiod_entry.date_modified > :sql_last_value
