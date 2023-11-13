-- This file has been generated by `logstash_config.py` file
-- ---------------------------------------------------------
SELECT aiod_entry.date_modified, organisation.identifier, name, description_identifier, text.plain as 'plain', text.html as 'html', legal_name
FROM aiod.organisation
INNER JOIN aiod.aiod_entry ON aiod.organisation.aiod_entry_identifier=aiod.aiod_entry.identifier
LEFT JOIN aiod.text ON aiod.organisation.description_identifier=aiod.text.identifier
WHERE aiod.organisation.date_deleted IS NULL
