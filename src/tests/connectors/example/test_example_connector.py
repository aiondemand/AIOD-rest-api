from typing import TYPE_CHECKING

import pytest

from connectors.example.example import (
    ExampleDatasetConnector,
    ExamplePublicationConnector,
    ExampleServiceConnector,
    ExamplePersonConnector,
    ExampleOrganisationConnector,
    ExampleMLModelConnector,
    ExampleExperimentConnector,
)

if TYPE_CHECKING:
    from connectors.example.example_connector import ExampleConnector  # noqa:F401

example_connectors = {
    "datasets": ExampleDatasetConnector(),
    "experiments": ExampleExperimentConnector(),
    "ml_models": ExampleMLModelConnector(),
    "organisations": ExampleOrganisationConnector(),
    "persons": ExamplePersonConnector(),
    "publications": ExamplePublicationConnector(),
    "services": ExampleServiceConnector(),
}  # type: dict[str, ExampleConnector]


@pytest.mark.parametrize(
    "datatype",
    [
        "datasets",
        "experiments",
        "ml_models",
        "organisations",
        "persons",
        "publications",
        "services",
    ],
)
def test_fetch_happy_path(datatype: str):
    connector = example_connectors[datatype]
    resources = list(connector.fetch())
    assert len(resources) >= 1
    resource = resources[0]
    if hasattr(resource, "keywords"):  # otherwise, only tested that connector can run
        assert set(resource.keywords) == {"keyword1", "keyword2"}
