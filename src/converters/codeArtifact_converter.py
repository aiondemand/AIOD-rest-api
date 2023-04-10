"""
Converting between different dataset representations
"""
from sqlalchemy.orm import Session

from converters.abstract_converter import ResourceConverter
from database.model.codeArtifact import OrmCodeArtifact
from schemas import AIoDCodeArtifact


class CodeArtifactConverter(ResourceConverter[AIoDCodeArtifact, OrmCodeArtifact]):
    def aiod_to_orm(
        self, session: Session, aiod: AIoDCodeArtifact, return_existing_if_present: bool = False
    ) -> OrmCodeArtifact:
        """
        Converting between codeAtifact representations: the AIoD schema towards the database variant
        """

        return OrmCodeArtifact.create_or_get(
            session=session,
            create=not return_existing_if_present,
            platform=aiod.platform,
            platform_identifier=aiod.platform_identifier,
            doi=aiod.doi,
            name=aiod.name,
        )

    def orm_to_aiod(self, orm: OrmCodeArtifact) -> AIoDCodeArtifact:
        """
        Converting between  representations: the database variant (OrmDataset) towards
        the AIoD schema.
        """
        return AIoDCodeArtifact(
            identifier=orm.identifier,
            doi=orm.doi,
            platform=orm.platform,
            platform_identifier=orm.platform_identifier,
            name=orm.name,
        )
