import sqlite3
import tempfile
from typing import Iterator, Type
from unittest.mock import Mock

import pytest
from fastapi import FastAPI
from sqlalchemy import event, text
from sqlalchemy.engine import Engine
from sqlmodel import create_engine, SQLModel, Session
from starlette.testclient import TestClient

from database.deletion.triggers import add_delete_triggers
from database.model.concept.concept import AIoDConcept
from database.model.platform.platform import Platform
from database.model.platform.platform_names import PlatformName
from main import add_routes
from tests.testutils.test_resource import RouterTestResource, test_resource_factory


@pytest.fixture(scope="session")
def deletion_triggers() -> Type[AIoDConcept]:
    """Making sure that the deletion triggers are only created once"""
    add_delete_triggers(AIoDConcept)
    return AIoDConcept


@pytest.fixture(scope="session")
def engine(deletion_triggers) -> Iterator[Engine]:
    """
    Create a SqlAlchemy engine for tests, backed by a temporary sqlite file.
    """
    temporary_file = tempfile.NamedTemporaryFile()
    engine = create_engine(f"sqlite:///{temporary_file.name}")
    SQLModel.metadata.create_all(engine)
    # Yielding is essential, the temporary file will be closed after the engine is used
    yield engine


@pytest.fixture(scope="session")
def engine_test_resource(deletion_triggers) -> Iterator[Engine]:
    """Create a SqlAlchemy Engine populated with an instance of the TestResource"""
    temporary_file = tempfile.NamedTemporaryFile()
    engine = create_engine(f"sqlite:///{temporary_file.name}")
    SQLModel.metadata.create_all(engine)
    yield engine


@pytest.fixture(autouse=True)
def clear_db(request):
    """
    This fixture will be used by every test and checks if the test uses an engine.
    If it does, it deletes the content of the database, so the test has a fresh db to work with.
    """

    for engine_name in ("engine", "engine_test_resource", "engine_test_resource_filled"):
        if engine_name in request.fixturenames:
            engine = request.getfixturevalue(engine_name)
            with engine.connect() as connection:
                transaction = connection.begin()
                connection.execute(text("PRAGMA foreign_keys=OFF"))
                for table in SQLModel.metadata.tables.values():
                    connection.execute(table.delete())
                connection.execute(text("PRAGMA foreign_keys=ON"))
                transaction.commit()
            with Session(engine) as session:
                session.add_all([Platform(name=name) for name in PlatformName])
                if "filled" in engine_name:
                    session.add(
                        test_resource_factory(
                            title="A title",
                            platform="example",
                            platform_resource_identifier="1",
                        )
                    )
                session.commit()


@event.listens_for(Engine, "connect")
def sqlite_enable_foreign_key_constraints(dbapi_connection, connection_record):
    """
    On default, sqlite disables foreign key constraints
    """
    if isinstance(dbapi_connection, sqlite3.Connection):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


@pytest.fixture
def engine_test_resource_filled(engine_test_resource: Engine) -> Iterator[Engine]:
    """
    Engine will be filled with an example value after before each test, in clear_db.
    """
    yield engine_test_resource


@pytest.fixture(scope="session")
def client(engine: Engine) -> TestClient:
    """
    Create a TestClient that can be used to mock sending requests to our application
    """
    app = FastAPI()
    add_routes(app, engine)
    return TestClient(app, base_url="http://localhost")


@pytest.fixture(scope="session")
def client_test_resource(engine_test_resource) -> TestClient:
    """A Startlette TestClient including routes to the TestResource, only in "aiod" schema"""
    app = FastAPI()
    app.include_router(RouterTestResource().create(engine_test_resource, ""))
    return TestClient(app, base_url="http://localhost")


@pytest.fixture()
def mocked_token() -> Mock:
    default_user = {
        "name": "test-user",
        "groups": [
            "default-roles-dev",
            "offline_access",
            "uma_authorization",
        ],
    }
    return Mock(return_value=default_user)


@pytest.fixture()
def mocked_privileged_token() -> Mock:
    default_user = {
        "name": "test-user",
        "groups": [
            "default-roles-dev",
            "offline_access",
            "uma_authorization",
            "edit_aiod_resources",
        ],
    }
    return Mock(return_value=default_user)
