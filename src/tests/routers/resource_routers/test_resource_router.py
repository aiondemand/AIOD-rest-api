import itertools
from datetime import datetime, timedelta
from unittest.mock import Mock

import pytest
from starlette.testclient import TestClient

from dependencies.sorting import SortDirection, Sort
from tests.testutils.users import register_asset


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
    auto_publish: None,
):
    response = client.post(
        f"/{resource_type}", json=body_asset, headers={"Authorization": "Fake token"}
    )
    assert response.status_code == 200, response.json()

    response = client.get(f"/{resource_type}", params=resource_filters)
    assert response.status_code == 200, response.json()

    response_json = response.json()
    assert isinstance(response_json, list)
    assert len(response_json) == expected_count


@pytest.mark.parametrize(
    "resource_type",
    [
        "case_studies",  # generic
        "organisations",  # currently has custom overrides
        "projects",  # currently has custom overrides
    ],
)
def test_happy_path_with_sorting(
        client: TestClient,
        mocked_privileged_token: Mock,
        body_asset: dict,
        resource_type,
        auto_publish: None,
):
    # We set up the resources so that the order of `date_created` and `date_modified` are
    # different, to assess if the `sort` (by property) parameter works later
    first = client.post(
        f"/{resource_type}", json=body_asset, headers={"Authorization": "Fake token"}
    ).json()["identifier"]
    second = client.post(
        f"/{resource_type}", json=body_asset, headers={"Authorization": "Fake token"}
    ).json()["identifier"]
    client.put(
        f"/{resource_type}/{first}",
        json=body_asset,
        headers={"Authorization": "Fake token"},
    )

    for sort, direction in itertools.product(list(Sort), list(SortDirection)):
        resources = client.get(
            f"/{resource_type}",
            params={
                "direction": str(direction),
                "sort": str(sort),
            },
        ).json()

        match sort, direction:
            case Sort.DATE_MODIFIED, SortDirection.ASC:
                assert [r["identifier"] for r in resources] == [second, first]
            case Sort.DATE_MODIFIED, SortDirection.DESC:
                assert [r["identifier"] for r in resources] == [first, second]
            case Sort.DATE_CREATED, SortDirection.ASC:
                assert [r["identifier"] for r in resources] == [first, second]
            case Sort.DATE_CREATED, SortDirection.DESC:
                assert [r["identifier"] for r in resources] == [second, first]
            case _:
                assert False, f"Unknown sort strategy: ({sort}, {direction})"
