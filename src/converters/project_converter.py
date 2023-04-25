"""
Converting between different dataset representations
"""
from sqlalchemy.orm import Session

from converters.abstract_converter import ResourceConverter


from database.model.project import OrmProject

from schemas import AIoDProject


class ProjectConverter(ResourceConverter[AIoDProject, OrmProject]):
    def aiod_to_orm(
        self, session: Session, aiod: AIoDProject, return_existing_if_present: bool = False
    ) -> OrmProject:
        """
        Converting between publication representations: the AIoD schema towards the database variant
        """

        return OrmProject.create_or_get(
            session=session,
            create=not return_existing_if_present,
            name=aiod.name,
            doi=aiod.doi,
            start_date=aiod.start_date,
            end_date=aiod.end_date,
            founded_under=aiod.founded_under,
            total_cost_euro=aiod.total_cost_euro,
            eu_contribution_euro=aiod.eu_contribution_euro,
            coordinated_by=aiod.coordinated_by,
            project_description_title=aiod.project_description_title,
            project_description_text=aiod.project_description_text,
            programmes_url=aiod.programmes_url,
            topic_url=aiod.topic_url,
            call_for_proposal=aiod.call_for_proposal,
            founding_scheme=aiod.founding_scheme,
            image=aiod.image,
            url=aiod.url,
            platform=aiod.platform,
            platform_identifier=aiod.platform_identifier,
        )

    def orm_to_aiod(self, orm: OrmProject) -> AIoDProject:
        """
        Converting between publication representations: the database variant (OrmDataset) towards
        the AIoD schema.
        """
        return AIoDProject(
            identifier=orm.identifier,
            platform=orm.platform,
            platform_identifier=orm.platform_identifier,
            name=orm.name,
            doi=orm.doi,
            start_date=orm.start_date,
            end_date=orm.end_date,
            founded_under=orm.founded_under,
            total_cost_euro=orm.total_cost_euro,
            eu_contribution_euro=orm.eu_contribution_euro,
            coordinated_by=orm.coordinated_by,
            project_description_title=orm.project_description_title,
            project_description_text=orm.project_description_text,
            programmes_url=orm.programmes_url,
            topic_url=orm.topic_url,
            call_for_proposal=orm.call_for_proposal,
            founding_scheme=orm.foundung_scheme,
            image=orm.image,
            url=orm.image,
        )
