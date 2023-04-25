"""
Converting between different organisation representations
"""
from sqlalchemy.orm import Session

from converters.abstract_converter import ResourceConverter
from database.model.agent import OrmAgent, OrmEmail
from database.model.general import OrmBusinessCategory, OrmTechnicalCategory
from database.model.organisation import OrmOrganisation
from schemas import AIoDOrganisation, AIoDAgent


class OrganisationResourceConverter(ResourceConverter[AIoDOrganisation, OrmOrganisation]):
    def aiod_to_orm(
        self, session: Session, aiod: AIoDOrganisation, return_existing_if_present: bool = False
    ) -> OrmOrganisation:
        """
        Converting between organisation representations:
        the AIoD schema towards the database variant
        """

        return OrmOrganisation.create_or_get(
            session=session,
            create=not return_existing_if_present,
            platform=aiod.platform,
            platform_identifier=aiod.platform_identifier,
            name=aiod.name,
            description=aiod.description,
            image_url=aiod.image_url,
            connection_to_ai=aiod.connection_to_ai,
            type=aiod.type,
            logo_url=aiod.logo_url,
            same_as=aiod.same_as,
            founding_date=aiod.founding_date,
            dissolution_date=aiod.dissolution_date,
            legal_name=aiod.legal_name,
            alternate_name=aiod.alternate_name,
            address=aiod.address,
            telephone=aiod.telephone,
            members=[
                OrmAgent(
                    platform=v.platform,
                    platform_identifier=v.platform_identifier,
                    name=v.name,
                    description=v.description,
                    image_url=v.image_url,
                )
                for v in aiod.members
            ],
            departments=[
                OrmAgent(
                    platform=v.platform,
                    platform_identifier=v.platform_identifier,
                    name=v.name,
                    description=v.description,
                    image_url=v.image_url,
                )
                for v in aiod.departments
            ],
            parent_organisation_id=aiod.parent_organisation,
            subsidiary_organisation_id=aiod.subsidiary_organisation,
            business_categories=[
                OrmBusinessCategory.as_unique(session=session, category=category)
                for category in aiod.business_categories
            ],
            technical_categories=[
                OrmTechnicalCategory.as_unique(session=session, category=category)
                for category in aiod.technical_categories
            ],
            email_addresses=[
                OrmEmail.as_unique(session=session, email=email) for email in aiod.email_addresses
            ],
        )

    def orm_to_aiod(self, orm: OrmOrganisation) -> AIoDOrganisation:
        """
        Converting between organisation representations:
        the database variant towards the AIoD schema.
        """
        return AIoDOrganisation(
            identifier=orm.identifier,
            name=orm.name,
            description=orm.description,
            image_url=orm.image_url,
            connection_to_ai=orm.connection_to_ai,
            type=orm.type,
            logo_url=orm.logo_url,
            same_as=orm.same_as,
            founding_date=orm.founding_date,
            dissolution_date=orm.dissolution_date,
            legal_name=orm.legal_name,
            alternate_name=orm.alternate_name,
            address=orm.address,
            telephone=orm.telephone,
            members=[
                AIoDAgent(
                    platform=v.platform,
                    platform_identifier=v.platform_identifier,
                    name=v.name,
                    description=v.description,
                )
                for v in orm.members
            ],
            departments=[
                AIoDAgent(
                    platform=v.platform,
                    platform_identifier=v.platform_identifier,
                    name=v.name,
                    description=v.description,
                )
                for v in orm.departments
            ],
            parent_organisation=orm.parent_organisation_id,
            subsidiary_organisation=orm.subsidiary_organisation_id,
            email_addresses={e.email for e in orm.email_addresses},
            business_categories={c.category for c in orm.business_categories},
            technical_categories={c.category for c in orm.technical_categories},
        )
