import tempfile
from typing import Iterator

import pytest
from fastapi import FastAPI
from sqlalchemy import create_engine, Engine
from starlette.testclient import TestClient

from database.model.base import Base
from main import add_routes


@pytest.fixture(scope="session")
def engine() -> Iterator[Engine]:
    """
    Create a SqlAlchemy engine for tests, backed by a temporary sqlite file.
    """
    temporary_file = tempfile.NamedTemporaryFile()
    engine = create_engine(f"sqlite:///{temporary_file.name}")
    Base.metadata.create_all(engine)
    # Yielding is essential, the temporary file will be closed after the engine is used
    yield engine


@pytest.fixture(autouse=True)
def clear_db(request):
    """
    This fixture will be used by every test and checks if the test uses an engine.
    If it does, it deletes the content of the database, so the test has a fresh db to work with.
    """
    if "engine" in request.fixturenames:
        engine = request.getfixturevalue("engine")
        with engine.connect() as connection:
            transaction = connection.begin()
            for table in Base.metadata.tables.values():
                connection.execute(table.delete())
            transaction.commit()


@pytest.fixture(scope="session")
def client(engine: Engine) -> TestClient:
    """
    Create a TestClient that can be used to mock sending requests to our application
    """
    app = FastAPI()
    add_routes(app, engine)
    return TestClient(app)
