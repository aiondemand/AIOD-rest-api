from database.model.agent.person import person_versions
from database.model.agent.team import team_versions
from database.model.agent.contact import contact_versions
from database.model.agent.organisation import organisation_versions
from database.model.case_study.case_study import case_study_versions
from database.model.computational_asset.computational_asset import computational_asset_versions
from database.model.dataset.dataset import dataset_versions
from database.model.educational_resource.educational_resource import educational_resource_versions
from database.model.event.event import event_versions
from database.model.knowledge_asset.publication import publication_versions
from database.model.models_and_experiments.experiment import experiment_versions
from database.model.models_and_experiments.ml_model import ml_model_versions
from database.model.news.news import news_versions
from database.model.project.project import project_versions
from database.model.resource_bundle.resource_bundle import resource_bundle_versions
from database.model.service.service import service_versions

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
