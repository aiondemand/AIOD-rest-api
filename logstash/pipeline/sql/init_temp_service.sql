SELECT service.identifier, service.name, service.description, service.same_as, service.resource_id, service.slogan, service.terms_of_service, aiod_entry.platform, aiod_entry.platform_identifier, aiod_entry.status_identifier, aiod_entry.date_modified, aiod_entry.date_created
FROM aiod.service INNER JOIN aiod.aiod_entry
ON aiod.service.aiod_entry_identifier=aiod.aiod_entry.identifier
ORDER BY aiod.service.identifier
