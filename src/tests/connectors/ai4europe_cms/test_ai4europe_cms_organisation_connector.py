import os
import json
import responses

from datetime import datetime

from connectors.ai4europe_cms.ai4europe_cms_organisation_connector import (
    AI4EuropeCmsOrganisationConnector,
)
from connectors.resource_with_relations import ResourceWithRelations
from database.model.agent.organisation import Organisation
from database.model.platform.platform_names import PlatformName
from tests.testutils.paths import path_test_resources


TOKEN = "TEST_AIBUILDER_API_TOKEN"
API_URL = "https://community-dev-api.aiod.eu/api/organisations/"
connector = AI4EuropeCmsOrganisationConnector()
test_resources_path = os.path.join(path_test_resources(), "connectors", "ai4europe_cms")


def test_run_happy_path():
    catalog_list_path = os.path.join(test_resources_path, "organisations_list.json")

    with responses.RequestsMock() as mocked_requests:
        with open(catalog_list_path, "r") as f:
            expected_response = json.load(f)

        with responses.RequestsMock() as mocked_requests:
            mocked_requests.add(
                responses.GET,
                API_URL,
                json=expected_response,
                headers={"AuthorizationToken": "1234567890"},
                status=200,
            )
            fetched_resources = list(connector.run(state={}))

        mocked_datetime = datetime.fromisoformat("2023-01-01T00:00:00+00:00")
        assert len(fetched_resources) == 3
        for i, (resource) in enumerate(fetched_resources):
            assert type(resource) == ResourceWithRelations
            assert resource.resource_ORM_class == Organisation
            assert resource.resource.platform == PlatformName.ai4europe_cms
            assert (
                resource.resource.platform_resource_identifier
                == f"mock-node-{str(i + 1)}"
            )
            assert resource.resource.name == f"mock-organisation-{i + 1}"
            assert resource.resource.date_published == mocked_datetime
            assert resource.resource.type == f"mock-type-{i + 1}"
