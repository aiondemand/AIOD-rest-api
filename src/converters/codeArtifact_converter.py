"""
Converting between different dataset representations
"""
from sqlalchemy.orm import Session

from converters.abstract_converter import ResourceConverter
from database.model.code_artifact import OrmCodeArtifact
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
            name=aiod.name,
            doi=aiod.doi,
            abstract=aiod.abstract,
            hardware_resources_description=aiod.hardware_resources_description,
            os_description=aiod.os_description,
            software_dependecies=aiod.software_dependecies,
            other_dependencies=aiod.other_dependencies,
            compilation_process=aiod.compilation_process,
            compilation_time_seconds=aiod.compilation_time_seconds,
            deployment_process=aiod.deployment_process,
            deployment_time_seconds=aiod.deployment_time_seconds,
            experiment_worklow=aiod.experiment_worklow,
            experiment_estimation_time_seconds=aiod.experiment_estimation_time_seconds,
            results_description=aiod.results_description,
            publication_results_experiment=aiod.publication_results_experiment,
            other_notes=aiod.other_notes,
        )

    def orm_to_aiod(self, orm: OrmCodeArtifact) -> AIoDCodeArtifact:
        """
        Converting between  representations: the database variant (OrmDataset) towards
        the AIoD schema.
        """
        return AIoDCodeArtifact(
            identifier=orm.identifier,
            platform=orm.platform,
            platform_identifier=orm.platform_identifier,
            name=orm.name,
            doi=orm.doi,
            abstract=orm.abstract,
            hardware_resources_description=orm.hardware_resources_description,
            os_description=orm.os_description,
            software_dependecies=orm.software_dependecies,
            other_dependencies=orm.other_dependencies,
            compilation_process=orm.compilation_process,
            compilation_time_seconds=orm.compilation_time_seconds,
            deployment_process=orm.deployment_process,
            deployment_time_seconds=orm.deployment_time_seconds,
            experiment_worklow=orm.experiment_worklow,
            experiment_estimation_time_seconds=orm.experiment_estimation_time_seconds,
            results_description=orm.results_description,
            publication_results_experiment=orm.publication_results_experiment,
            other_notes=orm.other_notes,
        )
