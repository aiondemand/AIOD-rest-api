"""
Converting between different dataset representations
"""
from sqlalchemy.orm import Session

from converters.abstract_converter import ResourceConverter
from converters.dataset_converter import retrieve_related_objects_by_ids
from database.model.dataset import OrmDataset
from database.model.publication import OrmPublication
from schemas import AIoDPublication


class PublicationConverter(ResourceConverter[AIoDPublication, OrmPublication]):
    def aiod_to_orm(
        self, session: Session, aiod: AIoDPublication, return_existing_if_present: bool = False
    ) -> OrmPublication:
        """
        Converting between publication representations: the AIoD schema towards the database variant
        """
        datasets = retrieve_related_objects_by_ids(session, aiod.datasets, OrmDataset)
        return OrmPublication.create_or_get(
            session=session,
            create=not return_existing_if_present,
            doi=aiod.doi,
            platform=aiod.platform,
            platform_identifier=aiod.platform_identifier,
            title=aiod.title,
            url=aiod.url,
            datasets=datasets,
        )

    def orm_to_aiod(self, orm: OrmPublication) -> AIoDPublication:
        """
        Converting between publication representations: the database variant (OrmDataset) towards
        the AIoD schema.
        """
        return AIoDPublication(
            identifier=orm.identifier,
            doi=orm.doi,
            platform=orm.platform,
            platform_identifier=orm.platform_identifier,
            title=orm.title,
            url=orm.url,
            datasets=[d.identifier for d in orm.datasets],
        )
