import datetime

import responses

from connectors.record_error import RecordError
from connectors.zenodo.zenodo_dataset_connector import ZenodoDatasetConnector
from database.model.agent.person import Person
from tests.testutils.paths import path_test_resources


def test_fetch_happy_path():
    connector = ZenodoDatasetConnector()
    with responses.RequestsMock() as mocked_requests:
        mock_zenodo_responses(mocked_requests)

        from_incl = datetime.datetime(2000, 1, 1, 12, 0, 0)
        to_excl = datetime.datetime(2000, 1, 2, 12, 0, 0)
        resources = list(connector.run(state={}, from_date=from_incl, to_excl=to_excl))
    datasets = [r for r in resources if not isinstance(r, RecordError)]
    assert len(datasets) == 1
    dataset = datasets[0].resource
    assert dataset.name == "THE FIELD'S MALL MASS SHOOTING: EMERGENCY MEDICAL SERVICES RESPONSE"
    assert dataset.description == "This is a description paragraph"
    assert dataset.date_published == datetime.datetime(2023, 5, 6)
    assert dataset.license == "https://creativecommons.org/licenses/by/4.0/legalcode"
    assert dataset.platform == "zenodo"
    assert dataset.platform_identifier == "zenodo.org:7961614"
    assert set(dataset.keyword) == {
        "Mass casualty",
        "Major incident",
        "Management and leadership",
        "Disaster",
        "Mass shooting",
    }

    creators: list[Person] = datasets[0].related_resources["creator"]  # type: ignore
    assert len(creators) == 4
    for given, sur in [
        ("Peter Martin", "Hansen"),
        ("henrik", "Alstrøm"),
        ("Anders", "Damm-Hejmdal"),
        ("Søren", "Mikkelsen"),
    ]:
        assert any(c for c in creators if c.given_name == given and c.surname == sur)


def test_retry_happy_path():
    connector = ZenodoDatasetConnector()
    with responses.RequestsMock() as mocked_requests:
        with open(path_test_resources() / "connectors" / "zenodo" / "dataset.json", "r") as f:
            dataset = f.read()
        mocked_requests.add(
            responses.GET,
            "https://zenodo.org/api/records/7902672",  # noqa E501
            body=dataset,
            status=200,
        )
        id_ = "7902672"
        resource_with_relations = connector.retry(id_)
    dataset = resource_with_relations.resource
    assert dataset.name == "THE FIELD'S MALL MASS SHOOTING: EMERGENCY MEDICAL SERVICES RESPONSE"
    assert dataset.description == "This is a description paragraph"
    assert dataset.date_published == datetime.datetime(
        2023, 5, 23, 7, 56, 17, 414652, tzinfo=datetime.timezone.utc
    )
    assert dataset.license == "CC-BY-4.0"
    assert dataset.platform == "zenodo"
    assert dataset.platform_identifier == "7902672"

    assert len(dataset.keyword) == 5
    assert set(dataset.keyword) == {
        "Mass casualty",
        "Major incident",
        "Management and leadership",
        "Disaster",
        "Mass shooting",
    }
    creators: list[Person] = resource_with_relations.related_resources["creator"]  # type: ignore
    assert len(creators) == 6
    for given, sur in [
        ("Peter Martin", "Hansen"),
        ("henrik", "Alstrøm"),
        ("Anders", "Damm-Hejmdal"),
        ("Søren", "Mikkelsen"),
        ("Marius", "Rehn"),
        ("Peter Anthony", "Berlac"),
    ]:
        assert any(c for c in creators if c.given_name == given and c.surname == sur)


def mock_zenodo_responses(mocked_requests: responses.RequestsMock):
    with open(
        path_test_resources() / "connectors" / "zenodo" / "list_records.xml",
        "r",
    ) as f:
        records_list = f.read()
    mocked_requests.add(
        responses.GET,
        "https://zenodo.org/oai2d?metadataPrefix=oai_datacite&from=2000-01-01T00%3A00%3A00&until=2000-01-02T12%3A00%3A00&verb=ListRecords",  # noqa E501
        body=records_list,
        status=200,
    )
