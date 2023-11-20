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

        from_incl = datetime.datetime(2023, 5, 23, 8, 0, 0)
        to_excl = datetime.datetime(2023, 5, 23, 9, 0, 0)
        resources = list(connector.run(state={}, from_incl=from_incl, to_excl=to_excl))
    datasets = [r for r in resources if not isinstance(r, RecordError)]
    errors = [r for r in resources if isinstance(r, RecordError)]
    assert {error.error for error in errors} == {"Wrong type"}
    assert len(datasets) == 6
    assert len(errors) == 20
    dataset = datasets[0].resource
    assert dataset.name == "kogalab21/all-alpha_design"
    expected = (
        "Source data and demos for the research article entitled “Design of "
        "complicated all-α protein structures” by Koya Sakuma, Naohiro Kobayashi, "
        "Toshihiko Sugiki, Toshio Nagashima, Toshimichi Fujiwara, Kano Suzuki, Naoya "
        "Kobayashi, Takeshi Murata, Takahiro Kosugi, Rie Koga, and Nobuyasu Koga."
    )
    assert dataset.description.plain == expected
    assert dataset.date_published == datetime.datetime(2023, 5, 18)
    assert dataset.license == "Other (Open)"
    assert dataset.platform == "zenodo"
    assert dataset.platform_resource_identifier == "zenodo.org:7947283"
    assert set(dataset.keyword) == set()

    creators: list[Person] = datasets[0].related_resources["creator"]
    assert len(creators) == 1
    assert creators[0].name == "Nobuyasu Koga"

    (dataset_7902673,) = [
        d.resource
        for d in datasets
        if d.resource.platform_resource_identifier == "zenodo.org:7902673"
    ]
    distributions = dataset_7902673.distribution
    assert len(distributions) == 3
    distribution = distributions[0]
    assert distribution.name == "FIELDS_CONFIDE_CHECLIST.docx"
    assert distribution.encoding_format == "application/octet-stream"
    assert distribution.checksum == "97f511d24f8867405a8f87afbc76939d"
    assert distribution.checksum_algorithm == "md5"
    assert (
        distribution.content_url
        == "https://zenodo.org/api/records/7902673/files/FIELDS_CONFIDE_CHECLIST.docx/content"
    )


def mock_zenodo_responses(mocked_requests: responses.RequestsMock):
    with open(
        path_test_resources() / "connectors" / "zenodo" / "list_records.xml",
        "r",
    ) as f:
        records_list = f.read()
    mocked_requests.add(
        responses.GET,
        "https://zenodo.org/oai2d?"
        "metadataPrefix=oai_datacite&"
        "from=2023-05-23T08%3A00%3A00&"
        "until=2023-05-23T09%3A00%3A00&"
        "verb=ListRecords",
        body=records_list,
        status=200,
    )
    for id_ in (6884943, 7793917, 7199024, 7947283, 7555467, 7902673):
        with open(path_test_resources() / "connectors" / "zenodo" / f"{id_}.json", "r") as f:
            body = f.read()
        mocked_requests.add(
            responses.GET, f"https://zenodo.org/api/records/{id_}/files", body=body, status=200
        )
