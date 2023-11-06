SELECT
    -- Concept
    news.identifier,
    news.platform,
    news.platform_identifier,
    -- Concept.aiod_entry
    status.name AS `status`,
    aiod_entry.date_modified,
    aiod_entry.date_created,
    -- Resource
    news.ai_resource_id AS `resource_identifier`,
    news.name,
    news.description,
    news.same_as,
    news.headline,
    news.alternative_headline,
    -- Application Area
    GROUP_CONCAT(application_area.name) AS `application_area`
FROM aiod.news
INNER JOIN aiod.aiod_entry ON aiod.news.aiod_entry_identifier=aiod.aiod_entry.identifier
INNER JOIN aiod.status ON aiod.aiod_entry.status_identifier=aiod.status.identifier
LEFT JOIN aiod.news_application_area_link ON aiod.news_application_area_link.from_identifier=aiod.news.identifier
LEFT JOIN aiod.application_area ON aiod.news_application_area_link.linked_identifier=aiod.application_area.identifier
WHERE aiod.aiod_entry.date_modified > :sql_last_value
GROUP BY aiod.news.identifier
ORDER BY aiod.news.identifier