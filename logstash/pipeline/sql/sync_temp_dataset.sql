SELECT * FROM aiod.dataset
WHERE date_modified > :sql_last_value
ORDER BY identifier
