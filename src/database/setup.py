"""
Utility functions for initializing the database and tables through SQLAlchemy.
"""
from operator import and_

import sqlmodel
from sqlalchemy import text, create_engine
from sqlmodel import SQLModel, select

from config import DB_CONFIG
from connectors.resource_with_relations import ResourceWithRelations
from database.model.concept.concept import AIoDConcept
from database.model.named_relation import NamedRelation
from database.model.platform.platform_names import PlatformName
from database.session import db_url
from routers import resource_routers


def drop_or_create_database(delete_first: bool):
    url = db_url(including_db=False)
    engine = create_engine(url, echo=False)  # Temporary engine, not connected to a database
    with engine.connect() as connection:
        database = DB_CONFIG.get("database", "aiod")
        if delete_first:
            connection.execute(text(f"DROP DATABASE IF EXISTS {database}"))
        connection.execute(text(f"CREATE DATABASE IF NOT EXISTS {database}"))


def _get_existing_resource(
    session: sqlmodel.Session, resource: AIoDConcept, clazz: type[SQLModel]
) -> AIoDConcept | None:
    """Selecting a resource based on platform and platform_resource_identifier"""
    is_enum = NamedRelation in clazz.__mro__
    if is_enum:
        query = select(clazz).where(clazz.name == resource)
    else:
        query = select(clazz).where(
            and_(
                clazz.platform == resource.platform,
                clazz.platform_resource_identifier == resource.platform_resource_identifier,
            )
        )
    return session.scalars(query).first()


def _create_or_fetch_related_objects(session: sqlmodel.Session, item: ResourceWithRelations):
    """
    For all resources in the `related_resources`, get the identifier, by either
    inserting them in the database, or retrieving the existing values, and put the identifiers
    into the item.resource.[field_name]
    """
    for field_name, related_resource_or_list in item.related_resources.items():
        if isinstance(related_resource_or_list, AIoDConcept):
            resources = [related_resource_or_list]
        else:
            resources = related_resource_or_list
        identifiers = []
        for resource in resources:
            if (
                resource.platform is not None
                and resource.platform != PlatformName.aiod
                and resource.platform_resource_identifier is not None
            ):
                # Get the router of this resource. The difficulty is, that the resource will be a
                # ResourceRead (e.g. a DatasetRead). So we search for the router for which the
                # resource name starts with the research-read-name

                resource_read_str = type(resource).__name__  # E.g. DatasetRead
                (router,) = [
                    router
                    for router in resource_routers.router_list
                    if resource_read_str.startswith(router.resource_class.__name__)
                    # E.g. "DatasetRead".startswith("Dataset")
                ]
                existing = _get_existing_resource(session, resource, router.resource_class)
                if existing is None:
                    created_resource = router.create_resource(session, resource)
                    identifiers.append(created_resource.identifier)
                else:
                    identifiers.append(existing.identifier)

        if isinstance(related_resource_or_list, AIoDConcept):
            (id_,) = identifiers
            item.resource.__setattr__(field_name, id_)  # E.g. Dataset.license_identifier = 1
        else:
            item.resource.__setattr__(field_name, identifiers)  # E.g. Dataset.keywords = [1, 4]
