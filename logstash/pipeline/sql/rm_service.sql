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
    service.ai_resource_id AS `resource_identifier`,
    service.name,
    service.description,
    service.same_as,
    -- Attributes
    service.slogan,
    service.terms_of_service,
    -- Application Area
    GROUP_CONCAT(application_area.name) AS `application_area`
FROM aiod.service
INNER JOIN aiod.aiod_entry ON aiod.service.aiod_entry_identifier=aiod.aiod_entry.identifier
INNER JOIN aiod.status ON aiod.aiod_entry.status_identifier=aiod.status.identifier
LEFT JOIN aiod.service_application_area_link ON aiod.service_application_area_link.from_identifier=aiod.service.identifier
LEFT JOIN aiod.application_area ON aiod.service_application_area_link.linked_identifier=aiod.application_area.identifier
WHERE aiod.service.date_deleted IS NOT NULL AND aiod.service.date_deleted > :sql_last_value
GROUP BY aiod.service.identifier
ORDER BY aiod.service.identifier
