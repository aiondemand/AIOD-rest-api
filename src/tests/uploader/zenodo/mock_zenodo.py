"""
    Generates mocked responses for zenodo endpoints.
    - POST to BASE_URL: Creates an empty record
    - GET to BASE_URL/RESOURCE_ID: Gets the info of the record.
    - GET to LICENSES_URL: Gets a list of valid licenses to upload content on Zenodo
    - PUT to BASE_URL/RESOURCE_ID: Updates metadata
    - PUT to REPO_URL/FILE_NAME: Uploads a file
    - POST to BASE_URL/RESOURCE_ID/actions/publish: Publishes the dataset with all content
    - GET to BASE_URL/RESOURCE_ID/files: Gets the list of files in draft mode
    - GET to RECORDS_URL/RESOURCE_ID/files: Gets the list of published data
"""

import responses

BASE_URL = "https://zenodo.org/api/deposit/depositions"
REPO_URL = "https://zenodo.org/api/files/fake-bucket-id00"
RECORDS_URL = "https://zenodo.org/api/records"
LICENSES_URL = "https://zenodo.org/api/vocabularies/licenses?q=&tags=data"
HTML_URL = "https://zenodo.org/records"
RESOURCE_ID = 100


def mock_create_repo(mocked_requests: responses.RequestsMock) -> None:
    mocked_requests.add(
        responses.POST,
        BASE_URL,
        json=record_response(),
        status=201,
    )


def mock_get_repo_metadata(
    mocked_requests: responses.RequestsMock, is_published: bool = False
) -> None:
    mocked_requests.add(
        responses.GET,
        f"{BASE_URL}/{RESOURCE_ID}",
        json=record_response(),
        status=200,
    )


def mock_get_licenses(mocked_requests: responses.RequestsMock) -> None:
    mocked_requests.add(
        responses.GET,
        LICENSES_URL,
        json={"hits": {"hits": [{"id": "CC-BY-4.0"}]}},
        status=200,
    )


def mock_update_metadata(mocked_requests: responses.RequestsMock) -> None:
    mocked_requests.add(
        responses.PUT,
        f"{BASE_URL}/{RESOURCE_ID}",
        json={},
        status=200,
    )


def mock_upload_file(mocked_requests: responses.RequestsMock, new_file: str) -> None:
    mocked_requests.add(
        responses.PUT,
        f"{REPO_URL}/{new_file}",
        json={},
        status=201,
    )


def mock_publish_resource(mocked_requests: responses.RequestsMock) -> None:
    mocked_requests.add(
        responses.POST,
        f"{BASE_URL}/{RESOURCE_ID}/actions/publish",
        json=publish_response(),
        status=202,
    )


def mock_get_draft_files(mocked_requests: responses.RequestsMock, *files: str) -> None:
    mocked_requests.add(
        responses.GET,
        f"{BASE_URL}/{RESOURCE_ID}/files",
        json=files_response_from_draft(*files),
        status=200,
    )


def mock_get_published_files(mocked_requests: responses.RequestsMock, *files: str) -> None:
    mocked_requests.add(
        responses.GET,
        f"{RECORDS_URL}/{RESOURCE_ID}/files",
        json=files_response_from_published(*files),
        status=200,
    )


def record_response() -> dict:
    response = {
        "id": RESOURCE_ID,
        "links": {"bucket": REPO_URL, "html": f"{HTML_URL}/{RESOURCE_ID}"},
    }
    return response


def publish_response() -> dict:
    response = {"links": {"record": f"{RECORDS_URL}/{RESOURCE_ID}"}}
    return response


def files_metadata(*filenames: str, is_published: bool = False) -> list[dict]:
    f"""
    Truncated metadata from zenodo when a request is made to the
    {'published' if is_published else 'draft'} repo url.
    """

    def fake_id(name):
        zenodo_pattern = "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
        name = list(name.replace(".", ""))
        file_id = "".join([name.pop() if (s != "-" and name) else s for s in zenodo_pattern])
        return file_id

    metadata: list[dict] = [
        {
            "key" if is_published else "filename": name,
            "file_id" if is_published else "id": fake_id(name),
            "checksum": f"{'md5:' if is_published else ''}12345abcd",
            "size" if is_published else "filesize": 20,
            "links": {"content": f"{RECORDS_URL}/{RESOURCE_ID}/files/{name}/content"}
            if is_published
            else {"download": f"{RECORDS_URL}/{RESOURCE_ID}/draft/files/{name}/content"},
        }
        for name in filenames
    ]
    return metadata


def files_response_from_draft(*filenames) -> list[dict]:
    """
    Truncated response from zenodo when a request is made to the draft repo url.
    """
    response = files_metadata(*filenames)
    return response


def files_response_from_published(*filenames: str) -> dict:
    """
    Truncated response from zenodo when a request is made to the published repo url.
    """
    response = {}
    response["entries"] = files_metadata(*filenames, is_published=True)
    return response
