"""
Utility functions for initializing the database and tables through SQLAlchemy.
"""

from operator import and_

import sqlmodel
from sqlalchemy import text, create_engine
from sqlmodel import SQLModel, select
from sqlalchemy.exc import OperationalError

from config import DB_CONFIG
from database.model.concept.concept import AIoDConcept
from database.model.named_relation import NamedRelation
from database.session import db_url


def create_database(*, delete_first: bool):
    url = db_url(including_db=False)
    engine = create_engine(
        url, echo=False
    )  # Temporary engine, not connected to a database
    with engine.connect() as connection:
        database = DB_CONFIG.get("database", "aiod")
        if delete_first:
            connection.execute(text(f"DROP DATABASE IF EXISTS {database}"))
        connection.execute(text(f"CREATE DATABASE IF NOT EXISTS {database}"))


def database_exists() -> bool:
    """Checks whether the database defined in the configuration exists."""
    url = db_url(including_db=True)
    # Using the singleton defined in `Session.py` may be cleaner, but I could
    # not find documentation that ensures me that creating the engine there and
    # then potentially re-creating the database later is safe.
    # Since this function is only supposed to be called once, using a separate
    # Engine object does not seem problematic.
    engine = create_engine(url, echo=False)
    try:
        with engine.connect() as _:
            pass
    except OperationalError:
        return False
    return True


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
                clazz.platform_resource_identifier
                == resource.platform_resource_identifier,
            )
        )
    return session.scalars(query).first()
