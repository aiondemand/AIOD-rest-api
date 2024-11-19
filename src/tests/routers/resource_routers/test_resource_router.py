from datetime import datetime, timedelta
from unittest.mock import Mock

import pytest
from starlette.testclient import TestClient


@pytest.mark.parametrize(
    "resource_type",
    [
        "case_studies",
        "computational_assets",
        "contacts",
        "datasets",
        "educational_resources",
        "events",
        "experiments",
        "ml_models",
        "news",
        "organisations",
        "persons",
        "projects",
        "publications",
        "services",
        "teams",
    ],
)
@pytest.mark.parametrize(
    "resource_filters,expected_count",
    [
        ({"date_modified_after": datetime.today().strftime("%Y-%m-%d")}, 1),
        ({"date_modified_before": datetime.today().strftime("%Y-%m-%d")}, 0),
        ({"date_modified_after": (datetime.today() + timedelta(days=1)).strftime("%Y-%m-%d")}, 0),
        ({"date_modified_before": (datetime.today() + timedelta(days=1)).strftime("%Y-%m-%d")}, 1),
        (
            {
                "date_modified_after": datetime.today().strftime("%Y-%m-%d"),
                "date_modified_before": datetime.today().strftime("%Y-%m-%d"),
            },
            0,
        ),
        (
            {
                "date_modified_after": datetime.today().strftime("%Y-%m-%d"),
                "date_modified_before": (datetime.today() + timedelta(days=1)).strftime("%Y-%m-%d"),
            },
            1,
        ),
    ],
)
def test_happy_path_with_filters(
    client: TestClient,
    mocked_privileged_token: Mock,
    body_asset: dict,
    resource_type,
    resource_filters: dict,
    expected_count: int,
):
    response = client.post(
        f"/{resource_type}/v1", json=body_asset, headers={"Authorization": "Fake token"}
    )
    assert response.status_code == 200, response.json()

    response = client.get(f"/{resource_type}/v1", params=resource_filters)
    assert response.status_code == 200, response.json()

    response_json = response.json()
    assert isinstance(response_json, list)
    assert len(response_json) == expected_count
