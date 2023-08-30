"""
Utility functions for initializing the database and tables through SQLAlchemy.
"""

from operator import and_

from sqlalchemy import text
from sqlalchemy.engine import Engine
from sqlmodel import create_engine, Session, SQLModel, select

from config import DB_CONFIG
from connectors.resource_with_relations import ResourceWithRelations
from database.model.concept.concept import AIoDConcept
from database.model.named_relation import NamedRelation
from database.model.platform.platform_names import PlatformName
from routers import resource_routers


def connect_to_database(
    url: str = "mysql://root:ok@127.0.0.1:3307/aiod",
    create_if_not_exists: bool = True,
    delete_first: bool = False,
) -> Engine:
    """Connect to server, optionally creating the database if it does not exist.

    Params
    ------
    url: URL to the database, see https://docs.sqlalchemy.org/en/20/core/engines.html#backend-specific-urls # noqa
    create_if_not_exists: create the database if it does not exist
    delete_first: drop the database before creating it again, to start with an empty database.
        IMPORTANT: Using `delete_first` means ALL data in that database will be lost permanently.

    Returns
    -------
    engine: Engine SQLAlchemy Engine configured with a database connection
    """

    if delete_first or create_if_not_exists:
        drop_or_create_database(url, delete_first)
    engine = create_engine(url, echo=False, pool_recycle=3600)

    with engine.connect() as connection:
        AIoDConcept.metadata.create_all(connection, checkfirst=True)
        connection.commit()
    return engine


def drop_or_create_database(url: str, delete_first: bool):
    server, database = url.rsplit("/", 1)
    engine = create_engine(server, echo=False)  # Temporary engine, not connected to a database

    with engine.connect() as connection:
        if delete_first:
            connection.execute(text(f"DROP DATABASE IF EXISTS {database}"))
        connection.execute(text(f"CREATE DATABASE IF NOT EXISTS {database}"))
        connection.commit()
    engine.dispose()


def _get_existing_resource(
    session: Session, resource: AIoDConcept, clazz: type[SQLModel]
) -> AIoDConcept | None:
    """Selecting a resource based on platform and platform_identifier"""
    is_enum = NamedRelation in clazz.__mro__
    if is_enum:
        query = select(clazz).where(clazz.name == resource)
    else:
        query = select(clazz).where(
            and_(
                clazz.platform == resource.platform,
                clazz.platform_identifier == resource.platform_identifier,
            )
        )
    return session.scalars(query).first()


def _create_or_fetch_related_objects(session: Session, item: ResourceWithRelations):
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
                and resource.platform_identifier is not None
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


def sqlmodel_engine(rebuild_db: str) -> Engine:
    """
    Return a SQLModel engine, backed by the MySql connection as configured in the configuration
    file.
    """
    username = DB_CONFIG.get("name", "root")
    password = DB_CONFIG.get("password", "ok")
    host = DB_CONFIG.get("host", "demodb")
    port = DB_CONFIG.get("port", 3306)
    database = DB_CONFIG.get("database", "aiod")

    db_url = f"mysql://{username}:{password}@{host}:{port}/{database}"

    delete_before_create = rebuild_db == "always"
    return connect_to_database(db_url, delete_first=delete_before_create)
