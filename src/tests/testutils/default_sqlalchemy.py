import sqlite3
import tempfile
from typing import Iterator, Type, Any
from unittest.mock import Mock

import pytest
from fastapi import FastAPI
from pytest import FixtureRequest
from sqlalchemy import event
from sqlalchemy.engine import Engine
from sqlmodel import create_engine, SQLModel, Session, select
from starlette.testclient import TestClient

from database.deletion.triggers import add_delete_triggers
from database.model.concept.concept import AIoDConcept
from database.model.platform.platform import Platform
from database.model.platform.platform_names import PlatformName
from database.session import EngineSingleton
from main import add_routes
from tests.testutils.test_resource import RouterTestResource, factory


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
    engine = create_engine(f"sqlite:///{temporary_file.name}?check_same_thread=False")
    AIoDConcept.metadata.create_all(engine)
    EngineSingleton().patch(engine)

    # Yielding is essential, the temporary file will be closed after the engine is used
    yield engine


@pytest.fixture
def engine_test_resource_filled(engine: Engine) -> Iterator[Engine]:
    """
    Engine will be filled with an example value after before each test, in clear_db.
    """
    yield engine


@pytest.fixture(autouse=True)
def clear_db(request, engine: Engine):
    """
    This fixture will be used by every test and checks if the test uses an engine.
    If it does, it deletes the content of the database, so the test has a fresh db to work with.
    """
    with Session(engine) as session:
        if session.scalars(select(Platform)).first():
            pytest.exit("A previous test did not clean properly. See other errors.")
    with Session(engine) as session:
        session.add_all([Platform(name=name) for name in PlatformName])
        if any("engine" in fixture and "filled" in fixture for fixture in request.fixturenames):
            session.add(
                factory(
                    title="A title",
                    platform="example",
                    platform_resource_identifier="1",
                )
            )
        session.commit()

    yield

    with engine.connect() as connection:
        transaction = connection.begin()
        for table in reversed(SQLModel.metadata.sorted_tables):
            connection.execute(table.delete())
        transaction.commit()


@event.listens_for(Engine, "connect")
def sqlite_enable_foreign_key_constraints(dbapi_connection, connection_record):
    """
    On default, sqlite disables foreign key constraints
    """
    if isinstance(dbapi_connection, sqlite3.Connection):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


@pytest.fixture(scope="session")
def client(engine: Engine) -> TestClient:
    """
    Create a TestClient that can be used to mock sending requests to our application
    """
    app = FastAPI()
    add_routes(app)
    return TestClient(app, base_url="http://localhost")


@pytest.fixture(scope="session")
def client_test_resource(engine: Engine) -> TestClient:
    """A Startlette TestClient including routes to the TestResource, only in "aiod" schema"""
    app = FastAPI()
    app.include_router(RouterTestResource().create(""))
    return TestClient(app, base_url="http://localhost")


def _user_with_roles(*roles: str) -> dict[str, Any]:
    return {
        "realm_access": {"roles": roles},
        "resource_access": {
            "account": {"roles": ["manage-account", "manage-account-links", "view-profile"]}
        },
        "scope": "openid profile email",
        "username": "user",
        "token_type": "Bearer",
        "active": True,
    }


@pytest.fixture()
def mocked_token(request: FixtureRequest) -> Mock:
    """
    Return a mocked function that returns a user, to mock the authentication.

    Optionally, you can give a list of roles to this fixture, using Pytest indirect parametrization:
    https://docs.pytest.org/en/latest/example/parametrize.html#deferring-the-setup-of-parametrized-resources
    """
    roles = (
        request.param
        if hasattr(request, "param")
        else ["offline_access", "uma_authorization", "default-roles-aiod"]
    )
    return Mock(return_value=_user_with_roles(*roles))


@pytest.fixture()
def mocked_privileged_token() -> Mock:
    roles = ["offline_access", "uma_authorization", "default-roles-aiod", "edit_aiod_resources"]
    return Mock(return_value=_user_with_roles(*roles))


@pytest.fixture()
def mocked_ai4europe_cms_token() -> Mock:
    roles = [
        "offline_access",
        "uma_authorization",
        "default-roles-aiod",
        "full_view_ai4europe_cms_resources",
    ]
    return Mock(return_value=_user_with_roles(*roles))
