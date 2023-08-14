SELECT * FROM aiod.publication
WHERE date_created > :sql_last_value
ORDER BY identifier
