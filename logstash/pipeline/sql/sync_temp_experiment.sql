SELECT experiment.identifier, experiment.name, experiment.description, experiment.same_as, experiment.resource_id, experiment.date_published, experiment.version, experiment.asset_id, experiment.license_identifier, experiment.pid, experiment.experimental_workflow, experiment.execution_settings, experiment.reproducibility_explanation, aiod_entry.platform, aiod_entry.platform_identifier, aiod_entry.status_identifier, aiod_entry.date_modified, aiod_entry.date_created
FROM aiod.experiment INNER JOIN aiod.aiod_entry
ON aiod.experiment.aiod_entry_identifier=aiod.aiod_entry.identifier
WHERE aiod.aiod_entry.date_modified > :sql_last_value
ORDER BY aiod.experiment.identifier
