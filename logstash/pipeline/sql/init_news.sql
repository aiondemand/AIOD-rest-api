-- This file has been generated by `generate_logstash_config.py`
-- file, placed in `src/setup/logstash`
-- -------------------------------------------------------------
SELECT news.identifier, news.name, text.plain as 'plain', text.html as 'html', aiod_entry.date_modified, headline, alternative_headline
FROM aiod.news
INNER JOIN aiod.aiod_entry ON aiod.news.aiod_entry_identifier=aiod.aiod_entry.identifier
LEFT JOIN aiod.text ON aiod.news.description_identifier=aiod.text.identifier
WHERE aiod.news.date_deleted IS NULL
