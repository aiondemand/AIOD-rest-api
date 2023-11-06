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
    dataset.ai_resource_id AS `resource_identifier`,
    dataset.name,
    dataset.description,
    dataset.same_as,
    -- AIAsset
    dataset.ai_asset_id AS `asset_identifier`,
    dataset.date_published,
    dataset.version,
    license.name AS `license`,
    -- Dataset
    dataset.issn,
    dataset.measurement_technique,
    dataset.temporal_coverage,
    -- Application Area
    GROUP_CONCAT(application_area.name) AS `application_area`
FROM aiod.dataset
INNER JOIN aiod.aiod_entry ON aiod.dataset.aiod_entry_identifier=aiod.aiod_entry.identifier
INNER JOIN aiod.status ON aiod.aiod_entry.status_identifier=aiod.status.identifier
LEFT JOIN aiod.license ON aiod.dataset.license_identifier=aiod.license.identifier
LEFT JOIN aiod.dataset_application_area_link ON aiod.dataset_application_area_link.from_identifier=aiod.dataset.identifier
LEFT JOIN aiod.application_area ON aiod.dataset_application_area_link.linked_identifier=aiod.application_area.identifier
WHERE aiod.aiod_entry.date_modified > :sql_last_value
GROUP BY aiod.dataset.identifier
ORDER BY aiod.dataset.identifier