"""
Fixtures that provide default instances for AIoD and ORM classes.

This way you have easy access to, for instance, an AIoDDataset filled with default values.
"""
import copy
import json

import pytest
from sqlalchemy.engine import Engine
from sqlmodel import Session

from database.model.agent.contact import Contact
from database.model.agent.organisation import Organisation
from database.model.agent.person import Person
from database.model.concept.status import Status
from database.model.dataset.dataset import Dataset
from database.model.knowledge_asset.publication import Publication
from database.model.models_and_experiments.experiment import Experiment
from database.model.resource_read_and_create import resource_create
from database.model.serializers import deserialize_resource_relationships
from tests.testutils.paths import path_test_resources


@pytest.fixture
def draft() -> Status:
    return Status(name="draft")


@pytest.fixture(scope="session")
def body_concept() -> dict:
    with open(path_test_resources() / "schemes" / "aiod" / "aiod_concept.json", "r") as f:
        return json.load(f)


@pytest.fixture(scope="session")
def body_resource(body_concept: dict) -> dict:
    body = copy.copy(body_concept)
    with open(path_test_resources() / "schemes" / "aiod" / "ai_resource.json", "r") as f:
        resource = json.load(f)
    body.update(resource)
    return body


@pytest.fixture(scope="session")
def body_asset(body_resource: dict) -> dict:
    body = copy.copy(body_resource)
    with open(path_test_resources() / "schemes" / "aiod" / "ai_asset.json", "r") as f:
        asset = json.load(f)
    body.update(asset)
    return body


@pytest.fixture(scope="session")
def body_agent(body_resource: dict) -> dict:
    body = copy.copy(body_resource)
    with open(path_test_resources() / "schemes" / "aiod" / "agent.json", "r") as f:
        agent = json.load(f)
    body.update(agent)
    return body


@pytest.fixture
def publication(body_asset: dict, engine: Engine) -> Publication:
    body = copy.copy(body_asset)
    body["permanent_identifier"] = "http://dx.doi.org/10.1093/ajae/aaq063"
    body["isbn"] = "9783161484100"
    body["issn"] = "20493630"
    body["type"] = "journal"
    return _create_class_with_body(Publication, body, engine)


@pytest.fixture
def contact(body_concept, engine: Engine) -> Contact:
    body = copy.copy(body_concept)
    body["email"] = ["a@b.com"]
    body["telephone"] = ["0032 XXXX XXXX"]
    body["location"] = [
        {
            "address": {"country": "NED", "street": "Street Name 10", "postal_code": "1234AB"},
            "geo": {"latitude": 37.42242, "longitude": -122.08585, "elevation_millimeters": 2000},
        }
    ]
    return _create_class_with_body(Contact, body, engine)


@pytest.fixture
def dataset(body_asset: dict, engine: Engine) -> Dataset:
    body = copy.copy(body_asset)
    body["issn"] = "20493630"
    body["measurement_technique"] = "mass spectrometry"
    body["temporal_coverage"] = "2011/2012"
    return _create_class_with_body(Dataset, body, engine)


@pytest.fixture
def organisation(body_agent, engine: Engine) -> Organisation:
    body = copy.copy(body_agent)
    body["date_founded"] = "2022-01-01"
    body["legal_name"] = "Legal Name"
    body["ai_relevance"] = "Description of relevance in AI"
    return _create_class_with_body(Organisation, body, engine)


@pytest.fixture
def person(body_agent, engine: Engine) -> Person:
    body = copy.copy(body_agent)
    body["expertise"] = ["machine learning"]
    body["language"] = ["eng", "nld"]
    return _create_class_with_body(Person, body, engine)


@pytest.fixture
def experiment(body_asset, engine: Engine) -> Experiment:
    body = copy.copy(body_asset)
    return _create_class_with_body(Experiment, body, engine)


def _create_class_with_body(clz, body: dict, engine: Engine):
    pydantic_class = resource_create(clz)
    res_create = pydantic_class(**body)
    res = clz.from_orm(res_create)
    with Session(engine) as session:
        deserialize_resource_relationships(session, clz, res, res_create)
        session.commit()
    if hasattr(res, "ai_resource"):
        res.ai_resource.type = clz.__tablename__
    return res
