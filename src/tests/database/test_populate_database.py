import json

import responses
from sqlalchemy import Engine, select
from sqlalchemy.orm import Session

from connectors import (
    ExampleDatasetConnector,
    ExamplePublicationConnector,
    OpenMlDatasetConnector,
    HuggingFaceDatasetConnector,
    ExampleCodeArtifactConnector,
)


from database.models import CodeArtifactDescription, Publication, DatasetDescription
from database.setup import populate_database
from tests.testutils.paths import path_test_resources

OPENML_URL = "https://www.openml.org/api/v1/json"
HUGGINGFACE_URL = "https://datasets-server.huggingface.co"


def test_example_happy_path(engine: Engine):
    populate_database(
        engine,
        dataset_connectors=[ExampleDatasetConnector()],
        publications_connectors=[ExamplePublicationConnector()],
        codeartifact_connectors=[ExampleCodeArtifactConnector()],
    )
    with Session(engine) as session:
        datasets = session.scalars(select(DatasetDescription)).all()
        publications = session.scalars(select(Publication)).all()
        codeartifacts = session.scalars(select(CodeArtifactDescription)).all()
        assert len(datasets) == 5
        assert len(publications) == 2
        assert len(codeartifacts) == 5
        assert {len(d.publications) for d in datasets} == {0, 1, 2}
        assert {len(p.datasets) for p in publications} == {1, 2}


def test_openml_happy_path(engine: Engine):
    with responses.RequestsMock() as mocked_requests:
        with open(path_test_resources() / "connectors" / "openml" / "data_list.json", "r") as f:
            response = json.load(f)
        mocked_requests.add(responses.GET, f"{OPENML_URL}/data/list", json=response, status=200)
        populate_database(
            engine,
            dataset_connectors=[OpenMlDatasetConnector()],
            publications_connectors=[ExamplePublicationConnector()],
        )

    with Session(engine) as session:
        datasets = session.scalars(select(DatasetDescription)).all()
        publications = session.scalars(select(Publication)).all()
        assert len(datasets) == 5
        assert len(publications) == 2
        assert {len(d.publications) for d in datasets} == {0, 1}
        assert {len(p.datasets) for p in publications} == {0, 1}


def test_huggingface_happy_path(engine: Engine):
    with responses.RequestsMock() as mocked_requests:
        path_data_list = path_test_resources() / "connectors" / "huggingface" / "data_list.json"
        with open(path_data_list, "r") as f:
            response = json.load(f)
        mocked_requests.add(responses.GET, f"{HUGGINGFACE_URL}/valid", json=response, status=200)
        for split_name in ("0n1xus/codexglue", "04-07-22/wep-probes", "rotten_tomatoes"):
            mock_split(mocked_requests, split_name)
        populate_database(
            engine,
            dataset_connectors=[HuggingFaceDatasetConnector()],
            publications_connectors=[ExamplePublicationConnector()],
        )

    with Session(engine) as session:
        datasets = session.scalars(select(DatasetDescription)).all()
        publications = session.scalars(select(Publication)).all()
        assert len(datasets) == 3 * 6
        ids = [d.node_specific_identifier for d in datasets]
        names = [d.name for d in datasets]
        assert "0n1xus|codexglue|code-completion-token-py150|train" in ids
        assert "codexglue config:code-completion-token-py150 split:train" in names
        assert "rotten_tomatoes|default|validation" in ids
        assert "rotten_tomatoes config:default split:validation" in names
        assert len(publications) == 2
        assert {len(d.publications) for d in datasets} == {0}
        assert {len(p.datasets) for p in publications} == {0}


def mock_split(mocked_requests: responses.RequestsMock, split_name: str):
    filename = f"splits_{split_name.replace('/', '|')}.json"
    path_split = path_test_resources() / "connectors" / "huggingface" / filename
    with open(path_split, "r") as f:
        response = json.load(f)
    mocked_requests.add(
        responses.GET, f"{HUGGINGFACE_URL}/splits?dataset={split_name}", json=response, status=200
    )
