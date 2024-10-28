import datetime

import pytest
import responses
import requests

from freezegun import freeze_time
from ratelimit import limits
from ratelimit.exception import RateLimitException
from requests.exceptions import HTTPError

from config import REQUEST_TIMEOUT
from connectors.record_error import RecordError
from connectors.zenodo import zenodo_dataset_connector
from connectors.zenodo.zenodo_dataset_connector import ZenodoDatasetConnector
from database.model.agent.contact import Contact
from tests.connectors.zenodo import mock_zenodo


fake_now = datetime.datetime.fromisoformat(
    mock_zenodo.TOKEN_EXPIRATION_DATETIME.replace("Z", "")
) - datetime.timedelta(minutes=2)


@freeze_time(fake_now)
def test_fetch_happy_path():
    """
    Test the successful path scenario for fetching records from Zenodo.
    This test ensures that all 51 records are fetched correctly and processed as expected
    (6 datasets without errors and the rest due to 'wrong type).

    Steps:
    1. Mock responses for list and record requests.
    2. Initialize the connector and fetch records within a specified time range.
    3. Validate the fetched datasets and errors against expected values.
    """
    connector = ZenodoDatasetConnector()
    with responses.RequestsMock() as mocked_requests:
        mock_zenodo.first_list_response(mocked_requests)
        mock_zenodo.first_list_records_responses(mocked_requests)
        mock_zenodo.second_list_response(mocked_requests)
        mock_zenodo.second_list_records_responses(mocked_requests)

        from_incl = datetime.datetime(2023, 5, 23, 8, 0, 0)
        to_excl = datetime.datetime(2023, 5, 23, 9, 0, 0)
        resources = list(connector.run(state={}, from_incl=from_incl, to_excl=to_excl))
    datasets = [r for r in resources if not isinstance(r, RecordError)]
    errors = [r for r in resources if isinstance(r, RecordError)]
    assert {error.error for error in errors} == {"Wrong type"}
    assert len(datasets) == 6
    assert len(errors) == 45
    dataset = datasets[0].resource
    assert dataset.name == "kogalab21/all-alpha_design"
    expected = (
        "Source data and demos for the research article entitled “Design of "
        "complicated all-α protein structures” by Koya Sakuma, Naohiro Kobayashi, "
        "Toshihiko Sugiki, Toshio Nagashima, Toshimichi Fujiwara, Kano Suzuki, Naoya "
        "Kobayashi, Takeshi Murata, Takahiro Kosugi, Rie Koga, and Nobuyasu Koga."
    )
    assert dataset.description.plain.replace(" ", "").replace("\n", "") == expected.replace(" ", "")
    assert dataset.date_published == datetime.datetime(2023, 5, 18)
    assert dataset.license == "Other (Open)"
    assert dataset.platform == "zenodo"
    assert dataset.platform_resource_identifier == "zenodo.org:7947283"
    assert set(dataset.keyword) == set()

    creators: list[Contact] = datasets[0].related_resources["creator"]
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


def test_fetch_expired_token_happy_path():
    """
    Test the scenario when the resumption token expires during fetching.
    This test ensures that the connector stops the calls before that happens avoiding a 422 error.
    Then it resumes the process fetching the next batch of records with a new resumption token.
    As a result all the records (51) are processed without skipping any from fetching.

    Steps:
    1. Mock responses for list and record requests.
    2. Initialize the connector and fetch records within a specified time range.
    3. Validate the fetched datasets and errors against expected values.
    """
    connector = ZenodoDatasetConnector()
    with responses.RequestsMock() as mocked_requests:
        mock_zenodo.first_list_response(mocked_requests)
        mock_zenodo.second_list_response_after_interruption(mocked_requests)
        mock_zenodo.first_list_records_responses(mocked_requests)
        mock_zenodo.second_list_records_responses(mocked_requests)

        state = {}
        from_incl = datetime.datetime(2023, 5, 23, 8, 0, 0)
        to_excl = datetime.datetime(2023, 5, 23, 9, 0, 0)
        resources = list(connector.run(state, from_incl=from_incl, to_excl=to_excl))
        datasets = [r for r in resources if not isinstance(r, RecordError)]
        errors = [r for r in resources if isinstance(r, RecordError)]

        assert {error.error for error in errors} == {"Wrong type"}
        assert len(datasets) == 6
        assert len(errors) == 45


