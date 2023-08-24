SELECT
    -- Concept
    publication.identifier,
    publication.platform,
    publication.platform_identifier,
    -- Concept.aiod_entry
    status.name AS `status`,
    aiod_entry.date_modified,
    aiod_entry.date_created,
    -- Resource
    publication.resource_id AS `resource_identifier`,
    publication.name,
    publication.description,
    publication.same_as,
    -- AIAsset
    publication.asset_id AS `asset_identifier`,
    publication.date_published,
    publication.version,
    license.name AS `license`,
    -- KnowledgeAsset
    publication.knowledge_asset_id AS `knowledge_asset_identifier`,
    -- Publication
    publication.permanent_identifier,
    publication.isbn,
    publication.issn,
    publication_type.name AS `publication_type`
FROM aiod.publication
INNER JOIN aiod.aiod_entry ON aiod.publication.aiod_entry_identifier=aiod.aiod_entry.identifier
INNER JOIN aiod.status ON aiod.aiod_entry.status_identifier=aiod.status.identifier
LEFT JOIN aiod.license ON aiod.publication.license_identifier=aiod.license.identifier
LEFT JOIN aiod.publication_type ON aiod.publication.type_identifier=aiod.publication_type.identifier
WHERE aiod.aiod_entry.date_modified > :sql_last_value
ORDER BY aiod.publication.identifier
