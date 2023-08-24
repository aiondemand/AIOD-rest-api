SELECT
    -- Concept
    dataset.identifier,
    dataset.platform,
    dataset.platform_identifier,
    -- Concept.aiod_entry
    status.name AS `status`,
    aiod_entry.date_modified,
    aiod_entry.date_created,
    -- Resource
    dataset.resource_id AS `resource_identifier`,
    dataset.name,
    dataset.description,
    dataset.same_as,
    -- AIAsset
    dataset.asset_id AS `asset_identifier`,
    dataset.date_published,
    dataset.version,
    license.name AS `license`,
    -- Dataset
    dataset.issn,
    dataset.measurement_technique,
    dataset.temporal_coverage
FROM aiod.dataset
INNER JOIN aiod.aiod_entry ON aiod.dataset.aiod_entry_identifier=aiod.aiod_entry.identifier
INNER JOIN aiod.status ON aiod.aiod_entry.status_identifier=aiod.status.identifier
LEFT JOIN aiod.license ON aiod.dataset.license_identifier=aiod.license.identifier
WHERE aiod.aiod_entry.date_modified > :sql_last_value
ORDER BY aiod.dataset.identifier
