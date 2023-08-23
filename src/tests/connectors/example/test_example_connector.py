import pytest

import connectors


@pytest.mark.skip(reason="connectors currently don't work")
@pytest.mark.parametrize(
    "datatype",
    [
        "case_studies",
        "computational_resources",
        "educational_resources",
        "events",
        "presentations",
        "projects",
        "publications",
        "news",
        "organisations",
    ],
)
def test_fetch_all_happy_path(datatype: str):
    connector = connectors.example_connectors[datatype]
    resources = list(connector.fetch_all(limit=None))
    assert len(resources) >= 1
    resource = resources[0]
    if hasattr(resource, "keywords"):  # otherwise, only tested that connector can run
        assert set(resource.keywords) == {"keyword1", "keyword2"}