@freeze_time(fake_now)
def test_fetch_harvesting_rate_limit(monkeypatch):
    """
    Test the scenario when the harvesting rate limit is reached.
    This test ensures that the connector handles rate limits correctly.
    With harvest rate limit set to 1, the API will fail to retrieve the second list.
    In reality the tested method will sleep and retry resuming the process.

    Steps:
    1. Mock the _check_harvesting_rate method to limit the calls.
    2. Mock responses for list requests.
    3. Initialize the connector and attempt to fetch records.
    4. Validate that a RateLimitException is raised with the correct message.
    """

    @staticmethod
    @limits(calls=1, period=60)
    def mock_check():
        pass

    monkeypatch.setattr(ZenodoDatasetConnector, "_check_harvesting_rate", mock_check)

    with responses.RequestsMock() as mocked_requests:
        mock_zenodo.first_list_response(mocked_requests)

        from_incl = datetime.datetime(2023, 5, 23, 8, 0, 0)
        to_excl = datetime.datetime(2023, 5, 23, 9, 0, 0)
        connector = zenodo_dataset_connector.ZenodoDatasetConnector()
        with pytest.raises(RateLimitException) as exc_info:
            resources = list(connector.run(state={}, from_incl=from_incl, to_excl=to_excl))
            assert resources is None, resources
        assert exc_info.value.args[0] == "too many calls"


@freeze_time(fake_now)
def test_fetch_records_rate_limit(monkeypatch):
    """
    Cheap check to test the scenario when the rate limit for fetching records is reached.
    This test ensures that the connector handles record fetch rate limits correctly.
    With rate limit set to 1, only the first record will be retrieved. In reality
    the tested method will sleep and retry resuming the process.

    Steps:
    1. Mock the _get_record method to limit the calls.
    2. Mock responses for list and record requests.
    3. Initialize the connector and attempt to fetch records.
    4. Validate that records are fetched correctly despite rate limits.
    """

    @staticmethod
    @limits(calls=1, period=60)
    def mock_check(id_number):
        response = requests.get(
            f"https://zenodo.org/api/records/{id_number}/files", timeout=REQUEST_TIMEOUT
        )
        return response

    monkeypatch.setattr(ZenodoDatasetConnector, "_get_record", mock_check)

    with responses.RequestsMock() as mocked_requests:
        mock_zenodo.first_list_response(mocked_requests)
        mock_zenodo.second_list_response(mocked_requests)
        mock_zenodo.record_response(mocked_requests, 7947283)

        from_incl = datetime.datetime(2023, 5, 23, 8, 0, 0)
        to_excl = datetime.datetime(2023, 5, 23, 9, 0, 0)
        connector = zenodo_dataset_connector.ZenodoDatasetConnector()
        resources = list(connector.run(state={}, from_incl=from_incl, to_excl=to_excl))

        datasets = [r for r in resources if not isinstance(r, RecordError)]
        errors = [r for r in resources if isinstance(r, RecordError)]
        assert {type(error.error) for error in errors} == {str, RateLimitException}

        assert len(datasets) == 1
        assert len(errors) == 50


@freeze_time(fake_now)
def test_resuming_processing_after_timeout():
    """
    Test the scenario when the fetching the records is interrupted by time out error
    from zenodo. It's expected that the API halts fetching the records and starts processing them
    to avoid losing the records already retrieved.

    Steps:
    1. Mock responses for list and record requests.
    2. Initialize the connector and fetch records within a specified time range.
    3. Validate the fetched datasets and errors against expected values.
    """
    connector = ZenodoDatasetConnector()
    with responses.RequestsMock() as mocked_requests:
        mock_zenodo.first_list_response(mocked_requests)
        mock_zenodo.second_list_response_time_out(mocked_requests)
        mock_zenodo.first_list_records_responses(mocked_requests)
        mock_zenodo.second_list_response_after_interruption(mocked_requests)
        mock_zenodo.second_list_records_responses(mocked_requests)

        from_incl = datetime.datetime(2023, 5, 23, 8, 0, 0)
        to_excl = datetime.datetime(2023, 5, 23, 9, 0, 0)
        resources = list(connector.run(state={}, from_incl=from_incl, to_excl=to_excl))
        datasets = [r for r in resources if not isinstance(r, RecordError)]
        errors = [r for r in resources if isinstance(r, RecordError)]
        assert {error.error for error in errors} == {"Wrong type"}
        assert len(datasets) == 6
        assert len(errors) == 45


@freeze_time(fake_now)
def test_response_with_no_records():
    """
    Test the scenario when the fetching the records returns an 422 error in the first call,
    which means that no record was found for the chosen period.

    Steps:
    1. Mock responses for list and record requests.
    2. Initialize the connector and fetch records within a specified time range.
    3. Validate the fetched datasets and errors and state against expected values.
    """
    connector = ZenodoDatasetConnector()
    state = {}
    with responses.RequestsMock() as mocked_requests:
        mock_zenodo.response_with_no_records(mocked_requests)

        from_incl = datetime.datetime(2023, 5, 23, 8, 0, 0)
        to_excl = datetime.datetime(2023, 5, 23, 9, 0, 0)
        resources = list(connector.run(state=state, from_incl=from_incl, to_excl=to_excl))
        datasets = [r for r in resources if not isinstance(r, RecordError)]
        errors = [r for r in resources if isinstance(r, RecordError)]
        assert len(datasets) == 0
        assert len(errors) == 1
        assert isinstance(errors[0].error, HTTPError), errors
        assert "422" in errors[0].error.args[0], errors
        assert state["from_incl"] == from_incl.timestamp()
        assert state["to_excl"] == to_excl.timestamp()
        assert state["last"] is None
