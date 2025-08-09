import logging


def test_reference_json_and_log_match(client, caplog):
    url_raises_because_dataset_does_not_exist = "/datasets/42"
    with caplog.at_level(logging.DEBUG):
        response = client.get(url_raises_because_dataset_does_not_exist).json()

    assert "reference" in response, response
    reference_in_log = response["reference"] in caplog.text
    assert reference_in_log, "The reference provided to the user should be in the log."
