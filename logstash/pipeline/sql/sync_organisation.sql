SELECT
    -- Concept
    organisation.identifier,
    organisation.platform,
    organisation.platform_identifier,
    -- Concept.aiod_entry
    status.name AS `status`,
    aiod_entry.date_modified,
    aiod_entry.date_created,
    -- Resource
    organisation.ai_resource_id AS `resource_identifier`,
    organisation.name,
    organisation.description,
    organisation.same_as,
    -- Attributes
    organisation.date_founded,
    organisation.legal_name,
    -- Type
    organisation_type.name AS `organisation_type`,
    -- Agent
    agent.type AS `agent`,
    -- Application Area
    GROUP_CONCAT(application_area.name) AS `application_area`
FROM aiod.organisation
INNER JOIN aiod.aiod_entry ON aiod.organisation.aiod_entry_identifier=aiod.aiod_entry.identifier
INNER JOIN aiod.status ON aiod.aiod_entry.status_identifier=aiod.status.identifier
LEFT JOIN aiod.organisation_type ON aiod.organisation.type_identifier=aiod.organisation_type.identifier
LEFT JOIN aiod.agent ON aiod.organisation.agent_id=aiod.agent.identifier
LEFT JOIN aiod.organisation_application_area_link ON aiod.organisation_application_area_link.from_identifier=aiod.organisation.identifier
LEFT JOIN aiod.application_area ON aiod.organisation_application_area_link.linked_identifier=aiod.application_area.identifier
WHERE aiod.organisation.date_deleted IS NULL AND aiod.aiod_entry.date_modified > :sql_last_value
GROUP BY aiod.organisation.identifier
ORDER BY aiod.organisation.identifier
