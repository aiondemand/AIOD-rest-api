SELECT
    -- Concept
    experiment.identifier,
    experiment.platform,
    experiment.platform_identifier,
    -- Concept.aiod_entry
    status.name AS `status`,
    aiod_entry.date_modified,
    aiod_entry.date_created,
    -- Resource
    experiment.ai_resource_id AS `resource_identifier`,
    experiment.name,
    experiment.description,
    experiment.same_as,
    -- AIAsset
    experiment.ai_asset_id AS `asset_identifier`,
    experiment.date_published,
    experiment.version,
    license.name AS `license`,
    -- Experiment
    experiment.experimental_workflow,
    experiment.execution_settings,
    experiment.reproducibility_explanation
FROM aiod.experiment
INNER JOIN aiod.aiod_entry ON aiod.experiment.aiod_entry_identifier=aiod.aiod_entry.identifier
INNER JOIN aiod.status ON aiod.aiod_entry.status_identifier=aiod.status.identifier
LEFT JOIN aiod.license ON aiod.experiment.license_identifier=aiod.license.identifier
WHERE aiod.aiod_entry.date_modified > :sql_last_value
ORDER BY aiod.experiment.identifier
