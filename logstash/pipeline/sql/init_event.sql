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
    event.organiser_identifier,
    -- Application Area
    GROUP_CONCAT(application_area.name) AS `application_area`
FROM aiod.event
INNER JOIN aiod.aiod_entry ON aiod.event.aiod_entry_identifier=aiod.aiod_entry.identifier
INNER JOIN aiod.agent ON aiod.event.organiser_identifier=aiod.agent.identifier
LEFT JOIN aiod.event_status ON aiod.event.status_identifier=aiod.event_status.identifier
LEFT JOIN aiod.event_mode ON aiod.event.mode_identifier=aiod.event_mode.identifier
LEFT JOIN aiod.event_application_area_link ON aiod.event_application_area_link.from_identifier=aiod.event.identifier
LEFT JOIN aiod.application_area ON aiod.event_application_area_link.linked_identifier=aiod.application_area.identifier
GROUP BY aiod.event.identifier
ORDER BY aiod.event.identifier
