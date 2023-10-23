SELECT
    -- Concept
    event.identifier,
    event.platform,
    event.platform_identifier,
    -- Concept.aiod_entry
    event_status.name AS `status`,
    event_mode.name AS `mode`,
    aiod_entry.date_modified,
    aiod_entry.date_created,
    agent.type AS `organiser_type`,
    -- Resource
    event.ai_resource_id AS `resource_identifier`,
    event.name,
    event.description,
    event.same_as,
    event.start_date,
    event.end_date,
    event.schedule,
    event.registration_link,
    event.organiser_identifier
FROM aiod.event
INNER JOIN aiod.aiod_entry ON aiod.event.aiod_entry_identifier=aiod.aiod_entry.identifier
INNER JOIN aiod.agent ON aiod.event.organiser_identifier=aiod.agent.identifier
LEFT JOIN aiod.event_status ON aiod.event.status_identifier=aiod.event_status.identifier
LEFT JOIN aiod.event_mode ON aiod.event.mode_identifier=aiod.event_mode.identifier
WHERE aiod.aiod_entry.date_modified > :sql_last_value
ORDER BY aiod.event.identifier
