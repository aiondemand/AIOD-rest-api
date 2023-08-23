from datetime import datetime

import pytest
import responses
import connectors
from database.model.platform.platform_names import PlatformName
from tests.testutils.paths import path_test_resources


def read_file(path):
    with open(path, "r") as file:
        content = file.read()
    return content


@pytest.mark.skip(reason="TODO: while going to Metadata model v2")
def test_fetch_all_happy_path():
    connector = connectors.dataset_connectors[PlatformName.zenodo]
    with responses.RequestsMock() as mocked_requests:
        mock_zenodo_responses(mocked_requests)
        datasets = list(connector.fetch_all())
    assert len(datasets) == 1
    dataset = datasets[0]
    assert dataset.name == "THE FIELD'S MALL MASS SHOOTING: EMERGENCY MEDICAL SERVICES RESPONSE"
    assert dataset.description == "This is a description paragraph"
    assert (
        dataset.creator
        == "Hansen, Peter Martin; Alstrøm, henrik; Damm-Hejmdal, Anders; Mikkelsen, Søren"
    )
    assert dataset.date_published == datetime(2023, 5, 6)
    assert dataset.license.name == "https://creativecommons.org/licenses/by/4.0/legalcode"
    assert dataset.platform == "zenodo"
    assert dataset.platform_identifier == "zenodo.org:7961614"
    assert dataset.publisher == "Zenodo"
    assert len(dataset.keywords) == 5
    assert {k.name for k in dataset.keywords} == {
        "Mass casualty",
        "Major incident",
        "Management and leadership",
        "Disaster",
        "Mass shooting",
    }


def mock_zenodo_responses(mocked_requests: responses.RequestsMock):
    with open(
        path_test_resources() / "connectors" / "zenodo" / "list_records.xml",
        "r",
    ) as f:
        records_list = f.read()
    mocked_requests.add(
        responses.GET,
        "https://zenodo.org/oai2d?metadataPrefix=oai_datacite&from=2000-01-01T12%3A00%3A00&verb=ListRecords",  # noqa E501
        body=records_list,
        status=200,
    )
