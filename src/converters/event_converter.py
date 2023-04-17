"""
Converting between different event representations
"""
from sqlalchemy.orm import Session
from converters.conversion_helpers import retrieve_related_objects_by_ids

from converters.abstract_converter import ResourceConverter
from database.model.ai_resource import OrmAIResource
from database.model.general import OrmBusinessCategory
from database.model.event import OrmEvent, OrmApplicationArea, OrmResearchArea
from schemas import AIoDEvent


class EventResourceConverter(ResourceConverter[AIoDEvent, OrmEvent]):
    def aiod_to_orm(
        self, session: Session, aiod: AIoDEvent, return_existing_if_present: bool = False
    ) -> OrmEvent:
        """
        Converting between event representations: the AIoD schema towards the database variant
        """
        sub_events = retrieve_related_objects_by_ids(session, aiod.sub_events, OrmEvent)
        super_events = retrieve_related_objects_by_ids(session, aiod.super_events, OrmEvent)
        relevant_resources = retrieve_related_objects_by_ids(
            session, aiod.relevant_resources, OrmAIResource
        )
        used_resources = retrieve_related_objects_by_ids(
            session, aiod.used_resources, OrmAIResource
        )
        return OrmEvent.create_or_get(
            session=session,
            create=not return_existing_if_present,
            platform=aiod.platform,
            platform_identifier=aiod.platform_identifier,
            name=aiod.name,
            description=aiod.description,
            registration_url=aiod.registration_url,
            location=aiod.location,
            start_date=aiod.start_date,
            end_date=aiod.end_date,
            duration=aiod.duration,
            status=aiod.status,
            attendance_mode=aiod.attendance_mode,
            type=aiod.type,
            sub_events=sub_events,
            super_events=super_events,
            relevant_resources=relevant_resources,
            used_resources=used_resources,
            business_categories=[
                OrmBusinessCategory.as_unique(session=session, category=category)
                for category in aiod.business_categories
            ],
            research_areas=[
                OrmResearchArea.as_unique(session=session, name=area)
                for area in aiod.research_areas
            ],
            application_areas=[
                OrmApplicationArea.as_unique(session=session, name=area)
                for area in aiod.application_areas
            ],
        )

    def orm_to_aiod(self, orm: OrmEvent) -> AIoDEvent:
        """
        Converting between events representations: the database variant towards the AIoD schema.
        """
        return AIoDEvent(
            identifier=orm.identifier,
            platform=orm.platform,
            platform_identifier=orm.platform_identifier
            if orm.platform_identifier is not None
            else str(orm.identifier),
            name=orm.name,
            description=orm.description,
            registration_url=orm.registration_url,
            location=orm.location,
            start_date=orm.start_date,
            end_date=orm.end_date,
            duration=orm.duration,
            status=orm.status,
            attendance_mode=orm.attendance_mode,
            type=orm.type,
            sub_events=[event.identifier for event in orm.sub_events],
            super_events=[event.identifier for event in orm.super_events],
            relevant_resources=[resource.identifier for resource in orm.relevant_resources],
            used_resources=[resource.identifier for resource in orm.used_resources],
            business_categories={c.category for c in orm.business_categories},
            research_areas={a.name for a in orm.research_areas},
            application_areas={a.name for a in orm.application_areas},
        )
