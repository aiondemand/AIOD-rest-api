-- This file has been generated by `generate_logstash_config_files.py`
-- file, placed in `src/setup/logstash_setup`
-- -------------------------------------------------------------------
SELECT service.identifier, service.name, text.plain as 'plain', text.html as 'html', aiod_entry.date_modified , slogan
FROM aiod.service
INNER JOIN aiod.aiod_entry ON aiod.service.aiod_entry_identifier=aiod.aiod_entry.identifier
LEFT JOIN aiod.text ON aiod.service.description_identifier=aiod.text.identifier
WHERE aiod.service.date_deleted IS NULL