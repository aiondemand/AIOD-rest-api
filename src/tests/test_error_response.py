import logging

from tests.testutils.users import logged_in_user


def test_reference_json_and_log_match(client, caplog):
    url_raises_because_dataset_does_not_exist = "/datasets/42"
    with caplog.at_level(logging.DEBUG):
        response = client.get(url_raises_because_dataset_does_not_exist).json()

    assert "reference" in response, response  # noqa: S101
    reference_in_log = response["reference"] in caplog.text
    assert reference_in_log, "The reference provided to the user should be in the log."  # noqa: S101


def test_duplicate_upload_logs_request_body(client, body_asset: dict, auto_publish: None, caplog):
    body = dict(body_asset)
    body["type"] = "storage"

    with logged_in_user():
        response = client.post(
            "/computational_assets", json=body, headers={"Authorization": "Fake token"}
        )
    assert response.status_code == 200, response.json()  # noqa: S101

    with logged_in_user(), caplog.at_level(logging.DEBUG):
        response = client.post(
            "/computational_assets",
            json={"invalid": "payload"},
            headers={"Authorization": "Fake token"},
        )

    assert response.status_code in (400, 422), response.json()  # noqa: S101
    assert "<Data Stream with unknown content>" not in caplog.text  # noqa: S101
    assert "invalid" in caplog.text  # noqa: S101
