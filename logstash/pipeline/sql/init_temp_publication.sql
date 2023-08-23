SELECT publication.identifier, publication.name, publication.description, publication.same_as, publication.resource_id, publication.date_published, publication.version, publication.asset_id, publication.license_identifier, publication.knowledge_asset_id, publication.permanent_identifier, publication.isbn, publication.issn, publication.type_identifier, aiod_entry.platform, aiod_entry.platform_identifier, aiod_entry.status_identifier, aiod_entry.date_modified, aiod_entry.date_created
FROM aiod.publication INNER JOIN aiod.aiod_entry
ON aiod.publication.aiod_entry_identifier=aiod.aiod_entry.identifier
ORDER BY aiod.publication.identifier
