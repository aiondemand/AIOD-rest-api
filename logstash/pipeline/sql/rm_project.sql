-- This file has been generated by `logstash_config.py` file
-- ---------------------------------------------------------
SELECT project.identifier
FROM aiod.project
WHERE aiod.project.date_deleted IS NOT NULL AND aiod.project.date_deleted > :sql_last_value
