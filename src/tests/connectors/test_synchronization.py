from sqlalchemy.engine import Engine
from sqlmodel import Session, select

from connectors.resource_with_relations import ResourceWithRelations
from connectors.synchronization import save_to_database
from database.model.agent.contact import Contact
from database.model.concept.aiod_entry import AIoDEntryCreate
from database.model.dataset.dataset import Dataset
from database.model.knowledge_asset.publication import Publication
from database.model.platform.platform_names import PlatformName
from database.model.resource_read_and_create import resource_create
from routers import resource_routers
from versioning import Version


class ZenodoConnector:
    resource_class = Dataset
    platform_name = PlatformName.zenodo


class ConnectorUser:
    is_connector = True

    def is_connector_for_platform(self, platform: str) -> bool:
        return platform == PlatformName.zenodo


def _dataset_router():
    (router,) = [
        router
        for router in resource_routers.versioned_routers[Version.LATEST]
        if router.resource_class == Dataset
    ]
    return router


def _dataset_with_relations(identifier: str, related_resources: dict) -> ResourceWithRelations:
    dataset = resource_create(Dataset)(
        name=f"dataset {identifier}",
        platform=PlatformName.zenodo,
        platform_resource_identifier=identifier,
        aiod_entry=AIoDEntryCreate(),
    )
    return ResourceWithRelations(
        resource=dataset, resource_ORM_class=Dataset, related_resources=related_resources
    )


def _save(session: Session, item: ResourceWithRelations):
    return save_to_database(
        session=session,
        connector=ZenodoConnector(),
        router=_dataset_router(),
        item=item,
        user=ConnectorUser(),
    )


def test_related_resources_without_platform_are_stored(engine: Engine):
    creators = [resource_create(Contact)(name="Doe, Jane"), resource_create(Contact)(name="Roe, R")]
    citation = resource_create(Publication)(name="A paper", aiod_entry=AIoDEntryCreate())
    item = _dataset_with_relations("zenodo.org:1", {"creator": creators, "citation": [citation]})

    with Session(engine) as session:
        assert _save(session, item) is None
        dataset = session.scalars(select(Dataset)).one()
        assert sorted(c.name for c in dataset.creator) == ["Doe, Jane", "Roe, R"]
        assert [p.name for p in dataset.citation] == ["A paper"]


def test_rerun_does_not_store_related_resources_again(engine: Engine):
    def item():
        return _dataset_with_relations(
            "zenodo.org:1", {"creator": [resource_create(Contact)(name="Doe, Jane")]}
        )

    with Session(engine) as session:
        assert _save(session, item()) is None
        assert _save(session, item()) is None
        assert len(session.scalars(select(Dataset)).all()) == 1
        assert len(session.scalars(select(Contact)).all()) == 1


def test_related_resource_with_platform_identifier_is_reused(engine: Engine):
    def citation():
        return resource_create(Publication)(
            name="A paper",
            platform=PlatformName.zenodo,
            platform_resource_identifier="zenodo.org:100",
            aiod_entry=AIoDEntryCreate(),
        )

    with Session(engine) as session:
        assert (
            _save(session, _dataset_with_relations("zenodo.org:1", {"citation": [citation()]}))
            is None
        )
        assert (
            _save(session, _dataset_with_relations("zenodo.org:2", {"citation": [citation()]}))
            is None
        )
        (publication,) = session.scalars(select(Publication)).all()
        datasets = session.scalars(select(Dataset)).all()
        assert [[p.identifier for p in d.citation] for d in datasets] == [
            [publication.identifier]
        ] * 2
