import responses

from tests.testutils.paths import path_test_resources


TOKEN_EXPIRATION_DATETIME = "2024-02-08T17:40:07Z"

with open(path_test_resources() / "connectors" / "zenodo" / "list_records_1.xml", "r", encoding="utf-8") as f:
    records_list_1 = f.read()

with open(path_test_resources() / "connectors" / "zenodo" / "list_records_2.xml", "r", encoding="utf-8") as f:
    records_list_2 = f.read()


def first_list_response(mocked_requests: responses.RequestsMock):
    mocked_requests.add(
        responses.GET,
        "https://zenodo.org/oai2d?"
        "metadataPrefix=oai_datacite&"
        "from=2023-05-23T08%3A00%3A00&"
        "until=2023-05-23T09%3A00%3A00&"
        "verb=ListRecords",
        body=records_list_1,
        status=200,
    )


def second_list_response(mocked_requests: responses.RequestsMock):
    mocked_requests.add(
        responses.GET,
        "https://zenodo.org/oai2d?"
        "resumptionToken=.resumption-token-to-page-2&"
        "verb=ListRecords",
        body=records_list_2,
        status=200,
    )


def second_list_response_after_interruption(mocked_requests: responses.RequestsMock):
    mocked_requests.add(
        responses.GET,
        "https://zenodo.org/oai2d?"
        "metadataPrefix=oai_datacite&"
        "from=2023-05-23T08%3A00%3A47.001000&"
        "until=2023-05-23T09%3A00%3A00&"
        "verb=ListRecords",
        body=records_list_2,
        status=200,
    )


def second_list_response_time_out(mocked_requests: responses.RequestsMock):
    mocked_requests.add(
        responses.GET,
        "https://zenodo.org/oai2d?"
        "resumptionToken=.resumption-token-to-page-2&"
        "verb=ListRecords",
        body=(
            "<html><body><h1>504 Gateway Time-out</h1>\n"
            "The server didn't respond in time.\n</body></html>\n"
        ),
        status=504,
    )


def response_with_no_records(mocked_requests: responses.RequestsMock):
    mocked_requests.add(
        responses.GET,
        "https://zenodo.org/oai2d?"
        "metadataPrefix=oai_datacite&"
        "from=2023-05-23T08%3A00%3A00&"
        "until=2023-05-23T09%3A00%3A00&"
        "verb=ListRecords",
        body="422 Client Error: UNPROCESSABLE ENTITY",
        status=422,
    )


def record_response(mocked_requests: responses.RequestsMock, id_: int):
    with open(path_test_resources() / "connectors" / "zenodo" / f"{id_}.json", "r", encoding="utf-8") as f:
        body = f.read()
    mocked_requests.add(
        responses.GET, f"https://zenodo.org/api/records/{id_}/files", body=body, status=200
    )


def first_list_records_responses(mocked_requests: responses.RequestsMock):
    for id_ in (6884943, 7793917, 7947283, 7555467, 7902673):
        record_response(mocked_requests, id_)


def second_list_records_responses(mocked_requests: responses.RequestsMock):
    record_response(mocked_requests, 7199024)
