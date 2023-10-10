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
FROM aiod.news
INNER JOIN aiod.aiod_entry ON aiod.news.aiod_entry_identifier=aiod.aiod_entry.identifier
INNER JOIN aiod.status ON aiod.aiod_entry.status_identifier=aiod.status.identifier
ORDER BY aiod.news.identifier
