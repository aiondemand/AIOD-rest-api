-- This file has been generated by `generate_logstash_config.py`
-- file, placed in `src/setup/logstash`
-- -------------------------------------------------------------
SELECT event.identifier, event.name, text.plain as 'plain', text.html as 'html', aiod_entry.date_modified
FROM aiod.event
INNER JOIN aiod.aiod_entry ON aiod.event.aiod_entry_identifier=aiod.aiod_entry.identifier
LEFT JOIN aiod.text ON aiod.event.description_identifier=aiod.text.identifier
WHERE aiod.event.date_deleted IS NULL
