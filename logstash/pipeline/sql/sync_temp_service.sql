SELECT service.identifier,
       service.platform,
       service.platform_identifier,
       service.name,
       service.description,
       service.same_as,
       service.resource_id,
       service.slogan,
       service.terms_of_service,
       aiod_entry.status_identifier,
       aiod_entry.date_modified,
       aiod_entry.date_created
FROM aiod.service INNER JOIN aiod.aiod_entry
ON aiod.service.aiod_entry_identifier=aiod.aiod_entry.identifier
WHERE aiod.aiod_entry.date_modified > :sql_last_value
ORDER BY aiod.service.identifier
