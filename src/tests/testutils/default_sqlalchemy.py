import sqlite3
import tempfile
from typing import Iterator, Any
from unittest.mock import Mock

import pytest
from fastapi import FastAPI
from pytest import FixtureRequest
from sqlalchemy import event, text
from sqlalchemy.engine import Engine
from sqlmodel import create_engine, SQLModel, Session, select
from starlette.testclient import TestClient

from authentication import keycloak_openid
from database.deletion.triggers import create_delete_triggers, \
    create_identifier_synchronization_triggers
from database.model.concept.aiod_entry import EntryStatus, AIoDEntryORM
from database.model.concept.concept import AIoDConcept
from database.model.platform.platform import Platform
from database.model.platform.platform_names import PlatformName
from database.session import EngineSingleton
from main import build_app
from database.model.ai_resource.application_area import ApplicationArea
from database.model.ai_resource.industrial_sector import IndustrialSector
from database.model.ai_resource.research_area import ResearchArea
from database.model.ai_resource.scientific_domain import ScientificDomain
from database.model.ai_asset.license import License
from database.model.knowledge_asset.PublicationType import PublicationType
from database.model.news.news_category import NewsCategory
from tests.testutils.test_resource import RouterTestResource, factory_test_resource
from tests.testutils.users import bypass_reviewer_publish_everything
from taxonomies.synchronize_taxonomy import Term

DEFAULT_TEST_RESOURCE_IDENTIFIER = "test_KwfnsoJOAejyRdv2PaXUPAbW"
DEFAULT_INDUSTRIAL_SECTORS = [
    Term("ecommerce", "for use in tests", children=[]),
    Term("Pharmaceuticals", "for use in tests", children=[]),
    Term("Computer Programming", "for use in tests", children=[]),
    Term("Cybersecurity", "for use in tests", children=[]),
]
DEFAULT_RESEARCH_AREAS = [
    Term("explainable ai", "for use in tests", children=[]),
    Term("ai services", "for use in tests", children=[]),
    Term("multi-agent systems", "for use in tests", children=[]),
]
DEFAULT_SCIENTIFIC_DOMAINS = [
    Term("voice recognition", "for use in tests", children=[]),
    Term("mathematics", "for use in tests", children=[]),
    Term("computer and information sciences", "for use in tests", children=[]),
]
DEFAULT_PUBLICATION_TYPE = [
    Term("article", "for use in tests", children=[]),
    Term("journal", "publication in a journal", children=[])
]
DEFAULT_NEWS_CATEGORY = [
    Term("Education", "for use in tests", children=[]),
    Term("research: education", "for use in tests", children=[]),
    Term("research: awards", "for use in tests", children=[]),
    Term("business: health", "for use in tests", children=[]),
]
DEFAULT_LICENSE = [
    Term("CC-BY-4.0", "for use in tests", children=[]),
]


@pytest.fixture(scope="session")
def engine() -> Iterator[Engine]:
    """
    Create a SqlAlchemy engine for tests, backed by a temporary sqlite file.
    """
    temporary_file = tempfile.NamedTemporaryFile()
    engine = create_engine(f"sqlite:///{temporary_file.name}?check_same_thread=False")
    AIoDConcept.metadata.create_all(engine)
    with Session(engine) as session:
        for trigger in create_delete_triggers(AIoDConcept):
            session.execute(trigger)
        for trigger in create_identifier_synchronization_triggers(dialect='sqlite'):
            session.execute(trigger)
    EngineSingleton().patch(engine)

    # Yielding is essential, the temporary file will be closed after the engine is used
    yield engine


@pytest.fixture
def engine_test_resource_filled(engine: Engine) -> Iterator[str]:
    """
    Engine will be filled with an example value after before each test, in clear_db.
    """
    yield DEFAULT_TEST_RESOURCE_IDENTIFIER


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
            test_resource = factory_test_resource(title="A title", platform="example",
                                  platform_resource_identifier="1")
            test_resource.identifier = DEFAULT_TEST_RESOURCE_IDENTIFIER
            session.add(test_resource)
        session.commit()
        bypass_reviewer_publish_everything()
        for taxonomy, terms in [
            (IndustrialSector, DEFAULT_INDUSTRIAL_SECTORS),
            (ResearchArea, DEFAULT_RESEARCH_AREAS),
            (ScientificDomain, DEFAULT_SCIENTIFIC_DOMAINS),
            (License, DEFAULT_LICENSE),
            (PublicationType, DEFAULT_PUBLICATION_TYPE),
            (NewsCategory, DEFAULT_NEWS_CATEGORY),
        ]:
            for term in terms:
                session.add(taxonomy(**term._asdict(), official=True))
        session.commit()

    yield

    with engine.connect() as connection:
        transaction = connection.begin()
        for table in reversed(SQLModel.metadata.sorted_tables):
            try:
                connection.execute(table.delete())
            except Exception as e:
                print(f"Error while clearing table {table.name}: {e}")
                raise
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
def client(request, engine: Engine) -> TestClient:
    """
    Create a TestClient that can be used to mock sending requests to our application
    """
    app = build_app(version="unittest")
    yield TestClient(app, base_url=f"http://localhost/{request.param}")


# *NEVER* broaden the scope of this fixture, bypassing reviews should be on a test-by-test basis
@pytest.fixture(scope="function")
def auto_publish(engine: Engine):
    """Automatically sets *all* new insertions to the aiod_entry table as published.

    This can be useful to bypass the reviewing workflow, as otherwise assets that were
    just uploaded also require authenticated requests as they would be in a private
    DRAFT status.
    """
    trigger_name = "publish_on_insert"
    with Session(engine) as session:
        session.execute(
            text(f"""
            CREATE TRIGGER {trigger_name}
            AFTER INSERT ON {AIoDEntryORM.__tablename__}
            BEGIN
              UPDATE {AIoDEntryORM.__tablename__}
              SET status='{EntryStatus.PUBLISHED.upper()}'
              WHERE identifier=NEW.identifier;
            END;
            """)
        )
    yield
    with Session(engine) as session:
        session.execute(text(f"DROP TRIGGER {trigger_name}"))


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
        "sub": "default0-fake-test-only-000000000000",
    }


@pytest.fixture()
def overwrites_keycloak_token():
    original = keycloak_openid.introspect
    yield
    keycloak_openid.introspect = original


@pytest.fixture()
def mocked_token(request: FixtureRequest, overwrites_keycloak_token: None):
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
    keycloak_openid.introspect = Mock(return_value=_user_with_roles(*roles))


@pytest.fixture()
def mocked_privileged_token(mocked_token: Mock, overwrites_keycloak_token: None):
    roles = ["offline_access", "uma_authorization", "default-roles-aiod"]
    keycloak_openid.introspect = Mock(return_value=_user_with_roles(*roles))


AI4EUROPE_CMS_TOKEN = Mock(return_value=_user_with_roles("full_view_ai4europe_cms_resources"))
