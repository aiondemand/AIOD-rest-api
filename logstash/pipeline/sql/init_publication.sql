-- This file has been generated by `generate_logstash_config.py`
-- file, placed in `src/setup/logstash`
-- -------------------------------------------------------------
SELECT publication.identifier, publication.name, text.plain as 'plain', text.html as 'html', aiod_entry.date_modified, isbn, issn
FROM aiod.publication
INNER JOIN aiod.aiod_entry ON aiod.publication.aiod_entry_identifier=aiod.aiod_entry.identifier
LEFT JOIN aiod.text ON aiod.publication.description_identifier=aiod.text.identifier
WHERE aiod.publication.date_deleted IS NULL
