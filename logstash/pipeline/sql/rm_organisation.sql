-- This file has been generated by `logstash_config.py` file
-- ---------------------------------------------------------
SELECT organisation.identifier
FROM aiod.organisation
WHERE aiod.organisation.date_deleted IS NOT NULL AND aiod.organisation.date_deleted > :sql_last_value
