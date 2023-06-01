import tempfile
from typing import Iterator

import pytest
from fastapi import FastAPI
from sqlalchemy.engine import Engine
from sqlmodel import create_engine, SQLModel, Session
from starlette.testclient import TestClient

from database.model import AIAsset
from main import add_routes
from tests.testutils.utils_resource import RouterResourceTest, ResourceTest
from unittest.mock import Mock


@pytest.fixture(scope="session")
def engine() -> Iterator[Engine]:
    """
    Create a SqlAlchemy engine for tests, backed by a temporary sqlite file.
    """
    temporary_file = tempfile.NamedTemporaryFile()
    engine = create_engine(f"sqlite:///{temporary_file.name}")
    SQLModel.metadata.create_all(engine)
    # Yielding is essential, the temporary file will be closed after the engine is used
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
                for table in SQLModel.metadata.tables.values():
                    connection.execute(table.delete())
                transaction.commit()
            if "filled" in engine_name:
                with Session(engine) as session:
                    session.add_all(
                        [
                            AIAsset(type="test_resource"),
                            ResourceTest(
                                title="A title",
                                platform="example",
                                platform_identifier="1",
                                identifier=1,
                            ),
                        ]
                    )
                    session.commit()


@pytest.fixture(scope="session")
def engine_test_resource() -> Iterator[Engine]:
    """Create a SqlAlchemy Engine populated with an instance of the ResourceTest"""
    temporary_file = tempfile.NamedTemporaryFile()
    engine = create_engine(f"sqlite:///{temporary_file.name}")
    SQLModel.metadata.create_all(engine)
    yield engine


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
    return TestClient(app)


@pytest.fixture(scope="session")
def client_test_resource(engine_test_resource) -> TestClient:
    """A Startlette TestClient including routes to the ResourceTest, only in "aiod" schema"""
    app = FastAPI()
    app.include_router(RouterResourceTest().create(engine_test_resource, ""))
    return TestClient(app)


@pytest.fixture()
def mocked_token() -> Mock:
    default_user = {
        "name": "test-user",
        "realm_access": {
            "roles": [
                "default-roles-dev",
                "offline_access",
                "uma_authorization",
            ]
        },
    }
    return Mock(return_value=default_user)


@pytest.fixture()
def mocked_privileged_token() -> Mock:
    default_user = {
        "name": "test-user",
        "realm_access": {
            "roles": [
                "default-roles-dev",
                "offline_access",
                "uma_authorization",
                "edit_aiod_resources",
            ]
        },
    }
    return Mock(return_value=default_user)
