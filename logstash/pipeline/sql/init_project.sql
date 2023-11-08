SELECT
    -- Concept
    project.identifier,
    project.platform,
    project.platform_identifier,
    -- Concept.aiod_entry
    status.name AS `status`,
    aiod_entry.date_modified,
    aiod_entry.date_created,
    -- Resource
    project.ai_resource_id AS `resource_identifier`,
    project.name,
    project.description,
    project.same_as,
    -- Attributes
    project.start_date,
    project.end_date,
    project.total_cost_euro,
    project.coordinator_identifier,
    -- Organisation
    organisation.name AS `coordinator_name`,
    -- Application Area
    GROUP_CONCAT(application_area.name) AS `application_area`
FROM aiod.project
INNER JOIN aiod.aiod_entry ON aiod.project.aiod_entry_identifier=aiod.aiod_entry.identifier
INNER JOIN aiod.status ON aiod.aiod_entry.status_identifier=aiod.status.identifier
LEFT JOIN aiod.organisation ON aiod.project.coordinator_identifier=aiod.organisation.identifier
LEFT JOIN aiod.project_application_area_link ON aiod.project_application_area_link.from_identifier=aiod.project.identifier
LEFT JOIN aiod.application_area ON aiod.project_application_area_link.linked_identifier=aiod.application_area.identifier
WHERE aiod.project.date_deleted IS NULL
GROUP BY aiod.project.identifier
ORDER BY aiod.project.identifier
