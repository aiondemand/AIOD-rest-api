SELECT
    -- Concept
    ml_model.identifier,
    ml_model.platform,
    ml_model.platform_identifier,
    -- Concept.aiod_entry
    status.name AS `status`,
    aiod_entry.date_modified,
    aiod_entry.date_created,
    -- Resource
    ml_model.resource_id AS `resource_identifier`,
    ml_model.name,
    ml_model.description,
    ml_model.same_as,
    -- AIAsset
    ml_model.asset_id AS `asset_identifier`,
    ml_model.date_published,
    ml_model.version,
    license.name AS `license`,
    -- MLModel
    ml_model.permanent_identifier,
    ml_model_type.name AS `ml_model_type`
FROM aiod.ml_model
INNER JOIN aiod.aiod_entry ON aiod.ml_model.aiod_entry_identifier=aiod.aiod_entry.identifier
INNER JOIN aiod.status ON aiod.aiod_entry.status_identifier=aiod.status.identifier
LEFT JOIN aiod.license ON aiod.ml_model.license_identifier=aiod.license.identifier
LEFT JOIN aiod.ml_model_type ON aiod.ml_model.type_identifier=aiod.ml_model_type.identifier
ORDER BY aiod.ml_model.identifier
