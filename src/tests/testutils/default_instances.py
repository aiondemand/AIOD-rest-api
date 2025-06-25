"""
Fixtures that provide default instances for AIoD and ORM classes.

This way you have easy access to, for instance, an AIoDDataset filled with default values.
"""

import copy
import json
import uuid
from functools import partial
from typing import Callable

import pytest
from sqlalchemy.engine import Engine

from database.model.agent.contact import Contact
from database.model.agent.organisation import Organisation
from database.model.agent.person import Person
from database.model.dataset.dataset import Dataset
from database.model.knowledge_asset.publication import Publication
from database.model.models_and_experiments.experiment import Experiment
from database.model.platform.platform import Platform
from database.model.resource_read_and_create import resource_create
from database.model.serializers import deserialize_resource_relationships
from database.session import DbSession
from tests.testutils.paths import path_test_resources


@pytest.fixture(scope="session")
def load_body_concept() -> dict:
    with open(path_test_resources() / "schemes" / "aiod" / "aiod_concept.json", "r") as f:
        return json.load(f)


@pytest.fixture()
def body_concept(load_body_concept: dict) -> dict:
    return copy.deepcopy(load_body_concept)


@pytest.fixture(scope="session")
def load_body_resource() -> dict:
    with open(path_test_resources() / "schemes" / "aiod" / "ai_resource.json", "r") as f:
        return json.load(f)


@pytest.fixture()
def body_resource(body_concept: dict, load_body_resource: dict) -> dict:
    body = copy.deepcopy(body_concept)
    body.update(load_body_resource)
    return copy.deepcopy(body)


@pytest.fixture(scope="session")
def load_body_asset() -> dict:
    with open(path_test_resources() / "schemes" / "aiod" / "ai_asset.json", "r") as f:
        return json.load(f)


@pytest.fixture()
def body_asset(body_resource: dict, load_body_asset: dict) -> dict:
    body = copy.deepcopy(body_resource)
    body.update(load_body_asset)
    return copy.deepcopy(body)


@pytest.fixture(scope="session")
def load_body_agent() -> dict:
    with open(path_test_resources() / "schemes" / "aiod" / "agent.json", "r") as f:
        return json.load(f)


@pytest.fixture()
def body_agent(body_resource: dict, load_body_agent: dict) -> dict:
    body = copy.deepcopy(body_resource)
    body.update(load_body_agent)
    return copy.deepcopy(body)


def make_publication(body_asset: dict, with_random_platform_identifier: bool = False) -> Publication:
    body = copy.deepcopy(body_asset)
    body["permanent_identifier"] = "http://dx.doi.org/10.1093/ajae/aaq063"
    body["isbn"] = "9783161484100"
    body["issn"] = "20493630"
    body["type"] = "journal"
    return _create_class_with_body(Publication, body)


@pytest.fixture
def publication(body_asset: dict) -> Publication:
    return make_publication(body_asset)


@pytest.fixture
def publication_factory(body_asset: dict) -> Callable[[], Publication]:
    return partial(make_publication, body_asset, with_random_platform_identifier=True)


@pytest.fixture
def contact(body_concept, engine: Engine) -> Contact:
    body = copy.deepcopy(body_concept)
    body["email"] = ["a@b.com"]
    body["telephone"] = ["0032 XXXX XXXX"]
    body["location"] = [
        {
            "address": {"country": "NED", "street": "Street Name 10", "postal_code": "1234AB"},
            "geo": {"latitude": 37.42242, "longitude": -122.08585, "elevation_millimeters": 2000},
        }
    ]
    return _create_class_with_body(Contact, body)


@pytest.fixture
def dataset(body_asset: dict) -> Dataset:
    body = copy.deepcopy(body_asset)
    body["issn"] = "20493630"
    body["measurement_technique"] = "mass spectrometry"
    body["temporal_coverage"] = "2011/2012"
    return _create_class_with_body(Dataset, body)


@pytest.fixture
def organisation(body_agent: dict) -> Organisation:
    body = copy.deepcopy(body_agent)
    body["date_founded"] = "2022-01-01"
    body["legal_name"] = "Legal Name"
    body["ai_relevance"] = "Description of relevance in AI"
    return _create_class_with_body(Organisation, body)


@pytest.fixture
def person(body_agent: dict) -> Person:
    body = copy.deepcopy(body_agent)
    body["expertise"] = ["machine learning"]
    body["language"] = ["eng", "nld"]
    return _create_class_with_body(Person, body)


@pytest.fixture
def experiment(body_asset: dict) -> Experiment:
    return _create_class_with_body(Experiment, body_asset)


@pytest.fixture
def platform() -> Platform:
    body = {"name": "aiod"}
    return _create_class_with_body(Platform, body)


def _create_class_with_body(clz, body: dict):
    pydantic_class = resource_create(clz)
    res_create = pydantic_class(**body)
    res = clz.from_orm(res_create)
    with DbSession() as session:
        deserialize_resource_relationships(session, clz, res, res_create)
        session.commit()
    if hasattr(res, "ai_resource"):
        res.ai_resource.type = clz.__tablename__
    return res
