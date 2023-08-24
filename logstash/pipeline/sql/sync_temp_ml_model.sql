SELECT ml_model.identifier,
       ml_model.platform,
       ml_model.platform_identifier,
       ml_model.name,
       ml_model.description,
       ml_model.same_as,
       ml_model.resource_id,
       ml_model.date_published,
       ml_model.version,
       ml_model.asset_id,
       ml_model.license_identifier,
       ml_model.pid,
       ml_model.type_identifier,
       aiod_entry.status_identifier,
       aiod_entry.date_modified,
       aiod_entry.date_created
FROM aiod.ml_model INNER JOIN aiod.aiod_entry
ON aiod.ml_model.aiod_entry_identifier=aiod.aiod_entry.identifier
WHERE aiod.aiod_entry.date_modified > :sql_last_value
ORDER BY aiod.ml_model.identifier
