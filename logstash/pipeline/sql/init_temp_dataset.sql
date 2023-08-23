SELECT dataset.identifier, dataset.name, dataset.description, dataset.same_as, dataset.resource_id, dataset.date_published, dataset.version, dataset.asset_id, dataset.license_identifier, dataset.issn, dataset.measurement_technique, dataset.temporal_coverage, dataset.size_identifier, dataset.spatial_coverage_identifier, aiod_entry.platform, aiod_entry.platform_identifier, aiod_entry.status_identifier, aiod_entry.date_modified, aiod_entry.date_created
FROM aiod.dataset INNER JOIN aiod.aiod_entry
ON aiod.dataset.aiod_entry_identifier=aiod.aiod_entry.identifier
ORDER BY aiod.dataset.identifier
