from database.model.concept.concept import AIoDConcept
from versioning import VersionedResource, Version


def get_versioned_resource(
    resource: type[AIoDConcept],
    version: Version = Version.LATEST,
    mapping: dict[Version, VersionedResource] | None = None,
) -> VersionedResource:
    versioned_resources = mapping or globals().get(f"{resource.__tablename__}_versions")
    if not versioned_resources:
        raise ValueError(f"No versioned resources for {resource.__tablename__!r}")
    if version not in versioned_resources:
        raise KeyError(
            f"Version {version!r} not supported for {resource.__tablename__}. "
            f"Choose one of {set(versioned_resources.keys())!r}."
        )
    return versioned_resources[version]
