SELECT
    -- Concept
    organisation.identifier,
    organisation.platform,
    organisation.platform_identifier,
    -- Concept.aiod_entry
    status.name AS `status`,
    aiod_entry.date_modified,
    aiod_entry.date_created,
    agent.type AS `agent`,
    -- Resource
    organisation.ai_resource_id AS `resource_identifier`,
    organisation.name,
    organisation.description,
    organisation.same_as,
    organisation.date_founded,
    organisation.legal_name,
    -- Organisation
    organisation_type.name AS `organisation_type`
FROM aiod.organisation
INNER JOIN aiod.aiod_entry ON aiod.organisation.aiod_entry_identifier=aiod.aiod_entry.identifier
INNER JOIN aiod.status ON aiod.aiod_entry.status_identifier=aiod.status.identifier
INNER JOIN aiod.agent ON aiod.organisation.agent_id=aiod.agent.identifier
LEFT JOIN aiod.organisation_type ON aiod.organisation.type_identifier=aiod.organisation_type.identifier
ORDER BY aiod.organisation.identifier
