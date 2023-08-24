SELECT
    -- Concept
    service.identifier,
    service.platform,
    service.platform_identifier,
    -- Concept.aiod_entry
    status.name AS `status`,
    aiod_entry.date_modified,
    aiod_entry.date_created,
    -- Resource
    service.resource_id AS `resource_identifier`,
    service.name,
    service.description,
    service.same_as,
    -- Service
    service.slogan,
    service.terms_of_service
FROM aiod.service
INNER JOIN aiod.aiod_entry ON aiod.service.aiod_entry_identifier=aiod.aiod_entry.identifier
INNER JOIN aiod.status ON aiod.aiod_entry.status_identifier=aiod.status.identifier
ORDER BY aiod.service.identifier
