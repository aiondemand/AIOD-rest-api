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
    project.start_date,
    project.end_date,
    project.total_cost_euro,
    project.coordinator_identifier,
    organisation.name AS coordinator,
FROM aiod.project
INNER JOIN aiod.aiod_entry ON aiod.project.aiod_entry_identifier=aiod.aiod_entry.identifier
INNER JOIN aiod.status ON aiod.aiod_entry.status_identifier=aiod.status.identifier
INNER JOIN aiod.organisation ON aiod.project.coordinator_identifier=aiod.organisation.identifier
WHERE aiod.aiod_entry.date_modified > :sql_last_value
ORDER BY aiod.project.identifier
