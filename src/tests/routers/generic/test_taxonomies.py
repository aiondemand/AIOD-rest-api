import copy
from http import HTTPStatus

import pytest

from tests.routers.resource_routers.test_router_organisation import with_organisation_taxonomies
from tests.testutils.users import logged_in_user


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("turnover", "foo"),
        ("number_of_employees", "foo"),
    ]
)
def test_invalid_value_is_rejected(field, value, body_agent, client, with_organisation_taxonomies):
    organisation = copy.copy(body_agent)
    organisation[field] = value

    with logged_in_user():
        response = client.post(
            "/organisations",
            json=organisation,
            headers={"Authorization": "Fake token"},
        )
    assert response.status_code == HTTPStatus.BAD_REQUEST
    assert "not part of the taxonomy" in response.json()["detail"]
    assert field in response.json()["detail"]
    assert value in response.json()["detail"]
